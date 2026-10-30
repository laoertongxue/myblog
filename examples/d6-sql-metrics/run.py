"""Python 3.10+，只用标准库。拒绝覆盖既有结果目录。"""
from pathlib import Path
import argparse,csv,json,sqlite3,hashlib,re,math,platform,sys
from datetime import datetime,date,timedelta
ROOT=Path(__file__).resolve().parent
START='2026-10-16 00:00:00'; END='2026-10-30 00:00:00'; ASOF=END
FIELDS={'sites':['scenario','site_id','site_name'],'skus':['scenario','sku_id','sku_name','unit'],'orders':['scenario','order_id','site_id','due_at','status'],'lines':['scenario','line_id','order_id','sku_id','ordered_qty'],'receipts':['scenario','event_id','line_id','received_at','qualified_qty'],'snapshots':['scenario','site_id','sku_id','snapshot_at','on_hand']}
KEYS={'sites':['scenario','site_id'],'skus':['scenario','sku_id'],'orders':['scenario','order_id'],'lines':['scenario','line_id'],'receipts':['scenario','event_id'],'snapshots':['scenario','site_id','sku_id','snapshot_at']}
def timestamp(v):
 if not isinstance(v,str) or not re.fullmatch(r'[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}',v):raise ValueError('时间格式错误')
 datetime.strptime(v,'%Y-%m-%d %H:%M:%S')
def load(folder):
 data={}
 for t,fields in FIELDS.items():
  with (Path(folder)/(t+'.csv')).open(encoding='utf-8',newline='') as f:
   reader=csv.DictReader(f)
   if reader.fieldnames!=fields:raise ValueError(t+' 字段契约不符')
   rows=list(reader)
  for r in rows:
   if None in r or any(v is None for v in r.values()):raise ValueError(t+' 列数错误')
   for k in ['ordered_qty','qualified_qty','on_hand']:
    if k in r:
     v=r[k]
     if k=='on_hand' and v=='':r[k]=None
     elif re.fullmatch(r'-?[0-9]+',v):r[k]=int(v)
     else:raise ValueError(t+' 数量须为整数；未知库存留空')
  data[t]=rows
 return data

def calculate(data):
 # 输入契约：数量用整数基本单位，时间为统一上海本地时间；不接收混合单位/时区。
 for t,rows in data.items():
  seen={}
  for r in rows:
   if set(r)!=set(FIELDS[t]):raise ValueError(t+' 字段契约不符')
   for k,v in r.items():
    if k not in ['ordered_qty','qualified_qty','on_hand'] and (not isinstance(v,str) or not v.strip()):raise ValueError(t+' 空文本字段')
   key=tuple(r[k] for k in KEYS[t]); old=seen.get(key)
   if old is not None and (t!='receipts' or old!=r):raise ValueError(t+' 身份重复或冲突：'+str(key))
   seen[key]=r
   for k in ['due_at','received_at','snapshot_at']:
    if k in r:timestamp(r[k])
   for k in ['ordered_qty','qualified_qty','on_hand']:
    if k in r:
     v=r[k]
     if v is None and k=='on_hand':continue
     if type(v)!=int or abs(v)>1_000_000_000:raise ValueError(t+' 非法数量')
     if k=='ordered_qty' and v<=0:raise ValueError('订货量必须大于0')
     if k=='qualified_qty' and v<0:raise ValueError('合格验收量不能为负')
   if t=='orders' and r['status'] not in ['valid','cancelled']:raise ValueError('未知订单状态')
 sites={(r['scenario'],r['site_id']) for r in data['sites']}
 skus={(r['scenario'],r['sku_id']) for r in data['skus']}
 orders={(r['scenario'],r['order_id']) for r in data['orders']}
 lines={(r['scenario'],r['line_id']) for r in data['lines']}
 for r in data['orders']:
  if (r['scenario'],r['site_id']) not in sites:raise ValueError('订单地点不存在')
  if not any(x['scenario']==r['scenario'] and x['order_id']==r['order_id'] for x in data['lines']):raise ValueError('订单没有商品行')
 for r in data['lines']:
  if (r['scenario'],r['order_id']) not in orders or (r['scenario'],r['sku_id']) not in skus:raise ValueError('订单行孤儿引用')
 for r in data['receipts']:
  if (r['scenario'],r['line_id']) not in lines:raise ValueError('验收孤儿引用')
 grid=[]
 for scenario,site in sorted(sites):
  for case,sku in sorted(skus):
   if case==scenario:
    for day in range(14):grid.append((scenario,site,sku,str(date(2026,10,16)+timedelta(days=day))+' 18:00:00'))
 gridset=set(grid)
 for r in data['snapshots']:
  if tuple(r[k] for k in KEYS['snapshots']) not in gridset:raise ValueError('快照不在声明的每日18点网格内')
 conn=sqlite3.connect(':memory:');conn.row_factory=sqlite3.Row
 for t,fields in FIELDS.items():
  columns=','.join(k+(' INTEGER' if k in ['ordered_qty','qualified_qty','on_hand'] else ' TEXT') for k in fields)
  conn.execute(f'CREATE TABLE {t} ({columns})')
  conn.executemany(f'INSERT INTO {t} VALUES ({",".join("?" for _ in fields)})',[[r[k] for k in fields] for r in data[t]])
 conn.execute('CREATE TABLE params(start_at TEXT,end_at TEXT,as_of TEXT)');conn.execute('INSERT INTO params VALUES (?,?,?)',(START,END,ASOF))
 conn.execute('CREATE TABLE expected_grid(scenario TEXT,site_id TEXT,sku_id TEXT,snapshot_at TEXT)');conn.executemany('INSERT INTO expected_grid VALUES (?,?,?,?)',grid)
 conn.executescript((ROOT/'metrics.sql').read_text(encoding='utf-8'))
 result={name:[dict(r) for r in conn.execute('SELECT * FROM '+name+' ORDER BY 1,2'+(',3' if name in ['metric_fill','metric_stockout'] else ''))] for name in ['metric_otif','metric_fill','metric_stockout','line_result','order_result']}
 excluded=[]
 for r in data['orders']:
  reason='cancelled' if r['status']=='cancelled' else ('not_due' if r['due_at']>ASOF else ('outside_window' if not START<=r['due_at']<END else ''))
  if reason:excluded.append({**r,'reason':reason})
 result['excluded_orders']=excluded
 result['snapshot_quality']=[dict(r) for r in conn.execute("SELECT * FROM snapshot_result WHERE quality!='valid' ORDER BY 1,2,3,4")]
 result['audit']={'python_version':platform.python_version(),'sqlite_version':sqlite3.sqlite_version,'timezone':'Asia/Shanghai','window_start_inclusive':START,'window_end_exclusive':END,'as_of':ASOF,'snapshot_daily_time':'18:00:00','simulated':True,'duplicate_receipt_rows_removed':len(data['receipts'])-conn.execute('SELECT COUNT(*) FROM receipt_unique').fetchone()[0],'expected_snapshots':len(grid),'input_rows':{k:len(v) for k,v in data.items()}}
 conn.close();return result

OUTPUT_FIELDS={
 'metric_otif':['scenario','site_id','numerator','denominator','ratio'],
 'metric_fill':['scenario','sku_id','unit','numerator','denominator','ratio'],
 'metric_stockout':['scenario','site_id','sku_id','numerator','denominator','ratio','expected_count','missing_count','unknown_count','negative_count','coverage'],
 'line_result':['scenario','line_id','order_id','sku_id','ordered_qty','on_time_qty','credited_qty','passed'],
 'order_result':['scenario','site_id','order_id','passed'],
 'excluded_orders':['scenario','order_id','site_id','due_at','status','reason'],
 'snapshot_quality':['scenario','site_id','sku_id','snapshot_at','on_hand','quality']
}

def write_results(result,out):
 out=Path(out)
 if out.exists():raise FileExistsError('拒绝覆盖既有结果目录：'+str(out))
 out.mkdir(parents=True)
 for name,rows in result.items():
  if name=='audit':continue
  with (out/(name+'.csv')).open('w',encoding='utf-8',newline='') as f:
   w=csv.DictWriter(f,fieldnames=OUTPUT_FIELDS[name]);w.writeheader();w.writerows(rows)
 (out/'audit.json').write_text(json.dumps(result['audit'],ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
if __name__=='__main__':
 # 输出终端即使是ASCII也不让中文提示使已成功的计算误报失败。
 for stream in (sys.stdout,sys.stderr):
  if hasattr(stream,'reconfigure'):stream.reconfigure(errors='backslashreplace')
 parser=argparse.ArgumentParser();parser.add_argument('--data',type=Path,default=ROOT/'data');parser.add_argument('--out',type=Path,default=ROOT/'output');args=parser.parse_args()
 if args.out.exists():parser.error('拒绝覆盖既有结果目录，请换一个 --out 路径。')
 result=calculate(load(args.data))
 result['audit']['input_sha256']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(args.data.glob('*.csv'))}
 result['audit']['sql_sha256']=hashlib.sha256((ROOT/'metrics.sql').read_bytes()).hexdigest()
 write_results(result,args.out)
 print('完成：'+str(args.out))
