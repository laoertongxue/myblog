{
  "title": "四专项工程：运行与实际能力",
  "description": "四专项工程：运行与实际能力：所有订单、包裹、商品、供应商与事件都是程序生成的虚构数据。不是企业真实数据，不接入生产系统，不会发邮件、改价、取消订单或下采购单。",
  "type": "forecast",
  "unit": "specialty-start",
  "weight": 58,
  "outputs": [
    "HTML"
  ]
}

<p class="check">完全模拟的可复现实验，不连接生产。<a href="/forecast/forecast-specialty-projects.zip" download>下载四专项完整工程包（20,000/12,000/10,000/2,000实体）</a>。运行前阅读覆盖data/outputs的说明。固定模拟世界的指标不是企业收益。</p><h2
id="供应链预测四专项可复现模拟项目包">供应链预测四专项：可复现模拟项目包</h2>
<p><strong>所有订单、包裹、商品、供应商与事件都是程序生成的虚构数据。不是企业真实数据，不接入生产系统，不会发邮件、改价、取消订单或下采购单。</strong></p>
<p>本包把“预售取消、退货回流、COD拒收、PO收齐交期”做成四个可以从头运行的小项目。目标不是证明复杂模型一定更好，而是让你亲眼检查：答案什么时候才知道、哪些记录还没结束、预测与实物账为什么不能混在一起。</p>
<h2 id="先看什么">先看什么</h2>
<ol type="1">
<li>不想安装软件：先打开 <code>outputs/RESULTS.md</code>
看这次实际跑出的结果。CSV可用表格软件打开，SVG可用浏览器打开。</li>
<li>想自己运行：按下节只执行一条命令。不需要注册账号、联网下载数据或安装第三方Python包。</li>
<li>想改参数：先读
<code>docs/EXERCISES.md</code>，一次只改一个参数，记下改动后重新跑。不要挑最好看的测试结果当最终成绩。</li>
</ol>
<h2 id="运行只有-python-标准库">运行：只有 Python 标准库</h2>
<p>要求 Python 3.10 或更新；本交付在 Python 3.12.14
实际运行。没有numpy、pandas、scikit-learn等第三方依赖。</p>
<p>解压后打开终端，进入本文件所在文件夹：</p>
<div class="sourceCode" id="cb1"><pre
class="sourceCode bash"><code class="sourceCode bash"><span id="cb1-1"><a href="#cb1-1" aria-hidden="true" tabindex="-1"></a><span class="ex">python</span> run_all.py</span></code></pre></div>
<p>某些Mac/Linux用 <code>python3 run_all.py</code>，Windows若
<code>python</code> 不存在可试
<code>py run_all.py</code>。命令会生成数据、拟合基线、评估、画图、运行测试，覆盖本包的
<code>data/</code> 和 <code>outputs/</code>
中同名生成文件。它不会修改文件夹之外的内容。</p>
<p>正常结束应看到 <code>Ran 23 tests</code>、<code>OK</code> 和
<code>Complete</code>。测试详情在
<code>outputs/test_results.txt</code>。其中包含不同种子的完整重跑、报告结论方向变化、零退货、PO全部删失、PO收齐年龄与收货顺序投毒测试。如果有失败，先看报错的测试名，不要把未通过的结果解释成业务结论。</p>
<p>已有数据，只重跑模型与测试：</p>
<div class="sourceCode" id="cb2"><pre
class="sourceCode bash"><code class="sourceCode bash"><span id="cb2-1"><a href="#cb2-1" aria-hidden="true" tabindex="-1"></a><span class="ex">python</span> run_all.py <span class="at">--skip-generate</span></span></code></pre></div>
<p>只运行测试：</p>
<div class="sourceCode" id="cb3"><pre
class="sourceCode bash"><code class="sourceCode bash"><span id="cb3-1"><a href="#cb3-1" aria-hidden="true" tabindex="-1"></a><span class="ex">python</span> <span class="at">-m</span> unittest discover <span class="at">-s</span> tests <span class="at">-v</span></span></code></pre></div>
<p>换种子作为一个新实验：<code>python run_all.py --seed 20261107</code>。若同时使用
<code>--skip-generate</code>，会直接读取现有数据，因此种子参数不起作用。默认交付种子是20261106；改变种子后以实际
<code>data/manifest.json</code> 的行数和 <code>outputs/RESULTS.md</code>
的结论为准，不沿用默认版成绩。</p>
<p>运行时间取决于电脑。程序无训练进度条，看到
<code>Evaluating returns ...</code>
后暂时不打印并不代表卡住。完整数据、结果和测试日志已随包附上。</p>
<h2 id="数据规模与日历">数据规模与日历</h2>
<p>所有日期以
<strong>2025-01-01为第0日</strong>，每个项目有独立账本，不可以用相同日期把四套虚构业务强行合并。</p>
<table style="width:100%;">
<colgroup>
<col style="width: 16%" />
<col style="width: 22%" />
<col style="width: 16%" />
<col style="width: 22%" />
<col style="width: 22%" />
</colgroup>
<thead>
<tr class="header">
<th>项目</th>
<th style="text-align: right;">独立实体数</th>
<th>创建/发货日期范围</th>
<th style="text-align: right;">观察到第几日</th>
<th style="text-align: right;">默认交付种子事件行数</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>预售</td>
<td style="text-align: right;">20,000单</td>
<td>第0至359日，360天</td>
<td style="text-align: right;">第419日</td>
<td style="text-align: right;">80,000</td>
</tr>
<tr class="even">
<td>退货</td>
<td style="text-align: right;">12,000行，每行1件</td>
<td>第0至179日，180天</td>
<td style="text-align: right;">第209日</td>
<td style="text-align: right;">33,053</td>
</tr>
<tr class="odd">
<td>COD</td>
<td style="text-align: right;">10,000包裹，每包1至4件</td>
<td>第0至179日，180天</td>
<td style="text-align: right;">第209日</td>
<td style="text-align: right;">34,319</td>
</tr>
<tr class="even">
<td>PO</td>
<td style="text-align: right;">2,000条，每条一种模拟物料</td>
<td>第0至359日，360天</td>
<td style="text-align: right;">第449日</td>
<td style="text-align: right;">7,659</td>
</tr>
</tbody>
</table>
<p>预售的20,000单在两种发货机制下重复模拟，是<strong>同一批订单的成对实验</strong>，不是40,000个独立样本。事件数含创建事件。退货多观察30天是生成器的明确假设：本模拟所有回流路径最晚29天结束；现实若存在60天退货，不能照搬这个成熟标准。</p>
<h2 id="文件地图">文件地图</h2>
<ul>
<li><code>src/generate.py</code>：固定种子20261106，各项目用种子加0/100/200/300。生成机制可逐行检查。</li>
<li><code>src/labels.py</code>：只看指定截止日之前的事件重建标签。</li>
<li><code>src/models.py</code>：可读的分组概率、逻辑回归、条件回流路径、Kaplan–Meier等基线。</li>
<li><code>src/evaluate.py</code>：按时间训练、在验证集选参数、冻结后评估测试集。</li>
<li><code>tests/test_project.py</code>：23项契约测试，检查时间、成熟度、状态守恒、未来事件隔离、手算、变种子重跑、动态报告及删失/零回流边界。</li>
<li><code>data/manifest.json</code>：种子、规模、时间分块、数据文件SHA-256校验值。</li>
<li>每个 <code>data/项目/</code>：<code>features.csv</code>
是评分当时可用的特征；<code>events.csv</code>
是事后逐步发生的事件。</li>
<li><code>ORACLE_DO_NOT_TRAIN.csv</code>：<strong>模拟器知道、现实运营人员不知道的潜在真相</strong>。不能并入训练特征。仅预售诊断用它比较偏差。</li>
<li><code>outputs/项目/</code>：已经运行出的预测、账本、图、模型选择与评估。</li>
<li><code>docs/DATA_DICTIONARY.md</code>：字段、单位、空值含义和事件口径。</li>
<li><code>docs/TIME_AND_LEAKAGE.md</code>：日期切分、成熟缓冲、防泄漏规则。</li>
<li><code>docs/MODEL_CARDS.md</code>：实现了什么、没有实现什么、结论不能怎么用。</li>
<li><code>docs/EXERCISES.md</code>：面向高中读者的四个动手步骤及答案检查。</li>
</ul>
<h2 id="四项任务各交付什么">四项任务各交付什么</h2>
<p><strong>1. 预售取消</strong></p>
<p>先画训练风险集，再计算未平滑/平滑的每日取消率。以验证集选择平滑强度；测试集只评分。<code>survival.svg</code>
对比独立发货、信息性发货与模拟潜在真值。<code>conditional_pending_demand_scenario.csv</code>
从当前未发订单出发计算条件留存；它是明确假设“不发货”的情景，不是可售库存，也不声称能还原真实消费者意愿。第60日强制关单单独计数，不训练成自然取消。</p>
<p><strong>2. 退货回流</strong></p>
<p>分别估计退货概率、退回后的可售良率、最终可售件的发货至入库时滞，再按发货批次加到对应日期。<code>test_cohort_daily_restock.csv</code>
只比较测试批次，避免把其他批次混进分母。下一周预测另用当时的无申请/退运/待质检/待上架状态筛选历史相似路径，已经回流的件不会再加一次。<code>actual_physical_stock_ledger.csv</code>
只认实际质检及上架事件；食品不可再售情景的回流固定为0。</p>
<p><strong>3. COD拒收</strong></p>
<p>比较训练期平均概率与标准化逻辑回归。在验证集前半段只校准截距，后半段选择人工复核阈值。测试集输出Brier、对数损失、分组校准和假想成本。成本里的复核有效率是假设，不能当作干预效果证据。<code>actual_inventory_and_expected_sales.csv</code>
分列在途、实物库存和测试批次预期净销售，发出100件就扣100件，不因为预计会拒收而少扣。</p>
<p><strong>4. PO交期</strong></p>
<p>每条PO可分三次收货，未收齐仍保留。比较固定交期、只看已完成样本的朴素分位数、包含右删失的Kaplan–Meier。P90证据不足时留空，不凭空填一个“保守值”。<code>coverage_bounds.csv</code>
显示覆盖率上下界与可预测样本数；已完成样本上的pinball仅作有选择偏差的诊断。</p>
<h2 id="不要跳过的边界">不要跳过的边界</h2>
<ul>
<li>所有“效果”都只针对这里的随机机制，不能直接迁移为企业ROI或上线依据。</li>
<li>有代码和测试，不等于识别了因果关系、消除了所有模型风险或完成了生产工程。</li>
<li>测试集中的COD风险有预设上移，故校准后模型也可能变差。请如实保留。</li>
<li>预售低Brier可能只因取消较少，不能单凭低分证明潜在留存曲线正确。</li>
<li>PO“尚未收齐”不是“永远不收齐”；右删失也不是取消。</li>
<li>本包没有生产连接、模型服务、权限体系、实时数据管道或自动业务动作。</li>
</ul>
<p>课程中如果还有单独的60日确定性手算表，那是另一套教学设定。不要把它的每日取消率当成本包随机数据的真值。</p>
