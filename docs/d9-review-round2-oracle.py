"""Independent round-two review. Does not edit the production candidate."""
from pathlib import Path
from datetime import date, timedelta
from fractions import Fraction
from copy import deepcopy
import csv
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile

REPO = Path(__file__).resolve().parents[1]
SOURCE = REPO/'examples/d9-seasonal-naive'
sys.path.insert(0,str(SOURCE))
import baseline
import run


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def independent_data(case):
    state=20261102+(1 if case=='apparel' else 0)
    base={'hewei':[20,22,21,24,28,36,32], 'apparel':[80,84,86,88,110,140,126]}[case]
    output=[]
    for index in range(180):
        state=(state*1664525+1013904223) & 0xffffffff
        value=base[index%7]+state%7-3
        if case=='apparel': value+=index//14+(90 if 117<=index<=119 else 0)
        output.append({'date':str(date(2026,4,6)+timedelta(days=index)), 'demand':max(0,value)})
    return output


def independent_prediction(rows,T,H):
    # One-based target index reduced to the last observed matching weekday.
    return [rows[T+h-7*((h-1)//7+1)-1]['demand'] for h in range(1,H+1)]


def independent_score(rows,a,b):
    daily=[{'day':d, 'actual':rows[d-1]['demand'], 'forecast':rows[d-8]['demand']} for d in range(a,b+1)]
    windows=[]
    for first in range(a,b-3):
        origin=first-1
        windows.append({'origin':origin,'first':first,'last':first+4,
                        'actual':sum(r['demand'] for r in rows[first-1:first+4]),
                        'forecast':sum(independent_prediction(rows,origin,5))})
    return {'days':len(daily),'daily':daily,'mae':float(Fraction(sum(abs(r['actual']-r['forecast']) for r in daily),len(daily))),
            'five_day_windows':len(windows),'five_day':windows,
            'five_day_sum_mae':float(Fraction(sum(abs(r['actual']-r['forecast']) for r in windows),len(windows)))}


def command(directory,*args,ok=True):
    result=subprocess.run([sys.executable,*args],cwd=directory,text=True,encoding='utf-8',capture_output=True)
    assert (result.returncode==0)==ok,(args,result.stdout,result.stderr)
    return {'args':list(args),'returncode':result.returncode,'stdout':result.stdout,'stderr':result.stderr}


evidence={'reviewer':'independent child d9_review2','candidate_sha256':{},'checks':{},'commands':[]}
for path in SOURCE.rglob('*'):
    if path.is_file() and '__pycache__' not in path.parts:
        evidence['candidate_sha256'][path.relative_to(SOURCE).as_posix()]=sha(path)

# Exhaustive origins, synthetic strictly increasing values: not the generator oracle.
synthetic=[{'date':str(date(2020,1,1)+timedelta(days=i)),'demand':1000+17*i} for i in range(200)]
count=0
for origin in range(7,181):
    for horizon in [1,5,7,8,14,15,40,400]:
        expected=independent_prediction(synthetic,origin,horizon)
        assert baseline.forecast_at(synthetic,origin,horizon)==expected
        polluted=deepcopy(synthetic)
        for row in polluted[origin:]: row.update(date='invalid',demand=None)
        assert baseline.forecast_at(polluted,origin,horizon)==expected
        count+=1
evidence['checks']['independent_formula_and_future_poison_groups']=count

hand=independent_prediction(independent_data('hewei'),112,7)
assert hand==[19,25,19,22,28,38,29]
evidence['checks']['hand']=hand
evidence['checks']['scores']={}
for case in ['hewei','apparel']:
    rows=independent_data(case)
    combined=[]
    for file in [SOURCE/f'data/{case}-development.csv',SOURCE/f'sealed/{case}-test.csv']:
        with file.open(encoding='utf-8',newline='') as stream:
            combined += list(csv.DictReader(stream))
    assert len(combined)==180
    for i,(row,expected) in enumerate(zip(combined,rows),1):
        assert row=={'day':str(i),'date':expected['date'],'demand':str(expected['demand']),
                     'split':'train' if i<=112 else 'validation' if i<=140 else 'test'}
    validation=independent_score(rows,113,140)
    test=independent_score(rows,141,180)
    assert validation==json.loads((SOURCE/f'results/{case}-validation.json').read_text(encoding='utf-8'))
    assert test==json.loads((SOURCE/'results/test.json').read_text(encoding='utf-8'))[case]
    assert len(test['daily'])==40 and [r['day'] for r in test['daily']]==list(range(141,181))
    assert len(test['five_day'])==36 and all(141<=r['first']<=r['last']<=180 for r in test['five_day'])
    evidence['checks']['scores'][case]={name:{k:v for k,v in result.items() if k not in ['daily','five_day']}
                                      for name,result in [('validation',validation),('test',test)]}

assert all(sum(1 for _ in baseline.windows(a,b,5))==n for a,b,n in [(113,140,24),(141,180,36)])
evidence['checks']['blocks']='24 validation,36 test; no crossing,full40 test days'

# Additional direct boundary attacks independent of candidate tests.
errors=[]
for value in [0,-7,7.0,False,True,'7',None,float('nan')]:
    for name,fn in [('horizon',lambda:baseline.seasonal_naive(synthetic[:7],value)),
                    ('period',lambda:baseline.seasonal_naive(synthetic[:7],1,value))]:
        try: fn()
        except (ValueError,TypeError): errors.append(name+':'+str(value))
        else: raise AssertionError((name,value))
for n in range(7):
    try: baseline.seasonal_naive(synthetic[:n],15)
    except ValueError: errors.append('short:'+str(n))
    else: raise AssertionError(n)
for value in [-1,None,False,True,float('nan'),float('inf'),float('-inf'),'0']:
    bad=deepcopy(synthetic[:7]);bad[3]['demand']=value
    try:baseline.seasonal_naive(bad,7)
    except ValueError:errors.append('demand:'+str(value))
    else:raise AssertionError(value)
zeros=[dict(r,demand=0) for r in synthetic[:7]]
assert baseline.seasonal_naive(zeros,15)==[0]*15
evidence['checks']['additional_boundary_rejections']=errors

with tempfile.TemporaryDirectory(prefix='d9-round2-') as tmp:
    copy=Path(tmp)/'copy'
    shutil.copytree(SOURCE,copy,ignore=shutil.ignore_patterns('__pycache__'))
    evidence['commands'].append(command(copy,'-m','unittest','-v'))
    before=(copy/'results/test.json').read_bytes()
    evidence['commands'].append(command(copy,'run.py','finalize'))
    assert before==(copy/'results/test.json').read_bytes()
    evidence['commands'].append(command(copy,'run.py','prepare',ok=False))
    assert before==(copy/'results/test.json').read_bytes()
    # Each code/policy/data tamper must fail without overwriting prior results.
    attacked=[]
    for target in ['baseline.py','generate.py','run.py','policy.json','data/hewei-development.csv','sealed/apparel-test.csv']:
        path=copy/target
        original=path.read_bytes()
        path.write_bytes(original+b'\n')
        evidence['commands'].append(command(copy,'run.py','finalize',ok=False))
        assert before==(copy/'results/test.json').read_bytes()
        path.write_bytes(original)
        attacked.append(target)
    evidence['checks']['freeze_tamper_rejected']=attacked
    # Run exactly the documented fresh-candidate sequence and compare all generated bytes.
    (copy/'freeze.json').unlink(); (copy/'results/test.json').unlink()
    for args in [('run.py','prepare'),('-m','unittest','-v'),('run.py','freeze'),('run.py','finalize')]:
        evidence['commands'].append(command(copy,*args))
    for folder in ['data','sealed','results']:
        for path in (SOURCE/folder).glob('*'):
            if path.is_file(): assert path.read_bytes()==(copy/folder/path.name).read_bytes()
    assert (SOURCE/'freeze.json').read_bytes()==(copy/'freeze.json').read_bytes()
    evidence['checks']['documented_full_rebuild']='byte-identical data,results,freeze receipt'

evidence['checks']['production_unchanged']=all(sha(SOURCE/path)==value for path,value in evidence['candidate_sha256'].items())
assert evidence['checks']['production_unchanged']
(REPO/'docs/d9-review-round2-evidence.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(evidence['checks'],ensure_ascii=False,indent=2))
