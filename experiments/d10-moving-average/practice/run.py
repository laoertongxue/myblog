"""Run the D10 validation comparison. No test labels, reader or unseal command."""
from pathlib import Path
import argparse
import csv
import hashlib
import json
import math
from baseline import forecast_at, load_csv, moving_average, validate_development, windows

ROOT = Path(__file__).resolve().parent
METHODS = [('MA3', 'moving_average', 3), ('MA7', 'moving_average', 7),
           ('MA14', 'moving_average', 14), ('SNaive7', 'seasonal_naive_7', 7)]


def dump_json(path, payload):
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8', newline='\n')


def write_csv(path, records):
    if not records:
        raise ValueError('no records to write')
    with path.open('w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(records[0]), lineterminator='\n')
        writer.writeheader()
        writer.writerows(records)


def verify_source():
    manifest = json.loads((ROOT / 'source_manifest.json').read_text(encoding='utf-8'))
    for relative, expected in manifest['files'].items():
        actual = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError(f'source bytes changed: {relative}; expected {expected}; got {actual}')
    return manifest


def compare(rows, case, daily_unit, total_unit):
    validate_development(rows)
    daily_records, window_records, summaries = [], [], []
    for label, method, k in METHODS:
        daily_errors, total_errors = [], []
        for origin, first, last in windows(113, 140, 1):
            pred = forecast_at(rows, origin, 1, method, k)[0]
            actual = rows[first - 1]['demand']
            error = abs(actual - pred)
            daily_errors.append(error)
            daily_records.append({
                'case': case, 'method': label, 'unit': daily_unit,
                'origin_day': origin, 'origin_date': rows[origin - 1]['date'],
                'target_day': first, 'target_date': rows[first - 1]['date'],
                'actual': actual, 'prediction': pred, 'absolute_error': error})
        for origin, first, last in windows(113, 140, 5):
            pred = forecast_at(rows, origin, 5, method, k)
            actual = [row['demand'] for row in rows[first - 1:last]]
            predicted_total, actual_total = math.fsum(pred), math.fsum(actual)
            error = abs(actual_total - predicted_total)
            total_errors.append(error)
            record = {'case': case, 'method': label, 'total_unit': total_unit,
                      'origin_day': origin, 'origin_date': rows[origin - 1]['date'],
                      'first_target_day': first, 'last_target_day': last,
                      'first_target_date': rows[first - 1]['date'],
                      'last_target_date': rows[last - 1]['date']}
            for h in range(5):
                record[f'prediction_h{h+1}'] = pred[h]
                record[f'actual_h{h+1}'] = actual[h]
            record.update(predicted_total=predicted_total, actual_total=actual_total, absolute_total_error=error)
            window_records.append(record)
        summaries.append({'method': label, 'k_or_period': k,
                          'daily_count': len(daily_errors),
                          'daily_mae': math.fsum(daily_errors) / len(daily_errors),
                          'daily_unit': daily_unit,
                          'five_day_window_count': len(total_errors),
                          'five_day_total_mae': math.fsum(total_errors) / len(total_errors),
                          'five_day_total_unit': total_unit})
    return daily_records, window_records, summaries


def main():
    source = verify_source()
    policy = json.loads((ROOT / 'policy.json').read_text(encoding='utf-8'))
    # Policy is documentation, not a hidden alternative way to change code behavior.
    if policy['moving_average_candidates'] != [3, 7, 14] or policy['splits'] != {'train': [1, 112], 'validation': [113, 140], 'test': [141, 180]}:
        raise ValueError('policy does not match D10 implementation')
    out = ROOT / 'results'
    out.mkdir(exist_ok=True)
    all_daily, all_windows, summary, hands = [], [], {}, {}
    for case, meta in policy['series'].items():
        rows = load_csv(ROOT / 'data' / f'{case}-development.csv', meta['identity'])
        daily, cumulative, metrics = compare(rows, case, meta['daily_unit'], meta['total_unit'])
        all_daily.extend(daily)
        all_windows.extend(cumulative)
        summary[case] = metrics
        hands[case] = {'origin_day': 112, 'origin_date': rows[111]['date'],
                       'known_last_14': [row['demand'] for row in rows[98:112]],
                       'daily_unit': meta['daily_unit'], 'five_day_total_unit': meta['total_unit'],
                       'methods': {label: {'next_day': forecast_at(rows, 112, 1, method, k)[0],
                                           'fixed_origin_five_day': forecast_at(rows, 112, 5, method, k),
                                           'five_day_total': math.fsum(forecast_at(rows, 112, 5, method, k))}
                                   for label, method, k in METHODS}}
    write_csv(out / 'daily_predictions.csv', all_daily)
    write_csv(out / 'five_day_windows.csv', all_windows)
    dump_json(out / 'validation_summary.json', {'version': 'D10-v1', 'split': 'validation only',
              'daily_target_days': [113, 140], 'five_day_first_targets': [113, 136],
              'warning': 'Simulated data; overlapping five-day windows; units not pooled; no test evaluation.',
              'source_files_sha256': source['files'], 'cases': summary})
    dump_json(out / 'origin112_examples.json', hands)
    dump_json(out / 'manual_oracle.json', {
        'description': 'Hand-calculated independent expectation, not fitted business data.',
        'observed': [10, 20, 30], 'k': 3,
        'expected_next_day': 20, 'expected_fixed_origin_five_day': [20, 20, 20, 20, 20],
        'expected_five_day_total': 100})
    print(json.dumps(summary, ensure_ascii=False, indent=2, allow_nan=False))


if __name__ == '__main__':
    argparse.ArgumentParser(description=__doc__).parse_args()
    main()
