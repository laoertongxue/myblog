"""D20 frozen continuation. Does not alter D9/D19 or select new parameters."""
import csv
import hashlib
import io
import json
import math
import importlib.util
from datetime import date,timedelta
from pathlib import Path
ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('d19_engine',ROOT/'source/d19_engine.py')
engine=importlib.util.module_from_spec(spec);spec.loader.exec_module(engine)
canonical=engine.canonical
csv_bytes=engine.csv_bytes
digest=engine.digest
EXPECTED_CONFIG='ee52a89b4dfd208160a30338cffbcfedfe2bf53e37e01a6cefd52200ea11400d'
EXPECTED_D9='273f1a5c13363109660030e3df6c618d601759c3db08c0b65ea6ea0c3f469d0e'

def load_frozen():
    raw=(ROOT/'source/d19_frozen_config.json').read_bytes()
    if digest(raw)!=EXPECTED_CONFIG: raise ValueError('D19 frozen configuration mismatch')
    cfg=json.loads(raw)
    if digest((ROOT/'source/d19_protocol.json').read_bytes())!=cfg['protocol_sha256']:raise ValueError('D19 protocol mismatch')
    return cfg

def load_data(case):
    if case not in ('hewei','apparel'):raise ValueError('unknown case')
    receipt=(ROOT/'source/d9_freeze.json').read_bytes()
    if digest(receipt)!=EXPECTED_D9:raise ValueError('D9 receipt mismatch')
    hashes=json.loads(receipt)['sha256']; values=[]
    for kind,start,end,prefix in [('development',1,140,'data'),('test',141,180,'sealed')]:
        raw=(ROOT/f'data/{case}-{kind}.csv').read_bytes()
        if digest(raw)!=hashes[f'{prefix}/{case}-{kind}.csv']:raise ValueError('source hash mismatch')
        rows=list(csv.DictReader(io.StringIO(raw.decode('utf8'))))
        if len(rows)!=end-start+1:raise ValueError('row count')
        for day,r in zip(range(start,end+1),rows):
            if set(r)!={'day','date','demand','split'} or r['day']!=str(day) or r['date']!=(date(2026,4,6)+timedelta(days=day-1)).isoformat() or r['split']!=('train' if day<=112 else 'validation' if day<=140 else 'test'):raise ValueError('schema/date/split')
            if not r['demand'].isdigit():raise ValueError('nonnegative integer demand required')
            values.append(int(r['demand']))
    return values

def forecast_rows(data,case,unit):
    rows=[]
    for h in (1,5):
        for origin in range(140,181-h):
            predicted=sum(engine.forecast(data[:origin],h));actual=sum(data[origin:origin+h])
            rows.append(dict(case=case,unit=unit,horizon=h,origin=origin,target_start=origin+1,target_end=origin+h,prediction=predicted,actual=actual,error=actual-predicted))
    return rows

def build():
    cfg=load_frozen(); summaries=[];ledgers=[];events=[];pending=[];forecasts=[];forecast_summary=[];comparisons=[]
    validation=json.loads((ROOT/'source/d19_validation_results.json').read_text())
    for case in ('hewei','apparel'):
        data=load_data(case);case_cfg=cfg['cases'][case];unit=case_cfg['unit']
        fr=forecast_rows(data,case,unit);forecasts.extend(fr)
        for h in (1,5):
            rr=[r for r in fr if r['horizon']==h]; errors=[r['error'] for r in rr]
            forecast_summary.append(dict(case=case,unit=unit,horizon=h,n=len(rr),MAE=sum(abs(e) for e in errors)/len(errors),RMSE=math.sqrt(sum(e*e for e in errors)/len(errors)),ME=sum(errors)/len(errors),error_sign='actual minus prediction'))
        for policy in ('daily_sQ','periodic_RS'):
            selected=case_cfg['winners'][policy];p=selected['parameters']
            ledger,ee,pp,summary=engine.simulate(data[152:180],data[:152],p,case_cfg['initial_oh'],case_cfg['initial_pipeline'],start=153)
            prefix=dict(case=case,unit=unit,policy=policy,candidate=selected['candidate'])
            ledgers.extend(dict(**prefix,**r) for r in ledger);events.extend(dict(**prefix,**r) for r in ee);pending.extend(dict(**prefix,**r) for r in pp)
            summaries.append(dict(**prefix,**summary,initial_oh=case_cfg['initial_oh'],initial_pipeline=0,parameters=p,start_day=153,end_day=180,days=28))
            v=next(r for r in validation if r['case']==case and r['candidate']==selected['candidate'])
            comparisons.append(dict(**prefix,validation={k:v[k] for k in ('demand','lost','mean_end_oh','order_count','fill_rate')},test={k:summary[k] for k in ('demand','lost','mean_end_oh','order_count','fill_rate')},note='Different demand segments; descriptive only; no retuning'))
    output={'results.json':canonical(summaries).encode(),'forecast_metrics.json':canonical(forecast_summary).encode(),'validation_test_comparison.json':canonical(comparisons).encode()}
    for name,rows in [('ledger.csv',ledgers),('order_events.csv',events),('pending.csv',pending),('forecast_windows.csv',forecasts)]:output[name]=csv_bytes(rows,list(rows[0]))
    output['execution_receipt.json']=canonical(dict(version='D20-frozen-continuation-v1',source_config_sha256=EXPECTED_CONFIG,source_protocol_sha256=cfg['protocol_sha256'],forecast_days=[141,180],inventory_days=[153,180],review_anchor=153,no_inventory_warmup=True,initial_state='same frozen OH and empty pipeline per case',no_retuning=True,historical_exposure='D9 published original test summaries; D19 protocol v2 revised after validation; not a new blind holdout',result_sha256={n:digest(b) for n,b in output.items()})).encode()
    return output

def verify():
    manifest=json.loads((ROOT/'manifest.json').read_text())
    for name,sha in manifest.items():
        if digest((ROOT/name).read_bytes())!=sha:raise ValueError('integrity mismatch: '+name)
    generated=build()
    for name,raw in generated.items():
        if raw!=(ROOT/'output'/name).read_bytes():raise ValueError('replay mismatch: '+name)
    return generated

if __name__=='__main__':
    verify();print('D20 verified: 4 frozen strategies, 112 inventory rows, 80 one-day and 72 five-day forecast windows. No parameter search or D9/D19 modification.')
