import copy, importlib.util, json, tempfile, unittest
from pathlib import Path
import run
from d21_checker import validate_case, validate_routes, evaluate

class D22Tests(unittest.TestCase):
    def setUp(self):self.c=run.load('hewei_extension');self.r=copy.deepcopy(self.c['baseline_routes'])
    def bad(self,change):
        c=copy.deepcopy(self.c);change(c)
        with self.assertRaises((ValueError,TypeError)):validate_case(c)
    def test_baseline_distance(self):self.assertEqual(evaluate(self.c,self.r)[0]['total_distance_m'],20000)
    def test_apparel_baseline(self):
        c=run.load('apparel');self.assertEqual(evaluate(c,c['baseline_routes'])[0]['total_distance_m'],28000)
    def test_capacity_equal_is_valid(self):self.c['vehicle_capacities']=[10,10];self.assertTrue(validate_routes(self.c,self.r))
    def test_capacity_over(self):
        self.c['vehicle_capacities']=[9,12]
        with self.assertRaises(ValueError):validate_routes(self.c,self.r)
    def test_wrong_vehicle_number(self):
        with self.assertRaises(ValueError):validate_routes(self.c,self.r[:1])
    def test_missing(self):
        self.r[0].pop(1)
        with self.assertRaises(ValueError):validate_routes(self.c,self.r)
    def test_duplicate(self):
        self.r[0][1]=2
        with self.assertRaises(ValueError):validate_routes(self.c,self.r)
    def test_no_return(self):
        self.r[0].pop()
        with self.assertRaises(ValueError):validate_routes(self.c,self.r)
    def test_no_departure(self):
        self.r[0].pop(0)
        with self.assertRaises(ValueError):validate_routes(self.c,self.r)
    def test_reload_forbidden(self):
        self.r[0].insert(3,0)
        with self.assertRaises(ValueError):validate_routes(self.c,self.r)
    def test_bad_node(self):
        self.r[0][1]=11
        with self.assertRaises(ValueError):validate_routes(self.c,self.r)
    def test_bool_node(self):
        self.r[0][1]=True
        with self.assertRaises(ValueError):validate_routes(self.c,self.r)
    def test_units(self):
        for k,v in [('distance_unit','km'),('load_unit','kg')]:
            with self.subTest(k=k):self.bad(lambda c:c.update({k:v}))
    def test_float_demand(self):self.bad(lambda c:c['demands'].__setitem__(1,2.0))
    def test_negative_demand(self):self.bad(lambda c:c['demands'].__setitem__(1,-1))
    def test_zero_capacity(self):self.bad(lambda c:c.update(vehicle_capacities=[0,12]))
    def test_not_simulated(self):self.bad(lambda c:c.update(simulated=False))
    def test_wrong_matrix(self):self.bad(lambda c:c['distance_matrix'].pop())
    def test_negative_distance(self):self.bad(lambda c:c['distance_matrix'][0].__setitem__(1,-1))
    def test_nonzero_depot_demand(self):self.bad(lambda c:c['demands'].__setitem__(0,1))
    def test_hand_four_node_route(self):
        # Depot + three customers: 0->1->2->3->0, includes return 4000 m.
        m=[[0,2000,3000,4000],[2000,0,1000,2000],[3000,1000,0,1000],[4000,2000,1000,0]]
        c={'case_id':'hand_four_nodes','simulated':True,'distance_unit':'m','load_unit':'box','depot':0,'node_ids':[0,1,2,3],'coordinates_grid':[[0,0],[1,1],[2,1],[3,1]],'grid_step_m':1000,'distance_matrix':m,'demands':[0,2,2,2],'vehicle_capacities':[6]}
        result,legs=evaluate(c,[[0,1,2,3,0]])
        self.assertEqual(result['total_distance_m'],8000)
        self.assertEqual([x['distance_m'] for x in legs],[2000,1000,1000,4000])
        self.assertEqual(result['routes'][0]['initial_load_box'],6)
    def test_packing_counterexample(self):
        # Exhaust ALL 2^3 allocations; no routing assumption is needed for this proof.
        import itertools
        self.assertLessEqual(6*3,10*2)
        feasible=[a for a in itertools.product(range(2),repeat=3) if all(6*a.count(v)<=10 for v in range(2))]
        self.assertEqual(feasible,[])
    def test_remaining_load(self):
        _,legs=evaluate(self.c,self.r)
        self.assertEqual([x['arrival_remaining_box'] for x in legs[:6]],[8,6,4,2,0,0])
        self.assertEqual([x['departure_load_box'] for x in legs[:6]],[10,8,6,4,2,0])
    def test_return_leg(self):
        _,legs=evaluate(self.c,self.r);self.assertEqual(legs[5]['distance_m'],4000)
    def test_saved_routes(self):
        for name in run.CASES:
            c=run.load(name);record=json.loads((run.ROOT/'outputs'/f'{name}_solver.json').read_text());result,_=run.audit(c,record)
            self.assertEqual(result['total_distance_m'],20000 if name=='hewei_extension' else 28000)
    def test_cumul_is_before_service(self):
        record=json.loads((run.ROOT/'outputs/hewei_extension_solver.json').read_text())
        self.assertEqual(record['capacity_cumul_before_service'][0],[0,0,2,4,6,8,10])
        record['capacity_cumul_before_service'][0][1]=2
        with self.assertRaises(ValueError):run.audit(self.c,record)
    def test_objective_tamper(self):
        record=json.loads((run.ROOT/'outputs/hewei_extension_solver.json').read_text());record['objective_m']-=1
        with self.assertRaises(ValueError):run.audit(self.c,record)
    def test_failed_outcome_not_comparable(self):
        with self.assertRaises(ValueError):run.audit(self.c,{'outcome':'no_solution_returned_not_a_proof'})
    def test_no_optimality_claim(self):
        record=json.loads((run.ROOT/'outputs/hewei_extension_solver.json').read_text());record['optimality_claim']=True
        with self.assertRaises(ValueError):run.audit(self.c,record)
    def test_official_saved_output_independent(self):
        import ast, re
        source=(run.ROOT/'reference/vrp_capacity.py').read_text()
        tree=ast.parse(source);fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='create_data_model')
        ns={};exec(compile(ast.Module(body=[fn],type_ignores=[]),'<official data>','exec'),ns)
        c=ns['create_data_model']();text=(run.ROOT/'reference/official_output.txt').read_text()
        lines=[s for s in text.splitlines() if 'Load(0) ->' in s]
        self.assertEqual(len(lines),4);seen=[];total=0
        for line,cap in zip(lines,c['vehicle_capacities']):
            pairs=[(int(a),int(b)) for a,b in re.findall(r'(\d+) Load\((\d+)\)',line)]
            route=[a for a,b in pairs];self.assertEqual((route[0],route[-1]),(0,0));seen+=route[1:-1]
            cumulative=0
            for node,load in pairs:cumulative+=c['demands'][node];self.assertEqual(cumulative,load)
            self.assertLessEqual(cumulative,cap)
            total+=sum(c['distance_matrix'][a][b] for a,b in zip(route,route[1:]))
        self.assertEqual(sorted(seen),list(range(1,17)));self.assertEqual(total,6208)
    def test_replay_byte_parity(self):
        with tempfile.TemporaryDirectory() as d:
            run.run(d)
            for n in ('comparison.json','delivery_legs.csv'):self.assertEqual((Path(d)/n).read_bytes(),(run.ROOT/'outputs'/n).read_bytes())

if __name__=='__main__':unittest.main()
