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
                 order_rs, is_review_day, number, write_csv, verify_frozen_inputs)


class InventoryTests(unittest.TestCase):
    def setUp(self):
        self.c, self.rows = load_case('hewei-r2')
        self.ledger, self.events = simulate(self.c, self.rows)

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


    def test_larger_unserved_demand_does_not_create_backlog(self):
        rows=copy.deepcopy(self.rows);rows[2]['demand']='999'
        ledger,events=simulate(self.c,rows)
        self.assertEqual(events,self.events)
        self.assertEqual(ledger[3:],self.ledger[3:])


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


    def test_exact_tuple_canonicalization_avoids_extreme_zero_exponents(self):
        with localcontext() as ctx:
            ctx.prec = 1
            for signal in ctx.traps: ctx.traps[signal] = True
            self.assertEqual(number('0e-1000000000', 'kg').as_tuple(), D(0).as_tuple())
            self.assertEqual(number('1.125000000000000000000000000', 'kg').as_tuple(), D('1.125').as_tuple())


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


    def test_four_hand_calculated_paths(self):
        # Independently worked seven-day quantities, not generated expectations.
        expected = {
            'hewei-r2': ([0,16,0,4,0,11,0], [5,4,0,0,11,5,6], [0,0,4,4,0,0,0]),
            'hewei-r3': ([0,0,20,0,0,6,0], [5,4,0,0,0,14,11], [0,0,4,4,5,0,0]),
            'apparel-r2': ([0,24,0,0,0,9,0], [5,0,0,0,21,15,13], [0,3,4,7,0,0,0]),
            'apparel-r3': ([0,0,24,0,0,6,0], [5,0,0,0,0,18,16], [0,3,4,7,3,0,0])}
        for strategy, (q, oh, lost) in expected.items():
            ledger, _ = simulate(*load_case(strategy))
            for field, values in [('order_quantity',q),('closing_on_hand',oh),('lost_sales',lost)]:
                self.assertEqual([r[field] for r in ledger], values, strategy+' '+field)

    def test_calendar_offsets_and_r1(self):
        for r, first, days in [(2,2,[2,4,6]),(3,3,[3,6]),(3,2,[2,5]),(1,1,list(range(1,8))),(2,9,[])]:
            self.assertEqual([d for d in range(1,8) if is_review_day(d,r,first)],days)

    def test_target_below_equal_above(self):
        for ip, q in [('19.999','0.001'),('20','0'),('20.001','0')]:
            self.assertEqual(order_rs(ip,0,0,20,2,2,2),D(q))

    def test_nonreview_day_cannot_order_even_at_zero_ip(self):
        self.assertEqual(order_rs(0,0,0,20,1,2,2),0)
        self.assertEqual(order_rs(0,0,40,20,1,2,2),0)

    def test_general_backlog_boundary_separate_from_simulation(self):
        # Backlog affects general IP; this is not a simulated backorder trajectory.
        self.assertEqual(order_rs(3,5,10,20,2,2,2),22) # IP=-2
        self.assertEqual(order_rs(3,5,0,20,2,2,2),12)
        c=dict(self.c,shortage_mode='backorders')
        with self.assertRaises(ValueError):simulate(c,self.rows)
        self.assertTrue(all(r['backlog']==0 for r in self.ledger))
        bad=copy.deepcopy(self.ledger);bad[2]['backlog']=4
        with self.assertRaises(ValueError):audit(self.c,self.rows,bad,self.events)

    def test_pipeline_prevents_duplicate_replenishment(self):
        ledger,events=simulate(*load_case('apparel-r2'))
        self.assertTrue(ledger[3]['is_review_day'])
        self.assertEqual(ledger[3]['closing_on_hand'],0)
        self.assertEqual(ledger[3]['on_order_before_order'],24)
        self.assertEqual(ledger[3]['order_quantity'],0)
        self.assertFalse(any(e['event']=='placed' and e['event_day']==4 for e in events))

    def test_review_restores_position_not_on_hand(self):
        for strategy in STRATEGIES:
            c,rows=load_case(strategy); ledger,events=simulate(c,rows)
            for row in ledger:
                if row['is_review_day']:
                    self.assertEqual(row['ip_after_order'],max(row['ip_before_order'],c['target_level']))
                else:self.assertEqual(row['order_quantity'],0)
            days=[e['event_day'] for e in events if e['event']=='placed']
            self.assertEqual(len(days),len(set(days)))
        self.assertEqual(self.ledger[1]['ip_after_order'],20)
        self.assertEqual(self.ledger[1]['closing_on_hand'],4)

    def test_new_order_cannot_serve_same_day(self):
        ledger,_=simulate(*load_case('apparel-r2'))
        self.assertEqual((ledger[1]['order_quantity'],ledger[1]['lost_sales']),(24,3))

    def test_zero_demand_and_zero_target(self):
        for stock,target,q in [(0,20,20),(25,20,0),(0,0,0)]:
            c=dict(self.c,initial_orders=[],initial_on_hand=stock,target_level=target)
            ledger,events=simulate(c,[dict(r,demand='0') for r in self.rows])
            self.assertEqual([r['order_quantity'] for r in ledger],[0,q,0,0,0,0,0])

    def test_zero_lead_time_is_next_morning(self):
        c=dict(self.c,lead_time=0,initial_orders=[])
        ledger,events=simulate(c,self.rows)
        self.assertEqual(ledger[1]['arrivals'],0)
        self.assertEqual(ledger[2]['arrivals'],20)
        self.assertTrue(all(e['arrival_day']==e['placed_day']+1 for e in events))

    def test_scaling(self):
        c=copy.deepcopy(self.c)
        for k in ('initial_on_hand','target_level'):c[k]*=2
        for o in c['initial_orders']:o['quantity']*=2
        ledger,_=simulate(c,[dict(r,demand=str(D(r['demand'])*2)) for r in self.rows])
        for a,b in zip(self.ledger,ledger):
            for k in ('served','lost_sales','order_quantity','ip_before_order','closing_on_hand'):
                self.assertEqual(b[k],a[k]*2)

    def test_invalid_review_config(self):
        for k,v in [('review_interval',0),('review_interval',True),('review_interval',1.5),('first_review_day',0),('first_review_day',False),('target_level',-1),('target_level','NaN'),('target_level',True),('lead_time',-1),('days',False)]:
            with self.subTest(key=k,value=v):
                with self.assertRaises(ValueError):simulate(dict(self.c,**{k:v}),self.rows)
        with self.assertRaises(ValueError):simulate(dict(self.c,backlog=4),self.rows)

    def test_review_flag_corruption(self):
        for value in [0,1,False]:
            ledger=copy.deepcopy(self.ledger);ledger[1]['is_review_day']=value
            with self.assertRaises(ValueError):audit(self.c,self.rows,ledger,self.events)

    def test_hostile_decimal_context(self):
        for precision in (1,2,28):
            with localcontext() as ctx:
                ctx.prec=precision;ctx.Emin=-1;ctx.Emax=1;ctx.rounding=ROUND_UP
                for signal in ctx.traps:ctx.traps[signal]=True
                ctx.clear_flags()
                self.assertEqual(simulate(self.c,self.rows),(self.ledger,self.events))
                self.assertEqual(order_rs('19.999',0,0,20,2,2,2),D('0.001'))
                self.assertEqual(order_rs(0,0,2001000000,1000000,2,2,2),D('2002000000'))
                self.assertFalse(any(ctx.flags.values()))
                self.assertEqual(ctx.prec,precision)

    def test_tail_and_summary(self):
        summary=json.loads((ROOT/'results/summary.json').read_text())['strategies']
        expected={'hewei-r2':(42,34,8,31,3,6,11),'hewei-r3':(42,29,13,26,2,11,6),
                  'apparel-r2':(35,21,14,33,2,13,9),'apparel-r3':(35,18,17,30,2,16,6)}
        keys=['total_demand','total_served','total_lost_sales','total_new_orders','order_count','closing_on_hand','closing_on_order']
        for strategy,values in expected.items():
            s=summary[strategy]
            self.assertEqual(tuple(s[k] for k in keys),values)
            self.assertEqual([(o['placed_day'],o['arrival_day'],o['quantity']) for o in s['closing_pending_orders']],[(6,9,values[-1])])

    def test_pure_function_not_persistent_idempotency(self):
        self.assertEqual([order_rs(4,0,0,20,2,2,2) for _ in range(3)],[16,16,16])


if __name__=='__main__':
    unittest.main()
