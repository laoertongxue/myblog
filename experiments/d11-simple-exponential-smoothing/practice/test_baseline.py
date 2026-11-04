"""Regression tests and independent hand/Fraction oracles. No test-set access."""
from copy import deepcopy
from datetime import date, timedelta
from fractions import Fraction
from pathlib import Path
from tempfile import TemporaryDirectory
import csv
import hashlib
import math
import unittest

from baseline import (forecast_at, load_csv, ses, levels, seasonal_naive,
                      validate, validate_development, windows)
from run import compare, verify_source

ROOT = Path(__file__).resolve().parent


def fixture(values, series='hand/example'):
    return [{'day': i + 1, 'date': (date(2026, 1, 1) + timedelta(days=i)).isoformat(),
             'demand': value, 'series': series} for i, value in enumerate(values)]


class HandOracleTests(unittest.TestCase):
    def test_two_observations(self):
        self.assertEqual(levels(fixture([10, 20]), .5), [10, 15])
        self.assertEqual(ses(fixture([10, 20]), 5, .5), [15] * 5)
        self.assertEqual(sum(ses(fixture([10, 20]), 5, .5)), 75)

    def test_three_observations_all_candidates(self):
        for alpha, expected in [(.2, 11.6), (.5, 12.5), (.8, 11.6)]:
            self.assertAlmostEqual(ses(fixture([10, 20, 10]), 1, alpha)[0], expected)

    def test_post_level_is_not_same_day_forecast(self):
        rows = fixture([10, 20, 10])
        self.assertEqual(forecast_at(rows, 1, 1, alpha=.5), [10])
        self.assertEqual(forecast_at(rows, 2, 1, alpha=.5), [15])
        self.assertEqual(levels(rows, .5), [10, 15, 12.5])

    def test_future_values_dates_and_objects_do_not_leak(self):
        for future in [[-999], [float('nan')], [None], [999999]]:
            rows = fixture([10, 20] + future)
            rows[2]['date'] = 'broken-future-date'
            self.assertEqual(forecast_at(rows, 2, 5, alpha=.5), [15] * 5)
            with self.assertRaises(ValueError):
                validate(rows)
        self.assertEqual(forecast_at(fixture([10, 20]) + [object()], 2, 5), [15] * 5)

    def test_fixed_origin_never_updates_with_future_actuals(self):
        rows = fixture([10, 20, 100, 0, 999, 4, 6])
        self.assertEqual(forecast_at(rows, 2, 5), [15] * 5)
        self.assertEqual(forecast_at(rows, 3, 1), [57.5])

    def test_alpha_endpoints(self):
        self.assertEqual(ses(fixture([10, 20, 30]), 5, 0), [10] * 5)
        self.assertEqual(ses(fixture([10, 20, 30]), 5, 1), [30] * 5)

    def test_first_observation_initializes(self):
        for alpha in [0, .2, .5, .8, 1]:
            self.assertEqual(ses(fixture([7]), 3, alpha), [7] * 3)

    def test_constant_and_zero(self):
        for v in [0, 9]:
            for alpha in [.2, .5, .8]:
                self.assertEqual(ses(fixture([v] * 12), 5, alpha), [v] * 5)

    def test_geometric_weight_oracle(self):
        values = [2, 9, 0, 8, 1]
        for a in [Fraction(1, 5), Fraction(1, 2), Fraction(4, 5)]:
            expected = (1-a)**4 * values[0] + sum(a * (1-a)**(4-j) * values[j] for j in range(1, 5))
            self.assertAlmostEqual(ses(fixture(values), 1, float(a))[0], float(expected))

    def test_seasonal_baseline_keeps_profile(self):
        self.assertEqual(seasonal_naive(fixture([1, 2, 3, 4, 5, 6, 7]), 8), [1, 2, 3, 4, 5, 6, 7, 1])


class BoundaryTests(unittest.TestCase):
    def test_empty_history_rejected(self):
        with self.assertRaises(ValueError):
            ses([], 1, .5)
        with self.assertRaises(ValueError):
            seasonal_naive(fixture([1] * 6), 1)

    def test_alpha_invalid(self):
        for bad in [-.1, 1.1, float('nan'), float('inf'), None, True, False, '0.5', 10**500]:
            with self.subTest(bad=str(bad)[:20]), self.assertRaises(ValueError):
                ses(fixture([10, 20]), 1, bad)

    def test_invalid_horizon_origin_period(self):
        rows = fixture([10] * 7)
        for bad in [0, -1, True, False, 1.5, '3', None]:
            for call in [lambda: ses(rows, bad, .5), lambda: forecast_at(rows, bad, 1), lambda: seasonal_naive(rows, 1, bad)]:
                with self.assertRaises(ValueError):
                    call()
        with self.assertRaises(ValueError):
            forecast_at(rows, 8, 1)
        with self.assertRaises(ValueError):
            forecast_at(rows, 7, 1, method='unknown')

    def test_bad_demand_rejected(self):
        for bad in [-1, float('nan'), float('inf'), float('-inf'), True, False, None, '10', 10 ** 500]:
            with self.subTest(bad=str(bad)[:20]):
                with self.assertRaises(ValueError):
                    ses(fixture([1, 2, bad]), 1, 0.5)

    def test_finite_large_demand_does_not_overflow_intermediate_sum(self):
        result = ses(fixture([1e308, 1e308, 1e308]), 1, 0.5)[0]
        self.assertTrue(math.isfinite(result))
        self.assertAlmostEqual(result / 1e308, 1.0)

    def test_missing_field_rejected(self):
        for key in ['day', 'date', 'demand', 'series']:
            rows = fixture([1, 2, 3])
            del rows[1][key]
            with self.assertRaises(ValueError):
                validate(rows)

    def test_dates_and_day_keys_rejected(self):
        for bad_date in ['2026-01-01', '2026-01-04', 'not-a-date', '20260102', None]:
            rows = fixture([1, 2, 3])
            rows[1]['date'] = bad_date
            with self.assertRaises(ValueError):
                validate(rows)
        for bad_day in [1, 4, True, '2', 2.0]:
            rows = fixture([1, 2, 3])
            rows[1]['day'] = bad_day
            with self.assertRaises(ValueError):
                validate(rows)
        with self.assertRaises(ValueError):
            validate(list(reversed(fixture([1, 2, 3]))))

    def test_entities_cannot_mix(self):
        rows = fixture([1, 2, 3])
        rows[1]['series'] = 'different/entity'
        with self.assertRaises(ValueError):
            validate(rows)

    def test_csv_missing_bad_and_nonfinite(self):
        for value in ['', 'NULL', 'True', '-1', 'NaN', 'inf', 'abc']:
            with self.subTest(value=value), TemporaryDirectory() as tmp:
                path = Path(tmp) / 'case.csv'
                path.write_text(f'day,date,demand,split\n1,2026-01-01,{value},train\n', encoding='utf-8')
                with self.assertRaises(ValueError):
                    load_csv(path, 'case')

    def test_empty_physical_lines_allowed_without_missing_dates(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / 'case.csv'
            path.write_text('day,date,demand,split\n1,2026-01-01,10,train\n\n2,2026-01-02,20,train\n\n', encoding='utf-8')
            self.assertEqual([r['demand'] for r in load_csv(path, 'case')], [10, 20])
            path.write_text('day,date,demand,split\n1,2026-01-01,10,train\n\n3,2026-01-03,20,train\n', encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'continuous'):
                load_csv(path, 'case')

    def test_whitespace_only_physical_line_is_invalid_record(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / 'case.csv'
            path.write_text('day,date,demand,split\n1,2026-01-01,10,train\n   \n2,2026-01-02,20,train\n', encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'missing or surplus CSV field'):
                load_csv(path, 'case')

    def test_csv_unclosed_or_malformed_quote_rejected(self):
        malformed = [
            'day,date,demand,split\n1,2026-01-01,3,"train',
            'day,date,demand,split\n1,2026-01-01,3,"train"oops\n',
            '"day,date,demand,split\n1,2026-01-01,3,train\n',
        ]
        for data in malformed:
            with self.subTest(data=data), TemporaryDirectory() as tmp:
                path = Path(tmp) / 'case.csv'
                path.write_text(data, encoding='utf-8')
                with self.assertRaisesRegex(ValueError, 'malformed CSV syntax'):
                    load_csv(path, 'case')

    def test_csv_bad_header_and_extra_field(self):
        bad_inputs = ['date,demand\n2026-01-01,3\n',
                      'day,date,demand,split\n1,2026-01-01,3,train,extra\n',
                      'day,date,demand,split\n1,2026-01-01,3,test\n',
                      'day,date,demand,split\n1,2026-01-01,3\n']
        for data in bad_inputs:
            with TemporaryDirectory() as tmp:
                path = Path(tmp) / 'case.csv'
                path.write_text(data, encoding='utf-8')
                with self.assertRaises(ValueError):
                    load_csv(path, 'case')

    def test_windows_never_cross_evaluation_split(self):
        daily = windows(113, 140, 1)
        five = windows(113, 140, 5)
        self.assertEqual(len(daily), 28)
        self.assertEqual(daily[0], (112, 113, 113))
        self.assertEqual(daily[-1], (139, 140, 140))
        self.assertEqual(len(five), 24)
        self.assertEqual(five[0], (112, 113, 117))
        self.assertEqual(five[-1], (135, 136, 140))
        self.assertTrue(all(first >= 113 and last <= 140 for _, first, last in five))
        self.assertEqual(windows(113, 116, 5), [])
        for args in [(0, 140, 5), (113, 112, 5), (113, 140, 0), (113, 140, True)]:
            with self.assertRaises(ValueError):
                windows(*args)



class SourceAndEvaluationTests(unittest.TestCase):
    def test_source_hashes_unchanged(self):
        manifest = verify_source()
        self.assertEqual(set(manifest['files']), {'data/hewei-development.csv', 'data/apparel-development.csv'})
        self.assertFalse((ROOT / 'sealed').exists())

    def test_exact_development_contract(self):
        rows = load_csv(ROOT / 'data/hewei-development.csv', 'hewei/A/SKU01')
        validate_development(rows)
        self.assertEqual(len(rows), 140)
        self.assertEqual(rows[111]['split'], 'train')
        self.assertEqual(rows[112]['split'], 'validation')
        self.assertEqual(rows[-1]['day'], 140)
        with self.assertRaises(ValueError):
            validate_development(rows[:-1])
        bad = deepcopy(rows)
        bad[112]['split'] = 'train'
        with self.assertRaises(ValueError):
            validate_development(bad)

    def test_all_metrics_independent_fraction_oracle(self):
        # Expanded geometric weights, independent of the recursive implementation.
        for case in ['hewei', 'apparel']:
            path = ROOT / 'data' / f'{case}-development.csv'
            with path.open(newline='') as f:
                values = [Fraction(r['demand']) for r in csv.DictReader(f)]
            daily, cumulative, summary = compare(load_csv(path, case), case, 'daily', 'total')
            self.assertEqual(len(daily), 112)
            self.assertEqual(len(cumulative), 96)
            for stats in summary:
                def expected(origin, horizon):
                    if stats['method'] == 'SNaive7':
                        return values[origin-7:origin-7+horizon]
                    a = Fraction(str(stats['alpha']))
                    level = (1-a)**(origin-1) * values[0]
                    level += sum(a * (1-a)**(origin-1-j) * values[j] for j in range(1, origin))
                    return [level] * horizon
                err1 = sum(abs(values[o]-expected(o, 1)[0]) for o in range(112, 140)) / 28
                err5 = sum(abs(sum(values[o:o+5])-sum(expected(o, 5))) for o in range(112, 136)) / 24
                self.assertAlmostEqual(stats['daily_mae'], float(err1), places=10)
                self.assertAlmostEqual(stats['five_day_total_mae'], float(err5), places=10)
                for record in [r for r in daily if r['method'] == stats['method']]:
                    self.assertAlmostEqual(record['prediction'], float(expected(record['origin_day'], 1)[0]), places=10)
                for record in [r for r in cumulative if r['method'] == stats['method']]:
                    for h, value in enumerate(expected(record['origin_day'], 5), 1):
                        self.assertAlmostEqual(record[f'prediction_h{h}'], float(value), places=10)


if __name__ == '__main__':
    unittest.main()
