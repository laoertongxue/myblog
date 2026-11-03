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

from baseline import (forecast_at, load_csv, moving_average, seasonal_naive,
                      validate, validate_development, windows)
from run import compare, verify_source

ROOT = Path(__file__).resolve().parent


def fixture(values, series='hand/example'):
    return [{'day': i + 1, 'date': (date(2026, 1, 1) + timedelta(days=i)).isoformat(),
             'demand': value, 'series': series} for i, value in enumerate(values)]


class HandOracleTests(unittest.TestCase):
    def test_exact_10_20_30(self):
        rows = fixture([10, 20, 30])
        self.assertEqual(moving_average(rows, 1, 3), [20])
        self.assertEqual(moving_average(rows, 5, 3), [20, 20, 20, 20, 20])
        self.assertEqual(sum(moving_average(rows, 5, 3)), 100)

    def test_exact_all_candidates(self):
        rows = fixture(list(range(1, 15)))
        # Independently hand-calculated literal expectations, not library helpers.
        for k, expected in [(3, 13), (7, 11), (14, 7.5)]:
            with self.subTest(k=k):
                self.assertEqual(moving_average(rows, 5, k), [expected] * 5)

    def test_fixed_origin_not_recursive_or_future_actual_update(self):
        rows = fixture([2, 4, 6, 8, 10, 0, 999, 999, 999, 999])
        self.assertEqual(forecast_at(rows, 5, 5, k=3), [8, 8, 8, 8, 8])
        # Wrong recursive forecast gives 26/3 next; using future actual 0 gives 6.
        self.assertNotEqual(forecast_at(rows, 5, 5, k=3)[1], 26 / 3)
        self.assertNotEqual(forecast_at(rows, 5, 5, k=3)[1], 6)

    def test_origin_is_last_known_not_first_target(self):
        rows = fixture([10, 20, 30, 999])
        self.assertEqual(forecast_at(rows, 3, 1, k=3), [20])
        self.assertEqual(forecast_at(rows, 4, 1, k=3), [1049 / 3])

    def test_future_perturbation_independent_literal_oracle(self):
        rows = fixture(list(range(1, 21)))
        changed = deepcopy(rows)
        for row in changed[14:]:
            row['demand'] = 99999
        for k, expected in [(3, 13), (7, 11), (14, 7.5)]:
            self.assertEqual(forecast_at(rows, 14, 5, k=k), [expected] * 5)
            self.assertEqual(forecast_at(changed, 14, 5, k=k), [expected] * 5)

    def test_future_negative_object_and_bad_date_do_not_leak(self):
        for mutation in ['negative', 'object', 'date']:
            changed = fixture(list(range(1, 21)))
            for row in changed[14:]:
                if mutation == 'negative':
                    row['demand'] = -999
                elif mutation == 'object':
                    row['demand'] = {'invalid': 'numeric object'}
                else:
                    row['date'] = 'broken-future-date'
            for k, expected in [(3, 13), (7, 11), (14, 7.5)]:
                with self.subTest(mutation=mutation, k=k):
                    self.assertEqual(forecast_at(changed, 14, 5, k=k), [expected] * 5)
            self.assertEqual(forecast_at(changed, 14, 5, method='seasonal_naive_7'), [8, 9, 10, 11, 12])
            with self.assertRaises(ValueError):
                validate(changed)

    def test_even_invalid_future_rows_are_not_inspected(self):
        rows = fixture([10, 20, 30]) + [{'not': 'an observed row'}]
        self.assertEqual(forecast_at(rows, 3, 5, k=3), [20] * 5)
        with self.assertRaises(ValueError):
            forecast_at(rows, 4, 1, k=3)

    def test_observed_origin_changes_prediction(self):
        rows = fixture([10, 20, 30])
        rows[2]['demand'] = 60
        self.assertEqual(forecast_at(rows, 3, 1, k=3), [30])

    def test_seasonal_profile_is_not_seven_day_average(self):
        rows = fixture([1, 2, 3, 4, 5, 6, 7])
        self.assertEqual(seasonal_naive(rows, 15), [1, 2, 3, 4, 5, 6, 7, 1, 2, 3, 4, 5, 6, 7, 1])
        self.assertEqual(moving_average(rows, 5, 7), [4] * 5)

    def test_zero_valid(self):
        self.assertEqual(moving_average(fixture([0, 0, 0]), 5, 3), [0] * 5)
        self.assertEqual(seasonal_naive(fixture([0] * 7), 1), [0])

    def test_trailing_window_drops_oldest(self):
        self.assertEqual(moving_average(fixture([999, 10, 20, 30]), 1, 3), [20])


class BoundaryTests(unittest.TestCase):
    def test_short_history_rejected_not_shortened(self):
        with self.assertRaises(ValueError):
            moving_average(fixture([1, 2]), 1, 3)
        with self.assertRaises(ValueError):
            seasonal_naive(fixture([1] * 6), 1)
        with self.assertRaises(ValueError):
            moving_average([], 1, 1)

    def test_bad_window_horizon_origin(self):
        rows = fixture(list(range(1, 15)))
        for bad in [0, -1, 1.5, True, False, '3', None]:
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    moving_average(rows, 1, bad)
                with self.assertRaises(ValueError):
                    moving_average(rows, bad, 3)
                with self.assertRaises(ValueError):
                    forecast_at(rows, bad, 1, k=3)
                with self.assertRaises(ValueError):
                    seasonal_naive(rows, 1, bad)
        with self.assertRaises(ValueError):
            forecast_at(rows, 15, 1, k=3)
        with self.assertRaises(ValueError):
            forecast_at(rows, 14, 1, method='unknown')

    def test_bad_demand_rejected(self):
        for bad in [-1, float('nan'), float('inf'), float('-inf'), True, False, None, '10', 10 ** 500]:
            with self.subTest(bad=str(bad)[:20]):
                with self.assertRaises(ValueError):
                    moving_average(fixture([1, 2, bad]), 1, 3)

    def test_finite_large_demand_does_not_overflow_intermediate_sum(self):
        result = moving_average(fixture([1e308, 1e308, 1e308]), 1, 3)[0]
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

    def test_all_validation_metrics_independent_fraction_oracle(self):
        # Separate CSV reader and Fraction arithmetic, no model/window helpers.
        # Inclusive source row index is j-1 for target day j. Every five-step
        # prediction is computed once from the pre-window origin history.
        for case in ['hewei', 'apparel']:
            path = ROOT / 'data' / f'{case}-development.csv'
            with path.open(encoding='utf-8', newline='') as handle:
                values = [Fraction(row['demand']) for row in csv.DictReader(handle)]
            rows = load_csv(path, case)
            daily, cumulative, summary = compare(rows, case, 'daily-unit', 'total-unit')
            self.assertEqual(len(daily), 112)
            self.assertEqual(len(cumulative), 96)
            for stats in summary:
                k = stats['k_or_period']
                mae1 = Fraction(0)
                mae5 = Fraction(0)
                for target_index in range(112, 140):
                    pred = values[target_index - 7] if stats['method'] == 'SNaive7' else sum(values[target_index-k:target_index], Fraction(0)) / k
                    mae1 += abs(values[target_index] - pred)
                for target_index in range(112, 136):
                    if stats['method'] == 'SNaive7':
                        pred_total = sum(values[target_index-7:target_index-2], Fraction(0))
                    else:
                        pred_total = 5 * sum(values[target_index-k:target_index], Fraction(0)) / k
                    mae5 += abs(sum(values[target_index:target_index+5], Fraction(0)) - pred_total)
                with self.subTest(case=case, method=stats['method']):
                    self.assertAlmostEqual(stats['daily_mae'], float(mae1 / 28), places=11)
                    self.assertAlmostEqual(stats['five_day_total_mae'], float(mae5 / 24), places=11)
            for row in cumulative:
                if row['method'] != 'SNaive7':
                    self.assertTrue(all(row[f'prediction_h{h}'] == row['prediction_h1'] for h in range(1, 6)))


if __name__ == '__main__':
    unittest.main()
