"""Rebuild five article illustrations; Python + matplotlib, separate from stdlib practice."""
from pathlib import Path
import csv, sys, os
os.environ.setdefault('MPLCONFIGDIR', '/tmp/p05-matplotlib')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyArrowPatch
from matplotlib.font_manager import FontProperties
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'images'
OUT.mkdir(parents=True, exist_ok=True)
FONT=FontProperties(fname='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc').get_name()
plt.rcParams.update({'font.family':FONT,'font.sans-serif':[FONT], 'axes.unicode_minus':False,'font.size':13,'svg.fonttype':'none','axes.spines.top':False,'axes.spines.right':False})
def canvas(w=11,h=6):
    fig,ax=plt.subplots(figsize=(w,h),dpi=100)
    return fig,ax
def save(fig,name):
    fig.savefig(OUT/(name+'.png'),dpi=100,facecolor='white')
    fig.savefig(OUT/(name+'.svg'),facecolor='white')
    plt.close(fig)
def frame(ax):
    ax.set(xlim=(0,100),ylim=(0,100));ax.axis('off')
def box(ax,x,y,w,h,title,body):
    ax.add_patch(Rectangle((x,y),w,h,facecolor='#f5f5f5',edgecolor='black',lw=1.1))
    ax.text(x+w/2,y+h*.7,title,ha='center',va='center',fontsize=16,weight='bold')
    ax.text(x+w/2,y+h*.28,body,ha='center',va='center',fontsize=12,linespacing=1.7)
def arrow(ax,x,y,xx,yy):
    ax.add_patch(FancyArrowPatch((x,y),(xx,yy),arrowstyle='-|>',mutation_scale=14,color='black',lw=1.2))

fig,ax=canvas(9,3.83);frame(ax);fig.subplots_adjust(left=.035,right=.965,top=.97,bottom=.04)
ax.text(2,94,'供应链预测与计划  /  05',fontsize=12,color='.4',va='top')
ax.text(2,73,'预测之后，究竟该订多少',fontsize=28,weight='bold',va='center')
ax.text(2,56,'数量有依据，时间接得上，约束过得去。',fontsize=15)
for x,title,body in [(2,'需求判断','分布 · 保护期'),(36,'库存账本','可用 · 到货 · 效期'),(70,'审核建议','箱规 · 容量 · 缺口')]:box(ax,x,13,28,31,title,body)
arrow(ax,31,29,35,29);arrow(ax,65,29,69,29)
ax.text(2,2,'双案例均为教学模拟；预测量不等于采购量。',fontsize=10,color='.35')
save(fig,'p05-cover')

fig,ax=canvas(11,5.8);frame(ax);fig.subplots_adjust(left=.025,right=.975,top=.96,bottom=.03)
ax.text(4,94,'保护三天，不等于新货能覆盖每一天',fontsize=23,weight='bold')
xs=[8,35,62,89]
ax.plot([8,89],[52,52],color='black',lw=1.8)
for x,t,date in zip(xs,['第1日','第2日','第3日','第4日'],['11月12日','11月13日','11月14日','11月15日']):
    ax.plot([x,x],[48,56],color='black',lw=1.5);ax.text(x,64,t,ha='center',fontsize=17,weight='bold');ax.text(x,72,date+' 08:00',ha='center',fontsize=11)
for x,t in zip(xs,['盘点并下单\n现货10kg','本次新货到达\n只能从此时使用','下一次检查\n旧在途8kg到','下一批常规货\n最早此时到']):ax.text(x,40,t,ha='center',va='top',fontsize=13,linespacing=1.8)
ax.annotate('',xy=(8,83),xytext=(35,83),arrowprops={'arrowstyle':'|-|','color':'black'});ax.text(21.5,86,'L = 1日',ha='center',fontsize=12)
ax.annotate('',xy=(8,10),xytext=(89,10),arrowprops={'arrowstyle':'|-|','color':'black'});ax.text(48.5,13,'本次查看第1–3日：H = L + R = 1 + 2 = 3日',ha='center',fontsize=13)
ax.text(4,0,'教学时钟；R = 2日。新单第2日才到，第1日缺口不能倒填。',fontsize=11,color='.35')
save(fig,'01-protection-window')

sys.path.insert(0,str(ROOT/'practice'));import run
c,nv,paths,dem,batches,ic,ac=run.load(ROOT/'practice'/'inputs')
# The article illustrations are templates for the original teaching fixture, not a general reporting dashboard.
summary=run.calculate((c,nv,paths,dem,batches,ic,ac))[0]
assert summary['newsvendor_alpha']==run.D('.75') and nv==[(run.D(x),run.D(1)) for x in [80,100,120,140]], 'Restore original newsvendor fixture before rebuilding article illustrations'
assert list(dem.values())==[run.D(12),run.D(14),run.D(10)] and summary['inventory_selected']['q']==15 and ic['capacity_kg']==18, 'Restore original inventory fixture before rebuilding article illustrations'
assert summary['apparel']['production_needed_pieces']==85 and summary['apparel']['purchase_m']==100 and summary['apparel_capacity_plan']['purchase_m']==80, 'Restore original apparel fixture before rebuilding article illustrations'
q=list(range(60,181))
cost=[sum(w*(c['underage_cost']*max(d-x,run.ZERO)+c['overage_cost']*max(x-d,run.ZERO)) for d,w in nv)/sum(w for _,w in nv) for x in q]
fig,ax=canvas(10,5.8)
ax.plot(q,[float(v) for v in cost],color='black',lw=2)
ax.axvspan(120,140,color='.88',zorder=0)
ax.scatter([80,100,120,140,160],[180,100,60,60,100],facecolor='white',edgecolor='black',s=65,zorder=4)
for a,b in [(80,180),(100,100),(120,60),(140,60),(160,100)]:ax.annotate(f'({a}, {b})',(a,b),xytext=(0,12 if a not in [120,140] else -24),textcoords='offset points',ha='center',fontsize=12)
ax.set(xlabel='准备量 Q（件）',ylabel='平均成本（元）',xlim=(60,180),ylim=(0,320),xticks=list(range(60,181,20)),title='120至140件并列最优，不是唯一答案')
ax.text(130,125,'每增加1件\n平均成本变化为0',ha='center',fontsize=13)
ax.grid(axis='y',color='.9',lw=.8);fig.subplots_adjust(left=.11,right=.97,top=.86,bottom=.18)
fig.text(.5,.045,'教学模拟：需求80/100/120/140各25%；少备6元/件，多备2元/件。',ha='center',fontsize=12)
save(fig,'02-newsvendor-cost')

_,led=run.simulate(run.D(15),dem,batches,ic)
fig,ax=canvas(10,5.8)
served=[float(x['served_kg']) for x in led];lost=[float(x['lost_kg']) for x in led]
ax.bar([1,2,3],served,color='.78',edgecolor='black',label='可满足量')
ax.bar([1,2,3],lost,bottom=served,color='white',edgecolor='black',hatch='///',label='未满足量')
for i,(s,l) in enumerate(zip(served,lost),1):
    ax.text(i,s/2,f'满足 {s:g}',ha='center',fontsize=14)
    if l:ax.text(i,s+l+0.5,f'缺 {l:g}',ha='center',fontsize=14,weight='bold')
ax.set(xticks=[1,2,3],xticklabels=['第1日\n初始现货10kg','第2日\n新货15kg到','第3日\n承接1 + 旧在途8kg'],ylabel='公斤',ylim=(0,18),title='订15kg可执行，但仍有3kg需求未覆盖')
ax.legend(frameon=False,loc='upper right');fig.subplots_adjust(left=.1,right=.97,top=.86,bottom=.22)
fig.text(.5,.045,'禾味A店SKU01，三日固定情景；首日缺口2kg不能由次日新货补救。',ha='center',fontsize=12)
save(fig,'03-hewei-ledger')

fig,ax=canvas(11,6.4);frame(ax);fig.subplots_adjust(left=.02,right=.98,top=.96,bottom=.025)
ax.text(4,94,'材料够，不代表生产来得及',fontsize=24,weight='bold')
box(ax,3,61,27,23,'100件需求情景','待发留存80 + 新增20')
box(ax,37,61,25,23,'85件待生产','减去可用成衣15件')
box(ax,70,61,27,23,'毛布178.947米','85 × 2 ÷ 0.95')
arrow(ax,31,72,36,72);arrow(ax,63,72,69,72)
box(ax,3,25,27,23,'及时可用80米','现有50 + 及时在途30\n晚到25米不扣减')
box(ax,37,25,25,23,'候选购布100米','净缺98.947米\n20米/卷，5卷')
box(ax,70,25,27,23,'产能仍缺15件','待产85 > 可产70\n整体计划不可行')
arrow(ax,31,36,36,36);arrow(ax,83,60,83,49)
ax.text(4,10,'另一方案：只为70件备料，可购80米；仍须保留15件需求缺口。',fontsize=14)
ax.text(4,0,'匿名服装教学模拟；期望情景不是P90；数值显示保留三位小数。',fontsize=11,color='.35')
save(fig,'04-apparel-material')
print('Created five PNG/SVG pairs in',OUT)
