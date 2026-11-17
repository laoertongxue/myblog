import unittest,math
from run import *
class Tests(unittest.TestCase):
 def test_zero(self):
  for m in METHODS:self.assertEqual(forecast([0]*10,m),0)
 def test_empty(self):
  with self.assertRaises(ValueError):forecast([],'tsb')
 def test_invalid(self):
  for v in [-1,float('nan'),float('inf'),True,None]:
   with self.assertRaises(ValueError):forecast([0,v],'tsb')
 def test_alpha(self):
  for a in [0,-1,1.1,float('nan')]:
   with self.assertRaises(ValueError):forecast([1],'tsb',a)
 def test_initial(self):self.assertAlmostEqual(forecast([0,0,6],'croston'),2)
 def test_hold(self):self.assertEqual(forecast([4,0,0],'croston'),4)
 def test_decay(self):self.assertAlmostEqual(forecast([4,0,0],'tsb',.1),3.24)
 def test_update(self):self.assertAlmostEqual(forecast([4,0,6],'croston',.2),4.4/1.2)
 def test_sba(self):self.assertAlmostEqual(forecast([4,0,6],'sba',.2),.9*forecast([4,0,6],'croston',.2))
 def test_describe(self):
  d=describe([0,2,0,0,4,0,0,0]);self.assertEqual(d['adi'],4);self.assertAlmostEqual(d['cv2'],2/9)
 def test_describe_edges(self):
  self.assertIsNone(describe([0,0])['adi']);self.assertIsNone(describe([1,0])['cv2'])
 def test_windows(self):
  _,r=evaluate(generate()['apparel'],112,140,'croston',.1)
  self.assertEqual(len(r),5);self.assertEqual(r[0]['target_start'],113);self.assertEqual(r[-1]['target_end'],137)
 def test_test_windows(self):
  _,r=evaluate(generate()['apparel'],140,180,'croston',.1);self.assertEqual(len(r),8);self.assertEqual(r[-1]['target_end'],180)
 def test_no_future(self):
  y=generate()['apparel'];_,a=evaluate(y,140,180,'tsb',.1);y[140:]=[999]*40;_,b=evaluate(y,140,180,'tsb',.1);self.assertEqual(a[0]['forecast_5'],b[0]['forecast_5'])
 def test_selection_no_test(self):
  d=generate();a,_=experiment(d);d['apparel'][140:]=[999]*40;b,_=experiment(d);self.assertEqual(a['apparel']['frozen_selection'],b['apparel']['frozen_selection'])
 def test_reproducible(self):self.assertEqual(experiment(generate()),experiment(generate()))
 def test_nonnegative(self):
  for m in METHODS:
   for n in range(1,181):self.assertGreaterEqual(forecast(generate()['apparel'][:n],m,.3),0)
 def test_unknown(self):
  with self.assertRaises(ValueError):forecast([1],'fake')
if __name__=='__main__':unittest.main()
