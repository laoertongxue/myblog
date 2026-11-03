#!/usr/bin/env python3
"""Reproduce D10 monochrome teaching figures, using only development CSVs.

Never reads D9 sealed/ or results/test.json. All Chinese uses Noto Sans CJK SC
(face 2), not a Japanese fallback. Pillow L canvases guarantee R == G == B.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from fontTools.ttLib import TTCollection, TTFont
import argparse, csv, hashlib, json, math
from itertools import combinations

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'images'; MOBILE=OUT/'mobile'; MOBILE320=OUT/'mobile-320'; TOOLS=ROOT/'figure-tools'
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--data-dir',type=Path,default=ROOT/'practice'/'data',help='Directory with the two unchanged D9-v1 140-row development CSVs (default: ROOT/practice/data).')
parser.add_argument('--font-path',type=Path,default=Path('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'),help='Noto Sans CJK SC font/collection path; no fallback permitted.')
parser.add_argument('--font-face',type=int,default=2,help='Collection face index (default 2: SC in system NotoSansCJK-Regular.ttc; use 0 for a standalone SC font).')
args=parser.parse_args()
SRC=args.data_dir.resolve()
OUT.mkdir(parents=True,exist_ok=True); MOBILE.mkdir(parents=True,exist_ok=True); MOBILE320.mkdir(parents=True,exist_ok=True); TOOLS.mkdir(parents=True,exist_ok=True)
FONT=str(args.font_path.expanduser().resolve())
FACE=args.font_face; SCALE=2
if not Path(FONT).exists():
    parser.error('Noto SC font not found; supply --font-path and the correct --font-face for your local font.')
TEXTS=[]; DRAWINGS=[]; CURVES={}
SOURCES={}
SOURCE_ZIP_SHA256='0063b6ddae7459eff9dc7779c0a0a6c9ecef8d0bd48320c653eae1c072ce1c31'
archive=ROOT/'source'/'d9-seasonal-naive-practice.zip'
ACTUAL_ZIP_SHA256=None
if archive.exists():
    ACTUAL_ZIP_SHA256=hashlib.sha256(archive.read_bytes()).hexdigest()
    assert ACTUAL_ZIP_SHA256==SOURCE_ZIP_SHA256
ZIP_VERIFICATION_STATUS='verified_from_optional_archive' if ACTUAL_ZIP_SHA256 else 'archive_not_bundled_declared_hash_only'
EXPECTED_CSV_SHA256={
 'hewei':'292072a63439529f22a73d41b83516928ae5a5b474b907b33d42e74962c23407',
 'apparel':'56badd2fc37decd72b2f55a980acb7add2594b96c7b8d269f6aaae59ee7d47e5'}
for case in ['hewei','apparel']:
    p=SRC/f'{case}-development.csv'
    raw=p.read_bytes(); actual_hash=hashlib.sha256(raw).hexdigest()
    assert actual_hash==EXPECTED_CSV_SHA256[case],f'Unexpected development CSV hash: {p}'
    source_label=str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p)
    SOURCES[source_label]=actual_hash
    rows=list(csv.DictReader(raw.decode('utf-8-sig').splitlines()))
    assert [int(r['day']) for r in rows]==list(range(1,141))
    assert [r['split'] for r in rows]==['train']*112+['validation']*28
    vals=[float(r['demand']) for r in rows]
    actual=vals[112:140]
    preds={k:[sum(vals[d-k-1:d-1])/k for d in range(113,141)] for k in [3,7,14]}
    CURVES[case]={'days':list(range(113,141)),'actual':actual,'predictions':preds}

def ff(n): return ImageFont.truetype(FONT,round(n*SCALE),index=FACE)
def polyseg(draw,p0,p1,fill=0,width=3):
    draw.line(tuple(round(x*SCALE) for p in [p0,p1] for x in p),fill=fill,width=max(1,round(width*SCALE)))
def styled(draw,pts,style='solid',width=3,fill=0):
    if style=='solid':
        draw.line([(round(x*SCALE),round(y*SCALE)) for x,y in pts],fill=fill,width=round(width*SCALE),joint='curve'); return
    pattern={'dash':[16,10],'dot':[3,9],'dashdot':[18,7,3,7]}[style]
    index=0; remain=pattern[0]; ink=True
    for a,b in zip(pts,pts[1:]):
        dx=b[0]-a[0]; dy=b[1]-a[1]; length=math.hypot(dx,dy)
        if not length: continue
        used=0
        while used<length-1e-8:
            take=min(remain,length-used)
            if ink: polyseg(draw,(a[0]+dx*used/length,a[1]+dy*used/length),(a[0]+dx*(used+take)/length,a[1]+dy*(used+take)/length),fill,width)
            used+=take; remain-=take
            if remain<1e-8:
                index=(index+1)%len(pattern); remain=pattern[index]; ink=index%2==0

class Figure:
    def __init__(self,name,w,h):
        self.name=name; self.w=w; self.h=h
        self.im=Image.new('L',(w*SCALE,h*SCALE),255); self.d=ImageDraw.Draw(self.im); self.boxes=[]
    def text(self,x,y,s,size=36,fill=0,anchor='lt',role='body'):
        font=ff(size); xy=(round(x*SCALE),round(y*SCALE))
        bbox=self.d.textbbox(xy,s,font=font,anchor=anchor)
        self.d.text(xy,s,font=font,fill=fill,anchor=anchor)
        b=[v/SCALE for v in bbox]
        rec={'text':s,'font_px':size,'bbox':b,'role':role}
        self.boxes.append(rec); TEXTS.append(s)
        assert b[0]>=0 and b[1]>=0 and b[2]<=self.w and b[3]<=self.h, (self.name,rec)
        return b
    def line(self,xy,width=2,fill=0,style='solid'):
        styled(self.d,list(zip(xy[::2],xy[1::2])),style,width,fill)
    def rect(self,box,fill=None,outline=0,width=2):
        self.d.rectangle(tuple(round(v*SCALE) for v in box),fill=fill,outline=outline,width=round(width*SCALE))
    def circle(self,x,y,r=5,fill=0,outline=None,width=1):
        self.d.ellipse(tuple(round(v*SCALE) for v in [x-r,y-r,x+r,y+r]),fill=fill,outline=outline,width=round(width*SCALE))
    def arrow(self,x1,y1,x2,y2,width=3,fill=0):
        self.line([x1,y1,x2,y2],width,fill)
        a=math.atan2(y2-y1,x2-x1); length=13
        for turn in [-.48,.48]: self.line([x2,y2,x2-length*math.cos(a+turn),y2-length*math.sin(a+turn)],width,fill)
    def save(self):
        self.im=self.im.resize((self.w,self.h),Image.Resampling.LANCZOS).convert('RGB')
        path=OUT/self.name; self.im.save(path,optimize=True)
        mh=round(self.h*390/self.w)
        self.im.resize((390,mh),Image.Resampling.LANCZOS).save(MOBILE/self.name,optimize=True)
        self.im.resize((320,round(self.h*320/self.w)),Image.Resampling.LANCZOS).save(MOBILE320/self.name,optimize=True)
        overlaps=[]
        for a,b in combinations(self.boxes,2):
            aa=a['bbox']; bb=b['bbox']
            if min(aa[2],bb[2])>max(aa[0],bb[0]) and min(aa[3],bb[3])>max(aa[1],bb[1]): overlaps.append([a['text'],b['text']])
        DRAWINGS.append({'file':str(path.relative_to(ROOT)),'width':self.w,'height':self.h,'minimum_text_font_px':min(b['font_px'] for b in self.boxes),'minimum_essential_text_font_px':min([b['font_px'] for b in self.boxes if b['role']=='body'] or [min(b['font_px'] for b in self.boxes)]),'text_boxes':self.boxes,'text_box_overlaps':overlaps})
        assert not overlaps,(self.name,overlaps)

def head(f,kicker,title,subtitle):
    f.text(68,40,kicker,32,90,role='kicker')
    f.text(68,100,title,54)
    f.text(68,187,subtitle,46,65)
    f.line([68,280,f.w-68,280],2,155)

def legend(f,x,y,label,style='solid',size=34):
    f.line([x,y+20,x+86,y+20],4,0,style)
    f.text(x+104,y,label,size)

# 00 exact-size cover. Numbers are intentionally omitted: this is mechanism only.
f=Figure('d10-00_cover.png',900,383)
f.text(44,25,'D10  /  MOVING AVERAGE',23,75,role='cover')
f.text(44,71,'移动平均：先把预测对齐',49,role='cover')
f.text(44,145,'只看已知历史，不把未来混进窗口',30,60,role='cover')
# History and future are diagrammatic, not measured demand.
pts=[(60,265),(109,244),(158,274),(207,228),(256,253),(305,215),(354,241)]
f.line([v for p in pts for v in p],3)
for x,y in pts: f.circle(x,y,4)
f.line([400,205,400,300],2,100,'dash')
f.text(228,299,'已知的最近 k 天',26,anchor='mt',role='cover')
f.arrow(373,254,449,254,3)
for x in [487,562,637,712,787]: f.circle(x,253,6,255,0,2)
f.line([464,253,808,253],3,0,'dash')
f.text(639,299,'未来 5 天：同一个均值',26,anchor='mt',role='cover')
f.text(44,350,'固定起点：平均一次，复制五次。',26,70,role='cover')
f.save()

# 01 date alignment plus deliberately synthetic step-response illustration.
f=Figure('d10-01_alignment.png',1200,1680)
head(f,'01  /  对齐机制','一个均值，两个日期','历史为 10、20、30；均值为 20')
xs=[210,470,730,990]
for x,n,t in zip(xs,['10','20','30','？'],['第 1 天','第 2 天','第 3 天','第 4 天']):
    f.rect([x-83,330,x+83,426],fill=247,outline=0,width=2)
    f.text(x,343,n,52,anchor='mt')
    f.text(x,452,t,46,anchor='mt')
f.line([114,522,1088,522],2,125)
f.text(88,555,'（10＋20＋30）÷3＝20',46)
f.text(88,643,'平滑：记在第 3 天',46)
f.text(88,720,'预测：对齐第 4 天',46)
f.rect([648,630,812,749],fill=255,outline=0,width=2)
f.text(730,639,'20',48,anchor='mt')
f.text(730,696,'平滑值',46,anchor='mt')
f.arrow(828,687,891,687,3)
f.rect([906,630,1074,749],fill=242,outline=0,width=2)
f.text(990,639,'20',48,anchor='mt')
f.text(990,696,'预测值',46,anchor='mt')
f.text(858,778,'后移 1 天',46,80,anchor='mt')
f.line([68,858,1132,858],2,155)
f.text(68,895,'窗口取舍：平滑，也会滞后',46)
f.text(68,970,'合成阶跃｜滚动一步预测',46,65)
legend(f,88,1049,'合成实际','solid',46)
legend(f,486,1049,'k＝3','dash',46)
legend(f,827,1049,'k＝7','dot',46)
x0,y0,w,h=100,1170,1000,290
f.line([x0,y0+h,x0+w,y0+h],2,120)
f.line([x0,y0,x0,y0+h],2,120)
vals=[10]*5+[30]*7
series=[vals]+[[sum(([10]*k+vals)[i:i+k])/k for i in range(len(vals))] for k in [3,7]]
for yy,style in zip(series,['solid','dash','dot']):
    points=[(x0+i*w/11,y0+h-(v-8)/25*h) for i,v in enumerate(yy)]
    if style=='solid':
        pts=[points[0]]
        for a,b in zip(points,points[1:]): pts.extend([(b[0],a[1]),b])
        styled(f.d,pts,style,4)
    else: styled(f.d,points,style,4)
f.text(1110,1483,'时间 →',46,80,anchor='rt')
f.text(68,1554,'机制示意，不是验证结果。',46,65)
f.text(68,1610,'不能据此选出更好的 k。',46)
f.save()

# 02 D9 test results were published; D10 neither rereads nor scores those labels.
f=Figure('d10-02_split.png',1200,1620)
head(f,'02  /  评估边界','先切分，再滚动','本篇只读前 140 天的开发集')
f.text(68,318,'D9 已公开原测试汇总；D10 不再评分。',46)
for x1,x2,title,span,shade in [(68,409,'训练段','第 1–112 天',244),(429,771,'验证段','第 113–140 天',225),(791,1132,'D10 不评分','第 141–180 天',255)]:
    f.rect([x1,403,x2,557],fill=shade,outline=0,width=2)
    f.text((x1+x2)/2,420,title,46,anchor='mt')
    f.text((x1+x2)/2,488,span,46,anchor='mt')
f.text(68,590,'区间长度示意，不按比例。',34,85,role='secondary')
f.text(68,672,'28 次日预测',46)
f.text(68,747,'起点 112–139 → 目标 113–140',46)
x0,x1=91,1109; sw=(x1-x0)/28
for i in range(28):
    cx=x0+(i+.5)*sw; f.circle(cx,849,5)
f.line([x0,849,x1,849],2,105)
for day in [113,117,124,131,140]:
    cx=x0+(day-113+.5)*sw
    f.line([cx,859,cx,872],2,100)
    f.text(cx,890,str(day),46,anchor='mt')
f.text(68,994,'首个 5 日窗：113–117',46)
f.text(1120,994,'起点 112',46,anchor='rt')
for i in range(28): f.rect([x0+i*sw,1073,x0+(i+1)*sw-3,1138],fill=205 if i<5 else 252,outline=120,width=1)
f.text(68,1200,'末个 5 日窗：136–140',46)
f.text(1120,1200,'起点 135',46,anchor='rt')
for i in range(28): f.rect([x0+i*sw,1279,x0+(i+1)*sw-3,1344],fill=205 if i>=23 else 252,outline=120,width=1)
f.text(68,1411,'24 个重叠的 5 日窗',46)
f.text(68,1486,'完整落在验证段，不跨边界。',46)
f.text(68,1557,'重叠窗口不是独立样本。',46,65)
f.save()

# 03 / 04: simulated validation data; daily rolling h=1, never fixed-origin h=5.
for case,name,title,unit,top,ticks in [
    ('hewei','d10-03_hewei.png','禾味 A 店 SKU01｜验证段','kg/日',50,[0,10,20,30,40,50]),
    ('apparel','d10-04_apparel.png','匿名服饰订单｜验证段','件/日',280,[0,50,100,150,200,250])]:
    f=Figure(name,1200,1370)
    f.text(68,40,'03  /  模拟结果' if case=='hewei' else '04  /  模拟结果',32,90,role='kicker')
    f.text(68,105,title,50)
    f.text(68,187,'教学模拟｜滚动一步（h＝1）',46,65)
    legend(f,85,284,'模拟实际','solid',46)
    legend(f,652,284,'MA3','dash',46)
    legend(f,85,362,'MA7','dot',46)
    legend(f,652,362,'MA14','dashdot',46)
    f.text(68,452,f'需求（{unit}）',46,65)
    left,right,upper,bottom=150,1128,550,985
    X=lambda d:left+(d-113)/(140-113)*(right-left)
    Y=lambda v:bottom-v/top*(bottom-upper)
    for tick in ticks:
        yy=Y(tick); f.line([left,yy,right,yy],1,218)
        f.text(left-18,yy,str(tick),46,70,anchor='rm')
    f.line([left,upper,left,bottom,right,bottom],2,100)
    for d in [113,117,121,125,129,133,137,140]:
        xx=X(d); f.line([xx,bottom,xx,bottom+10],2,100)
        f.text(xx,bottom+23,str(d),46,70,anchor='mt')
    f.text(1128,1081,'目标日',46,65,anchor='rt')
    curves=CURVES[case]
    for k,style in [(3,'dash'),(7,'dot'),(14,'dashdot')]:
        styled(f.d,[(X(d),Y(v)) for d,v in zip(curves['days'],curves['predictions'][k])],style,4)
    actualpts=[(X(d),Y(v)) for d,v in zip(curves['days'],curves['actual'])]
    styled(f.d,actualpts,'solid',4)
    for x,y in actualpts: f.circle(x,y,3)
    f.text(68,1170,'只用此前 k 天的已知值。',46)
    f.text(68,1240,'不是固定起点 5 步预测。',46)
    bottomnote='仅用于教学，不是真实经营数据。' if case=='hewei' else '118–120 天人为加量（模拟设定）。'
    f.text(68,1310,bottomnote,46,65)
    f.save()

# Pixel, typeface, geometry and source checks.
if Path(FONT).read_bytes()[:4]==b'ttcf':
    face=TTCollection(FONT).fonts[FACE]
else:
    assert FACE==0,'A standalone SC font requires --font-face 0.'
    face=TTFont(FONT)
family=next(n.toUnicode() for n in face['name'].names if n.nameID==1 and n.platformID==3)
assert family in {'Noto Sans CJK SC','Noto Sans SC'},f'Simplified-Chinese Noto face required, got {family!r}'
cmap=face.getBestCmap(); allchars=set(''.join(TEXTS)); missing=sorted(c for c in allchars if not c.isspace() and ord(c) not in cmap)
assert not missing,missing
pixelchecks=[]
for f in DRAWINGS:
    path=ROOT/f['file']; im=Image.open(path)
    assert im.mode=='RGB'
    r,g,b=im.split(); equal=r.tobytes()==g.tobytes()==b.tobytes()
    assert equal
    pixelchecks.append({'file':f['file'],'mode':'RGB','channels_equal_every_pixel':equal,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'mobile_preview':str((MOBILE/path.name).relative_to(ROOT)),'mobile_preview_320':str((MOBILE320/path.name).relative_to(ROOT))})
assert DRAWINGS[0]['width']==900 and DRAWINGS[0]['height']==383
assert all(f['width']>=1000 for f in DRAWINGS[1:])
# If the separately-produced practice output exists, compare every plotted MA value.
practice=ROOT/'practice'/'results'/'daily_predictions.csv'
practicecheck={'status':'not_available'}
if practice.exists():
    rows=list(csv.DictReader(practice.read_text().splitlines())); compared=0
    for row in rows:
        if row['method'] not in ['MA3','MA7','MA14']: continue
        case=row['case']; k=int(row['method'][2:]); day=int(row['target_day'])
        actual=CURVES[case]['actual'][day-113]; pred=CURVES[case]['predictions'][k][day-113]
        assert abs(actual-float(row['actual']))<1e-10
        assert abs(pred-float(row['prediction']))<1e-10
        compared+=1
    assert compared==2*3*28
    practicecheck={'status':'matched','rows_compared':compared,'sha256':hashlib.sha256(practice.read_bytes()).hexdigest()}
report={
 'source_zip_sha256_declared':SOURCE_ZIP_SHA256,
 'source_zip_sha256_verified':ACTUAL_ZIP_SHA256,
 'source_zip_verification_status':ZIP_VERIFICATION_STATUS,
 'development_csv_hash_validation':'Both input files matched the fixed original D9-v1 development CSV hashes.',
 'source_development_csv_sha256':SOURCES,
 'data_boundary':'Only 140-row development CSVs read; no sealed paths or test results read.',
 'font':{'path':FONT,'collection_face':FACE,'family':family,'missing_glyphs':missing,'unique_nonspace_characters':len([c for c in allchars if not c.isspace()])},
 'rendering':'Pillow L at 2x, downsample LANCZOS, convert RGB; all plot coordinates use raw daily data.',
 'plotted_protocol':{'targets':[113,140],'rolling_origins':[112,139],'horizon':1,'candidates':[3,7,14],'fixed_origin_h5_not_plotted':True},
 'practice_daily_predictions_comparison':practicecheck,
 'pixel_checks':pixelchecks,'figures':DRAWINGS,
 'mobile_visual_review':'PENDING: inspect all 320 px and 390 px previews; this is not an adversarial review.'}
review_path=TOOLS/'mobile-review.json'
if review_path.exists():
    review=json.loads(review_path.read_text())
    if all(hashlib.sha256((ROOT/item['file']).read_bytes()).hexdigest()==item['sha256'] for item in review['images']):
        report['mobile_visual_review']=review
(TOOLS/'render-quality-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
(TOOLS/'plotted-curves.json').write_text(json.dumps(CURVES,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'figures':[x['file'] for x in DRAWINGS],'source_hashes':SOURCES,'glyphs_missing':missing,'font_face':family,'practice_match':practicecheck,'report':str(TOOLS/'render-quality-report.json')},ensure_ascii=False,indent=2))
