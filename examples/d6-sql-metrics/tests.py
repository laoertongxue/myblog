"""独立手算断言 + Python 逐事件参考算法 + 输入契约反例。"""
import sys
sys.dont_write_bytecode=True
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
import subprocess,math,csv,os
from run import load,calculate,write_results,ROOT,START,END,ASOF,OUTPUT_FIELDS,FIELDS
D=load(ROOT/'data');R=calculate(D);checks=0

def check(name,ok):
 global checks
 if not ok:raise AssertionError(name)
 checks+=1

def row(table,**keys):return next(r for r in R[table] if all(r[k]==v for k,v in keys.items()))
def triplet(table,keys,n,d,rate):
 r=row(table,**keys)
 check(table+' numerator '+str(keys),r['numerator']==n)
 check(table+' denominator '+str(keys),r['denominator']==d)
 check(table+' ratio '+str(keys),r['ratio']==rate)

triplet('metric_otif',dict(site_id='A01'),1,2,.5)
triplet('metric_otif',dict(site_id='A02'),0,0,None)
triplet('metric_otif',dict(site_id='H01'),1,3,1/3)
triplet('metric_otif',dict(site_id='H02'),1,2,.5)
triplet('metric_fill',dict(sku_id='AS01'),200,200,1.)
triplet('metric_fill',dict(sku_id='AS02'),40,50,.8)
triplet('metric_fill',dict(sku_id='HS01'),20,30,2/3)
triplet('metric_fill',dict(sku_id='HS05'),8,8,1.)
triplet('metric_fill',dict(sku_id='HS06'),0,4,0.)
triplet('metric_fill',dict(sku_id='HS08'),0,0,None)
triplet('metric_stockout',dict(site_id='H01',sku_id='HS01'),2,11,2/11)
s=row('metric_stockout',site_id='H01',sku_id='HS01')
check('snapshot expected14',s['expected_count']==14)
check('missing1',s['missing_count']==1)
check('unknown1',s['unknown_count']==1)
check('negative1',s['negative_count']==1)
check('coverage11/14',s['coverage']==11/14)
check('dedup2',R['audit']['duplicate_receipt_rows_removed']==2)
check('expected448',R['audit']['expected_snapshots']==448)
check('snapshot input446',len(D['snapshots'])==446)
check('cancelled H4 excluded',any(r['order_id']=='HO4' and r['reason']=='cancelled' for r in R['excluded_orders']))
check('notdue H5 excluded',any(r['order_id']=='HO5' and r['reason']=='not_due' for r in R['excluded_orders']))
check('late one second excluded',row('line_result',line_id='HL4')['on_time_qty']==0)
check('deadline exact included',row('line_result',line_id='HL7')['on_time_qty']==8)
check('split line100 not200',row('line_result',line_id='AL1')['on_time_qty']==100)
check('wholeorder AO1 fail',row('order_result',order_id='AO1')['passed']==0)
check('late pants still40',row('line_result',line_id='AL2')['on_time_qty']==40)
check('overdelivery preserved before cap',row('line_result',line_id='AL3')['on_time_qty']==120)
# 独立参考实现：逐订单、逐行、逐事件扫描，完全不执行或复用 SQL。
def oracle_checks(data,results):
 unique={ (x['scenario'],x['event_id']):x for x in data['receipts'] }
 line_oracle={};order_oracle={}
 for o in data['orders']:
  if o['status']!='valid' or not START<=o['due_at']<END or o['due_at']>ASOF:continue
  good=True
  for l in data['lines']:
   if (l['scenario'],l['order_id'])!=(o['scenario'],o['order_id']):continue
   q=sum(r['qualified_qty'] for r in unique.values() if (r['scenario'],r['line_id'])==(l['scenario'],l['line_id']) and r['received_at']<=o['due_at'] and r['received_at']<=ASOF)
   line_oracle[(l['scenario'],l['line_id'])]=(q,l['ordered_qty'],l['sku_id']);good=good and q>=l['ordered_qty']
  order_oracle[(o['scenario'],o['order_id'])]=(int(good),o['site_id'])
 for actual in results['metric_otif']:
  vals=[v[0] for key,v in order_oracle.items() if key[0]==actual['scenario'] and v[1]==actual['site_id']]
  check('independent OTIF '+actual['site_id'],actual['numerator']==sum(vals) and actual['denominator']==len(vals))
 for actual in results['metric_fill']:
  vals=[v for key,v in line_oracle.items() if key[0]==actual['scenario'] and v[2]==actual['sku_id']]
  check('independent fill '+actual['sku_id'],actual['numerator']==sum(min(v[0],v[1]) for v in vals) and actual['denominator']==sum(v[1] for v in vals))
 for actual in results['metric_stockout']:
  vals=[r['on_hand'] for r in data['snapshots'] if r['scenario']==actual['scenario'] and r['site_id']==actual['site_id'] and r['sku_id']==actual['sku_id']]
  valid=[x for x in vals if x is not None and x>=0]
  check('independent snapshot '+actual['site_id']+actual['sku_id'],actual['numerator']==valid.count(0) and actual['denominator']==len(valid))

oracle_checks(D,R)

def rejected(name,mutate):
 d=deepcopy(D);mutate(d)
 try:calculate(d)
 except (ValueError,TypeError):check(name,True)
 else:check(name,False)
rejected('conflicting receipt event',lambda d:d['receipts'].append({**d['receipts'][0],'qualified_qty':999}))
rejected('duplicate line',lambda d:d['lines'].append(d['lines'][0].copy()))
rejected('duplicate snapshot',lambda d:d['snapshots'].append(d['snapshots'][0].copy()))
rejected('orphan receipt',lambda d:d['receipts'][0].update(line_id='NO_SUCH_LINE'))
rejected('orphan order',lambda d:d['orders'][0].update(site_id='NO_SUCH_SITE'))
rejected('orphan SKU',lambda d:d['lines'][0].update(sku_id='NO_SUCH_SKU'))
rejected('negative ordered',lambda d:d['lines'][0].update(ordered_qty=-1))
rejected('zero ordered',lambda d:d['lines'][0].update(ordered_qty=0))
rejected('negative qualified',lambda d:d['receipts'][0].update(qualified_qty=-1))
rejected('NaN quantity',lambda d:d['lines'][0].update(ordered_qty=float('nan')))
rejected('float quantity',lambda d:d['lines'][0].update(ordered_qty=1.5))
rejected('mixed timestamp',lambda d:d['orders'][0].update(due_at='2026-10-20T12:00:00+08:00'))
rejected('impossible timestamp',lambda d:d['orders'][0].update(due_at='2026-02-30 12:00:00'))
rejected('unknown status',lambda d:d['orders'][0].update(status='whatever'))
rejected('empty event',lambda d:d['receipts'][0].update(event_id=''))
rejected('offgrid snapshot',lambda d:d['snapshots'][0].update(snapshot_at='2026-10-16 18:00:01'))
rejected('order without lines',lambda d:d['lines'].__setitem__(slice(None),[r for r in d['lines'] if r['order_id']!='HO1']))
rejected('fullwidth due timestamp',lambda d:d['orders'][0].update(due_at='２０２６-10-20 12:00:00'))
rejected('fullwidth receipt timestamp',lambda d:d['receipts'][0].update(received_at='２０２６-10-19 12:00:00'))
# 从真实CSV经CLI重放，验证字符外观相似不能绕过输入契约且失败不留下结果。
for table,column,value in [('orders','due_at','２０２６-10-20 12:00:00'),('receipts','received_at','２０２６-10-19 12:00:00')]:
 with TemporaryDirectory() as t:
  folder=Path(t)/'data';folder.mkdir();bad=deepcopy(D);bad[table][0][column]=value
  for name,rows in bad.items():
   with (folder/(name+'.csv')).open('w',encoding='utf-8',newline='') as f:
    w=csv.DictWriter(f,fieldnames=FIELDS[name]);w.writeheader();w.writerows(rows)
  out=Path(t)/'output'
  proc=subprocess.run([sys.executable,str(ROOT/'run.py'),'--data',str(folder),'--out',str(out)],capture_output=True)
  check('CSV fullwidth rejected '+table,proc.returncode!=0)
  check('CSV failure no result '+table,not out.exists())
with TemporaryDirectory() as t:
 folder=Path(t);bad=deepcopy(D);bad['lines'][0]['ordered_qty']='１０'
 for name,rows in bad.items():
  with (folder/(name+'.csv')).open('w',encoding='utf-8',newline='') as f:
   w=csv.DictWriter(f,fieldnames=FIELDS[name]);w.writeheader();w.writerows(rows)
 try:load(folder)
 except ValueError:check('fullwidth quantity rejected',True)
 else:check('fullwidth quantity rejected',False)
# 改变事件行顺序，不应改变所有计算输出。
d=deepcopy(D);d['receipts'].reverse();check('receipt order invariant',calculate(d)==R)
# 新身份合法分批必须保留：将一次6拆成2+4，删除原事件重复，两条新事件相加仍为6。
d=deepcopy(D);d['receipts']=[r for r in d['receipts'] if r['event_id']!='HE1']
base=next(r for r in D['receipts'] if r['event_id']=='HE1')
d['receipts'] += [{**base,'event_id':'HE1a','qualified_qty':2},{**base,'event_id':'HE1b','qualified_qty':4}]
check('new split identity retained',calculate(d)['metric_fill']==R['metric_fill'])
# 全部快照缺失：保留预期网格，分母0，结果NULL，覆盖率0。
d=deepcopy(D);d['snapshots']=[];z=calculate(d)['metric_stockout']
check('all snapshot missing null',all(r['ratio'] is None and r['coverage']==0 and r['missing_count']==14 for r in z))
# 起点包含；终点不包含；同一订单只存在一个共同承诺时间。
d=deepcopy(D);d['orders'][0]['due_at']=START
check('inclusive start',any(x['order_id']=='HO1' for x in calculate(d)['order_result']))
d=deepcopy(D);d['orders'][0]['due_at']=END
check('exclusive end',not any(x['order_id']=='HO1' for x in calculate(d)['order_result']))
# 仅改变一个变量：截止时刻与晚一秒必须产生不同达标结论。
d=deepcopy(D)
for r in d['receipts']:
 if r['event_id']=='HE7':r['received_at']='2026-10-24 12:00:01'
changed=calculate(d)
check('deadline plus1 changes line',next(r for r in changed['line_result'] if r['line_id']=='HL7')['passed']==0)
check('deadline plus1 changes store OTIF',next(r for r in changed['metric_otif'] if r['site_id']=='H02')['numerator']==0)
d=deepcopy(D)
for r in d['receipts']:
 if r['event_id']=='AE4':r['qualified_qty']=999
check('extra overdelivery invariant',calculate(d)['metric_fill']==R['metric_fill'])
check('line credited cap',row('line_result',line_id='AL3')['credited_qty']==100)
check('line pass flag',row('line_result',line_id='AL3')['passed']==1)

# 队列按承诺时间选取，观察期之前的合法验收仍可满足期内承诺。
d=deepcopy(D)
for r in d['receipts']:
 if r['event_id']=='HE1':r['received_at']='2026-10-15 12:00:00'
check('prewindow receipt counts for due cohort',calculate(d)['metric_fill']==R['metric_fill'])
# 两案例故意使用相同单号/行号/事件号/地点/SKU，证明场景键不是依靠前缀隔离。
def without_prefix(data):
 for rows in data.values():
  for r in rows:
   for k in ['site_id','sku_id','order_id','line_id','event_id']:
    if k in r:r[k]=r[k][1:]
 return data
collision_data=without_prefix(deepcopy(D));collision_result=calculate(collision_data)
oracle_checks(collision_data,collision_result)
for name in ['metric_otif','metric_fill','metric_stockout']:
 normalized=without_prefix({name:deepcopy(R[name])})[name]
 check('cross scenario collision invariant '+name,collision_result[name]==normalized)

with TemporaryDirectory() as t:
 out=Path(t)/'results';write_results(R,out)
 before={p.name:p.read_bytes() for p in out.iterdir()}
 try:write_results(R,out)
 except FileExistsError:check('no overwrite',True)
 else:check('no overwrite',False)
 check('existing results unchanged',before=={p.name:p.read_bytes() for p in out.iterdir()})
with TemporaryDirectory() as t:
 # 即使某类结果零行，也要输出稳定表头，避免下游误把空文件当格式损坏。
 empty={name:[] for name in OUTPUT_FIELDS};empty['audit']={}
 out=Path(t)/'empty';write_results(empty,out)
 for name,fields in OUTPUT_FIELDS.items():
  with (out/(name+'.csv')).open(encoding='utf-8',newline='') as f:
   check('empty CSV header '+name,list(csv.reader(f))==[fields])
with TemporaryDirectory() as t:
 out=Path(t)/'ascii-output'
 proc=subprocess.run([sys.executable,str(ROOT/'run.py'),'--out',str(out)],capture_output=True,env={**os.environ,'LC_ALL':'C','PYTHONUTF8':'0'})
 check('full CLI succeeds in ASCII locale',proc.returncode==0)
 check('full CLI preserves UTF8 CSV', (out/'metric_otif.csv').read_text(encoding='utf-8')==(ROOT/'expected'/'metric_otif.csv').read_text(encoding='utf-8'))
print(f'PASS: {checks} assertions (manual expectations, independent oracle, boundary and contract tests)')
