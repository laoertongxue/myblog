"""Independent arithmetic, information-boundary and data-contract checks."""
import unittest
import math
from fractions import Fraction as F
from copy import deepcopy
from datetime import date, timedelta
from baseline import forecast_at, load_csv, validate_development, windows
from metrics import evaluate
from run import ROOT, CASES, METHODS, compare, verify_source


def fixture(values):
    return [{'day':i+1,'date':(date(2026,1,1)+timedelta(days=i)).isoformat(),
             'demand':v,'series':'synthetic'} for i,v in enumerate(values)]


class MetricsTests(unittest.TestCase):
    def test_hand_example(self):
        result = evaluate([0,10],[2,8])
        for key,value in {'mae':2,'rmse':2,'me':0,'wape':.4,'n':2}.items():
            self.assertAlmostEqual(result[key],value)

    def test_asymmetric_error_and_order_reversal(self):
        r=evaluate([10,10],[7,14])
        for k,v in {'me':-.5,'mae':3.5,'rmse':math.sqrt(12.5),'wape':.35}.items():
            self.assertAlmostEqual(r[k],v)
        a=evaluate([10]*4,[7]*4)
        b=evaluate([10]*4,[10,10,10,2])
        self.assertLess(b['mae'],a['mae'])
        self.assertGreater(b['rmse'],a['rmse'])
        self.assertEqual(evaluate([0,10],[5,10])['wape'],.5)
        for r in (r,a,b): self.assertLessEqual(abs(r['me']),r['mae']); self.assertLessEqual(r['mae'],r['rmse'])

    def test_zero_total_is_undefined_even_if_perfect(self):
        for pred in ([0,0],[2,0]):
            result=evaluate([0,0],pred)
            self.assertIsNone(result['wape'])
            self.assertEqual(result['wape_status'],'undefined_zero_actual_sum')

    def test_zero_rows_not_dropped(self):
        self.assertAlmostEqual(evaluate([0,10],[2,8])['wape'],.4)
        self.assertEqual(evaluate([0,10],[2,8])['n'],2)

    def test_sign_and_cancellation(self):
        self.assertEqual(evaluate([3],[1])['me'],2)
        self.assertEqual(evaluate([1],[3])['me'],-2)
        self.assertEqual(evaluate([10,10],[0,20])['me'],0)
        self.assertEqual(evaluate([10,10],[0,20])['mae'],10)

    def test_rmse_penalizes_large_miss(self):
        steady=evaluate([10]*4,[8]*4)
        spike=evaluate([10]*4,[10,10,10,2])
        self.assertEqual(steady['mae'],spike['mae'])
        self.assertEqual(steady['rmse'],2)
        self.assertEqual(spike['rmse'],4)

    def test_invalid_inputs(self):
        for actual,pred in [([],[]),([1],[1,2]),([math.nan],[0]),([1],[math.inf]),
                            ([-1],[0]),([True],[0]),([1],['1']),([None],[0]),([10**1000],[0])]:
            with self.subTest(actual=actual,pred=pred),self.assertRaises(ValueError):
                evaluate(actual,pred)

    def test_negative_predictions_remain_errors(self):
        self.assertEqual(evaluate([2],[-2])['mae'],4)

    def test_large_finite_rmse(self):
        self.assertEqual(evaluate([1e200],[0])['rmse'],1e200)

    def test_overflow_fails(self):
        with self.assertRaises(ValueError): evaluate([1e308],[-1e308])
        with self.assertRaises(ValueError): evaluate([1e308,1e308],[0,0])

    def test_smallest_subnormal_mean_survives(self):
        tiny = math.ulp(0.0)
        r = evaluate([tiny, tiny], [0, 0])
        self.assertEqual(r['me'], tiny)
        self.assertEqual(r['mae'], tiny)
        self.assertEqual(r['rmse'], tiny)
        self.assertEqual(r['wape'], 1.0)
        # Exact equality matters: assertAlmostEqual would accept the old zero bug.
        r = evaluate([0, 0], [tiny, tiny])
        self.assertEqual(r['me'], -tiny)
        self.assertEqual(r['mae'], tiny)
        self.assertEqual(r['rmse'], tiny)
        self.assertIsNone(r['wape'])

    def test_subnormal_cancellation_is_legitimate(self):
        tiny = math.ulp(0.0)
        r = evaluate([tiny, 0], [0, tiny])
        self.assertEqual(r['me'], 0)
        self.assertEqual(r['mae'], tiny)
        self.assertEqual(r['rmse'], tiny)
        self.assertEqual(r['wape'], 2.0)

    def test_unrepresentable_nonzero_means_rejected(self):
        tiny = math.ulp(0.0)
        with self.assertRaisesRegex(ValueError, 'underflows'):
            evaluate([tiny, 0], [0, 0])
        with self.assertRaisesRegex(ValueError, 'underflows'):
            evaluate([0, 0], [tiny, 0])
        with self.assertRaisesRegex(ValueError, 'underflows'):
            evaluate([tiny, tiny, 0], [0, 0, tiny])

    def test_wape_range_checks(self):
        tiny = math.ulp(0.0)
        with self.assertRaisesRegex(ValueError, 'underflows'):
            evaluate([1e308, 0], [1e308, 1e-100])
        with self.assertRaises(ValueError):
            evaluate([tiny], [1e308])

    def test_finite_large_values_without_squared_overflow(self):
        r = evaluate([1e307, 1e307], [0, 0])
        self.assertEqual(r['me'], 1e307)
        self.assertEqual(r['mae'], 1e307)
        self.assertEqual(r['rmse'], 1e307)
        self.assertEqual(r['wape'], 1)

    def test_absolute_error_aggregate_overflow_rejected(self):
        with self.assertRaises(ValueError):
            evaluate([0, 0], [1e308, -1e308])

    def test_wape_can_exceed_one(self):
        self.assertEqual(evaluate([1],[4])['wape'],3)

    def test_scale_and_order_identity(self):
        for pred in ([2,8],[0,10],[4,6]):
            r=evaluate([0,10],pred)
            self.assertAlmostEqual(r['wape'],r['mae']/5)
            scaled=evaluate([0,100],[p*10 for p in pred])
            self.assertEqual(scaled['wape'],r['wape'])
            self.assertAlmostEqual(scaled['mae'],r['mae']*10)

    def test_group_aggregation(self):
        a=evaluate([0,10],[2,8]); b=evaluate([20],[15]); all_=evaluate([0,10,20],[2,8,15])
        self.assertAlmostEqual(all_['mae'],(2*a['mae']+b['mae'])/3)
        self.assertAlmostEqual(all_['rmse']**2,(2*a['rmse']**2+b['rmse']**2)/3)
        self.assertAlmostEqual(all_['wape'],(a['absolute_error_sum']+b['absolute_error_sum'])/30)


class ForecastTests(unittest.TestCase):
    def test_fixed_origin_hand_predictions(self):
        rows=fixture([1,2,3,4,5,6,7,8])
        self.assertEqual(forecast_at(rows,7,5,method='seasonal_naive_7'),[1,2,3,4,5])
        self.assertEqual(forecast_at(rows,7,5,method='moving_average',k=3),[6]*5)
        self.assertEqual(forecast_at(fixture([10,20]),2,5,alpha=.5),[15]*5)

    def test_future_poison_does_not_change_predictions(self):
        rows=fixture(list(range(1,141)))
        poisoned=deepcopy(rows)
        poisoned[112:]=[{'bad':'future'}]*28
        for label,args in METHODS:
            self.assertEqual(forecast_at(rows,112,5,**args),forecast_at(poisoned,112,5,**args),label)

    def test_windows_do_not_cross_boundaries(self):
        self.assertEqual(windows(113,140,5)[0],(112,113,117))
        self.assertEqual(windows(113,140,5)[-1],(135,136,140))
        self.assertEqual(len(windows(113,140,5)),24)
        self.assertEqual(len(windows(113,140,1)),28)

    def test_source_hashes_and_development_contract(self):
        verify_source()
        for case,(identity,_,__) in CASES.items():
            rows=load_csv(ROOT/'data'/f'{case}-development.csv',identity)
            validate_development(rows)
            for change in ('date','split','length','negative'):
                bad=deepcopy(rows)
                if change=='date': bad[10]['date']=bad[9]['date']
                if change=='split': bad[112]['split']='train'
                if change=='length': bad.pop()
                if change=='negative': bad[3]['demand']=-1
                with self.assertRaises(ValueError): validate_development(bad)

    def test_fraction_oracle_all_targets_and_metrics(self):
        for case,(identity,unit,total_unit) in CASES.items():
            rows=load_csv(ROOT/'data'/f'{case}-development.csv',identity)
            vals=[F(str(r['demand'])) for r in rows]
            daily,totals,scores=compare(rows,case,unit,total_unit)
            self.assertEqual(len(daily),196);self.assertEqual(len(totals),168)
            for label,args in METHODS:
                oracle=[]
                for origin in range(112,140):
                    if label=='SNaive7': p=vals[origin-7]
                    elif label.startswith('MA'):
                        k=int(label[2:]);p=sum(vals[origin-k:origin])/k
                    else:
                        a=F(label[3:]);q=1-a
                        p=q**(origin-1)*vals[0]+sum(a*q**(origin-1-i)*vals[i] for i in range(1,origin))
                    oracle.append(p)
                selected=[r for r in daily if r['method']==label]
                for r,p in zip(selected,oracle):
                    self.assertAlmostEqual(r['prediction'],float(p),places=10)
                for group,count in [('all',28),('weekday',20),('weekend',8)]:
                    idx=[i for i,r in enumerate(selected) if group=='all' or r['day_group']==group]
                    es=[vals[112+i]-oracle[i] for i in idx]
                    actual=sum(vals[112+i] for i in idx)
                    s=next(s for s in scores if s['method']==label and s['group']==group)
                    self.assertEqual(s['n'],count)
                    expected={'me':sum(es)/count,'mae':sum(map(abs,es))/count,
                              'rmse':math.sqrt(float(sum(e*e for e in es)/count)),
                              'wape':sum(map(abs,es))/actual}
                    for key,value in expected.items(): self.assertAlmostEqual(s[key],float(value),places=10)
                for r in [r for r in totals if r['method']==label]:
                    origin=r['origin_day']; base=oracle[origin-112]
                    expected=[vals[origin-7+h] for h in range(5)] if label=='SNaive7' else [base]*5
                    for h in range(5): self.assertAlmostEqual(r[f'prediction_h{h+1}'],float(expected[h]),places=10)


if __name__=='__main__': unittest.main()
