"""Independent exact-arithmetic oracle and attacks on the issuance boundary."""
import copy
from datetime import date,timedelta
from fractions import Fraction as F
import math
import unittest
from baseline import forecast_at, load_csv, validate_development, windows
from metrics import evaluate
from run import ROOT, METHODS, CASES, issue, replay, leakage_diagnostics, stockout_counterexample, freeze, verify_source


def oracle(values, label, h):
    values = [F(str(v)) for v in values]
    if label == 'SNaive7':
        return values[-7+(h-1)%7]
    if label.startswith('MA'):
        k = int(label[2:]); return sum(values[-k:])/k
    a=F(label[3:]); n=len(values)
    return values[0]*(1-a)**(n-1)+sum(a*(1-a)**(n-1-i)*values[i] for i in range(1,n))


class BacktestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows={c:load_csv(ROOT/'data'/f'{c}-development.csv',meta[0]) for c,meta in CASES.items()}
        cls.results={c:replay(rows,c) for c,rows in cls.rows.items()}

    def test_source_hashes_and_only_development(self):
        self.assertEqual(len(verify_source()['files']),2)
        self.assertEqual(sorted(p.name for p in (ROOT/'data').iterdir()),['apparel-development.csv','hewei-development.csv'])
        for rows in self.rows.values():
            validate_development(rows)
            self.assertEqual(len(rows),140)

    def test_window_counts_and_edges(self):
        self.assertEqual(windows(113,140,1),[(i-1,i,i) for i in range(113,141)])
        self.assertEqual(windows(113,140,5),[(i-1,i,i+4) for i in range(113,137)])
        self.assertEqual(windows(113,114,5),[])
        for args in [(0,140,5),(113,112,1),(113,140,0),(113,140,True)]:
            with self.assertRaises(ValueError): windows(*args)

    def test_all_forecasts_with_fraction_oracle(self):
        for case,(forecasts,_,_) in self.results.items():
            self.assertEqual(len(forecasts),7*(28+24*5))
            rows=self.rows[case]
            for r in forecasts:
                expected=oracle([v['demand'] for v in rows[:r['origin_day']]],r['method'],r['h'])
                self.assertAlmostEqual(r['prediction'],float(expected),places=10)

    def test_all_dates_horizons_parameters_and_no_cross_block(self):
        for case,(forecasts,_,_) in self.results.items():
            for r in forecasts:
                self.assertEqual(r['target_day'],r['origin_day']+r['h'])
                self.assertEqual(date.fromisoformat(r['target_date']),date.fromisoformat(r['origin_date'])+timedelta(days=r['h']))
                self.assertEqual(r['history_last_day'],r['origin_day'])
                self.assertTrue(113<=r['target_day']<=140)
                self.assertTrue(1<=r['h']<=r['task_horizon'])
                self.assertTrue(r['parameters'])
                self.assertEqual(r['series'],CASES[case][0])

    def test_totals_equal_same_origin_forecasts(self):
        for _,(forecasts,totals,_) in self.results.items():
            self.assertEqual(len(totals),7*(28+24))
            for t in totals:
                rs=[r for r in forecasts if (r['method'],r['origin_day'],r['task_horizon'])==(t['method'],t['origin_day'],t['task_horizon'])]
                self.assertEqual(len(rs),t['task_horizon'])
                self.assertEqual(t['prediction'],math.fsum(r['prediction'] for r in rs))
                self.assertEqual(t['actual'],math.fsum(r['actual'] for r in rs))
                self.assertLessEqual(abs(t['error']),t['sum_daily_absolute_errors']+1e-12)

    def test_scores_against_exact_oracle(self):
        for case,(_,totals,scores) in self.results.items():
            rows=self.rows[case]
            for s in scores:
                ts=[t for t in totals if (t['method'],t['task_horizon'])==(s['method'],s['task_horizon'])]
                actual=[sum(F(str(v['demand'])) for v in rows[t['first_target_day']-1:t['last_target_day']]) for t in ts]
                pred=[sum(oracle([v['demand'] for v in rows[:t['origin_day']]],s['method'],h) for h in range(1,s['task_horizon']+1)) for t in ts]
                errors=[a-p for a,p in zip(actual,pred)]
                expected={'me':sum(errors)/len(errors),'mae':sum(map(abs,errors))/len(errors),
                          'rmse':math.sqrt(float(sum(e*e for e in errors)/len(errors))),
                          'wape':sum(map(abs,errors))/sum(actual)}
                for key,value in expected.items():self.assertAlmostEqual(s[key],float(value),places=10)
                self.assertEqual(s['n'],28 if s['task_horizon']==1 else 24)

    def test_all_future_and_prefix_attacks(self):
        for case,rows in self.rows.items():
            reports,_=leakage_diagnostics(rows,case)
            self.assertEqual(len(reports),24*7)
            # Cover the final four one-step origins as well.
            for origin in range(136,140):
                for label,args in METHODS:
                    self.assertEqual(issue(rows,origin,1,case,label,args),issue(rows[:origin]+[None]*4,origin,1,case,label,args))

    def test_full_replay_future_change_cannot_rewrite_prior_vintages(self):
        for case,rows in self.rows.items():
            altered=copy.deepcopy(rows)
            for r in altered[120:]:r.update(demand=r['demand']+1000,stockout=True)
            old=self.results[case][0];new=replay(altered,case)[0]
            for a,b in zip(old,new):
                if a['origin_day']<=120:self.assertEqual(a['prediction'],b['prediction'])

    def test_observed_history_can_update_next_origin(self):
        for case,rows in self.rows.items():
            altered=copy.deepcopy(rows);altered[112]['demand']+=10
            a={'method':'ses','alpha':.5}
            self.assertEqual(forecast_at(rows,112,5,**a),forecast_at(altered,112,5,**a))
            self.assertAlmostEqual(forecast_at(altered,113,1,**a)[0]-forecast_at(rows,113,1,**a)[0],5)

    def test_revisions_negative_control_is_detectably_wrong(self):
        for case,rows in self.rows.items():
            _,n=leakage_diagnostics(rows,case)
            self.assertNotAlmostEqual(n['fixed_total'],n['revised_total'])

    def test_no_full_sample_preprocessing(self):
        rows=self.rows['hewei']
        with self.assertRaises(ValueError):
            forecast_at([dict(r,demand=None) if i==20 else r for i,r in enumerate(rows)],112,1)
        self.assertEqual(forecast_at(rows,112,5),forecast_at(rows[:112]+[{'demand':'poison','stockout':True}],112,5))

    def test_reject_missing_duplicate_and_foreign_series(self):
        for change in ('missing','duplicate','foreign'):
            rows=copy.deepcopy(self.rows['hewei'])
            if change=='missing':rows[20]['demand']=None
            if change=='duplicate':rows[20]['date']=rows[19]['date']
            if change=='foreign':rows[20]['series']='other'
            with self.assertRaises(ValueError):replay(rows,'hewei')

    def test_sum_error_is_not_sum_absolute_error(self):
        actual=[0,4,2,2,2];pred=[2,2,2,2,2]
        self.assertEqual(abs(sum(actual)-sum(pred)),0)
        self.assertEqual(sum(abs(a-p) for a,p in zip(actual,pred)),4)

    def test_overlap_denominator_not_unique_volume(self):
        for case,(_,totals,scores) in self.results.items():
            unique=sum(r['demand'] for r in self.rows[case][112:])
            for s in scores:
                if s['task_horizon']==5:self.assertGreater(s['actual_sum'],unique)

    def test_stockout_different_statuses_not_zero_imputation(self):
        records,scores=stockout_counterexample()
        for case in CASES:
            rs={r['simulation_day']:r for r in records if r['case']==case}
            self.assertEqual(rs[3]['observed_sales'],0)
            self.assertEqual(rs[3]['latent_simulated_demand'],0)
            for day in (5,8):self.assertIsNone(rs[day]['observed_sales'])
            self.assertIsNone(rs[5]['latent_simulated_demand'])
            self.assertGreater(rs[8]['latent_simulated_demand'],0)
            self.assertEqual(rs[12]['observed_sales'],0)
            self.assertGreater(rs[12]['latent_simulated_demand'],0)
            for day in (6,7,12):self.assertEqual(rs[day]['observed_sales'],min(rs[day]['latent_simulated_demand'],rs[day]['capacity']))
        self.assertTrue(all(s['n']==12 for s in scores))

    def test_sales_perfect_does_not_imply_demand_perfect(self):
        records,_=stockout_counterexample()
        for r in records:
            if r['simulation_day']==6:
                self.assertEqual(r['observed_sales'],r['fixed_demo_prediction'])
                self.assertGreater(r['latent_simulated_demand'],r['fixed_demo_prediction'])

    def test_separate_stockout_does_not_mutate_main(self):
        before=copy.deepcopy(self.rows)
        stockout_counterexample()
        self.assertEqual(before,self.rows)

    def test_freeze_is_post_replay_min_mae_per_task(self):
        scores=sum((r[2] for r in self.results.values()),[])
        result=freeze(scores,verify_source())
        self.assertEqual(len(result['selected']),4)
        for selected in result['selected']:
            subset=[r for r in scores if (r['case'],r['task_horizon'])==(selected['case'],selected['task_horizon'])]
            self.assertEqual(selected['mae'],min(r['mae'] for r in subset))

    def test_metric_manual_zero_denominator_and_invalid(self):
        r=evaluate([0,10],[2,8])
        self.assertEqual([r[k] for k in ('mae','rmse','me','wape')],[2,2,0,.4])
        self.assertIsNone(evaluate([0,0],[2,0])['wape'])
        for actual,pred in [([],[]),([1],[1,2]),([None],[0]),([float('nan')],[0]),([-1],[0])]:
            with self.assertRaises(ValueError):evaluate(actual,pred)

    def test_moving_average_preserves_subnormal_mean(self):
        tiny = math.nextafter(0.0, 1.0)
        rows = [dict(r, demand=tiny) for r in self.rows['hewei'][:3]]
        self.assertEqual(forecast_at(rows,3,5,method='moving_average',k=3),[tiny]*5)

    def test_moving_average_rejects_unrepresentable_mean(self):
        tiny = math.nextafter(0.0, 1.0)
        rows = [dict(r,demand=v) for r,v in zip(self.rows['hewei'][:3],[tiny,0,0])]
        with self.assertRaisesRegex(ValueError,'underflows'):
            forecast_at(rows,3,1,method='moving_average',k=3)
        self.assertEqual(forecast_at([dict(r,demand=0) for r in rows],3,1,method='moving_average',k=3),[0])

    def test_moving_average_requires_finite_aggregate(self):
        rows = [dict(r,demand=1e308) for r in self.rows['hewei'][:3]]
        with self.assertRaisesRegex(ValueError,'sum exceeds'):
            forecast_at(rows,3,1,method='moving_average',k=3)
        for r in rows:r['demand']=1e307
        self.assertEqual(forecast_at(rows,3,1,method='moving_average',k=3),[1e307])


if __name__=='__main__':unittest.main()
