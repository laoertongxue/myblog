import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import run

class InventoryTests(unittest.TestCase):
    def setUp(self):
        self.p = dict(policy='daily_sQ',L=2,R=1,Q=6,fixed_threshold=10)
        self.d = [7,9,8,4,5,6,3]
        self.pipeline = [dict(id='initial',quantity=8,arrival_day=2)]

    def play(self, **kw):
        args = dict(demands=self.d,history=[],params=self.p,initial_oh=12,initial_pipeline=self.pipeline,start=1)
        args.update(kw)
        return run.simulate(**args)

    def test_hand_daily_full_ledger(self):
        rows, events, pending, s=self.play()
        self.assertEqual([(r['arrivals'],r['fulfilled'],r['lost'],r['end_oh'],r['pipeline_before'],r['ip_before'],r['ordered']) for r in rows],
            [(0,7,0,5,8,13,0),(8,9,0,4,0,4,6),(0,4,4,0,6,6,6),(0,0,4,0,12,12,0),(6,5,0,1,6,7,6),(6,6,0,1,6,7,6),(0,1,2,0,12,12,0)])
        self.assertEqual(s['lost'],10)
        self.assertEqual([(o['arrival_day'],o['quantity']) for o in pending],[(8,6),(9,6)])

    def test_hand_periodic_full_ledger(self):
        p=dict(policy='periodic_RS',L=2,R=3,fixed_threshold=20)
        rows,_,_,s=self.play(params=p)
        self.assertEqual([(r['arrivals'],r['fulfilled'],r['lost'],r['end_oh'],r['ordered']) for r in rows],
                         [(0,7,0,5,7),(8,9,0,4,0),(0,4,4,0,0),(7,4,0,3,17),(0,3,2,0,0),(0,0,6,0,0),(17,3,0,14,6)])
        self.assertEqual(s['lost'],12)

    def test_conservation_all_candidates(self):
        outputs=run.build()
        import csv,io
        rows=list(csv.DictReader(io.StringIO(outputs['ledger.csv'].decode())))
        for r in rows:
            n={k:int(v) for k,v in r.items() if k not in ('case','candidate','unit','arrival_day')}
            self.assertEqual(n['demand'],n['fulfilled']+n['lost'])
            self.assertEqual(n['opening_oh']+n['arrivals']-n['fulfilled'],n['end_oh'])
            self.assertEqual(n['pipeline_before']+n['ordered'],n['pipeline_after'])
            self.assertGreaterEqual(n['end_oh'],0)
            self.assertEqual(n['ip_before'],n['end_oh']+n['pipeline_before'])
        frozen=json.loads(outputs['frozen_config.json'])
        for r in json.loads(outputs['results.json']):
            self.assertEqual(frozen['cases'][r['case']]['initial_oh']+r['arrivals']-r['fulfilled'],r['end_oh'])
            self.assertEqual(r['ordered']-r['arrivals'],r['end_pipeline'])

    def test_equal_threshold_and_no_repeat(self):
        rows,*_=self.play(demands=[0],initial_oh=10,initial_pipeline=[])
        self.assertEqual(rows[0]['ordered'],6)
        rows,*_=self.play(demands=[0],initial_oh=0,initial_pipeline=[])
        self.assertEqual(rows[0]['ordered'],6)
        self.assertEqual(rows[0]['ip_after'],6)
        rows,*_=self.play(demands=[0],initial_oh=11,initial_pipeline=[])
        self.assertEqual(rows[0]['ordered'],0)

    def test_zero_lead_is_next_day(self):
        p=dict(self.p,L=0)
        rows,*_=self.play(demands=[20,6],params=p,initial_pipeline=[])
        self.assertEqual(rows[0]['lost'],8)
        self.assertEqual(rows[0]['arrivals'],0)
        self.assertEqual(rows[1]['arrivals'],6)

    def test_future_perturbation(self):
        data=run.load_data('hewei')
        p=dict(policy='periodic_RS',L=2,R=3,z=1,scale=2)
        baseline=run.simulate(data[112:],data[:112],p,80)[0]
        for cut in range(1,28):
            demand=data[112:112+cut]+[999999]*(28-cut)
            changed=run.simulate(demand,data[:112],p,80)[0]
            self.assertEqual(baseline[:cut],changed[:cut])

    def test_predictor_independent_of_sales(self):
        data=run.load_data('hewei')
        p=dict(policy='daily_sQ',L=2,R=1,Q=30,z=1,scale=2)
        a=run.simulate(data[112:],data[:112],p,0)[0]
        b=run.simulate(data[112:],data[:112],p,100000)[0]
        self.assertNotEqual([r['fulfilled'] for r in a],[r['fulfilled'] for r in b])
        self.assertEqual([r['threshold'] for r in a],[r['threshold'] for r in b])

    def test_zero_demand_fill_rate_undefined(self):
        rows,_,_,s=self.play(demands=[0]*7)
        self.assertIsNone(s['fill_rate'])
        self.assertEqual(s['lost'],0)

    def test_rounding_up(self):
        p=dict(policy='periodic_RS',L=2,R=3,z=1,scale=.01)
        rows,*_=self.play(demands=[0],history=[0]*112,params=p,initial_oh=0,initial_pipeline=[])
        self.assertEqual(rows[0]['threshold'],1)
        self.assertEqual(rows[0]['ordered'],1)

    def test_inputs_not_mutated(self):
        old=copy.deepcopy((self.p,self.pipeline,self.d))
        self.play()
        self.assertEqual(old,(self.p,self.pipeline,self.d))

    def test_invalid_demands(self):
        for value in (-1,True,1.5,float('nan'),float('inf'),'3',None):
            with self.subTest(value=value),self.assertRaises(ValueError):self.play(demands=[value])
        with self.assertRaises(ValueError):self.play(demands=[])

    def test_invalid_parameters(self):
        for field,value in [('L',-1),('R',0),('R',3),('Q',0),('Q',True),('policy','unknown'),('fixed_threshold',-1)]:
            with self.subTest(field=field,value=value),self.assertRaises(ValueError):self.play(params=dict(self.p,**{field:value}))
        for scale in (-1,float('inf'),float('nan'),True):
            p=dict(policy='daily_sQ',L=2,R=1,Q=6,z=1,scale=scale)
            with self.assertRaises(ValueError):self.play(params=p,history=[1]*112)

    def test_initial_order_validation(self):
        for pipeline in ([self.pipeline[0],self.pipeline[0]], [dict(id='a',quantity=0,arrival_day=2)], [dict(id='a',quantity=1,arrival_day=0)]):
            with self.assertRaises(ValueError):self.play(initial_pipeline=pipeline)

    def test_arrival_once_same_date_distinct_orders(self):
        pipeline=[dict(id='a',quantity=3,arrival_day=1),dict(id='b',quantity=4,arrival_day=1)]
        rows,events,_,_=self.play(demands=[0,0],initial_pipeline=pipeline)
        self.assertEqual([r['arrivals'] for r in rows],[7,0])
        self.assertEqual(len([e for e in events if e['event']=='arrival']),2)

    def test_tail_not_discarded(self):
        rows,_,pending,s=self.play(demands=[20],initial_pipeline=[])
        self.assertEqual(s['end_pipeline'],6)
        self.assertEqual(pending[0]['arrival_day'],4)
        self.assertEqual(s['arrivals'],0)

    def test_training_windows(self):
        for H,n in [(3,103),(5,101)]:
            rms,count=run.error_scale([1]*112,H)
            self.assertEqual((rms,count),(0,n))
        with self.assertRaises(ValueError):run.error_scale([1]*140,5)

    def test_forecast_seasonal_and_historical(self):
        self.assertEqual(run.forecast([1,2,3,4,5,6,7],9),[1,2,3,4,5,6,7,1,2])
        with self.assertRaises(ValueError):run.forecast([1]*6,5)

    def test_deterministic_and_frozen(self):
        self.assertEqual(run.build(),run.build())
        run.verify()

    def test_tampering_refused_no_baseline_rewrite(self):
        import shutil
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)/'practice'
            shutil.copytree(run.ROOT,root,ignore=shutil.ignore_patterns('__pycache__'))
            original=(root/'output/frozen_config.json').read_bytes()
            (root/'output/frozen_config.json').write_bytes(original+b' ')
            with patch.object(run,'ROOT',root),self.assertRaisesRegex(ValueError,'integrity mismatch'):
                run.verify()
            self.assertEqual((root/'output/frozen_config.json').read_bytes(),original+b' ')

    def test_apparel_manual_independent_rows(self):
        demand=[5,8,4,7,3,6,2]
        initial=[dict(id='initial',quantity=4,arrival_day=1)]
        expected={
            'daily_sQ':[(4,5,0,5,6),(0,5,3,0,6),(0,0,4,0,0),(6,6,1,0,6),(6,3,0,3,0),(0,3,3,0,6),(6,2,0,4,0)],
            'periodic_RS':[(4,5,0,5,13),(0,5,3,0,0),(0,0,4,0,0),(13,7,0,6,12),(0,3,0,3,0),(0,3,3,0,0),(12,2,0,10,8)]}
        for policy,R,threshold in [('daily_sQ',1,8),('periodic_RS',3,18)]:
            p=dict(policy=policy,L=2,R=R,Q=6,fixed_threshold=threshold)
            rows,*_=self.play(demands=demand,initial_oh=6,initial_pipeline=initial,params=p)
            self.assertEqual([(r['arrivals'],r['fulfilled'],r['lost'],r['end_oh'],r['ordered']) for r in rows],expected[policy])

    def test_training_rms_independent_reference(self):
        from fractions import Fraction
        for case in run.SOURCES:
            train=run.load_data(case)[:112]
            for H in (3,5):
                errors=[]
                for origin in range(7,113-H):
                    prediction=sum(train[origin-7:origin-7+H])
                    errors.append(sum(train[origin:origin+H])-prediction)
                square=Fraction(sum(e*e for e in errors),len(errors))
                rms,n=run.error_scale(train,H)
                self.assertAlmostEqual(rms*rms,float(square),places=10)
                self.assertEqual(n,len(errors))

    def test_training_errors_export_stays_inside_training(self):
        import csv, io
        result=run.build()
        rows=list(csv.DictReader(io.StringIO(result['training_errors.csv'].decode())))
        self.assertEqual(len(rows),408)
        scales=json.loads(result['training_scales.json'])
        for case in run.SOURCES:
            for policy,H in [('daily_sQ',3),('periodic_RS',5)]:
                subset=[r for r in rows if r['case']==case and int(r['horizon'])==H]
                errors=[int(r['error']) for r in subset]
                self.assertEqual(len(subset),scales[case][policy]['n'])
                self.assertAlmostEqual(sum(e*e for e in errors)/len(errors),scales[case][policy]['rms']**2)
                for r in subset:
                    self.assertEqual(int(r['target_start']),int(r['origin'])+1)
                    self.assertEqual(int(r['target_end']),int(r['origin'])+H)
                    self.assertLessEqual(int(r['target_end']),112)
                    self.assertEqual(int(r['actual_sum'])-int(r['forecast_sum']),int(r['error']))

    def test_candidate_rank_and_future_plan_contract(self):
        result=run.build()
        config=json.loads(result['frozen_config.json'])
        rows=json.loads(result['results.json'])
        self.assertEqual(len(rows),18)
        for case in run.SOURCES:
            for policy in ('daily_sQ','periodic_RS'):
                group=[r for r in rows if r['case']==case and r['parameters']['policy']==policy]
                ordered=sorted(group,key=lambda r:(r['lost'],r['mean_end_oh'],r['order_count'],run.canonical(r['parameters'])))
                self.assertEqual(config['cases'][case]['winners'][policy]['candidate'],ordered[0]['candidate'])
        self.assertEqual(config['future_plan']['inventory_run_days'],[153,180])
        self.assertEqual(config['future_plan']['review_anchor'],153)
        self.assertNotIn('inventory_warmup_days',config['future_plan'])
        self.assertEqual(config['future_plan']['five_day_origins'],[140,175])

    def test_no_test_labels_read(self):
        seen=[]
        original=Path.read_bytes
        def guarded(path):
            seen.append(str(path))
            self.assertNotIn('sealed',path.parts)
            return original(path)
        with patch.object(Path,'read_bytes',guarded):run.build()
        self.assertEqual(len([p for p in seen if p.endswith('-development.csv')]),2)

if __name__=='__main__':unittest.main()
