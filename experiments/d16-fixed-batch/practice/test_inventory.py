"""Independent hand checks, adversarial records, metamorphic and CLI tests."""
import copy
import csv
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from decimal import Decimal as D, localcontext, ROUND_UP, ROUND_DOWN, ROUND_FLOOR
from run import (ROOT, STRATEGIES, EVENT_FIELDS, load_case, simulate, audit,
                 order_qr, number, write_csv, verify_frozen_inputs)


class InventoryTests(unittest.TestCase):
    def setUp(self):
        self.c, self.rows = load_case('hewei-q6')
        self.ledger, self.events = simulate(self.c, self.rows)

    def test_hewei_q6_all_days_hand_calculation(self):
        expected = {
            'arrivals': [0,8,0,0,6,6,0], 'served': [7,9,4,0,5,6,1],
            'lost_sales': [0,0,4,4,0,0,2], 'closing_on_hand': [5,4,0,0,1,1,0],
            'on_order_before_order': [8,0,6,12,6,6,12],
            'ip_before_order': [13,4,6,12,7,7,12],
            'order_quantity': [0,6,6,0,6,6,0],
            'on_order_after_order': [8,6,12,12,12,12,12],
            'ip_after_order': [13,10,12,12,13,13,12]}
        for key, values in expected.items():
            self.assertEqual([r[key] for r in self.ledger], values, key)

    def test_hewei_q12_all_days_hand_calculation(self):
        ledger, _ = simulate(*load_case('hewei-q12'))
        expected = {
            'arrivals': [0,8,0,0,12,0,0], 'served': [7,9,4,0,5,6,1],
            'lost_sales': [0,0,4,4,0,0,2], 'closing_on_hand': [5,4,0,0,7,1,0],
            'on_order_before_order': [8,0,12,12,0,12,12],
            'ip_before_order': [13,4,12,12,7,13,12],
            'order_quantity': [0,12,0,0,12,0,0],
            'on_order_after_order': [8,12,12,12,12,12,12],
            'ip_after_order': [13,16,12,12,19,13,12]}
        for key, values in expected.items():
            self.assertEqual([r[key] for r in ledger], values, key)

    def test_apparel_hand_calculation(self):
        expected = {
            'apparel-q6': ([6,6,6,6,0,6,6], [5,0,2,1,4,4,2]),
            'apparel-q12': ([12,0,12,0,0,12,0], [5,0,8,1,10,4,2])}
        for strategy, (q, oh) in expected.items():
            ledger, _ = simulate(*load_case(strategy))
            self.assertEqual([r['order_quantity'] for r in ledger], q)
            self.assertEqual([r['closing_on_hand'] for r in ledger], oh)
            self.assertEqual([r['lost_sales'] for r in ledger], [0,3,0,0,0,0,0])

    def test_threshold_below_equal_above(self):
        for ip, expected in [('9.999',6), ('10',6), ('10.001',0)]:
            self.assertEqual(order_qr(D(ip), D(0), D(6), D(10)), expected)

    def test_inventory_position_not_only_on_hand(self):
        self.assertEqual(order_qr(D(5), D(8), D(6), D(10)), 0)
        self.assertEqual(order_qr(D(5), D(0), D(6), D(10)), 6)

    def test_pure_policy_does_not_provide_idempotency(self):
        # The same arguments produce the same Q again. Callers must deduplicate writes.
        for _ in range(3):
            self.assertEqual(order_qr(D(3), D(0), D(6), D(10)), 6)

    def test_no_repeat_even_when_postorder_still_below_r(self):
        c = dict(self.c, initial_on_hand=3, initial_orders=[], days=1)
        rows = [dict(self.rows[0], demand='0')]
        ledger, events = simulate(c, rows)
        self.assertEqual(ledger[0]['ip_after_order'], 9)
        self.assertEqual(ledger[0]['order_quantity'], 6)
        self.assertEqual(len(events), 1)

    def test_no_repeat_even_when_postorder_equals_r(self):
        self.assertEqual(self.ledger[1]['ip_after_order'],10)
        self.assertEqual(sum(e['event']=='placed' and e['event_day']==2 for e in self.events),1)

    def test_undershoot_not_assumed_equal_to_r(self):
        self.assertEqual(self.ledger[0]['ip_before_order'],13)
        self.assertEqual(self.ledger[1]['ip_before_order'],4)
        self.assertEqual(self.ledger[1]['ip_after_order'],10)
        self.assertNotEqual(self.ledger[1]['ip_after_order'],16)

    def test_one_order_per_day_all_strategies(self):
        for strategy in STRATEGIES:
            c,rows=load_case(strategy); ledger,events=simulate(c,rows)
            self.assertTrue(all(r['order_quantity'] in (0,c['fixed_quantity']) for r in ledger))
            days=[e['event_day'] for e in events if e['event']=='placed']
            self.assertEqual(len(days),len(set(days)))

    def test_total_material_conservation(self):
        for strategy in STRATEGIES:
            c,rows=load_case(strategy); ledger,_=simulate(c,rows)
            self.assertEqual(c['initial_on_hand']+sum(r['arrivals']-r['served'] for r in ledger),ledger[-1]['closing_on_hand'])
            self.assertEqual(sum(o['quantity'] for o in c['initial_orders'])+sum(r['order_quantity']-r['arrivals'] for r in ledger),ledger[-1]['on_order_after_order'])
            self.assertEqual(sum(r['demand'] for r in ledger),sum(r['served']+r['lost_sales'] for r in ledger))

    def test_receipts_before_demand_and_remove_pipeline(self):
        self.assertEqual(self.ledger[1]['served'],9)  # Opening OH is only 5; receipt is usable.
        self.assertEqual(self.ledger[1]['on_order_before_order'],0)
        for row in self.ledger:
            self.assertEqual(row['opening_on_hand']+row['opening_on_order'],row['available_before_demand']+row['on_order_before_order'])

    def test_new_order_cannot_serve_same_day(self):
        self.assertEqual(self.ledger[2]['order_quantity'],6)
        self.assertEqual(self.ledger[2]['lost_sales'],4)

    def test_lost_sales_not_backorders(self):
        self.assertEqual(self.ledger[2]['ip_before_order'],6)
        self.assertEqual(self.ledger[3]['ip_before_order'],12)
        self.assertEqual(self.ledger[4]['served'],5)
        bad=copy.deepcopy(self.ledger);bad[2]['ip_before_order']-=4
        with self.assertRaises(ValueError): audit(self.c,self.rows,bad,self.events)

    def test_future_demand_prefix_invariance(self):
        for strategy in STRATEGIES:
            c,rows=load_case(strategy);ledger,_=simulate(c,rows)
            for cutoff in range(1,7):
                altered=copy.deepcopy(rows)
                for r in altered[cutoff:]:r['demand']='999'
                changed,_=simulate(c,altered)
                self.assertEqual(changed[:cutoff],ledger[:cutoff])

    def test_prefix_horizon_invariance(self):
        for cutoff in range(1,8):
            ledger,_=simulate(dict(self.c,days=cutoff),self.rows[:cutoff])
            self.assertEqual(ledger,self.ledger[:cutoff])

    def test_scaling_quantities_preserves_decision_days(self):
        c=copy.deepcopy(self.c)
        for key in ('initial_on_hand','fixed_quantity','reorder_point'):c[key]*=2
        for o in c['initial_orders']:o['quantity']*=2
        rows=[dict(r,demand=str(D(r['demand'])*2)) for r in self.rows]
        ledger,_=simulate(c,rows)
        for orig,new in zip(self.ledger,ledger):
            for key in ('arrivals','served','lost_sales','ip_before_order','order_quantity','closing_on_hand'):
                self.assertEqual(new[key],orig[key]*2)

    def test_larger_unserved_demand_does_not_create_backlog(self):
        rows=copy.deepcopy(self.rows);rows[2]['demand']='999'
        ledger,events=simulate(self.c,rows)
        self.assertEqual(events,self.events)
        self.assertEqual(ledger[3:],self.ledger[3:])

    def test_zero_demand_high_initial_stock_has_empty_events(self):
        c=dict(self.c,initial_orders=[],initial_on_hand=11)
        rows=[dict(r,demand='0') for r in self.rows]
        ledger,events=simulate(c,rows)
        self.assertEqual(events,[])
        self.assertTrue(all(r['order_quantity']==0 for r in ledger))
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'empty.csv';write_csv(path,events,EVENT_FIELDS)
            self.assertEqual(path.read_text(),','.join(EVENT_FIELDS)+'\n')

    def test_zero_demand_empty_stock_reorders_once_daily_until_above_r(self):
        c=dict(self.c,initial_orders=[],initial_on_hand=0)
        ledger,_=simulate(c,[dict(r,demand='0') for r in self.rows])
        self.assertEqual([r['order_quantity'] for r in ledger],[6,6,0,0,0,0,0])
        self.assertEqual(ledger[-1]['closing_on_hand'],12)

    def test_zero_lead_time_is_next_morning(self):
        c=dict(self.c,lead_time=0,initial_orders=[])
        ledger,events=simulate(c,self.rows)
        self.assertEqual(ledger[0]['arrivals'],0)
        self.assertEqual(ledger[1]['arrivals'],6)
        self.assertTrue(all(e['arrival_day']==e['placed_day']+1 for e in events))

    def test_multiple_orders_arriving_same_morning(self):
        c=copy.deepcopy(self.c)
        c['initial_orders'][0]['quantity']=3
        c['initial_orders'].append(dict(c['initial_orders'][0],order_id='initial-second',quantity=5))
        ledger,events=simulate(c,self.rows)
        self.assertEqual(ledger,self.ledger)
        self.assertEqual(sum(e['event']=='arrival' and e['event_day']==2 for e in events),2)

    def test_reverse_same_day_initial_order_input_preserves_ledger(self):
        c=copy.deepcopy(self.c)
        c['initial_orders'][0]['quantity']=3
        c['initial_orders'].append(dict(c['initial_orders'][0],order_id='second',quantity=5))
        ledger,_=simulate(c,self.rows);c['initial_orders'].reverse()
        other,_=simulate(c,self.rows)
        self.assertEqual(ledger,other)

    def test_new_order_lead_time_two_arrives_t_plus_three(self):
        placed=next(e for e in self.events if e['event']=='placed')
        self.assertEqual((placed['placed_day'],placed['arrival_day']),(2,5))
        events=copy.deepcopy(self.events)
        for e in events:
            if e['order_id']==placed['order_id']:
                e['arrival_day']-=1
                if e['event']=='arrival':e['event_day']-=1
        with self.assertRaises(ValueError):audit(self.c,self.rows,self.ledger,events)

    def test_invalid_quantity_inputs(self):
        for value in (True,False,None,[],{},'NaN','Infinity','-Infinity','-1','oops','1000001','0.0001','1e-100000'):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):simulate(self.c,[dict(self.rows[0],demand=value)]+self.rows[1:])

    def test_units_and_precision(self):
        self.assertEqual(number('1.125','kg'),D('1.125'))
        for value,unit in [('1.5','pieces'),('1','unknown')]:
            with self.assertRaises(ValueError):number(value,unit)

    def test_precision_rejects_nonzero_tails_beyond_decimal_context(self):
        for value in ('1.00000000000000000000000000001',
                      '0.10000000000000000000000000000001',
                      '999999.000000000000000000000000001',
                      '1e-100000', '10001e-7'):
            for unit in ('kg', 'pieces'):
                with self.subTest(value=value, unit=unit):
                    with self.assertRaises(ValueError): number(value, unit)

    def test_precision_accepts_insignificant_trailing_zeros_and_exponents(self):
        for value, expected in [('1.00000000000000000000000000000', '1'),
                                ('0.10000000000000000000000000000000', '0.1'),
                                ('1125000000000000000000000e-24', '1.125'),
                                ('1000e-6', '0.001'), ('1e3', '1000'),
                                ('0e-100000', '0'), ('-0.0000000000', '0')]:
            with self.subTest(value=value):
                self.assertEqual(number(value, 'kg'), D(expected))

    def test_piece_precision_checks_exact_integer_coefficient(self):
        for value in ('1000e-3', '1.00000000000000000000000000000', '1e6', '0e-99'):
            self.assertEqual(number(value, 'pieces'), D(value))
        for value in ('1.00100000000000000000000000000', '1e-3',
                      '100000000000000000000000000001e-29'):
            with self.assertRaises(ValueError): number(value, 'pieces')

    def test_precision_validation_independent_of_decimal_context(self):
        for precision in (2, 28, 50):
            with localcontext() as ctx:
                ctx.prec = precision
                self.assertEqual(number('1.125000000000000000000000000000', 'kg'), D('1.125'))
                self.assertEqual(number('123456.000000000000000000000000', 'pieces'), D('123456'))
                for value in ('1.00000000000000000000000000001',
                              '0.10000000000000000000000000000001', '1.0001'):
                    with self.assertRaises(ValueError): number(value, 'kg')

    def test_imported_entrypoints_isolate_decimal_context(self):
        c = dict(self.c, initial_on_hand='100.001', reorder_point=100,
                 initial_orders=[], days=1)
        rows = [dict(self.rows[0], demand='0')]
        expected_ledger, expected_events = simulate(c, rows)
        self.assertEqual(expected_ledger[0]['closing_on_hand'], D('100.001'))
        self.assertEqual(expected_ledger[0]['order_quantity'], 0)
        for precision in (1, 2, 28):
            for rounding in (ROUND_UP, ROUND_DOWN, ROUND_FLOOR):
                with self.subTest(precision=precision, rounding=rounding):
                    with localcontext() as ctx:
                        ctx.prec = precision
                        ctx.rounding = rounding
                        ctx.Emin = -1
                        ctx.Emax = 1
                        for signal in ctx.traps: ctx.traps[signal] = True
                        ctx.clear_flags()
                        ledger, events = simulate(c, rows)
                        self.assertEqual((ledger, events), (expected_ledger, expected_events))
                        self.assertEqual(order_qr(D('100.001'), D(0), D(6), D(100)), 0)
                        audit(c, rows, ledger, events)
                        self.assertEqual(ctx.prec, precision)
                        self.assertEqual(ctx.rounding, rounding)
                        self.assertTrue(all(ctx.traps.values()))
                        self.assertFalse(any(ctx.flags.values()))

    def test_audit_rejects_rounded_trajectory_under_hostile_context(self):
        c = dict(self.c, initial_on_hand='100.001', reorder_point=100,
                 initial_orders=[], days=1)
        rows = [dict(self.rows[0], demand='0')]
        ledger, _ = simulate(c, rows)
        for key in ('opening_on_hand', 'available_before_demand',
                    'closing_on_hand', 'ip_before_order'):
            ledger[0][key] = D(100)
        ledger[0].update(order_quantity=D(6), on_order_after_order=D(6), ip_after_order=D(106))
        events = [dict(order_id='new-hewei-001', case='hewei', series=c['series'],
                       unit='kg', placed_day=1, arrival_day=4, quantity=D(6),
                       event='placed', event_day=1)]
        with localcontext() as ctx:
            ctx.prec = 2
            ctx.rounding = ROUND_DOWN
            for signal in ctx.traps: ctx.traps[signal] = True
            with self.assertRaises(ValueError): audit(c, rows, ledger, events)

    def test_initial_order_count_enforces_exact_arithmetic_bound(self):
        c = copy.deepcopy(self.c)
        c['initial_orders'] = [dict(c['initial_orders'][0], order_id=f'initial-{i}',
                                    quantity=1000000) for i in range(1000)]
        rows = [dict(r, demand='0') for r in self.rows]
        with localcontext() as ctx:
            ctx.prec = 2
            for signal in ctx.traps: ctx.traps[signal] = True
            ledger, _ = simulate(c, rows)
        self.assertEqual(ledger[1]['arrivals'], D('1000000000'))
        self.assertEqual(ledger[-1]['closing_on_hand'], D('1000000012'))
        c['initial_orders'].append(dict(c['initial_orders'][0], order_id='one-too-many'))
        with self.assertRaisesRegex(ValueError, 'at most 1000 initial orders'):
            simulate(c, rows)

    def test_direct_policy_state_bound_and_exact_fraction(self):
        with localcontext() as ctx:
            ctx.prec = 1
            for signal in ctx.traps: ctx.traps[signal] = True
            self.assertEqual(order_qr(D('2001000000'), D('2001000000'), D(6), D(100)), 0)
            self.assertEqual(order_qr(D('99.999'), D('0.002'), D(6), D(100)), 0)
            self.assertEqual(order_qr(D('99.999'), D('0.001'), D(6), D(100)), 6)
            with self.assertRaises(ValueError): order_qr(D('2001000000.001'), D(0), D(6), D(100))

    def test_exact_tuple_canonicalization_avoids_extreme_zero_exponents(self):
        with localcontext() as ctx:
            ctx.prec = 1
            for signal in ctx.traps: ctx.traps[signal] = True
            self.assertEqual(number('0e-1000000000', 'kg').as_tuple(), D(0).as_tuple())
            self.assertEqual(number('1.125000000000000000000000000', 'kg').as_tuple(), D('1.125').as_tuple())

    def test_invalid_config_fields_values_and_types(self):
        for key,value in [('lead_time',True),('lead_time',-1),('days',False),('days',0),('initial_on_hand','NaN'),('fixed_quantity',0),('fixed_quantity',True),('reorder_point',-1),('shortage_mode','backorders'),('start_date',True),('start_date','2026-02-30'),('initial_orders',None)]:
            with self.subTest(key=key,value=value):
                c=copy.deepcopy(self.c);c[key]=value
                with self.assertRaises(ValueError):simulate(c,self.rows)
        c=copy.deepcopy(self.c);c['order_up_to']=20
        with self.assertRaises(ValueError):simulate(c,self.rows)

    def test_missing_days_duplicates_dates_and_columns(self):
        with self.assertRaises(ValueError):simulate(self.c,self.rows[:-1])
        for key,value in [('day','1'),('day',True),('date','2026-01-01'),('date','2026-02-30'),('date','20260102')]:
            rows=copy.deepcopy(self.rows);rows[1][key]=value
            with self.assertRaises(ValueError):simulate(self.c,rows)
        rows=copy.deepcopy(self.rows);del rows[1]['demand']
        with self.assertRaises(ValueError):simulate(self.c,rows)
        rows=copy.deepcopy(self.rows);rows[1]['backorder']=3
        with self.assertRaises(ValueError):simulate(self.c,rows)

    def test_cross_entity_and_unit_rejected(self):
        for key,value in [('case','apparel'),('series','hewei/B/SKU01'),('unit','pieces')]:
            rows=copy.deepcopy(self.rows);rows[0][key]=value
            with self.assertRaises(ValueError):simulate(self.c,rows)
            c=copy.deepcopy(self.c);c['initial_orders'][0][key]=value
            with self.assertRaises(ValueError):simulate(c,self.rows)

    def test_invalid_initial_orders(self):
        for key,value in [('order_id','new-x'),('order_id',''),('placed_day',True),('placed_day',1),('arrival_day',True),('arrival_day',1),('quantity',0)]:
            c=copy.deepcopy(self.c);c['initial_orders'][0][key]=value
            with self.assertRaises(ValueError):simulate(c,self.rows)
        c=copy.deepcopy(self.c);c['initial_orders']*=2
        with self.assertRaises(ValueError):simulate(c,self.rows)

    def test_bad_ledger_fields_or_values_rejected(self):
        for key,value in [('on_order_before_order',8),('ip_before_order',12),('order_quantity',12),('day',True)]:
            ledger=copy.deepcopy(self.ledger);ledger[1][key]=value
            with self.assertRaises(ValueError):audit(self.c,self.rows,ledger,self.events)
        for mutation in ('missing','extra'):
            ledger=copy.deepcopy(self.ledger)
            if mutation=='missing':del ledger[0]['served']
            else:ledger[0]['backorders']=0
            with self.assertRaises(ValueError):audit(self.c,self.rows,ledger,self.events)

    def test_bad_event_fields_and_partial_cancelled_rejected(self):
        for kind in ('initial_open','placed','arrival'):
            for mutation in ('missing','extra','partial','cancelled','bool'):
                events=copy.deepcopy(self.events);e=next(e for e in events if e['event']==kind)
                if mutation=='missing':del e['quantity']
                elif mutation=='extra':e['cancelled_quantity']=1
                elif mutation=='partial':e['quantity']-=1
                elif mutation=='cancelled':e['event']='cancelled'
                else:e['event_day']=True
                with self.assertRaises(ValueError):audit(self.c,self.rows,self.ledger,events)

    def test_missing_duplicate_and_early_arrival_rejected(self):
        arrival=next(e for e in self.events if e['event']=='arrival')
        for events in ([e for e in self.events if e is not arrival],self.events+[arrival]):
            with self.assertRaises(ValueError):audit(self.c,self.rows,self.ledger,events)
        events=copy.deepcopy(self.events);next(e for e in events if e['event']=='arrival')['event_day']-=1
        with self.assertRaises(ValueError):audit(self.c,self.rows,self.ledger,events)

    def test_event_chronology_rejected(self):
        with self.assertRaises(ValueError):audit(self.c,self.rows,self.ledger,list(reversed(self.events)))

    def test_duplicated_daily_order_rejected(self):
        events=copy.deepcopy(self.events);e=copy.deepcopy(next(e for e in events if e['event']=='placed'))
        e['order_id']='other-new';events.insert(3,e)
        with self.assertRaises(ValueError):audit(self.c,self.rows,self.ledger,events)

    def test_summary_and_tail_hand_calculations(self):
        summary=json.loads((ROOT/'results/summary.json').read_text())['strategies']
        expected={'hewei-q6':(42,32,10,24,4,0,12,[(5,8,6),(6,9,6)]),
                  'hewei-q12':(42,32,10,24,2,0,12,[(5,8,12)]),
                  'apparel-q6':(35,32,3,36,6,2,12,[(6,8,6),(7,9,6)]),
                  'apparel-q12':(35,32,3,36,3,2,12,[(6,8,12)])}
        keys=['total_demand','total_served','total_lost_sales','total_new_orders','order_count','closing_on_hand','closing_on_order']
        for strategy,values in expected.items():
            s=summary[strategy]
            self.assertEqual(tuple(s[k] for k in keys),values[:-1])
            self.assertEqual([(o['placed_day'],o['arrival_day'],o['quantity']) for o in s['closing_pending_orders']],values[-1])
            self.assertEqual(sum(o['quantity'] for o in s['closing_pending_orders']),s['closing_on_order'])

    def test_frozen_inputs_verify(self):
        self.assertEqual(set(verify_frozen_inputs()['files']),{'frozen_policy.json','POLICY_CARD.md','data/hewei-demand.csv','data/apparel-demand.csv'})

    def test_changed_input_or_refreshed_manifest_rejected_before_outputs(self):
        for target in ('frozen_policy.json','POLICY_CARD.md','data/hewei-demand.csv','source_manifest.json'):
            with tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp)/'practice';shutil.copytree(ROOT,root,ignore=shutil.ignore_patterns('__pycache__'))
                before={p.name:p.read_bytes() for p in (root/'results').iterdir()}
                with (root/target).open('a') as f:f.write(' ')
                if target=='source_manifest.json':
                    # Updating a manifest to legitimize altered data must still fail.
                    (root/'data/hewei-demand.csv').write_text('changed')
                    manifest=json.loads((root/target).read_text())
                    manifest['files']['data/hewei-demand.csv']=hashlib.sha256(b'changed').hexdigest()
                    (root/target).write_text(json.dumps(manifest))
                result=subprocess.run([sys.executable,str(root/'run.py')],cwd=tmp,capture_output=True,text=True)
                self.assertNotEqual(result.returncode,0)
                self.assertIn('separate experiment',result.stderr)
                self.assertEqual(before,{p.name:p.read_bytes() for p in (root/'results').iterdir()})

    def test_standalone_deterministic_run_and_optimized_mode(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'practice';shutil.copytree(ROOT,root,ignore=shutil.ignore_patterns('__pycache__'))
            expected={p.name:p.read_bytes() for p in (root/'results').iterdir()}
            shutil.rmtree(root/'results')
            for flags in ([],['-O']):
                subprocess.run([sys.executable,*flags,str(root/'run.py')],cwd=tmp,check=True,stdout=subprocess.DEVNULL)
                self.assertEqual(expected,{p.name:p.read_bytes() for p in (root/'results').iterdir()})
            hashes=json.loads((root/'results/output_hashes.json').read_text())
            for name,digest in hashes.items():
                self.assertEqual(hashlib.sha256((root/'results'/name).read_bytes()).hexdigest(),digest)


if __name__=='__main__':
    unittest.main()
