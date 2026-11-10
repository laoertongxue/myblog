#!/usr/bin/env python3
"""Draw D17 monochrome teaching diagrams with shared SVG/PNG layout."""
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
BUNDLE=REPO/'content/blog/periodic-review-order-up-to/images'
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
   shutil.copy2(svgpath,REPO/'assets/cover-sources/d17-periodic-review.svg')
  report.append({'file':self.name,'dimensions':[self.w,self.h],'grayscale':True,'text_overlap':False,'bounds_pass':True,'text_boxes':self.texts,'sha256':hashlib.sha256((OUT/self.name).read_bytes()).hexdigest()})
f=Figure('d17-00_cover.png',900,383)
f.text(40,28,'D17  /  定期复核 · 教学模拟',25)
f.text(40,94,'到复核日，再补到目标',58)
f.rect((40,220,393,317));f.text(64,244,'每隔 R 天',44)
f.line([(415,267),(475,267),(462,254)])
f.rect((499,220,860,317));f.text(523,244,'补至目标 S',44)
f.save(cover=True)
f=Figure('d17-01_calendar.png',700,1090)
f.text(32,32,'先看日期，再算订货量',43)
f.text(32,108,'教学模拟 · R = 2，首次第 2 日',32)
for y,day,decision in [(193,'第 2 日','复核：按 S 与 IP 算量'),(380,'第 3 日','非复核：即使 IP = 0'),(567,'第 4 日','复核：再次计算订货量')]:
 f.rect((32,y,668,y+155));f.text(56,y+22,day,40);f.text(56,y+92,decision,34)
f.text(32,775,'复核日：第 2、4、6……日末',35)
f.line([(32,854),(668,854)])
f.text(32,897,'非复核日：q = 0',43)
f.text(32,981,'缺货不会自动打开订货窗口。',33)
f.save()
f=Figure('d17-02_order-up-to.png',700,1430)
f.text(32,32,'补的是库存位置缺口',43)
f.text(32,108,'教学模拟 · 数量单位：公斤',32)
f.rect((32,181,668,353));f.text(56,209,'仅复核日',34);f.text(56,281,'q = max(0, S − IP)',44)
f.text(32,402,'IP = OH + OO − BO',41)
f.text(32,476,'现货 + 有效在途 − 欠交',35)
f.text(32,543,'主案例为失销：BO = 0',35)
f.rect((32,630,668,895));f.text(56,657,'第 2 日末：S = 20，IP = 4',36)
f.text(56,734,'下单 q = 16，IP 补到 20',36)
f.text(56,790,'下单时不增现货',32);f.text(56,836,'第 5 日初到货后才可用',32)
f.text(32,928,'若复核时 IP = 20 或 22',36)
f.text(32,996,'q 均为 0；不下负数订单。',35)
f.line([(32,1075),(668,1075)])
f.text(32,1123,'欠交示意（非主案例）',37)
f.text(32,1195,'IP = 5 + 8 − 3 = 10',40)
f.text(32,1271,'若到复核日，S = 20 → q = 10',33)
f.text(32,1350,'S 是目标，不是固定订货批量。',32)
f.save()
f=Figure('d17-03_timing.png',700,1510)
f.text(32,32,'时点写清，保护期才清楚',41)
f.text(32,108,'教学模拟 · R = 2，L = 2',32)
f.rect((32,180,668,380));f.text(56,210,'每天：到货 → 需求 → 日末复核',32)
f.text(56,283,'L 表示下单后完整等待日数',33)
f.text(56,337,'非复核日跳过下单',32)
for y,title,sub in [(438,'第 2 日日末','本次复核并下单'),(618,'第 4 日日末','下次复核；q > 0 才下单'),(798,'第 5 日日初','第 2 日的订单到货'),(978,'第 7 日日初','第 4 日若下单，此时到货')]:
 f.rect((32,y,668,y+135));f.text(56,y+20,title,38);f.text(56,y+82,sub,33)
 if y<978:f.line([(350,y+144),(350,y+168),(341,y+159)])
f.line([(32,1162),(668,1162)])
f.text(32,1206,'本次复核后，到下次订单可售前',32)
f.text(32,1272,'第 3–6 日：共 R + L = 4 天',37)
f.text(32,1349,'可作需求保护期的起点。',34)
f.text(32,1420,'设定 S 仍须核对时点与缺货风险。',32)
f.save()
(ROOT/'figure-tools/render-quality-report.json').write_text(json.dumps({'python':platform.python_version(),'pillow':PIL.__version__,'font_families':sorted(families),'font_index':a.font_index,'font_sha256':hashlib.sha256(FONT.read_bytes()).hexdigest(),'scenario':{'label':'教学模拟','unit':'公斤','review_interval':2,'first_review_day':2,'target':20,'lead_time_full_days':2,'arrival':'order t end arrives t+3 start','unmet_demand':'lost sales, no backlog','backlog_example':'separate illustrative model only'},'figures':report},ensure_ascii=False,indent=2)+'\n')
print('Rendered four monochrome figures; glyphs, bounds and pairwise text overlap passed.')
for width in [280,350]:
 ims=[Image.open(OUT/f'preview-{width}'/r['file']) for r in report]
 sheet=Image.new('RGB',(width*4+50,max(im.height for im in ims)+20),'white')
 for i,im in enumerate(ims):sheet.paste(im,(10+i*(width+10),10))
 sheet.save(OUT/f'preview-{width}/contact-sheet.png')
