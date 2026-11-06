"""Generate NEW synthetic examples only into an explicitly named, absent directory.

This is separate from validation. It never overwrites a directory or input file.
Example: python generate_planning_examples.py --out-dir /tmp/new-planning-demo
The course Markdown is not regenerated or edited by this tool.
"""
import argparse,csv,json,math
from pathlib import Path

def generate(destination):
    destination.mkdir(parents=True,exist_ok=False)
    rates=[.18,.037,.033,.03,.027,.023,.02]+[.015]*7+[.009]*16+[.005]*15+[.003]*14
    active=1000.;curve=[]
    for t,rate in enumerate(rates,1):
        before=active;natural=before*rate;active-=natural
        curve.append(dict(day=t,natural_hazard=rate,start_expected=before,natural_cancels_expected=natural,forced_cancels_expected=0.,active_end_expected=active,natural_cumulative_rate=1-active/1000))
    curve.append(dict(day=60,natural_hazard=None,start_expected=active,natural_cancels_expected=0.,forced_cancels_expected=active,active_end_expected=0.,natural_cumulative_rate=1-active/1000))
    document={'provenance':'All inputs are synthetic teaching assumptions. Not measured business results.','N':1000,'day60_policy':'Force close all remaining orders at start of day 60.','rows':curve}
    with (destination/'forecast-planning-60day.json').open('x') as f:json.dump(document,f,ensure_ascii=False,indent=2)
    with (destination/'forecast-planning-60day.csv').open('x',newline='') as f:
        w=csv.DictWriter(f,fieldnames=curve[0]);w.writeheader();w.writerows(curve)
    plans=[]
    for a in [0,2,3,4,5]:
        for b in [0,2,3,4,5]:
            qa,qb=6*a,4*b;volume=12*(a+b);trucks=math.ceil((a+b)/3)
            if volume>64 or trucks>2:continue
            ua,ub=max(17-qa,0),max(11-qb,0);ea,eb=max(qa-17,0),max(qb-11,0)
            plans.append(dict(a_boxes=a,b_boxes=b,a_units=qa,b_units=qb,liters=volume,trucks=trucks,a_short=ua,b_short=ub,a_excess=ea,b_excess=eb,cost=8*ua+6*ub+ea+eb+3*(a>0)+3*(b>0)+12*trucks))
    with (destination/'forecast-planning-milp.csv').open('x',newline='') as f:
        w=csv.DictWriter(f,fieldnames=plans[0]);w.writeheader();w.writerows(plans)
    print(f'Created new synthetic data under {destination}; no existing files were edited.')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out-dir',type=Path,required=True)
    a=p.parse_args()
    try:generate(a.out_dir)
    except FileExistsError:p.exit(1,'Refusing to overwrite: choose a new, absent output directory.\n')
