"""D21 synthetic routing baseline. Python >=3.10, standard library only."""
from __future__ import annotations
import argparse, csv, heapq, json
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def integer(x, label, low=0, high=10**9):
    if type(x) is not int or not low <= x <= high:
        raise ValueError(f'{label}: expected integer in [{low}, {high}]')
    return x

def validate_case(c):
    if not isinstance(c, dict): raise ValueError('case must be object')
    if not isinstance(c.get('case_id'),str) or not c['case_id'].strip(): raise ValueError('case_id required')
    if c.get('distance_unit') != 'm' or c.get('load_unit') != 'box':
        raise ValueError('units must be m and box')
    if c.get('simulated') is not True: raise ValueError('simulation marker required')
    if c.get('depot') != 0 or type(c.get('depot')) is not int: raise ValueError('depot must be integer 0')
    ids=c.get('node_ids'); matrix=c.get('distance_matrix'); demands=c.get('demands')
    if not isinstance(ids,list) or not 2<=len(ids)<=100 or any(type(x) is not int for x in ids) or ids != list(range(len(ids))):
        raise ValueError('node_ids must be contiguous integers 0..n-1, 2<=n<=100')
    n=len(ids)
    if not isinstance(matrix,list) or len(matrix)!=n or any(not isinstance(row,list) or len(row)!=n for row in matrix): raise ValueError('matrix shape mismatch')
    for i,row in enumerate(matrix):
        for j,x in enumerate(row):
            integer(x,'distance')
            if i==j and x!=0: raise ValueError('diagonal must be zero')
            if i!=j and x==0: raise ValueError('distinct fixture nodes must have positive distance')
    if any(matrix[i][j]!=matrix[j][i] for i in ids for j in ids): raise ValueError('this fixture requires symmetry')
    if any(matrix[i][j]>matrix[i][k]+matrix[k][j] for i in ids for j in ids for k in ids): raise ValueError('this fixture requires triangle inequality')
    coords=c.get('coordinates_grid'); step=c.get('grid_step_m')
    integer(step,'grid_step_m',1)
    if not isinstance(coords,list) or len(coords)!=n or any(not isinstance(point,list) or len(point)!=2 for point in coords):
        raise ValueError('coordinates_grid must contain one integer [x,y] per node')
    for point in coords:
        for v in point: integer(v,'coordinate',-10**6,10**6)
    if any(matrix[i][j]!=step*sum(abs(coords[i][k]-coords[j][k]) for k in (0,1)) for i in ids for j in ids):
        raise ValueError('matrix differs from coordinate Manhattan distances')
    if not isinstance(demands,list) or len(demands)!=n: raise ValueError('demands shape mismatch')
    for d in demands: integer(d,'demand')
    if demands[0]!=0: raise ValueError('depot demand must be zero')
    caps=c.get('vehicle_capacities')
    if not isinstance(caps,list) or not 1<=len(caps)<=100: raise ValueError('capacities required')
    for cap in caps: integer(cap,'capacity',1)
    return c

def validate_routes(c,routes):
    validate_case(c)
    if not isinstance(routes,list) or len(routes)!=len(c['vehicle_capacities']): raise ValueError('one route per vehicle required')
    served=[]
    for route,cap in zip(routes,c['vehicle_capacities']):
        if not isinstance(route,list) or len(route)<2: raise ValueError('route must start/end at depot')
        for node in route: integer(node,'node',0,len(c['node_ids'])-1)
        if route[0]!=0 or route[-1]!=0: raise ValueError('route must start/end at depot')
        if 0 in route[1:-1]: raise ValueError('intermediate depot not allowed in single-trip model')
        customers=route[1:-1]; served.extend(customers)
        if sum(c['demands'][x] for x in customers)>cap: raise ValueError('capacity exceeded')
    if sorted(served)!=c['node_ids'][1:]: raise ValueError('customers must be served exactly once')
    return True

def evaluate(c,routes):
    validate_routes(c,routes)
    legs=[]; summaries=[]
    for v,route in enumerate(routes):
        initial=sum(c['demands'][x] for x in route[1:-1]); remaining=initial; distance=0
        for step,(a,b) in enumerate(zip(route,route[1:]),1):
            d=c['distance_matrix'][a][b]; distance+=d
            delivered=c['demands'][b] if b else 0
            before=remaining; remaining-=delivered
            legs.append({'case':c['case_id'],'vehicle':v+1,'leg':step,'from':a,'to':b,'distance_m':d,'cumulative_distance_m':distance,'departure_load_box':before,'delivered_box':delivered,'arrival_remaining_box':remaining})
        summaries.append({'vehicle':v+1,'route':route,'distance_m':distance,'initial_load_box':initial,'capacity_box':c['vehicle_capacities'][v],'remaining_box':remaining})
    return {'case_id':c['case_id'],'simulated':True,'optimality_claim':False,'routes':summaries,'total_distance_m':sum(x['distance_m'] for x in summaries),'total_delivered_box':sum(c['demands']),'all_customers_once':True},legs

def shortest_path(g,start,target):
    if not isinstance(g,list) or not 1<=len(g)<=100 or any(not isinstance(r,list) or len(r)!=len(g) for r in g): raise ValueError('graph must be square')
    n=len(g); integer(start,'start',0,n-1); integer(target,'target',0,n-1)
    for i,row in enumerate(g):
        for j,w in enumerate(row):
            if w is not None: integer(w,'edge')
            if i==j and w!=0: raise ValueError('graph diagonal must be zero')
    dist=[None]*n; paths=[None]*n; dist[start]=0; paths[start]=[start]; queue=[(0,start)]
    settled=[]
    while queue:
        d,u=heapq.heappop(queue)
        if d!=dist[u]: continue
        settled.append({'node':u,'distance':d,'path':paths[u]})
        if u==target: return {'distance_m':d,'path':paths[u],'settled':settled}
        for v,w in enumerate(g[u]):
            if v==u or w is None: continue
            nd=d+w
            if dist[v] is None or nd<dist[v]:
                dist[v]=nd; paths[v]=paths[u]+[v]; heapq.heappush(queue,(nd,v))
    return {'distance_m':None,'path':[],'settled':settled}

def write_json(path,data):
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def run(input_dir=ROOT/'inputs',output_dir=ROOT/'outputs'):
    input_dir=Path(input_dir); output_dir=Path(output_dir)
    if input_dir.resolve()==output_dir.resolve() or input_dir.resolve() in output_dir.resolve().parents: raise ValueError('outputs must not be inside inputs')
    results=[]; all_legs=[]
    for name in ['hewei_extension.json','apparel.json']:
        c=json.loads((input_dir/name).read_text(encoding='utf-8'))
        result,legs=evaluate(c,c['baseline_routes']); results.append(result); all_legs.extend(legs)
    graph=json.loads((input_dir/'shortest_path.json').read_text(encoding='utf-8'))
    if not isinstance(graph,dict): raise ValueError('shortest graph must be object')
    if graph.get('distance_unit') != 'm': raise ValueError('shortest graph unit must be m')
    shortest=shortest_path(graph['matrix'],graph['start'],graph['target'])
    output_dir.mkdir(parents=True,exist_ok=True)
    write_json(output_dir/'summary.json',results); write_json(output_dir/'shortest_path_result.json',shortest)
    with (output_dir/'route_legs.csv').open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(all_legs[0]),lineterminator='\n'); w.writeheader(); w.writerows(all_legs)
    return results

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--input-dir',type=Path,default=ROOT/'inputs'); p.add_argument('--output-dir',type=Path,default=ROOT/'outputs'); a=p.parse_args()
    try: print(json.dumps(run(a.input_dir,a.output_dir),ensure_ascii=False,indent=2))
    except (ValueError,KeyError,TypeError,OSError) as e: p.exit(2,f'输入或文件错误：{e}\n')
