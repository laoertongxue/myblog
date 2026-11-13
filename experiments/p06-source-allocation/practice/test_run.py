import copy, csv, hashlib, json, shutil, subprocess, sys, tempfile, unittest
from fractions import Fraction as F
from pathlib import Path
import run

class TestPlan(unittest.TestCase):
    def setUp(self):
        self.h=json.loads((run.ROOT/'inputs/hewei.json').read_text())
        self.a=json.loads((run.ROOT/'inputs/apparel.json').read_text())
    def test_hewei_exact(self):
        r=run.solve(self.h);self.assertEqual(r['candidate_count'],42)
        self.assertEqual(r['expected']['selected']['plan'],(10,20,0));self.assertEqual(r['expected']['selected']['expected_cost'],112)
        self.assertEqual(r['high_service']['selected']['plan'],(20,20,0));self.assertEqual(r['high_service']['selected']['expected_cost'],119)
    def test_apparel_exact(self):
        r=run.solve(self.a);self.assertEqual(r['candidate_count'],191)
        self.assertEqual(r['expected']['selected']['plan'],(0,40,50));self.assertEqual(r['expected']['selected']['expected_cost'],502)
        self.assertEqual(r['high_service']['selected']['plan'],(10,40,50));self.assertEqual(r['high_service']['selected']['expected_cost'],536)
    def test_weighted_shortage_and_surplus(self):
        h=run.solve(self.h)['expected']['selected'];a=run.solve(self.a)['expected']['selected']
        self.assertEqual((h['expected_shortage'],h['expected_surplus']),(3,2));self.assertEqual((a['expected_shortage'],a['expected_surplus']),(3,11))
        self.assertEqual((31-h['expected_shortage'])/31,F(28,31));self.assertEqual((82-a['expected_shortage'])/82,F(79,82))
    def test_scenario_costs(self):
        self.assertEqual([x['total_cost'] for x in run.evaluate(self.h,(10,20,0))['scenarios']],[90,80,180])
        self.assertEqual([x['total_cost'] for x in run.evaluate(self.a,(0,40,50))['scenarios']],[480,440,620])
    def test_high_costs(self):
        self.assertEqual([x['total_cost'] for x in run.evaluate(self.h,(20,20,0))['scenarios']],[130,120,110])
        self.assertEqual([x['total_cost'] for x in run.evaluate(self.a,(10,40,50))['scenarios']],[580,540,500])
    def test_greedy_counterexample(self):
        self.h['scenarios']=[{'name':'确定','demand':10,'probability':'1'}]
        self.assertEqual(run.evaluate(self.h,(0,10,0))['expected_cost'],40)
        self.assertEqual(run.solve(self.h)['expected']['selected']['plan'],(10,0,0))
    def test_fixed_cost_paid_once(self):
        self.assertEqual(run.evaluate(self.h,(0,20,0))['supply_cost'],50)
    def test_zero_source_no_fixed_charge(self):
        self.assertEqual(run.evaluate(self.a,(0,0,0))['supply_cost'],0)
    def test_material_limit(self):
        self.assertEqual(run.source_caps(self.a),(80,40,50))
        with self.assertRaises(ValueError):run.evaluate(self.a,(0,0,60))
    def test_donor_reserve(self):
        with self.assertRaises(ValueError):run.evaluate(self.h,(0,25,0))
    def test_arrival_late_excluded(self):
        self.h['transfer']['arrival_at']='2026-01-02T08:00:01+08:00'
        self.assertEqual(run.solve(self.h)['effective_caps'][1],0)
        self.assertEqual(run.solve(self.h)['expected']['selected']['plan'],(30,0,0))
    def test_arrival_exact_cutoff_included(self):
        self.h['transfer']['arrival_at']=self.h['deadline'];self.assertEqual(run.source_caps(self.h)[1],20)
    def test_equal_instants_different_timezones(self):
        self.h['transfer']['arrival_at']='2026-01-02T00:00:00+00:00';self.assertEqual(run.source_caps(self.h)[1],20)
    def test_future_version_rejected(self):
        self.h['known_at']='2026-01-01T08:00:01+08:00'
        with self.assertRaises(ValueError):run.solve(self.h)
    def test_known_at_exact_decision_allowed(self):
        self.h['known_at']=self.h['decision_at'];run.solve(self.h)
    def test_naive_timestamp_rejected(self):
        self.h['known_at']='2026-01-01T07:00:00'
        with self.assertRaises(ValueError):run.solve(self.h)
    def test_reversed_time_rejected(self):
        self.h['deadline']=self.h['decision_at']
        with self.assertRaises(ValueError):run.solve(self.h)
    def test_past_new_arrival_rejected(self):
        self.h['purchase']['arrival_at']='2025-12-31T08:00:00+08:00'
        with self.assertRaises(ValueError):run.solve(self.h)
    def test_capacity_impossible_high_service(self):
        self.h['receive_capacity']=35;r=run.solve(self.h)
        self.assertEqual(r['high_service']['status'],'INFEASIBLE');self.assertIsNone(r['high_service']['selected'])
    def test_zero_capacity_still_expectation_feasible(self):
        self.h['receive_capacity']=0;r=run.solve(self.h)
        self.assertEqual(r['candidate_count'],1);self.assertEqual(r['expected']['selected']['expected_cost'],310)
    def test_zero_demand(self):
        self.h['scenarios']=[{'name':'无缺口','demand':0,'probability':'1'}]
        self.assertEqual(run.solve(self.h)['expected']['selected']['plan'],(0,0,0))
    def test_batch_floor(self):
        self.h['transfer']['donor_stock']=33
        self.assertEqual(max(r['plan'][1] for r in run.enumerate_plans(self.h)),15)
    def test_malformed_quantities(self):
        for v in (-1,True,1.5,'5',None):
            with self.subTest(v=v):
                c=copy.deepcopy(self.h);c['batch']=v
                with self.assertRaises(ValueError):run.solve(c)
    def test_zero_batch(self):
        self.h['batch']=0
        with self.assertRaises(ValueError):run.solve(self.h)
    def test_bad_probabilities(self):
        for v in ('NaN','Infinity','1/0','-0.2','0',True,0.2):
            with self.subTest(v=v):
                c=copy.deepcopy(self.h);c['scenarios'][0]['probability']=v
                with self.assertRaises(ValueError):run.solve(c)
    def test_probability_sum(self):
        self.h['scenarios'][0]['probability']='0.21'
        with self.assertRaises(ValueError):run.solve(self.h)
    def test_fractional_probabilities_exact(self):
        for s in self.h['scenarios']:s['probability']='1/3'
        run.solve(self.h)
    def test_duplicate_scenario_name(self):
        self.h['scenarios'][1]['name']='低'
        with self.assertRaises(ValueError):run.solve(self.h)
    def test_empty_scenarios(self):
        self.h['scenarios']=[]
        with self.assertRaises(ValueError):run.solve(self.h)
    def test_bad_reserve(self):
        self.h['transfer']['donor_reserve']=36
        with self.assertRaises(ValueError):run.solve(self.h)
    def test_zero_material_rate(self):
        self.a['production']['material_per_unit']=0
        with self.assertRaises(ValueError):run.solve(self.a)
    def test_wrong_unit(self):
        self.h['unit']='piece'
        with self.assertRaises(ValueError):run.solve(self.h)
    def test_unknown_field(self):
        self.h['future_actual']=40
        with self.assertRaises(ValueError):run.solve(self.h)
    def test_no_scenario_reoptimization(self):
        r=run.solve(self.h)['expected']['selected']
        self.assertEqual([s['shortage'] for s in r['scenarios']],[0,0,10])
        self.assertEqual(r['plan'],(10,20,0))
    def test_probability_changes_do_not_modify_candidate_supply(self):
        x=run.enumerate_plans(self.h)
        self.h['scenarios'][0]['probability']='0.3';self.h['scenarios'][2]['probability']='0.2'
        y=run.enumerate_plans(self.h)
        self.assertEqual([(r['plan'],r['supply_cost']) for r in x],[(r['plan'],r['supply_cost']) for r in y])
    def test_exact_ties_preserved(self):
        self.h['purchase']['unit_cost']='0.1';self.h['transfer']['unit_cost']='1/10';self.h['transfer']['fixed_cost']='0'
        self.h['scenarios']=[{'name':'确定','demand':10,'probability':'1'}]
        r=run.solve(self.h)['expected'];self.assertEqual(r['all_optimal_plans'],[(0,10,0),(5,5,0),(10,0,0)])
        self.assertEqual(r['selected']['plan'],(0,10,0));self.assertEqual(r['selected']['expected_cost'],1)
    def test_bad_plan(self):
        for p in [(1,0,0),(-5,0,0),(True,0,0),(40,20,0),(0,0),None]:
            with self.subTest(p=p):
                with self.assertRaises(ValueError):run.evaluate(self.h,p)
    def test_negative_cost(self):
        self.h['shortage_cost']='-1'
        with self.assertRaises(ValueError):run.solve(self.h)
    def test_nonempty_title(self):
        self.h['title']=''
        with self.assertRaises(ValueError):run.solve(self.h)
    def test_reproducible_from_other_cwd(self):
        with tempfile.TemporaryDirectory() as d:
            out=Path(d)/'out'
            subprocess.run([sys.executable,str(run.ROOT/'run.py'),'--output-dir',str(out)],cwd=d,check=True)
            for f in (run.ROOT/'outputs').glob('*'):
                self.assertEqual(f.read_bytes(),(out/f.name).read_bytes())
    def test_input_is_not_mutated(self):
        old=copy.deepcopy(self.h);run.solve(self.h);self.assertEqual(old,self.h)
    def test_all_candidates_satisfy_invariants(self):
        for c in (self.h,self.a):
            for r in run.enumerate_plans(c):
                for s in r['scenarios']:
                    self.assertEqual(r['quantity']-s['surplus'],s['demand']-s['shortage'])
                    self.assertFalse(s['shortage'] and s['surplus'])

    def test_late_arrival_exercise_end_to_end(self):
        with tempfile.TemporaryDirectory() as d:
            folder=Path(d);shutil.copytree(run.ROOT/'inputs',folder/'inputs')
            c=json.loads((folder/'inputs/hewei.json').read_text())
            c['transfer']['arrival_at']='2026-01-02T08:00:01+08:00'
            (folder/'inputs/hewei.json').write_text(json.dumps(c))
            run.run(folder/'inputs',folder/'out')
            result=json.loads((folder/'out/hewei_result.json').read_text())
            self.assertEqual(result['expected']['selected']['plan'],[30,0,0])
            self.assertEqual(result['expected']['selected']['expected_cost'],'122')
            self.assertEqual(len(list((folder/'out').iterdir())),7)
            counter=json.loads((folder/'out/greedy_counterexample.json').read_text())
            self.assertEqual(counter['cheap_unit_first']['status'],'FEASIBLE')
    def test_independent_counterexample_infeasible_probe(self):
        with tempfile.TemporaryDirectory() as d:
            folder=Path(d);shutil.copytree(run.ROOT/'inputs',folder/'inputs')
            p=folder/'inputs/counterexample.json';c=json.loads(p.read_text())
            c['transfer']['arrival_at']='2026-01-02T08:00:01+08:00';p.write_text(json.dumps(c))
            run.run(folder/'inputs',folder/'out')
            counter=json.loads((folder/'out/greedy_counterexample.json').read_text())
            self.assertEqual(counter['cheap_unit_first']['status'],'INFEASIBLE')
            self.assertIsNone(counter['cheap_unit_first']['evaluation'])
            self.assertEqual(counter['all_purchase']['status'],'FEASIBLE')
    def test_invalid_last_input_writes_nothing(self):
        with tempfile.TemporaryDirectory() as d:
            folder=Path(d);shutil.copytree(run.ROOT/'inputs',folder/'inputs')
            p=folder/'inputs/counterexample.json';c=json.loads(p.read_text())
            c['batch']=0;p.write_text(json.dumps(c))
            with self.assertRaises(ValueError):run.run(folder/'inputs',folder/'out')
            self.assertFalse((folder/'out').exists())
    def test_all_candidate_scenario_cost_rows(self):
        for name,count in [('hewei',126),('apparel',573)]:
            with (run.ROOT/f'outputs/{name}_candidate_scenarios.csv').open() as f:rows=list(csv.DictReader(f))
            self.assertEqual(len(rows),count)
            totals={}
            for r in rows:
                key=tuple(int(r[k]) for k in run.SOURCE_NAMES)
                totals[key]=totals.get(key,F(0))+F(r['weighted_cost'])
                self.assertEqual(F(r['weighted_cost']),F(r['probability'])*F(r['total_cost']))
            c=json.loads((run.ROOT/f'inputs/{name}.json').read_text())
            self.assertEqual(totals,{r['plan']:r['expected_cost'] for r in run.enumerate_plans(c)})

    def test_infeasible_target_and_reachable_bound(self):
        self.h['receive_capacity']=35
        r=run.solve(self.h);b=r['high_service']
        self.assertEqual(b['required_quantity'],40)
        self.assertEqual(b['max_feasible_quantity'],35)
        self.assertIn('最大可达总量仅35',b['reason'])
        self.assertEqual(r['bound_explanation']['receive_capacity'],35)
    def test_snapshot_and_hash_reproducible(self):
        r=run.solve(self.h)
        self.assertEqual(r['input_snapshot'],self.h)
        canonical=json.dumps(r['input_snapshot'],ensure_ascii=False,sort_keys=True,separators=(',',':'))
        self.assertEqual(r['input_sha256'],hashlib.sha256(canonical.encode('utf-8')).hexdigest())
        r['input_snapshot']['title']='改变结果快照'
        self.assertNotEqual(r['input_snapshot']['title'],self.h['title'])
    def test_hash_changes_with_inputs(self):
        a=run.solve(self.h)['input_sha256'];self.h['receive_capacity']=35
        self.assertNotEqual(a,run.solve(self.h)['input_sha256'])
    def test_wrong_case_filename_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            folder=Path(d);shutil.copytree(run.ROOT/'inputs',folder/'inputs')
            shutil.copyfile(folder/'inputs/apparel.json',folder/'inputs/hewei.json')
            with self.assertRaises(ValueError):run.run(folder/'inputs',folder/'out')
            self.assertFalse((folder/'out').exists())

if __name__=='__main__':unittest.main()
