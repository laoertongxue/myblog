"""D18: disclosed mechanism replay, not parameter selection or unseen testing."""
from pathlib import Path
from decimal import Decimal as D, Context, ROUND_CEILING, ROUND_HALF_EVEN, localcontext
from datetime import date, timedelta
from fractions import Fraction
import csv
import hashlib
import json

from inventory import (simulate, audit, number, integer, check_identity, require,
                       validate_config, validate_row, write_csv, dump_json,
                       LEDGER_FIELDS, EVENT_FIELDS, exact_arithmetic)

ROOT = Path(__file__).resolve().parent
FIXED_RECEIPT_SHA256 = '397925935669a2935fe882c35b1e0a038c73a305c64e05619ee4adb5bce19d8e'
CASES = ('hewei', 'apparel')
Z_VALUES = ('0', '1', '1.645')
STRATEGIES = tuple(f'{case}-z{z}' for case in CASES for z in Z_VALUES)
STATS_CONTEXT = Context(prec=40, rounding=ROUND_HALF_EVEN)
SOURCE_NAMES = ('POLICY_CARD.md', 'parameters.json', 'data/hewei-training.csv',
                'data/apparel-training.csv', 'data/hewei-replay.csv',
                'data/apparel-replay.csv', 'REVISION_NOTES.md',
                'freeze_receipt_v1_superseded.json',
                'freeze_receipt_v2_pre_precision.json')
CYCLE_FIELDS = ['cycle_index', 'start_day', 'end_day', 'unit', 'demand', 'served',
                'lost_sales', 'no_stockout', 'unit_fill_rate']


def decimal_text(value):
    """12 fractional digits for display only; inventory calculations stay exact."""
    with localcontext(STATS_CONTEXT):
        return format(value.quantize(D('0.000000000001')), 'f')


def ratio(numerator, denominator):
    with localcontext(STATS_CONTEXT):
        return None if denominator == 0 else decimal_text(D(numerator) / D(denominator))


def estimate(values, unit):
    if not isinstance(values, list) or not 2 <= len(values) <= 1000:
        raise ValueError('sample standard deviation needs 2 to 1000 training days')
    numbers = [number(v, unit) for v in values]
    with localcontext(STATS_CONTEXT):
        mean = sum(numbers) / len(numbers)
        variance = sum((x-mean)**2 for x in numbers) / (len(numbers)-1)
        return mean, variance.sqrt()


def formula_input(value):
    """Bound externally supplied moments while retaining 40-digit estimates."""
    if isinstance(value, bool) or not isinstance(value, (str,int,float,D)):
        raise ValueError('invalid formula input')
    try:
        x=D(str(value))
    except Exception as exc:
        raise ValueError('invalid formula input') from exc
    if not x.is_finite() or not 0 <= x <= 1000000:
        raise ValueError('formula input must be finite, nonnegative and bounded')
    # Count exact significant digits from the tuple, never context-normalize.
    # The smallest nonzero training mean is .001/1000 = .000001;
    # the smallest nonzero sample standard deviation is larger than that.
    digits=x.as_tuple().digits
    end=len(digits)
    while end and digits[end-1]==0:
        end-=1
    if x and (x < D('0.000001') or end > 40):
        raise ValueError('formula moments support at most 40 significant digits and nonzero values >= 0.000001')
    return x


def exact_target_level(mean, sigma_day, horizon, z, step):
    """ceil((mean*H + z*sigma*sqrt(H))/step), without rounded sqrt/sums.

    For nonnegative b, a+b*sqrt(H) <= k*step iff the gap is nonnegative
    and gap**2 >= b**2*H. Fraction makes that comparison exact for the
    supplied finite Decimal moments, including 40-digit training estimates.
    """
    a=Fraction(mean)*horizon
    b=Fraction(z)*Fraction(sigma_day)
    unit=Fraction(step)
    square=b*b*horizon
    def sufficient(k):
        gap=k*unit-a
        return gap>=0 and gap*gap>=square
    lower,upper=0,int(Fraction(1000000)//unit)
    require(sufficient(upper),'rounded target exceeds supported quantity bound')
    while lower<upper:
        middle=(lower+upper)//2
        if sufficient(middle):upper=middle
        else:lower=middle+1
    with localcontext(STATS_CONTEXT):
        return D(lower)*step


def target(mean, sigma_day, horizon, z, unit, increment):
    """Moment/normal approximation is a teaching assumption, not a service promise."""
    if unit not in ('kg', 'pieces'):
        raise ValueError('unknown unit')
    require(type(horizon) is int and 1 <= horizon <= 2000, 'invalid protection horizon')
    mean,sigma_day=formula_input(mean),formula_input(sigma_day)
    # z has an explicit supported decimal resolution; tiny positives are
    # rejected rather than silently lost when added to a much larger mean.
    z=number(z,'kg',D(5))
    step=number(increment,unit)
    if step <= 0:
        raise ValueError('increment must be positive')
    level=exact_target_level(mean,sigma_day,horizon,z,step)
    number(level,unit)
    with localcontext(STATS_CONTEXT):
        sigma_h=sigma_day*D(horizon).sqrt()
        ss=z*sigma_h
        mean_h=mean*horizon
        raw=mean_h+ss
        # Display values are approximate; no displayed/rounded value decides S.
        return {'horizon_days':horizon, 'z':str(z), 'daily_mean':decimal_text(mean),
                'daily_sample_std':decimal_text(sigma_day),
                'horizon_sigma_iid':decimal_text(sigma_h),
                'mean_horizon_demand':decimal_text(mean_h),
                'theoretical_safety_stock':decimal_text(ss),
                'continuous_target':decimal_text(raw), 'target_rounding_increment':str(step),
                'target_level':str(level), 'effective_buffer':decimal_text(level-mean_h)}


def load_csv(path):
    with path.open(encoding='utf-8',newline='') as f:
        reader=csv.DictReader(f)
        required=['case','series','unit','day','date','demand']
        require(reader.fieldnames == required, 'invalid or duplicated CSV header')
        return list(reader)


def load_case(strategy, root=ROOT):
    if strategy not in STRATEGIES:
        raise ValueError('unknown strategy')
    case,z=strategy.split('-z')
    config=json.loads((root/'parameters.json').read_text(encoding='utf-8'))
    require(set(config)=={'experiment_id','design','candidates','cases'},'invalid parameters')
    require(config['experiment_id']=='D18-v2-disclosed-mechanism','invalid experiment')
    require(config['design']=='fixed_candidates_no_selection_no_unseen_test','unsupported design')
    require(config['candidates']==list(Z_VALUES) and set(config['cases'])==set(CASES),'candidate or case mismatch')
    p=config['cases'][case]
    expected={'simulation','training_start_date','training_days','target_rounding_increment'}
    require(set(p)==expected,'unexpected case parameter')
    c=dict(p['simulation'])
    require('target_level' not in c,'target must be derived, not supplied')
    c['target_level']='0'
    validate_config(c)
    integer(p['training_days'],2)
    train=load_csv(root/'data'/f'{case}-training.csv')
    require(len(train)==p['training_days'],'wrong training horizon')
    train_c=dict(c, start_date=p['training_start_date'], days=p['training_days'])
    validate_config(train_c)
    values=[validate_row(row,train_c,i) for i,row in enumerate(train,1)]
    last_train=date.fromisoformat(train_c['start_date'])+timedelta(days=len(train)-1)
    require(last_train < date.fromisoformat(c['start_date']),'training must precede replay')
    mean,sigma=estimate(values,c['unit'])
    calculation=target(mean,sigma,c['review_interval']+c['lead_time'],z,c['unit'],p['target_rounding_increment'])
    c['target_level']=calculation['target_level']
    rows=load_csv(root/'data'/f'{case}-replay.csv')
    return c,rows,calculation


@exact_arithmetic
def service_metrics(ledger, interval, first_arrival):
    """Fixed scheduled-arrival windows, not outcome-selected actual-order cycles.

    Both service metrics use the same complete windows. Startup and partial tail
    days are excluded from both; all-window quantities are reported separately.
    """
    integer(interval,1)
    require(type(first_arrival) is int and 1 <= first_arrival <= 2001, 'invalid first planned arrival')
    if not isinstance(ledger,list) or not ledger:
        raise ValueError('nonempty ledger required')
    first=ledger[0]
    case=first.get('case')
    check_identity(first,case)
    normalized=[]
    for day,row in enumerate(ledger,1):
        check_identity(row,case)
        require(type(row['day']) is int and row['day']==day,'invalid metric day order')
        clean=dict(row)
        for key in ('demand','served','lost_sales'):
            clean[key]=number(row[key],first['unit'])
        require(clean['served']+clean['lost_sales']==clean['demand'],'metric conservation')
        normalized.append(clean)
    ledger=normalized
    cycles=[]
    for start in range(first_arrival,len(ledger)+1,interval):
        end=start+interval-1
        if end > len(ledger):
            break
        window=ledger[start-1:end]
        demand=sum((r['demand'] for r in window),D(0))
        served=sum((r['served'] for r in window),D(0))
        lost=sum((r['lost_sales'] for r in window),D(0))
        cycles.append({'cycle_index':len(cycles)+1,'start_day':start,'end_day':end,
                       'unit':first['unit'],'demand':demand,'served':served,
                       'lost_sales':lost,'no_stockout':lost==0,
                       'unit_fill_rate':ratio(served,demand)})
    demand=sum((c['demand'] for c in cycles),D(0))
    served=sum((c['served'] for c in cycles),D(0))
    successes=sum(c['no_stockout'] for c in cycles)
    included=[r['day'] for r in ledger if any(c['start_day']<=r['day']<=c['end_day'] for c in cycles)]
    metrics={'complete_cycles':len(cycles),'no_stockout_cycles':successes,
             'cycle_no_stockout_rate':ratio(successes,len(cycles)),
             'total_demand':demand,'total_served':served,'total_lost_sales':demand-served,
             'unit_fill_rate':ratio(served,demand),'included_days':included,
             'excluded_startup_days':[r['day'] for r in ledger if r['day']<first_arrival],
             'excluded_partial_tail_days':[r['day'] for r in ledger if r['day']>=first_arrival and r['day'] not in included],
             'zero_demand_cycles':sum(c['demand']==0 for c in cycles)}
    return metrics,cycles


def verify_release_code(root=ROOT):
    """Release code receipt; no circular self-hash and no automatic regeneration.

    check-d18.py separately pins this receipt. The package manifest covers it.
    This is release integrity, not evidence the code preceded data disclosure.
    """
    receipt=json.loads((root/'code_receipt.json').read_text(encoding='utf-8'))
    require(set(receipt)=={'stage','files'},'invalid code receipt')
    require(receipt['stage']=='release_code_after_development_review','invalid code receipt stage')
    require(set(receipt['files'])=={'run.py','inventory.py','test_safety_stock.py'},'code receipt coverage')
    for name,digest in receipt['files'].items():
        require(hashlib.sha256((root/name).read_bytes()).hexdigest()==digest,
                f'Released code changed: {name}. Review a new release; do not auto-refresh.')
    return receipt


def verify_frozen_inputs(root=ROOT):
    message='Frozen evidence changed; review a new experiment, never refresh this hash automatically.'
    receipt_bytes=(root/'freeze_receipt.json').read_bytes()
    require(hashlib.sha256(receipt_bytes).hexdigest()==FIXED_RECEIPT_SHA256,message)
    receipt=json.loads(receipt_bytes)
    require(set(receipt['files'])==set(SOURCE_NAMES),'frozen source coverage mismatch')
    require(receipt['unseen_test']=='not_created_not_read_not_run','no unseen-test claim permitted')
    for name,digest in receipt['files'].items():
        require(hashlib.sha256((root/name).read_bytes()).hexdigest()==digest,f'{message} {name}')
    return receipt


def main(root=ROOT):
    # No output is created until every frozen input is verified and all six
    # in-memory simulations finish. There is no final-test path or finalize mode.
    verify_release_code(root)
    receipt=verify_frozen_inputs(root)
    results={}
    summaries={}
    for strategy in STRATEGIES:
        c,rows,calculation=load_case(strategy,root)
        ledger,events=simulate(c,rows)
        service,cycles=service_metrics(ledger,c['review_interval'],c['first_review_day']+c['lead_time']+1)
        results[strategy]=(ledger,events,cycles)
        summaries[strategy]={'case':c['case'],'series':c['series'],'unit':c['unit'],
            'days':c['days'],'review_interval':c['review_interval'],'lead_time':c['lead_time'],
            'first_review_day':c['first_review_day'],'calculation':calculation,
            'service_complete_cycles':service,
            'all_window':{'total_demand':sum(r['demand'] for r in ledger),
                'total_served':sum(r['served'] for r in ledger),
                'total_lost_sales':sum(r['lost_sales'] for r in ledger),
                'initial_on_hand':c['initial_on_hand'],
                'initial_on_order':sum(number(o['quantity'],c['unit']) for o in c['initial_orders']),
                'total_arrivals':sum(r['arrivals'] for r in ledger),
                'total_new_orders':sum(r['order_quantity'] for r in ledger),
                'order_count':sum(r['order_quantity']>0 for r in ledger),
                'closing_on_hand':ledger[-1]['closing_on_hand'],
                'closing_on_order':ledger[-1]['on_order_after_order'],
                'closing_inventory_position':ledger[-1]['ip_after_order'],
                'closing_pending_orders':[{key:e[key] for key in ('order_id','placed_day','arrival_day','quantity')}
                    for e in events if e['event']!='arrival' and e['arrival_day']>c['days']]}}
    out=root/'results';out.mkdir(exist_ok=True)
    for strategy,(ledger,events,cycles) in results.items():
        write_csv(out/f'{strategy}-ledger.csv',ledger,LEDGER_FIELDS)
        write_csv(out/f'{strategy}-order-events.csv',events,EVENT_FIELDS)
        write_csv(out/f'{strategy}-cycles.csv',cycles,CYCLE_FIELDS)
    dump_json(out/'summary.json',{'experiment_id':'D18-v2-disclosed-mechanism',
        'boundary':'Disclosed specified paths; no selection, validation, unseen test, business gain or probability guarantee.',
        'freeze_receipt_sha256':FIXED_RECEIPT_SHA256,'input_sha256':receipt['files'],'strategies':summaries})
    names=[f'{s}-{kind}.csv' for s in STRATEGIES for kind in ('ledger','order-events','cycles')]+['summary.json']
    dump_json(out/'output_hashes.json',{name:hashlib.sha256((out/name).read_bytes()).hexdigest() for name in sorted(names)})
    print(json.dumps({'experiment':'D18','strategies':len(summaries),'unseen_test':'not_run'},ensure_ascii=False))


if __name__=='__main__':
    import sys
    if len(sys.argv)!=1:
        raise SystemExit('Usage: python run.py (no unseen-test or finalize command exists)')
    main()
