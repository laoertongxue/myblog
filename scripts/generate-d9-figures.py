"""Regenerate editable SVGs from actual validation output; stdlib only."""
import html
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ROOT = REPO/'examples/d9-seasonal-naive'
sys.path.insert(0,str(ROOT))
from baseline import forecast_at
from generate import generate
SLUG = 'seasonal-naive-demand-forecast'
DEST = REPO/'assets/diagram-sources'/SLUG
DEST.mkdir(parents=True,exist_ok=True)


class Figure:
    def __init__(self,w,h,title,subtitle):
        self.w,self.h=w,h
        self.parts=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">',
                    '<rect width="100%" height="100%" fill="#f4f4f4"/>',
                    '<g font-family="Microsoft YaHei, Noto Sans CJK SC, sans-serif" fill="#202020">']
        self.text(34,48,title,26,True)
        self.text(34,81,subtitle,16)
    def text(self,x,y,s,size=20,bold=False):
        self.parts.append(f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{700 if bold else 400}">{html.escape(str(s))}</text>')
    def box(self,x,y,w,h,fill='#ffffff'):
        self.parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="7" fill="{fill}"/>')
    def line(self,x1,y1,x2,y2,dash=False):
        self.parts.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#777777" stroke-width="2"'+(' stroke-dasharray="7 5"' if dash else '')+'/>')
    def save(self,name,cover=False):
        path=REPO/f'assets/cover-sources/{SLUG}.svg' if cover else DEST/f'{name}.svg'
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(''.join(self.parts)+'</g></svg>',encoding='utf-8')


f=Figure(900,383,'季节性朴素需求预测','供应链算法实践 / D9 · 完全可观测的教学模拟')
f.text(34,133,'上周同一天，是一个能手算的起点',27,True)
values=forecast_at(generate(),112,7)
for i,(label,value) in enumerate(zip(['一','二','三','四','五','六','日'],values)):
    x=34+i*119
    f.box(x,164,108,129)
    f.text(x+19,199,'周'+label,20)
    f.text(x+28,247,value,29,True)
    f.text(x+20,278,'公斤',16)
f.text(34,343,'最后七天 → 下一周   |   时间隔离 · 未来扰动 · 异常周反例',18)
f.save('d9-00_cover',True)

f=Figure(1000,580,'先沿时间划界，再开始预测','112 / 28 / 40 · 不随机打散 · 五天目标窗口完整留在所属分块')
for x,w,title,subtitle,fill in [(34,520,'初始训练 1—112','4月6日—7月26日','#dddddd'),(566,170,'验证 113—140','7月27日—8月23日','#ffffff'),(748,218,'测试 141—180','8月24日—10月2日','#bbbbbb')]:
    f.box(x,121,w,127,fill)
    f.text(x+14,166,title,21,True)
    f.text(x+14,206,subtitle,14)
f.box(34,275,932,116)
f.text(54,315,'验证五天窗口：113—117 … 136—140，共24个',23,True)
f.text(54,355,'137—141 跨入测试段：拒绝作为验证窗口',20)
f.box(34,410,932,116)
f.text(54,450,'测试五天窗口：141—145 … 176—180，共36个',23,True)
f.text(54,490,'逐日滚动：过去测试日可成为历史；固定规则不回头挑选',20)
f.text(34,558,'解释图依据 policy.json 与 windows() 的真实边界；相邻窗口重叠，不是独立样本。',16)
f.save('d9-01_split')

f=Figure(1000,540,'七个预测，逐个对齐同一个星期','T=112（周日）· 来源106—112 · 目标113—119 · 单位：公斤')
for i,(day,value) in enumerate(zip(['一','二','三','四','五','六','日'],values)):
    x=34+i*135
    f.box(x,123,122,268)
    f.text(x+27,159,'周'+day,23,True)
    f.text(x+16,203,'已知 '+str(106+i),17)
    f.text(x+39,245,value,30,True)
    f.line(x+61,262,x+61,298)
    f.text(x+16,328,'预测 '+str(113+i),17)
    f.text(x+39,370,value,30,True)
f.text(34,437,'第8步再次取19，第14步取29，第15步再次取19。',23,True)
f.text(34,478,'固定起点永远循环最后完整七天；不读取起点之后的实际需求。',20)
f.text(34,518,'解释图读取 results/hand.json 对应生成值；七步演示不冒充五天累计评价。',16)
f.save('d9-02_weekdays')

f=Figure(1000,850,'同一条基线，在两个模拟情景下会怎样','实际验证结果图 · 黑实线为实际，灰虚线为滚动一天预测 · 横轴为日序')
for j,(case,label,maximum) in enumerate([('hewei','禾味 A店 SKU01 / 公斤',45),('apparel','匿名服装终端订单 / 件',260)]):
    result=json.loads((ROOT/f'results/{case}-validation.json').read_text())
    top=135+j*305
    f.text(34,top-10,label,22,True)
    f.text(620,top-10,f'日MAE {result["mae"]:.4f}',20)
    x0,y0,w,h=84,top+12,846,198
    for tick in range(4):
        v=maximum*tick/3
        y=y0+h-v/maximum*h
        f.line(x0,y,x0+w,y)
        f.text(34,y+5,f'{v:.0f}',15)
    for field,color,dash in [('actual','#202020',False),('forecast','#888888',True)]:
        pts=' '.join(f'{x0+i*w/27:.2f},{y0+h-r[field]/maximum*h:.2f}' for i,r in enumerate(result['daily']))
        f.parts.append(f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="3"'+(' stroke-dasharray="8 6"' if dash else '')+'/>')
    for day in (113,118,120,127,134,140):
        f.text(x0+(day-113)*w/27-13,y0+h+28,day,15)
    if case=='apparel':
        f.box(84,711,846,56)
        f.text(104,746,'活动冲击：118—120日',19,True)
        f.text(500,746,'复制高点：125—127日',19,True)
f.text(34,817,'两图纵轴与单位不同；活动与趋势为事先给定模拟情景，不证明行业准确率或经营收益。',16)
f.save('d9-03_cases')

rows=generate()
before=forecast_at(rows,112,15)
for row in rows[112:]: row.update(date='invalid',demand=-999)
after=forecast_at(rows,112,15)
assert before==after
f=Figure(1000,570,'主动攻击：未来变了，旧预测应当不变','实际执行T=112、h=15；第113天以后改成非法日期和−999需求')
f.box(34,117,932,167)
f.text(54,153,'原始未来：'+ ' / '.join(map(str,before)),21,True)
f.text(54,201,'污染未来：'+ ' / '.join(map(str,after)),21,True)
f.text(54,252,'15个值完全相同：先截取已知前缀，再校验与预测。',22)
for j,(title,detail) in enumerate([('合法零需求','保留0，不把零当缺失'),('非法输入必须拒绝','不足7天 / 负数与非有限数 / 缺日期与重复日期 / 非法步长')]):
    y=306+j*103
    f.box(34,y,932,85)
    f.text(54,y+32,title,22,True)
    f.text(54,y+65,detail,18)
f.text(34,551,'解释图来自实际扰动执行；完整输入攻击见 test_baseline.py，未来污染不进入主实验。',16)
f.save('d9-04_boundaries')
print('Wrote cover + 4 editable SVG figures from fixed rules and validation output.')
