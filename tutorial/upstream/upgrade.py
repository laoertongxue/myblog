"""Append audited teaching material. Evidence links do not assert complete requirement coverage."""
from pathlib import Path
import re,json,html,zipfile,hashlib

def integrate(root,modules,render):
 for i,m in enumerate(modules):m.update(id=f'legacy-{i}',group='基础教程' if i<17 else '资料与项目')
 path=root/'content/upgrade';src=(path/'forecast-missing-planning-math.md').read_text()
 chapters=re.split(r'(?=^## 第[一二三四五六七八]章)',src,flags=re.M)[1:]
 mathids=['abc-xyz','sop-fva','milp','deviance-residual','presale-60days','cross-price','multiechelon','markdown-dp']
 requirementmap={
 'abc-xyz':['G04'],'sop-fva':['A09','B03','G09','G10','K04'],'milp':['A08','G05'],
 'deviance-residual':['P10','P11','P12','K03'],'presale-60days':['P04','P05','P08','P09','P13','P14'],
 'cross-price':['E01','E02'],'multiechelon':['A07','C12'],'markdown-dp':['M02','M03','M04']}
 links={}
 for key,body in zip(mathids,chapters):
  title=body.splitlines()[0].removeprefix('## ')
  intro='本课使用模拟数据与明确假设。数学推导、枚举和数据核验不等于真实业务模型有效。配套包包含60天教学曲线及约束枚举，不是完整订单训练集。'
  content=f'<p class="check">{intro}<br><a href="planning-math-labs.zip" download>下载数学实验、完整教材与只读验证器</a></p>'+render(body)
  modules.append(dict(id=key,group='白皮书进阶',title=title,kicker='白皮书进阶 · 数学与计划',html=content,requirement_ids=requirementmap[key]))
  for rid in requirementmap[key]:links.setdefault(rid,[]).append((key,title,'数学/小实验；完整工程范围仍须逐项核对'))
 specs=[('cases-fresh-apparel.md',r'^## (生鲜F[1-5]|鞋服A[1-5])：',{'生鲜F':'fresh','鞋服A':'apparel'},'fresh-apparel-fixtures.zip'),('cases-fmcg-restaurant.md',r'^## ([FR][1-5]) ',{'F':'fmcg','R':'restaurant'},'fmcg-restaurant-fixtures.zip'),('cases-manufacturing-pharma.md',r'^## (制造案例 M[1-5]|医药案例 P[1-5])：',{'制造案例 M':'manufacturing','医药案例 P':'pharma'},'manufacturing-pharma-labs.zip')]
 mapping={'fresh-01':['C01'],'fresh-02':['C03'],'fresh-03':['C04'],'fresh-04':['C06'],'fresh-05':['C04'], 'apparel-01':['C07'],'apparel-02':['B02','C08'],'apparel-03':['C10'],'apparel-04':['C09'],'apparel-05':['P01','P04','P15'], 'fmcg-01':['C11'],'fmcg-02':['C11'],'fmcg-03':['C12'],'fmcg-04':['C12'],'fmcg-05':['E01','E02','E03'], 'restaurant-01':['C13'],'restaurant-02':['A03','G08'],'restaurant-03':['C14'],'restaurant-04':['C14'],'restaurant-05':['A08','C03'], 'manufacturing-01':['C15'],'manufacturing-02':['C16'],'manufacturing-03':['C17'],'manufacturing-04':['L03'],'manufacturing-05':['B05'], 'pharma-01':['B06','C18'],'pharma-02':['C19'],'pharma-03':['C19'],'pharma-04':['C20','G10','K04'],'pharma-05':['C18','R04']}
 names={'fresh':'生鲜食品','apparel':'鞋服快反','fmcg':'快消电商','restaurant':'餐饮茶饮','manufacturing':'制造与备件','pharma':'医药流通'}
 counts={k:0 for k in names}
 for filename,pattern,prefixes,bundle in specs:
  text=(path/filename).read_text();matches=list(re.finditer(pattern,text,re.M));assert len(matches)==10,(filename,len(matches))
  intro=text[:matches[0].start()]
  for i,match in enumerate(matches):
   token=match[1]; prefix=next(v for k,v in prefixes.items() if token.startswith(k));number=int(token[-1]);key=f'{prefix}-{number:02}'
   end=matches[i+1].start() if i+1<len(matches) else len(text)
   body=text[match.start():end]
   # omit a subsequent group banner but retain all substantive lesson paragraphs
   body=re.sub(r'^# (第一组|第二组).*$', '',body,flags=re.M)
   title=body.splitlines()[0].removeprefix('## ');counts[prefix]+=1
   pre=f'<p class="check">{names[prefix]} · 第{number}个独立案例。数据、参数及结果均为教学模拟；本例小样本演算不是大规模模型训练或真实业务效果。<br><a href="{bundle}" download>下载本行业案例输入、说明与可运行计算器</a></p>'
   common='<details><summary>共同阅读与提交约定</summary>'+render(intro)+'</details>'
   modules.append(dict(id=key,group='行业案例',industry=names[prefix],title=title,kicker=f'{names[prefix]} · 案例 {number}/5',html=pre+common+render(body),requirement_ids=mapping[key]))
   for rid in mapping[key]:links.setdefault(rid,[]).append((key,title,'独立案例的小样本讲解与计算；不自动代表原条目全部范围完成'))
 assert all(n==5 for n in counts.values()),counts
 # Four executable specialty projects: preserve actual model cards and evaluation limits.
 special=path/'specialty'
 if (special/'README.md').exists():
  pack='forecast-specialty-projects.zip'
  banner='<p class="check">完全模拟的可复现实验，不连接生产。<a href="'+pack+'" download>下载四专项完整工程包（20,000/12,000/10,000/2,000实体）</a>。运行前阅读覆盖data/outputs的说明。固定模拟世界的指标不是企业收益。</p>'
  for key,title,file in [('specialty-start','四专项工程：运行与实际能力','README.md'),('specialty-time','四专项：时间切分与标签成熟','TIME_AND_LEAKAGE.md'),('specialty-data','四专项：字段、事件与单位字典','DATA_DICTIONARY.md')]:
   modules.append(dict(id=key,group='专项工程',title=title,kicker='完整工程 · 方法与输入',html=banner+render((special/file).read_text())))
  cards=re.split(r'(?=^## [A-D]\. )',(special/'MODEL_CARDS.md').read_text(),flags=re.M)[1:]
  exercises=re.split(r'(?=^## 练习[1-4])',(special/'EXERCISES.md').read_text(),flags=re.M)[1:]
  results=re.split(r'(?=^## [1-4]\. )',(special/'RESULTS.md').read_text(),flags=re.M)[1:]
  lab_specs=[('presale','预售取消：风险集到条件待发情景',['P02','P03','P05','P06','P07','P08','P09','P11','P13','P15','G06'],['survival.svg'],'分组平滑hazard已实现；logit hazard/Cox/IPCW未实现，信息性删失不自动识别反事实'),('returns','退货：概率、时滞与可售回流',['R01','R02','R03','R04'],['daily_restock.svg'],'品类概率收缩和条件历史路径已实现；GBDT、删失退货生存与完整采购优化未实现'),('cod','COD：真实拟合、校准与两本账',['D01','D02','D03','D04','G08'],['calibration.svg','threshold_cost.svg'],'逻辑回归/截距校准/阈值已实现；容量、确认工作流和真实干预效果未实现'),('po','PO：部分收货、KM和P90边界',['L02','L03'],['km_survival.svg','po_coverage.svg'],'KM/经验分位与删失覆盖已实现；分位数回归、需求交期相关库存仿真未实现')]
  for n,(key,title,rids,graphs,limit) in enumerate(lab_specs):
   figs=''.join(f'<figure><img loading="lazy" src="specialty-outputs/{key}/{g}" alt="{html.escape(title)}：{g}，固定种子模拟输出"><figcaption>固定种子20261106的实际程序输出，仅反映教学模拟。{g}</figcaption></figure>' for g in graphs)
   body=banner+'<p><a href="#unit-specialty-start">运行方法</a> · <a href="#unit-specialty-time">时间协议</a> · <a href="#unit-specialty-data">字段字典</a></p>'+render(exercises[n])+'<h2>模型实现及未实现范围</h2>'+render(cards[n])+'<h2>实际运行结果与解释</h2>'+render(results[n])+figs
   modules.append(dict(id=key+'-full',group='专项工程',title=title,kicker='完整工程 · '+limit,html=body,requirement_ids=rids))
   for rid in rids:links.setdefault(rid,[]).append((key+'-full',title,limit))

 # Independently reviewed model supplement, preserving all derivations and execution limits.
 modelpath=path/'forecast-model-remaining.md'
 if modelpath.exists():
  text=modelpath.read_text(); parts=re.split(r'(?=^## model-[a-z-]+：)',text,flags=re.M)
  common=render(parts[0]); manifest=json.loads((path/'forecast-model-remaining-manifest.json').read_text())
  specs={x['id']:x for x in manifest['units']}
  for body in parts[1:]:
   key=re.match(r'## (model-[a-z-]+)：',body)[1]; spec=specs[key]
   title=body.splitlines()[0].split('：',1)[1]
   banner='<p class="check">模拟教学与独立审查范围内的实际代码。<a href="forecast-model-labs.zip" download>下载模型实验 r3</a>。Prophet、TFT、DeepAR和视觉编码器未运行；不得把分解算术或张量校验称为深度训练。</p>'
   modules.append(dict(id=key,group='白皮书进阶',title=title,kicker='模型补课 · 实现层级可核对',html=banner+'<details><summary>共同运行方法与能力边界</summary>'+common+'</details>'+render(body),requirement_ids=spec['source_ids']))
   for rid in spec['source_ids']:links.setdefault(rid,[]).append((key,title,spec['evidence_scope']))
 planpath=path/'forecast-planning-remaining.md'
 if planpath.exists():
  text=planpath.read_text(); parts=re.split(r'(?=^# PR0[1-6]｜)',text,flags=re.M)
  common=render(parts[0]); specs={x['unit_id']:x for x in json.loads((path/'planning-remaining-map.json').read_text())['items']}
  for body in parts[1:]:
   code=re.match(r'# (PR0[1-6])｜',body)[1];spec=specs[code];key='planning-'+code.lower()
   title=body.splitlines()[0].split('｜',1)[1]
   banner='<p class="check">已独立审查的模拟计划实验。<a href="planning-remaining-labs.zip" download>下载计划侧6个实验</a>。固定优先级或有限枚举的结果不是通用MILP/APS全局最优，不代表真实收益。包内pending为冻结时记录，第二版独立审查已通过其注明范围。</p>'
   modules.append(dict(id=key,group='白皮书进阶',title=title,kicker='计划补课 · '+spec['scope_limit'],html=banner+'<details><summary>共同运行方法与教学边界</summary>'+common+'</details>'+render(body),requirement_ids=spec['whitepaper_ids']))
   for rid in spec['whitepaper_ids']:links.setdefault(rid,[]).append((key,title,spec['scope_limit']))
 industrypath=path/'forecast-industry-expanded.md'
 if industrypath.exists():
  parts=re.split(r'(?=^## [1-6] )',industrypath.read_text(),flags=re.M);common=render(parts[0]);appendix=render(parts[6])
  specs=[('fresh-hourly-unobserved',['C01','C02']),('temperature-shelf-life',['C04']),('apparel-bayesian-lifecycle',['B02','C08']),('vmi-asof-conservation',['B05']),('collab-first-second-allocation',['C14'])]
  for body,(key,rids) in zip(parts[1:6],specs):
   title=body.splitlines()[0].removeprefix('## ')
   banner='<p class="check">R3模拟教学实验，16份CSV/149行。<a href="forecast-industry-expanded.zip" download>下载行业机制扩展 R3</a>。温度风险不授权延长标签效期；缺货需求不可直接观测；VMI实物账与当时可见信息分开。程序结果不是自动补货、食品放行或实际收益证据。</p>'
   modules.append(dict(id=key,group='白皮书进阶',title=title,kicker='行业机制扩展 · 数据与边界',html=banner+'<details><summary>共同运行与验收方法</summary>'+common+appendix+'</details>'+render(body),requirement_ids=rids))
   for rid in rids:links.setdefault(rid,[]).append((key,title,'完整模拟小实验；只覆盖本课注明的业务机制，不替代生产系统或不可识别的反事实'))
 # Next audited teaching increments; their independent package acceptance is not full scope certification.
 corepath=path/'forecast-core-gap-lessons.json'
 if corepath.exists():
  book=json.loads(corepath.read_text());intro=(path/'forecast-core-gap-lessons.md').read_text().split('## core-01')[0]
  for spec in book['lessons']:
   key=spec['id'];title=spec['title'];rids=spec['requirement_ids']
   banner='<p class="check">新增离线教学实验，非生产流程。<a href="forecast-core-gap-labs.zip" download>下载核心12章实验包</a>。core-13已新增有限预售/PO/STO/WO联合实验；通用跨期联合优化未实现，审批、回写和执行仅在本地模拟。</p>'
   modules.append(dict(id=key,group='白皮书进阶',title=title,kicker='架构与治理补课 · '+spec['remaining_limit'],html=banner+'<details><summary>共同运行方法与边界</summary>'+render(intro)+'</details>'+render(spec['markdown']),requirement_ids=rids))
   for rid in rids:links.setdefault(rid,[]).append((key,title,'独立验收的离线教学子范围；'+spec['remaining_limit']))
 gapindustry=path/'forecast-industry-gap-lessons.md'
 if gapindustry.exists():
  parts=re.split(r'(?=^## 行业补课[一二三四五六七八九])',gapindustry.read_text(),flags=re.M);specs=json.loads((path/'forecast-industry-gap-manifest.json').read_text())['lessons'];assert len(parts)==10
  for body,spec in zip(parts[1:],specs):
   key=spec['slug'];title=spec['title'];rids=spec['source_ids']
   banner='<p class="check">R2独立验收的行业教学扩展。<a href="forecast-industry-gap-labs.zip" download>下载行业9课实验包</a>。所有数据均模拟；'+html.escape(spec['limits'])+'。</p>'
   modules.append(dict(id=key,group='白皮书进阶',title=title,kicker='行业链条补课 · 模拟输入与验收',html=banner+'<details><summary>共同阅读约定</summary>'+render(parts[0])+'</details>'+render(body),requirement_ids=rids))
   for rid in rids:links.setdefault(rid,[]).append((key,title,spec['evidence']+'；限制：'+spec['limits']))
 gapsp=path/'forecast-specialty-gap-lessons.md'
 if gapsp.exists():
  parts=re.split(r'(?=^## 模块 SG0[1-5])',gapsp.read_text(),flags=re.M);specs=json.loads((path/'specialty-gap-map.json').read_text())['modules'];assert len(parts)==6
  for body,spec in zip(parts[1:],specs):
   key=spec['id'];title=spec['title'];rids=spec['items']
   banner='<p class="check">R3离线模拟专项补课。<a href="forecast-specialty-gap-labs.zip" download>下载五模块专项实验包</a>。PO测试P50校准警戒未通过；最终分位仅21/131张有支持，下一批7日99/131张有支持，其余留空。此处真实拟合仅限模拟数据，不是生产认证或实时业务服务。</p>'
   modules.append(dict(id=key,group='专项工程',title=title,kicker='专项补课 · '+spec['limits'],html=banner+'<details><summary>共同运行方法与时间规则</summary>'+render(parts[0])+'</details>'+render(body),requirement_ids=rids))
   for rid in rids:links.setdefault(rid,[]).append((key,title,spec['implemented']+'；限制：'+spec['limits']))
 jointpath=path/'forecast-joint-presale-lessons.json'
 if jointpath.exists():
  for spec in json.loads(jointpath.read_text())['lessons']:
   banner='<p class="check">有限联合教学模型：单SKU、三天、三个预售净留存情景，联合PO/STO/WO整数决策。<a href="forecast-joint-presale-lab.zip" download>下载联合预售实验</a>。不连接生产，未实现通用多SKU、多工序、随机交期、多阶段APS/MRP/MEIO。</p>'
   modules.append(dict(id=spec['id'],group='白皮书进阶',title=spec['title'],kicker='有限联合决策 · 逐候选独立核验',html=banner+render(spec['markdown']),requirement_ids=spec['requirement_ids']))
   links.setdefault('A07',[]).append((spec['id'],spec['title'],'3520候选联合枚举与独立逐候选核验；最优252瓶/651，对照270瓶/687；仅明示的有限模型'))
  old=next(m for m in modules if m['id']=='core-06')
  old['html']='<p class="check">更新：本课保留分开求解的基础对照。<a href="#unit-core-13">core-13 已新增预售与PO/STO/WO联合的有限教学模型</a>，并非通用生产优化系统。</p>'+old['html']
 trace=json.loads((path/'forecast-upgrade-traceability.json').read_text())
 rows=[]
 for item in trace['items']:
  refs=links.get(item['id'],[])
  item['lesson_ids']=[x[0] for x in refs]
  item['case_ids']=[x[0] for x in refs if re.match(r'^(fresh|apparel|fmcg|restaurant|manufacturing|pharma)-',x[0])]
  ev=item.setdefault('evidence',{})
  ev['explanation']=[x[0]+': '+x[1] for x in refs]
  ev['independent_review']=[item['independent_review']] if item.get('independent_review') else []
  # A lesson link is not a formula or test assertion. Those require an explicit evidence ID.
  for field in ['formula_ids','test_ids']:
   if not item.get(field):item[field]=[]
  item['unmapped_evidence_note']='逐公式及逐测试编号尚未建立时保持为空，不据课程链接推断验证。'
  bundle_map={
   'specialty-gap-':('forecast-specialty-gap-labs.zip','按README运行run_all.py及tests和audit_replay.py','模拟数据实际logistic/GBDT/分位回归；未接生产','R3独立53契约、7反例；保留P50失败及支持拒绝'),
   'core-13':('forecast-joint-presale-lab.zip','按README运行联合枚举及测试','固定模拟情景整数枚举，非模型训练或生产系统','3520候选独立逐项核验；有限共同决策'),
   'core-':('forecast-core-gap-labs.zip','python core_lab.py --self-test','离线规则与契约模拟，非生产流程','69测试及独立输入扰动/双目录复现；原12章A07范围由core-13独立有限联合实验补充'),
   'industry-':('forecast-industry-gap-labs.zip','按包内README执行运行器及测试','部分OLS真实拟合与模拟决策，非真实业务有效性','R2独立封包测试与输出复现；约束见每章'),
   'model-':('forecast-model-labs.zip','python run_models.py; python tests/test_labs.py; python verify_reproducibility.py','三商品OLS/GBDT/岭回归/KMeans实际拟合；Prophet/TFT/DeepAR未运行','43项测试及12文件重现；具体单位能力以模型卡为准'),
   'planning-':('planning-remaining-labs.zip','python run.py; python test_labs.py','无预测模型训练；固定规则和有限枚举','71作者检查及独立守恒/边界检查；不是生产级优化证明'),
   'fresh-':('fresh-apparel-fixtures.zip','python check_answers.py --self-test','手算与固定参数规则；未训练大样本模型','只读CSV、数值及输入扰动检查'),
   'apparel-':('fresh-apparel-fixtures.zip','python check_answers.py --self-test','手算与固定参数规则；未训练大样本模型','只读CSV、数值及输入扰动检查'),
   'fmcg-':('fmcg-restaurant-fixtures.zip','python run_cases.py --self-test','手算与给定参数规则；未训练大样本模型','实际CSV计算、输入变异与时点拒绝'),
   'restaurant-':('fmcg-restaurant-fixtures.zip','python run_cases.py --self-test','手算与给定参数规则；未训练大样本模型','实际CSV计算、输入变异与时点拒绝'),
   'manufacturing-':('manufacturing-pharma-labs.zip','python verify_cases.py --self-test','固定参数与库存规则；未训练大样本模型','实际CSV计算、10扰动和13非法输入'),
   'pharma-':('manufacturing-pharma-labs.zip','python verify_cases.py --self-test','固定参数与库存规则；未训练大样本模型','实际CSV计算、10扰动和13非法输入')}
  for special_id in ['fresh-hourly-unobserved','temperature-shelf-life','apparel-bayesian-lifecycle','vmi-asof-conservation','collab-first-second-allocation']:
   bundle_map[special_id]=('forecast-industry-expanded.zip','python run_labs.py; python -m unittest -v test_labs','模拟规则与估计/概率更新；无真实业务训练证据','R3独立审查55测试、变异及时间边界检查；具体机制以正文为准')
  bundles=[]
  for key,title,limit in refs:
   for prefix,details in bundle_map.items():
    if key.startswith(prefix) and not (key=='core-13' and prefix=='core-') and (prefix not in ['fresh-','apparel-','fmcg-','restaurant-','manufacturing-','pharma-'] or re.match(r'^'+re.escape(prefix)+r'\d{2}$',key)):bundles.append(details)
  if bundles:
   bundles=list(dict.fromkeys(bundles));item['dataset_ids']=list(dict.fromkeys(v[0] for v in bundles));item['artifact_paths']=item['dataset_ids']
   for field,n in [('input_dataset',0),('executable_command',1),('training_record',2),('actual_outputs',3)]:ev[field]=list(dict.fromkeys(v[n] for v in bundles))

  # Do not infer complete coverage from a link or a passed case-level review.
  reviewed=item.get('independent_review') or {}
  status='限定教学机制审查：'+reviewed.get('status','未审')+'。'+reviewed.get('evidence','未有独立证据')

  newrefs=[v for v in refs if v[0].startswith(('core-','industry-','specialty-gap-'))]
  if newrefs:status+=' 已按108模块逐项审查及A07联合实验核验认定；不表示生产能力已实现。'
  item['candidate_status']=status
  cells=''.join(f'<td>{html.escape(v)}</td>' for v in [item['id'],item['source_scope'],item['baseline_status']])
  refhtml='<br>'.join(f'<a href="#unit-{key}">{html.escape(title)}</a><small>{html.escape(limit)}</small>' for key,title,limit in refs) or '尚未新增'
  evidence=item.get('evidence',{})
  details='<details><summary>查看讲授、数据、运行与能力证据</summary>'+''.join('<p><b>'+html.escape(label)+'</b>：'+html.escape(str(evidence.get(key) or '尚无新增证据'))+'</p>' for key,label in [('input_dataset','输入包'),('executable_command','执行命令'),('actual_outputs','实际输出与测试'),('training_record','模型训练层级'),('evaluation_protocol','评估范围')])+'</details>'
  rows.append('<tr>'+cells+'<td>'+refhtml+details+'</td><td>'+html.escape(status)+'<p>'+html.escape(item.get('unimplemented_or_unverified',item['required_upgrade']))+'</p></td></tr>')
 partials=[a for a in trace['items'] if (a.get('independent_review') or {}).get('status')=='部分']
 partial_html='<h2>91项限定教学机制与重要边界</h2><p>依据108模块逐项独立审查，并补充A07联合实验独立核验，91项限定教学机制已有解释、输入、计算、边界和验收。该结论不表示白皮书涉及的所有算法、生产系统或真实业务效果均已验证。</p><p class="check">A07只覆盖单SKU、三天、三个预售净留存情景的有限联合PO/STO/WO模型，未实现通用多SKU、多工序、随机交期或多阶段APS/MRP/MEIO。COD现金与双源分单等仍是独立教具，不是四专项生产主工程的自动串联。PO测试P50校准警戒失败；最终分位仅21/131张、下一批7日仅99/131张有支持，其余留空。Prophet、TFT、DeepAR及视觉编码器未训练或运行；输入/机制教学不能称模型训练。食品风险模型不授权延长效期或自动放行。所有数据与结果均模拟，不证明真实收益。</p>'
 coverage=partial_html+'<h1>白皮书逐项对照：内容与实现范围</h1><p>91项来自白皮书机制与公式的逐项拆分。旧版审查为17项完整、60项部分、14项缺失；它们不等权，不能换算为科学的完成百分比。下表新增链接表示能找到相关学习证据，不意味着该条目的全部范围已经完成。</p><p class="check">108模块逐项审查加A07独立核验，共91项限定教学机制闭合。完整仅指该行限定教学机制已有解释、输入、计算、边界与验收，不等于所有方法或生产流程完成。这不是生产系统100%完成或真实业务认证。30个案例通过的是教学内容与小样本程序闭环，不是30个生产模型。未闭合内容继续明确列出，不以“选修”或标题代替完成。</p><div class="table-wrap"><table><thead><tr><th>ID</th><th>白皮书范围</th><th>旧版状态</th><th>新增学习证据</th><th>当前范围与待核对内容</th></tr></thead><tbody>'+''.join(rows)+'</tbody></table></div>'
 modules.append(dict(id='whitepaper-trace',group='资料与项目',title='白皮书91项对照与未完成范围',kicker='可追溯 · 范围声明',html=coverage))
 (root/'dist/traceability.json').write_text(json.dumps(trace,ensure_ascii=False,indent=2))
 resources=[]
 for file in sorted((root/'dist').glob('*.zip')):
  with zipfile.ZipFile(file) as z:
   assert z.testzip() is None
   csvs=[]
   for name in z.namelist():
    if name.endswith('.csv'):
     csvs.append(f'{name}: {max(0,len(z.read(name).decode("utf-8-sig").splitlines())-1)}行')
  digest=hashlib.sha256(file.read_bytes()).hexdigest()
  resources.append(f'<h2><a href="{file.name}" download>{file.name}</a></h2><p>{file.stat().st_size:,} bytes · SHA256 {digest}</p><details><summary>查看CSV实际行数</summary><ul>'+''.join('<li>'+html.escape(c)+'</li>' for c in csvs)+'</ul></details>')
 modules.append(dict(id='resource-center',group='资料与项目',title='数据与可执行项目资源中心',kicker='下载 · 版本与边界',html='<h1>数据与可执行项目</h1><p>所有文件均为模拟教学材料。各包有独立README、参数和用途，不把不同包的样本视作同一训练集。模型训练与完整专项工程以包内实际说明为准；不要把手算包称为订单级模型已训练。</p>'+''.join(resources)))
 return modules
