from pathlib import Path
import copy, csv, hashlib, json, subprocess, sys, tempfile, zipfile
from datetime import datetime, timezone
ROOT=Path(__file__).resolve().parents[2]
# Preserve first-pass evidence while executing the same independent oracle and original attacks.
source=(ROOT/'docs/d15-review/round1-independent.py').read_text().replace('round1-results.json','round1-retest-results.json').replace('round1-reader.log','round1-retest-reader.log')
exec(compile(source, str(ROOT/'docs/d15-review/round1-independent.py'), 'exec'))
assert report['zero_target_empty_event_attack']['exit_code']==0
assert report['unknown_event_field'].startswith('REJECTED')
# Check explicit schema on all three event types and on ledger; missing and extra fields.
c,rows=m.load_case('hewei');ledger,events=m.simulate(c,rows)
for kind in ('initial_open','placed','arrival'):
    for mode in ('extra','missing'):
        bad=copy.deepcopy(events);e=next(e for e in bad if e['event']==kind)
        if mode=='extra':e['cancelled_quantity']=3
        else:del e['unit']
        try:m.audit(c,rows,ledger,bad)
        except ValueError:pass
        else:raise AssertionError((kind,mode,'was accepted'))
for mode in ('extra','missing'):
    bad=copy.deepcopy(ledger)
    if mode=='extra':bad[0]['backorders']=3
    else:del bad[0]['unit']
    try:m.audit(c,rows,bad,events)
    except ValueError:pass
    else:raise AssertionError(('ledger',mode,'was accepted'))
with tempfile.TemporaryDirectory() as tmp:
    t=Path(tmp)
    with zipfile.ZipFile(ROOT/'static/downloads/d15-inventory-position-practice.zip') as z:z.extractall(t)
    c=json.loads((t/'parameters.json').read_text())
    c['hewei'].update(initial_on_hand=0,order_up_to=0,initial_orders=[])
    (t/'parameters.json').write_text(json.dumps(c))
    manifest=json.loads((t/'source_manifest.json').read_text());manifest['files']['parameters.json']=hashlib.sha256((t/'parameters.json').read_bytes()).hexdigest();(t/'source_manifest.json').write_text(json.dumps(manifest))
    subprocess.run([sys.executable,'-B',str(t/'run.py')],cwd='/tmp',check=True,stdout=subprocess.DEVNULL)
    with (t/'results/hewei-order-events.csv').open() as f:
        reader=csv.DictReader(f);assert reader.fieldnames==m.EVENT_FIELDS;assert list(reader)==[]
    s=json.loads((t/'results/summary.json').read_text())['cases']['hewei']
    assert s['total_lost_sales']==42 and s['closing_on_hand']==0 and s['closing_pending_orders']==[]
    before={p.name:p.read_bytes() for p in (t/'results').iterdir()}
    subprocess.run([sys.executable,'-B',str(t/'run.py')],cwd='/tmp',check=True,stdout=subprocess.DEVNULL)
    assert all((t/'results'/n).read_bytes()==b for n,b in before.items())
summary=json.loads((P/'results/summary.json').read_text())['cases']
for case in ('hewei','apparel'):
    c,rows=m.load_case(case);_,queue=oracle(c,rows)
    assert {o['arrival_day']:o['quantity'] for o in summary[case]['closing_pending_orders']}==queue
article=(ROOT/'content/blog/inventory-position-event-timing/index.md').read_text()
date_line=next(x for x in article.splitlines() if x.startswith('date: '))
assert datetime.fromisoformat(date_line[6:])<=datetime.now(timezone.utc)
print('PASS: original empty-event attack, strict schemas (8 attacks), header-only CSV and deterministic rerun, pending queue, article date',date_line)
