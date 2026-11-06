"""Read-only validation of synthetic course artifacts.

No output artifacts are written. --self-test mutates disposable copies in the
system temporary directory and requires every corrupt copy to be rejected.
The expected hazards, MILP constraints and calculations are rebuilt here;
JSON, CSV and Markdown are evidence to check, never the source of expected values.
"""
from pathlib import Path
from math import sqrt, log, exp, ceil, isfinite
from itertools import product
from functools import lru_cache
import argparse
import csv
import hashlib
import json
import shutil
import tempfile

FILES = (
    'forecast-missing-planning-math.md',
    'forecast-planning-60day.json',
    'forecast-planning-60day.csv',
    'forecast-planning-milp.csv',
)
CURVE_FIELDS = ['day', 'natural_hazard', 'start_expected',
                'natural_cancels_expected', 'forced_cancels_expected',
                'active_end_expected', 'natural_cumulative_rate']
POLICY = 'Force close all remaining orders at start of day 60.'
PROVENANCE = 'All inputs are synthetic teaching assumptions. Not measured business results.'

class ValidationError(RuntimeError):
    pass

def require(ok, message):
    if not ok:
        raise ValidationError(message)

def near(actual, expected, label, tol=1e-8):
    require(type(actual) in (int, float), f'{label}: not a number')
    require(isfinite(actual), f'{label}: non-finite number')
    require(abs(actual-expected) <= tol, f'{label}: got {actual}, expected {expected}')

def snapshots(root):
    result = {}
    for name in FILES:
        path = root/name
        require(path.is_file(), f'missing file: {path}')
        result[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result

def expected_curve():
    # Independent reconstruction from the manuscript's fixed teaching schedule.
    early = {1:.18, 2:.037, 3:.033, 4:.03, 5:.027, 6:.023, 7:.02}
    balance = 1000.0
    out = []
    for day in range(1, 61):
        start = balance
        if day == 60:
            hazard, natural, forced, balance = None, 0.0, start, 0.0
            cumulative = 1-start/1000
        else:
            if day <= 7: hazard = early[day]
            elif day <= 14: hazard = .015
            elif day <= 30: hazard = .009
            elif day <= 45: hazard = .005
            else: hazard = .003
            natural, forced = start*hazard, 0.0
            balance = start-natural
            cumulative = 1-balance/1000
        out.append(dict(day=day, natural_hazard=hazard, start_expected=start,
                        natural_cancels_expected=natural, forced_cancels_expected=forced,
                        active_end_expected=balance, natural_cumulative_rate=cumulative))
    return out

def expected_milp(warehouse=64):
    # Enumeration derives every quantity and objective, without reading a CSV.
    out=[]
    for a in range(7):
        for b in range(7):
            if a==1 or b==1: continue
            qa,qb=6*a,4*b
            volume=2*qa+3*qb
            trucks=ceil(volume/36)
            if volume>warehouse or trucks>2: continue
            short_a,short_b=max(17-qa,0),max(11-qb,0)
            extra_a,extra_b=max(qa-17,0),max(qb-11,0)
            cost=8*short_a+6*short_b+extra_a+extra_b+3*(a>0)+3*(b>0)+12*trucks
            out.append(dict(a_boxes=a,b_boxes=b,a_units=qa,b_units=qb,liters=volume,
                            trucks=trucks,a_short=short_a,b_short=short_b,
                            a_excess=extra_a,b_excess=extra_b,cost=cost))
    return out

def load_json(path):
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError) as exc:
        raise ValidationError(f'cannot read JSON {path.name}: {exc}') from exc

def load_csv(path, fields):
    try:
        with path.open(newline='') as handle:
            reader=csv.DictReader(handle)
            require(reader.fieldnames==fields, f'{path.name}: wrong or missing CSV header')
            rows=list(reader)
    except OSError as exc:
        raise ValidationError(f'cannot read CSV {path.name}: {exc}') from exc
    for index,row in enumerate(rows):
        require(set(row)==set(fields), f'{path.name} row {index+1}: wrong field count')
        require(all(v is not None for v in row.values()), f'{path.name} row {index+1}: missing value')
    return rows

def csv_number(text, label, integer=False):
    try:
        value=int(text) if integer else float(text)
    except (ValueError,TypeError) as exc:
        raise ValidationError(f'{label}: invalid numeric field {text!r}') from exc
    require(isfinite(value), f'{label}: non-finite value')
    return value

def check_curve_row(actual, expected, label):
    require(type(actual)==dict and set(actual)==set(CURVE_FIELDS), f'{label}: wrong fields')
    require(type(actual['day'])==int, f'{label}: day must be an integer')
    for key,want in expected.items():
        if want is None:
            require(actual[key] is None, f'{label}.{key}: day 60 natural hazard must be null')
        else:
            near(actual[key],want,f'{label}.{key}')
    near(actual['start_expected'], actual['natural_cancels_expected']+
         actual['forced_cancels_expected']+actual['active_end_expected'], label+' balance')

def table_block(text, start, end):
    require(text.count(start)==1, f'expected unique heading {start}')
    block=text.split(start,1)[1]
    require(end in block, f'missing end marker after {start}')
    block=block.split(end,1)[0]
    lines=[line.strip() for line in block.splitlines() if line.strip().startswith('|')]
    require(len(lines)>=2, f'missing table after {start}')
    return [[cell.strip().replace('**','') for cell in line.split('|')[1:-1]] for line in lines]

def validate_curve(root, text):
    expected=expected_curve()
    doc=load_json(root/'forecast-planning-60day.json')
    require(type(doc)==dict, 'curve JSON: expected object')
    require(type(doc.get('N'))==int and doc['N']==1000, 'curve JSON: N must be 1000')
    require(doc.get('provenance')==PROVENANCE, 'curve JSON: missing simulation provenance')
    require(doc.get('day60_policy')==POLICY, 'curve JSON: missing or wrong force-close policy')
    rows=doc.get('rows')
    require(type(rows)==list and len(rows)==60, 'curve JSON: exactly 60 rows required')
    for i,(actual,want) in enumerate(zip(rows,expected),1):
        check_curve_row(actual,want,f'JSON day {i}')
    near(sum(r['natural_cancels_expected']+r['forced_cancels_expected'] for r in rows),1000,'JSON total conservation')
    require(rows[-1]['natural_cancels_expected']==0 and rows[-1]['forced_cancels_expected']>0,
            'JSON day 60: event type must be forced closure, not natural cancellation')
    csv_rows=load_csv(root/'forecast-planning-60day.csv',CURVE_FIELDS)
    require(len(csv_rows)==60,'curve CSV: exactly 60 rows required')
    for i,(row,want) in enumerate(zip(csv_rows,expected),1):
        actual={}
        for field in CURVE_FIELDS:
            raw=row[field]
            if field=='natural_hazard' and want[field] is None:
                require(raw=='',f'CSV day {i}: natural hazard must be empty on day 60')
                actual[field]=None
            else:
                actual[field]=csv_number(raw,f'CSV day {i}.{field}',integer=(field=='day'))
        check_curve_row(actual,want,f'CSV day {i}')
    table=table_block(text,'### 5.5 全 60 天逐日核对表','核对结论：')
    require(table[0]==['天','自然日风险率','天初预计单数','自然取消单数','强关单数','天末活跃单数','累计自然取消'],
            'Markdown curve: wrong column names or units')
    require(len(table)==62,'Markdown curve: header, separator and all 60 data rows required')
    for i,(cells,want) in enumerate(zip(table[2:],expected),1):
        require(len(cells)==7,f'Markdown day {i}: expected seven cells')
        require(csv_number(cells[0],f'Markdown day {i}',integer=True)==i,f'Markdown day {i}: wrong order')
        if want['natural_hazard'] is None:
            require(cells[1]=='不适用','Markdown day 60: natural hazard must be not applicable')
        else:
            require(cells[1].endswith('%'),f'Markdown day {i}: missing hazard percent sign')
            near(csv_number(cells[1][:-1],f'Markdown day {i} hazard'),round(100*want['natural_hazard'],2),f'Markdown day {i} hazard')
        for col,key in [(2,'start_expected'),(3,'natural_cancels_expected'),(4,'forced_cancels_expected'),(5,'active_end_expected')]:
            near(csv_number(cells[col],f'Markdown day {i}.{key}'),round(want[key],3),f'Markdown day {i}.{key}')
        require(cells[6].endswith('%'),f'Markdown day {i}: missing cumulative percent sign')
        near(csv_number(cells[6][:-1],f'Markdown day {i} cumulative'),round(want['natural_cumulative_rate']*100,3),f'Markdown day {i} cumulative')

def validate_milp(root,text):
    expected=expected_milp()
    require(len(expected)==12,'independent MILP enumeration error')
    fields=list(expected[0])
    raw=load_csv(root/'forecast-planning-milp.csv',fields)
    require(len(raw)==12,'MILP CSV must contain all 12 feasible alternatives')
    actual=[{k:csv_number(r[k],f'MILP CSV row {i}.{k}',integer=True) for k in fields} for i,r in enumerate(raw,1)]
    key=lambda r:(r['a_boxes'],r['b_boxes'])
    require(sorted(actual,key=key)==sorted(expected,key=key),'MILP CSV differs from independent constraint/cost enumeration')
    table=table_block(text,'### 3.3 把全部可行方案列出来验证','最优方案逐步验算：')
    require(len(table)==14,'MILP Markdown must have header, separator and 12 alternatives')
    require(len(table[0])==len(fields),'MILP Markdown: wrong header width')
    for i,(cells,want) in enumerate(zip(table[2:],expected),1):
        require(len(cells)==len(fields),f'MILP Markdown row {i}: wrong width')
        got=[csv_number(c,f'MILP Markdown row {i}',integer=True) for c in cells]
        require(got==list(want.values()),f'MILP Markdown row {i}: differs from enumeration')
    best=min(expected,key=lambda r:r['cost'])
    require((best['a_units'],best['b_units'],best['cost'])==(18,8,49),'unexpected MILP best solution')
    wide=min(expected_milp(72),key=lambda r:r['cost'])
    require((wide['a_units'],wide['b_units'],wide['cost'])==(18,12,32),'capacity sensitivity failed')
    require(not any(r['a_short']==r['b_short']==0 for r in expected),'64-liter no-shortage condition should be infeasible')

def binomial_deviance(c,n,p):
    # R=0 has no information: caller must explicitly skip the row, not score it.
    if type(n)!=int or n<=0:
        raise ValueError('n must be a positive integer; skip zero-risk rows explicitly')
    if type(c)!=int or not 0<=c<=n:
        raise ValueError('c must be an integer in [0,n]')
    if type(p) not in (int,float) or not isfinite(p) or not 0<=p<=1:
        raise ValueError('p must be finite and in [0,1]')
    if (p==0 and c>0) or (p==1 and c<n):return float('inf')
    first=0. if c==0 else c*log(c/(n*p))
    second=0. if c==n else (n-c)*log((n-c)/(n*(1-p)))
    return 2*(first+second)

def numeric_checks(text):
    values=[1000*50,2000*15,1000*10,1000*5,600*5,1000*2]
    require(sum(values)==100000,'ABC sum')
    x=[20,40,20,40];mean=sum(x)/len(x)
    near(mean,30,'XYZ mean');near(sqrt(sum((v-mean)**2 for v in x)/4),10,'XYZ sd')
    actual=[100,120,80,100]
    wmape=lambda f:sum(abs(a-b) for a,b in zip(actual,f))/sum(actual)
    for f,w in [([100]*4,.1),([90,130,85,95],.075),([105,125,100,110],.1),([90,130,80,95],.0625)]:
        near(wmape(f),w,'FVA')
    near(binomial_deviance(20,100,.1),8.880601517376451,'deviance model A')
    near(binomial_deviance(20,100,.25),1.4004213294429988,'deviance model B')
    near(binomial_deviance(0,100,.1),21.07210313156527,'deviance zero events')
    require(binomial_deviance(0,100,0)==0 and binomial_deviance(100,100,1)==0,'deviance degenerate match')
    require(binomial_deviance(1,100,0)==float('inf'),'deviance impossible event')
    for args in [(0,0,.1),(1,100,-.1),(1.5,100,.2),(1,100,1.1),(1,2.5,.1),(True,100,.1),(1,100,float('nan'))]:
        try:binomial_deviance(*args)
        except ValueError:pass
        else:raise ValidationError(f'deviance accepted invalid input: {args}')
    near((20*.9**2+80*.1**2)/100,.17,'Brier')
    # Conditional-censoring counterexample, standardization and IPCW.
    near(1-5/60,11/12,'unadjusted survival counterexample')
    near(.5*(1-5/10)+.5*1,.75,'standardized survival')
    near(1-(5/0.2)/(10/0.2+50),.75,'IPCW survival')
    near(1-(10/0.4)/(20/0.4+50),.75,'IPCW sensitivity')
    eta=log(1/9)+log(2)*1+log(1.5)*1
    near(exp(eta)/(1+exp(eta)),.25,'expanded logit calculation')
    require('91.667%' in text and '85.714%' in text,'missing conditional-censoring exercises')
    # Independent physical stock conservation, including lead-time-one pipeline.
    central,a,b,pipeline=100,30,20,(10,0)
    totals=[central+a+b+sum(pipeline)];states=[(0,central,a,b,sum(pipeline),totals[-1])]
    for t,(supply,send_a,send_b,sale_a,sale_b) in enumerate([(40,25,15,20,10),(0,10,20,30,18),(0,0,0,12,20)],1):
        previous=totals[-1]
        central+=supply-send_a-send_b
        a+=pipeline[0]-sale_a;b+=pipeline[1]-sale_b
        pipeline=(send_a,send_b)
        total=central+a+b+sum(pipeline)
        require(min(central,a,b)>=0,'negative inventory in teaching example')
        near(total,previous+supply-sale_a-sale_b,f'network balance t={t}')
        totals.append(total);states.append((t,central,a,b,sum(pipeline),total))
    require(totals==[160,170,122,90],'stock total examples')
    require(states[2]==(2,70,15,7,30,122),'period two stock detail')
    curve=expected_curve()
    near(100*curve[13]['active_end_expected']/curve[6]['active_end_expected'],89.96086310076883,'conditional day7 to14')
    near(curve[58]['active_end_expected']*.8/.82,466.0778618462028,'day1 hazard sensitivity')
    for got,want in [(100*.9**-1.5,117.12139482105108),(80*.9**.6,75.09923146876555),(40*.9**-.3,41.284519897127595),(100*1.1**.4,103.886011825408),(1.65*sqrt(1300),59.491596045155816),(1.65*sqrt(2260),78.4401045384311),(1.65*sqrt(2600),84.13382197428095)]:
        near(got,want,'elasticity or pooling')
    prices=(10,6);demand={10:2,6:4}
    for salvage,expected in [(1,41),(-5,38)]:
        outcomes=[]
        for plan in product(prices,repeat=2):
            inv=5;revenue=0
            for price in plan:
                sold=min(inv,demand[price]);inv-=sold;revenue+=price*sold
            outcomes.append(revenue+salvage*inv)
        @lru_cache(None)
        def value(t,inv):
            if t==3:return salvage*inv
            return max(price*min(inv,demand[price])+value(t+1,inv-min(inv,demand[price])) for price in prices)
        require(value(1,5)==expected==max(outcomes),'DP versus enumeration')
    require(.5*min(2,0)+.5*min(2,4)==1,'stochastic sales min expectation')

def validate(root):
    before=snapshots(root)
    text=(root/FILES[0]).read_text()
    require(text.count('\n## 第')==8,'manuscript must contain all eight chapters')
    validate_curve(root,text)
    validate_milp(root,text)
    numeric_checks(text)
    require(snapshots(root)==before,'validator changed an input file')
    return before

def mutation_tests(root):
    original=snapshots(root)
    def edit_json(folder, change):
        path=folder/'forecast-planning-60day.json';doc=json.loads(path.read_text())
        change(doc);path.write_text(json.dumps(doc))
    def move_forced_to_natural(folder):
        def change(doc):
            last=doc['rows'][-1]
            last['natural_cancels_expected']=last['forced_cancels_expected']
            last['forced_cancels_expected']=0.
        edit_json(folder,change)
    def zero_day60(folder):
        def change(doc):
            doc['rows'][-1]['natural_cancels_expected']=0.
            doc['rows'][-1]['forced_cancels_expected']=0.
        edit_json(folder,change)
    def cumulative_99(folder):
        def change(doc):
            for row in doc['rows']:row['natural_cumulative_rate']=.99
        edit_json(folder,change)
    def empty_csv(folder):
        (folder/'forecast-planning-60day.csv').write_text('')
    def remove_59_md_rows(folder):
        path=folder/FILES[0];text=path.read_text()
        before,tail=text.split('### 5.5 全 60 天逐日核对表',1)
        block,after=tail.split('核对结论：',1)
        kept=[]
        for line in block.splitlines():
            cells=[x.strip() for x in line.split('|')[1:-1]] if line.strip().startswith('|') else []
            if len(cells)==7 and cells[0].isdigit() and 1<=int(cells[0])<=59:continue
            kept.append(line)
        path.write_text(before+'### 5.5 全 60 天逐日核对表'+'\n'.join(kept)+'\n核对结论：'+after)
    def corrupt_milp(folder):
        path=folder/'forecast-planning-milp.csv';rows=list(csv.DictReader(path.open()))
        rows[0]['cost']='0'
        with path.open('w',newline='') as handle:
            writer=csv.DictWriter(handle,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    def corrupt_csv_only(folder):
        path=folder/'forecast-planning-60day.csv';rows=list(csv.DictReader(path.open()))
        rows[5]['natural_cancels_expected']='0'
        with path.open('w',newline='') as handle:
            writer=csv.DictWriter(handle,fieldnames=CURVE_FIELDS);writer.writeheader();writer.writerows(rows)
    def corrupt_body_only(folder):
        path=folder/FILES[0];text=path.read_text()
        target='| 1 | 18.00% | 1000.000 | 180.000 | 0.000 | 820.000 | 18.000% |'
        require(target in text,'mutation target missing')
        path.write_text(text.replace(target,target.replace('18.000%','99.000%'),1))
    tests=[('day60 event-type swap',move_forced_to_natural),('day60 zeros',zero_day60),
           ('all cumulative rates 99%',cumulative_99),('empty CSV',empty_csv),
           ('first 59 Markdown days missing',remove_59_md_rows),('MILP input cost changed',corrupt_milp),
           ('CSV-only numeric corruption',corrupt_csv_only),('Markdown-only corruption',corrupt_body_only)]
    for name,mutate in tests:
        with tempfile.TemporaryDirectory(prefix='planning-validation-mutation-') as directory:
            folder=Path(directory)
            for filename in FILES:shutil.copyfile(root/filename,folder/filename)
            mutate(folder)
            mutated_before=snapshots(folder)
            try:validate(folder)
            except ValidationError as exc:
                print(f'EXPECTED FAIL: {name}: {exc}')
            else:raise ValidationError(f'false pass: mutation {name}')
            require(snapshots(folder)==mutated_before,'validation rewrote a corrupt input instead of rejecting it')
    require(snapshots(root)==original,'mutation tests changed original artifacts')
    return len(tests)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parent)
    parser.add_argument('--self-test',action='store_true')
    args=parser.parse_args()
    try:
        validate(args.root)
        print('PASS: read-only validation of independently reconstructed JSON/CSV/Markdown 60-day curve, full MILP, and numeric examples.')
        if args.self_test:
            count=mutation_tests(args.root)
            print(f'PASS: {count} corrupted temporary copies were rejected; original input hashes are unchanged.')
    except (ValidationError,OSError) as exc:
        parser.exit(1,f'FAIL: {exc}\n')

if __name__=='__main__':main()
