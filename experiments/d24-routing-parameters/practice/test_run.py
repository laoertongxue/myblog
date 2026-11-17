import copy,json,unittest
from pathlib import Path
import run
class Tests(unittest.TestCase):
 def test_saved_records(self):
  for key,c,t,g in run.scenarios():
   with self.subTest(key=key):self.assertTrue(run.audit(run.read(run.ROOT/'outputs'/(key+'.json')),c,t))
 def test_capacities(self):
  ss=run.scenarios();self.assertEqual(len(ss),14)
  for key,c,t,g in ss:
   if 'minus20' in key:self.assertEqual(c['vehicle_capacities'],[9,9]);self.assertGreater(sum(c['demands']),sum(c['vehicle_capacities']))
 def test_single_factor(self):
  for name in ['apparel','hewei_extension']:
   ss=[x for x in run.scenarios() if x[0].startswith(name+'_') and x[3]!='window'];base=ss[0][1]
   for key,c,t,g in ss:
    changed=copy.deepcopy(c);changed['vehicle_capacities']=base['vehicle_capacities'];self.assertEqual(changed,base)
 def test_window_subset(self):
  for name in ['apparel_tw','hewei_tw']:
   base=run.read(run.ROOT/'inputs'/(name+'.json'));tw=base['tightened_window'];old=base['time_windows'][base['tightened_node']]
   self.assertTrue(old[0]<=tw[0]<=tw[1]<=old[1]);self.assertNotEqual(tw,old)
 def test_missing_customer(self):
  c=run.read(run.ROOT/'inputs/apparel.json');routes=copy.deepcopy(c['baseline_routes']);routes[0].pop(1)
  with self.assertRaises(ValueError):run.check(c,routes)
 def test_duplicate_customer(self):
  c=run.read(run.ROOT/'inputs/apparel.json');r=copy.deepcopy(c['baseline_routes']);r[0][1]=r[0][2]
  with self.assertRaises(ValueError):run.check(c,r)
 def test_capacity(self):
  c=run.read(run.ROOT/'inputs/apparel.json');c['vehicle_capacities']=[9,9]
  with self.assertRaises(ValueError):run.check(c,c['baseline_routes'])
 def test_depot(self):
  c=run.read(run.ROOT/'inputs/apparel.json');r=copy.deepcopy(c['baseline_routes']);r[0][-1]=1
  with self.assertRaises(ValueError):run.check(c,r)
 def test_late_window(self):
  c=run.read(run.ROOT/'inputs/apparel_tw.json');c['time_windows'][1]=[0,0]
  with self.assertRaises(ValueError):run.check(c,c['baseline_routes'])
 def test_late_return(self):
  c=run.read(run.ROOT/'inputs/apparel_tw.json');c['return_deadline']=480
  with self.assertRaises(ValueError):run.check(c,c['baseline_routes'])
 def test_tamper(self):
  key,c,t,_=run.scenarios()[0];r=run.read(run.ROOT/'outputs'/(key+'.json'));r['metrics']['distance_m']+=1
  with self.assertRaises(ValueError):run.audit(r,c,t)
 def test_hash(self):
  key,c,t,_=run.scenarios()[0];r=run.read(run.ROOT/'outputs'/(key+'.json'));c['vehicle_capacities'][0]=11
  with self.assertRaises(ValueError):run.audit(r,c,t)
 def test_null_metrics(self):
  key,c,t,_=run.scenarios()[1];r=run.read(run.ROOT/'outputs'/(key+'.json'));r['metrics']={}
  with self.assertRaises(ValueError):run.audit(r,c,t)
 def test_cert(self):
  key,c,t,_=run.scenarios()[1];r=run.read(run.ROOT/'outputs'/(key+'.json'));r['independent_infeasibility_certificate']=None
  with self.assertRaises(ValueError):run.audit(r,c,t)
 def test_config_mutations(self):
  key,c,t,_=run.scenarios()[0];r=run.read(run.ROOT/'outputs'/(key+'.json'))
  for field,bad in [('raw_status',6),('status','INFEASIBLE'),('ortools_version','fake'),('first_solution','bogus'),('local_search','bogus'),('optimality_claim',True),('wall_seconds',-1),('wall_seconds',float('nan'))]:
   x=copy.deepcopy(r);x[field]=bad
   with self.subTest(field=field),self.assertRaises(ValueError):run.audit(x,c,t)
 def test_time_input_mutations(self):
  c=run.read(run.ROOT/'inputs/apparel_tw.json')
  for field,bad in [('time_unit','seconds'),('departure_minutes',[False,480]),('return_deadline',-1),('service_minutes',[100,8,8,10,8])]:
   x=copy.deepcopy(c);x[field]=bad
   with self.subTest(field=field),self.assertRaises(ValueError):run.check(x,x['baseline_routes'])
 def test_scenario_identity(self):
  from unittest.mock import patch
  real=run.read
  def altered(path):
   obj=real(path)
   if path.name=='apparel_base.json':obj['id']='fake'
   return obj
  import tempfile
  with tempfile.TemporaryDirectory() as d,patch.object(run,'read',side_effect=altered),self.assertRaises(ValueError):run.run(Path(d))
if __name__=='__main__':unittest.main(verbosity=2)
