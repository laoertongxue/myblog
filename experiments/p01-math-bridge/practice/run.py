#!/usr/bin/env python3
"""Read small simulated CSVs; reproduce arithmetic, not a fitted model."""
import argparse
import csv
import json
import math
from decimal import Decimal, InvalidOperation
from pathlib import Path


def number(value, label):
    try:
        result = float(value)
    except (ValueError, TypeError) as exc:
        raise ValueError(f'{label}: numeric value required') from exc
    if not math.isfinite(result):
        raise ValueError(f'{label}: finite value required')
    if result == 0:
        try:
            if Decimal(str(value)) != 0:
                raise ValueError(f'{label}: nonzero input underflows numeric range')
        except InvalidOperation as exc:
            raise ValueError(f'{label}: numeric value required') from exc
    return result


def nonnegative(value, label):
    result = number(value, label)
    if result < 0:
        raise ValueError(f'{label}: must be nonnegative')
    return result


def count(value, label):
    text = str(value).strip()
    if not text.isascii() or not text.isdecimal():
        raise ValueError(f'{label}: nonnegative integer digits required')
    result = int(text)
    # Downstream probabilities use binary64; reject unsupported integer ranges.
    if result > 2 ** 53 - 1:
        raise ValueError(f'{label}: count exceeds supported exact-integer range')
    return result


def probability(value):
    p = number(value, 'probability')
    if not 0 <= p <= 1:
        raise ValueError('probability: must be in [0, 1]')
    return p


def logit(value):
    p = probability(value)
    if not 0 < p < 1:
        raise ValueError('logit requires 0 < p < 1')
    return math.log(p) - math.log1p(-p)


def sigmoid(value):
    z = number(value, 'score')
    # This branch avoids exp(1000) overflow; floating point may round to 0/1.
    if z >= 0:
        return 1 / (1 + math.exp(-z))
    exp_z = math.exp(z)
    return exp_z / (1 + exp_z)


def read_csv(path, fields, rows):
    with path.open(newline='', encoding='utf-8-sig') as stream:
        reader = csv.DictReader(stream, strict=True)
        try:
            if reader.fieldnames != fields:
                raise ValueError(f'{path.name}: columns must be {fields}')
            values = list(reader)
        except csv.Error as exc:
            raise ValueError(f'{path.name}: malformed CSV: {exc}') from exc
    if len(values) != rows:
        raise ValueError(f'{path.name}: exercise requires exactly {rows} rows')
    if any(None in row or any(v is None or not v.strip() for v in row.values()) for row in values):
        raise ValueError(f'{path.name}: missing or extra cells')
    return values


def scaled_input(value, label, scale, maximum):
    """Validate the decimal grid before converting to exact integer units."""
    try:
        exact = Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError(f'{label}: decimal number required') from exc
    rule = f'{label}: supported range 0..{maximum}, step 1/{scale}'
    if not exact.is_finite() or exact < 0 or exact > maximum:
        raise ValueError(rule)
    if exact and exact < Decimal(1) / scale:
        raise ValueError(rule)
    numerator, denominator = exact.as_integer_ratio()
    scaled = numerator * scale
    if scaled % denominator:
        raise ValueError(rule)
    return scaled // denominator


def quantity(value, label):
    return scaled_input(value, label, 1000, 1000000)


def errors(actual, forecast):
    if not actual or len(actual) != len(forecast):
        raise ValueError('actual and forecast must have equal nonzero length')
    actual = [quantity(v, 'actual') for v in actual]
    forecast = [quantity(v, 'forecast') for v in forecast]
    es = [a - f for a, f in zip(actual, forecast)]
    # Integer grams preserve small differences between large supported values.
    mse = sum(e * e for e in es) / (len(es) * 1000000)
    return {'error': [e / 1000 for e in es],
            'mae': sum(abs(e) for e in es) / (len(es) * 1000), 'rmse': math.sqrt(mse)}


def calculate(data_dir):
    daily = read_csv(data_dir / 'hewei.csv', ['day', 'series', 'unit', 'actual', 'forecast', 'weight'], 3)
    if [count(r['day'], 'day') for r in daily] != [1, 2, 3]:
        raise ValueError('hewei: days must be unique and ordered 1, 2, 3')
    if any(r['series'] != 'hewei_A_chicken' or r['unit'] != 'kg' for r in daily):
        raise ValueError('hewei: expected one series hewei_A_chicken, measured in kg')
    grams = [quantity(r['actual'], 'actual') for r in daily]
    forecast_grams = [quantity(r['forecast'], 'forecast') for r in daily]
    weights = [scaled_input(r['weight'], 'weight', 1000000, 1) for r in daily]
    if sum(weights) != 1000000:
        raise ValueError('weights must sum to exactly 1')
    n = len(grams)
    total = sum(grams)
    # n*sum(x²)-sum(x)² is exact here because every operand is a Python integer.
    variance_numerator = n * sum(y * y for y in grams) - total * total
    population_variance = variance_numerator / (n * n * 1000000)
    sample_variance = variance_numerator / (n * (n - 1) * 1000000)
    error = errors([r['actual'] for r in daily], [r['forecast'] for r in daily])
    checks = [dict(day=i + 1, actual=y / 1000, forecast=f / 1000,
                   error=(y - f) / 1000, abs_error=abs(y - f) / 1000,
                   squared_error=(y - f) ** 2 / 1000000)
              for i, (y, f) in enumerate(zip(grams, forecast_grams))]
    hewei = {'series': 'hewei_A_chicken', 'unit': 'kg', 'sum': total / 1000, 'n': n,
             'mean': total / (n * 1000),
             'weighted_mean': sum(y * w for y, w in zip(grams, weights)) / 1000000000,
             'population_variance': population_variance, 'population_sd': math.sqrt(population_variance),
             'sample_variance': sample_variance, 'sample_sd': math.sqrt(sample_variance),
             'mae': error['mae'], 'rmse': error['rmse']}
    cancellations = read_csv(data_dir / 'apparel.csv', ['day', 'series', 'unit', 'risk_start', 'cancel', 'remaining'], 2)
    if [count(r['day'], 'day') for r in cancellations] != [1, 2]:
        raise ValueError('apparel: days must be unique and ordered 1, 2')
    risks, cancelled, remaining, hazards = [], [], [], []
    for row in cancellations:
        if row['series'] != 'apparel_S01_M' or row['unit'] != 'order':
            raise ValueError('apparel: expected one series apparel_S01_M, measured in orders')
        risk = count(row['risk_start'], 'risk_start')
        cancel = count(row['cancel'], 'cancel')
        left = count(row['remaining'], 'remaining')
        if risk == 0:
            raise ValueError('conditional cancellation rate undefined for an empty risk set')
        if cancel > risk or left != risk - cancel:
            raise ValueError('apparel: cancel <= risk_start and remaining = risk_start - cancel required')
        if remaining and risk != remaining[-1]:
            raise ValueError('apparel: next risk set must equal previous remaining count')
        risks.append(risk); cancelled.append(cancel); remaining.append(left)
        hazards.append(probability(cancel / risk))
    batch = read_csv(data_dir / 'new_batch.csv', ['series', 'unit', 'orders'], 1)[0]
    if batch['series'] != 'apparel_S01_M' or batch['unit'] != 'order':
        raise ValueError('new batch must use the same apparel series and unit')
    size = count(batch['orders'], 'orders')
    # With no entries or other exits, the conditional product telescopes to this ratio.
    survival = remaining[-1] / risks[0]
    apparel = {'series': 'apparel_S01_M', 'unit': 'order', 'risk_start': risks, 'cancel': cancelled,
               'remaining': remaining, 'conditional_cancel_rate': hazards,
               'day2_cancel_share_of_initial': cancelled[1] / risks[0],
               'survival_probability_assumed_for_new_batch': survival,
               'new_batch_size': size, 'expected_remaining_new_batch': (size * remaining[-1]) / risks[0]}
    # Separate fixed examples explain operations; they are not model estimates.
    demo = errors([10, 12], [13, 11])
    definitions = {'error_demo_unit': 'kg', 'error_demo': demo, 'f_of_4_for_f_2x_plus_3': 11,
                   'two_cubed': 2 ** 3, 'log2_8': math.log2(8), 'ln1': math.log(1),
                   'logit_0_5': logit(.5), 'logit_0_8': logit(.8),
                   'sigmoid_0': sigmoid(0), 'sigmoid_log4': sigmoid(math.log(4))}
    return {'simulation_only': True, 'hewei': hewei, 'apparel': apparel, 'definitions': definitions}, checks


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    base = Path(__file__).resolve().parent
    parser.add_argument('--data-dir', type=Path, default=base / 'data')
    parser.add_argument('--out-dir', type=Path, default=base / 'results')
    args = parser.parse_args()
    try:
        result, checks = calculate(args.data_dir)
    except (ValueError, OSError, OverflowError) as exc:
        parser.exit(2, f'Input error: {exc}\n')
    args.out_dir.mkdir(parents=True, exist_ok=True)
    with (args.out_dir / 'math_checks.csv').open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(checks[0]))
        writer.writeheader(); writer.writerows(checks)
    (args.out_dir / 'results.json').write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))


if __name__ == '__main__':
    main()
