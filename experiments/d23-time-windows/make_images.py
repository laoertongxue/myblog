from PIL import Image,ImageDraw,ImageFont
from pathlib import Path
out=Path(__file__).parent/'article'
font='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
def new(name,title,sub,height=500):
 im=Image.new('RGB',(900,height),'#f4f1e9');d=ImageDraw.Draw(im);d.text((45,30),title,font=ImageFont.truetype(font,32),fill='#161616');d.text((45,85),sub,font=ImageFont.truetype(font,17),fill='#555555');return im,d
def text(d,xy,t,size=22):d.text(xy,t,font=ImageFont.truetype(font,size),fill='#171717')
im,d=new('cover','路线不长，为什么仍会迟到','D23 · 容量约束 + 时间窗 + 卸货时长',383)
for x,t,s in [(45,'到达','8:11'),(260,'等待','9 分钟'),(475,'服务','8:20'),(690,'离开','8:28')]:
 d.rectangle((x,155,x+165,275),outline='#222',width=2);text(d,(x+25,175),t);text(d,(x+25,220),s,26)
text(d,(45,320),'模拟案例  /  时间窗约束“开始服务”，不等于到达',19);im.save(out/'cover.png')
im,d=new('timeline','一站的时间，拆成四个时点','匿名服装点 1 · 8:00 出仓 · 8:20—9:00 开始服务窗口')
for x1,x2,label,detail in [(60,310,'行驶 11 分钟','8:00 → 8:11'),(310,550,'等待 9 分钟','8:11 → 8:20'),(550,830,'卸货 8 分钟','8:20 → 8:28')]:
 d.rectangle((x1,170,x2,300),outline='#222',width=2);text(d,(x1+15,195),label);text(d,(x1+15,245),detail,18)
text(d,(60,350),'到达 ≠ 开始服务；早到允许等待，卸货计入后续排程',23)
text(d,(60,400),'教学模拟：行驶、等待、服务分别记录，不替代真实路况',18);im.save(out/'timeline.png')
im,d=new('comparison','同样收紧窗口，不同路线反应','点 2：8:30—9:10 → 仅 8:30 开始服务；全部为模拟')
for y,title,old,newv,note in [(150,'匿名服装','14 公里','18 公里','旧顺序晚到 6 分钟；换顺序后仍可行'),(300,'禾味扩展','10 公里','10 公里','旧顺序恰好 8:30 开始服务；仍可行')]:
 text(d,(50,y),title,25);text(d,(250,y),old,29);text(d,(475,y),'→',29);text(d,(580,y),newv,29);text(d,(250,y+55),note,20)
text(d,(50,440),'业务约束已改变，差额不能解释为算法优化收益',20);im.save(out/'comparison.png')
