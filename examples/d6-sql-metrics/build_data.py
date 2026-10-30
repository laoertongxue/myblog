"""生成完全模拟、可复现的 14 天教学数据，不连接任何生产系统。"""
from pathlib import Path
import csv
from datetime import date,timedelta
ROOT=Path(__file__).resolve().parent
FIELDS={'sites':['scenario','site_id','site_name'],'skus':['scenario','sku_id','sku_name','unit'],'orders':['scenario','order_id','site_id','due_at','status'],'lines':['scenario','line_id','order_id','sku_id','ordered_qty'],'receipts':['scenario','event_id','line_id','received_at','qualified_qty'],'snapshots':['scenario','site_id','sku_id','snapshot_at','on_hand']}
def build():
 d={k:[] for k in FIELDS}
 for case,prefix,scale in [('禾味','H',1),('匿名服装企业','A',10)]:
  for s in ['01','02']: d['sites'].append([case,prefix+s,('门店' if prefix=='H' else '接收点')+s])
  names=['大米','鸡肉','番茄','鸡蛋','土豆','牛奶','食用油','面粉'] if prefix=='H' else ['TEE-M上衣M','PANT-M裤子M','长裤S','长裤M','外套S','外套M','裙装S','裙装M']
  for i,n in enumerate(names,1): d['skus'].append([case,prefix+f'S{i:02}',n,({4:'个',6:'升',7:'升'}.get(i,'kg')) if prefix=='H' else '件'])
  for i,site,status,due in [(1,'01','valid','2026-10-20 12:00:00'),(2,'01','valid','2026-10-21 12:00:00'),(3,'01','valid','2026-10-22 12:00:00'),(4,'01','cancelled','2026-10-23 12:00:00'),(5,'02','valid','2026-10-31 12:00:00'),(6,'02','valid','2026-10-24 12:00:00'),(7,'02','valid','2026-10-25 12:00:00')]: d['orders'].append([case,prefix+f'O{i}',prefix+site,due,status])
  specs=[(1,1,1,10),(2,1,2,5),(3,2,1,10),(4,3,1,10),(5,4,3,5),(6,5,4,5),(7,6,5,8),(8,7,6,4)]
  for lid,oid,sku,q in specs:d['lines'].append([case,prefix+f'L{lid}',prefix+f'O{oid}',prefix+f'S{sku:02}',q*scale])
  rs=[(1,1,'2026-10-19 12:00:00',6),(2,1,'2026-10-20 12:00:00',4),(3,2,'2026-10-20 11:00:00',4),(4,3,'2026-10-21 12:00:00',12),(5,4,'2026-10-22 12:00:01',10),(6,5,'2026-10-23 12:00:00',5),(7,7,'2026-10-24 12:00:00',8),(8,8,'2026-10-25 11:00:00',0)]
  for eid,lid,t,q in rs:d['receipts'].append([case,prefix+f'E{eid}',prefix+f'L{lid}',t,q*scale])
  d['receipts'].append(d['receipts'][-8].copy()) # 相同事件重传，按身份去重，不是删除合法分批
  if prefix=='A':
   d['orders']=[r for r in d['orders'] if r[0]!=case or r[1] in ['AO1','AO2']]
   d['lines']=[r for r in d['lines'] if r[0]!=case or r[1] in ['AL1','AL2','AL3']]
   d['receipts']=[r for r in d['receipts'] if r[0]!=case or r[2] in ['AL1','AL2','AL3']]
   d['receipts'].append([case,'AE9','AL2','2026-10-20 12:00:01',10])
  for s in ['01','02']:
   for i in range(1,9):
    for day in range(14):
     t=str(date(2026,10,16)+timedelta(days=day))+' 18:00:00'
     if s=='01' and i==1 and day==2:continue # 缺一条，不补零
     q=10*scale
     if s=='01' and i==1:
      if day in [0,1]:q=0
      elif day==3:q=-1
      elif day==4:q=''
     if s=='02' and i==2 and day==13:q=0
     d['snapshots'].append([case,prefix+s,prefix+f'S{i:02}',t,q])
 return d
if __name__=='__main__':
 target=ROOT/'data';target.mkdir(exist_ok=True)
 for table,rows in build().items():
  with (target/(table+'.csv')).open('w',encoding='utf-8',newline='') as f:
   w=csv.writer(f);w.writerow(FIELDS[table]);w.writerows(rows)
 print('Generated six simulated tables: 2 scenarios, each with 14 days, 2 sites and 8 SKUs.')
