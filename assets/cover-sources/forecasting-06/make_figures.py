from pathlib import Path
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from matplotlib.patches import FancyBboxPatch
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'images';OUT.mkdir(parents=True,exist_ok=True)
FONT=os.environ.get('CJK_FONT_PATH','/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
if not Path(FONT).is_file():raise SystemExit('请用 CJK_FONT_PATH 指定中文字体文件')
plt.rcParams.update({'font.family':FontProperties(fname=FONT).get_name(),'svg.fonttype':'none','axes.unicode_minus':False,'font.size':18})
def base(w,h,title,sub):
 f=plt.figure(figsize=(w/100,h/100),dpi=100,facecolor='white');a=f.add_axes([0,0,1,1]);a.set(xlim=(0,w),ylim=(h,0));a.axis('off');a.text(36,62,title,fontsize=25,weight='bold');a.text(36,105,sub,fontsize=15,color='.25');return f,a

def box(a,x,y,w,h,txt,fs=20):
 a.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0,rounding_size=10',facecolor='.96',edgecolor='.25',linewidth=1.5));a.text(x+w/2,y+h/2,txt,ha='center',va='center',fontsize=fs,linespacing=1.7)
def arrow(a,x,y,z):a.annotate('',xy=(x,z),xytext=(x,y),arrowprops={'arrowstyle':'->','color':'black','lw':2})
def save(f,n):
 f.savefig(OUT/(n+'.png'),dpi=100);f.savefig(OUT/(n+'.svg'));plt.close(f)
f,a=base(900,383,'采购、调拨还是生产','供应链预测与计划 · 第06篇 · 全部为教学模拟')
for x,t in [(36,'净缺口\n有情景'),(324,'来源选择\n有约束'),(612,'供给建议\n有取舍')]:box(a,x,157,250,145,t,23)
a.annotate('',xy=(316,230),xytext=(294,230),arrowprops={'arrowstyle':'->'});a.annotate('',xy=(604,230),xytext=(582,230),arrowprops={'arrowstyle':'->'})
a.text(36,350,'先固定一份方案，再对所有情景计算费用。',fontsize=19);save(f,'00-cover')
f,a=base(700,900,'先决定，再看到需求','固定数量不能随着未来情景偷偷改变')
box(a,36,150,628,120,'决策时点\n输入需求情景、概率、来源与资源',20)
arrow(a,350,280,320);box(a,36,330,628,110,'固定一份方案\n例如采购10kg＋调拨20kg',21)
arrow(a,350,450,490)
for x,t in [(36,'低需求\n20kg'),(254,'中需求\n30kg'),(472,'高需求\n40kg')]:box(a,x,500,192,120,t,20)
box(a,36,680,628,115,'三行都用同一个30kg方案\n费用90、80、180元',21)
a.text(36,856,'期望费用 = 0.2×90 + 0.5×80 + 0.3×180 = 112元',fontsize=15);save(f,'01-decision')
f,a=base(700,900,'禾味：目标不同，建议不同','同一需求分布与资源边界 · 单位公斤')
box(a,36,150,628,190,'最低期望费用\n采购10＋调拨20＝供给30\n费用期望112元',22)
box(a,36,385,628,190,'高情景也保供\n采购20＋调拨20＝供给40\n费用期望119元',22)
box(a,36,620,628,160,'多7元期望费用\n期望少供：3 → 0\n期望余量：2 → 9',22)
a.text(36,840,'100%只针对所列情景与确定到货假设。',fontsize=17);save(f,'02-hewei')
f,a=base(700,1000,'服装：产能必须和材料一起看','匿名模拟 · 同一款码 · 成品单位为件')
box(a,36,150,628,150,'机器：最多60件\n面料：100米 ÷ 2米/件＝50件',22)
arrow(a,350,310,350);box(a,36,360,628,100,'生产上限＝min(60,50)＝50件',21)
box(a,36,510,628,145,'最低期望费用\n采购0＋调拨40＋生产50\n期望费用502元，期望少供3件',20)
box(a,36,700,628,145,'高情景也保供\n采购10＋调拨40＋生产50\n期望费用536元，期望少供0件',20)
a.text(36,920,'仅建模一种面料，不代表完整BOM齐套。',fontsize=17);save(f,'03-apparel')
f,a=base(700,1050,'建议的五步验收','计算正确，还要让边界可被使用者核对')
for i,t in enumerate(['① 输入快照\n净缺口、概率、时点、单位','② 来源与资源\n到货、批量、保留量、材料','③ 枚举所有允许组合\n先查硬约束，再计费用','④ 保留对照结果\n全部并列解、缺口、余货','⑤ 人工审核\n不可行不改条件，不自动下单']):
 y=145+i*170;box(a,36,y,628,130,t,21)
 if i<4:arrow(a,350,y+135,y+165)
a.text(36,1015,'教学小模型，不是企业级MRP或APS。',fontsize=17);save(f,'04-audit')
print('5 figures generated')
