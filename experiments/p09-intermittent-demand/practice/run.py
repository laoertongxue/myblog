"""Original deterministic teaching experiment; Python 3.10+, standard library only."""
import csv,json,math,statistics,hashlib
from pathlib import Path
ROOT=Path(__file__).parent
METHODS=['zero','mean','croston','sba','tsb']
def valid(y):
 if not y or any(isinstance(v,bool) or not isinstance(v,(float,int)) or not math.isfinite(v) or v<0 for v in y): raise ValueError('nonempty finite nonnegative demand required')
def describe(y):
 valid(y); z=[x for x in y if x>0]
 return {'n':len(y),'events':len(z),'adi':len(y)/len(z) if z else None,'cv2':statistics.variance(z)/statistics.mean(z)**2 if len(z)>1 else None}
def forecast(y,method,alpha=.1):
 valid(y)
 if method not in METHODS:raise ValueError('method')
 if not 0<alpha<=1:raise ValueError('alpha')
 if method=='zero':return 0.
 if method=='mean':return sum(y)/len(y)
 # Initialization is first event; leading zeros count in its interval.
 first=next((i for i,v in enumerate(y) if v>0),None)
 if first is None:return 0.
 z=y[first]; a=first+1.; p=1/a; last=first
 for i in range(first+1,len(y)):
  hit=y[i]>0
  p=alpha*int(hit)+(1-alpha)*p
  if hit:
   z=alpha*y[i]+(1-alpha)*z
   a=alpha*(i-last)+(1-alpha)*a;last=i
 if method=='tsb':return p*z
 return z/a*(1-alpha/2 if method=='sba' else 1)
def generate():
 # Fixed synthetic scenarios, not parameter-fitted to outcomes.
 apparel=[(80+20*((d//11)%4)) if d%11 in (3,) or (d<140 and d%29==7) else 0 for d in range(180)]
 food=[(2+((d//7)%4)) if d%7==2 and (d<145 or d%14==2) else 0 for d in range(180)]
 return {'apparel':apparel,'hewei':food}
def evaluate(y,start,end,method,alpha):
 valid(y)
 if not(1<=start<end<=len(y)):raise ValueError('split')
 rows=[]
 for o in range(start,end-4,5):
  rate=forecast(y[:o],method,alpha); actual=y[o:o+5]; total=sum(actual)
  rows.append({'origin':o,'target_start':o+1,'target_end':o+5,'forecast_5':5*rate,'actual_5':total,'abs_error_5':abs(5*rate-total),'bias_5':5*rate-total,'daily_abs_sum':sum(abs(rate-v) for v in actual)})
 if not rows:raise ValueError('no full windows')
 return {'window_mae':sum(r['abs_error_5'] for r in rows)/len(rows),'bias':sum(r['bias_5'] for r in rows)/len(rows),'daily_mae':sum(r['daily_abs_sum'] for r in rows)/(5*len(rows)),'n_windows':len(rows)},rows
def experiment(data):
 out={}; predictions=[]
 for case,y in data.items():
  if len(y)!=180:raise ValueError('180 days required')
  scores=[]
  for m in METHODS:
   for a in ([.1,.3] if m in ['croston','sba','tsb'] else [.1]):
    score,vr=evaluate(y,112,140,m,a);scores.append({'method':m,'alpha':a,**score})
    predictions += [{'case':case,'method':m,'alpha':a,'split':'validation',**r} for r in vr]
  winner=min(scores,key=lambda s:(s['window_mae'],METHODS.index(s['method']),s['alpha']))
  test=[]
  for m in METHODS:
   selected=min([s for s in scores if s['method']==m],key=lambda s:(s['window_mae'],s['alpha']))
   score,rows=evaluate(y,140,180,m,selected['alpha'])
   test.append({'method':m,'alpha':selected['alpha'],**score})
   predictions += [{'case':case,'method':m,'alpha':selected['alpha'],'split':'test',**r} for r in rows]
  out[case]={'unit':'件' if case=='apparel' else 'kg','train_description':describe(y[:112]),'validation':scores,'frozen_selection':{'method':winner['method'],'alpha':winner['alpha']},'test':test,'data_sha256':hashlib.sha256(json.dumps(y).encode()).hexdigest()}
 return out,predictions
def write():
 data=generate(); result,rows=experiment(data)
 (ROOT/'data.json').write_text(json.dumps(data,indent=2))
 (ROOT/'frozen-selection.json').write_text(json.dumps({k:v['frozen_selection'] for k,v in result.items()},indent=2))
 (ROOT/'results.json').write_text(json.dumps(result,indent=2,ensure_ascii=False))
 with (ROOT/'predictions.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':write()
