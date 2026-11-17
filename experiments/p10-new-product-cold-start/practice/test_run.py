import unittest,copy,math,json
from pathlib import Path
from run import *
class Test(unittest.TestCase):
 def setUp(self):self.cases=json.loads((ROOT/'data/cases.json').read_text());self.c=self.cases[0];self.ref,self.val,self.test=validate_case(self.c)
 def test_blend_hand(self):self.assertEqual(blend(120,80,.25),110)
 def test_blend_bounds(self):
  for w in GRID:self.assertTrue(80<=blend(120,80,w)<=120)
 def test_bad_weight(self):
  for x in [-1,1.1,float('nan'),float('inf'),True]:
   with self.assertRaises(ValueError):blend(120,80,x)
 def test_negative_units(self):
  with self.assertRaises(ValueError):blend(-1,4,.5)
 def test_weights(self):
  self.assertEqual(run_case(self.cases[0])['weight'],.5);self.assertEqual(run_case(self.cases[1])['weight'],.5)
 def test_expected(self):
  r=run_case(self.c);self.assertEqual([x['mixed_w2'] for x in r['test']],[100,140]);self.assertEqual(r['test_mae_week2']['mixed_w2'],20)
 def test_no_test_labels_in_selection(self):
  a=run_case(self.c);self.c['products'][-1]['w2']=99999;b=run_case(self.c);self.assertEqual(a['weight'],b['weight']);self.assertEqual(a['test'][1]['mixed_w2'],b['test'][1]['mixed_w2'])
 def test_future_reference(self):
  x=copy.deepcopy(self.ref[0]);x['launch']='2027-01-01';x['w2']=9999
  self.assertEqual(analog(self.ref+[x],self.test[0],2,'2026-03-08')[0],120)
 def test_self_reference(self):
  x=copy.deepcopy(self.test[0]);x['split']='reference';x['w2']=99999
  self.assertEqual(analog(self.ref+[x],self.test[0],2,'2026-03-08')[0],120)
 def test_reference_censor(self):
  self.ref[0]['fully_observed']=False;self.ref[0]['w2']=0
  self.assertEqual(analog(self.ref,self.test[0],2,'2026-03-08')[0],130)
 def test_all_reference_censored(self):
  for r in self.ref:r['fully_observed']=False
  with self.assertRaises(ValueError):analog(self.ref,self.test[0],2,'2026-03-08')
 def test_no_match(self):
  self.test[0]['band']='other'
  with self.assertRaises(ValueError):analog(self.ref,self.test[0],2,'2026-03-08')
 def test_not_observed(self):
  with self.assertRaises(ValueError):recent_feature(self.test[0],'2026-03-07')
 def test_censor(self):
  self.test[0]['fully_observed']=False
  with self.assertRaises(ValueError):recent_feature(self.test[0],'2026-03-08')
 def test_split_maturity(self):
  self.c['products'][3]['launch']='2026-03-01'
  with self.assertRaises(ValueError):run_case(self.c)
 def test_duplicates(self):
  self.c['products'].append(self.c['products'][0])
  with self.assertRaises(ValueError):run_case(self.c)
 def test_selection_rejects_test(self):
  with self.assertRaises(ValueError):select_weight(self.ref,self.test)
 def test_scenario(self):self.assertAlmostEqual(scenario(70,100,.4,.15,.12)['ingredient_total_kg'],19.14)
 def test_bad_substitution(self):
  for s in [-.1,1.1]:
   with self.assertRaises(ValueError):scenario(70,100,s,.15,.12)
 def test_hewei(self):self.assertEqual(run_case(self.cases[1])['test_mae_week2']['mixed_w2'],7.5)
if __name__=='__main__':unittest.main()
