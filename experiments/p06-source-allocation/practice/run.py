#!/usr/bin/env python3
"""有限单期情景枚举。只用 Python 标准库，概率和成本精确计算。"""
import argparse, csv, hashlib, json
from datetime import datetime
from fractions import Fraction
from itertools import product
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE_NAMES = ('purchase', 'transfer', 'production')

def integer(v, label, positive=False):
    if type(v) is not int or v < (1 if positive else 0):
        raise ValueError(f'{label}: 必须为{"正" if positive else "非负"}整数，布尔值不是数量')
    return v

def fraction(v, label, positive=False):
    if type(v) not in (int, str):
        raise ValueError(f'{label}: 用整数或精确十进制/分数字符串，不接受浮点或布尔值')
    try: f = Fraction(v)
    except (ValueError, ZeroDivisionError) as e: raise ValueError(f'{label}: 无效精确数值') from e
    if f < 0 or (positive and f == 0): raise ValueError(f'{label}: 数值超出范围')
    return f

def timestamp(v, label):
    if not isinstance(v, str): raise ValueError(f'{label}: 需要带时区ISO时间')
    try: dt = datetime.fromisoformat(v)
    except ValueError as e: raise ValueError(f'{label}: 无效时间') from e
    if dt.utcoffset() is None: raise ValueError(f'{label}: 时间必须有时区')
    return dt

def require_keys(obj, keys, label):
    if not isinstance(obj, dict) or set(obj) != set(keys):
        raise ValueError(f'{label}: 字段必须恰为 {sorted(keys)}')

def validate(c):
    require_keys(c, ('case_id','title','unit','decision_at','deadline','known_at','batch','receive_capacity','shortage_cost','surplus_cost','scenarios',*SOURCE_NAMES), 'case')
    for k in ('case_id','title','unit'):
        if not isinstance(c[k],str) or not c[k].strip(): raise ValueError(f'{k}: 不能为空')
    if c['case_id'] not in ('hewei','apparel'): raise ValueError('case_id: 只支持本教学的两案例')
    if c['unit'] != {'hewei':'kg','apparel':'piece'}[c['case_id']]: raise ValueError('unit: 与案例单位不符')
    start=timestamp(c['decision_at'],'decision_at'); end=timestamp(c['deadline'],'deadline')
    if end <= start: raise ValueError('deadline: 必须晚于决策时间')
    if timestamp(c['known_at'],'known_at') > start: raise ValueError('known_at: 不得使用决策后的输入版本')
    b=integer(c['batch'],'batch',True); integer(c['receive_capacity'],'receive_capacity')
    fraction(c['shortage_cost'],'shortage_cost'); fraction(c['surplus_cost'],'surplus_cost')
    ss=c['scenarios']
    if not isinstance(ss,list) or not ss: raise ValueError('scenarios: 不能为空')
    names=set(); probs=[]
    for s in ss:
        require_keys(s,('name','demand','probability'),'scenario')
        if not isinstance(s['name'],str) or not s['name'].strip() or s['name'] in names: raise ValueError('scenario: 名称不能为空或重复')
        names.add(s['name']); integer(s['demand'],'demand'); probs.append(fraction(s['probability'],'probability',True))
    if sum(probs) != 1: raise ValueError('probability: 概率必须精确合计为1')
    for name in SOURCE_NAMES:
        s=c[name]; extra={'purchase':['capacity'],'transfer':['donor_stock','donor_reserve'],'production':['capacity','material_available','material_per_unit']}[name]
        require_keys(s,(*extra,'unit_cost','fixed_cost','arrival_at'), name)
        for k in extra: integer(s[k],f'{name}.{k}',k=='material_per_unit')
        for k in ('unit_cost','fixed_cost'): fraction(s[k],f'{name}.{k}')
        if timestamp(s['arrival_at'],f'{name}.arrival_at') < start: raise ValueError('arrival_at: 必须不早于决策；既有库存不属于新增来源')
    if c['transfer']['donor_reserve'] > c['transfer']['donor_stock']: raise ValueError('donor_reserve: 不能超过捐出方库存')
    caps=source_caps(c)
    if (caps[0]//b+1)*(caps[1]//b+1)*(caps[2]//b+1)>100000: raise ValueError('候选数量超过本教学枚举上限100000')
    return c

def source_caps(c):
    raw=(c['purchase']['capacity'], c['transfer']['donor_stock']-c['transfer']['donor_reserve'], min(c['production']['capacity'],c['production']['material_available']//c['production']['material_per_unit']))
    end=timestamp(c['deadline'],'deadline')
    return tuple(min(n,c['receive_capacity']) if timestamp(c[k]['arrival_at'],k)<=end else 0 for k,n in zip(SOURCE_NAMES,raw))

def evaluate(c, plan):
    """一个事前固定方案在全部情景下评价，不在情景内部重选来源。"""
    validate(c)
    if not isinstance(plan,(tuple,list)) or len(plan)!=3: raise ValueError('plan: 需要采购、调拨、生产三个量')
    b=c['batch']; caps=source_caps(c)
    for k,q,cap in zip(SOURCE_NAMES,plan,caps):
        integer(q,k)
        if q%b or q>cap: raise ValueError('plan: 数量不满足批量/来源上界')
    total=sum(plan)
    if total>c['receive_capacity']: raise ValueError('plan: 超过接收容量')
    supply=sum(fraction(c[k]['unit_cost'],k)*q+(fraction(c[k]['fixed_cost'],k) if q else 0) for k,q in zip(SOURCE_NAMES,plan))
    rows=[]
    for s in c['scenarios']:
        loss=max(s['demand']-total,0); left=max(total-s['demand'],0)
        cost=supply+fraction(c['shortage_cost'],'shortage')*loss+fraction(c['surplus_cost'],'surplus')*left
        rows.append(dict(name=s['name'],probability=fraction(s['probability'],'p'),demand=s['demand'],shortage=loss,surplus=left,total_cost=cost))
    return dict(plan=tuple(plan),quantity=total,supply_cost=supply,expected_cost=sum(s['probability']*s['total_cost'] for s in rows),expected_shortage=sum(s['probability']*s['shortage'] for s in rows),expected_surplus=sum(s['probability']*s['surplus'] for s in rows),scenarios=rows)

def enumerate_plans(c):
    validate(c)
    ranges=[range(0,cap+1,c['batch']) for cap in source_caps(c)]
    return [evaluate(c,p) for p in product(*ranges) if sum(p)<=c['receive_capacity']]

def choose(rows, demand_floor=0):
    feasible=[r for r in rows if r['quantity']>=demand_floor]
    max_reachable=max((r['quantity'] for r in rows), default=0)
    if not feasible: return {'status':'INFEASIBLE','all_optimal_plans':[],'selected':None,'required_quantity':demand_floor,'max_feasible_quantity':max_reachable,'reason':f'要求总量至少{demand_floor}，本模型枚举的最大可达总量仅{max_reachable}；详见上界说明。这不是最小冲突集合诊断。'}
    best=min(r['expected_cost'] for r in feasible)
    ties=sorted([r for r in feasible if r['expected_cost']==best],key=lambda r:r['plan'])
    return {'status':'OPTIMAL_IN_ENUMERATED_MODEL','all_optimal_plans':[r['plan'] for r in ties], 'selected':ties[0], 'required_quantity':demand_floor,'max_feasible_quantity':max_reachable}

def input_record(c):
    canonical=json.dumps(c,ensure_ascii=False,sort_keys=True,separators=(',',':'))
    return {'input_snapshot':json.loads(canonical),'input_sha256':hashlib.sha256(canonical.encode('utf-8')).hexdigest(),'hash_encoding':'UTF-8 JSON, ensure_ascii=False, sort_keys=True, separators=(comma,colon), no trailing newline'}

def solve(c):
    rows=enumerate_plans(c)
    return dict(**input_record(c),case_id=c['case_id'],unit=c['unit'],candidate_count=len(rows),effective_caps=source_caps(c),bound_explanation={'receive_capacity':c['receive_capacity'],'batch':c['batch'],'purchase_capacity':c['purchase']['capacity'],'donor_stock':c['transfer']['donor_stock'],'donor_reserve':c['transfer']['donor_reserve'],'machine_capacity':c['production']['capacity'],'material_supported_quantity':c['production']['material_available']//c['production']['material_per_unit'],'timely_sources':{k:timestamp(c[k]['arrival_at'],k)<=timestamp(c['deadline'],'deadline') for k in SOURCE_NAMES},'note':'effective_caps已按及时性与接收容量过滤；再按批量枚举并检查合计容量。上述是本模型上界说明，不是通用最小冲突诊断。'},tie_rule='按(采购量,调拨量,生产量)字典序最小；不代表额外业务偏好',expected=choose(rows),high_service=choose(rows,max(s['demand'] for s in c['scenarios'])))

def serial(x):
    if isinstance(x,Fraction): return str(x)
    if isinstance(x,dict): return {k:serial(v) for k,v in x.items()}
    if isinstance(x,(list,tuple)): return [serial(v) for v in x]
    return x

def dump(path,x): path.write_text(json.dumps(serial(x),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def run(input_dir,out_dir):
    # 先完整验证和计算所有输入，再开始写文件，避免输入错误留下半套新结果。
    computed=[]
    for name in ('hewei','apparel'):
        c=json.loads((input_dir/f'{name}.json').read_text(encoding='utf-8'))
        if c.get('case_id') != name: raise ValueError(f'{name}.json的case_id必须为{name}')
        rows=enumerate_plans(c); computed.append((name,rows,solve(c)))
    h=json.loads((input_dir/'counterexample.json').read_text(encoding='utf-8'))
    validate(h)
    def probe(plan):
        try: return {'status':'FEASIBLE','evaluation':evaluate(h,plan)}
        except ValueError as error: return {'status':'INFEASIBLE','evaluation':None,'reason':str(error)}
    counter={**input_record(h),'note':'counterexample.json为独立确定缺口手算诊断输入，不跟随hewei.json修改；不是看完主情景后改方案',
             'cheap_unit_first':probe((0,10,0)), 'all_purchase':probe((10,0,0)), 'enumeration':solve(h)['expected']}
    out_dir.mkdir(parents=True,exist_ok=True)
    for name,rows,result in computed:
        dump(out_dir/f'{name}_result.json',result)
        with (out_dir/f'{name}_candidates.csv').open('w',encoding='utf-8',newline='') as f:
            w=csv.writer(f,lineterminator='\n');w.writerow(['purchase','transfer','production','quantity','supply_cost','expected_cost','expected_shortage','expected_surplus'])
            for r in rows:w.writerow([*r['plan'],r['quantity'],str(r['supply_cost']),str(r['expected_cost']),str(r['expected_shortage']),str(r['expected_surplus'])])
        with (out_dir/f'{name}_candidate_scenarios.csv').open('w',encoding='utf-8',newline='') as f:
            w=csv.writer(f,lineterminator='\n');w.writerow(['purchase','transfer','production','scenario','probability','demand','quantity','shortage','surplus','supply_cost','total_cost','weighted_cost'])
            for r in rows:
                for scenario in r['scenarios']:
                    w.writerow([*r['plan'],scenario['name'],str(scenario['probability']),scenario['demand'],r['quantity'],scenario['shortage'],scenario['surplus'],str(r['supply_cost']),str(scenario['total_cost']),str(scenario['probability']*scenario['total_cost'])])
    dump(out_dir/'greedy_counterexample.json',counter)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--input-dir',type=Path,default=ROOT/'inputs');p.add_argument('--output-dir',type=Path,default=ROOT/'outputs');a=p.parse_args();run(a.input_dir,a.output_dir)
