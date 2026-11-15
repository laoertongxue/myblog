"""Rebuild editorial diagrams; matplotlib + Noto Sans CJK required. No network."""
from pathlib import Path
import os
os.environ.setdefault('MPLCONFIGDIR','/tmp/article8-mpl')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from matplotlib.patches import FancyBboxPatch
ROOT=Path(__file__).resolve().parent
OUT=ROOT.parent/'images';OUT.mkdir(parents=True,exist_ok=True)
FONT=os.environ.get('CJK_FONT_PATH','/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
if not Path(FONT).is_file(): raise SystemExit('Set CJK_FONT_PATH to a CJK font file')
plt.rcParams.update({'font.family':FontProperties(fname=FONT).get_name(),'svg.fonttype':'none','axes.unicode_minus':False,'font.size':18})
def base(h,title,sub):
 f=plt.figure(figsize=(10,h/100),dpi=140,facecolor='white');a=f.add_axes([0,0,1,1]);a.set(xlim=(0,1000),ylim=(h,0));a.axis('off');a.text(42,58,title,fontsize=24,weight='bold');a.text(42,99,sub,fontsize=14,color='.3');return f,a

def box(a,x,y,w,h,txt,fs=20,gray='.96'):
 a.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0,rounding_size=9',facecolor=gray,edgecolor='.3',linewidth=1.2));a.text(x+w/2,y+h/2,txt,ha='center',va='center',fontsize=fs,linespacing=1.6)
def line(a,x1,y1,x2,y2):a.annotate('',xy=(x2,y2),xytext=(x1,y1),arrowprops={'arrowstyle':'->','color':'.35','lw':1.6})
def save(f,n):
 f.savefig(OUT/(n+'.png'),dpi=140);f.savefig(OUT/(n+'.svg'));plt.close(f)
f,a=base(565,'总部说100，地区加起来却是110','同一 SKU · 同一未来7天 · 同一预测版本 · 教学模拟')
box(a,330,135,340,105,'总部独立预测\n100件',22)
line(a,430,242,265,300);line(a,570,242,735,300)
box(a,70,305,390,100,'北区：60件',23);box(a,540,305,390,100,'南区：50件',23)
box(a,70,445,860,78,'60 + 50 = 110 ≠ 100　　先暴露差异，再选择协调规则',19)
save(f,'01-hierarchy-conflict')
f,a=base(620,'三条协调路径，不是一道唯一答案','均采用同一组模拟输入：总部100，北区60，南区50')
cols=[42,350,658]
for x,title,detail,total in zip(cols,['自下而上','固定总部总量','混合总量（权重0.6）'],['保留地区预测\n60 / 50','按原比例拆分\n54.545… / 45.454…\n整数：55 / 45','先混合再拆分\n56.727… / 47.272…\n整数：57 / 47'],['总量110','总量100','总量104']):
 box(a,x,145,300,63,title,17,gray='.9');box(a,x,228,300,180,detail,18);box(a,x,430,300,70,total,23)
a.text(42,550,'混合总量 = 0.6 × 100 + 0.4 × 110 = 104',fontsize=21,weight='bold')
a.text(42,590,'权重为教学给定，不代表已经训练出最优权重。',fontsize=16)
save(f,'02-three-methods')
f,a=base(565,'加总正确，不代表预测更准','反例：事后实际为北区60、南区50，共110件 · 教学模拟')
box(a,42,145,440,145,'保留底层预测\n北60 / 南50 / 总110\n两地区绝对误差：0、0',20)
box(a,518,145,440,145,'强制总部总量100\n北55 / 南45 / 总100\n两地区绝对误差：5、5',20)
box(a,42,320,440,90,'底层 MAE = (0 + 0) ÷ 2 = 0',19)
box(a,518,320,440,90,'底层 MAE = (5 + 5) ÷ 2 = 5',19)
a.text(42,465,'两种方案都满足「地区之和 = 总量」。',fontsize=22,weight='bold')
a.text(42,515,'验收要查一致性，也要在相同评价窗口比较误差。',fontsize=19)
save(f,'03-coherent-not-accurate')
f,a=base(570,'需求与供给，保留两本账','同一交付窗口、同一 SKU、同一单位 · 教学模拟')
box(a,42,145,440,120,'需求判断\n协调预测：100件',23)
box(a,518,145,440,120,'供给限制\n可交付产能：80件',23)
line(a,260,267,400,320);line(a,740,267,600,320)
box(a,230,325,540,100,'供给缺口 = 100 − 80 = 20件',22)
a.text(42,480,'保留100件需求，单独报告20件缺口。',fontsize=23,weight='bold')
a.text(42,530,'不能把预测改成80件，再宣称计划已经平衡。',fontsize=19)
save(f,'04-demand-supply')
print('Generated 4 PNG + 4 editable SVG diagrams in',OUT)
