"""D19 development-only replay. Python standard library, no sealed-data entry point."""
import csv
import hashlib
import io
import json
import math
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCES = {'hewei': '292072a63439529f22a73d41b83516928ae5a5b474b907b33d42e74962c23407',
           'apparel': '56badd2fc37decd72b2f55a980acb7add2594b96c7b8d269f6aaae59ee7d47e5'}

def canonical(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + '\n'

def digest(data):
    return hashlib.sha256(data).hexdigest()

def integer(value, name, minimum=0):
    if type(value) is not int or value < minimum:
        raise ValueError(name + ' must be an integer >= ' + str(minimum))
    return value

def load_data(case):
    raw = (ROOT / 'data' / (case + '-development.csv')).read_bytes()
    if digest(raw) != SOURCES[case]:
        raise ValueError('development data hash mismatch')
    rows = list(csv.DictReader(io.StringIO(raw.decode())))
    if len(rows) != 140:
        raise ValueError('exactly 140 development rows required')
    first = date.fromisoformat(rows[0]['date'])
    result = []
    for day, row in enumerate(rows, 1):
        if (set(row) != {'day', 'date', 'demand', 'split'} or int(row['day']) != day
                or date.fromisoformat(row['date']) != first + timedelta(days=day-1)
                or row['split'] != ('train' if day <= 112 else 'validation')):
            raise ValueError('invalid development schema, dates or split')
        result.append(integer(int(row['demand']), 'demand'))
    return result

def forecast(history, horizon):
    integer(horizon, 'horizon', 1)
    if len(history) < 7:
        raise ValueError('need seven observed raw demands')
    for value in history:
        integer(value, 'history demand')
    return [history[-7 + h % 7] for h in range(horizon)]

def error_scale(train, horizon):
    if len(train) != 112:
        raise ValueError('training block must have 112 observations')
    errors = [sum(train[o:o+horizon]) - sum(forecast(train[:o], horizon))
              for o in range(7, 113-horizon)]
    return math.sqrt(sum(e*e for e in errors)/len(errors)), len(errors)

def simulate(demands, history, params, initial_oh, initial_pipeline=(), start=113):
    integer(start, 'start', 1)
    integer(initial_oh, 'initial OH')
    if not demands:
        raise ValueError('empty demand block')
    for value in demands:
        integer(value, 'raw demand')
    if params.get('policy') not in ('daily_sQ', 'periodic_RS'):
        raise ValueError('unsupported policy')
    L = integer(params['L'], 'L')
    R = integer(params['R'], 'R', 1)
    if params['policy'] == 'daily_sQ' and R != 1:
        raise ValueError('daily review requires R=1')
    if 'fixed_threshold' in params:
        integer(params['fixed_threshold'], 'fixed threshold')
    else:
        z, scale = params['z'], params['scale']
        if (isinstance(z, bool) or isinstance(scale, bool) or not isinstance(z, (int, float))
                or not isinstance(scale, (int, float)) or not math.isfinite(z)
                or not math.isfinite(scale) or z < 0 or scale < 0):
            raise ValueError('invalid safety parameters')
        forecast(history, L+R)
    if params['policy'] == 'daily_sQ':
        integer(params['Q'], 'Q', 1)
    pending, seen = [], set()
    for order in initial_pipeline:
        order = dict(order)
        if not isinstance(order['id'], str) or not order['id'] or order['id'] in seen:
            raise ValueError('duplicate or invalid order id')
        integer(order['arrival_day'], 'initial arrival', start)
        integer(order['quantity'], 'initial quantity', 1)
        seen.add(order['id'])
        pending.append(order)
    oh, ledger, events, observed = initial_oh, [], [], list(history)
    for offset, demand in enumerate(demands):
        day = start + offset
        arriving = [o for o in pending if o['arrival_day'] == day]
        pending = [o for o in pending if o['arrival_day'] != day]
        arrivals = sum(o['quantity'] for o in arriving)
        events.extend(dict(event='arrival', day=day, **o) for o in arriving)
        opening = oh
        oh += arrivals
        fulfilled = min(oh, demand)
        oh -= fulfilled
        observed.append(demand)  # Exogenous demand is observed even when stockout occurs.
        oo = sum(o['quantity'] for o in pending)
        ip = oh + oo
        review = offset % R == 0
        target = (params['fixed_threshold'] if 'fixed_threshold' in params else
                  math.ceil(sum(forecast(observed, L+R)) + params['z'] * params['scale']))
        q = 0
        if review:
            if params['policy'] == 'daily_sQ':
                q = params['Q'] if ip <= target else 0
            else:
                q = max(0, target-ip)
        if q:
            order = {'id': 'new-' + str(day), 'quantity': q, 'arrival_day': day+L+1}
            if order['id'] in seen:
                raise ValueError('duplicate order id')
            seen.add(order['id'])
            pending.append(order)
            events.append(dict(event='placed', day=day, **order))
        ledger.append(dict(day=day, opening_oh=opening, arrivals=arrivals, demand=demand,
                           fulfilled=fulfilled, lost=demand-fulfilled, end_oh=oh,
                           pipeline_before=oo, ip_before=ip, review=int(review),
                           threshold=target, ordered=q, arrival_day=day+L+1 if q else '',
                           pipeline_after=oo+q, ip_after=ip+q))
    summary = dict(demand=sum(demands), fulfilled=sum(r['fulfilled'] for r in ledger),
                   lost=sum(r['lost'] for r in ledger), mean_end_oh=sum(r['end_oh'] for r in ledger)/len(ledger),
                   order_count=sum(r['ordered'] > 0 for r in ledger), ordered=sum(r['ordered'] for r in ledger),
                   arrivals=sum(r['arrivals'] for r in ledger), end_oh=oh,
                   end_pipeline=sum(o['quantity'] for o in pending))
    summary['fill_rate'] = summary['fulfilled']/summary['demand'] if summary['demand'] else None
    return ledger, events, sorted(pending, key=lambda o: (o['arrival_day'], o['id'])), summary

def csv_bytes(rows, fields):
    stream = io.StringIO(newline='')
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator='\n')
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode()

def build():
    protocol = json.loads((ROOT/'protocol.json').read_text())
    all_ledger, all_events, all_pending, ranking, parameters, manual = [], [], [], [], [], []
    frozen = {'version': protocol['version'], 'protocol_sha256': digest((ROOT/'protocol.json').read_bytes()),
              'sources': SOURCES, 'future_plan': protocol['future_plan'], 'cases': {},
              'forecast': protocol['forecast'], 'timing': protocol['timing'],
              'rounding': protocol['rounding'], 'selection': protocol['selection'],
              'validation_review_anchor': 113, 'protection_horizons': {'daily_sQ': 3, 'periodic_RS': 5}}
    scales = {}
    training_errors = []
    for case in SOURCES:
        data = load_data(case)
        train = data[:112]
        mean = sum(train)/112
        initial = math.ceil(3*mean)
        unit = 'kg' if case == 'hewei' else 'piece'
        scales[case] = {}
        candidates = []
        for policy, R in [('daily_sQ', 1), ('periodic_RS', 3)]:
            scale, n = error_scale(train, 2+R)
            errors = [sum(train[o:o+2+R])-sum(forecast(train[:o], 2+R)) for o in range(7,113-(2+R))]
            scales[case][policy] = dict(horizon=2+R, rms=scale, mean_error=sum(errors)/len(errors), n=n, first_origin=7, last_origin=112-(2+R))
            for origin in range(7, 113-(2+R)):
                actual = sum(train[origin:origin+2+R])
                predicted = sum(forecast(train[:origin], 2+R))
                training_errors.append(dict(case=case, unit=unit, horizon=2+R, origin=origin,
                    target_start=origin+1, target_end=origin+2+R, actual_sum=actual,
                    forecast_sum=predicted, error=actual-predicted))
            for z in protocol['z_grid']:
                for multiple in (protocol['q_mean_multipliers'] if R == 1 else [None]):
                    p = dict(policy=policy, R=R, L=2, z=z, scale=scale)
                    if multiple is not None:
                        p['Q'] = math.ceil(multiple*mean)
                    candidates.append(p)
        winners = {}
        for p in candidates:
            key = p['policy'] + '-z' + str(p['z']) + ('-Q'+str(p['Q']) if 'Q' in p else '')
            ledger, events, pending, summary = simulate(data[112:], train, p, initial)
            prefix = dict(case=case, unit=unit, candidate=key)
            all_ledger.extend(dict(**prefix, **r) for r in ledger)
            all_events.extend(dict(**prefix, **r) for r in events)
            all_pending.extend(dict(**prefix, **r) for r in pending)
            row = dict(**prefix, **summary, parameters=p)
            ranking.append(row)
            parameters.append(dict(**prefix, **p, initial_oh=initial, initial_pipeline=[]))
        for policy in ('daily_sQ', 'periodic_RS'):
            group = sorted([r for r in ranking if r['case'] == case and r['parameters']['policy'] == policy],
                           key=lambda r: (r['lost'], r['mean_end_oh'], r['order_count'], canonical(r['parameters'])))
            for rank, row in enumerate(group, 1):
                row['rank_within_policy'] = rank
            winners[policy] = dict(candidate=group[0]['candidate'], parameters=group[0]['parameters'])
        frozen['cases'][case] = dict(unit=unit, initial_oh=initial, initial_pipeline=[], winners=winners)
    # Independent seven-day mechanics fixtures, not training or selection evidence.
    for case, demand, oh, pipeline, threshold, Q in [
        ('hewei', [7,9,8,4,5,6,3], 12, [{'id':'initial','quantity':8,'arrival_day':2}],10,6),
        ('apparel',[5,8,4,7,3,6,2],6,[{'id':'initial','quantity':4,'arrival_day':1}],8,6)]:
        for policy, R, target in [('daily_sQ',1,threshold), ('periodic_RS',3,20 if case=='hewei' else 18)]:
            p=dict(policy=policy,R=R,L=2,Q=Q,fixed_threshold=target)
            ledger, events, pending, summary=simulate(demand, [], p, oh, pipeline, start=1)
            manual.append(dict(case=case, parameters=p, initial_oh=oh, initial_pipeline=pipeline,
                               ledger=ledger, events=events, pending=pending, summary=summary))
    output = {'frozen_config.json': canonical(frozen).encode(), 'results.json': canonical(ranking).encode(),
              'parameters.json': canonical(parameters).encode(), 'training_scales.json': canonical(scales).encode(),
              'manual_seven_days.json': canonical(manual).encode()}
    for name, rows, fallback in [('ledger.csv',all_ledger,[]), ('order_events.csv',all_events,[]), ('pending.csv',all_pending,[])]:
        output[name] = csv_bytes(rows,list(rows[0]) if rows else fallback)
    output['training_errors.csv'] = csv_bytes(training_errors, list(training_errors[0]))
    output['freeze_receipt.json'] = canonical({'version':protocol['version'], 'frozen_config_sha256':digest(output['frozen_config.json']),
        'protocol_sha256':digest((ROOT/'protocol.json').read_bytes()), 'selection_results_sha256':digest(output['results.json']),
        'status':'development selected; no D20 execution; no external timestamp or tamper-proof guarantee'}).encode()
    return output

def verify():
    manifest = json.loads((ROOT/'manifest.json').read_text())
    for name, expected in manifest.items():
        if digest((ROOT/name).read_bytes()) != expected:
            raise ValueError('integrity mismatch: ' + name)
    result = build()
    for name, data in result.items():
        if data != (ROOT/'output'/name).read_bytes():
            raise ValueError('replay mismatch: ' + name)
    return result

if __name__ == '__main__':
    result = verify()
    print('D19 verified: 18 candidates, 504 daily rows, 4 frozen policy configurations; D20 not run.')
