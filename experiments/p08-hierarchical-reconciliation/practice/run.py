"""Finite, synthetic forecast-reconciliation teaching fixture. Python >=3.10 stdlib."""
import argparse,csv,json,math
from pathlib import Path
from collections import defaultdict

def number(x,name='number'):
    v=float(x)
    if not math.isfinite(v) or v<0: raise ValueError(f'{name} must be finite and nonnegative')
    return v

def reconcile(values,total,method='fixed',weight=.6,integer=False):
    if not values: raise ValueError('empty leaves')
    clean={str(k):number(v) for k,v in values.items()}
    if len(clean)!=len(values): raise ValueError('ambiguous leaf IDs')
    total=number(total,'total');weight=number(weight,'weight')
    if weight>1: raise ValueError('weight > 1')
    if method not in ('bottom_up','fixed','mixed'): raise ValueError('unknown method')
    s=number(sum(clean.values()),'leaf sum');target=number(s if method=='bottom_up' else total if method=='fixed' else weight*total+(1-weight)*s,'coordinated target')
    if integer and abs(target-round(target))>1e-9: raise ValueError('integer target required; choose explicit total-rounding policy first')
    if not s:
        if target: raise ValueError('positive target with zero leaf sum; supply shares explicitly')
        return {k:0 for k in sorted(clean)},target
    raw={k:number(target*(v/s),'reconciled leaf') for k,v in clean.items()}
    if not integer: return dict(sorted(raw.items())),target
    out={k:math.floor(v+1e-12) for k,v in raw.items()};left=round(target)-sum(out.values())
    for k in sorted(raw,key=lambda k:(-round(raw[k]-out[k],12),k))[:left]:out[k]+=1
    return dict(sorted(out.items())),target

def gross(net,yield_rate):
    net=number(net);y=number(yield_rate)
    if y<=0 or y>1: raise ValueError('yield must be in (0,1]')
    return number(net/y,'gross requirement')

def write(path,rows):
    rows=list(rows);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def generate(dest):
    dest=Path(dest)
    if dest.exists() and any(dest.iterdir()): raise FileExistsError('refuse to overwrite nonempty input directory')
    dest.mkdir(parents=True,exist_ok=True)
    leaves=[];groups=[]
    # All values below are constructed, not fitted. Actual=base is a deliberate counterexample.
    for color in ('black','white'):
      for size in ('S','M','L'):
        sku=f'apparel_{color}_{size}'
        groups.append(dict(case='apparel',day=1,sku=sku,total=100,weight=.6,unit='piece',yield_rate=1))
        for leaf,base,cap in [('north',60,50),('south',50,60)]:
          leaves.append(dict(case='apparel',day=1,sku=sku,leaf=leaf,base=base,actual=base,stock=0,capacity=cap))
    names=['milk','coconut_milk','coffee','tea','syrup','lemon','pearls','oat_milk']
    for day in range(1,15):
      for i,sku in enumerate(names):
        scale=1+i/4;factor=1+((day-1)%4)/10
        a=18*scale*factor;b=14*scale*factor
        groups.append(dict(case='hewei',day=day,sku=sku,total=30*scale*factor,weight=.6,unit='kg',yield_rate=.8 if sku=='lemon' else 1))
        for leaf,base,cap in [('store_A',a,16*scale*factor),('store_B',b,20*scale*factor)]:
          leaves.append(dict(case='hewei',day=day,sku=sku,leaf=leaf,base=round(base,8),actual=round(base,8),stock=0,capacity=round(cap,8)))
    write(dest/'leaves.csv',leaves);write(dest/'groups.csv',groups)

def read(path):
    with Path(path).open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))

def expected_grid():
    """This fixed teaching fixture has a deliberate, closed schema, not arbitrary enterprise IDs."""
    grid={}
    for color in ('black','white'):
      for size in ('S','M','L'):
        grid[('apparel',1,f'apparel_{color}_{size}')]=('piece',{'north','south'})
    for day in range(1,15):
      for sku in ('milk','coconut_milk','coffee','tea','syrup','lemon','pearls','oat_milk'):
        grid[('hewei',day,sku)]=('kg',{'store_A','store_B'})
    return grid

def accuracy_counterexamples():
    base={'north':60,'south':50};rows=[]
    for scenario,actual in [('bottom_up_exact',{'north':60,'south':50}),('fixed_exact',{'north':55,'south':45})]:
      for method in ('bottom_up','fixed','mixed'):
        forecast,total=reconcile(base,100,method,integer=True)
        errors=[abs(forecast[k]-actual[k]) for k in sorted(actual)]
        rows.append(dict(scenario=scenario,method=method,unit='piece',actual_north=actual['north'],actual_south=actual['south'],forecast_north=forecast['north'],forecast_south=forecast['south'],leaf_absolute_error_sum=sum(errors),leaf_MAE=sum(errors)/2))
    return rows

def calculate(data,out):
    data=Path(data);out=Path(out)
    if out.resolve()==data.resolve() or data.resolve() in out.resolve().parents:raise ValueError('output must not be inside input directory')
    groups={};leaves=defaultdict(dict)
    for r in read(data/'groups.csv'):
      key=(r['case'],int(r['day']),r['sku'])
      if key in groups:raise ValueError('duplicate group key')
      if r['unit'] not in ('piece','kg'):raise ValueError('unknown unit')
      number(r['total']);gross(1,r['yield_rate']);groups[key]=r
    for r in read(data/'leaves.csv'):
      key=(r['case'],int(r['day']),r['sku']);leaf=r['leaf']
      if key not in groups:raise ValueError('orphan leaf')
      if leaf in leaves[key]:raise ValueError('duplicate leaf key')
      for col in ('base','actual','stock','capacity'):r[col]=number(r[col],col)
      leaves[key][leaf]=r
    if set(groups)!=set(leaves):raise ValueError('missing leaves')
    grid=expected_grid()
    if set(groups)!=set(grid):raise ValueError('fixture requires exact apparel and hewei case/day/SKU grid')
    for key,(unit,leaf_ids) in grid.items():
      if groups[key]['unit']!=unit:raise ValueError('unit contradicts case/SKU contract')
      if set(leaves[key])!=leaf_ids:raise ValueError('leaf IDs contradict case contract')
    details=[];summary=[]
    for key,g in sorted(groups.items()):
      raw=leaves[key]
      if len(raw)!=2:raise ValueError('fixture requires two leaves per group')
      for method in ('bottom_up','fixed','mixed'):
        values,target=reconcile({k:r['base'] for k,r in raw.items()},g['total'],method,float(g['weight']),g['unit']=='piece')
        error=0;gap=0
        for leaf,value in values.items():
          r=raw[leaf];net=max(0,value-r['stock']);raw_requirement=gross(net,g['yield_rate'])
          # capacity is net-item availability for this single period, not a forecasting bound.
          supply=min(net,r['capacity']);shortage=net-supply;error+=abs(value-r['actual']);gap+=shortage
          details.append(dict(case=key[0],day=key[1],sku=key[2],method=method,leaf=leaf,unit=g['unit'],base=r['base'],reconciled=value,adjustment=value-r['base'],actual=r['actual'],absolute_error=abs(value-r['actual']),net_requirement=net,gross_requirement=raw_requirement,net_supply=supply,uncovered_net=shortage))
        summary.append(dict(case=key[0],day=key[1],sku=key[2],method=method,unit=g['unit'],target=target,leaf_sum=sum(values.values()),coherence_error=abs(target-sum(values.values())),actual_total=sum(r['actual'] for r in raw.values()),leaf_absolute_error_sum=error,uncovered_net=gap))
    write(out/'reconciled.csv',details);write(out/'group_checks.csv',summary)
    write(out/'accuracy_counterexamples.csv',accuracy_counterexamples())
    metadata={'scope':'constructed point-forecast reconciliation; no model fitting or blind test','groups':len(groups),'input_leaves':sum(map(len,leaves.values())),'output_rows':len(details),'summary_rows':len(summary),'warning':'Do not aggregate kg errors across different ingredient SKUs; no procurement executed.'}
    (out/'metadata.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2),encoding='utf-8')
    return details,summary

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--generate',type=Path);p.add_argument('--data',type=Path,default=Path(__file__).parent/'data');p.add_argument('--out',type=Path,default=Path(__file__).parent/'outputs');a=p.parse_args()
 if a.generate:generate(a.generate)
 else:
  d,s=calculate(a.data,a.out);print(f'{len(d)} detail rows, {len(s)} group checks')
