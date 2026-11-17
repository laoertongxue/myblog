import unittest,json,copy
from routing import *
class Tests(unittest.TestCase):
 def setUp(self):self.c=json.loads((ROOT/'inputs/apparel.json').read_text())
 def test_baseline(self):
  a=check(self.c,self.c['baseline_routes']);self.assertTrue(a['feasible']);self.assertEqual(a['distance_m'],14000);self.assertEqual(a['rows'][0]['wait'],9);self.assertEqual(a['rows'][1]['arrival'],516);self.assertEqual(a['rows'][4]['arrival'],573)
 def test_tight(self):
  c=tightened(self.c);self.assertIn('window_0_2',check(c,c['baseline_routes'])['errors']);self.assertTrue(check(c,[[0,2,1,4,3,0],[0,0]])['feasible'])
 def test_coverage(self):
  for r in [[[0,1,2,3,0],[0,0]],[[0,1,2,3,4,1,0],[0,0]]]:self.assertIn('coverage',check(self.c,r)['errors'])
 def test_capacity(self):
  self.c['vehicle_capacities']=[6,12];self.assertIn('capacity_0',check(self.c,self.c['baseline_routes'])['errors'])
 def test_return(self):
  self.c['return_deadline']=550;self.assertIn('return_0',check(self.c,self.c['baseline_routes'])['errors'])
 def test_service_effect(self):
  a=check(self.c,self.c['baseline_routes']);self.c['service_minutes'][1]=0;b=check(self.c,self.c['baseline_routes']);self.assertNotEqual(a['rows'][1]['arrival'],b['rows'][1]['arrival'])
 def test_invalid_inputs(self):
  for key,val in [('time_matrix',[[0]]),('demands',[0,-2,2,2,2]),('time_windows',[[480,600],[540,500],[510,550],[520,580],[520,590]]),('service_minutes',[0,1.5,2,2,2])]:
   with self.subTest(key=key):
    c=copy.deepcopy(self.c);c[key]=val
    with self.assertRaises(AssertionError):validate(c)
 def test_routes(self):
  for routes in [[[0,1,0,2,3,4,0],[0,0]],[[0,1,2,3,4,9,0],[0,0]],[[0,1,2,3,4,0]]]:self.assertFalse(check(self.c,routes)['feasible'])
 def test_published(self):
  for name in ['apparel','hewei_extension']:
   c=json.loads((ROOT/'inputs'/f'{name}.json').read_text())
   for variant,cc in [('base',c),('tightened',tightened(c))]:
    rec=json.loads((ROOT/'outputs'/f'{name}_{variant}.json').read_text());self.assertEqual(audit_record(cc,rec),rec['audit']);self.assertTrue(rec['audit']['feasible']);self.assertGreater(len(enumerate_feasible(cc)),0)
 def test_corrupt_evidence(self):
  rec=json.loads((ROOT/'outputs/apparel_base.json').read_text())
  for key,val in [('raw_status',4),('optimality_claim',True),('elapsed_seconds',-1),('input_sha256','bad'),('objective_m',0),('routes',None),('enumeration_count',999),('baseline_audit',{})]:
   with self.subTest(key=key):
    r=copy.deepcopy(rec);r[key]=val
    with self.assertRaises(AssertionError):audit_record(self.c,r)
 def test_impossible(self):
  self.c['time_windows'][2]=[480,480];self.assertEqual(enumerate_feasible(self.c),[])
if __name__=='__main__':unittest.main()
