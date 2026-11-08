#!/usr/bin/env python3
"""Draw D15 monochrome teaching diagrams with shared SVG/PNG layout."""
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
BUNDLE=REPO/'content/blog/inventory-position-event-timing/images'
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
   shutil.copy2(svgpath,REPO/'assets/cover-sources/d15-inventory-position.svg')
  report.append({'file':self.name,'dimensions':[self.w,self.h],'grayscale':True,'text_overlap':False,'bounds_pass':True,'text_boxes':self.texts,'sha256':hashlib.sha256((OUT/self.name).read_bytes()).hexdigest()})
f=Figure('d15-00_cover.png',900,383)
f.text(42,28,'D15  /  库存决策 · 教学模拟',25)
f.text(42,97,'库存够不够，先看时点',63)
for x,s in [(42,'到货'),(342,'需求'),(642,'下单')]:
 f.rect((x,221,x+212,301));f.text(x+63,240,s,42)
f.line([(265,261),(324,261),(312,250)]);f.line([(565,261),(624,261),(612,250)])
f.save(cover=True)
f=Figure('d15-01_event-timing.png',700,1240)
f.text(32,32,'先固定一天的顺序',44)
f.text(32,102,'教学模拟 · 每日复核 · L = 2',30)
for y,n,title,sub in [(180,'01','日初到货','已到货，才进入可用现货'),(355,'02','当日需求','用当日可用现货履约'),(530,'03','日末复核下单','新订单此时还不是现货')]:
 f.rect((32,y,668,y+132));f.text(52,y+22,n,34);f.text(125,y+18,title,38);f.text(125,y+78,sub,28)
 if y<530:f.line([(350,y+142),(350,y+162),(342,y+154)])
f.text(32,722,'这笔新订单，哪天能卖？',36)
for y,left,right in [(805,'t 日末','下单'),(884,'t+1 全天','等待第 1 天'),(963,'t+2 全天','等待第 2 天'),(1042,'t+3 日初','到货后可售')]:
 f.text(56,y,left,33);f.text(326,y,right,33)
 if y<1042:f.line([(38,y+15),(38,y+70)])
f.line([(310,865),(648,865)]);f.line([(310,1024),(648,1024)])
f.text(32,1155,'到货之前，不能提前拿它履约。',32)
f.save()
f=Figure('d15-02_inventory-position.png',700,1120)
f.text(32,32,'现货与库存位置，各管一件事',37)
f.text(32,102,'教学模拟 · 禾味 · 第 1 天日末下单前',28)
f.text(32,143,'单位：公斤',26)
f.rect((32,180,668,345));f.text(56,204,'今天能卖多少？看可用现货',33);f.text(56,267,'可用现货 = 5',42)
f.text(32,398,'该补多少？还要看有效在途',35)
f.rect((32,465,668,695));f.text(56,491,'库存位置 IP',34);f.text(56,554,'5 + 8 = 13',51);f.text(56,637,'现货 5 + 有效在途 8',30)
f.rect((32,750,668,928));f.text(56,777,'目标 S = 20',34);f.text(56,839,'下单量 = 20 − 13 = 7',39)
f.text(32,977,'下单后 IP = 20，现货仍为 5。',32)
f.text(32,1043,'在途不能当现货，也不能漏算。',32)
f.save()
f=Figure('d15-03_lost-sales.png',700,940)
f.text(32,32,'失销，不是明天的欠交',42)
f.text(32,102,'教学模拟 · 禾味 · 第 3 天 · 单位：公斤',28)
f.rect((32,180,668,350));f.text(56,206,'当日可用现货 4',40);f.text(56,274,'当日需求 8',40)
f.line([(350,367),(350,414),(340,404)])
f.rect((32,438,331,598));f.text(58,463,'履约',33);f.text(58,522,'4',51)
f.rect((369,438,668,598));f.text(395,463,'失销',33);f.text(395,522,'4',51)
f.text(32,652,'日末现货 = 0',40)
f.text(32,729,'未满足的 4 不转为次日欠交。',33)
f.line([(32,800),(668,800)])
f.text(32,837,'真实业务若承诺欠交，须另建规则。',31)
f.save()
(ROOT/'figure-tools/render-quality-report.json').write_text(json.dumps({'python':platform.python_version(),'pillow':PIL.__version__,'font_families':sorted(families),'font_index':a.font_index,'font_sha256':hashlib.sha256(FONT.read_bytes()).hexdigest(),'scenario':{'label':'教学模拟','initial_on_hand':12,'initial_pipeline_due_day':2,'initial_pipeline_qty':8,'lead_time_full_days':2,'target':20,'demand':[7,9,8,4,5,6,3]},'figures':report},ensure_ascii=False,indent=2)+'\n')
print('Rendered four monochrome figures; glyphs, bounds and pairwise text overlap passed.')
for width in [280,350]:
 ims=[Image.open(OUT/f'preview-{width}'/r['file']) for r in report]
 sheet=Image.new('RGB',(width*4+50,max(im.height for im in ims)+20),'white')
 for i,im in enumerate(ims):sheet.paste(im,(10+i*(width+10),10))
 sheet.save(OUT/f'preview-{width}/contact-sheet.png')
