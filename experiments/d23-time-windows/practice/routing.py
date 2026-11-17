"""D23 deterministic replay and OR-Tools adapter. All inputs are simulations."""
import json,time,copy,itertools,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def validate(c):
 n=len(c['node_ids']);v=len(c['vehicle_capacities'])
 assert c['node_ids']==list(range(n)) and c['depot']==0
 for k in ['distance_matrix','time_matrix']:
  m=c[k];assert len(m)==n and all(len(row)==n for row in m)
  assert all(type(x) is int and x>=0 for row in m for x in row)
  assert all(m[i][i]==0 for i in range(n))
 for k in ['demands','service_minutes']:
  assert len(c[k])==n and all(type(x) is int and x>=0 for x in c[k]) and c[k][0]==0
 assert len(c['time_windows'])==n
 assert all(len(w)==2 and all(type(x) is int and x>=0 for x in w) and w[0]<=w[1] for w in c['time_windows'])
 assert len(c['departure_minutes'])==v and all(type(x) is int and x>=0 for x in c['departure_minutes'])
 assert all(type(x) is int and x>0 for x in c['vehicle_capacities'])
 assert type(c['return_deadline']) is int and c['return_deadline']>=max(c['departure_minutes'])
 assert c['distance_unit']=='m' and c['load_unit']=='box' and c['time_unit']=='minute_after_midnight'

def check(c,routes):
 validate(c); errors=[];rows=[];dist=0;seen=[];used=0
 if len(routes)!=len(c['vehicle_capacities']):return {'feasible':False,'errors':['vehicle_count'],'distance_m':None,'rows':[]}
 for v,r in enumerate(routes):
  if len(r)<2 or r[0]!=0 or r[-1]!=0 or any(type(x) is not int or x<0 or x>=len(c['node_ids']) for x in r) or 0 in r[1:-1]:
   errors.append(f'route_shape_{v}');continue
  used+=bool(r[1:-1]);seen+=r[1:-1];load=sum(c['demands'][i] for i in r[1:-1])
  if load>c['vehicle_capacities'][v]:errors.append(f'capacity_{v}')
  leave=c['departure_minutes'][v]
  for seq,(a,b) in enumerate(zip(r,r[1:]),1):
   arrival=leave+c['time_matrix'][a][b];start=arrival if b==0 else max(arrival,c['time_windows'][b][0]);wait=start-arrival;leave=start+c['service_minutes'][b];dist+=c['distance_matrix'][a][b]
   if b and start>c['time_windows'][b][1]:errors.append(f'window_{v}_{b}')
   if not b and arrival>c['return_deadline']:errors.append(f'return_{v}')
   load-=c['demands'][b];rows.append(dict(vehicle=v,seq=seq,node=b,arrival=arrival,wait=wait,service_start=start,departure=leave,remaining_box=load))
 if sorted(seen)!=list(range(1,len(c['node_ids']))):errors.append('coverage')
 return dict(feasible=not errors,errors=errors,distance_m=dist,used_vehicles=used,rows=rows)

def solve(c,seconds=5):
 validate(c)
 assert type(seconds) is int and seconds>0
 import ortools
 from ortools.constraint_solver import pywrapcp,routing_enums_pb2
 m=pywrapcp.RoutingIndexManager(len(c['node_ids']),len(c['vehicle_capacities']),0);r=pywrapcp.RoutingModel(m)
 cost=r.RegisterTransitCallback(lambda a,b:c['distance_matrix'][m.IndexToNode(a)][m.IndexToNode(b)])
 r.SetArcCostEvaluatorOfAllVehicles(cost)
 dem=r.RegisterUnaryTransitCallback(lambda a:c['demands'][m.IndexToNode(a)])
 r.AddDimensionWithVehicleCapacity(dem,0,c['vehicle_capacities'],True,'Capacity')
 transit=r.RegisterTransitCallback(lambda a,b:c['service_minutes'][m.IndexToNode(a)]+c['time_matrix'][m.IndexToNode(a)][m.IndexToNode(b)])
 r.AddDimension(transit,c['return_deadline'],c['return_deadline'],False,'Time');td=r.GetDimensionOrDie('Time')
 for i in c['node_ids'][1:]:td.CumulVar(m.NodeToIndex(i)).SetRange(*c['time_windows'][i])
 for v,t in enumerate(c['departure_minutes']):
  td.CumulVar(r.Start(v)).SetRange(t,t);td.CumulVar(r.End(v)).SetRange(t,c['return_deadline'])
 p=pywrapcp.DefaultRoutingSearchParameters();p.first_solution_strategy=routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC;p.local_search_metaheuristic=routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH;p.time_limit.seconds=seconds
 t=time.perf_counter();a=r.SolveWithParameters(p);elapsed=time.perf_counter()-t
 out=dict(input_sha256=hashlib.sha256(json.dumps(c,sort_keys=True,ensure_ascii=False).encode()).hexdigest(),ortools_version=ortools.__version__,raw_status=r.status(),elapsed_seconds=elapsed,time_limit_seconds=seconds,first_solution='PATH_CHEAPEST_ARC',local_search='GUIDED_LOCAL_SEARCH',optimality_claim=False,routes=None)
 if a is None:return out
 routes=[]
 for v in range(len(c['vehicle_capacities'])):
  ix=r.Start(v);route=[]
  while not r.IsEnd(ix):route.append(m.IndexToNode(ix));ix=a.Value(r.NextVar(ix))
  routes.append(route+[0])
 audit=check(c,routes);assert audit['feasible'] and audit['distance_m']==a.ObjectiveValue()
 return dict(out,routes=routes,objective_m=a.ObjectiveValue(),audit=audit)

def audit_record(c,record):
 assert record['input_sha256']==hashlib.sha256(json.dumps(c,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
 assert record['optimality_claim'] is False
 assert record['ortools_version']=='9.14.6206'
 assert record['first_solution']=='PATH_CHEAPEST_ARC' and record['local_search']=='GUIDED_LOCAL_SEARCH'
 assert type(record['time_limit_seconds']) is int and record['time_limit_seconds']>0
 assert isinstance(record['elapsed_seconds'],(int,float)) and 0<=record['elapsed_seconds']<float('inf')
 assert record['routes'] is not None and record['raw_status'] in (1,2,7)
 assert record['baseline_audit']==check(c,c['baseline_routes'])
 assert record['enumeration_count']==len(enumerate_feasible(c))
 actual=check(c,record['routes']);assert actual['feasible'] and actual==record['audit'] and actual['distance_m']==record['objective_m']
 return actual

def tightened(c):
 c=copy.deepcopy(c);c['time_windows'][c['tightened_node']]=c['tightened_window'];return c

def enumerate_feasible(c):
 """Independent finite candidate generation; replay uses checker, not solver."""
 found=[]
 for p in itertools.permutations(c['node_ids'][1:]):
  for k in range(len(p)+1):
   routes=[[0,*p[:k],0],[0,*p[k:],0]];a=check(c,routes)
   if a['feasible']:found.append((a['distance_m'],routes))
 return sorted(found)

if __name__=='__main__':
 import csv,argparse
 p=argparse.ArgumentParser();p.add_argument('--solve',action='store_true');p.add_argument('--out',default='outputs');a=p.parse_args();out=Path(a.out)
 if a.solve and out.resolve()==(ROOT/'outputs').resolve():p.error('--solve requires a separate --out; preserve published evidence')
 out.mkdir(exist_ok=True,parents=True)
 if a.solve:
  for name in ['apparel','hewei_extension']:
   c=json.loads((ROOT/'inputs'/f'{name}.json').read_text())
   for variant,cc in [('base',c),('tightened',tightened(c))]:
    result=solve(cc);result['baseline_audit']=check(cc,c['baseline_routes']);result['enumeration_count']=len(enumerate_feasible(cc))
    (out/f'{name}_{variant}.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    if result['routes'] is None:continue
    with (out/f'{name}_{variant}_schedule.csv').open('w') as f:
     rows=result['audit']['rows'];w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 else:
  expected=[ROOT/'outputs'/f'{name}_{variant}.json' for name in ['apparel','hewei_extension'] for variant in ['base','tightened']]
  for f in expected:
   name=f.stem.removesuffix('_base').removesuffix('_tightened');c=json.loads((ROOT/'inputs'/f'{name}.json').read_text());c=tightened(c) if f.stem.endswith('tightened') else c;record=json.loads(f.read_text());audit_record(c,record)
  print('Published route replay passed')
