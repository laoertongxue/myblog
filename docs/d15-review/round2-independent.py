from pathlib import Path
import sys, json, csv, copy, random, hashlib, re, tempfile, zipfile, subprocess, os
from decimal import Decimal as D
R=Path(__file__).resolve().parents[2]; P=R/'experiments/d15-inventory-position/practice'
sys.path.insert(0,str(P)); import run

def ref(c,rows):
    stock=D(str(c['initial_on_hand'])); queue={}
    for o in c['initial_orders']: queue[o['arrival_day']]=queue.get(o['arrival_day'],D(0))+D(str(o['quantity']))
    out=[]
    for t,row in enumerate(rows,1):
        old=stock; oo=sum(queue.values(),D(0)); receipt=queue.pop(t,D(0)); available=stock+receipt
        demand=D(row['demand']); sale=min(available,demand); stock=available-sale
        pipe=sum(queue.values(),D(0)); ip=stock+pipe; q=max(D(0),D(str(c['order_up_to']))-ip)
        if q: queue[t+c['lead_time']+1]=queue.get(t+c['lead_time']+1,D(0))+q
        out.append(dict(zip(run.LEDGER_FIELDS[5:],[old,oo,receipt,available,demand,sale,demand-sale,stock,pipe,ip,q,pipe+q,ip+q])))
    return out,queue

report={'cases':{},'random_decimal_cases':0,'invalid_cases':0}
for case in run.IDENTITIES:
    c,rows=run.load_case(case); want,queue=ref(c,rows); got,events=run.simulate(c,rows)
    disk=list(csv.DictReader((P/f'results/{case}-ledger.csv').open()))
    for a,b,z in zip(want,got,disk):
        for k,v in a.items(): assert b[k]==v==D(z[k]),(case,k)
    report['cases'][case]={'total_demand':str(sum(r['demand'] for r in want)), 'served':str(sum(r['served'] for r in want)), 'lost':str(sum(r['lost_sales'] for r in want)), 'receipts':str(sum(r['arrivals'] for r in want)), 'orders':str(sum(r['order_quantity'] for r in want)), 'closing':str(want[-1]['closing_on_hand']),'pending':{k:str(v) for k,v in queue.items()}}
    if case=='hewei':
        article=(R/'content/blog/inventory-position-event-timing/index.md').read_text()
        table=re.findall(r'<tr>((?:<td>.*?</td>)+)</tr>',article)
        for day,(html,w) in enumerate(zip(table,want),1):
            actual=[int(x) for x in re.findall('<td>(.*?)</td>',html)]
            expected=[day]+[int(w[k]) for k in ['arrivals','demand','served','lost_sales','closing_on_hand','on_order_before_order','ip_before_order','order_quantity']]+[day+3]
            assert actual==expected
random.seed(1502)
for trial in range(600):
    c,rows=run.load_case('hewei'); c.update(initial_orders=[], initial_on_hand=str(D(random.randrange(100000))/1000),order_up_to=str(D(random.randrange(100000))/1000),lead_time=random.randrange(7))
    for r in rows:r['demand']=str(D(random.randrange(30000))/1000)
    want,queue=ref(c,rows); got,events=run.simulate(c,rows)
    for a,b in zip(want,got):
        for k,v in a.items(): assert b[k]==v
    for cutoff in [1,3,6]:
        altered=copy.deepcopy(rows)
        for r in altered[cutoff:]:r['demand']='999.999'
        assert run.simulate(c,altered)[0][:cutoff]==got[:cutoff]
    report['random_decimal_cases']+=1
for key,values in {'lead_time':[-1,True,1.5,1001,'2'], 'days':[0,True,7.0,1001], 'order_up_to':[-1,'NaN','Infinity','0.0001',1000001,True], 'initial_on_hand':[-1,'-Infinity','0.00001',False]}.items():
    for v in values:
        c,rows=run.load_case('hewei');c[key]=v
        try:run.simulate(c,rows)
        except ValueError:report['invalid_cases']+=1
        else:raise AssertionError((key,v))
for value in ['1.001','2.5']:
    c,rows=run.load_case('apparel'); rows[0]['demand']=value
    try:run.simulate(c,rows)
    except ValueError: report['invalid_cases']+=1
    else:raise AssertionError(value)
# Redraw outside repository, from image ZIP, without practice/data or images present.
with tempfile.TemporaryDirectory(prefix='d15-round2-render-') as tmp:
    t=Path(tmp)
    with zipfile.ZipFile(R/'static/downloads/d15-inventory-position-images.zip') as z:
        for n in z.namelist():
            if n.startswith('figure-tools/'):z.extract(n,t)
    subprocess.run([os.environ.get('D15_RENDER_PYTHON',sys.executable),str(t/'figure-tools/render_figures.py'),'--font-path',os.environ['D15_FONT_PATH']],cwd='/',check=True,stdout=subprocess.DEVNULL)
    matches=[]
    for p in (t/'images').rglob('*.png'):
        n=p.relative_to(t/'images'); assert p.read_bytes()==(R/'experiments/d15-inventory-position/images'/n).read_bytes(); matches.append(str(n))
    for p in (t/'figure-tools').glob('*.svg'):
        assert p.read_bytes()==(R/'experiments/d15-inventory-position/figure-tools'/p.name).read_bytes()
    report['independent_redraw']={'matching_pngs':matches,'matching_svgs':4,'no_practice_needed':True,'cwd':'/'}
files=[R/'content/blog/inventory-position-event-timing/index.md',P/'run.py',P/'test_inventory.py',P/'parameters.json',P/'source_manifest.json']+list((P/'data').glob('*.csv'))+[R/f'scripts/{n}' for n in ['check-d15.py','check-d15-browser.js','package-d15.py']]+list((R/'static/downloads').glob('d15-*.zip'))
report['sha256']={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
(R/'docs/d15-review/round2-results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False,indent=2))
