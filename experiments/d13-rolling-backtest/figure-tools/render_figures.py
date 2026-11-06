#!/usr/bin/env python3
"""D13 monochrome publication figures from replay and separate simulation."""
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

negative=json.loads((ROOT/'practice/results/negative_control.json').read_text())
with (ROOT/'practice/results/stockout_simulation.csv').open() as h:
    stock=list(csv.DictReader(h))

f=Figure('d13-00_cover.png',900,383)
f.text(40,26,'D13  /  ROLLING BACKTEST',23,70)
f.text(40,85,'预测时，还不知道的事',54)
f.path([(65,242),(835,242)],width=3)
f.path([(440,188),(440,300)],width=4)
f.text(78,200,'已知历史',30)
f.text(540,200,'未来观测',30,90)
f.text(365,320,'先预测，再更新',29)
f.save()

f=Figure('d13-01_origins.png',1200,1280)
f.text(60,45,'每个起点，都保存当时的版本',56)
f.text(60,150,'第 112 天日终：只看 1—112 天',50)
for y,title,sub in [(300,'一步：目标 113','得到 113 天实际后，才进入下一起点'),(585,'五步：目标 113—117','五个预测一起发出，中间不改旧版本')]:
    f.rect((45,y-30,1155,y+175))
    f.text(75,y,title,56)
    f.text(75,y+100,sub,46)
f.text(60,880,'一步：112—139 起点，28 个目标',49)
f.text(60,990,'五步：112—135 起点，24 个窗口',49)
f.text(60,1110,'只到第 140 天；窗口重叠非独立样本',48)
f.save()

f=Figure('d13-02_revisions.png',1200,1390)
f.text(60,45,'同样五天，却不是同一份预测',56)
f.text(60,150,'匿名服装模拟｜SES α=0.8｜件',49,65)
r=next(r for r in negative if r['case']=='apparel')
f.text(60,290,'第 117 天日终一次发出',54)
f.text(60,395,'五步均为 111.2033 件/日',52)
f.rect((55,510,1145,680))
f.text(85,555,f'固定起点合计：{r["fixed_total"]:.2f} 件',58)
f.text(60,795,'随后每天吸收新订单，再修订',52)
f.rect((55,910,1145,1080),fill=225)
f.text(85,955,f'逐日修订合计：{r["revised_total"]:.2f} 件',58)
f.text(60,1195,'后者不能冒充第 117 天发出的五步。',48)
f.text(60,1290,'目标 118—122 天；不将负对照用于评分。',46,65)
f.save()

f=Figure('d13-03_stockout.png',1200,1890)
f.text(60,45,'缺货截断：销量低，不代表需求低',55)
f.text(60,145,'独立 14 天模拟，服装为禾味数量五倍',46,65)
f.path([(65,255),(200,255)],width=5)
f.text(230,224,'模拟需求',48)
f.path([(615,255),(750,255)],style='dash',width=5,fill=95)
f.text(780,224,'可观测销量',48)
for top,case,title,maxv,ticks in [(405,'hewei','禾味｜公斤/日',45,[0,20,40]),(1000,'apparel','匿名服装｜件/日',225,[0,100,200])]:
    f.text(60,top-55,title,50)
    left,right,base,height=150,1130,top+360,325
    f.path([(left,top+25),(left,base),(right,base)],width=3)
    for v in ticks:
        y=base-v/maxv*height
        f.path([(left,y),(right,y)],width=1,fill=205)
        f.text(120,y,str(v),40,anchor='rm')
    rs=[r for r in stock if r['case']==case]
    for key,style,gray in [('latent_simulated_demand','solid',0),('observed_sales','dash',95)]:
        segments=[];points=[]
        for r in rs:
            if not r[key]:
                if points:segments.append(points);points=[]
                continue
            points.append((left+(int(r['simulation_day'])-1)*(right-left)/13,base-float(r[key])/maxv*height))
        if points:segments.append(points)
        for pts in segments:
            f.path(pts,style,width=4,fill=gray)
            for x,y in pts:
                f.d.ellipse(((x-5)*SCALE,(y-5)*SCALE,(x+5)*SCALE,(y+5)*SCALE),fill=gray)
    for d in [1,3,5,8,12,14]:
        x=left+(d-1)*(right-left)/13
        f.text(x,base+30,str(d),38,anchor='mt')
    f.text(620,base+100,'模拟日（1 月 5—18 日）',42,anchor='mt')
f.text(60,1540,'第 3 天真零；第 12 天缺货零销量。',48)
f.text(60,1640,'第 5 天休店、第 8 天缺测：销量留空。',48)
f.text(60,1740,'实线真值仅模拟作者知道，现实不能照搬。',46)
f.save()

(ROOT/'figure-tools/render-quality-report.json').write_text(json.dumps({'font_families':sorted(families),'font_sha256':hashlib.sha256(Path(FONT).read_bytes()).hexdigest(),'inputs_sha256':{name:hashlib.sha256((ROOT/'practice/results'/name).read_bytes()).hexdigest() for name in ['negative_control.json','stockout_simulation.csv']},'figures':REPORT},ensure_ascii=False,indent=2)+'\n')
print('Four grayscale figures rendered; glyph, bounds and text overlap checks passed.')
