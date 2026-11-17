"""D24 single-factor experiments. Standard-library replay; optional pinned OR-Tools solve."""
import argparse, copy, csv, hashlib, json, platform, time, math
from pathlib import Path
from d21_checker import validate_case, evaluate
ROOT=Path(__file__).resolve().parent
VERSION='9.14.6206'
STATUS={0:'NOT_SOLVED',1:'SUCCESS',2:'PARTIAL_SUCCESS_LOCAL_OPTIMUM_NOT_REACHED',3:'FAIL',4:'FAIL_TIMEOUT',5:'INVALID',6:'INFEASIBLE',7:'OPTIMAL'}
def read(p): return json.loads(p.read_text(encoding='utf-8'))
def dump(p,x): p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def digest(c): return hashlib.sha256(json.dumps(c,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
def scenarios():
    out=[]
    for name in ['apparel','hewei_extension']:
        base=read(ROOT/'inputs'/f'{name}.json')
        for cap,label in [(12,'base'),(9,'capacity_floor_minus20'),(14,'capacity_floor_plus20')]:
            c=copy.deepcopy(base);c['vehicle_capacities']=[cap,cap]
            out.append((f'{name}_{label}',c,1,'capacity'))
        for seconds in [5,10]:out.append((f'{name}_time_{seconds}',copy.deepcopy(base),seconds,'search_time'))
    for name in ['apparel_tw','hewei_tw']:
        c=read(ROOT/'inputs'/f'{name}.json');out.append((name+'_base',copy.deepcopy(c),1,'window'))
        c['time_windows'][c['tightened_node']]=c['tightened_window'];out.append((name+'_tight',c,1,'window'))
    return out

def validate_time(c):
    if 'time_matrix' not in c:return
    if c.get('time_unit')!='minute_after_midnight':raise ValueError('time unit')
    n=len(c['node_ids']);tm=c['time_matrix'];sv=c['service_minutes'];tw=c['time_windows'];dep=c['departure_minutes']
    integer=lambda x:type(x)is int and 0<=x<=1440
    if len(tm)!=n or any(len(row)!=n or any(not integer(x) for x in row) for row in tm):raise ValueError('time matrix')
    if any(tm[i][i]!=0 for i in range(n)):raise ValueError('time diagonal')
    if len(sv)!=n or any(not integer(x) for x in sv) or sv[0]!=0:raise ValueError('service minutes')
    if len(tw)!=n or any(len(w)!=2 or not all(integer(x) for x in w) or w[0]>w[1] for w in tw):raise ValueError('time windows')
    if len(dep)!=len(c['vehicle_capacities']) or any(not integer(x) for x in dep):raise ValueError('departure minutes')
    if not integer(c['return_deadline']) or any(x>c['return_deadline'] for x in dep):raise ValueError('return deadline')
    if any(not tw[0][0]<=x<=tw[0][1] for x in dep) or c['return_deadline']>tw[0][1]:raise ValueError('depot window')

def check(c,routes):
    validate_time(c)
    metrics,_=evaluate(c,routes)
    waits=None; schedule=[]
    if 'time_matrix' in c:
        waits=0
        n=len(c['node_ids']);tm=c['time_matrix'];sv=c['service_minutes'];tw=c['time_windows']
        if len(tm)!=n or any(len(r)!=n for r in tm) or len(sv)!=n or len(tw)!=n:raise ValueError('time dimensions')
        for r in tm:
            if any(type(v)is not int or v<0 for v in r):raise ValueError('time matrix integer')
        if any(type(v)is not int or v<0 for v in sv):raise ValueError('service integer')
        if any(len(w)!=2 or any(type(x)is not int for x in w) or w[0]>w[1] for w in tw):raise ValueError('invalid time window')
        if len(c['departure_minutes'])!=len(routes):raise ValueError('departures')
        for v,route in enumerate(routes):
            t=c['departure_minutes'][v]
            for a,b in zip(route,route[1:]):
                arrival=t+tm[a][b]
                if b==0:
                    if arrival>c['return_deadline']:raise ValueError('late return')
                    schedule.append([v,b,arrival,arrival,arrival,0]);continue
                start=max(arrival,tw[b][0]);wait=start-arrival
                if start>tw[b][1]:raise ValueError('late service start')
                t=start+sv[b];waits+=wait;schedule.append([v,b,arrival,start,t,wait])
    return dict(distance_m=metrics['total_distance_m'],vehicles_used=sum(len(r)>2 for r in routes),violations=0,waiting_minutes=waits,schedule=schedule)

def solve(c,seconds):
    validate_case(c);validate_time(c)
    if type(seconds)is not int or seconds<=0:raise ValueError('positive integer seconds required')
    import ortools
    from ortools.constraint_solver import pywrapcp as p,routing_enums_pb2 as e
    if ortools.__version__!=VERSION:raise ValueError('install pinned version '+VERSION)
    m=p.RoutingIndexManager(len(c['node_ids']),len(c['vehicle_capacities']),0);r=p.RoutingModel(m)
    cost=r.RegisterTransitCallback(lambda a,b:c['distance_matrix'][m.IndexToNode(a)][m.IndexToNode(b)]);r.SetArcCostEvaluatorOfAllVehicles(cost)
    demand=r.RegisterUnaryTransitCallback(lambda a:c['demands'][m.IndexToNode(a)])
    r.AddDimensionWithVehicleCapacity(demand,0,c['vehicle_capacities'],True,'Capacity')
    if 'time_matrix' in c:
        transit=r.RegisterTransitCallback(lambda a,b:c['service_minutes'][m.IndexToNode(a)]+c['time_matrix'][m.IndexToNode(a)][m.IndexToNode(b)])
        r.AddDimension(transit,1440,1440,False,'Time');dim=r.GetDimensionOrDie('Time')
        for n in c['node_ids'][1:]:dim.CumulVar(m.NodeToIndex(n)).SetRange(*c['time_windows'][n])
        for v,t in enumerate(c['departure_minutes']):
            dim.CumulVar(r.Start(v)).SetRange(t,t);dim.CumulVar(r.End(v)).SetRange(t,c['return_deadline'])
    par=p.DefaultRoutingSearchParameters();par.first_solution_strategy=e.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    par.local_search_metaheuristic=e.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH;par.time_limit.seconds=seconds
    t=time.perf_counter();a=r.SolveWithParameters(par);elapsed=time.perf_counter()-t
    result={'raw_status':r.status(),'status':STATUS.get(r.status(),'UNKNOWN'),'wall_seconds':round(elapsed,6),'routes':None,'objective_m':None,'metrics':None}
    if a:
        routes=[]
        for v in range(len(c['vehicle_capacities'])):
            ix=r.Start(v);route=[]
            while not r.IsEnd(ix):route.append(m.IndexToNode(ix));ix=a.Value(r.NextVar(ix))
            route.append(0);routes.append(route)
        result.update(routes=routes,objective_m=a.ObjectiveValue(),metrics=check(c,routes))
        if result['metrics']['distance_m']!=a.ObjectiveValue():raise ValueError('objective mismatch')
    result['independent_infeasibility_certificate']='total_demand_exceeds_total_capacity' if sum(c['demands'])>sum(c['vehicle_capacities']) else None
    return result

def audit(record,c,seconds):
    validate_case(c);validate_time(c)
    expected={'ortools_version':VERSION,'first_solution':'PATH_CHEAPEST_ARC','local_search':'GUIDED_LOCAL_SEARCH','optimality_claim':False,'capacity_box':c['vehicle_capacities']}
    if any(record.get(k)!=v for k,v in expected.items()) or record.get('optimality_claim') is not False:raise ValueError('fixed config mismatch')
    raw=record.get('raw_status');wall=record.get('wall_seconds')
    if type(raw)is not int or raw not in STATUS or record.get('status')!=STATUS[raw]:raise ValueError('status mapping mismatch')
    if type(wall) not in (int,float) or not math.isfinite(wall) or wall<0:raise ValueError('bad wall time')
    if (record['routes'] is not None)!=(raw in (1,2,7)):raise ValueError('status/route contradiction')
    if record['input_sha256']!=digest(c) or record['time_limit_seconds']!=seconds:raise ValueError('input/config mismatch')
    if record['routes'] is not None:
        metrics=check(c,record['routes'])
        if metrics!=record['metrics'] or metrics['distance_m']!=record['objective_m']:raise ValueError('stored metrics mismatch')
    elif record['metrics'] is not None or record['objective_m'] is not None:raise ValueError('no solution must use null')
    cert='total_demand_exceeds_total_capacity' if sum(c['demands'])>sum(c['vehicle_capacities']) else None
    if record['independent_infeasibility_certificate']!=cert:raise ValueError('bad certificate')
    return True

def run(out,generate=False):
    out.mkdir(parents=True,exist_ok=True);results=[]
    for key,c,seconds,group in scenarios():
        if generate:
            rec=solve(c,seconds);rec.update(id=key,group=group,input_sha256=digest(c),time_limit_seconds=seconds,capacity_box=c['vehicle_capacities'],ortools_version=VERSION,python_version=platform.python_version(),first_solution='PATH_CHEAPEST_ARC',local_search='GUIDED_LOCAL_SEARCH',optimality_claim=False)
            dump(out/(key+'.json'),rec)
        else:rec=read(ROOT/'outputs'/(key+'.json'))
        if rec.get('id')!=key or rec.get('group')!=group:raise ValueError('scenario identity mismatch')
        audit(rec,c,seconds);results.append(rec)
    rows=[]
    for r in results:
        m=r['metrics'] or {};rows.append(dict(id=r['id'],capacity=r['capacity_box'][0],limit_seconds=r['time_limit_seconds'],status=r['status'],distance_m=m.get('distance_m'),vehicles_used=m.get('vehicles_used'),wall_seconds=r['wall_seconds'],violations=m.get('violations'),waiting_minutes=m.get('waiting_minutes'),certificate=r['independent_infeasibility_certificate']))
    with (out/'comparison.csv').open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
    dump(out/'comparison.json',rows);return rows
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--solve',action='store_true');p.add_argument('--output-dir',type=Path,default=ROOT/'replay');a=p.parse_args()
    if a.output_dir.resolve()==(ROOT/'outputs').resolve():p.error('preserve published evidence; choose another output dir')
    print(json.dumps(run(a.output_dir,a.solve),ensure_ascii=False,indent=2))
