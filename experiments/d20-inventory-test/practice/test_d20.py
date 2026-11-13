import csv,io,json,math,unittest,copy,tempfile,shutil
from pathlib import Path
import run
E=run.engine

class TestD20(unittest.TestCase):
 def setUp(self):self.cfg=run.load_frozen()
 def test_source_hashes(self):
  for c in self.cfg['cases']:self.assertEqual(len(run.load_data(c)),180)
 def test_exact_frozen_config(self):self.assertEqual(run.digest((run.ROOT/'source/d19_frozen_config.json').read_bytes()),run.EXPECTED_CONFIG)
 def test_freeze_receipt(self):
  r=json.loads((run.ROOT/'source/d19_freeze_receipt.json').read_text());self.assertEqual(r['frozen_config_sha256'],run.EXPECTED_CONFIG)
  self.assertEqual(r['selection_results_sha256'],run.digest((run.ROOT/'source/d19_validation_results.json').read_bytes()))
 def test_window_counts(self):
  for c,cc in self.cfg['cases'].items():
   rows=run.forecast_rows(run.load_data(c),c,cc['unit']);self.assertEqual([sum(r['horizon']==h for r in rows) for h in (1,5)],[40,36])
 def test_window_boundaries(self):
  for r in run.forecast_rows(run.load_data('hewei'),'hewei','kg'):self.assertTrue(141<=r['target_start']<=r['target_end']<=180);self.assertEqual(r['target_start'],r['origin']+1)
 def test_no_retuning(self):
  result=json.loads(run.build()['results.json'])
  for r in result:self.assertEqual(r['parameters'],self.cfg['cases'][r['case']]['winners'][r['policy']]['parameters'])
 def test_exact_results(self):
  rr=json.loads(run.build()['results.json']);self.assertEqual([(r['lost'],r['order_count'],r['end_oh'],r['end_pipeline']) for r in rr],[(5,15,39,104),(8,10,78,64),(65,8,162,422),(69,10,304,284)])
 def test_independent_daily_calculation(self):
  # Independent index-based calendar implementation, no engine.simulate call for reference.
  for c,cc in self.cfg['cases'].items():
   d=run.load_data(c)
   for key,selected in cc['winners'].items():
    p=selected['parameters'];oh=cc['initial_oh'];scheduled={};total_orders=0
    expected=[]
    for day in range(153,181):
     opening=oh;arrivals=scheduled.pop(day,0);oh+=arrivals;f=min(oh,d[day-1]);oh-=f
     future=sum(d[day-7+h] for h in range(p['L']+p['R']))
     threshold=math.ceil(future+p['z']*p['scale']);oo=sum(scheduled.values());ip=oh+oo
     review=(day-153)%p['R']==0
     q=(p['Q'] if ip<=threshold else 0) if key=='daily_sQ' else max(0,threshold-ip) if review else 0
     if q:scheduled[day+3]=scheduled.get(day+3,0)+q;total_orders+=1
     expected.append((day,opening,arrivals,f,d[day-1]-f,oh,oo,ip,threshold,q))
    ledger,_,_,_=E.simulate(d[152:],d[:152],p,cc['initial_oh'],start=153)
    actual=[tuple(r[k] for k in ('day','opening_oh','arrivals','fulfilled','lost','end_oh','pipeline_before','ip_before','threshold','ordered')) for r in ledger]
    self.assertEqual(actual,expected)
 def test_all_conservation(self):
  for c,cc in self.cfg['cases'].items():
   d=run.load_data(c)
   for selected in cc['winners'].values():
    ll,ee,pp,s=E.simulate(d[152:],d[:152],selected['parameters'],cc['initial_oh'],start=153)
    prior=0
    for r in ll:
     self.assertEqual(r['opening_oh']+r['arrivals']-r['fulfilled'],r['end_oh']);self.assertEqual(r['demand'],r['fulfilled']+r['lost'])
     self.assertEqual(prior-r['arrivals']+r['ordered'],r['pipeline_after']);prior=r['pipeline_after']
     self.assertGreaterEqual(r['end_oh'],0);self.assertGreaterEqual(prior,0)
    self.assertEqual(cc['initial_oh']+s['arrivals']-s['fulfilled'],s['end_oh']);self.assertEqual(s['ordered']-s['arrivals'],s['end_pipeline'])
    self.assertEqual(sum(x['quantity'] for x in pp),s['end_pipeline'])
 def test_initial_states(self):
  for r in json.loads(run.build()['results.json']):self.assertEqual((r['initial_oh'],r['initial_pipeline']),(78 if r['case']=='hewei' else 316,0))
 def test_review_phase(self):
  rows=list(csv.DictReader(io.StringIO(run.build()['ledger.csv'].decode())))
  for r in rows:
   if r['policy']=='periodic_RS':self.assertEqual(int(r['review']),int((int(r['day'])-153)%3==0))
 def test_arrival_timing(self):
  rows=list(csv.DictReader(io.StringIO(run.build()['order_events.csv'].decode())))
  for r in rows:
   if r['event']=='placed':self.assertEqual(int(r['arrival_day']),int(r['day'])+3)
   else:self.assertEqual(int(r['arrival_day']),int(r['day']))
 def test_future_perturbations(self):
  for c,cc in self.cfg['cases'].items():
   d=run.load_data(c)
   for selected in cc['winners'].values():
    p=selected['parameters'];base=E.simulate(d[152:],d[:152],p,cc['initial_oh'],start=153)[0]
    for offset in range(1,28):
     altered=d[152:].copy();altered[offset]+=10000
     result=E.simulate(altered,d[:152],p,cc['initial_oh'],start=153)[0]
     self.assertEqual(base[:offset],result[:offset])
 def test_sales_do_not_feed_forecast(self):
  for c,cc in self.cfg['cases'].items():
   d=run.load_data(c)
   for selected in cc['winners'].values():
    p=selected['parameters'];a=E.simulate(d[152:],d[:152],p,0,start=153)[0];b=E.simulate(d[152:],d[:152],p,99999,start=153)[0]
    self.assertEqual([r['threshold'] for r in a],[r['threshold'] for r in b])
 def test_repeated_build(self):self.assertEqual(run.build(),run.build())
 def test_inputs_unmodified(self):
  d=run.load_data('hewei');p=self.cfg['cases']['hewei']['winners']['daily_sQ']['parameters'];before=copy.deepcopy((d,p));E.simulate(d[152:],d[:152],p,78,start=153);self.assertEqual((d,p),before)
 def test_zero_demand(self):
  s=E.simulate([0]*7,[0]*7,dict(policy='periodic_RS',R=3,L=2,z=0,scale=0),0,start=8)[3];self.assertIsNone(s['fill_rate']);self.assertEqual(s['order_count'],0)
 def test_equal_threshold(self):
  r=E.simulate([0],[],dict(policy='daily_sQ',R=1,L=2,Q=6,fixed_threshold=10),10,start=1)[0][0];self.assertEqual(r['ordered'],6)
 def test_no_same_day_delivery(self):
  rows=E.simulate([9,9],[],dict(policy='daily_sQ',R=1,L=0,Q=10,fixed_threshold=10),0,start=1)[0];self.assertEqual(rows[0]['fulfilled'],0);self.assertEqual(rows[1]['arrivals'],10)
 def test_one_order_daily(self):
  rows=E.simulate([100]*5,[],dict(policy='daily_sQ',R=1,L=2,Q=6,fixed_threshold=1000),0,start=1)[0];self.assertTrue(all(r['ordered']==6 for r in rows))
 def test_invalid_negative(self):
  with self.assertRaises(ValueError):E.simulate([-1],[],dict(policy='daily_sQ',R=1,L=2,Q=6,fixed_threshold=10),0,start=1)
 def test_invalid_bool(self):
  with self.assertRaises(ValueError):E.forecast([1]*6+[True],1)
 def test_invalid_nan(self):
  with self.assertRaises(ValueError):E.simulate([1],[1]*7,dict(policy='periodic_RS',R=3,L=2,z=float('nan'),scale=1),0,start=8)
 def test_duplicate_order(self):
  with self.assertRaises(ValueError):E.simulate([1],[],dict(policy='daily_sQ',R=1,L=2,Q=6,fixed_threshold=10),0,[dict(id='a',arrival_day=1,quantity=2)]*2,start=1)
 def test_past_arrival(self):
  with self.assertRaises(ValueError):E.simulate([1],[],dict(policy='daily_sQ',R=1,L=2,Q=6,fixed_threshold=10),0,[dict(id='a',arrival_day=1,quantity=2)],start=2)
 def test_forecast_exact_index(self):self.assertEqual(E.forecast([1,2,3,4,5,6,7],9),[1,2,3,4,5,6,7,1,2])
 def test_forecast_error_sign(self):
  rows=run.forecast_rows(run.load_data('hewei'),'hewei','kg')
  for r in rows:self.assertEqual(r['error'],r['actual']-r['prediction'])
 def test_mean_denominator(self):
  result=json.loads(run.build()['results.json']);rows=list(csv.DictReader(io.StringIO(run.build()['ledger.csv'].decode())))
  for r in result:
   ll=[x for x in rows if x['case']==r['case'] and x['policy']==r['policy']];self.assertEqual(len(ll),28);self.assertEqual(sum(int(x['end_oh']) for x in ll)/28,r['mean_end_oh'])
 def test_manifest(self):run.verify()
 def test_tamper_rejected(self):
  with tempfile.TemporaryDirectory() as tmp:
   dest=Path(tmp)/'p';shutil.copytree(run.ROOT,dest);path=dest/'data/hewei-test.csv';path.write_bytes(path.read_bytes()+b'\n');old=run.ROOT
   try:
    run.ROOT=dest
    with self.assertRaises(ValueError):run.verify()
   finally:run.ROOT=old

if __name__=='__main__':unittest.main()
