from pathlib import Path
import re,json,subprocess,html,csv,math
root=Path(__file__).parent; dist=root/'dist'; dist.mkdir(exist_ok=True)
def render(s):
 return subprocess.run(['pandoc','-f','markdown-smart','-t','html','--mathml'],input=s,text=True,capture_output=True,check=True).stdout
f=(root/'content/forecast-foundations.md').read_text(); a=(root/'content/forecast-advanced.md').read_text()
fc=re.split(r'(?=^## 第\d+章)',f,flags=re.M)[1:]
ac=re.split(r'(?=^# \d+ )',a,flags=re.M)[1:]
modules=[]
def add(title,kicker,body): modules.append(dict(title=title,kicker=kicker,html=render(body)))
add('数学桥梁','预备 · 手算入门',(root/'content/forecast-math-bridge.md').read_text())
add('定义问题与数据地基','阶段 01 · 3课', '\n'.join(fc[:2]))
add('昨日、同日与移动平均','阶段 02 · 3课',fc[2]+'\n## 项目前补课：简单指数平滑\n'+fc[6].split('### 7.2 ')[1].split('### 7.3 ')[0])
add('误差、偏差与公平回测','阶段 03 · 3课',fc[3])
add('从一条直线到类别特征','阶段 04 · 3课','\n'.join(fc[4:6]))
add('平滑、趋势与ARIMA','阶段 05 · 3课','\n'.join(fc[6:9]))
add('树模型、全局与长尾','阶段 06 · 3课','\n'.join(ac[:6]))
add('概率预测与库存决策','阶段 07 · 3课',ac[6])
add('六行业迁移工作坊','阶段 08 · 3课',(root/'content/forecast_industry_lessons.md').read_text()+'\n\n## 追加：六个快速手算实验与答案\n'+(root/'content/forecast-industries.md').read_text())
p=(root/'content/forecast-specialized-course.md')
if p.exists():
 s=p.read_text(); parts=re.split(r'(?=^# 阶段\d+)',s,flags=re.M)[1:]
 for part in parts:
  if part.strip():
   title=part.splitlines()[0].lstrip('# ');add(title,'专项 · 3课与项目',part)
add('毕业项目与上线边界','阶段 16 · 3课','\n'.join(ac[7:]))
projects=(root/'content/projects.md')
if projects.exists():
 handbook=projects.read_text().split('## 六、文章转换门槛')[0]
 blocks=re.findall(r'(### 阶段(\d+)：.*?)(?=\n### 阶段|\n## 四、)',handbook,re.S)
 for block,n in blocks:
  idx=int(n)
  if idx<=8: target=idx
  elif idx==16: target=len(modules)-1
  else:
   target=next((i for i,m in enumerate(modules) if f'阶段{idx}' in m['title'] or f'阶段 {idx}' in m['title']),-1)
  if 0<=target<len(modules): modules[target]['html']+=render('\n## 本阶段项目与验收\n'+block)
 add('项目作业与验收手册','工具箱 · 全阶段',handbook)
add('来源、范围与纠错说明','资料 · 阅读入口', '''# 来源与教学范围

本教程根据用户上传《供应链预测与计划全景白皮书》重新组织，并结合先前《供应链需求预测实战教程》补充基础。它是可顺序学习的课程，不是博客文章专题；不修改12lab.cn。原白皮书的未附证据收益数字、行业实际比例与所谓实证评分不作事实沿用。

## 阅读入口

- [Forecasting: Principles and Practice 第3版](https://otexts.com/fpp3/)：第5章基础与准确性、第7章回归、第8章指数平滑、第9章ARIMA、第10章动态回归、第11章层级预测、第13章实践边界。
- [FPP3 交叉验证](https://otexts.com/fpp3/tscv.html)：阅读滚动预测起点部分。
- [scikit-learn 概率校准](https://scikit-learn.org/stable/modules/calibration.html)：阅读校准曲线与Brier评分的含义。
- [scikit-learn 梯度提升](https://scikit-learn.org/stable/modules/ensemble.html#gradient-boosting)：理解分段树及逐步修正，不必先推导优化算法。
- [lifelines 生存分析入门](https://lifelines.readthedocs.io/en/latest/Survival%20Analysis%20intro.html)：理解生存函数与删失；不把软件输出当作识别假设已通过。
- [MIT OCW Logistics Systems](https://ocw.mit.edu/courses/1-260j-logistics-systems-fall-2006/pages/lecture-notes/)：选择库存与需求相关讲义，先做本教程简化例题。
- [OR-Tools 优化介绍](https://developers.google.com/optimization/introduction)：阅读目标、变量、约束的区别。

链接为官方或作者资料入口，未编造页码。英文资料可先辅助翻译，再用本教程数字逐步核对。本轮未逐个网页联网验证可用性。

## 从原稿修正的关键边界

1. 取消概率和留存订单数使用不同符号。现存未取消订单使用条件留存比，不重复乘从下单起的全程留存。
2. 物流发货是竞争事件，也可能与取消风险有关，不能自动据此识别完全不发货的反事实。
3. 离散logit风险回归不是Cox比例风险模型；Croston与TSB的第二个平滑对象不同。
4. 退货回流必须考虑预测日起点之前的历史发货批次；COD库存按实物流记录，不重复净额扣减。
5. 动态定价的销售不能超过库存。需求响应只是预测关联，不自动是价格因果效应。
6. 未核实的收益百分比不作为结论。效期规则需具体法规确认，不由模型擅自延长。

## 数据与验证协议

所有练习数据为模拟。禾味是2店8食材的虚构案例；匿名服装企业不出现真实品牌。14天仅用于手算，预测扩展为180天，按112/28/40切分；5天评价窗口不得跨块。以往已经公开的测试段只作历史演示，不能称为新的盲测；新模型最终比较应另造并封存测试数据。此站的教学计划、验收答案不表示学习者已完成实验。

原型仅离线建议，不自动采购、派车、改价、联系客户或发布文章。进度只存在当前浏览器，勾选代表自报完成，不是服务端认证。
''')
for idx in [1,3]:
 modules[idx]['html']='<p class="check">本阶段可直接下载：<a href="data-quality-backtest.zip" download>P01/P03输入、生成器、操作说明与参考答案</a>。先做题再看answers目录。</p>'+modules[idx]['html']
for idx in range(9,min(16,len(modules))):
 if idx<=13:
  key={9:'cod',10:'presale',11:'returns',12:'cod',13:'po'}[idx]
  notice=f'<p class="check">先用小表理解，再做已提供的完整工程：<a href="#unit-{key}-full">进入本专项实际项目、输出与模型能力说明</a>。已实现模型以新工程模型卡为准，不把下述早期项目中的进阶模型要求视作已经实现。<a href="specialized-handcalc.zip" download>手算输入</a>。</p>'
 else:
  notice='<p class="check"><a href="specialized-handcalc.zip" download>下载手算输入与检验脚本</a>。本章尚未提供原计划的大样本关联训练/随机多期定价工程，不能以手算完成代表这些范围已落实。</p>'
 modules[idx]['html']=notice+modules[idx]['html']
modules[8]['html']='<p class="check">本阶段必修：<a href="forecast-industry-project-data.zip" download>六行业手算题完整输入与说明</a>，按本页末P08六项与追加手算课验收即可。<a href="industry-lab-starter.zip" download>180天模拟起步包</a>及正文大规模建模均为选修扩展，不是核心通过门槛，起步夹具不表示已完成预测实验。</p>'+modules[8]['html']
from upgrade import integrate
modules=integrate(root,modules,render)
(dist/'course.json').write_text(json.dumps(modules,ensure_ascii=False))
# reproducible deterministic teaching dataset; not original experiments
with (dist/'hewei-180d.csv').open('w') as out:
 w=csv.writer(out);w.writerow(['day','store_id','sku_id','demand_kg','split','simulated'])
 for d in range(1,181):
  for st in range(1,3):
   for sk in range(1,9):
    val=round(8+sk*1.3+st+(3 if (d-1)%7>=5 else 0)+.015*d+((d*17+sk*11+st*3)%9-4)*.3,2)
    w.writerow([d,f'S{st}',f'I{sk}',val,'train' if d<=112 else 'validation' if d<=140 else 'historical_test',True])
print('modules',len(modules),'chars',sum(len(m['html']) for m in modules))
