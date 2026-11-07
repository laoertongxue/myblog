#!/usr/bin/env python3
"""Draw D14 grayscale figures from the D14 replay metrics; no model fitting."""
from pathlib import Path
from itertools import combinations
import argparse,csv,hashlib,json,html,shutil,platform
from PIL import Image,ImageDraw,ImageFont,ImageChops
from fontTools.ttLib import TTFont
import PIL
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--font-path',type=Path,required=True)
p.add_argument('--font-index',type=int,default=0,help='TTC index; installed Noto Sans CJK SC is 2')
a=p.parse_args(); FONT=a.font_path.expanduser().resolve()
ROOT=Path(__file__).resolve().parents[1]
REPO=ROOT.parent.parent
IN_REPO=(ROOT.parent.name=='experiments' and (REPO/'hugo.toml').is_file())
OUT=ROOT/'images'; OUT.mkdir(parents=True,exist_ok=True)
BUNDLE=REPO/'content/blog/forecast-model-selection-boundaries/images'
font=TTFont(str(FONT),fontNumber=a.font_index); cmap=font.getBestCmap()
families={n.toUnicode() for n in font['name'].names if n.nameID in (1,16)}
assert families & {'Noto Sans SC','Noto Sans CJK SC'},families
METRICS=ROOT/'practice/results/metrics.csv'
rows=list(csv.DictReader(METRICS.open())); report=[]; S=2
class Figure:
 def __init__(self,name,w,h):
  self.name=name;self.w=w;self.h=h;self.texts=[];self.svg=[]
  self.im=Image.new('L',(w*S,h*S),255);self.d=ImageDraw.Draw(self.im)
 def text(self,x,y,s,size=32,fill=0):
  assert all(ord(c) in cmap or c.isspace() for c in s),s
  f=ImageFont.truetype(str(FONT),size*S,index=a.font_index)
  box=self.d.textbbox((x*S,y*S),s,font=f,anchor='lt'); b=[v/S for v in box]
  assert b[0]>=0 and b[1]>=0 and b[2]<=self.w and b[3]<=self.h,(s,b)
  self.d.text((x*S,y*S),s,font=f,fill=fill,anchor='lt')
  self.texts.append({'text':s,'font_size':size,'bbox':b})
  # SVG uses baseline position derived from the same font's text bounding box.
  baseline=y*S-self.d.textbbox((0,0),s,font=f,anchor='ls')[1]
  self.svg.append(f'<text x="{x}" y="{baseline/S}" font-size="{size}" fill="rgb({fill},{fill},{fill})">{html.escape(s)}</text>')
 def rect(self,b):
  self.d.rectangle(tuple(v*S for v in b),outline=0,width=2*S)
  self.svg.append(f'<rect x="{b[0]}" y="{b[1]}" width="{b[2]-b[0]}" height="{b[3]-b[1]}" fill="none" stroke="black" stroke-width="2"/>')
 def line(self,pts):
  self.d.line([(x*S,y*S) for x,y in pts],fill=0,width=3*S)
  self.svg.append('<polyline points="'+' '.join(f'{x},{y}' for x,y in pts)+'" fill="none" stroke="black" stroke-width="3"/>')
 def save(self,cover=False):
  for x,y in combinations(self.texts,2):
   b,c=x['bbox'],y['bbox']
   assert not(min(b[2],c[2])>max(b[0],c[0]) and min(b[3],c[3])>max(b[1],c[1])),(x,y)
  im=self.im.resize((self.w,self.h),Image.Resampling.LANCZOS).convert('RGB')
  for width in [self.w,350,280]:
   folder=OUT if width==self.w else OUT/f'preview-{width}';folder.mkdir(exist_ok=True)
   pic=im if width==self.w else im.resize((width,round(self.h*width/self.w)),Image.Resampling.LANCZOS)
   pic.save(folder/self.name,optimize=True)
   r,g,b=pic.split();assert ImageChops.difference(r,g).getbbox() is None and ImageChops.difference(g,b).getbbox() is None
  if IN_REPO and BUNDLE.is_dir():shutil.copy2(OUT/self.name,BUNDLE/self.name)
  svgpath=ROOT/'figure-tools'/self.name.replace('.png','.svg')
  svgpath.parent.mkdir(parents=True,exist_ok=True)
  svgpath.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" viewBox="0 0 {self.w} {self.h}"><rect width="100%" height="100%" fill="white"/><g font-family="Noto Sans CJK SC, Noto Sans SC" font-weight="400">'+''.join(self.svg)+'</g></svg>')
  if cover and IN_REPO and (REPO/'assets/cover-sources').is_dir():
   shutil.copy2(svgpath,REPO/'assets/cover-sources/d14-model-selection.svg')
  report.append({'file':self.name,'dimensions':[self.w,self.h],'grayscale':True,'text_overlap':False,'bounds_pass':True,'text_boxes':self.texts,'sha256':hashlib.sha256((OUT/self.name).read_bytes()).hexdigest()})
f=Figure('d14-00_cover.png',900,383)
f.text(42,25,'D14  /  MODEL SELECTION',25)
f.text(42,88,'先做基线，再谈选型',65)
for x,s in [(42,'任务'),(342,'数据'),(642,'候选')]:
 f.rect((x,210,x+212,292));f.text(x+60,230,s,42)
f.line([(262,251),(328,251),(315,240)]);f.line([(562,251),(628,251),(615,240)])
f.text(42,329,'没有脱离任务的“最好模型”',31)
f.save(cover=True)
f=Figure('d14-01_ranking-boundaries.png',700,1090)
f.text(30,30,'同一数据，不同决策',42)
f.text(30,97,'D13 回放 · 匿名服装 · 模拟数据',30)
for top,h,metric,title,method in [(175,'1','mae','一步预测 · MAE','SNaive7'),(425,'1','rmse','一步预测 · RMSE','SES0.8'),(675,'5','mae','固定五日累计 · MAE','MA14')]:
 candidates=[r for r in rows if r['case']=='apparel' and r['task_horizon']==h]
 r=min(candidates,key=lambda r:float(r[metric]));assert r['method']==method
 unit='件/日' if h=='1' else '件'
 f.rect((25,top,675,top+220));f.text(45,top+23,title,36)
 f.text(45,top+82,f'{method}  |  {float(r[metric]):.4f} {unit}',38)
 f.text(45,top+155,'仅在既有候选、该任务指标下最小',30)
f.text(30,950,'不共轴，不跨任务或指标比大小。',32)
f.text(30,1010,'这是局部排名，不是模型能力总榜。',32)
f.save()
f=Figure('d14-02_selection-cards.png',700,1530)
f.text(30,30,'先核对边界，再增加候选',40)
f.text(30,97,'以下路线 D14 均未实现、未评分',32)
for top,title,lines in [
 (170,'01  SARIMA',['观察季节性与自相关。','需要足够长、稳定的有序数据。','先核对序列，再谈季节参数。']),
 (490,'02  Croston 类',['先分清真实零与缺货零销量。','建模非零需求量及发生间隔。','不能修复缺货；经典 Croston 有偏。','间歇需求也要与简单基线比较。']),
 (890,'03  树模型',['输入滞后、日历、活动特征。','每个特征必须在预测时已知。','按时间划分，不能随机切分。','防跨实体泄漏，核对特征来源。'])]:
 height=280 if len(lines)==3 else 360
 f.rect((25,top,675,top+height));f.text(45,top+25,title,40)
 for i,s in enumerate(lines):f.text(45,top+100+i*60,s,31)
f.text(30,1320,'候选路线 ≠ 已证明更优',38)
f.text(30,1390,'图中没有新模型优劣数字。',32)
f.text(30,1450,'D14 的任务：明确何时值得试。',32)
f.save()
(ROOT/'figure-tools/render-quality-report.json').write_text(json.dumps({'python':platform.python_version(),'pillow':PIL.__version__,'font_families':sorted(families),'font_index':a.font_index,'font_sha256':hashlib.sha256(FONT.read_bytes()).hexdigest(),'metrics_source':'practice/results/metrics.csv','metrics_sha256':hashlib.sha256(METRICS.read_bytes()).hexdigest(),'figures':report},ensure_ascii=False,indent=2)+'\n')
print('Rendered three monochrome figures; glyphs, text bounds, and pairwise overlap checks passed.')

for width in [280,350]:
 ims=[Image.open(OUT/f'preview-{width}'/r['file']) for r in report]
 sheet=Image.new('RGB',(width*3+40,max(im.height for im in ims)+20),(221,221,221))
 for i,im in enumerate(ims):sheet.paste(im,(10+i*(width+10),10))
 sheet.save(OUT/f'preview-{width}/contact-sheet.png')
