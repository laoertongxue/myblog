from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
import json
P=Path(__file__).parent; O=P/'delivery/images';O.mkdir(exist_ok=True)
font='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
plt.rcParams['font.family']=FontProperties(fname=font).get_name();plt.rcParams['axes.unicode_minus']=False
plt.rcParams.update({'font.size':13,'axes.spines.top':False,'axes.spines.right':False})
def save(fig,n):fig.savefig(O/n,dpi=100,facecolor='white');plt.close(fig)
f,ax=plt.subplots(figsize=(9,3.83));ax.axis('off');ax.set_xlim(0,1);ax.set_ylim(0,1);ax.text(.04,.89,'多数日子没有订单，偶尔一单很大',fontsize=22,weight='bold');ax.text(.04,.69,'供应链预测与计划 · 09 / 间歇需求',fontsize=13)
ax.plot([.06,.2,.32,.46,.58,.72,.85],[.18,.18,.53,.18,.18,.4,.18],color='black',marker='o');ax.text(.04,.02,'先辨认真正的零，再分开估计发生频率与正批量',fontsize=12);save(f,'01-cover.png')
f,ax=plt.subplots(figsize=(10,6));xs=list(range(9));ax.plot(xs,[100]*9,'k--',label='Croston：保持 100 件/周');ax.plot(xs,[100*.9**x for x in xs],'k-o',label='TSB：概率每周保留 90%');ax.set(xlabel='连续无订单周数',ylabel='平均需求率（件/周）',title='同为零尾部，不同方法作出不同响应');ax.legend();ax.annotate('第 4 周：65.61',xy=(4,65.61),xytext=(4.5,78),arrowprops={'arrowstyle':'->'});f.tight_layout();save(f,'02-zero-tail.png')
r=json.loads((P/'practice/results.json').read_text());f,axs=plt.subplots(1,2,figsize=(10,6));labels=['零预测','历史均值','Croston','SBA','TSB']
for ax,c,t,u in zip(axs,['apparel','hewei'],['匿名服装','禾味'],['件','kg']):
 vals=[x['window_mae'] for x in r[c]['test']];ax.bar(range(5),vals,color=['white']*5,edgecolor='black',hatch=['','//','','xx','..']);ax.set_xticks(range(5),labels,rotation=35);ax.set_title(t+'：测试窗口 MAE');ax.set_ylabel('5 天累计需求误差（'+u+'）')
 for i,v in enumerate(vals):ax.text(i,v+.02*max(vals),f'{v:.2f}',ha='center',fontsize=10)
 ax.set_ylim(0,max(vals)*1.23)
f.suptitle('两案例均在验证段选择 Croston（α = 0.1）\n测试成绩只报告，不反过来改选型',fontsize=15);f.tight_layout();save(f,'03-errors.png')
f,ax=plt.subplots(figsize=(10,6));ax.axis('off')
items=[('01  零值语义','真实零 / 缺货 / 停售 / 缺失'),('02  需求率估计','批量 ÷ 间隔，或概率 × 批量'),('03  冻结与检验','窗口误差、偏差，不只看日 MAE'),('04  供给计划','库存、交期、批量、效期另行约束')]
for i,(a,b) in enumerate(items):
 y=.87-i*.23;ax.text(.08,y,a,fontsize=18,weight='bold');ax.text(.08,y-.09,b,fontsize=15)
 if i<3:ax.annotate('',xy=(.8,y-.16),xytext=(.8,y-.02),arrowprops={'arrowstyle':'->'})
f.tight_layout();save(f,'04-workflow.png')
