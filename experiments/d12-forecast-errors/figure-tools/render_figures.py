#!/usr/bin/env python3
"""D12 monochrome figures: literal hand examples and verified metric output."""
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

with (ROOT/'practice/results/metrics.csv').open() as h:
    scores=list(csv.DictReader(h))
def score(case,method,group):
    return next(r for r in scores if r['case']==case and r['method']==method and r['group']==group)

f=Figure('d12-00_cover.png',900,383)
f.text(40,28,'D12  /  FORECAST ERROR & BIAS',22,70)
f.text(40,86,'平均偏差接近零，预测就准吗',49)
f.path([(60,250),(840,250)],width=2,fill=100)
f.rect((180,180,300,250),fill=90)
f.rect((600,250,720,320),fill=180)
f.text(345,198,'低估 ＋ 高估',28)
f.text(365,272,'可能抵消',28)
f.save()

f=Figure('d12-01_manual.png',1200,1260)
f.text(60,48,'平均偏差为零，仍然每天都错',58)
f.text(60,150,'手算示例，非业务观测',50,60)
for y,txt in [(280,'实际：0、10   预测：2、8'),(410,'误差 = 实际 − 预测：−2、+2'),(560,'ME = 0     MAE = 2     RMSE = 2'),(710,'WAPE = (2+2) ÷ (0+10) = 40%')]:
    f.text(60,y,txt,50)
f.rect((50,870,1150,1145))
f.text(82,916,'零需求日仍贡献绝对误差。',52)
f.text(82,1020,'实际总量为零：WAPE 未定义。',52)
f.save()

f=Figure('d12-02_hewei.png',1200,1370)
f.text(60,48,'禾味 MA7：总平均藏住了方向',58)
f.text(60,152,'模拟验证段｜ME｜公斤/日',50,65)
for y,group,title,n in [(300,'all','总体',28),(535,'weekday','工作日',20),(770,'weekend','周末',8)]:
    r=score('hewei','MA7',group);v=float(r['me'])
    f.text(60,y,f'{title} n={n}：{v:+.4f}',56)
    f.path([(460,y+125),(1080,y+125)],width=2,fill=170)
    f.path([(650,y+70),(650,y+160)],width=3)
    end=650+v*50
    f.rect((min(end,650),y+98,max(end,650),y+150),fill=100)
f.text(60,1040,'负数：高估；正数：低估。',52)
f.text(60,1150,'按目标日分组：周一至五 / 周六日。',50)
f.text(60,1250,'不是节假日或门店营业日历。',50,65)
f.save()

f=Figure('d12-03_apparel.png',1200,1410)
f.text(60,48,'匿名服装：换指标，结论会变化',56)
f.text(60,150,'同一模拟验证段｜28 个目标｜件/日',48,65)
for y,key,label,maxv in [(310,'mae','MAE',50),(760,'rmse','RMSE',50)]:
    f.text(60,y,label,58)
    for i,(method,title,gray) in enumerate([('SNaive7','季节性朴素',80),('SES0.8','SES α=0.8',180)]):
        yy=y+130+i*140;v=float(score('apparel',method,'all')[key])
        f.text(60,yy,title,48)
        f.rect((415,yy,415+v/maxv*540,yy+68),fill=gray)
        f.text(1100,yy,f'{v:.2f}',48,anchor='rt')
f.text(60,1210,'MAE：季节基线更低；RMSE：SES更低。',48)
f.text(60,1310,'仅此段模拟比较，不代表真实收益。',48,65)
f.save()

f=Figure('d12-04_horizons.png',1200,1270)
f.text(60,48,'三种误差，先问在评价什么',58)
for y,title,body in [(230,'逐日一步预测','每天重新起点，28 个目标'),(490,'固定起点五天总量','同一时点发布五步，24 个窗口'),(750,'五天逐日绝对误差之和','每天错配不能通过正负抵消')]:
    f.rect((50,y-20,1150,y+168))
    f.text(80,y,title,54)
    f.text(80,y+92,body,50)
f.text(60,1030,'五日窗口仅覆盖 113—140 天。',52)
f.text(60,1140,'窗口相互重叠，不能视作独立样本。',50)
f.save()
(ROOT/'figure-tools/render-quality-report.json').write_text(json.dumps({'font_families':sorted(families),'font_sha256':hashlib.sha256(Path(FONT).read_bytes()).hexdigest(),'metrics_sha256':hashlib.sha256((ROOT/'practice/results/metrics.csv').read_bytes()).hexdigest(),'figures':REPORT},ensure_ascii=False,indent=2)+'\n')
print('Five grayscale figures rendered, glyph/bounds/text-overlap checks passed.')
