"""D16: deterministic, exact-decimal lost-sales teaching simulator; stdlib only."""
from pathlib import Path
from datetime import date, timedelta
from decimal import (Decimal, InvalidOperation, DivisionByZero, Overflow, Context,
                     localcontext, ROUND_HALF_EVEN)
from functools import wraps
import csv
import hashlib
import json

ROOT = Path(__file__).resolve().parent
FIXED_MANIFEST_SHA256 = '756c71c22c95b0ba789fc120d82185c83532d6a6900093368a82908761258761'
STRATEGIES = ('hewei-q6', 'hewei-q12', 'apparel-q6', 'apparel-q12')
MAX_INITIAL_ORDERS = 1000
# <= 1000 initial orders + 1000 daily orders + one initial stock quantity,
# each <= 1,000,000. Three decimal places require at most 13 significant digits.
MAX_STATE = Decimal('2001000000')
# Direct policy inputs each use MAX_STATE, so their sum <= 4,002,000,000,
# still only 13 significant digits at mill-unit precision. 16 is sufficient.
EXACT_CONTEXT = Context(prec=16, rounding=ROUND_HALF_EVEN, Emin=-999999,
                        Emax=999999, capitals=1, clamp=0, flags=[],
                        traps=[InvalidOperation, DivisionByZero, Overflow])


def exact_arithmetic(function):
    """Fresh explicit context; caller precision, rounding, flags and traps cannot leak."""
    @wraps(function)
    def wrapped(*args, **kwargs):
        with localcontext(EXACT_CONTEXT):
            return function(*args, **kwargs)
    return wrapped

LEDGER_FIELDS = ['case', 'series', 'unit', 'day', 'date', 'opening_on_hand',
                 'opening_on_order', 'arrivals', 'available_before_demand', 'demand',
                 'served', 'lost_sales', 'closing_on_hand', 'on_order_before_order',
                 'ip_before_order', 'order_quantity', 'on_order_after_order', 'ip_after_order']
EVENT_FIELDS = ['order_id', 'case', 'series', 'unit', 'placed_day', 'arrival_day',
                'quantity', 'event', 'event_day']
IDENTITIES = {'hewei': ('hewei/A/SKU01', 'kg'),
              'apparel': ('anonymous-apparel/terminal/SKU01', 'pieces')}


def number(value, unit, maximum=Decimal('1000000')):
    if unit not in ('kg', 'pieces'):
        raise ValueError('unknown unit')
    if isinstance(value, bool) or not isinstance(value, (str, int, float, Decimal)):
        raise ValueError('quantity must be numeric')
    try:
        n = Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError('invalid number') from exc
    if not n.is_finite() or n < 0 or n > maximum:
        raise ValueError(f'quantity must be finite, nonnegative and <= {maximum}')
    # Inspect the exact coefficient, never multiply/normalize under a rounding
    # context: those operations can hide a tiny nonzero fractional tail.
    digits = n.as_tuple().digits
    exponent = n.as_tuple().exponent
    if any(digits):
        trailing_zeros = 0
        for digit in reversed(digits):
            if digit != 0:
                break
            trailing_zeros += 1
        fractional_places = max(0, -exponent - trailing_zeros)
    else:
        fractional_places = 0
    if fractional_places > 3:
        raise ValueError('at most three fractional places')
    if unit == 'pieces' and fractional_places > 0:
        raise ValueError('pieces must be whole numbers')
    # Canonicalize from the exact tuple, without context-sensitive normalize().
    if not any(digits):
        return Decimal(0)
    significant_digits = digits[:-trailing_zeros] if trailing_zeros else digits
    return Decimal((0, significant_digits, exponent + trailing_zeros))


def integer(value, minimum=0):
    if type(value) is not int or value < minimum or value > 1000:
        raise ValueError('invalid integer parameter')
    return value


def check_identity(record, case):
    if not isinstance(record, dict) or not isinstance(case, str) or not {'case', 'series', 'unit'} <= set(record):
        raise ValueError('invalid identity fields')
    if case not in IDENTITIES or (record['series'], record['unit']) != IDENTITIES[case] or record['case'] != case:
        raise ValueError('case/series/unit mismatch')


def validate_config(c):
    required = {'case', 'series', 'unit', 'start_date', 'days', 'initial_on_hand',
                'lead_time', 'fixed_quantity', 'reorder_point', 'initial_orders', 'shortage_mode'}
    if not isinstance(c, dict) or set(c) != required or c['shortage_mode'] != 'lost_sales':
        raise ValueError('unsupported config: no backorders, partial arrivals or cancellations')
    check_identity(c, c['case'])
    if not isinstance(c['start_date'], str):
        raise ValueError('invalid start date')
    start = date.fromisoformat(c['start_date'])
    if start.isoformat() != c['start_date']:
        raise ValueError('date must be YYYY-MM-DD')
    integer(c['days'], 1)
    integer(c['lead_time'])
    number(c['initial_on_hand'], c['unit'])
    number(c['reorder_point'], c['unit'])
    if number(c['fixed_quantity'], c['unit']) <= 0:
        raise ValueError('fixed quantity must be positive')
    if not isinstance(c['initial_orders'], list):
        raise ValueError('initial_orders must be a list')
    if len(c['initial_orders']) > MAX_INITIAL_ORDERS:
        raise ValueError('at most 1000 initial orders')
    ids = set()
    for order in c['initial_orders']:
        if not isinstance(order, dict) or set(order) != {'order_id', 'case', 'series', 'unit', 'placed_day', 'arrival_day', 'quantity'}:
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
    if not isinstance(r, dict) or set(r) != {'case', 'series', 'unit', 'day', 'date', 'demand'}:
        raise ValueError('unexpected demand columns')
    check_identity(r, c['case'])
    if str(r['day']) != str(day) or r['date'] != (date.fromisoformat(c['start_date']) + timedelta(days=day-1)).isoformat():
        raise ValueError('missing, duplicate or invalid date/day')
    return number(r['demand'], c['unit'])


@exact_arithmetic
def order_qr(on_hand, on_order, fixed_quantity, reorder_point):
    """Pure policy on validated Decimal state; no production idempotency guarantee.

    The simulator invokes once per unique day, not continuously or in a while loop.
    Real repeat scheduling needs persistent idempotent writes, not this function.
    """
    on_hand = number(on_hand, 'kg', MAX_STATE)
    on_order = number(on_order, 'kg', MAX_STATE)
    fixed_quantity = number(fixed_quantity, 'kg')
    reorder_point = number(reorder_point, 'kg')
    if fixed_quantity <= 0:
        raise ValueError('fixed quantity must be positive')
    return fixed_quantity if on_hand + on_order <= reorder_point else Decimal(0)


@exact_arithmetic
def simulate(c, rows):
    validate_config(c)
    if not isinstance(rows, list) or len(rows) != c['days']:
        raise ValueError('wrong horizon')
    unit = c['unit']
    oh = number(c['initial_on_hand'], unit)
    fixed_quantity = number(c['fixed_quantity'], unit)
    reorder_point = number(c['reorder_point'], unit)
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
        q = order_qr(oh, pipe_before, fixed_quantity, reorder_point)
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


@exact_arithmetic
def audit(c, rows, ledger, events):
    """Independent event replay plus conservation and fixed-rule checks."""
    validate_config(c)
    require(len(ledger) == len(rows) == c['days'], 'ledger horizon')
    orders, arrivals = {}, {}
    previous_event_key = (-1, -1)
    for event in events:
        require(isinstance(event, dict) and set(event) == set(EVENT_FIELDS), 'unexpected event fields')
        check_identity(event, c['case'])
        oid = event['order_id']
        require(event['event'] in ('initial_open', 'placed', 'arrival'), 'unsupported event')
        require(event['arrival_day'] == event['placed_day']+c['lead_time']+1, 'early/late arrival schedule')
        require(number(event['quantity'], c['unit']) > 0, 'event quantity must be positive')
        require(type(event['placed_day']) is int and -1000 <= event['placed_day'] <= c['days'], 'invalid placed day')
        require(type(event['arrival_day']) is int and 1 <= event['arrival_day'] <= c['days']+c['lead_time']+1, 'invalid arrival day')
        require(type(event['event_day']) is int and 0 <= event['event_day'] <= c['days'], 'invalid event day')
        require(isinstance(oid, str) and bool(oid), 'invalid event order ID')
        event_key = (event['event_day'], {'initial_open': 0, 'arrival': 1, 'placed': 2}[event['event']])
        require(event_key >= previous_event_key, 'event sequence violates daily order')
        previous_event_key = event_key
        if event['event'] != 'arrival':
            require(oid not in orders, 'duplicate order')
            require(event['event_day'] == (0 if event['event'] == 'initial_open' else event['placed_day']), 'placement timestamp')
            require(event['event'] != 'placed' or (1 <= event['placed_day'] <= c['days'] and oid == f"new-{c['case']}-{event['placed_day']:03}"), 'placement outside horizon or unstable order key')
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
        require(isinstance(row, dict) and set(row) == set(LEDGER_FIELDS), 'unexpected ledger fields')
        check_identity(row, c['case'])
        demand = validate_row(r, c, day)
        require(type(row['day']) is int and row['day'] == day and row['date'] == r['date'], 'ledger date')
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
        require(q == (number(c['fixed_quantity'], c['unit']) if before <= number(c['reorder_point'], c['unit']) else Decimal(0)), 'fixed batch threshold rule violated')
        for key, value in expected.items():
            require(not isinstance(row[key], bool) and row[key] == value, f'day {day}: {key} violates conservation')
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


def load_case(strategy):
    if strategy not in STRATEGIES:
        raise ValueError('unknown strategy')
    config = json.loads((ROOT/'frozen_policy.json').read_text(encoding='utf-8'))['parameters'][strategy]
    with (ROOT/'data'/f"{config['case']}-demand.csv").open(encoding='utf-8', newline='') as f:
        rows = list(csv.DictReader(f))
    return config, rows


def verify_frozen_inputs():
    path = ROOT/'source_manifest.json'
    message = 'Frozen input changed; create and review a separate experiment, never refresh this run hash.'
    require(hashlib.sha256(path.read_bytes()).hexdigest() == FIXED_MANIFEST_SHA256, message)
    manifest = json.loads(path.read_text(encoding='utf-8'))
    for name, digest in manifest['files'].items():
        require(hashlib.sha256((ROOT/name).read_bytes()).hexdigest() == digest, f'{message} File: {name}')
    return manifest


def main():
    # Verification must finish before creating or modifying any output.
    manifest = verify_frozen_inputs()
    out = ROOT/'results'
    out.mkdir(exist_ok=True)
    summaries = {}
    for strategy in STRATEGIES:
        c, rows = load_case(strategy)
        ledger, events = simulate(c, rows)
        write_csv(out/f'{strategy}-ledger.csv', ledger, LEDGER_FIELDS)
        write_csv(out/f'{strategy}-order-events.csv', events, EVENT_FIELDS)
        summaries[strategy] = {'case': c['case'], 'series': c['series'], 'unit': c['unit'], 'days': c['days'],
                           'fixed_quantity': c['fixed_quantity'], 'reorder_point': c['reorder_point'],
                           'lead_time': c['lead_time'],
                           'total_demand': sum(r['demand'] for r in ledger),
                           'total_served': sum(r['served'] for r in ledger),
                           'total_lost_sales': sum(r['lost_sales'] for r in ledger),
                           'total_arrivals': sum(r['arrivals'] for r in ledger),
                           'order_count': sum(r['order_quantity'] > 0 for r in ledger),
                           'total_new_orders': sum(r['order_quantity'] for r in ledger),
                           'closing_on_hand': ledger[-1]['closing_on_hand'],
                           'closing_on_order': ledger[-1]['on_order_after_order'],
                           'closing_inventory_position': ledger[-1]['ip_after_order'],
                           'closing_pending_orders': [
                               {key: e[key] for key in ('order_id', 'placed_day', 'arrival_day', 'quantity')}
                               for e in events if e['event'] != 'arrival'
                               and e['arrival_day'] > c['days']]}
    dump_json(out/'summary.json', {'run_id': 'D16-v1-seven-day-fixed-batch',
        'boundary': 'Fixed seven-day mechanism example, not statistical evaluation or business benefit evidence.',
        'strategies': summaries, 'input_sha256': manifest['files'],
        'source_manifest_sha256': FIXED_MANIFEST_SHA256})
    names = [f'{s}-{kind}.csv' for s in STRATEGIES for kind in ('ledger', 'order-events')] + ['summary.json']
    dump_json(out/'output_hashes.json', {name: hashlib.sha256((out/name).read_bytes()).hexdigest()
        for name in sorted(names)})
    print(json.dumps(json_ready(summaries), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
