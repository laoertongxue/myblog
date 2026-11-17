"""Validation/evaluation reused from D21, independent of OR-Tools internals.
Pure delivery, one trip per vehicle, one service per customer; standard library only.
"""
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
    if 'time_matrix' not in c:  # D23 supplies explicit matrices, no grid metadata.
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
