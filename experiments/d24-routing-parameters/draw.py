from PIL import Image,ImageDraw,ImageFont
from pathlib import Path
ROOT=Path(__file__).resolve().parent
F='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc';B='/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'
def font(s,b=False):return ImageFont.truetype(B if b else F,s)
def canvas(w,h,title,sub):
 im=Image.new('RGB',(w,h),'#fafafa');d=ImageDraw.Draw(im);d.rectangle((0,0,12,h),fill='black');d.text((42,27),title,font=font(30,True),fill='black');d.text((44,78),sub,font=font(17),fill='#555');return im,d
def box(d,x,y,w,h,title,lines):
 d.rectangle((x,y,x+w,y+h),outline='#222',width=2);d.text((x+20,y+14),title,font=font(23,True),fill='black')
 for i,line in enumerate(lines):d.text((x+20,y+60+i*35),line,font=font(19),fill='#333')
def save(im,n):im.save(ROOT/'images'/n)
im,d=canvas(900,383,'多给十秒，路线就会更好吗？','D24 · 单因素实验 / 业务情景 ≠ 求解设置')
box(d,44,132,382,167,'改容量、改窗口',['改变允许采用的方案集合','先检查可行性，再比较情景'])
box(d,451,132,405,167,'只改搜索时限',['保持输入与目标完全一致','1 秒 → 5 秒 → 10 秒'])
d.text((44,330),'模拟实验 · 记录失败，也保留没有改善的结果',font=font(19),fill='#333');save(im,'d24-00_cover.png')
im,d=canvas(1000,650,'实验协议：每次只改一个因素','固定输入、目标与其他设置，才知道结果在回答什么')
box(d,45,140,435,360,'业务情景实验',['容量：12 → 9 / 14 箱','实际变化：−25% / +16.67%','窗口：点 2 [510,550]','              → [510,510]','每个情景重新验算路线'])
box(d,510,140,445,360,'求解设置实验',['同一份节点、需求、车辆','同一份距离与目标','同一首解、局部搜索策略','只改变：1 / 5 / 10 秒','不把情景变化写成算法降本'])
d.text((46,551),'本篇统一使用 PATH_CHEAPEST_ARC + GUIDED_LOCAL_SEARCH',font=font(19),fill='#333');d.text((46,587),'D22 旧记录使用 GREEDY_DESCENT，本篇重新运行基准。',font=font(19),fill='#333');save(im,'d24-01_design.png')
im,d=canvas(1000,650,'本次结果：更大容量、更多时间，未必更短','两案均为模拟；无解行记“不适用”，不记 0 公里')
headers=['实验','匿名服装','禾味扩展'];xs=[50,490,745]
for x,t in zip(xs,headers):d.text((x,140),t,font=font(23,True),fill='black')
rows=[('每车 9 箱','不可行：20 > 18','不可行：20 > 18'),('每车 12 / 14 箱','28 / 28 公里','20 / 20 公里'),('搜索 1 / 5 / 10 秒','28 / 28 / 28 公里','20 / 20 / 20 公里'),('四点窗口：原 → 收紧','14 → 18 公里','10 → 10 公里')]
for i,row in enumerate(rows):
 y=205+i*72;d.line((45,y-15,953,y-15),fill='#bbb',width=1)
 for x,t in zip(xs,row):d.text((x,y),t,font=font(20),fill='black')
d.text((47,534),'四点返回路线均验算通过；服装的 +4 公里不是最优性下界。',font=font(21),fill='#333');d.text((47,579),'每配置仅运行一次，不据此推广为算法性能结论或实际运营收益。',font=font(20),fill='#333');save(im,'d24-02_results.png')
im,d=canvas(1000,650,'路线进入评审前，要经过哪些门槛？','不把“返回了结果”当成“可以执行”')
items=[('01 冻结','输入散列、单位、目标、配置、版本'),('02 运行','保留原始状态、路线、求解墙钟时间'),('03 验算','覆盖、容量、距离、服务开始、回仓'),('04 表达','无解不填零；可行不冒充全局最优')]
for i,(title,line) in enumerate(items):
 y=130+i*105;d.rectangle((45,y,220,y+76),fill='black');d.text((65,y+20),title,font=font(23,True),fill='white');d.rectangle((220,y,953,y+76),outline='#222',width=2);d.text((245,y+22),line,font=font(23),fill='black')
d.text((46,587),'正式派车还需真实地图、交通、车辆限制、业务审核与操作授权。',font=font(19),fill='#444');save(im,'d24-03_gate.png')
