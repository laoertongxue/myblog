import unittest
import csv
import tempfile
from pathlib import Path
from unittest.mock import patch
from copy import deepcopy
from baseline import seasonal_naive, forecast_at, windows, validate
from generate import generate
import run


class BaselineTests(unittest.TestCase):
    def test_hand_and_multiple_weeks(self):
        rows = generate()
        last = [r['demand'] for r in rows[105:112]]
        self.assertEqual(last,[19,25,19,22,28,38,29])
        self.assertEqual(forecast_at(rows,112,7), last)
        self.assertEqual(forecast_at(rows,112,15), last*2+last[:1])
        for h in (7,8,14,15):
            self.assertEqual(forecast_at(rows,112,h)[-1],last[(h-1)%7])

    def test_future_poison(self):
        rows = generate()
        expected = forecast_at(rows,112,15)
        mutated = deepcopy(rows)
        for row in mutated[112:]:
            row.update(date='not-a-date',demand=-999)
        self.assertEqual(forecast_at(mutated,112,15),expected)

    def test_insufficient_history(self):
        for n in range(7):
            with self.assertRaises(ValueError):
                seasonal_naive(generate()[:n],7)

    def test_zero_is_valid(self):
        rows = generate()[:7]
        for row in rows: row['demand']=0
        self.assertEqual(seasonal_naive(rows,15),[0]*15)

    def test_bad_values(self):
        for value in (-1, float('nan'), float('inf'), None, True, '3'):
            rows = generate()[:7]
            rows[0]['demand']=value
            with self.assertRaises(ValueError): seasonal_naive(rows,1)

    def test_bad_dates(self):
        for kind in ('missing','duplicate','reversed','invalid'):
            rows = generate()[:9]
            if kind=='missing': del rows[2]
            if kind=='duplicate': rows[2]['date']=rows[1]['date']
            if kind=='reversed': rows.reverse()
            if kind=='invalid': rows[2]['date']='2026-02-30'
            with self.assertRaises(ValueError): seasonal_naive(rows,1)

    def test_bad_controls(self):
        for value in (0,-1,1.5,True,'7',None):
            with self.assertRaises(ValueError): seasonal_naive(generate(),value)
            with self.assertRaises(ValueError): seasonal_naive(generate(),1,value)
            with self.assertRaises(ValueError): forecast_at(generate(),value,1)
        with self.assertRaises(ValueError): forecast_at(generate(),181,1)

    def test_blocks(self):
        for a,b,count in [(113,140,24),(141,180,36)]:
            values=windows(a,b,5)
            self.assertEqual(len(values),count)
            self.assertTrue(all(a<=first<=last<=b and first==origin+1 for origin,first,last in values))
        self.assertEqual(windows(113,116,5),[])

    def test_generator(self):
        for case in ('hewei','apparel'):
            rows=generate(case)
            validate(rows)
            self.assertEqual(len(rows),180)
            self.assertEqual(rows,generate(case))

    def test_prepare_rejects_old_candidate(self):
        for marker in ('freeze.json','results/test.json'):
            with tempfile.TemporaryDirectory() as directory:
                root=Path(directory)
                (root/marker).parent.mkdir(parents=True,exist_ok=True)
                (root/marker).write_text('old evidence')
                with patch.object(run,'ROOT',root), self.assertRaises(ValueError): run.prepare()
                self.assertEqual((root/marker).read_text(),'old evidence')

    def test_csv_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'data.csv'
            rows=[dict(day=i,**r,split='train' if i<=112 else 'validation')
                  for i,r in enumerate(generate()[:140],1)]
            run.write_csv(path,rows)
            self.assertEqual(run.read_csv(path,1,140,{'train','validation'}),generate()[:140])
            for field,value in [('day',999),('split','test'),('date','2026-01-01')]:
                bad=deepcopy(rows)
                bad[112][field]=value
                run.write_csv(path,bad)
                with self.assertRaises(ValueError): run.read_csv(path,1,140,{'train','validation'})

    def test_portable_lf_output(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'file'
            run.dump(path,{'中文':'固定规则'})
            self.assertNotIn(b'\r',path.read_bytes())
            run.write_csv(path,[{'day':1,'date':'2026-04-06','demand':0,'split':'train'}])
            self.assertEqual(path.read_bytes(),b'day,date,demand,split\n1,2026-04-06,0,train\n')


if __name__=='__main__': unittest.main()
