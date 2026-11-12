#!/usr/bin/env python3
"""All-new teaching simulation. Standard library only; never writes input files."""
import argparse
import csv
import json
import re
from fractions import Fraction
from decimal import Decimal, InvalidOperation, getcontext
from pathlib import Path

D = Decimal
ZERO = D(0)
getcontext().prec = 60
MAX_ROWS = 1000
MAX_CANDIDATES = 1000
MAX_LEDGER_ROWS = 100000


def number(value):
    text = str(value)
    if not re.fullmatch(r"[0-9]{1,7}(?:\.[0-9]{1,6})?", text):
        raise ValueError(f"Expected plain decimal with at most 6 fractional places: {text[:80]}")
    try:
        n = D(text)
    except InvalidOperation as exc:
        raise ValueError(f'Invalid decimal: {value}') from exc
    if not n.is_finite() or not ZERO <= n <= D(1000000):
        raise ValueError(f'Expected finite nonnegative number: {value}')
    return n


def integer(value):
    n = number(value)
    if n != n.to_integral_value():
        raise ValueError(f'Expected integer: {value}')
    return int(n)


def rows(path, columns, key):
    if Path(path).stat().st_size > 1048576:
        raise ValueError(f'{path}: input exceeds 1 MiB')
    with Path(path).open(encoding='utf-8', newline='') as f:
        reader = csv.DictReader(f, strict=True)
        if reader.fieldnames != columns:
            raise ValueError(f'{path}: expected columns {columns}')
        try:
            result = []
            for row in reader:
                result.append(row)
                if len(result) > MAX_ROWS:
                    raise ValueError(f"{path}: too many rows")
        except csv.Error as exc:
            raise ValueError(f"{path}: malformed CSV") from exc
    if not result or any(None in r or any(v is None or not v.strip() for v in r.values()) for r in result):
        raise ValueError(f'{path}: empty/malformed input')
    keys = [r[key] for r in result]
    if key in ('batch','path') and any(not re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]{0,63}', value) for value in keys):
        raise ValueError(f'{path}: IDs must start with an ASCII letter and contain only ASCII letters, digits, underscore or hyphen, maximum 64 characters')
    if len(set(keys)) != len(keys):
        raise ValueError(f'{path}: duplicate {key}')
    return result


def config(path, expected):
    c = {r['key']: number(r['value']) for r in rows(path, ['key', 'value'], 'key')}
    if set(c) != set(expected.split()):
        raise ValueError(f'{path}: missing or unknown config key')
    return c


def decimal_ratio(value):
    """Render an exact rational as Decimal; presentation only, not threshold decisions."""
    f = Fraction(value)
    return D(f.numerator) / D(f.denominator)


def quantile(values, weights, alpha):
    """Exact inverse empirical CDF; compare rational masses without rounded alpha."""
    if not values or len(values) != len(weights) or not ZERO < alpha <= 1:
        raise ValueError('Invalid quantile arguments')
    if any(w <= 0 or not w.is_finite() for w in weights):
        raise ValueError('Weights must be finite and positive')
    target = Fraction(alpha) * sum(map(Fraction, weights))
    running = Fraction(0)
    for value, weight in sorted(zip(values, weights)):
        running += Fraction(weight)
        if running >= target:
            return value
    raise AssertionError('unreachable')


def ceil_pack(value, pack):
    """Round exact ratio upward; never divide in finite-precision Decimal first."""
    if pack <= 0:
        raise ValueError('Pack must be positive')
    ratio = Fraction(value) / Fraction(pack)
    count = -(-ratio.numerator // ratio.denominator)
    return decimal_ratio(count * Fraction(pack))


def load(root):
    root = Path(root)
    nc = config(root/'newsvendor_config.csv', 'underage_cost overage_cost candidate_start candidate_stop candidate_step')
    if nc['underage_cost'] <= 0 or nc['overage_cost'] <= 0 or nc['candidate_step'] <= 0 or nc['candidate_stop'] < nc['candidate_start']:
        raise ValueError('Invalid newsvendor costs/range')
    if (nc['candidate_stop'] - nc['candidate_start']) // nc['candidate_step'] + 1 > MAX_CANDIDATES:
        raise ValueError('Too many newsvendor candidates')
    nv = [(number(r['demand']), number(r['weight'])) for r in rows(root/'newsvendor.csv', ['demand','weight'], 'demand')]
    if len({d for d,w in nv}) != len(nv):
        raise ValueError('Duplicate numeric demand key')
    pr = rows(root/'paths.csv', ['path','day1','day2','day3','weight'], 'path')
    paths = [([number(r[f'day{i}']) for i in range(1,4)], number(r['weight'])) for r in pr]
    if any(w <= 0 for _, w in nv + paths):
        raise ValueError('Weights must be positive')
    demand = {integer(r['day']): number(r['kg']) for r in rows(root/'demand.csv', ['day','kg'], 'day')}
    if set(demand) != set(range(1,len(demand)+1)) or len(demand) != len(rows(root/'demand.csv', ['day','kg'], 'day')):
        raise ValueError('Demand must cover each day 1..H exactly once')
    batches = [{'batch':r['batch'], 'source_type':r['source_type'], 'arrival_day':integer(r['arrival_day']), 'expiry_day':integer(r['expiry_day']), 'kg':number(r['kg'])} for r in rows(root/'batches.csv', ['batch','source_type','arrival_day','expiry_day','kg'], 'batch')]
    ic = config(root/'inventory_config.csv', 'lead_time review_period new_arrival_day new_expiry_day pack_kg moq_kg capacity_kg candidate_max_kg')
    for key in ['lead_time','review_period','new_arrival_day','new_expiry_day']:
        ic[key] = integer(ic[key])
    h = len(demand)
    if ic['review_period'] < 1 or ic['lead_time'] + ic['review_period'] != h or ic['new_arrival_day'] != 1 + ic['lead_time'] or not 1 <= ic['new_arrival_day'] <= ic['new_expiry_day'] <= h:
        raise ValueError('Invalid or uncovered inventory horizon/timing')
    if ic['pack_kg'] <= 0 or ic['capacity_kg'] <= 0 or ic['candidate_max_kg'] % ic['pack_kg']:
        raise ValueError('Invalid pack/capacity/enumeration range')
    count = ic['candidate_max_kg'] // ic['pack_kg'] + 1
    if count > MAX_CANDIDATES or count*h > MAX_LEDGER_ROWS or h > 366:
        raise ValueError('Candidate/horizon/ledger size limit exceeded')
    for b in batches:
        if b['source_type'] not in ('initial','transit') or (b['source_type'] == 'initial' and b['arrival_day'] != 1):
            raise ValueError('Initial stock must be available at the day-1 decision')
        if b['batch'] == 'new_order' or not 1 <= b['arrival_day'] <= b['expiry_day'] <= h:
            raise ValueError('Invalid batch ID/timing or uncovered batch')
    ac = config(root/'apparel.csv', 'pending_orders pieces_per_order conditional_retention additional_demand finished_stock net_bom_m yield material_stock_m timely_transit_m late_transit_m roll_m moq_m production_capacity_pieces')
    if not ZERO < ac['yield'] <= 1 or not ZERO <= ac['conditional_retention'] <= 1 or ac['roll_m'] <= 0:
        raise ValueError('Invalid yield/retention/roll')
    return nc, nv, paths, demand, batches, ic, ac


def simulate(q, demand, batches, c):
    """Diagnostic trajectory even for rejected candidates; never clips arrivals."""
    supply = [dict(b) for b in batches] + [dict(batch='new_order',arrival_day=c['new_arrival_day'],expiry_day=c['new_expiry_day'],kg=q)]
    stock = [dict(b) for b in supply if b.get('source_type') == 'initial']
    supply = [b for b in supply if b.get('source_type') != 'initial']
    ledger = []
    feasible = (q == 0 or q >= c['moq_kg']) and q % c['pack_kg'] == 0
    reasons = [] if feasible else ['pack_or_moq']
    for day in sorted(demand):
        opening = sum((b['kg'] for b in stock), ZERO)
        arrivals = [dict(b) for b in supply if b['arrival_day'] == day]
        stock.extend(arrivals)
        arrival_kg = sum((b['kg'] for b in arrivals), ZERO)
        peak = opening + arrival_kg
        if peak > c['capacity_kg']:
            feasible = False
            reasons.append(f'capacity_day{day}')
        need = demand[day]
        allocations = []
        for b in sorted(stock, key=lambda b:(b['expiry_day'],b['batch'])):
            used = min(b['kg'], need)
            b['kg'] -= used
            need -= used
            if used:
                allocations.append(f"{b['batch']}:{used}")
        expired = sum((b['kg'] for b in stock if b['expiry_day'] == day), ZERO)
        stock = [b for b in stock if b['expiry_day'] > day and b['kg'] > 0]
        closing = sum((b['kg'] for b in stock), ZERO)
        ledger.append(dict(q=q,day=day,opening_kg=opening,arrival_kg=arrival_kg,peak_kg=peak,demand_kg=demand[day],served_kg=demand[day]-need,lost_kg=need,expired_kg=expired,closing_kg=closing,fefo_allocations=';'.join(allocations)))
    return dict(q=q,feasible=feasible,reasons=';'.join(reasons),lost_kg=sum(r['lost_kg'] for r in ledger),expired_kg=sum(r['expired_kg'] for r in ledger),closing_kg=ledger[-1]['closing_kg']), ledger


def calculate(data):
    nc, nv, paths, demand, batches, ic, ac = data
    cu, co = nc['underage_cost'], nc['overage_cost']
    alpha_exact = Fraction(cu) / (Fraction(cu) + Fraction(co))
    alpha = decimal_ratio(alpha_exact)
    nrows = []
    exact_costs = []
    q = nc['candidate_start']
    while q <= nc['candidate_stop']:
        weight_sum = sum(Fraction(w) for _,w in nv)
        short = sum(Fraction(max(d-q,ZERO))*Fraction(w) for d,w in nv)/weight_sum
        left = sum(Fraction(max(q-d,ZERO))*Fraction(w) for d,w in nv)/weight_sum
        cost = Fraction(cu)*short + Fraction(co)*left
        exact_costs.append(cost)
        nrows.append(dict(q=q,expected_shortage=decimal_ratio(short),expected_surplus=decimal_ratio(left),expected_cost=decimal_ratio(cost)))
        q += nc['candidate_step']
    daily = [quantile([p[i] for p,w in paths],[w for p,w in paths],D('.9')) for i in range(3)]
    total_p90 = quantile([sum(p) for p,w in paths],[w for p,w in paths],D('.9'))
    candidates, ledger = [], []
    q = ZERO
    while q <= ic['candidate_max_kg']:
        result, trace = simulate(q,demand,batches,ic)
        candidates.append(result)
        ledger.extend(trace)
        q += ic['pack_kg']
    valid = [r for r in candidates if r['feasible']]
    if not valid:
        raise ValueError('No feasible candidate, including zero order')
    chosen = min(valid,key=lambda r:(r['lost_kg'],r['expired_kg'],r['q']))
    scenario = ac['pending_orders']*ac['pieces_per_order']*ac['conditional_retention']+ac['additional_demand']
    production = max(scenario-ac['finished_stock'], ZERO)
    gross_exact = Fraction(production)*Fraction(ac['net_bom_m'])/Fraction(ac['yield'])
    shortage_exact = max(gross_exact-Fraction(ac['material_stock_m'])-Fraction(ac['timely_transit_m']),Fraction(0))
    gross, shortage = decimal_ratio(gross_exact), decimal_ratio(shortage_exact)
    purchase = ZERO if shortage_exact == 0 else ceil_pack(max(shortage_exact,Fraction(ac['moq_m'])),ac['roll_m'])
    capacity_production = min(production, ac['production_capacity_pieces'])
    capacity_gross_exact = Fraction(capacity_production)*Fraction(ac['net_bom_m'])/Fraction(ac['yield'])
    capacity_shortage_exact = max(capacity_gross_exact-Fraction(ac['material_stock_m'])-Fraction(ac['timely_transit_m']),Fraction(0))
    capacity_gross, capacity_shortage = decimal_ratio(capacity_gross_exact), decimal_ratio(capacity_shortage_exact)
    capacity_purchase = ZERO if capacity_shortage_exact == 0 else ceil_pack(max(capacity_shortage_exact,Fraction(ac['moq_m'])),ac['roll_m'])
    summary = dict(teaching_only=True,inventory_data_semantics='frozen planning scenario, not observed outcomes',quantile_definition='inverse empirical CDF',newsvendor_alpha=alpha,newsvendor_quantile=quantile([d for d,w in nv],[w for d,w in nv],alpha_exact),newsvendor_minimizers=[row['q'] for row,cost in zip(nrows,exact_costs) if cost==min(exact_costs)],daily_p90=daily,sum_daily_p90=sum(daily),total_p90=total_p90,inventory_selected=chosen,naive_q=ceil_pack(max(sum(demand.values())-sum(b['kg'] for b in batches),ZERO),ic['pack_kg']),apparel=dict(expected_scenario_pieces=scenario,production_needed_pieces=production,gross_material_m=gross,shortage_m=shortage,purchase_m=purchase,late_excluded_m=ac['late_transit_m'],capacity_pieces=ac['production_capacity_pieces'],production_capacity_gap=max(production-ac['production_capacity_pieces'],ZERO)))
    capacity_pack_ceiling = (ic['capacity_kg'] // ic['pack_kg']) * ic['pack_kg']
    truncated = capacity_pack_ceiling >= ic['moq_kg'] and ic['candidate_max_kg'] < capacity_pack_ceiling
    summary['inventory_enumeration'] = dict(start_kg=ZERO,stop_kg=ic['candidate_max_kg'],step_kg=ic['pack_kg'],selection_scope='best among enumerated feasible candidates only; not a global optimum claim',potentially_truncated=truncated,warning=('Enumeration maximum is below capacity-based largest legal pack; expand range before claiming adequate search coverage' if truncated else ''),capacity_based_pack_ceiling_kg=capacity_pack_ceiling)
    summary['apparel_capacity_plan'] = dict(planned_production_pieces=capacity_production,gross_material_m=capacity_gross,shortage_m=capacity_shortage,purchase_m=capacity_purchase,unmet_scenario_pieces=production-capacity_production,not_a_delivery_guarantee=True)
    return summary,nrows,candidates,ledger


def save_csv(path, data):
    with path.open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(data[0]))
        writer.writeheader()
        writer.writerows(data)


def execute(inputs, output):
    inputs, output = Path(inputs).resolve(), Path(output).resolve()
    source = Path(__file__).resolve().parent
    if output.exists() or output == inputs or output in inputs.parents or inputs in output.parents or output == source or output in source.parents:
        raise ValueError('Output must be a NEW directory, separate from inputs and not an ancestor of code')
    results = calculate(load(inputs))  # validate and calculate before creating anything
    output.mkdir(parents=True,exist_ok=False)
    summary,nrows,candidates,ledger=results
    (output/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2,default=str)+'\n',encoding='utf-8')
    save_csv(output/'newsvendor.csv',nrows)
    save_csv(output/'inventory_candidates.csv',candidates)
    save_csv(output/'inventory_ledger.csv',ledger)
    a, c = summary['apparel'], summary['apparel_capacity_plan']
    save_csv(output/'apparel_plans.csv', [
        dict(plan='full_target_preparation',production_pieces=a['production_needed_pieces'],gross_material_m=a['gross_material_m'],shortage_m=a['shortage_m'],purchase_m=a['purchase_m'],capacity_or_unmet_gap_pieces=a['production_capacity_gap']),
        dict(plan='capacity_limited_scenario',production_pieces=c['planned_production_pieces'],gross_material_m=c['gross_material_m'],shortage_m=c['shortage_m'],purchase_m=c['purchase_m'],capacity_or_unmet_gap_pieces=c['unmet_scenario_pieces'])])
    return summary


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs',type=Path,default=Path(__file__).parent/'inputs')
    parser.add_argument('--output',type=Path,required=True,help='New output directory; existing paths are refused')
    args=parser.parse_args()
    try:
        result=execute(args.inputs,args.output)
    except (ValueError,OSError,csv.Error) as exc:
        parser.exit(2,f'Error: {exc}\n')
    print(json.dumps(result,ensure_ascii=False,indent=2,default=str))

if __name__ == '__main__':
    main()
