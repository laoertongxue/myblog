"""Cold-start teaching experiment. Standard library only; all numbers simulated."""
import csv,json,math,hashlib
from pathlib import Path
from datetime import date,timedelta
ROOT=Path(__file__).resolve().parent
GRID=[0,.25,.5,.75,1]
def nonnegative(x):
    if isinstance(x,bool) or not isinstance(x,(int,float)) or not math.isfinite(x) or x<0: raise ValueError('finite nonnegative number required')
    return x
def blend(analog,recent,w):
    nonnegative(analog);nonnegative(recent);nonnegative(w)
    if w>1: raise ValueError('weight out of bounds')
    return (1-w)*analog+w*recent
def analog(refs,target,week,asof):
    if week not in (1,2):raise ValueError('week')
    cutoff=date.fromisoformat(asof); launch=date.fromisoformat(target['launch'])
    if cutoff<launch:raise ValueError('forecast origin before launch')
    eligible=[]
    for r in refs:
        # Frozen reference cohort only, matched attributes; entire target-age window known.
        if r['id']==target['id'] or r['split']!='reference' or not r['fully_observed']: continue
        known=date.fromisoformat(r['launch'])+timedelta(days=week*7)
        if known>cutoff:continue
        if (r['family'],r['band'],r['coverage'])!=(target['family'],target['band'],target['coverage']):continue
        eligible.append(r)
    if not eligible:raise ValueError('no eligible analogy; manual review required')
    vals=[nonnegative(r[f'w{week}']) for r in eligible]
    return sum(vals)/len(vals),[r['id'] for r in eligible]
def recent_feature(target,asof):
    if date.fromisoformat(asof)<date.fromisoformat(target['launch'])+timedelta(days=7):raise ValueError('week 1 not observed')
    if not target['fully_observed']:raise ValueError('censored observation; manual review required')
    return nonnegative(target['w1'])
def select_weight(refs,validation):
    if not validation or any(t['split']!='validation' for t in validation):raise ValueError('validation only')
    scores=[]
    for w in GRID:
        errors=[]
        for t in validation:
            asof=(date.fromisoformat(t['launch'])+timedelta(days=7)).isoformat()
            a,_=analog(refs,t,2,asof);r=recent_feature(t,asof)
            errors.append(abs(blend(a,r,w)-nonnegative(t['w2'])))
        scores.append({'weight':w,'mae':sum(errors)/len(errors)})
    # Fixed before test; ties choose lower reliance on recent observation.
    return min(scores,key=lambda x:(x['mae'],x['weight']))['weight'],scores
def validate_case(case):
    rows=case['products'];ids=[r['id'] for r in rows]
    if len(ids)!=len(set(ids)):raise ValueError('duplicate product')
    for r in rows:
        if r['split'] not in ('reference','validation','test'):raise ValueError('split')
        date.fromisoformat(r['launch']);nonnegative(r['w1']);nonnegative(r['w2'])
        if type(r['fully_observed']) is not bool:raise ValueError('observability')
    ref=[r for r in rows if r['split']=='reference'];val=[r for r in rows if r['split']=='validation'];test=[r for r in rows if r['split']=='test']
    if not ref or not val or not test:raise ValueError('missing split')
    if max(date.fromisoformat(r['launch'])+timedelta(days=14) for r in val)>min(date.fromisoformat(r['launch']) for r in test):raise ValueError('validation not mature before test')
    return ref,val,test
def run_case(case):
    ref,val,test=validate_case(case);w,scores=select_weight(ref,val);result=[]
    for t in test:
        a1,ids1=analog(ref,t,1,t['launch']);asof=(date.fromisoformat(t['launch'])+timedelta(days=7)).isoformat()
        a2,ids2=analog(ref,t,2,asof);r=recent_feature(t,asof)
        result.append({'id':t['id'],'launch':t['launch'],'origin_w2':asof,'analog_ids':ids2,'zero_history_w1':a1,'actual_w1':t['w1'],'analog_w2':a2,'recent_w2':r,'weight':w,'mixed_w2':blend(a2,r,w),'actual_w2':t['w2']})
    metrics={m:sum(abs(r[m]-r['actual_w2']) for r in result)/len(result) for m in ('analog_w2','recent_w2','mixed_w2')}
    return {'case':case['name'],'unit':case['unit'],'weight':w,'validation_scores':scores,'test':result,'test_mae_week2':metrics}
def scenario(new_units,old_units,substitution,new_recipe,old_recipe):
    for x in (new_units,old_units,substitution,new_recipe,old_recipe):nonnegative(x)
    if substitution>1 or new_units*substitution>old_units:raise ValueError('invalid substitution scenario')
    retained=old_units-new_units*substitution
    return {'new_units':new_units,'retained_old_units':retained,'ingredient_total_kg':new_units*new_recipe+retained*old_recipe}
def main():
    raw=(ROOT/'data/cases.json').read_bytes();cases=json.loads(raw)
    out={'simulated':True,'input_sha256':hashlib.sha256(raw).hexdigest(),'protocol':'two weekly age windows; frozen reference cohort; validate weight then test new IDs','cases':[run_case(c) for c in cases], 'hewei_scenarios':[dict(substitution=s,**scenario(70,100,s,.15,.12)) for s in (0,.4,.8)]}
    (ROOT/'outputs').mkdir(exist_ok=True)
    (ROOT/'outputs/results.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    with (ROOT/'outputs/predictions.csv').open('w',newline='') as f:
        fields=['case','unit','id','launch','origin_w2','zero_history_w1','actual_w1','analog_w2','recent_w2','weight','mixed_w2','actual_w2'];w=csv.DictWriter(f,fields);w.writeheader()
        for c in out['cases']:
            for r in c['test']:w.writerow({k:({'case':c['case'],'unit':c['unit']}|r)[k] for k in fields})
    print(json.dumps(out,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
