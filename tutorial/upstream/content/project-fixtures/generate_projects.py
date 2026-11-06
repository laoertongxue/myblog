"""P01/P03 synthetic input and answer generator. Python standard library only."""
import csv,json,datetime,random,pathlib,math
ROOT=pathlib.Path(__file__).parent
START=datetime.date(2026,1,5)
def write(path,headers,rows):
 path.parent.mkdir(parents=True,exist_ok=True)
 with path.open('w',newline='',encoding='utf-8-sig') as f:
  w=csv.writer(f);w.writerow(headers);w.writerows(rows)
def p01():
 d=ROOT/'P01'; headers=['date','store_id','sku_id','unit','demand','sales','stockout_flag']
 clean=[]
 for t in range(14):
  for store in range(1,3):
   for sku in range(1,9):
    y=20+t%7+store+sku
    clean.append([(START+datetime.timedelta(days=t)).isoformat(),f'S{store}',f'K{sku:02}','kg',y,y,0])
 dirty=[r[:] for r in clean]
 # Exactly two unknown-SKU cells and two wrong-unit cells, plus three duplicate rows.
 dirty[0][2]='UNKNOWN01';dirty[1][2]='UNKNOWN02'
 dirty[2][3]='g';dirty[3][3]='g'
 dirty.extend([dirty[20][:],dirty[40][:],dirty[60][:]])
 write(d/'input/demand_dirty.csv',headers,dirty)
 write(d/'input/sku_master.csv',['sku_id','unit'],[[f'K{s:02}','kg'] for s in range(1,9)])
 # Correction ledger represents explicit source evidence, not guessed repairs.
 write(d/'input/correction_evidence.csv',['date','store_id','old_sku','correct_sku','correct_unit'],[
 [dirty[0][0],'S1','UNKNOWN01','K01','kg'],[dirty[1][0],'S1','UNKNOWN02','K02','kg'],
 [dirty[2][0],'S1','K03','K03','kg'],[dirty[3][0],'S1','K04','K04','kg']])
 events=[]
 for order in range(1,9):
  events += [[f'O{order:02}','2026-01-05T09:00:00','created',1],
             [f'O{order:02}','2026-01-05T12:00:00','shipped',1],
             [f'O{order:02}','2026-01-05T13:00:00','pre_ship_cancel' if order==1 else 'delivered',1]]
 write(d/'input/order_events_dirty.csv',['order_id','event_at','event_type','quantity'],events)
 write(d/'answers/clean_demand.csv',headers,clean)
 checks={'duplicate_extra_rows':len(dirty)-len({tuple(r[:3]) for r in dirty}),
 'unknown_sku_cells':sum(r[2].startswith('UNKNOWN') for r in dirty),
 'wrong_unit_cells':sum(r[3]!='kg' for r in dirty),
 'invalid_order_events':sum(r[2]=='pre_ship_cancel' for r in events)}
 assert checks=={'duplicate_extra_rows':3,'unknown_sku_cells':2,'wrong_unit_cells':2,'invalid_order_events':1}
 assert len(clean)==224 and len(dirty)==227 and len(events)==24
 (d/'answers/expected.json').write_text(json.dumps({'checks':checks,'total_defects':8,'dirty_daily_rows':227,'clean_daily_rows':224,'order_event_rows':24,'repair':'Use correction_evidence; de-duplicate identical keys; quarantine invalid O01 cancellation. Do not invent its true final state.'},indent=2),encoding='utf8')
 return checks
def p03():
 d=ROOT/'P03'; rng=random.Random(20261106); rows=[]; ys={}
 for store in range(1,3):
  for sku in range(1,9):
   sid=f'S{store}-K{sku:02}';seq=[]
   for t in range(180):
    y=round(max(0,20+store*2+sku+(t%7)*1.5+.025*t+rng.uniform(-2,2)),3);seq.append(y)
   ys[sid]=seq
   for i,y in enumerate(seq):
    date=START+datetime.timedelta(days=i)
    rows.append([i+1,date.isoformat(),sid,store,sku,'kg',y,date.isoformat()+'T23:59:00','train' if i<112 else 'validation' if i<140 else 'historical_test'])
 write(d/'input/demand_180d.csv',['day','date','series_id','store_id','sku_id','unit','demand','available_at','split'],rows)
 # Four intentionally unsafe recipes with inspectable values/provenance.
 feature_rows=[]
 for sid,seq in ys.items():
  global_mean=sum(seq)/180
  for target in range(2,180):
   origin=target-1
   # target-indexed centered mean includes target and next day; future target is direct leak.
   centered=sum(seq[target-2:target+1])/3
   feature_rows.append([sid,origin,target,seq[target-2],centered,target+1,seq[target-1],target,global_mean,180])
 write(d/'input/features_deliberately_leaky.csv',['series_id','origin_day','target_day','safe_lag1','centered_mean_BAD','centered_last_source_day','target_value_BAD','target_source_day','global_mean_BAD','scaler_fit_end_day'],feature_rows)
 indices=list(range(1,181));rng.shuffle(indices);train=set(indices[:112]);val=set(indices[112:140]);test=set(indices[140:])
 write(d/'input/random_split_BAD.csv',['day','split'],[[i,'train' if i in train else 'validation' if i in val else 'test'] for i in range(1,181)])
 # Answers: strictly historical features and rolling one-step seasonal-naive validation ledger.
 ledger=[]
 for sid,seq in ys.items():
  for origin in range(112,140):
   target=origin+1
   pred=seq[target-8]
   ledger.append([sid,origin,target,origin,origin,pred,seq[target-1],'validation','seasonal_naive_7'])
 write(d/'answers/safe_one_step_ledger.csv',['series_id','origin_day','target_day','train_end_day','feature_cutoff_day','forecast','actual','split','model'],ledger)
 windows=[[origin,origin+1,origin+5] for origin in range(112,136)]
 write(d/'answers/fixed_5day_windows.csv',['origin_day','first_target','last_target'],windows)
 fixes=[['centered_mean','last_source_day exceeds origin','Use trailing mean ending at origin'],['target_value','target_source_day exceeds origin','Drop target from features'],['global_scaler','fit_end_day 180 exceeds origin','Fit transforms on current training data only'],['random_split','training contains dates later than evaluation targets','Use fixed chronological split']]
 write(d/'answers/leakage_findings.csv',['defect','evidence','fix'],fixes)
 assert len(rows)==2880 and len(ledger)==16*28 and len(windows)==24
 assert all(r[2]==r[1]+1 and r[3]<=r[1] and r[4]<=r[1] for r in ledger)
 assert all(113<=r[1]<=r[2]<=140 for r in windows)
 assert max(train)>min(val)
 report={'records':2880,'series':16,'train_days':112,'validation_days':28,'historical_test_days':40,'validation_one_step_targets_per_series':28,'one_step_ledger_rows':448,'fixed_5day_windows_per_series':24,'leak_types':4,'seed':20261106,'data':'synthetic, fully observed; no stockout; all day data available at 23:59; origins after this cutoff','evaluation_note':'historical test is not an untouched blind holdout'}
 (d/'answers/expected.json').write_text(json.dumps(report,indent=2),encoding='utf8')
 return report
if __name__=='__main__':
 result={'P01':p01(),'P03':p03(),'status':'passed'}
 (ROOT/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(result,ensure_ascii=False))
