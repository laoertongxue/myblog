"""D14 model selection audit. Forecast issuance and later scoring are separate."""
from pathlib import Path
from datetime import date, timedelta
import argparse
import csv
import hashlib
import json
import math
from baseline import forecast_at, load_csv, validate_development, windows
from metrics import evaluate

ROOT = Path(__file__).resolve().parent
RUN_ID = 'D14-v1-development-selection-audit'
METHODS = [('SNaive7', {'method': 'seasonal_naive_7'})] + [
    (f'MA{k}', {'method': 'moving_average', 'k': k}) for k in (3, 7, 14)] + [
    (f'SES{a}', {'method': 'ses', 'alpha': a}) for a in (.2, .5, .8)]
CASES = {'hewei': ('hewei/A/SKU01', 'kg/day', 'kg'),
         'apparel': ('anonymous-apparel/terminal-order-demand', 'pieces/day', 'pieces')}


def dump_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8', newline='\n')


def write_csv(path, records):
    with path.open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(records[0]), lineterminator='\n')
        writer.writeheader()
        writer.writerows(records)


def verify_source():
    manifest = json.loads((ROOT/'source_manifest.json').read_text(encoding='utf-8'))
    for name, expected in manifest['files'].items():
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest() != expected:
            raise ValueError(f'source bytes changed: {name}')
    return manifest


def issue(rows, origin, horizon, case, label, args):
    """No future labels, flags or dates are consulted to issue this vintage."""
    predictions = forecast_at(rows, origin, horizon, **args)
    # forecast_at has validated only rows[:origin]. Check identity within
    # that known history; never inspect a future row to bind the case.
    if case not in CASES or rows[origin-1]['series'] != CASES[case][0]:
        raise ValueError('history series does not match case identity')
    origin_date = date.fromisoformat(rows[origin-1]['date'])
    identity, daily_unit, _ = CASES[case]
    return [{'run_id': RUN_ID, 'case': case, 'series': identity, 'method': label,
             'parameters': json.dumps(args, sort_keys=True, separators=(',', ':')),
             'unit': daily_unit, 'task_horizon': horizon, 'origin_day': origin,
             'origin_date': origin_date.isoformat(), 'history_last_day': origin,
             'target_day': origin+h, 'target_date': (origin_date+timedelta(days=h)).isoformat(),
             'h': h, 'prediction': value}
            for h, value in enumerate(predictions, 1)]


def replay(rows, case):
    # This validates the offline file, not a fitted transformation or forecast.
    validate_development(rows)
    if case not in CASES or rows[0]['series'] != CASES[case][0]:
        raise ValueError('development series does not match case identity')
    forecasts, totals, scores = [], [], []
    for label, args in METHODS:
        for horizon in (1, 5):
            scored = []
            for origin, first, last in windows(113, 140, horizon):
                vintage = issue(rows, origin, horizon, case, label, args)
                # Only after the entire vintage is issued are targets attached.
                for record in vintage:
                    target = rows[record['target_day']-1]
                    assert target['date'] == record['target_date']
                    record.update(actual=target['demand'], error=target['demand']-record['prediction'])
                forecasts.extend(vintage)
                actual = math.fsum(r['actual'] for r in vintage)
                prediction = math.fsum(r['prediction'] for r in vintage)
                row = {key: vintage[0][key] for key in ('run_id','case','series','method','parameters','origin_day','origin_date')}
                row.update(task_horizon=horizon, unit=CASES[case][1 if horizon == 1 else 2],
                           first_target_day=first, last_target_day=last,
                           first_target_date=vintage[0]['target_date'], last_target_date=vintage[-1]['target_date'],
                           actual=actual, prediction=prediction, error=actual-prediction,
                           sum_daily_absolute_errors=math.fsum(abs(r['error']) for r in vintage))
                scored.append(row)
                totals.append(row)
            scores.append({'case':case, 'method':label, 'parameters':json.dumps(args, sort_keys=True),
                           'task_horizon':horizon, 'unit':CASES[case][1 if horizon == 1 else 2],
                           **evaluate([r['actual'] for r in scored], [r['prediction'] for r in scored])})
    return forecasts, totals, scores


def leakage_diagnostics(rows, case):
    reports = []
    for origin in range(112, 136):
        for label, args in METHODS:
            original = issue(rows, origin, 5, case, label, args)
            # Poison labels and flags, then also remove future mappings entirely.
            altered = [dict(r) for r in rows]
            for r in altered[origin:]:
                r.update(demand=r['demand']+10000, stockout=True, observed=False)
            assert original == issue(altered, origin, 5, case, label, args)
            assert original == issue(rows[:origin]+[None]*(len(rows)-origin), origin, 5, case, label, args)
            assert original == issue(rows[:origin], origin, 5, case, label, args)
            reports.append({'case':case,'method':label,'origin_day':origin,'horizon':5,
                            'future_label_flag_attack':'unchanged', 'invalid_future_attack':'unchanged',
                            'prefix_only_attack':'unchanged'})
    # A deliberately WRONG negative control: five later revisions are not a vintage.
    origin = 117
    label, args = METHODS[-1]
    fixed = [r['prediction'] for r in issue(rows, origin, 5, case, label, args)]
    revised = [issue(rows, origin+h, 1, case, label, args)[0]['prediction'] for h in range(5)]
    return reports, {'case':case,'method':label,'origin_day':origin,'target_days':[118,119,120,121,122],
                     'fixed_origin_predictions':fixed, 'later_one_step_revisions_WRONG_FOR_ORIGIN117':revised,
                     'fixed_total':math.fsum(fixed),'revised_total':math.fsum(revised),
                     'warning':'revisions use new observations; never used as five-day scores'}


def rankings(scores):
    """Retrospective evidence only: never called by issue or replay."""
    result = []
    for case in CASES:
        for horizon in (1, 5):
            options = [r for r in scores if r['case'] == case and r['task_horizon'] == horizon]
            for metric in ('mae', 'rmse'):
                ordered = sorted(options, key=lambda r: (r[metric], r['method']))
                for rank, row in enumerate(ordered, 1):
                    result.append({'case':case, 'task_horizon':horizon, 'metric':metric,
                                   'rank':rank, 'method':row['method'], 'value':row[metric],
                                   'unit':row['unit'], 'n':row['n']})
    return result


def main():
    source = verify_source()
    forecasts, totals, scores, attacks, negative = [], [], [], [], []
    for case, (identity, _, _) in CASES.items():
        rows = load_csv(ROOT/'data'/f'{case}-development.csv', identity)
        f,t,s = replay(rows,case)
        forecasts.extend(f); totals.extend(t); scores.extend(s)
        a,n = leakage_diagnostics(rows,case)
        attacks.extend(a); negative.append(n)
    out = ROOT/'results'; out.mkdir(exist_ok=True)
    for name, data in [('predictions',forecasts),('window_totals',totals),('metrics',scores),
                       ('rankings',rankings(scores)),('leakage_diagnostics',attacks)]:
        write_csv(out/f'{name}.csv',data)
    dump_json(out/'negative_control.json',negative)
    dump_json(out/'run_manifest.json',{'run_id':RUN_ID,'source':source,'methods':METHODS,
              'initial_history':[1,112],'validation':[113,140], 'forecasts':len(forecasts),
              'one_day_origins':[112,139], 'five_day_origins':[112,135],
              'one_day_targets_per_method_case':28,'five_day_windows_per_method_case':24,
              'forecast_order':'issue all h at an origin before attach labels; expanding observed history across origins',
              'test_labels':'not included or accessed; original test summaries already exposed',
              'claim_limit':'repeatedly inspected simulated development replay, not blind test or business benefit',
              'selection_timing':'post replay audit only; no choice fed into past predictions',
              'tie_break':'ascending method label; ordinal order is not significance',
              'new_models':'SARIMA, Croston family and trees NOT implemented or scored',
              'five_day_wape_denominator':'sum of actual totals across 24 overlapping windows, not unique volume'})
    output_files = sorted(p for p in out.iterdir() if p.is_file() and p.name != 'output_hashes.json')
    dump_json(out/'output_hashes.json',{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in output_files})
    print(f'{len(forecasts)} forecast rows, {len(totals)} totals, {len(scores)} scores, {len(attacks)} attack cases.')


if __name__ == '__main__':
    argparse.ArgumentParser(description=__doc__).parse_args()
    main()
