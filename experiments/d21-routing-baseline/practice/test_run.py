import copy, json, tempfile, unittest, shutil, subprocess, sys
from pathlib import Path
from run import ROOT, evaluate, run, shortest_path, validate_case, validate_routes

class RoutingTests(unittest.TestCase):
    def setUp(self):
        self.c=json.loads((ROOT/'inputs/hewei_extension.json').read_text()); self.routes=copy.deepcopy(self.c['baseline_routes'])
    def bad_case(self,field,value):
        self.c[field]=value
        with self.assertRaises(ValueError): validate_case(self.c)
    def test_baseline(self):
        s,legs=evaluate(self.c,self.routes)
        self.assertEqual(s['total_distance_m'],20000); self.assertEqual(len(legs),12)
        self.assertEqual(s['total_delivered_box'],20); self.assertFalse(s['optimality_claim'])
    def test_apparel(self):
        c=json.loads((ROOT/'inputs/apparel.json').read_text()); s,_=evaluate(c,c['baseline_routes'])
        self.assertEqual([r['distance_m'] for r in s['routes']],[14000,14000])
    def test_return_included(self):
        _,legs=evaluate(self.c,self.routes)
        self.assertEqual([r['distance_m'] for r in legs if r['to']==0],[4000,4000])
    def test_load_conservation(self):
        _,legs=evaluate(self.c,self.routes)
        for x in legs: self.assertEqual(x['departure_load_box']-x['delivered_box'],x['arrival_remaining_box'])
    def test_capacity_equal(self):
        self.c['vehicle_capacities']=[10,10]; self.assertTrue(validate_routes(self.c,self.routes))
    def test_overload(self):
        self.c['vehicle_capacities']=[9,12]
        with self.assertRaises(ValueError): validate_routes(self.c,self.routes)
    def test_missing(self):
        self.routes[0].pop(1)
        with self.assertRaises(ValueError): validate_routes(self.c,self.routes)
    def test_repeat(self):
        self.routes[0][2]=1
        with self.assertRaises(ValueError): validate_routes(self.c,self.routes)
    def test_no_return(self):
        self.routes[0].pop()
        with self.assertRaises(ValueError): validate_routes(self.c,self.routes)
    def test_no_departure(self):
        self.routes[0].pop(0)
        with self.assertRaises(ValueError): validate_routes(self.c,self.routes)
    def test_intermediate_depot(self):
        self.routes[0].insert(2,0)
        with self.assertRaises(ValueError): validate_routes(self.c,self.routes)
    def test_invalid_node(self):
        for node in [-1,11,True,1.0,'1']:
            r=copy.deepcopy(self.routes); r[0][1]=node
            with self.assertRaises(ValueError): validate_routes(self.c,r)
    def test_vehicle_count(self):
        with self.assertRaises(ValueError): validate_routes(self.c,self.routes[:1])
    def test_bad_units(self):
        self.bad_case('distance_unit','km')
    def test_bad_load_units(self): self.bad_case('load_unit','kg')
    def test_bad_id(self): self.bad_case('node_ids',[0,2])
    def test_bad_depot(self): self.bad_case('depot',False)
    def test_bad_shape(self): self.bad_case('distance_matrix',[[0]])
    def test_negative_edge(self):
        self.c['distance_matrix'][0][1]=-1
        with self.assertRaises(ValueError): validate_case(self.c)
    def test_float_edge(self):
        self.c['distance_matrix'][0][1]=1.5
        with self.assertRaises(ValueError): validate_case(self.c)
    def test_bool_edge(self):
        self.c['distance_matrix'][0][1]=True
        with self.assertRaises(ValueError): validate_case(self.c)
    def test_asymmetric(self):
        self.c['distance_matrix'][0][1]+=1
        with self.assertRaises(ValueError): validate_case(self.c)
    def test_triangle(self):
        self.c['distance_matrix'][0][1]=self.c['distance_matrix'][1][0]=100000
        with self.assertRaises(ValueError): validate_case(self.c)
    def test_diagonal(self):
        self.c['distance_matrix'][0][0]=1
        with self.assertRaises(ValueError): validate_case(self.c)
    def test_demands_length(self): self.bad_case('demands',[0])
    def test_negative_demand(self):
        self.c['demands'][1]=-2
        with self.assertRaises(ValueError): validate_case(self.c)
    def test_depot_demand(self):
        self.c['demands'][0]=1
        with self.assertRaises(ValueError): validate_case(self.c)
    def test_zero_capacity(self): self.bad_case('vehicle_capacities',[0,12])
    def test_zero_demand(self):
        self.c['demands']=[0]*11
        s,_=evaluate(self.c,self.routes); self.assertEqual(s['total_delivered_box'],0)
    def test_unsimulated(self): self.bad_case('simulated',False)
    def test_shortest_hand(self):
        g=json.loads((ROOT/'inputs/shortest_path.json').read_text())
        r=shortest_path(g['matrix'],0,3)
        self.assertEqual(r['path'],[0,2,1,3]); self.assertEqual(r['distance_m'],4000)
        self.assertEqual([x['node'] for x in r['settled']],[0,2,1,3])
    def test_shortest_unreachable(self):
        self.assertIsNone(shortest_path([[0,None],[None,0]],0,1)['distance_m'])
    def test_shortest_zero_edge(self):
        self.assertEqual(shortest_path([[0,0],[0,0]],0,1)['distance_m'],0)
    def test_shortest_same(self): self.assertEqual(shortest_path([[0]],0,0)['path'],[0])
    def test_shortest_negative(self):
        with self.assertRaises(ValueError): shortest_path([[0,-1],[-1,0]],0,1)
    def test_shortest_bad_node(self):
        with self.assertRaises(ValueError): shortest_path([[0]],True,0)
    def test_reproduction(self):
        with tempfile.TemporaryDirectory() as d:
            run(output_dir=Path(d))
            for p in (ROOT/'outputs').iterdir(): self.assertEqual(p.read_bytes(),(Path(d)/p.name).read_bytes())
    def test_coordinate_shape(self):
        for coords in (None, [], [[0,0]], [[0,0,0]]*11):
            with self.subTest(coords=coords): self.bad_case('coordinates_grid',coords)
    def test_coordinate_integer(self):
        for value in (True,1.5,'1',None):
            self.c=json.loads((ROOT/'inputs/hewei_extension.json').read_text())
            self.c['coordinates_grid'][1][0]=value
            with self.subTest(value=value), self.assertRaises(ValueError): validate_case(self.c)
    def test_coordinate_matrix_mismatch(self):
        self.c['coordinates_grid'][1]=[999,999]
        with self.assertRaises(ValueError): validate_case(self.c)
    def test_grid_step(self):
        for step in (None,0,-1,True,1.5,2000):
            with self.subTest(step=step): self.bad_case('grid_step_m',step)
    def test_shortest_nonobject_cli(self):
        with tempfile.TemporaryDirectory() as d:
            inputs=Path(d)/'inputs';shutil.copytree(ROOT/'inputs',inputs)
            (inputs/'shortest_path.json').write_text('[]')
            result=subprocess.run([sys.executable,'-B',str(ROOT/'run.py'),'--input-dir',str(inputs),'--output-dir',str(Path(d)/'output')],capture_output=True,text=True,encoding='utf-8')
            self.assertEqual(result.returncode,2)
            self.assertIn('shortest graph must be object',result.stderr)
            self.assertNotIn('Traceback',result.stderr)
            self.assertFalse((Path(d)/'output').exists())
    def test_no_input_overwrite(self):
        with self.assertRaises(ValueError): run(output_dir=ROOT/'inputs')

if __name__=='__main__': unittest.main()
