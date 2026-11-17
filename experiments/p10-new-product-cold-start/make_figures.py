from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
p=Path(__file__).parent/'delivery/images';p.mkdir(exist_ok=True)
f=FontProperties(fname='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
plt.rcParams['axes.unicode_minus']=False

def text(ax,x,y,s,size=15,**kw):ax.text(x,y,s,fontproperties=f,fontsize=size,**kw)
def base(w,h):
 fig,ax=plt.subplots(figsize=(w/100,h/100),dpi=100);fig.patch.set_facecolor('white');return fig,ax
fig,ax=base(900,383);ax.axis('off');text(ax,.03,.85,'新品没有历史销量',28,weight='bold');text(ax,.03,.68,'第一版预测，从相似对象开始',20)
for x,a,b in [(.05,'上市时','冻结参考池'),(.37,'七天后','同窗口混合'),(.69,'进入计划','核对替代与约束')]:
 ax.add_patch(plt.Rectangle((x,.2),.26,.3,fill=False,color='black',lw=1.5));text(ax,x+.13,.39,a,17,ha='center');text(ax,x+.13,.27,b,13,ha='center')
text(ax,.03,.05,'专题 10 · 匿名服装 / 虚构禾味 · 全部为教学模拟',11);fig.subplots_adjust(0,0,1,1);fig.savefig(p/'01-cover.png');plt.close(fig)
fig,ax=base(1000,580);ax.set_xlim(0,1);ax.set_ylim(0,1);ax.axis('off');text(ax,.03,.91,'先冻结，再评价：每案例 7 个上新对象',24)
for y,label,desc in [(.7,'1 月｜参考 3 个','只借已结束的周龄窗口；不纳入未来对象'),(.47,'2 月｜验证 2 个','在 0 / 0.25 / 0.5 / 0.75 / 1 中选权重'),(.24,'3 月｜测试 2 个','上市时预测第 1 周；第 7 天另预测第 2 周')]:
 ax.plot([.04,.96],[y-.1,y-.1],color='#ccc');text(ax,.04,y,label,18);text(ax,.32,y,desc,15)
text(ax,.04,.06,'两个预测窗口不同，不能用误差差值证明“七天信息带来改善”。',14);fig.savefig(p/'02-timeline.png');plt.close(fig)
fig,ax=base(1000,620);xs=[0,1,2];a=[40,20,20];h=[17.5,12.5,7.5]
ax.bar([x-.18 for x in xs],a,width=.36,color='black',label='匿名服装 / 件');ax.bar([x+.18 for x in xs],h,width=.36,color='white',edgecolor='black',hatch='///',label='禾味 / 份')
ax.set_xticks(xs,['等权类比','首周延续','混合 w=0.5'],fontproperties=f,fontsize=14);ax.set_ylabel('各自单位的 MAE（不可跨案例合并）',fontproperties=f,fontsize=13);ax.set_title('第二周测试误差：每案例仅 2 个模拟对象',fontproperties=f,fontsize=21,pad=20);ax.legend(prop=f)
for shift,vals in [(-.18,a),(.18,h)]:
 for x,v in enumerate(vals):ax.text(x+shift,v+.7,str(v),ha='center',fontsize=13)
ax.set_ylim(0,48);ax.spines[['top','right']].set_visible(False);fig.tight_layout();fig.savefig(p/'03-errors.png');plt.close(fig)
fig,ax=base(1000,620);vals=[22.5,19.14,15.78];ax.bar(range(3),vals,color=['black','#888','white'],edgecolor='black');ax.set_xticks(range(3),['0%：不替代','40%：转移 28 份','80%：转移 56 份'],fontproperties=f,fontsize=14)
ax.set_ylabel('共用鸡腿肉需求 / 公斤',fontproperties=f,fontsize=14);ax.set_title('新品 70 份 + 旧菜剩余需求：独立假设情景',fontproperties=f,fontsize=21,pad=20)
for x,v in enumerate(vals):ax.text(x,v+.4,f'{v:.2f}',ha='center',fontsize=15)
ax.set_ylim(0,28);ax.spines[['top','right']].set_visible(False);text(ax,.02,.96,'新菜 0.15 kg/份；旧菜 0.12 kg/份；比例不是概率',13,transform=ax.transAxes);fig.tight_layout();fig.savefig(p/'04-substitution.png');plt.close(fig)
