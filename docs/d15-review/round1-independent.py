"""Independent D15 integer recurrence, archive checks, and boundary attacks."""
from pathlib import Path
import csv, json, hashlib, importlib.util, random, tempfile, subprocess, sys, zipfile, copy
ROOT=Path(__file__).resolve().parents[2]
P=ROOT/'experiments/d15-inventory-position/practice'
spec=importlib.util.spec_from_file_location('candidate',P/'run.py'); m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
report={}
def oracle(c,rows):
    stock=int(c['initial_on_hand']); schedule={}; result=[]
    for o in c['initial_orders']: schedule[o['arrival_day']]=schedule.get(o['arrival_day'],0)+int(o['quantity'])
    for d,r in enumerate(rows,1):
        opening=stock; opening_order=sum(schedule.values()); receipt=schedule.pop(d,0); available=stock+receipt
        demand=int(r['demand']); served=min(available,demand); stock=available-served; pipeline=sum(schedule.values()); before=stock+pipeline
        q=max(0,int(c['order_up_to'])-before)
        if q: schedule[d+c['lead_time']+1]=schedule.get(d+c['lead_time']+1,0)+q
        result.append(dict(opening_on_hand=opening,opening_on_order=opening_order,arrivals=receipt,available_before_demand=available,demand=demand,served=served,lost_sales=demand-served,closing_on_hand=stock,on_order_before_order=pipeline,ip_before_order=before,order_quantity=q,on_order_after_order=pipeline+q,ip_after_order=before+q))
    return result,schedule
for case in ('hewei','apparel'):
    c,rows=m.load_case(case); expected,queue=oracle(c,rows)
    saved=list(csv.DictReader((P/f'results/{case}-ledger.csv').open()))
    for actual,exp in zip(saved,expected):
        for k,v in exp.items(): assert int(actual[k])==v,(case,k,actual[k],v)
    report[case]={'ledger_rows':len(expected),'ending_queue':queue,'demand':sum(x['demand'] for x in expected),'served':sum(x['served'] for x in expected)}
rng=random.Random(1515)
for i in range(400):
    c,rows=m.load_case('hewei');c.update(initial_on_hand=rng.randrange(40),order_up_to=rng.randrange(40),lead_time=rng.randrange(6),initial_orders=[])
    for r in rows:r['demand']=str(rng.randrange(50))
    exp,queue=oracle(c,rows);actual,_=m.simulate(c,rows)
    for a,e in zip(actual,exp):
        for k,v in e.items():assert a[k]==v,(i,k,a[k],v)
report['random_integer_scenarios']=400
with tempfile.TemporaryDirectory() as tmp:
    t=Path(tmp)
    for kind in ('practice','article','images'):
        path=ROOT/f'static/downloads/d15-inventory-position-{kind}.zip'
        with zipfile.ZipFile(path) as z:
            names=z.namelist();assert len(names)==len(set(names));assert all(not Path(n).is_absolute() and '..' not in Path(n).parts and '\\' not in n for n in names)
            entries=dict(line.split('  ',1)[::-1] for line in z.read('MANIFEST.sha256').decode().splitlines())
            assert set(entries)==set(names)-{'MANIFEST.sha256'}
            for n,h in entries.items():assert hashlib.sha256(z.read(n)).hexdigest()==h
            report[kind+'_zip_sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
            if kind=='practice':z.extractall(t)
    with (ROOT/'docs/d15-review/round1-reader.log').open('w') as log:
        subprocess.run([sys.executable,'-B','-m','unittest','-v'],cwd=t,stdout=log,stderr=log,check=True)
        before={p.relative_to(t):p.read_bytes() for p in t.rglob('*') if p.is_file()}
        subprocess.run([sys.executable,'-B',str(t/'run.py')],cwd='/tmp',stdout=log,stderr=log,check=True)
        assert all((t/n).read_bytes()==b for n,b in before.items())
    # Genuine reader variant: re-sign changed inputs in isolated copy, as README permits.
    conf=json.loads((t/'parameters.json').read_text());conf['hewei'].update(initial_on_hand=0,order_up_to=0,initial_orders=[])
    (t/'parameters.json').write_text(json.dumps(conf))
    manifest=json.loads((t/'source_manifest.json').read_text())
    manifest['files']['parameters.json']=hashlib.sha256((t/'parameters.json').read_bytes()).hexdigest()
    (t/'source_manifest.json').write_text(json.dumps(manifest))
    proc=subprocess.run([sys.executable,'-B',str(t/'run.py')],cwd='/tmp',capture_output=True,text=True)
    report['zero_target_empty_event_attack']={'exit_code':proc.returncode,'stderr':proc.stderr}
# Audit does not reject unsupported fields on known event types.
c,rows=m.load_case('hewei');ledger,events=m.simulate(c,rows)
events[0]['cancelled_quantity']=3
try:m.audit(c,rows,ledger,events);report['unknown_event_field']='ACCEPTED cancelled_quantity=3'
except Exception as e:report['unknown_event_field']='REJECTED '+repr(e)
(ROOT/'docs/d15-review/round1-results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False,indent=2))
