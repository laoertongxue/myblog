#!/usr/bin/env python3
"""D11 monochrome figures: unchanged development data, independently computed SES."""
from pathlib import Path
import argparse, csv, hashlib, json, math
from itertools import combinations
from PIL import Image, ImageDraw, ImageFont, ImageChops
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parents[1]
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--font-path', type=Path, required=True, help='Standalone Noto Sans SC TTF/OTF font')
a = p.parse_args()
FONT = str(a.font_path.expanduser().resolve())
font = TTFont(FONT)
families = {n.toUnicode() for n in font['name'].names if n.nameID in (1, 16)}
if not any(n in families for n in ['Noto Sans SC', 'Noto Sans CJK SC']):
    raise ValueError(f'Simplified Chinese Noto font required, got {families}')
cmap = font.getBestCmap()
OUT = ROOT / 'images'; OUT.mkdir(exist_ok=True)
SCALE = 2
REPORT = []
CURVES = {}
HASHES = {'hewei': '292072a63439529f22a73d41b83516928ae5a5b474b907b33d42e74962c23407',
          'apparel': '56badd2fc37decd72b2f55a980acb7add2594b96c7b8d269f6aaae59ee7d47e5'}
for case, expected in HASHES.items():
    path = ROOT / 'practice/data' / f'{case}-development.csv'
    assert hashlib.sha256(path.read_bytes()).hexdigest() == expected
    with path.open(newline='') as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 140 and [r['split'] for r in rows] == ['train']*112+['validation']*28
    vals = [float(r['demand']) for r in rows]
    levels = {}
    for alpha in [.2, .5, .8]:
        seq = [vals[0]]
        for v in vals[1:]:
            seq.append(alpha*v+(1-alpha)*seq[-1])
        levels[str(alpha)] = seq
    CURVES[case] = {'days': list(range(113,141)), 'actual': vals[112:],
        'predictions': {k:v[111:139] for k,v in levels.items()},
        'levels': {k:v[112:] for k,v in levels.items()}}


def line(draw, points, style='solid', width=3, fill=0):
    if style == 'solid':
        draw.line([(round(x*SCALE),round(y*SCALE)) for x,y in points], fill=fill, width=round(width*SCALE), joint='curve')
        return
    pattern = {'dash': [20,12], 'dot': [4,12], 'dashdot': [24,8,4,8]}[style]
    i=0; remaining=pattern[0]
    for (x,y),(xx,yy) in zip(points,points[1:]):
        length=math.hypot(xx-x,yy-y); used=0
        while used < length-1e-8:
            take=min(remaining,length-used)
            if i%2==0:
                q=[(x+(xx-x)*u/length,y+(yy-y)*u/length) for u in [used,used+take]]
                line(draw,q,'solid',width,fill)
            used+=take;remaining-=take
            if remaining<1e-8:
                i=(i+1)%len(pattern);remaining=pattern[i]

class Figure:
    def __init__(self,name,w,h):
        self.name=name; self.w=w;self.h=h;self.texts=[]
        self.im=Image.new('L',(w*SCALE,h*SCALE),255);self.d=ImageDraw.Draw(self.im)
    def text(self,x,y,s,size=52,fill=0,anchor='lt'):
        assert all(ord(c) in cmap or c.isspace() for c in s), ('missing glyph',s)
        f=ImageFont.truetype(FONT,round(size*SCALE))
        xy=(round(x*SCALE),round(y*SCALE));b=self.d.textbbox(xy,s,font=f,anchor=anchor)
        assert b[0]>=0 and b[1]>=0 and b[2]<=self.w*SCALE and b[3]<=self.h*SCALE,(self.name,s,b)
        self.d.text(xy,s,font=f,fill=fill,anchor=anchor)
        self.texts.append({'text':s,'font_size':size,'bbox':[v/SCALE for v in b]})
    def path(self,points,style='solid',width=3,fill=0):
        line(self.d,points,style,width,fill)
    def rect(self,b,fill=246):
        self.d.rectangle(tuple(round(v*SCALE) for v in b),fill=fill,outline=0,width=2*SCALE)
    def save(self):
        for x,y in combinations(self.texts,2):
            b=x['bbox'];c=y['bbox']
            assert not (min(b[2],c[2])>max(b[0],c[0]) and min(b[3],c[3])>max(b[1],c[1])),(self.name,x['text'],y['text'])
        im=self.im.resize((self.w,self.h),Image.Resampling.LANCZOS).convert('RGB')
        for width in [self.w,350,280]:
            folder=OUT if width==self.w else OUT/f'preview-{width}'
            folder.mkdir(exist_ok=True)
            target=folder/self.name
            rendered=im if width==self.w else im.resize((width,round(self.h*width/self.w)),Image.Resampling.LANCZOS)
            rendered.save(target,optimize=True)
            r,g,b=rendered.split()
            assert ImageChops.difference(r,g).getbbox() is None and ImageChops.difference(g,b).getbbox() is None
        REPORT.append({'file':self.name,'size':[self.w,self.h],'sha256':hashlib.sha256((OUT/self.name).read_bytes()).hexdigest(),'text_boxes':self.texts,'text_overlap':False,'grayscale':True})

f=Figure('d11-00_cover.png',900,383)
f.text(40,28,'D11  /  SIMPLE EXPONENTIAL SMOOTHING',22,70)
f.text(40,79,'指数平滑：参数越大越好吗',48)
f.text(40,150,'新观测 × α ＋ 旧水平 ×（1−α）',29,50)
f.path([(55,265),(120,258),(185,270),(250,229),(315,255),(380,215)],width=4)
f.path([(435,206),(435,294)],'dash',2,110)
f.path([(480,246),(825,246)],'dash',4)
f.text(40,315,'截至今天更新',27)
f.text(488,315,'同一起点，未来五步同值',27)
f.save()

f=Figure('d11-01_alignment.png',1200,1470)
f.text(60,48,'先预测，再观察，再更新',62)
f.text(60,146,'手算序列｜10、20、10；α = 0.5',50,50)
for y,title,body in [(270,'第 1 天结束：初始化','水平 = 10；预测第 2 天 = 10'),
                     (490,'第 2 天结束：看到 20','水平 = 0.5×20 + 0.5×10 = 15'),
                     (710,'第 3 天到来前','预测第 3 天 = 15，而不是 12.5'),
                     (930,'第 3 天结束：看到 10','更新水平 = 12.5，用于后续预测')]:
    f.rect((52,y-18,1148,y+158))
    f.text(82,y+4,title,54)
    f.text(82,y+88,body,50)
f.text(60,1180,'停在第 2 天：未来五步均为 15。',52)
f.text(60,1280,'今天更新后的水平，不能给今天评分。',52)
f.text(60,1380,'手算机制示意，非业务观测。',48,80)
f.save()

f=Figure('d11-02_split.png',1200,1320)
f.text(60,48,'沿用数据，也沿用评价边界',60)
f.text(60,150,'两份模拟开发序列，各 140 天',52,65)
for y,title,body in [(280,'1—112 天｜训练历史','首值初始化；逐日更新水平'),
                     (505,'113—140 天｜验证','28 个一步目标；24 个五日窗口'),
                     (730,'141—180 天｜不读、不评分','D9 已展示测试汇总，不能称盲测')]:
    f.rect((52,y-18,1148,y+158))
    f.text(82,y+4,title,54)
    f.text(82,y+88,body,50)
f.text(60,995,'五日首窗：113—117',52)
f.text(60,1085,'五日末窗：136—140',52)
f.text(60,1185,'窗口重叠；不是 24 次独立实验。',52)
f.save()

def legend(f,y):
    for x,dy,label,style in [(70,0,'实际','solid'),(615,0,'α = 0.2','dash'),
                            (70,82,'α = 0.5','dot'),(615,82,'α = 0.8','dashdot')]:
        f.path([(x,y+dy+24),(x+110,y+dy+24)],style,5)
        f.text(x+138,y+dy,label,50)

def plot(f,top,case,field):
    data=CURVES[case]; x0=158; y0=top; w=972;h=365
    ymax=45 if case=='hewei' else 260
    ticks=[0,20,40] if case=='hewei' else [0,120,240]
    for v in ticks:
        y=y0+h-v/ymax*h
        f.path([(x0,y),(x0+w,y)],width=1,fill=205)
        f.text(x0-20,y,str(v),48,80,anchor='rm')
    f.path([(x0,y0),(x0,y0+h),(x0+w,y0+h)],width=2)
    for day in [113,122,131,140]:
        x=x0+(day-113)/27*w
        f.text(x,y0+h+28,str(day),48,65,anchor='mt')
    for values,style,gray in [(data['actual'],'solid',100)]+[(data[field][key],style,0) for key,style in [('0.2','dash'),('0.5','dot'),('0.8','dashdot')]]:
        f.path([(x0+i/27*w,y0+h-v/ymax*h) for i,v in enumerate(values)],style,4,gray)

for case,name,title,unit in [('hewei','d11-03_hewei.png','禾味 A 店 · SKU01','公斤/日'),('apparel','d11-04_apparel.png','匿名服装 · 终端订单','件/日')]:
    f=Figure(name,1200,1860)
    f.text(60,48,title,60)
    f.text(60,144,f'模拟验证段｜第 113—140 天｜{unit}',48,60)
    legend(f,245)
    f.text(60,455,'上：逐日一步预测，起点在前一天',52)
    plot(f,555,case,'predictions')
    f.text(60,1042,'下：当日更新后水平，已见当日实际',52)
    plot(f,1145,case,'levels')
    f.text(60,1640,'横轴：模拟日编号；上下轴范围相同。',50,65)
    f.text(60,1730,'只有上图的预测进入本文误差表。',52)
    f.save()

# Cross-check every figure value against the separately generated practice CSVs.
with (ROOT/'practice/results/daily_predictions.csv').open(newline='') as handle:
    for r in csv.DictReader(handle):
        if r['method'].startswith('SES'):
            i=int(r['target_day'])-113; c=CURVES[r['case']]
            assert abs(c['predictions'][r['method'][3:]][i]-float(r['prediction']))<1e-10
            assert c['actual'][i]==float(r['actual'])
with (ROOT/'practice/results/levels.csv').open(newline='') as handle:
    for r in csv.DictReader(handle):
        if int(r['day'])>=113:
            assert abs(CURVES[r['case']]['levels'][r['alpha']][int(r['day'])-113]-float(r['post_observation_level']))<1e-10
(ROOT/'figure-tools/plotted-curves.json').write_text(json.dumps(CURVES,ensure_ascii=False,indent=2)+'\n')
(ROOT/'figure-tools/render-quality-report.json').write_text(json.dumps({'font_families':sorted(families),'font_sha256':hashlib.sha256(Path(FONT).read_bytes()).hexdigest(),'inputs_sha256':HASHES,'crosscheck':'all validation SES predictions and post-observation levels matched practice CSVs','figures':REPORT},ensure_ascii=False,indent=2)+'\n')
print('Five grayscale figures rendered, all glyph/bounds/text-overlap/data checks passed.')
