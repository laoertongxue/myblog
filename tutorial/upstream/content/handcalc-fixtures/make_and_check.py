"""标准库即可运行；全部模拟，不联网。生成各专项手算CSV并校验答案。"""
import csv, json, math, pathlib
root=pathlib.Path(__file__).parent
rows={
 'probabilities.csv':(['id','p','actual'],[['A',.8,1],['B',.2,0],['C',.6,0],['D',.4,1]]),
 'presale.csv':(['day','risk_start','cancel','ship'],[[1,100,10,20],[2,70,7,0]]),
 'restock.csv':(['ship_day','shipped','return_p','good_p','lag_days','lag_p','target_day'],[[8,100,.2,.8,2,.4,10],[7,50,.2,.8,3,.6,10]]),
 'cod_inventory.csv':(['step','qty_change','meaning'],[['ship',-100,'all physical shipments leave'],['qualified_restock',18,'20 refused times 90 percent good'],['damaged',0,'2 damaged are not sellable']]),
 'leadtime_scenarios.csv':(['scenario','supplier_A_days','supplier_B_days'],[[1,4,2],[2,4,4],[3,4,4],[4,4,6]]),
 'cross_elasticity.csv':(['outcome_sku','changed_price_sku','price_change_fraction','demand_change_fraction'],[['B','A',.1,.05],['C','A',.1,-.03]]),
 'intermittent.csv':(['week','demand'],[[i+1,v] for i,v in enumerate([0,4,0,0,8,0,0,0])]),
 'newsvendor.csv':(['demand','probability','underage_cost','overage_cost'],[[d,.25,6,2] for d in [80,100,120,140]])
}
paths=[]
for p1 in [10,8]:
 for p2 in [10,8]:
  inv=10;s1=min(4 if p1==10 else 7,inv);inv-=s1;s2=min(4 if p2==10 else 7,inv);inv-=s2
  paths.append([p1,p2,s1,s2,inv,p1*s1+p2*s2])
rows['pricing_paths.csv']=(['price_1','price_2','sales_1','sales_2','end_inventory','revenue'],paths)
for name,(headers,records) in rows.items():
 with (root/name).open('w',newline='',encoding='utf-8-sig') as f:
  w=csv.writer(f);w.writerow(headers);w.writerows(records)
assert math.isclose(sum((r[1]-r[2])**2 for r in rows['probabilities.csv'][1])/4,.2)
assert math.isclose((1-.1)*(1-.1),.81)
assert math.isclose((1+8*.1)/(2+8),.18)
assert math.isclose(80*.54/.72,60)
assert math.isclose(sum(r[1]*r[2]*r[3]*r[5] for r in rows['restock.csv'][1]),11.2)
assert [r[-1] for r in paths]==[80,88,86,80]
assert round(1.645*math.sqrt(116),2)==17.72
assert [sum(.25*(6*max(d-q,0)+2*max(q-d,0)) for d in [80,100,120,140]) for q in [100,120,140]]==[100,60,60]
report={'status':'passed','assertions':8,'datasets':len(rows),'data':'simulated','rounding':'display only; compute with full precision'}
(root/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(report)
