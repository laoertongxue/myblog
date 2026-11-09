#!/usr/bin/env python3
"""Draw D16 monochrome teaching diagrams with shared SVG/PNG layout."""
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
BUNDLE=REPO/'content/blog/fixed-batch-reorder-threshold/images'
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
   shutil.copy2(svgpath,REPO/'assets/cover-sources/d16-fixed-batch.svg')
  report.append({'file':self.name,'dimensions':[self.w,self.h],'grayscale':True,'text_overlap':False,'bounds_pass':True,'text_boxes':self.texts,'sha256':hashlib.sha256((OUT/self.name).read_bytes()).hexdigest()})
f=Figure('d16-00_cover.png',900,383)
f.text(42,28,'D16  /  固定批量 · 教学模拟',25)
f.text(42,97,'到阈值，就补一批',65)
f.rect((42,220,400,310));f.text(72,243,'IP ≤ r',44)
f.line([(425,265),(493,265),(480,253)])
f.rect((520,220,858,310));f.text(548,243,'只订一批 Q',44)
f.save(cover=True)
f=Figure('d16-01_rule.png',700,1120)
f.text(32,32,'每天只检查一次',46)
f.text(32,106,'教学模拟 · 日末固定批量规则',32)
for y,cond,action in [(190,'IP > r','不下单：订货量 0'),(400,'IP = r','触发：订货量 Q'),(610,'IP < r','也只下单一批 Q')]:
 f.rect((32,y,668,y+170));f.text(56,y+22,cond,46);f.text(56,y+102,action,36)
f.text(32,833,'r 是触发阈值，Q 是固定批量。',33)
f.text(32,899,'不是补到 r，也不是补到目标 S。',32)
f.line([(32,967),(668,967)])
f.text(32,1008,'每日复核，不是连续复核。',36)
f.save()
f=Figure('d16-02_one-batch.png',700,1290)
f.text(32,32,'低于阈值，也只补一批',43)
f.text(32,106,'教学模拟 · 单位：公斤',32)
f.rect((32,182,668,359));f.text(56,208,'日末下单前',34);f.text(56,277,'IP = 3，r = 10，Q = 6',38)
f.line([(350,379),(350,419),(340,409)])
f.rect((32,444,668,612));f.text(56,470,'3 ≤ 10：触发一次',37);f.text(56,541,'当天只下一单 6 公斤',38)
f.line([(350,632),(350,672),(340,662)])
f.rect((32,697,668,876));f.text(56,724,'下单后 IP = 3 + 6 = 9',38);f.text(56,800,'9 ≤ 10，但本次复核已结束',33)
f.text(32,930,'不能用 while 循环继续追单。',34)
f.text(32,1000,'下一次检查：明天日末。',36)
f.line([(32,1074),(668,1074)])
f.text(32,1125,'新订单进入在途，不进入现货。',33)
f.text(32,1195,'下单 ≠ 到货，不能立刻拿来卖。',32)
f.save()
f=Figure('d16-03_timing.png',700,1440)
f.text(32,32,'先后顺序，决定哪天能卖',42)
f.text(32,106,'教学模拟 · L = 2 个完整等待日',32)
for y,title,sub in [(190,'01  日初到货','到货后，才增加可用现货'),(365,'02  当日需求','现货履约；不足部分记失销'),(540,'03  日末检查与下单','只检查一次；新单增加在途')]:
 f.rect((32,y,668,y+135));f.text(56,y+20,title,36);f.text(56,y+80,sub,32)
 if y<540:f.line([(350,y+144),(350,y+165),(342,y+157)])
f.text(32,732,'t 日末下的单，何时到？',38)
for y,left,right in [(822,'t 日末','下单'),(911,'t+1 全天','完整等待第 1 天'),(1000,'t+2 全天','完整等待第 2 天'),(1089,'t+3 日初','到货，开始可售')]:
 f.text(56,y,left,34);f.text(300,y,right,32)
 if y<1089:f.line([(37,y+18),(37,y+79)])
f.line([(32,1185),(668,1185)])
f.text(32,1235,'失销不转为明天的欠交。',36)
f.text(32,1310,'IP = 日末现货 + 有效在途',34)
f.save()
(ROOT/'figure-tools/render-quality-report.json').write_text(json.dumps({'python':platform.python_version(),'pillow':PIL.__version__,'font_families':sorted(families),'font_index':a.font_index,'font_sha256':hashlib.sha256(FONT.read_bytes()).hexdigest(),'scenario':{'label':'教学模拟','unit':'公斤','review':'daily end, at most one order','counterexample':{'inventory_position_before':3,'reorder_point':10,'fixed_batch':6,'inventory_position_after':9},'lead_time_full_days':2,'arrival':'order t end arrives t+3 start','unmet_demand':'lost sales, no backlog'},'figures':report},ensure_ascii=False,indent=2)+'\n')
print('Rendered four monochrome figures; glyphs, bounds and pairwise text overlap passed.')
for width in [280,350]:
 ims=[Image.open(OUT/f'preview-{width}'/r['file']) for r in report]
 sheet=Image.new('RGB',(width*4+50,max(im.height for im in ims)+20),'white')
 for i,im in enumerate(ims):sheet.paste(im,(10+i*(width+10),10))
 sheet.save(OUT/f'preview-{width}/contact-sheet.png')
