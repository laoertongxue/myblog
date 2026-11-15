"""D22 CVRP: replay checked routes by default, solve only on explicit --solve."""
import argparse, csv, json, hashlib, platform
from pathlib import Path
from d21_checker import validate_case, evaluate
ROOT=Path(__file__).resolve().parent
CASES=('hewei_extension','apparel')
VERSION='9.14.6206'
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def load(name):return json.loads((ROOT/'inputs'/f'{name}.json').read_text(encoding='utf-8'))
def solve(c):
    validate_case(c)
    import ortools
    from ortools.constraint_solver import pywrapcp, routing_enums_pb2
    if ortools.__version__!=VERSION:raise ValueError('Install pinned OR-Tools '+VERSION)
    manager=pywrapcp.RoutingIndexManager(len(c['node_ids']),len(c['vehicle_capacities']),0)
    routing=pywrapcp.RoutingModel(manager)
    cost=routing.RegisterTransitCallback(lambda a,b:c['distance_matrix'][manager.IndexToNode(a)][manager.IndexToNode(b)])
    routing.SetArcCostEvaluatorOfAllVehicles(cost)
    demand=routing.RegisterUnaryTransitCallback(lambda a:c['demands'][manager.IndexToNode(a)])
    routing.AddDimensionWithVehicleCapacity(demand,0,c['vehicle_capacities'],True,'Capacity')
    params=pywrapcp.DefaultRoutingSearchParameters()
    params.first_solution_strategy=routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    params.local_search_metaheuristic=routing_enums_pb2.LocalSearchMetaheuristic.GREEDY_DESCENT
    params.time_limit.seconds=10
    assignment=routing.SolveWithParameters(params)
    result={'ortools_version':ortools.__version__,'python_version':platform.python_version(),'first_solution':'PATH_CHEAPEST_ARC','local_search':'GREEDY_DESCENT','time_limit_seconds':10,'raw_status':routing.status(),'optimality_claim':False}
    if assignment is None:
        return dict(result,outcome='no_solution_returned_not_a_proof',routes=[])
    routes=[];cumuls=[];capacity=routing.GetDimensionOrDie('Capacity')
    for v in range(len(c['vehicle_capacities'])):
        ix=routing.Start(v);r=[];cu=[]
        while not routing.IsEnd(ix):
            r.append(manager.IndexToNode(ix));cu.append(assignment.Value(capacity.CumulVar(ix)));ix=assignment.Value(routing.NextVar(ix))
        r.append(0);cu.append(assignment.Value(capacity.CumulVar(ix)));routes.append(r);cumuls.append(cu)
    evaluated,_=evaluate(c,routes)
    if evaluated['total_distance_m']!=assignment.ObjectiveValue():raise ValueError('objective differs from independent check')
    return dict(result,outcome='feasible_found_not_proven_optimal',routes=routes,capacity_cumul_before_service=cumuls,objective_m=assignment.ObjectiveValue())
def audit(c,record):
    if record.get('outcome')!='feasible_found_not_proven_optimal':raise ValueError('no feasible route to compare')
    if record.get('optimality_claim') is not False:raise ValueError('unreviewed optimality claim')
    result,legs=evaluate(c,record['routes'])
    if result['total_distance_m']!=record['objective_m']:raise ValueError('stored objective differs')
    expected=[]
    for r in record['routes']:
        s=0;cu=[]
        for node in r:cu.append(s);s+=c['demands'][node]
        expected.append(cu)
    if record['capacity_cumul_before_service']!=expected:raise ValueError('capacity cumul timing differs')
    for leg in legs:
        leg['after_service_remaining_box']=leg.pop('arrival_remaining_box')
        leg['cumulative_delivered_box']=sum(c['demands'][n] for n in record['routes'][leg['vehicle']-1][1:leg['leg']+1])
    return result,legs
def run(out,generate=False):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    summaries=[];legs=[]
    for name in CASES:
        c=load(name);input_hash=hashlib.sha256((ROOT/'inputs'/f'{name}.json').read_bytes()).hexdigest()
        if generate:
            record=solve(c);record['input_sha256']=input_hash;dump(out/f'{name}_solver.json',record)
        else:record=json.loads((ROOT/'outputs'/f'{name}_solver.json').read_text())
        if record['input_sha256']!=input_hash:raise ValueError('input hash differs')
        result,ls=audit(c,record);baseline,_=evaluate(c,c['baseline_routes'])
        summaries.append({'case_id':name,'baseline':baseline,'solver':result,'difference_m':baseline['total_distance_m']-result['total_distance_m'],'optimality_claim':False})
        legs.extend(ls)
    dump(out/'comparison.json',summaries)
    with (out/'delivery_legs.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(legs[0]),lineterminator='\n');w.writeheader();w.writerows(legs)
    return summaries
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--solve',action='store_true');p.add_argument('--output-dir',type=Path,default=ROOT/'outputs');a=p.parse_args()
    if a.solve and a.output_dir.resolve()==(ROOT/'outputs').resolve():p.error('--solve requires a separate --output-dir; preserve published evidence')
    print(json.dumps(run(a.output_dir,a.solve),ensure_ascii=False,indent=2))
