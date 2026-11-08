"""D15: deterministic, exact-decimal lost-sales teaching simulator; stdlib only."""
from pathlib import Path
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
import csv
import hashlib
import json

ROOT = Path(__file__).resolve().parent
LEDGER_FIELDS = ['case', 'series', 'unit', 'day', 'date', 'opening_on_hand',
                 'opening_on_order', 'arrivals', 'available_before_demand', 'demand',
                 'served', 'lost_sales', 'closing_on_hand', 'on_order_before_order',
                 'ip_before_order', 'order_quantity', 'on_order_after_order', 'ip_after_order']
EVENT_FIELDS = ['order_id', 'case', 'series', 'unit', 'placed_day', 'arrival_day',
                'quantity', 'event', 'event_day']
IDENTITIES = {'hewei': ('hewei/A/SKU01', 'kg'),
              'apparel': ('anonymous-apparel/terminal/SKU01', 'pieces')}


def number(value, unit):
    if isinstance(value, bool) or not isinstance(value, (str, int, float, Decimal)):
        raise ValueError('quantity must be numeric')
    try:
        n = Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError('invalid number') from exc
    if not n.is_finite() or n < 0 or n > Decimal('1000000'):
        raise ValueError('quantity must be finite, nonnegative and <= 1000000')
    # Bounded exact arithmetic, not a general arbitrary-precision inventory engine.
    if n != n.quantize(Decimal('0.001')):
        raise ValueError('at most three fractional places')
    if unit == 'pieces' and n != n.to_integral_value():
        raise ValueError('pieces must be whole numbers')
    return n


def integer(value, minimum=0):
    if type(value) is not int or value < minimum or value > 1000:
        raise ValueError('invalid integer parameter')
    return value


def check_identity(record, case):
    if case not in IDENTITIES or (record['series'], record['unit']) != IDENTITIES[case] or record['case'] != case:
        raise ValueError('case/series/unit mismatch')


def validate_config(c):
    required = {'case', 'series', 'unit', 'start_date', 'days', 'initial_on_hand',
                'lead_time', 'order_up_to', 'initial_orders', 'shortage_mode'}
    if set(c) != required or c['shortage_mode'] != 'lost_sales':
        raise ValueError('unsupported config: no backorders, partial arrivals or cancellations')
    check_identity(c, c['case'])
    start = date.fromisoformat(c['start_date'])
    if start.isoformat() != c['start_date']:
        raise ValueError('date must be YYYY-MM-DD')
    integer(c['days'], 1)
    integer(c['lead_time'])
    number(c['initial_on_hand'], c['unit'])
    number(c['order_up_to'], c['unit'])
    ids = set()
    for order in c['initial_orders']:
        if set(order) != {'order_id', 'case', 'series', 'unit', 'placed_day', 'arrival_day', 'quantity'}:
            raise ValueError('unsupported order fields')
        check_identity(order, c['case'])
        if not isinstance(order['order_id'], str) or not order['order_id'] or order['order_id'] in ids or order['order_id'].startswith('new-'):
            raise ValueError('duplicate/reserved/invalid order ID')
        ids.add(order['order_id'])
        if type(order['placed_day']) is not int or not -1000 <= order['placed_day'] <= 0:
            raise ValueError('initial order must precede day 1')
        integer(order['arrival_day'], 1)
        if order['arrival_day'] != order['placed_day'] + c['lead_time'] + 1:
            raise ValueError('arrival violates full waiting days')
        if number(order['quantity'], c['unit']) == 0:
            raise ValueError('order quantity must be positive')


def validate_row(r, c, day):
    if set(r) != {'case', 'series', 'unit', 'day', 'date', 'demand'}:
        raise ValueError('unexpected demand columns')
    check_identity(r, c['case'])
    if str(r['day']) != str(day) or r['date'] != (date.fromisoformat(c['start_date']) + timedelta(days=day-1)).isoformat():
        raise ValueError('missing, duplicate or invalid date/day')
    return number(r['demand'], c['unit'])


def decide_order(on_hand, on_order, target):
    """Decision receives only current state and a fixed target, never future demand."""
    return max(Decimal(0), target-on_hand-on_order)


def simulate(c, rows):
    validate_config(c)
    if len(rows) != c['days']:
        raise ValueError('wrong horizon')
    unit = c['unit']
    oh = number(c['initial_on_hand'], unit)
    target = number(c['order_up_to'], unit)
    pipeline = [dict(o, quantity=number(o['quantity'], unit)) for o in c['initial_orders']]
    ledger, events = [], []
    for o in pipeline:
        events.append(dict(o, event='initial_open', event_day=0))
    for day, r in enumerate(rows, 1):
        demand = validate_row(r, c, day)
        opening = oh
        pipe_open = sum((o['quantity'] for o in pipeline), Decimal(0))
        due = [o for o in pipeline if o['arrival_day'] == day]
        arrivals = sum((o['quantity'] for o in due), Decimal(0))
        for o in due:
            events.append(dict(o, event='arrival', event_day=day))
        pipeline = [o for o in pipeline if o['arrival_day'] > day]
        oh += arrivals
        available = oh
        served = min(oh, demand)
        lost = demand-served
        oh -= served
        pipe_before = sum((o['quantity'] for o in pipeline), Decimal(0))
        ip_before = oh+pipe_before  # Lost sales are NOT backorders.
        q = decide_order(oh, pipe_before, target)
        if q:
            o = {'order_id': f"new-{c['case']}-{day:03}", 'case': c['case'],
                 'series': c['series'], 'unit': unit, 'placed_day': day,
                 'arrival_day': day+c['lead_time']+1, 'quantity': q}
            pipeline.append(o)
            events.append(dict(o, event='placed', event_day=day))
        ledger.append({'case': c['case'], 'series': c['series'], 'unit': unit,
                       'day': day, 'date': r['date'], 'opening_on_hand': opening,
                       'opening_on_order': pipe_open, 'arrivals': arrivals,
                       'available_before_demand': available, 'demand': demand,
                       'served': served, 'lost_sales': lost, 'closing_on_hand': oh,
                       'on_order_before_order': pipe_before, 'ip_before_order': ip_before,
                       'order_quantity': q, 'on_order_after_order': pipe_before+q,
                       'ip_after_order': ip_before+q})
    audit(c, rows, ledger, events)
    return ledger, events


def require(condition, message):
    if not condition:
        raise ValueError(message)


def audit(c, rows, ledger, events):
    """Independent event replay plus conservation and fixed-rule checks."""
    validate_config(c)
    require(len(ledger) == len(rows) == c['days'], 'ledger horizon')
    orders, arrivals = {}, {}
    for event in events:
        require(set(event) == set(EVENT_FIELDS), 'unexpected event fields')
        check_identity(event, c['case'])
        oid = event['order_id']
        require(event['event'] in ('initial_open', 'placed', 'arrival'), 'unsupported event')
        require(event['arrival_day'] == event['placed_day']+c['lead_time']+1, 'early/late arrival schedule')
        number(event['quantity'], c['unit'])
        if event['event'] != 'arrival':
            require(oid not in orders, 'duplicate order')
            require(event['event_day'] == (0 if event['event'] == 'initial_open' else event['placed_day']), 'placement timestamp')
            require(event['event'] != 'placed' or 1 <= event['placed_day'] <= c['days'], 'placement outside horizon')
            orders[oid] = event
        else:
            require(oid in orders and oid not in arrivals, 'unknown/duplicate arrival')
            require(event['event_day'] == event['arrival_day'], 'early/late arrival event')
            for key in ('case', 'series', 'unit', 'placed_day', 'arrival_day', 'quantity'):
                require(event[key] == orders[oid][key], 'partial/altered arrival')
            arrivals[oid] = event
    expected_initial = {o['order_id']: o for o in c['initial_orders']}
    actual_initial = {oid: o for oid, o in orders.items() if o['event'] == 'initial_open'}
    require(expected_initial.keys() == actual_initial.keys(), 'initial pipeline mismatch')
    for oid, original in expected_initial.items():
        for key, value in original.items():
            require(actual_initial[oid][key] == (number(value, c['unit']) if key == 'quantity' else value), 'initial order changed')
    for oid, o in orders.items():
        require((oid in arrivals) == (o['arrival_day'] <= c['days']), 'missing or out-of-horizon receipt')
    previous_oh = number(c['initial_on_hand'], c['unit'])
    for day, (r, row) in enumerate(zip(rows, ledger), 1):
        require(set(row) == set(LEDGER_FIELDS), 'unexpected ledger fields')
        check_identity(row, c['case'])
        demand = validate_row(r, c, day)
        require(row['day'] == day and row['date'] == r['date'], 'ledger date')
        receipt = sum((o['quantity'] for o in orders.values() if o['arrival_day'] == day), Decimal(0))
        pipe = sum((o['quantity'] for o in orders.values() if o['placed_day'] < day < o['arrival_day']), Decimal(0))
        placed = [o for o in orders.values() if o['placed_day'] == day]
        require(len(placed) <= 1, 'duplicate daily orders')
        q = sum((o['quantity'] for o in placed), Decimal(0))
        served = min(previous_oh+receipt, demand)
        closing = previous_oh+receipt-served
        before = closing+pipe
        expected = {'opening_on_hand': previous_oh, 'opening_on_order': pipe+receipt,
                    'arrivals': receipt, 'available_before_demand': previous_oh+receipt,
                    'demand': demand, 'served': served, 'lost_sales': demand-served,
                    'closing_on_hand': closing, 'on_order_before_order': pipe,
                    'ip_before_order': before, 'order_quantity': q,
                    'on_order_after_order': pipe+q, 'ip_after_order': before+q}
        require(q == max(Decimal(0), number(c['order_up_to'], c['unit'])-before), 'fixed order-up-to rule violated')
        for key, value in expected.items():
            require(row[key] == value, f'day {day}: {key} violates conservation')
        previous_oh = closing


def json_ready(obj):
    if isinstance(obj, Decimal):
        return int(obj) if obj == obj.to_integral_value() else float(obj)
    if isinstance(obj, dict):
        return {k: json_ready(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [json_ready(v) for v in obj]
    return obj


def dump_json(path, obj):
    path.write_text(json.dumps(json_ready(obj), ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8')


def write_csv(path, records, fields):
    with path.open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator='\n')
        writer.writeheader()
        writer.writerows(records)


def load_case(case):
    config = json.loads((ROOT/'parameters.json').read_text(encoding='utf-8'))[case]
    with (ROOT/'data'/f'{case}-demand.csv').open(encoding='utf-8', newline='') as f:
        rows = list(csv.DictReader(f))
    return config, rows


def main():
    manifest = json.loads((ROOT/'source_manifest.json').read_text(encoding='utf-8'))
    for name, digest in manifest['files'].items():
        require(hashlib.sha256((ROOT/name).read_bytes()).hexdigest() == digest, f'input hash mismatch: {name}')
    out = ROOT/'results'
    out.mkdir(exist_ok=True)
    summaries = {}
    for case in IDENTITIES:
        c, rows = load_case(case)
        ledger, events = simulate(c, rows)
        write_csv(out/f'{case}-ledger.csv', ledger, LEDGER_FIELDS)
        write_csv(out/f'{case}-order-events.csv', events, EVENT_FIELDS)
        summaries[case] = {'series': c['series'], 'unit': c['unit'], 'days': c['days'],
                           'total_demand': sum(r['demand'] for r in ledger),
                           'total_served': sum(r['served'] for r in ledger),
                           'total_lost_sales': sum(r['lost_sales'] for r in ledger),
                           'total_new_orders': sum(r['order_quantity'] for r in ledger),
                           'closing_on_hand': ledger[-1]['closing_on_hand'],
                           'closing_on_order': ledger[-1]['on_order_after_order'],
                           'closing_inventory_position': ledger[-1]['ip_after_order'],
                           'closing_pending_orders': [
                               {key: e[key] for key in ('order_id', 'arrival_day', 'quantity')}
                               for e in events if e['event'] != 'arrival'
                               and e['arrival_day'] > c['days']]}
    dump_json(out/'summary.json', {'run_id': 'D15-v1-new-seven-day-teaching-fixture',
        'boundary': 'Fixed seven-day arithmetic example, not statistical evaluation or business benefit evidence.',
        'cases': summaries, 'input_sha256': manifest['files']})
    dump_json(out/'output_hashes.json', {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(out.iterdir()) if p.name != 'output_hashes.json' and p.is_file()})
    print(json.dumps(json_ready(summaries), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
