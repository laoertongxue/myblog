"""prepare -> freeze -> finalize. No parameter search and no test-driven selection."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
from baseline import forecast_at, validate, windows
from generate import generate, SEED, SPLITS, VERSION

ROOT = Path(__file__).resolve().parent
POLICY = {'version': VERSION, 'seed': SEED, 'period': 7, 'splits': SPLITS,
          'core': 'hewei/A/SKU01', 'units': {'hewei': 'kg/day', 'apparel': 'pieces/day'},
          'daily': 'rolling origin, horizon=1, all days in block',
          'five_day': 'rolling origin, horizon=5, full target window inside block',
          'selection': 'period=7 fixed by weekly teaching hypothesis; no tuning',
          'test_history': 'past observed test days may update history; policy fixed'}


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=['day', 'date', 'demand', 'split'], lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path, start, end, allowed_splits):
    with path.open(encoding='utf-8', newline='') as stream:
        rows = list(csv.DictReader(stream))
    if len(rows) != end-start+1:
        raise ValueError('wrong block length')
    from generate import START
    from datetime import timedelta
    for day, row in enumerate(rows,start):
        expected = next(k for k,(a,b) in SPLITS.items() if a <= day <= b)
        if (int(row['day']) != day or row['split'] != expected or expected not in allowed_splits
                or row['date'] != (START+timedelta(days=day-1)).isoformat()):
            raise ValueError('CSV day/date/split mismatch')
    result = [{'date': r['date'], 'demand': int(r['demand'])} for r in rows]
    validate(result)
    return result


def score(rows, start, end):
    daily, cumulative = [], []
    for origin, first, last in windows(start, end, 1):
        prediction = forecast_at(rows, origin, 1)[0]
        daily.append({'day': first, 'actual': rows[first-1]['demand'], 'forecast': prediction})
    for origin, first, last in windows(start, end, 5):
        prediction = sum(forecast_at(rows, origin, 5))
        actual = sum(r['demand'] for r in rows[first-1:last])
        cumulative.append({'origin': origin, 'first': first, 'last': last,
                           'actual': actual, 'forecast': prediction})
    return {'days': len(daily), 'mae': sum(abs(r['actual']-r['forecast']) for r in daily)/len(daily),
            'five_day_windows': len(cumulative),
            'five_day_sum_mae': sum(abs(r['actual']-r['forecast']) for r in cumulative)/len(cumulative),
            'daily': daily, 'five_day': cumulative}


def prepare():
    if (ROOT/'freeze.json').exists() or (ROOT/'results/test.json').exists():
        raise ValueError('existing frozen/test candidate: use a fresh directory to prepare a new candidate')
    for case in ('hewei', 'apparel'):
        rows = generate(case)
        marked = [dict(day=i, **row, split=next(k for k,(a,b) in SPLITS.items() if a <= i <= b))
                  for i,row in enumerate(rows,1)]
        write_csv(ROOT/f'data/{case}-development.csv', marked[:140])
        write_csv(ROOT/f'sealed/{case}-test.csv', marked[140:])
        dump(ROOT/f'results/{case}-validation.json', score(rows[:140], 113, 140))
    dump(ROOT/'policy.json', POLICY)
    dump(ROOT/'results/hand.json', {'origin':112, 'source_days':list(range(106,113)),
         'target_days':list(range(113,120)), 'values':forecast_at(generate(),112,7)})
    print('Prepared development data and separate test labels; test scores not read.')


def freeze():
    paths = ['baseline.py', 'generate.py', 'run.py', 'policy.json'] + [
        f'{folder}/{case}-{suffix}.csv' for case in ('hewei','apparel')
        for folder,suffix in [('data','development'),('sealed','test')]]
    dump(ROOT/'freeze.json', {'policy': POLICY, 'sha256': {p:digest(ROOT/p) for p in paths},
         'note':'Reproducible policy receipt, not access control or proof of an earlier timestamp. See review log.'})
    print('Frozen code, policy and data hashes before test evaluation.')


def finalize():
    receipt = json.loads((ROOT/'freeze.json').read_text(encoding='utf-8'))
    if receipt['policy'] != POLICY or any(digest(ROOT/p) != sha for p,sha in receipt['sha256'].items()):
        raise ValueError('frozen candidate changed; review and freeze a new candidate explicitly')
    report = {}
    for case in ('hewei','apparel'):
        rows = (read_csv(ROOT/f'data/{case}-development.csv',1,140,{'train','validation'})
                + read_csv(ROOT/f'sealed/{case}-test.csv',141,180,{'test'}))
        validate(rows)
        if rows != generate(case):
            raise ValueError('generated data mismatch')
        report[case] = score(rows,141,180)
    dump(ROOT/'results/test.json', report)
    print(json.dumps({case:{k:v for k,v in r.items() if k not in ('daily','five_day')} for case,r in report.items()},indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=['prepare','freeze','finalize'])
    {'prepare':prepare,'freeze':freeze,'finalize':finalize}[parser.parse_args().phase]()
