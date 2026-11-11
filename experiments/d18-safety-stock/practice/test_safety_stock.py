"""Independent arithmetic, adversarial boundaries, causal prefixes and CLI replay."""
import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from decimal import Decimal as D, localcontext, ROUND_DOWN

from inventory import (simulate, audit, number, validate_config, order_rs,
                       is_review_day, LEDGER_FIELDS, EVENT_FIELDS)
from run import (ROOT, STRATEGIES, CASES, Z_VALUES, estimate, target,
                 service_metrics, load_case, verify_frozen_inputs, load_csv,
                 FIXED_RECEIPT_SHA256)


class SafetyStockTests(unittest.TestCase):
    def setUp(self):
        self.c,self.rows,self.calc=load_case('hewei-z1.645')
        self.ledger,self.events=simulate(self.c,self.rows)

    def altered_rows(self, demands):
        rows=copy.deepcopy(self.rows[:len(demands)])
        for row,value in zip(rows,demands):row['demand']=str(value)
        return rows

    def metric_rows(self,demands,served,unit='kg'):
        case='hewei' if unit=='kg' else 'apparel'
        series='hewei/A/SKU01' if case=='hewei' else 'anonymous-apparel/terminal/SKU01'
        return [dict(case=case,series=series,unit=unit,day=i,demand=D(str(d)),
                     served=D(str(s)),lost_sales=D(str(d))-D(str(s)))
                for i,(d,s) in enumerate(zip(demands,served),1)]

    def test_training_mean_sample_std_hand_calculated(self):
        self.assertEqual(estimate([4,4,4,4,6,8,8,8,8],'kg'),(D(6),D(2)))
        self.assertEqual(estimate([5,5,5,5,8,11,11,11,11],'pieces'),(D(8),D(3)))
        self.assertEqual(estimate([0,2],'kg')[0],1)
        self.assertAlmostEqual(estimate([0,2],'kg')[1],D('1.414213562373095048801688724'),places=25)

    def test_formula_hewei_hand_calculated(self):
        x=target(6,2,4,'1.645','kg',1)
        for key,value in [('horizon_sigma_iid',4),('theoretical_safety_stock','6.58'),
                          ('continuous_target','30.58'),('target_level',31),('effective_buffer',7)]:
            self.assertEqual(D(x[key]),D(value))

    def test_formula_apparel_hand_calculated(self):
        x=target(8,3,4,'1.645','pieces',1)
        self.assertEqual(D(x['theoretical_safety_stock']),D('9.87'))
        self.assertEqual(D(x['continuous_target']),D('41.87'))
        self.assertEqual(D(x['target_level']),42)

    def test_zero_variance(self):
        mean,sigma=estimate([6]*9,'kg');self.assertEqual((mean,sigma),(6,0))
        self.assertEqual(D(target(mean,sigma,4,'1.645','kg',1)['target_level']),24)

    def test_target_rounding_does_not_impose_order_pack_size(self):
        rows=copy.deepcopy(self.rows)
        rows[0]['demand']='6.5'
        ledger,_=simulate(self.c,rows)
        self.assertEqual(D(self.c['target_level']),31)
        self.assertEqual(ledger[1]['order_quantity'],D('19.5'))

    def test_zero_z(self):
        self.assertEqual(D(target(6,2,4,0,'kg',1)['target_level']),24)

    def test_fractional_target_rounding_increment(self):
        x=target(6,2,4,'1.645','kg','0.001')
        self.assertEqual(D(x['target_level']),D('30.580'))

    def test_target_context_isolation(self):
        expected=target(6,2,4,'1.645','kg',1)
        with localcontext() as ctx:
            ctx.prec=2;ctx.rounding=ROUND_DOWN;ctx.Emax=2;ctx.Emin=-2
            self.assertEqual(target(6,2,4,'1.645','kg',1),expected)
            self.assertEqual(estimate([4,4,4,4,6,8,8,8,8],'kg'),(6,2))

    def test_invalid_formula_inputs(self):
        for value in (-1,True,'NaN','Infinity','bad',None,'1000001'):
            for index in (0,1,3):
                args=[6,2,4,'1.645','kg',1];args[index]=value
                with self.subTest(value=value,index=index),self.assertRaises(ValueError):target(*args)
        for horizon in (0,True,1.5,2001):
            with self.assertRaises(ValueError):target(6,2,horizon,1,'kg',1)
        with self.assertRaises(ValueError):target(6,2,4,6,'kg',1)
        with self.assertRaises(ValueError):target(6,2,4,1,'kg',0)
        with self.assertRaises(ValueError):target(6,2,4,1,'liters',1)
        with self.assertRaises(ValueError):target(6,2,4,1,'pieces','.5')

    def test_formula_rejects_more_than_40_significant_digits(self):
        value='1.00000000000000000000000000000000000000001'
        with self.assertRaisesRegex(ValueError,'40 significant digits'):
            target(value,0,1,0,'kg',1)
        with self.assertRaisesRegex(ValueError,'40 significant digits'):
            target(0,value,1,1,'kg',1)

    def test_formula_rejects_tiny_z_instead_of_rounding_it_away(self):
        with self.assertRaises(ValueError):target(6,2,4,'1e-50','kg',1)
        with self.assertRaises(ValueError):target(6,2,4,'0.0001','kg',1)
        self.assertEqual(D(target(6,2,4,'0.001','kg',1)['target_level']),25)

    def test_formula_rejects_unsupported_tiny_moments(self):
        with self.assertRaises(ValueError):target('0.0000001',0,1,0,'kg',1)
        with self.assertRaises(ValueError):target(0,'0.0000001',1,1,'kg',1)
        self.assertEqual(D(target('0.000001',0,1,0,'kg',1)['target_level']),1)

    def test_supported_40_digit_moment_exact_integer_boundary(self):
        near_one='1.'+'0'*38+'1'  # 40 significant digits, strictly > 1.
        self.assertEqual(D(target(near_one,0,1,0,'kg',1)['target_level']),2)
        # A 40-digit mean plus a 3-digit positive buffer can require 42
        # significant digits in their sum; exact comparison must retain it.
        self.assertEqual(D(target(near_one,'0.999',1,1,'kg',1)['target_level']),2)
        self.assertEqual(D(target(near_one,'0.999',1,1,'kg','.001')['target_level']),2)
        self.assertEqual(D(target(1,'0.999',1,1,'kg','.001')['target_level']),D('1.999'))

    def test_40_digit_training_estimates_remain_supported(self):
        mean,sigma=estimate([0,1,1],'kg')
        self.assertEqual(len(mean.as_tuple().digits),40)
        self.assertEqual(len(sigma.as_tuple().digits),40)
        self.assertEqual(D(target(mean,sigma,4,1,'kg',1)['target_level']),4)
        mean,sigma=estimate(['0.001']+[0]*999,'kg')
        self.assertEqual(mean,D('0.000001'))
        self.assertEqual(D(target(mean,sigma,4,'1.645','kg',1)['target_level']),1)

    def test_exact_target_rounding_nonsquare_horizon_and_zero(self):
        self.assertEqual(D(target(0,1,2,1,'kg',1)['target_level']),2)
        self.assertEqual(D(target(0,1,4,1,'kg',1)['target_level']),2)
        self.assertEqual(D(target(0,0,2000,0,'kg',1)['target_level']),0)

    def test_invalid_training_inputs(self):
        for values in ([],[1],(1,2),[1,-2],[1,'NaN'],[1,True],[1,'Infinity']):
            with self.assertRaises(ValueError):estimate(values,'kg')
        with self.assertRaises(ValueError):estimate([1,2.5],'pieces')

    def test_metric_counterexample_75_vs_98_75(self):
        m,c=service_metrics(self.metric_rows([20]*4,[20,20,20,19]),1,1)
        self.assertEqual((m['complete_cycles'],m['no_stockout_cycles']),(4,3))
        self.assertEqual(D(m['cycle_no_stockout_rate']),D('.75'))
        self.assertEqual(D(m['unit_fill_rate']),D('.9875'))

    def test_all_zero_periods_success_but_fill_na(self):
        m,c=service_metrics(self.metric_rows([0]*4,[0]*4),2,1)
        self.assertEqual((m['complete_cycles'],m['no_stockout_cycles']),(2,2))
        self.assertEqual(D(m['cycle_no_stockout_rate']),1)
        self.assertIsNone(m['unit_fill_rate'])
        self.assertTrue(all(x['unit_fill_rate'] is None for x in c))

    def test_zero_demand_cycle_included_in_denominator(self):
        m,c=service_metrics(self.metric_rows([0,2],[0,1]),1,1)
        self.assertEqual(m['zero_demand_cycles'],1)
        self.assertEqual(D(m['cycle_no_stockout_rate']),D('.5'))

    def test_unit_fill_is_ratio_of_sums_not_average(self):
        m,_=service_metrics(self.metric_rows([1,99],[0,99]),1,1)
        self.assertEqual(D(m['unit_fill_rate']),D('.99'))
        self.assertNotEqual(D(m['unit_fill_rate']),D('.5'))

    def test_startup_and_partial_tail_excluded_from_both_metrics(self):
        m,c=service_metrics(self.metric_rows([99,10,10,999],[0,10,10,0]),2,2)
        self.assertEqual((m['total_demand'],m['total_served']),(20,20))
        self.assertEqual(m['excluded_startup_days'],[1])
        self.assertEqual(m['excluded_partial_tail_days'],[4])
        self.assertEqual(D(m['cycle_no_stockout_rate']),1)

    def test_no_complete_cycles_both_na(self):
        m,c=service_metrics(self.metric_rows([1,1],[1,1]),2,2)
        self.assertEqual(m['complete_cycles'],0);self.assertEqual(c,[])
        self.assertIsNone(m['cycle_no_stockout_rate']);self.assertIsNone(m['unit_fill_rate'])
        m,c=service_metrics(self.metric_rows([1],[1]),2,2001)
        self.assertEqual(m['excluded_startup_days'],[1])

    def test_zero_order_still_retains_fixed_cycle(self):
        self.assertEqual(self.ledger[11]['order_quantity'],0)
        m,c=service_metrics(self.ledger,2,5)
        self.assertEqual([(x['start_day'],x['end_day']) for x in c],[(5,6),(7,8),(9,10),(11,12),(13,14)])
        self.assertEqual(m['zero_demand_cycles'],1)

    def test_metric_rejects_mixed_units_identity_or_day(self):
        for field,value in [('unit','pieces'),('case','apparel'),('series','other'),('day',99)]:
            rows=self.metric_rows([1,1],[1,1]);rows[1][field]=value
            with self.assertRaises(ValueError):service_metrics(rows,1,1)
        with self.assertRaises(ValueError):service_metrics([],1,1)

    def test_metric_rejects_bad_quantities_or_conservation(self):
        for value in (-1,'NaN',True,'Infinity'):
            rows=self.metric_rows([1],[1]);rows[0]['served']=value
            with self.assertRaises(ValueError):service_metrics(rows,1,1)
        rows=self.metric_rows([1],[1]);rows[0]['served']=2
        with self.assertRaises(ValueError):service_metrics(rows,1,1)

    def test_six_frozen_strategies_have_independent_expected_totals(self):
        expected={'hewei-z0':(24,66,56,10,3,94,84,10,0,20),
                  'hewei-z1':(28,66,60,6,3,94,88,6,4,20),
                  'hewei-z1.645':(31,66,63,3,4,94,91,3,7,20),
                  'apparel-z0':(32,90,76,14,3,128,112,16,0,28),
                  'apparel-z1':(38,90,82,8,3,128,120,8,4,28),
                  'apparel-z1.645':(42,90,86,4,4,128,124,4,8,28)}
        for strategy,want in expected.items():
            c,rows,_=load_case(strategy);ledger,_=simulate(c,rows);m,_=service_metrics(ledger,2,5)
            got=(D(c['target_level']),m['total_demand'],m['total_served'],m['total_lost_sales'],m['no_stockout_cycles'],
                 sum(r['demand'] for r in ledger),sum(r['served'] for r in ledger),sum(r['lost_sales'] for r in ledger),
                 ledger[-1]['closing_on_hand'],ledger[-1]['on_order_after_order'])
            self.assertEqual(got,want,strategy)

    def test_first_stockout_hand_calculation(self):
        # z1.645: day2 order19 -> day5; day4 order12 -> day7.
        # day5/6 demand18 leaves1; day7/8 stock13 faces16, loses3.
        self.assertEqual(self.ledger[1]['order_quantity'],19)
        self.assertEqual(self.ledger[3]['order_quantity'],12)
        self.assertEqual(self.ledger[4]['arrivals'],19)
        self.assertEqual(self.ledger[5]['closing_on_hand'],1)
        self.assertEqual(self.ledger[7]['lost_sales'],3)

    def test_all_strategies_same_initial_inventory(self):
        for case,initial in [('hewei',24),('apparel',32)]:
            for z in Z_VALUES:
                c,_,_=load_case(f'{case}-z{z}')
                self.assertEqual(c['initial_on_hand'],initial);self.assertEqual(c['initial_orders'],[])

    def test_material_conservation_all_strategies(self):
        for strategy in STRATEGIES:
            c,rows,_=load_case(strategy);ledger,events=simulate(c,rows)
            self.assertEqual(D(c['initial_on_hand'])+sum(r['arrivals']-r['served'] for r in ledger),ledger[-1]['closing_on_hand'])
            self.assertEqual(sum(r['order_quantity']-r['arrivals'] for r in ledger),ledger[-1]['on_order_after_order'])
            self.assertEqual(sum(r['demand'] for r in ledger),sum(r['served']+r['lost_sales'] for r in ledger))
            self.assertTrue(all(r['backlog']==0 for r in ledger))

    def test_arrivals_before_demand_and_ip_conservation(self):
        self.assertEqual((self.ledger[4]['opening_on_hand'],self.ledger[4]['arrivals'],self.ledger[4]['served']),(0,19,9))
        for r in self.ledger:
            self.assertEqual(r['opening_on_hand']+r['opening_on_order'],r['available_before_demand']+r['on_order_before_order'])

    def test_new_order_cannot_serve_same_day(self):
        self.assertEqual(self.ledger[1]['closing_on_hand'],12)
        self.assertEqual(self.ledger[1]['order_quantity'],19)
        self.assertEqual(self.ledger[1]['arrivals'],0)

    def test_tail_orders_stay_on_order(self):
        tail=[e for e in self.events if e['event']=='placed' and e['arrival_day']>15]
        self.assertEqual([(e['placed_day'],e['arrival_day'],e['quantity']) for e in tail],[(14,17,20)])
        self.assertFalse(any(e['event']=='arrival' and e['event_day']>15 for e in self.events))

    def test_future_demand_prefix_invariance_all_six(self):
        for strategy in STRATEGIES:
            c,rows,_=load_case(strategy);baseline,_=simulate(c,rows)
            for cutoff in range(1,15):
                changed=copy.deepcopy(rows)
                for r in changed[cutoff:]:r['demand']='999'
                replay,_=simulate(c,changed)
                self.assertEqual(replay[:cutoff],baseline[:cutoff],(strategy,cutoff))

    def test_horizon_prefix_invariance(self):
        for cutoff in range(1,16):
            ledger,_=simulate(dict(self.c,days=cutoff),self.rows[:cutoff])
            self.assertEqual(ledger,self.ledger[:cutoff])

    def test_lost_sales_not_backlog(self):
        rows=copy.deepcopy(self.rows);rows[7]['demand']='999'
        ledger,events=simulate(self.c,rows)
        self.assertEqual(ledger[8:],self.ledger[8:]);self.assertEqual(events,self.events)
        with self.assertRaises(ValueError):simulate(dict(self.c,shortage_mode='backorders'),self.rows)

    def test_zero_demand_simulation(self):
        rows=self.altered_rows([0]*15)
        ledger,_=simulate(self.c,rows)
        self.assertTrue(all(r['served']==r['lost_sales']==0 for r in ledger))
        m,_=service_metrics(ledger,2,5)
        self.assertEqual(m['no_stockout_cycles'],5);self.assertIsNone(m['unit_fill_rate'])

    def test_l0_arrives_next_morning(self):
        c=dict(self.c,lead_time=0,review_interval=1,first_review_day=1)
        ledger,events=simulate(c,self.rows)
        placed=next(e for e in events if e['event']=='placed')
        self.assertEqual((placed['placed_day'],placed['arrival_day']),(1,2))
        self.assertEqual(ledger[0]['arrivals'],0)
        self.assertEqual(ledger[1]['arrivals'],13)

    def test_policy_calendar_and_position_boundaries(self):
        self.assertEqual(order_rs(3,5,0,31,1,2,2),0)
        self.assertEqual(order_rs(3,5,0,31,2,2,2),23)
        self.assertEqual(order_rs(3,28,0,31,2,2,2),0)
        self.assertEqual(order_rs(3,99,0,31,2,2,2),0)
        self.assertFalse(is_review_day(1,2,2));self.assertTrue(is_review_day(2,2,2))

    def test_quantity_rejects_nonfinite_negative_bad_units(self):
        for x in (-1,'NaN','Infinity',True,None,'0.0001','1000001','1e-100000'):
            with self.assertRaises(ValueError):number(x,'kg')
        with self.assertRaises(ValueError):number(1,'liters')
        with self.assertRaises(ValueError):number('1.1','pieces')

    def test_invalid_day_date_identity_and_unit(self):
        for field,value in [('date','2026-10-31'),('day','2'),('unit','pieces'),('series','hewei/B/SKU01')]:
            rows=copy.deepcopy(self.rows);rows[0][field]=value
            with self.assertRaises(ValueError):simulate(self.c,rows)
        with self.assertRaises(ValueError):simulate(self.c,self.rows[:-1])

    def test_invalid_review_and_lead_time(self):
        for field,value in [('review_interval',0),('lead_time',-1),('first_review_day',True),('days',0)]:
            with self.assertRaises(ValueError):simulate(dict(self.c,**{field:value}),self.rows)

    def test_independent_audit_rejects_each_corrupted_ledger_quantity(self):
        quantities=[key for key,value in self.ledger[5].items() if isinstance(value,D)]
        for key in quantities:
            ledger=copy.deepcopy(self.ledger);ledger[5][key]+=1
            with self.subTest(key=key),self.assertRaises(ValueError):audit(self.c,self.rows,ledger,self.events)

    def test_audit_rejects_early_arrival(self):
        events=copy.deepcopy(self.events);oid=events[0]['order_id']
        for e in events:
            if e['order_id']==oid:
                e['arrival_day']-=1
                if e['event']=='arrival':e['event_day']-=1
        with self.assertRaises(ValueError):audit(self.c,self.rows,self.ledger,events)

    def test_audit_rejects_duplicate_and_missing_event(self):
        with self.assertRaises(ValueError):audit(self.c,self.rows,self.ledger,self.events+[self.events[-1]])
        with self.assertRaises(ValueError):audit(self.c,self.rows,self.ledger,self.events[:-1])

    def test_inventory_decimal_context_isolation(self):
        with localcontext() as ctx:
            ctx.prec=2;ctx.rounding=ROUND_DOWN;ctx.Emax=2;ctx.Emin=-2
            ledger,events=simulate(self.c,self.rows)
        self.assertEqual(ledger,self.ledger);self.assertEqual(events,self.events)

    def test_frozen_receipt_hash_and_unseen_boundary(self):
        receipt=verify_frozen_inputs()
        self.assertEqual(receipt['unseen_test'],'not_created_not_read_not_run')
        self.assertEqual(receipt['candidate_selection'],'none')
        self.assertFalse((ROOT/'sealed').exists())
        self.assertFalse((ROOT/'data/test.csv').exists())

    def test_output_hashes_verify_committed_bytes(self):
        hashes=json.loads((ROOT/'results/output_hashes.json').read_text())
        self.assertEqual(len(hashes),19)
        for name,digest in hashes.items():
            self.assertEqual(hashlib.sha256((ROOT/'results'/name).read_bytes()).hexdigest(),digest)

    def test_cli_clean_copy_byte_identical_arbitrary_cwd(self):
        with tempfile.TemporaryDirectory(prefix='d18-clean-') as temp:
            p=Path(temp)/'practice';shutil.copytree(ROOT,p,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
            expected={x.relative_to(p):x.read_bytes() for x in p.rglob('*') if x.is_file()}
            result=subprocess.run([sys.executable,'-B',str(p/'run.py')],cwd=temp,capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            for name,blob in expected.items():self.assertEqual((p/name).read_bytes(),blob,name)

    def test_cli_tampering_fails_before_output(self):
        for name in ['parameters.json','POLICY_CARD.md','freeze_receipt.json','data/hewei-training.csv','data/apparel-replay.csv']:
            with tempfile.TemporaryDirectory(prefix='d18-tamper-') as temp:
                p=Path(temp)/'practice';shutil.copytree(ROOT,p,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
                shutil.rmtree(p/'results');(p/name).write_bytes((p/name).read_bytes()+b'\n')
                result=subprocess.run([sys.executable,'-B',str(p/'run.py')],cwd=temp,capture_output=True,text=True)
                self.assertNotEqual(result.returncode,0,name);self.assertFalse((p/'results').exists())

    def test_cli_refuses_final_test_command(self):
        result=subprocess.run([sys.executable,'-B',str(ROOT/'run.py'),'finalize'],capture_output=True,text=True)
        self.assertNotEqual(result.returncode,0)
        self.assertIn('no unseen-test or finalize command',result.stderr)

    def test_python_optimized_mode_keeps_audit(self):
        code="from inventory import number; number('NaN','kg')"
        result=subprocess.run([sys.executable,'-B','-O','-c',code],cwd=ROOT,capture_output=True,text=True)
        self.assertNotEqual(result.returncode,0);self.assertIn('ValueError',result.stderr)

    def test_csv_duplicate_header_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'bad.csv';path.write_text('case,series,unit,day,date,demand,demand\n')
            with self.assertRaises(ValueError):load_csv(path)

    def test_training_cannot_overlap_replay(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'practice';shutil.copytree(ROOT,p,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
            data=json.loads((p/'parameters.json').read_text())
            data['cases']['hewei']['simulation']['start_date']='2026-09-09'
            (p/'parameters.json').write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError,'training must precede replay'):load_case('hewei-z0',p)

    def test_hidden_parameter_selection_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'practice';shutil.copytree(ROOT,p,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
            data=json.loads((p/'parameters.json').read_text());data['design']='choose_best_from_replay'
            (p/'parameters.json').write_text(json.dumps(data))
            with self.assertRaises(ValueError):load_case('hewei-z0',p)


if __name__=='__main__':unittest.main()
