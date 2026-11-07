"""Reviewer-only decimal oracle; never opens original test labels or sealed paths."""
from pathlib import Path
from decimal import Decimal as D, getcontext
import csv, json, hashlib, zipfile, tempfile, subprocess, sys, copy
getcontext().prec=65
ROOT=Path(__file__).resolve().parents[2]
P=ROOT/'experiments/d14-model-selection/practice'
REPORT=Path(__file__).with_name('round1-results.json')
checks=[]
def check(v, label):
    assert v,label
    checks.append(label)
def table(p):
    with p.open() as f:return list(csv.DictReader(f))
def close(a,b):return abs(float(a)-float(b))<1e-9
expected={}
for case in ['hewei','apparel']:
    raw=table(P/'data'/f'{case}-development.csv')
    check(len(raw)==140 and [int(r['day']) for r in raw]==list(range(1,141)),case+' 140 ordered days')
    check([r['split'] for r in raw]==['train']*112+['validation']*28,case+' 112/28 split')
    y=[D(r['demand']) for r in raw]
    for label in ['SNaive7','MA3','MA7','MA14','SES0.2','SES0.5','SES0.8']:
        for horizon in [1,5]:
            errors=[]; actuals=[]; preds=[]
            for o in range(112,141-horizon):
                if label.startswith('SES'):
                    alpha=D(label[3:]);level=y[0]
                    for v in y[1:o]:level+=(v-level)*alpha
                vector=[]
                for step in range(1,horizon+1):
                    if label=='SNaive7':v=y[o+step-8]
                    elif label.startswith('MA'):
                        k=int(label[2:]);v=sum(y[o-k:o])/D(k)
                    else:v=level
                    vector.append(v)
                    expected[(case,label,horizon,o,step)]=v
                a=sum(y[o:o+horizon]);p=sum(vector)
                actuals.append(a);preds.append(p);errors.append(a-p)
            n=D(len(errors));absolute=sum(abs(e) for e in errors)
            stats={'n':n,'me':sum(errors)/n,'mae':absolute/n,'rmse':(sum(e*e for e in errors)/n).sqrt(),'wape':absolute/sum(actuals),'actual_sum':sum(actuals),'absolute_error_sum':absolute}
            row=next(r for r in table(P/'results/metrics.csv') if r['case']==case and r['method']==label and int(r['task_horizon'])==horizon)
            check(all(close(row[k],v) for k,v in stats.items()),f'decimal metrics {case} {label} h={horizon}')
for r in table(P/'results/predictions.csv'):
    key=(r['case'],r['method'],int(r['task_horizon']),int(r['origin_day']),int(r['h']))
    check(close(r['prediction'],expected.pop(key)),f'prediction {key}')
    check(int(r['target_day'])==int(r['origin_day'])+int(r['h'])<=140,'target within validation')
check(not expected,'all 2072 independent forecasts present')
# Targeted black-box input attacks use production code only for actual outcome.
sys.path.insert(0,str(P));sys.dont_write_bytecode=True
import baseline, run
rows=baseline.load_csv(P/'data/hewei-development.csv','hewei/A/SKU01')
for value in [None,True,-1,float('nan'),float('inf'),'2']:
    changed=copy.deepcopy(rows);changed[80]['demand']=value
    try:baseline.forecast_at(changed,112,5)
    except ValueError:pass
    else:raise AssertionError(f'accepted invalid observed demand {value}')
check(True,'six invalid observed demand attacks rejected')
for label,args in run.METHODS:
    for origin in [112,117,135,139]:
        h=1 if origin==139 else 5
        reference=run.issue(rows,origin,h,'hewei',label,args)
        poison=copy.deepcopy(rows[:origin])+[{'date':'BAD','demand':float('nan'),'series':'alien'}]*(140-origin)
        check(reference==run.issue(poison,origin,h,'hewei',label,args),f'poisoned future unchanged {label} {origin}')
archives={}
for zpath in sorted((ROOT/'static/downloads').glob('d14*.zip')):
    with zipfile.ZipFile(zpath) as z:
        names=z.namelist();check(len(names)==len(set(names)),'unique members '+zpath.name)
        check(all(not Path(n).is_absolute() and '..' not in Path(n).parts and 'sealed' not in Path(n).parts for n in names),'safe members '+zpath.name)
        entries=z.read('MANIFEST.sha256').decode().splitlines()
        for line in entries:
            digest,name=line.split('  ',1)
            check(hashlib.sha256(z.read(name)).hexdigest()==digest,'manifest '+name)
        if zpath.name.endswith('practice.zip'):
            with tempfile.TemporaryDirectory() as td:
                z.extractall(td)
                before={n:Path(td,n).read_bytes() for n in names}
                tests=subprocess.run([sys.executable,'-B','-m','unittest','-v'],cwd=td,capture_output=True,text=True)
                check(tests.returncode==0,'clean ZIP unittest')
                rerun=subprocess.run([sys.executable,'-B',str(Path(td,'run.py'))],cwd='/tmp',capture_output=True,text=True)
                check(rerun.returncode==0,'clean ZIP replay from foreign cwd')
                check(all(Path(td,n).read_bytes()==v for n,v in before.items()),'clean replay byte identity')
                Path(__file__).with_name('round1-clean-tests.txt').write_text(tests.stdout+tests.stderr+rerun.stdout+rerun.stderr)
        # Check delivered bytes are current, then redraw images outside the repo.
        target=(P if zpath.name.endswith('practice.zip') else ROOT/'content/blog/forecast-model-selection-boundaries' if zpath.name.endswith('article.zip') else P.parent)
        check(all(z.read(n)==(target/n).read_bytes() for n in names if n!='MANIFEST.sha256'),'ZIP matches current source '+zpath.name)
        if zpath.name.endswith('images.zip'):
            font=Path('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
            check(font.is_file(),'review environment has required font')
            with tempfile.TemporaryDirectory() as td:
                z.extractall(td)
                rendered=subprocess.run([sys.executable,str(Path(td)/'figure-tools/render_figures.py'),'--font-path',str(font),'--font-index','2'],cwd='/tmp',capture_output=True,text=True)
                check(rendered.returncode==0,'isolated image ZIP redraw')
                for file in ['d14-00_cover.png','d14-01_ranking-boundaries.png','d14-02_selection-cards.png']:
                    check(Path(td,'images',file).read_bytes()==(target/'images'/file).read_bytes(),'PNG redraw identical '+file)
                check(not Path(td,'content').exists() and not Path(td,'assets').exists(),'portable redraw creates no repository directories')
                Path(__file__).with_name('round1-render.txt').write_text(rendered.stdout+rendered.stderr)
        archives[zpath.name]={'sha256':hashlib.sha256(zpath.read_bytes()).hexdigest(),'members':len(names)}
REPORT.write_text(json.dumps({'status':'PASS','checks':len(checks),'oracle':'65 digit Decimal; independently generated 2072 predictions and 28 metric rows','archives':archives},indent=2)+'\n')
print(REPORT.read_text())
