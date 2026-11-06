"""Independent expected values, input mutation and arithmetic invariants."""
import csv
import math
import random
from fractions import Fraction
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

import run


class PracticeTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.data = Path(self.temp.name) / 'data'
        shutil.copytree(Path(__file__).parent / 'data', self.data)

    def edit(self, name, change):
        path = self.data / name
        with path.open(newline='', encoding='utf-8') as stream:
            reader = csv.DictReader(stream)
            fields, rows = reader.fieldnames, list(reader)
        change(rows)
        with path.open('w', newline='', encoding='utf-8') as stream:
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader(); writer.writerows(rows)

    def test_exact_hand_answers(self):
        answer, checks = run.calculate(self.data)
        h, a, d = answer['hewei'], answer['apparel'], answer['definitions']
        self.assertEqual([r['error'] for r in checks], [-1, 1, 1])
        for key, expected in {'sum': 36, 'n': 3, 'mean': 12, 'weighted_mean': 12.6,
                              'population_variance': 8 / 3, 'population_sd': math.sqrt(8 / 3),
                              'sample_variance': 4, 'sample_sd': 2, 'mae': 1, 'rmse': 1}.items():
            self.assertAlmostEqual(h[key], expected, msg=key)
        self.assertEqual(a['remaining'], [90, 81])
        self.assertEqual(a['conditional_cancel_rate'], [.1, .1])
        self.assertAlmostEqual(a['day2_cancel_share_of_initial'], .09)
        self.assertAlmostEqual(a['expected_remaining_new_batch'], 24.3)
        self.assertEqual(d['error_demo']['error'], [-3, 1])
        self.assertAlmostEqual(d['error_demo']['mae'], 2)
        self.assertAlmostEqual(d['error_demo']['rmse'], math.sqrt(5))
        self.assertAlmostEqual(d['logit_0_8'], math.log(4))
        self.assertAlmostEqual(d['sigmoid_log4'], .8)

    def test_translation_reads_csv(self):
        self.edit('hewei.csv', lambda rows: [r.update(actual=str(float(r['actual']) + 5),
                                                     forecast=str(float(r['forecast']) + 5)) for r in rows])
        h = run.calculate(self.data)[0]['hewei']
        self.assertAlmostEqual(h['mean'], 17)
        self.assertAlmostEqual(h['weighted_mean'], 17.6)
        self.assertAlmostEqual(h['population_sd'], math.sqrt(8 / 3))
        self.assertEqual(h['mae'], 1)

    def test_scale_reads_csv(self):
        self.edit('hewei.csv', lambda rows: [r.update(actual=str(float(r['actual']) * 2),
                                                     forecast=str(float(r['forecast']) * 2)) for r in rows])
        h = run.calculate(self.data)[0]['hewei']
        self.assertAlmostEqual(h['mean'], 24)
        self.assertAlmostEqual(h['weighted_mean'], 25.2)
        self.assertAlmostEqual(h['population_sd'], 2 * math.sqrt(8 / 3))
        self.assertEqual(h['mae'], 2)

    def test_new_batch_reads_csv(self):
        self.edit('new_batch.csv', lambda rows: rows[0].update(orders='10'))
        self.assertAlmostEqual(run.calculate(self.data)[0]['apparel']['expected_remaining_new_batch'], 8.1)

    def test_zero_new_batch(self):
        self.edit('new_batch.csv', lambda rows: rows[0].update(orders='0'))
        self.assertEqual(run.calculate(self.data)[0]['apparel']['expected_remaining_new_batch'], 0)

    def test_missing_row(self):
        self.edit('hewei.csv', lambda rows: rows.pop())
        with self.assertRaises(ValueError): run.calculate(self.data)

    def test_duplicate_day(self):
        self.edit('hewei.csv', lambda rows: rows[1].update(day='1'))
        with self.assertRaises(ValueError): run.calculate(self.data)

    def test_extra_row(self):
        self.edit('apparel.csv', lambda rows: rows.append(dict(rows[0])))
        with self.assertRaises(ValueError): run.calculate(self.data)

    def test_empty_cell(self):
        self.edit('hewei.csv', lambda rows: rows[0].update(actual=''))
        with self.assertRaises(ValueError): run.calculate(self.data)

    def test_negative_demand(self):
        self.edit('hewei.csv', lambda rows: rows[0].update(actual='-1'))
        with self.assertRaises(ValueError): run.calculate(self.data)

    def test_negative_forecast(self):
        self.edit('hewei.csv', lambda rows: rows[0].update(forecast='-1'))
        with self.assertRaises(ValueError): run.calculate(self.data)

    def test_nonfinite(self):
        for invalid in ('nan', 'inf', '-inf'):
            with self.subTest(invalid=invalid):
                self.edit('hewei.csv', lambda rows: rows[0].update(actual=invalid))
                with self.assertRaises(ValueError): run.calculate(self.data)

    def test_negative_weight(self):
        self.edit('hewei.csv', lambda rows: rows[0].update(weight='-0.2'))
        with self.assertRaises(ValueError): run.calculate(self.data)

    def test_weights_do_not_sum_to_one(self):
        self.edit('hewei.csv', lambda rows: rows[0].update(weight='2'))
        with self.assertRaises(ValueError): run.calculate(self.data)

    def test_units_cannot_mix(self):
        self.edit('hewei.csv', lambda rows: rows[0].update(unit='box'))
        with self.assertRaises(ValueError): run.calculate(self.data)

    def test_series_cannot_mix(self):
        self.edit('hewei.csv', lambda rows: rows[0].update(series='hewei_B_chicken'))
        with self.assertRaises(ValueError): run.calculate(self.data)

    def test_fraction_hidden_by_float_rounding_rejected(self):
        self.edit('new_batch.csv', lambda rows: rows[0].update(orders='10.0000000000000001'))
        with self.assertRaises(ValueError):
            run.calculate(self.data)

    def test_count_beyond_exact_float_integer_range_rejected(self):
        self.edit('new_batch.csv', lambda rows: rows[0].update(orders='9007199254740993'))
        with self.assertRaises(ValueError):
            run.calculate(self.data)

    def test_cancel_exceeds_risk(self):
        self.edit('apparel.csv', lambda rows: rows[0].update(cancel='101'))
        with self.assertRaises(ValueError): run.calculate(self.data)

    def test_risk_continuity(self):
        self.edit('apparel.csv', lambda rows: rows[1].update(risk_start='100', remaining='91'))
        with self.assertRaises(ValueError): run.calculate(self.data)

    def test_remaining_identity(self):
        self.edit('apparel.csv', lambda rows: rows[1].update(remaining='80'))
        with self.assertRaises(ValueError): run.calculate(self.data)

    def test_fractional_order(self):
        self.edit('apparel.csv', lambda rows: rows[0].update(cancel='10.5'))
        with self.assertRaises(ValueError): run.calculate(self.data)

    def test_zero_risk(self):
        self.edit('apparel.csv', lambda rows: rows[0].update(risk_start='0', cancel='0', remaining='0'))
        with self.assertRaises(ValueError): run.calculate(self.data)

    def test_cancel_probability_one_at_last_day(self):
        self.edit('apparel.csv', lambda rows: rows[1].update(cancel='90', remaining='0'))
        a = run.calculate(self.data)[0]['apparel']
        self.assertEqual(a['conditional_cancel_rate'][1], 1)
        self.assertEqual(a['expected_remaining_new_batch'], 0)

    def test_probability_edges_and_logit_domain(self):
        for value in (0, 1):
            self.assertEqual(run.probability(value), value)
            with self.assertRaises(ValueError): run.logit(value)
        for value in (-.1, 1.1, math.nan, math.inf):
            with self.assertRaises(ValueError): run.probability(value)

    def test_sigmoid_stability_and_inverse(self):
        for z in (-1000, 1000):
            self.assertTrue(0 <= run.sigmoid(z) <= 1)
        for p in (.0001, .1, .5, .8, .9999):
            self.assertAlmostEqual(run.sigmoid(run.logit(p)), p)
        with self.assertRaises(ValueError): run.sigmoid(math.inf)

    def test_errors_require_pairs(self):
        for actual, forecast in (([], []), ([1], []), ([1, 2], [1])):
            with self.assertRaises(ValueError): run.errors(actual, forecast)

    def test_tiny_error_rejected_cli_without_success_output(self):
        self.edit('hewei.csv', lambda rows: [r.update(actual='1e-200', forecast='0') for r in rows])
        out = Path(self.temp.name) / 'out'
        process = subprocess.run([sys.executable, str(Path(run.__file__)), '--data-dir', str(self.data),
                                  '--out-dir', str(out)], capture_output=True, text=True)
        self.assertEqual(process.returncode, 2)
        self.assertIn('supported range', process.stderr)
        self.assertEqual(process.stdout, '')
        self.assertFalse(out.exists())

    def test_tiny_squared_error_in_mixed_scale_data_rejected(self):
        with self.assertRaisesRegex(ValueError, 'supported range'):
            run.errors([1, 1e-200], [0, 0])

    def test_mean_square_division_underflow_rejected(self):
        with self.assertRaisesRegex(ValueError, 'supported range'):
            run.errors([2e-162, 0, 0], [0, 0, 0])

    def test_small_float_representable_but_outside_exercise_range_rejected(self):
        self.edit('hewei.csv', lambda rows: [r.update(actual='3e-150', forecast='0') for r in rows])
        with self.assertRaisesRegex(ValueError, 'supported range'):
            run.calculate(self.data)

    def test_nonzero_variance_underflow_rejected(self):
        self.edit('hewei.csv', lambda rows: [r.update(actual=str((i + 1) * 1e-200),
                                                     forecast=str((i + 1) * 1e-200)) for i, r in enumerate(rows)])
        with self.assertRaisesRegex(ValueError, 'supported range'):
            run.calculate(self.data)

    def test_true_zero_square_allowed(self):
        for actual in ([0, 0, 0], [.001, .001, .001]):
            with self.subTest(actual=actual):
                result = run.errors(actual, actual)
                self.assertEqual(result['mae'], 0)
                self.assertEqual(result['rmse'], 0)

    def test_unterminated_quote_rejected_cli(self):
        out = Path(self.temp.name) / 'out'
        out.mkdir()
        sentinel = out / 'results.json'
        sentinel.write_text('previous successful result')
        for ending in ('"30', '"30\n', '"30"oops'):
            with self.subTest(ending=ending):
                (self.data / 'new_batch.csv').write_text('series,unit,orders\napparel_S01_M,order,' + ending)
                process = subprocess.run([sys.executable, str(Path(run.__file__)), '--data-dir', str(self.data),
                                          '--out-dir', str(out)], capture_output=True, text=True)
                self.assertEqual(process.returncode, 2)
                self.assertIn('malformed CSV', process.stderr)
                self.assertEqual(process.stdout, '')
                self.assertEqual(sentinel.read_text(), 'previous successful result')
                self.assertFalse((out / 'math_checks.csv').exists())

    def test_correctly_quoted_last_cell_allowed(self):
        (self.data / 'new_batch.csv').write_text('series,unit,orders\napparel_S01_M,order,"30"')
        self.assertEqual(run.calculate(self.data)[0]['apparel']['new_batch_size'], 30)

    def test_nonzero_input_literal_underflow_rejected_cli(self):
        for value in ('1e-400', '-1e-400'):
            with self.subTest(value=value):
                self.edit('hewei.csv', lambda rows: [r.update(actual=value, forecast='0') for r in rows])
                out = Path(self.temp.name) / 'underflow-out'
                process = subprocess.run([sys.executable, str(Path(run.__file__)), '--data-dir', str(self.data),
                                          '--out-dir', str(out)], capture_output=True, text=True)
                self.assertEqual(process.returncode, 2)
                self.assertIn('supported range', process.stderr)
                self.assertEqual(process.stdout, '')
                self.assertFalse(out.exists())

    def test_actual_zero_literals_still_allowed(self):
        for value in ('0', '-0.0', '0e-400', '-0e-400'):
            with self.subTest(value=value):
                self.assertEqual(run.nonnegative(value, 'actual'), 0)

    def test_parent_v4_three_cli_attacks_rejected(self):
        cases = [(['2.5e-162'] * 3, ['0'] * 3),
                 (['0', '2.5e-162', '5e-162'], ['0'] * 3),
                 (['5e-324'] * 3, ['5e-324'] * 3)]
        for actual, forecast in cases:
            with self.subTest(actual=actual):
                self.edit('hewei.csv', lambda rows: [r.update(actual=a, forecast=f)
                          for r, a, f in zip(rows, actual, forecast)])
                out = Path(self.temp.name) / 'rejected'
                process = subprocess.run([sys.executable, str(Path(run.__file__)), '--data-dir', str(self.data),
                                          '--out-dir', str(out)], capture_output=True, text=True)
                self.assertEqual(process.returncode, 2)
                self.assertIn('supported range', process.stderr)
                self.assertEqual(process.stdout, '')
                self.assertFalse(out.exists())

    def test_subnormal_halfway_and_large_mutations_rejected(self):
        invalid = ['5e-324', '2.4703282292062327e-324', '2.5e-162', '1e-400', '-1e-400',
                   str(math.nextafter(0.0, 1.0)), str(math.nextafter(sys.float_info.min, 0.0)),
                   str(sys.float_info.min), '1e308', '1e1000000',
                   '0.0005', '0.0009999999999999999999999', str(2 ** -14), str(2 ** -24),
                   '1.00000000000000011102230246251565404236316680908203125',
                   str(math.nextafter(.001, 0)), str(math.nextafter(.001, 1)),
                   '1000000.00000000000000001', '1000000.001', str(math.nextafter(1e6, math.inf))]
        for value in invalid:
            with self.subTest(value=value):
                self.edit('hewei.csv', lambda rows: rows[0].update(actual=value))
                with self.assertRaises(ValueError): run.calculate(self.data)

    def test_decimal_grid_inclusive_boundaries(self):
        for value, grams in [('0', 0), ('-0.000', 0), ('0.001', 1), ('1.0000', 1000),
                             ('65503.999', 65503999), ('65504', 65504000), ('65504.001', 65504001),
                             ('65520', 65520000), ('999999.999', 999999999), ('1e6', 1000000000)]:
            self.assertEqual(run.quantity(value, 'quantity'), grams)
        for value, ppm in [('0', 0), ('0.000001', 1), ('0.999999', 999999), ('1', 1000000)]:
            self.assertEqual(run.scaled_input(value, 'weight', 1000000, 1), ppm)
        for value in ['5e-324', '0.0000005', '0.000000999999999999', '0.10000000000000001', '1.00000000000000001']:
            with self.assertRaises(ValueError): run.scaled_input(value, 'weight', 1000000, 1)

    def test_smallest_supported_weighted_mean_and_variances(self):
        self.edit('hewei.csv', lambda rows: [r.update(actual='0.001', forecast='0') for r in rows])
        h, rows = run.calculate(self.data)
        self.assertEqual(h['hewei']['weighted_mean'], .001)
        self.assertEqual(h['hewei']['mae'], .001)
        self.assertEqual(h['hewei']['rmse'], .001)
        self.assertTrue(all(r['squared_error'] == .000001 for r in rows))
        self.edit('hewei.csv', lambda rows: [r.update(actual=str(i / 1000)) for i, r in enumerate(rows)])
        h = run.calculate(self.data)[0]['hewei']
        self.assertTrue(math.isclose(h['population_sd'], math.sqrt(Fraction(2, 3000000)), rel_tol=1e-14))
        self.assertEqual(h['sample_sd'], .001)
        self.assertLess(h['population_sd'], h['sample_sd'])

    def test_large_close_quantities_keep_gram_differences(self):
        actual = ['999999.998', '999999.999', '1000000']
        forecast = ['999999.997', '999999.998', '999999.999']
        self.edit('hewei.csv', lambda rows: [r.update(actual=a, forecast=f) for r, a, f in zip(rows, actual, forecast)])
        result, checks = run.calculate(self.data)
        self.assertEqual(result['hewei']['mae'], .001)
        self.assertEqual(result['hewei']['rmse'], .001)
        self.assertEqual(result['hewei']['sample_sd'], .001)
        self.assertTrue(all(r['error'] == .001 for r in checks))

    def test_small_weight_product_preserved_and_exact_weight_sum(self):
        self.edit('hewei.csv', lambda rows: [r.update(actual=a, forecast='0', weight=w)
                  for r, a, w in zip(rows, ['0.001', '0', '0'], ['0.000001', '0.999999', '0'])])
        self.assertEqual(run.calculate(self.data)[0]['hewei']['weighted_mean'], 1e-9)
        self.edit('hewei.csv', lambda rows: rows[1].update(weight='0.999998'))
        with self.assertRaises(ValueError): run.calculate(self.data)

    def test_supported_random_grid_against_fraction_oracle(self):
        rng = random.Random(4096)
        for _ in range(200):
            grams = [rng.randrange(0, 1000000001) for _ in range(3)]
            forecasts = [rng.randrange(0, 1000000001) for _ in range(3)]
            def kg(v): return f'{v // 1000}.{v % 1000:03d}'
            self.edit('hewei.csv', lambda rows: [r.update(actual=kg(a), forecast=kg(f))
                      for r, a, f in zip(rows, grams, forecasts)])
            h = run.calculate(self.data)[0]['hewei']
            ys = [Fraction(g, 1000) for g in grams]
            mean = sum(ys) / 3
            pop = sum((y - mean) ** 2 for y in ys) / 3
            sample = sum((y - mean) ** 2 for y in ys) / 2
            es = [Fraction(a - f, 1000) for a, f in zip(grams, forecasts)]
            expected = {'mean': float(mean), 'population_variance': float(pop), 'sample_variance': float(sample),
                        'mae': float(sum(abs(e) for e in es) / 3), 'rmse': math.sqrt(float(sum(e * e for e in es) / 3)),
                        'weighted_mean': float(sum(y * w for y, w in zip(ys, [Fraction(1, 5), Fraction(3, 10), Fraction(1, 2)])))}
            for key, value in expected.items():
                self.assertTrue(math.isclose(h[key], value, rel_tol=1e-14, abs_tol=0), (key, h[key], value))
            self.assertGreaterEqual(h['rmse'] * (1 + 1e-14), h['mae'])

    def test_large_order_ratio_avoids_one_minus_cancellation(self):
        maximum = 2 ** 53 - 1
        self.edit('apparel.csv', lambda rows: [rows[0].update(risk_start=str(maximum), cancel=str(maximum - 1), remaining='1'),
                                               rows[1].update(risk_start='1', cancel='0', remaining='1')])
        self.edit('new_batch.csv', lambda rows: rows[0].update(orders=str(maximum)))
        a = run.calculate(self.data)[0]['apparel']
        self.assertEqual(a['survival_probability_assumed_for_new_batch'], 1 / maximum)
        self.assertEqual(a['expected_remaining_new_batch'], 1)


if __name__ == '__main__':
    unittest.main()
