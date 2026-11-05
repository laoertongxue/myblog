"""D12: seven existing candidates, identical validation targets, no test labels."""
from pathlib import Path
from datetime import date
import argparse
import csv
import hashlib
import json
from baseline import forecast_at, load_csv, validate_development, windows
from metrics import evaluate

ROOT = Path(__file__).resolve().parent
METHODS = [('SNaive7', {'method': 'seasonal_naive_7'})] + [
    (f'MA{k}', {'method': 'moving_average', 'k': k}) for k in (3, 7, 14)] + [
    (f'SES{a}', {'method': 'ses', 'alpha': a}) for a in (.2, .5, .8)]
CASES = {'hewei': ('hewei/A/SKU01', 'kg/day', 'kg'),
         'apparel': ('anonymous-apparel/terminal-order-demand', 'pieces/day', 'pieces')}


def write_csv(path, records):
    with path.open('w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(records[0]), lineterminator='\n')
        w.writeheader()
        w.writerows(records)


def dump_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8', newline='\n')


def verify_source():
    source = json.loads((ROOT/'source_manifest.json').read_text())
    for name, expected in source['files'].items():
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest() != expected:
            raise ValueError(f'source bytes changed: {name}')
    return source


def compare(rows, case, daily_unit, total_unit):
    validate_development(rows)
    daily, totals, scores = [], [], []
    for label, args in METHODS:
        selected = []
        for origin, first, last in windows(113, 140, 1):
            target = rows[first-1]
            pred = forecast_at(rows, origin, 1, **args)[0]
            actual = target['demand']
            record = {'case': case, 'method': label, 'unit': daily_unit,
                      'origin_day': origin, 'origin_date': rows[origin-1]['date'],
                      'target_day': first, 'target_date': target['date'],
                      'day_group': 'weekend' if date.fromisoformat(target['date']).weekday() >= 5 else 'weekday',
                      'actual': actual, 'prediction': pred, 'error': actual-pred,
                      'absolute_error': abs(actual-pred)}
            daily.append(record)
            selected.append(record)
        for group in ('all', 'weekday', 'weekend'):
            records = [r for r in selected if group == 'all' or r['day_group'] == group]
            scores.append({'case': case, 'method': label, 'group': group, 'unit': daily_unit,
                           **evaluate([r['actual'] for r in records], [r['prediction'] for r in records])})
        # Same-origin five-day totals are a separate task, never assembled from daily revisions.
        for origin, first, last in windows(113, 140, 5):
            preds = forecast_at(rows, origin, 5, **args)
            actuals = [r['demand'] for r in rows[first-1:last]]
            record = {'case': case, 'method': label, 'unit': total_unit, 'origin_day': origin,
                      'first_target_day': first, 'last_target_day': last}
            for h in range(5):
                record[f'prediction_h{h+1}'] = preds[h]
                record[f'actual_h{h+1}'] = actuals[h]
            record.update(actual_total=sum(actuals), prediction_total=sum(preds), error=sum(actuals)-sum(preds))
            totals.append(record)
    return daily, totals, scores


def main():
    source = verify_source()
    daily, totals, scores = [], [], []
    for case, (identity, unit, total_unit) in CASES.items():
        rows = load_csv(ROOT/'data'/f'{case}-development.csv', identity)
        d, t, s = compare(rows, case, unit, total_unit)
        daily.extend(d); totals.extend(t); scores.extend(s)
    out = ROOT/'results'
    out.mkdir(exist_ok=True)
    write_csv(out/'daily_predictions.csv', daily)
    write_csv(out/'five_day_windows.csv', totals)
    write_csv(out/'metrics.csv', scores)
    dump_json(out/'validation_summary.json', {'version': 'D12-v2', 'run_id': 'D12-v2-validation-113-140',
        'source_files_sha256': source['files'], 'methods': METHODS,
        'train_days': [1,112], 'validation_days': [113,140], 'error_sign': 'actual - prediction',
        'wape_storage': 'ratio; multiply by 100 for percent', 'grouping': 'target date Monday-Friday / Saturday-Sunday, no holiday adjustment',
        'selection': 'all existing candidates shown; no final selection or test evaluation', 'metrics': scores})
    dump_json(out/'manual_oracle.json', {'actual': [0,10], 'prediction': [2,8], 'error': [-2,2],
        'expected': {'mae':2, 'rmse':2, 'me':0, 'wape':0.4},
        'zero_actual_example': {'actual':[0,0], 'prediction':[2,0], 'mae':1, 'me':-1, 'rmse':2**0.5, 'wape':None}})
    print(f'{len(daily)} daily predictions; {len(totals)} fixed-origin windows; {len(scores)} metric rows.')


if __name__ == '__main__':
    argparse.ArgumentParser(description=__doc__).parse_args()
    main()
