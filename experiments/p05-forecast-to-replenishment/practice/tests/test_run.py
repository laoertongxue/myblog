import csv
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('practice_run', ROOT/'run.py')
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)
D = r.D


class PracticeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.inputs = self.base/'inputs'
        shutil.copytree(ROOT/'inputs', self.inputs)
        self.data = r.load(self.inputs)
        self.summary, self.nv, self.candidates, self.ledger = r.calculate(self.data)

    def replace(self, file, old, new):
        p = self.inputs/file
        p.write_text(p.read_text().replace(old,new))

    def invalid(self):
        with self.assertRaises(ValueError):
            r.load(self.inputs)

    def test_newsvendor_quantile(self):
        self.assertEqual(self.summary['newsvendor_quantile'],D(120))

    def test_newsvendor_costs(self):
        self.assertEqual([v['expected_cost'] for v in self.nv],list(map(D,[180,100,60,60,100])))

    def test_newsvendor_shortages(self):
        self.assertEqual([v['expected_shortage'] for v in self.nv],list(map(D,[30,15,5,0,0])))

    def test_newsvendor_surpluses(self):
        self.assertEqual([v['expected_surplus'] for v in self.nv],list(map(D,[0,5,15,30,50])))

    def test_optimum_is_tied(self):
        self.assertEqual(self.summary['newsvendor_minimizers'],[D(120),D(140)])

    def test_quantile_at_jump(self):
        self.assertEqual(r.quantile([D(10),D(30)],[D(9),D(1)],D('.9')),D(10))
        self.assertEqual(r.quantile([D(10),D(30)],[D(9),D(1)],D('.9000000001')),D(30))

    def test_joint_paths_counterexample(self):
        self.assertEqual(self.summary['daily_p90'],[D(10)]*3)
        self.assertEqual(self.summary['sum_daily_p90'],D(30))
        self.assertEqual(self.summary['total_p90'],D(50))

    def test_moq_rejects_five(self):
        self.assertFalse(next(x for x in self.candidates if x['q']==5)['feasible'])

    def test_zero_order_allowed(self):
        self.assertTrue(self.candidates[0]['feasible'])

    def test_feasible_set(self):
        self.assertEqual([x['q'] for x in self.candidates if x['feasible']],[D(0),D(10),D(15)])

    def test_best_executable(self):
        self.assertEqual(self.summary['inventory_selected']['q'],D(15))
        self.assertEqual([x['lost_kg'] for x in self.ledger if x['q']==15],[D(2),D(0),D(1)])

    def test_late_order_never_repairs_day_one(self):
        self.assertEqual({x['lost_kg'] for x in self.ledger if x['day']==1},{D(2)})

    def test_naive_capacity_failure(self):
        self.assertEqual(self.summary['naive_q'],D(20))
        row=next(x for x in self.candidates if x['q']==20)
        self.assertFalse(row['feasible'])
        self.assertIn('capacity_day2',row['reasons'])

    def test_sixteen_covers_only_later_days(self):
        c=dict(self.data[5],pack_kg=D(1))
        result, trace=r.simulate(D(16),self.data[3],self.data[4],c)
        self.assertTrue(result['feasible'])
        self.assertEqual([x['lost_kg'] for x in trace],[D(2),D(0),D(0)])

    def test_mass_balance_every_candidate_day(self):
        for x in self.ledger:
            self.assertEqual(x['opening_kg']+x['arrival_kg'],x['served_kg']+x['expired_kg']+x['closing_kg'])
            self.assertEqual(x['demand_kg'],x['served_kg']+x['lost_kg'])

    def test_capacity_counts_existing_stock(self):
        demand={1:D(0),2:D(0),3:D(0)}
        batches=[dict(batch='carry',arrival_day=1,expiry_day=3,kg=D(9))]
        result,trace=r.simulate(D(10),demand,batches,self.data[5])
        self.assertFalse(result['feasible'])
        self.assertEqual(trace[1]['peak_kg'],D(19))

    def test_fefo_earliest_expiry_first(self):
        batches=[dict(batch='later',arrival_day=1,expiry_day=3,kg=D(5)),dict(batch='sooner',arrival_day=1,expiry_day=1,kg=D(5))]
        result,trace=r.simulate(D(0),{1:D(6),2:D(0),3:D(0)},batches,self.data[5])
        self.assertEqual(trace[0]['fefo_allocations'],'sooner:5;later:1')
        self.assertEqual(trace[2]['expired_kg'],D(4))

    def test_expired_stock_cannot_serve_tomorrow(self):
        batches=[dict(batch='early',arrival_day=1,expiry_day=1,kg=D(5))]
        _,trace=r.simulate(D(0),{1:D(0),2:D(5),3:D(0)},batches,self.data[5])
        self.assertEqual(trace[0]['expired_kg'],D(5))
        self.assertEqual(trace[1]['lost_kg'],D(5))

    def test_apparel_scenario_not_quantile(self):
        a=self.summary['apparel']
        self.assertEqual(a['expected_scenario_pieces'],D(100))
        self.assertEqual(a['production_needed_pieces'],D(85))

    def test_apparel_material_and_rounding(self):
        a=self.summary['apparel']
        self.assertEqual(a['gross_material_m'],D(170)/D('.95'))
        self.assertEqual(a['shortage_m'],r.decimal_ratio(r.Fraction(170)/r.Fraction('.95')-80))
        self.assertEqual(a['purchase_m'],D(100))

    def test_late_material_excluded(self):
        self.replace('apparel.csv','late_transit_m,25','late_transit_m,999')
        a=r.calculate(r.load(self.inputs))[0]['apparel']
        self.assertEqual(a['purchase_m'],D(100))

    def test_capacity_gap_not_procurement_success(self):
        self.assertEqual(self.summary['apparel']['production_capacity_gap'],D(15))

    def test_decimal_exact_boundary(self):
        self.assertEqual(r.ceil_pack(D('100.00000000000000001'),D(20)),D(120))
        self.assertEqual(r.ceil_pack(D('100'),D(20)),D(100))
        self.assertEqual(r.ceil_pack(D('99.99999999999999999'),D(20)),D(100))

    def test_nonfinite_rejected(self):
        for value in ['NaN','Infinity','-Infinity']:
            with self.subTest(value=value), self.assertRaises(ValueError):
                r.number(value)

    def test_negative_rejected(self):
        with self.assertRaises(ValueError):
            r.number('-1')

    def test_duplicate_config_rejected(self):
        with (self.inputs/'apparel.csv').open('a') as f:
            f.write('roll_m,20\n')
        self.invalid()

    def test_duplicate_path_rejected(self):
        self.replace('paths.csv','p02,','p01,')
        self.invalid()

    def test_numeric_day_alias_rejected(self):
        self.replace('demand.csv','2,14','01,14')
        self.invalid()

    def test_gap_in_days_rejected(self):
        self.replace('demand.csv','2,14','4,14')
        self.invalid()

    def test_expiry_before_arrival_rejected(self):
        self.replace('batches.csv','old_transit,transit,3,3,8','old_transit,transit,3,2,8')
        self.invalid()

    def test_uncovered_batch_rejected(self):
        self.replace('batches.csv','old_transit,transit,3,3,8','old_transit,transit,4,4,8')
        self.invalid()

    def test_bad_lead_time_rejected(self):
        self.replace('inventory_config.csv','lead_time,1','lead_time,2')
        self.invalid()

    def test_fractional_day_rejected(self):
        self.replace('demand.csv','2,14','2.5,14')
        self.invalid()

    def test_zero_pack_rejected(self):
        self.replace('inventory_config.csv','pack_kg,5','pack_kg,0')
        self.invalid()

    def test_yield_zero_rejected(self):
        self.replace('apparel.csv','yield,0.95','yield,0')
        self.invalid()

    def test_retention_over_one_rejected(self):
        self.replace('apparel.csv','conditional_retention,0.8','conditional_retention,1.1')
        self.invalid()

    def test_zero_weight_rejected(self):
        self.replace('newsvendor.csv','80,1','80,0')
        self.invalid()

    def test_unknown_key_rejected(self):
        self.replace('apparel.csv','roll_m,20','wrong,20')
        self.invalid()

    def test_changed_input_changes_result(self):
        self.replace('demand.csv','3,10','3,8')
        changed=r.calculate(r.load(self.inputs))[0]
        self.assertEqual(changed['inventory_selected']['lost_kg'],D(2))

    def test_no_input_mutation(self):
        before={p.name:p.read_bytes() for p in self.inputs.iterdir()}
        r.execute(self.inputs,self.base/'output')
        self.assertEqual(before,{p.name:p.read_bytes() for p in self.inputs.iterdir()})

    def test_existing_output_rejected_without_modification(self):
        out=self.base/'output'
        out.mkdir()
        sentinel=out/'keep.txt'
        sentinel.write_text('unchanged')
        with self.assertRaises(ValueError):
            r.execute(self.inputs,out)
        self.assertEqual(sentinel.read_text(),'unchanged')

    def test_output_inside_inputs_rejected(self):
        with self.assertRaises(ValueError):
            r.execute(self.inputs,self.inputs/'out')

    def test_output_symlink_into_inputs_rejected(self):
        link=self.base/'link'
        link.symlink_to(self.inputs,target_is_directory=True)
        with self.assertRaises(ValueError):
            r.execute(self.inputs,link/'out')

    def test_invalid_input_creates_no_output(self):
        self.replace('apparel.csv','yield,0.95','yield,NaN')
        out=self.base/'output'
        with self.assertRaises(ValueError):
            r.execute(self.inputs,out)
        self.assertFalse(out.exists())

    def test_saved_ledger_has_all_candidates(self):
        out=self.base/'output'
        r.execute(self.inputs,out)
        with (out/'inventory_ledger.csv').open() as f:
            self.assertEqual(len(list(csv.DictReader(f))),21)
        saved=json.loads((out/'summary.json').read_text())
        self.assertEqual(saved['inventory_selected']['q'],'15')

    def test_initial_stock_is_opening_not_arrival(self):
        row=next(x for x in self.ledger if x['q']==15 and x['day']==1)
        self.assertEqual(row['opening_kg'],D(10))
        self.assertEqual(row['arrival_kg'],D(0))
        self.assertEqual(row['peak_kg'],D(10))

    def test_expiry_pressure(self):
        self.replace('demand.csv','1,12','1,6')
        summary,_,_,ledger=r.calculate(r.load(self.inputs))
        self.assertEqual(summary['inventory_selected']['q'],D(15))
        selected=[x for x in ledger if x['q']==15]
        self.assertEqual([x['expired_kg'] for x in selected],[D(4),D(0),D(0)])
        self.assertEqual([x['lost_kg'] for x in selected],[D(0),D(0),D(1)])

    def test_apparel_capacity_plan(self):
        a=self.summary['apparel_capacity_plan']
        self.assertEqual(a['planned_production_pieces'],D(70))
        self.assertEqual(a['gross_material_m'],D(140)/D('.95'))
        self.assertEqual(a['shortage_m'],r.decimal_ratio(r.Fraction(140)/r.Fraction('.95')-80))
        self.assertEqual(a['purchase_m'],D(80))
        self.assertEqual(a['unmet_scenario_pieces'],D(15))

    def test_huge_exponent_rejected(self):
        for value in ['1e9999999999999999999','1e-99999','1E6']:
            with self.subTest(value=value),self.assertRaises(ValueError):
                r.number(value)

    def test_input_decimal_places_bounded(self):
        with self.assertRaises(ValueError):
            r.number('0.0000001')
        self.assertEqual(r.number('0.000001'),D('.000001'))

    def test_input_value_bounded(self):
        with self.assertRaises(ValueError):
            r.number('1000000.000001')
        self.assertEqual(r.number('1000000'),D(1000000))

    def test_candidate_count_bounded(self):
        self.replace('inventory_config.csv','pack_kg,5','pack_kg,0.000001')
        self.invalid()

    def test_newsvendor_count_bounded(self):
        self.replace('newsvendor_config.csv','candidate_step,20','candidate_step,0.000001')
        self.invalid()

    def test_zero_underage_cost_rejected_explicitly(self):
        self.replace('newsvendor_config.csv','underage_cost,6','underage_cost,0')
        self.invalid()

    def test_zero_overage_cost_rejected_explicitly(self):
        self.replace('newsvendor_config.csv','overage_cost,2','overage_cost,0')
        self.invalid()

    def test_malformed_quote_rejected(self):
        with (self.inputs/'paths.csv').open('a') as f:
            f.write('"unfinished')
        self.invalid()

    def test_file_size_bounded(self):
        (self.inputs/'paths.csv').write_text('x'*1048577)
        self.invalid()

    def test_row_count_bounded(self):
        (self.inputs/'paths.csv').write_text('path,day1,day2,day3,weight\n'+''.join(f'p{i},10,10,10,1\n' for i in range(1001)))
        self.invalid()

    def test_initial_stock_wrong_day_rejected(self):
        self.replace('batches.csv','initial,initial,1,1,10','initial,initial,2,2,10')
        self.invalid()

    def test_invalid_source_type_rejected(self):
        self.replace('batches.csv','initial,initial,1,1,10','initial,unknown,1,1,10')
        self.invalid()

    def test_numeric_demand_duplicate_rejected(self):
        self.replace('newsvendor.csv','100,1','80.0,1')
        self.invalid()

    def test_formula_batch_id_rejected(self):
        self.replace('batches.csv','initial,initial','=1+1,initial')
        self.invalid()

    def test_formula_path_id_rejected(self):
        self.replace('paths.csv','p01,','+CMD,')
        self.invalid()

    def test_long_id_rejected(self):
        self.replace('paths.csv','p01,','a'*65+',')
        self.invalid()

    def test_reserved_batch_id_rejected(self):
        self.replace('batches.csv','initial,initial','new_order,initial')
        self.invalid()

    def test_truncated_enumeration_warns(self):
        self.replace('inventory_config.csv','candidate_max_kg,30','candidate_max_kg,10')
        summary=r.calculate(r.load(self.inputs))[0]
        self.assertEqual(summary['inventory_selected']['q'],D(10))
        self.assertTrue(summary['inventory_enumeration']['potentially_truncated'])
        self.assertTrue(summary['inventory_enumeration']['warning'])
        self.assertEqual(summary['inventory_enumeration']['stop_kg'],D(10))

    def test_base_enumeration_scope_is_explicit(self):
        e=self.summary['inventory_enumeration']
        self.assertEqual(e['stop_kg'],D(30))
        self.assertEqual(e['capacity_based_pack_ceiling_kg'],D(15))
        self.assertFalse(e['potentially_truncated'])
        self.assertIn('not a global optimum',e['selection_scope'])

    def test_rational_critical_quantile_jump_regression(self):
        self.replace('newsvendor_config.csv','underage_cost,6','underage_cost,2')
        self.replace('newsvendor_config.csv','overage_cost,2','overage_cost,15')
        (self.inputs/'newsvendor.csv').write_text('demand,weight\n80,2\n100,15\n')
        summary=r.calculate(r.load(self.inputs))[0]
        self.assertEqual(summary['newsvendor_quantile'],D(80))

    def test_exact_cost_ties_survive_display_rounding(self):
        self.replace('newsvendor_config.csv','underage_cost,6','underage_cost,1')
        self.replace('newsvendor_config.csv','overage_cost,2','overage_cost,5')
        self.replace('newsvendor_config.csv','candidate_stop,160','candidate_stop,100')
        self.replace('newsvendor_config.csv','candidate_step,20','candidate_step,5')
        (self.inputs/'newsvendor.csv').write_text('demand,weight\n80,1\n100,5\n')
        summary,table,_,_=r.calculate(r.load(self.inputs))
        self.assertEqual(summary['newsvendor_minimizers'],list(map(D,[80,85,90,95,100])))
        self.assertEqual(len({x['expected_cost'] for x in table}),1)
        self.assertEqual(table[0]['expected_cost'],D(100)/D(6))

    def test_ceil_exact_rational_above_boundary(self):
        # Below display precision: round only the exact rational, not its display.
        value=r.Fraction(100)+r.Fraction(1,10**80)
        self.assertEqual(r.ceil_pack(value,D(20)),D(120))

    def test_ceil_exact_rational_at_and_below_boundary(self):
        self.assertEqual(r.ceil_pack(r.Fraction(100),D(20)),D(100))
        self.assertEqual(r.ceil_pack(r.Fraction(100)-r.Fraction(1,10**80),D(20)),D(100))

    def test_decimal_input_ceil_far_beyond_context_precision(self):
        value=D('100.'+'0'*80+'1')
        self.assertEqual(r.ceil_pack(value,D(20)),D(120))

if __name__ == '__main__':
    unittest.main()
