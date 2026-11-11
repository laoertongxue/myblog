#!/usr/bin/env python3
"""Draw D18 monochrome teaching diagrams with shared SVG/PNG layout."""
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
BUNDLE=REPO/'content/blog/safety-stock-service-level/images'
font=TTFont(str(FONT),fontNumber=a.font_index); cmap=font.getBestCmap()
families={n.toUnicode() for n in font['name'].names if n.nameID in (1,16)}
assert families & {'Noto Sans SC','Noto Sans CJK SC'},families
report=[]; S=2
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
   shutil.copy2(svgpath,REPO/'assets/cover-sources/d18-safety-stock.svg')
  report.append({'file':self.name,'dimensions':[self.w,self.h],'grayscale':True,'text_overlap':False,'bounds_pass':True,'text_boxes':self.texts,'sha256':hashlib.sha256((OUT/self.name).read_bytes()).hexdigest()})
f=Figure('d18-00_cover.png',900,383)
f.text(40,28,'D18  /  安全库存 · 教学模拟',25)
f.text(40,94,'服务水平，先说清分母',56)
f.rect((40,220,393,317));f.text(66,248,'多少周期不缺货',36)
f.rect((499,220,860,317));f.text(523,248,'多少需求被满足',36)
f.save(cover=True)
f=Figure('d18-01_service.png',700,1190)
f.text(32,32,'同一条路径，两种服务指标',40)
f.text(32,112,'独立指标示意 · 数量单位：公斤',32)
f.rect((32,188,668,460));f.text(56,216,'四个完整周期，各需求 20',36)
f.text(56,292,'履约：20、20、20、19',39)
f.text(56,374,'失销：  0、  0、  0、  1',37)
f.text(32,516,'周期无缺货率',42)
f.text(32,592,'3 ÷ 4 = 75%',48)
f.text(32,691,'单位满足率',42)
f.text(32,768,'79 ÷ 80 = 98.75%',43)
f.line([(32,865),(668,865)])
f.text(32,910,'零需求周期：保留在周期分母',34)
f.text(32,980,'全窗口零需求：单位满足率 N/A',32)
f.text(32,1060,'这是指标算例，不是服务承诺。',33)
f.save()
f=Figure('d18-02_buffer.png',700,1480)
f.text(32,32,'先找保护期，再计算缓冲',40)
f.text(32,112,'禾味公式算例 · 公斤 · 教学模拟',32)
f.rect((32,190,668,430));f.text(56,220,'R = 2，L = 2，H = 4 天',35)
f.text(56,297,'日均需求 6，日标准差 2',36)
f.text(56,367,'σH = 2 × √4 = 4',39)
f.text(32,489,'安全系数 z = 1.645',39)
f.text(32,564,'SS = 1.645 × 4 = 6.58',40)
f.text(32,651,'连续目标 S* = 6 × 4 + 6.58',34)
f.text(32,720,'S* = 30.58，取整 S = 31',40)
f.line([(32,815),(668,815)])
f.text(32,860,'固定 H、每日独立同分布时',34)
f.text(32,930,'可用 σH = σ日 × √H。',36)
f.text(32,1028,'把 z 对应到约 95%：',36)
f.text(32,1100,'还要保护期需求近似正态，',33)
f.text(32,1170,'均值估计可靠，事件时点相符。',32)
f.text(32,1276,'失销回放仍须逐日核验。',36)
f.text(32,1360,'不能承诺单位满足率为 95%。',33)
f.save()
f=Figure('d18-03_freeze.png',700,1300)
f.text(32,32,'先验证，再冻结，最后测试',40)
f.text(32,112,'本篇只运行公开机制回放',33)
for y,title,sub in [(198,'开发 / 验证','选候选、指标、周期与舍入规则'),(418,'冻结策略卡','锁定参数、输入范围和事件时序'),(638,'未见测试','冻结后只评估，不回头挑参数')]:
 f.rect((32,y,668,y+160));f.text(56,y+24,title,42);f.text(56,y+100,sub,31)
 if y<638:f.line([(350,y+173),(350,y+208),(340,y+198)])
f.line([(32,868),(668,868)])
f.text(32,915,'D18 的三个 z 均为事前给定。',33)
f.text(32,990,'比较用于理解，不选择冠军。',34)
f.text(32,1075,'不读取 D9 封存段。',37)
f.text(32,1155,'不提前运行 D20 最终评估。',34)
f.save()
(ROOT/'figure-tools/render-quality-report.json').write_text(json.dumps({'python':platform.python_version(),'pillow':PIL.__version__,'font_families':sorted(families),'font_index':a.font_index,'font_sha256':hashlib.sha256(FONT.read_bytes()).hexdigest(),'figures':report},ensure_ascii=False,indent=2)+'\n')
print('Rendered four monochrome figures; glyphs, bounds and pairwise text overlap passed.')
for width in [280,350]:
 ims=[Image.open(OUT/f'preview-{width}'/r['file']) for r in report]
 sheet=Image.new('RGB',(width*4+50,max(im.height for im in ims)+20),'white')
 for i,im in enumerate(ims):sheet.paste(im,(10+i*(width+10),10))
 sheet.save(OUT/f'preview-{width}/contact-sheet.png')
