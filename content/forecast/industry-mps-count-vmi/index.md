{
  "title": "制造主计划计数分布与产权责任",
  "description": "制造主计划计数分布与产权责任：这里补齐生鲜基地到门店、鞋服地域颜色尺码、延迟制造、促销透支、活动类比、制造备件及医药聚合预测之间原来未展开的步骤。所有企业、商品、事件、数据、时间和参数均为明确构造的模拟。没有真实业务数据，没有连接采购、生产、财务、配送或医疗系统。本课中",
  "type": "forecast",
  "unit": "industry-mps-count-vmi",
  "weight": 99,
  "outputs": [
    "HTML"
  ]
}

<p class="check">R2独立验收的行业教学扩展。<a href="/forecast/forecast-industry-gap-labs.zip" download>下载行业9课实验包</a>。所有数据均模拟；给定VMI产权合同、固定单位价值、无财税/法务认证，非通用APS。</p><details><summary>共同阅读约定</summary><h2 id="行业多层级预测与决策补课">行业多层级预测与决策补课</h2>
<p>这里补齐生鲜基地到门店、鞋服地域颜色尺码、延迟制造、促销透支、活动类比、制造备件及医药聚合预测之间原来未展开的步骤。所有企业、商品、事件、数据、时间和参数均为明确构造的模拟。没有真实业务数据，没有连接采购、生产、财务、配送或医疗系统。本课中的“订单”“分录”“锁产”均为离线建议或教学账，不代表已经执行。</p>
<p>R2补强了输入校验：重复主键、矛盾的组级份额、超出固定需求模板会报错；时间序列按时间键计算，不依赖CSV行顺序。默认手算答案不变。</p>
<p>先完成百分比、加权平均、库存收支和训练集/验证集的基础课，再按本课顺序学习。每课建议60到90分钟：读业务问题、逐项手算、跑代码、修改一个输入、写边界。数学只用高一可读的代数与概率；需要最小二乘时会解释其含义，代码负责重复算术，不把“调用了一个函数”当作理解。</p>
<p>项目包 forecast-industry-gap-labs.zip 只需 Python 3.10
或更新版本的标准库。解压并进入目录后执行：</p>
<div class="sourceCode" id="cb1"><pre class="sourceCode sh"><code class="sourceCode bash"><span id="cb1-1"><a href="#cb1-1" aria-hidden="true" tabindex="-1"></a><span class="ex">python</span> run_all.py</span>
<span id="cb1-2"><a href="#cb1-2" aria-hidden="true" tabindex="-1"></a><span class="ex">python</span> <span class="at">-m</span> unittest <span class="at">-v</span> test_industry</span>
<span id="cb1-3"><a href="#cb1-3" aria-hidden="true" tabindex="-1"></a><span class="ex">python</span> manufacture_pharma.py self-test</span></code></pre></div>
<p>首次解压已含模拟CSV。run_all.py仅重算，不覆盖输入。要另建一份原始输入，运行
<code>python generate_all.py --data fresh_data</code>，随后用
<code>python run_all.py --data fresh_data --out fresh_outputs</code>
重算。生成器拒绝覆盖非空目录；先复制目录再改参。生成数据与运行模型是两步，脚本输出由CSV计算，不从教材答案回填。统一参考结果在
outputs/，子项目结果在
outputs/manufacture_pharma/。仅运行上面第一条不等于跑过测试。</p>
</details><h2 id="行业补课七-冻结主生产计划-计数分布与-vmi-责任账">行业补课七
冻结主生产计划 计数分布与 VMI 责任账</h2>
<p>稳定 slug：<code>industry-mps-count-vmi</code>。来源：B05，第二部分
L65–67。建议学习时间：三段各 35 分钟，作业 30 分钟。</p>
<h3 id="这节课解决什么问题">1 这节课解决什么问题</h3>
<p>制造企业会同时遇到三种问题：下一季至明年每周安排多少产出，某网点下个月会领几件备件，以及供应商放在厂里的货到底是谁的。三者时间、单位和责任不同，不能拿一张日销量预测表替代。</p>
<p>完成本课后，你应该能够：</p>
<ol type="1">
<li>编制同一起点的 13 周和 52
周主生产计划，保持前四周冻结，并把缺口显示出来。</li>
<li>用相同的训练期、测试期比较 Poisson
与负二项分布，而不只比较平均数。</li>
<li>按发运、收货、产权转移、领用、报废、退回、付款逐笔核对数量、价值和责任。</li>
</ol>
<h3 id="主生产计划-mps-的期限与冻结区">2 主生产计划 MPS
的期限与冻结区</h3>
<p>MPS 是 Master Production
Schedule，即主生产计划。本课以一个成品为单位，输出每周预计完成并可用的成品数量。它不是采购订单，也没有把这些成品进一步展开成多层
BOM。</p>
<p>本例在第 0 周编计划：</p>
<ul>
<li>13 周版看未来约一季；52 周版看未来约一年。52
周远期数字仍需修订，不能把“看得远”理解为“承诺得更确定”。</li>
<li>两版从同一周开始，前四周使用已批准计划，冻结区外允许重算。</li>
<li>周产能最多 100 件，每批 10 件，期初库存 40 件，希望周末至少留 20
件。</li>
<li>原需求按 60、70、80、90 四周循环。原计划前四周产出为
40、70、80、90。</li>
<li>第 0 周收到新信息：第 2 周需求由 70 增到
170。新信息已知，但前四周产出不因此自动改变。</li>
</ul>
<p>“冻结”表示不能由算法擅改已批准数量。遇到严重缺口，程序提出变更请求，交给业务流程处理；本项目不模拟审批通过，不偷偷解冻。</p>
<h4 id="每个符号只代表一件事">2.1 每个符号只代表一件事</h4>
<p>设某周编号为 t：</p>
<ul>
<li>D_t：本周需求，单位件。</li>
<li>Q_t：本周计划可用的成品数量，单位件。</li>
<li>N_(t−1)：上周末净库存，单位件；正数是现货，负数表示欠交。</li>
<li>N_t：本周末净库存。</li>
<li>S：期望保留的安全库存，本例 20 件。</li>
<li>C：周产能上限，本例 100 件。</li>
<li>L：批量大小，本例 10 件。</li>
<li>F：冻结周数，本例 4；Q_old,t 是旧批准数量。</li>
<li>max(a,b) 取较大值，min(a,b) 取较小值；ceil(x) 向上取整，例如
ceil(2.3)=3。</li>
</ul>
<p>先算不考虑冻结的产出建议：</p>
<p><code>需要量 = max(0, D_t + S − N_(t−1))</code></p>
<p><code>产出建议 = min(C, L × ceil(需要量 / L))</code></p>
<p>再执行冻结规则：前 F 周用
Q_old,t，其余周用产出建议。然后逐周递推：</p>
<p><code>N_t = N_(t−1) + Q_t − D_t</code></p>
<p><code>现货 = max(0, N_t)</code>；<code>欠交 = max(0, −N_t)</code>。</p>
<p>例如 N_t=−80 表示现货 0、欠交 80，不是货架上存在“负 80
件”。下一周先弥补欠交，再满足新增需求。程序的安全库存目标是软目标，产能不足时允许达不到，但把结果列出。</p>
<h4 id="手算前八周">2.2 手算前八周</h4>
<table>
<colgroup>
<col style="width: 11%" />
<col style="width: 15%" />
<col style="width: 15%" />
<col style="width: 11%" />
<col style="width: 15%" />
<col style="width: 15%" />
<col style="width: 15%" />
</colgroup>
<thead>
<tr class="header">
<th>周</th>
<th style="text-align: right;">新需求 D</th>
<th style="text-align: right;">旧计划</th>
<th>是否冻结</th>
<th style="text-align: right;">本次产出 Q</th>
<th style="text-align: right;">期末净库存 N</th>
<th style="text-align: right;">期末欠交</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>1</td>
<td style="text-align: right;">60</td>
<td style="text-align: right;">40</td>
<td>是</td>
<td style="text-align: right;">40</td>
<td style="text-align: right;">20</td>
<td style="text-align: right;">0</td>
</tr>
<tr class="even">
<td>2</td>
<td style="text-align: right;">170</td>
<td style="text-align: right;">70</td>
<td>是</td>
<td style="text-align: right;">70</td>
<td style="text-align: right;">−80</td>
<td style="text-align: right;">80</td>
</tr>
<tr class="odd">
<td>3</td>
<td style="text-align: right;">80</td>
<td style="text-align: right;">80</td>
<td>是</td>
<td style="text-align: right;">80</td>
<td style="text-align: right;">−80</td>
<td style="text-align: right;">80</td>
</tr>
<tr class="even">
<td>4</td>
<td style="text-align: right;">90</td>
<td style="text-align: right;">90</td>
<td>是</td>
<td style="text-align: right;">90</td>
<td style="text-align: right;">−80</td>
<td style="text-align: right;">80</td>
</tr>
<tr class="odd">
<td>5</td>
<td style="text-align: right;">60</td>
<td style="text-align: right;">60</td>
<td>否</td>
<td style="text-align: right;">100</td>
<td style="text-align: right;">−40</td>
<td style="text-align: right;">40</td>
</tr>
<tr class="even">
<td>6</td>
<td style="text-align: right;">70</td>
<td style="text-align: right;">70</td>
<td>否</td>
<td style="text-align: right;">100</td>
<td style="text-align: right;">−10</td>
<td style="text-align: right;">10</td>
</tr>
<tr class="odd">
<td>7</td>
<td style="text-align: right;">80</td>
<td style="text-align: right;">80</td>
<td>否</td>
<td style="text-align: right;">100</td>
<td style="text-align: right;">10</td>
<td style="text-align: right;">0</td>
</tr>
<tr class="even">
<td>8</td>
<td style="text-align: right;">90</td>
<td style="text-align: right;">90</td>
<td>否</td>
<td style="text-align: right;">100</td>
<td style="text-align: right;">20</td>
<td style="text-align: right;">0</td>
</tr>
</tbody>
</table>
<p>第 2 周：20+70−170=−80。若允许改变计划，算法最多也只能建议 100
件，而不是不顾产能安排 170 件。由于本周冻结，保留
70，另输出变更请求。</p>
<p>第 5 周：需要量=60+20−(−80)=160，产能只允许
100，净库存=−80+100−60=−40。第 7 周欠交消除，第 8 周安全库存回到 20。13
周与 52 周版的前 13
周一致，因为本例使用同样的输入和逐周规则，没有远期全局优化。</p>
<h4 id="数据与输出">2.3 数据与输出</h4>
<ul>
<li><code>mps_parameters.csv</code>：每行一个计划期限。<code>horizon_weeks</code>
为 13 或
52；<code>opening_units</code>、<code>safety_units</code>、<code>capacity_units</code>、<code>lot_units</code>
的单位都是成品件；<code>freeze_weeks</code>
是冻结周数；<code>planning_as_of_week=0</code> 为信息截止周。</li>
<li><code>mps_demand.csv</code>：一周一行，共 52
行。<code>base_demand_units</code>
是用于生成旧计划的原始需求留痕；重算实际使用
<code>revised_demand_units</code> 与
<code>prior_receipt_units</code>。<code>known_at_week</code>
必须不晚于计划截止周。</li>
<li><code>mps_13.csv</code> 和
<code>mps_52.csv</code>：保留旧数量、建议数量、实际采用数量、冻结标志、净库存、现货、欠交、冻结变更请求。</li>
</ul>
<p>本例假设本周 Q
可用于本周需求，已经把前置投料安排折合进完成量；没有显式计算工序提前期、共享物料、换线或跨工厂产能。它是小型离线
MPS 机制练习，不是 APS 最优排程。</p>
<h3 id="为什么平均每月两件仍然可能需要不同模型">3
为什么平均每月两件仍然可能需要不同模型</h3>
<p>设 K 是某网点某个月领用备件的件数，它只能取
0、1、2……。两条序列平均都等于 2，不代表风险一样。</p>
<ul>
<li>regular：每六个月为 0、1、2、2、3、4。</li>
<li>bursty：训练期每六个月为 0、0、1、1、2、8。</li>
</ul>
<p>每种模式重复四次，形成 24 个月训练期。随后保留 12
个月作为测试：regular 延续原模式，bursty 改为
0、0、0、1、3、8，重复两次。测试期不参与拟合。全部都是人为构造，不能据此推断真实备件需求分布。</p>
<h4 id="均值与样本方差">3.1 均值与样本方差</h4>
<p>记训练观测为 k_1 到 k_n，n 是月份数。μ（读作 mu）是均值：</p>
<p><code>μ = (k_1 + ... + k_n) / n</code></p>
<p>样本方差记为 s²：</p>
<p><code>s² = [(k_1−μ)² + ... + (k_n−μ)²] / (n−1)</code></p>
<p>平方是为了让正负偏差不会相互抵消。本课使用 n−1 作分母，不要与除以 n
的“总体方差”混用。</p>
<p>bursty 的一组总和为 12，均值=12/6=2。一组偏差平方和为
4+4+1+1+0+36=46，四组为 184，所以 24 个月的
s²=184/23=8。它的方差比均值大，称为过度离散。</p>
<h4 id="poisson-分布的概率">3.2 Poisson 分布的概率</h4>
<p>Poisson
常译作泊松。假设每月事件发生率相近、事件之间没有强烈聚集等因素，其均值与方差都为
μ。它给每个整数 k 一个概率：</p>
<p><code>P(K=k) = e^(−μ) × μ^k / k!</code></p>
<p>P 表示概率；e 约为 2.71828；k! 是 1×2×…×k，约定 0!=1；μ^k 是 μ 连乘 k
次。μ=2 时：</p>
<ul>
<li>P(K=0)=e^(−2)≈0.135335，即零需求月约占 13.53%。</li>
<li>P(K=2)=e^(−2)×2²/2≈0.270671。</li>
</ul>
<p>这不是说下一月一定有两件，而是对所有可能件数分配概率。</p>
<h4 id="负二项分布增加一个分散参数">3.3 负二项分布增加一个分散参数</h4>
<p>本课采用 NB2 参数化：均值仍为 μ，额外参数 r&gt;0 控制分散程度：</p>
<p><code>方差 = μ + μ²/r</code></p>
<p>r
越小，在相同均值下允许的波动越大。用训练样本的均值和方差代入，可解得：</p>
<p><code>r = μ² / (s²−μ)</code></p>
<p>这叫矩估计，用样本的均值、方差去匹配分布，不是最大似然估计。本例
μ=2、s²=8，因此 r=4/(8−2)=2/3。</p>
<p>记 p=r/(r+μ)，则零需求的概率是 p^r。这里 p=(2/3)/(2/3+2)=1/4，因此
P(K=0)=(1/4)^(2/3)≈0.396850。它能同时给零需求月和大需求月更高的概率。</p>
<p>如果想不借助高等函数算任意 k，可以从 P(K=0) 出发递推：</p>
<p><code>P(K=k+1) = P(K=k) × (k+r)/(k+1) × μ/(r+μ)</code></p>
<p>右边所有符号都已定义。代码采用等价的对数 Gamma
形式避免中间数太大，理解上述递推即可，不要求先学 Gamma 函数。</p>
<p>若 s²≤μ，这个矩估计不能产生合法的有限正 r。程序明确回退
Poisson，<code>effective_model</code> 写
Poisson，<code>dispersion_r</code> 留空。regular 的
s²=1.739130&lt;2，所以不能硬造一个负 r。若训练全为零，模型把零的概率设为
1；测试突然出现正数，负对数损失为无穷，结果写
<code>infinity</code>，而不是静默抹平错误。</p>
<h4 id="用相同测试月份比较概率">3.4 用相同测试月份比较概率</h4>
<p>对测试月实际出现的 k，查模型分配的概率 p_k。负对数损失为
<code>−ln(p_k)</code>，ln 为自然对数；概率越小，损失越大。测试 n_test
个月的平均值叫平均 NLL，越小越好。例如实际为 0，Poisson 给概率
0.135335，对应损失 2；负二项给 0.396850，对应损失约 0.924196。</p>
<p>默认数据的实际运行结果：</p>
<table>
<colgroup>
<col style="width: 13%" />
<col style="width: 17%" />
<col style="width: 17%" />
<col style="width: 17%" />
<col style="width: 17%" />
<col style="width: 17%" />
</colgroup>
<thead>
<tr class="header">
<th>序列与模型</th>
<th style="text-align: right;">均值</th>
<th style="text-align: right;">方差估计</th>
<th style="text-align: right;">P(K=0)</th>
<th style="text-align: right;">P(K≥6)</th>
<th style="text-align: right;">测试平均 NLL</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>bursty Poisson</td>
<td style="text-align: right;">2</td>
<td style="text-align: right;">8</td>
<td style="text-align: right;">0.135335</td>
<td style="text-align: right;">0.016564</td>
<td style="text-align: right;">2.679766</td>
</tr>
<tr class="even">
<td>bursty 负二项</td>
<td style="text-align: right;">2</td>
<td style="text-align: right;">8</td>
<td style="text-align: right;">0.396850</td>
<td style="text-align: right;">0.101403</td>
<td style="text-align: right;">1.853080</td>
</tr>
<tr class="odd">
<td>regular Poisson</td>
<td style="text-align: right;">2</td>
<td style="text-align: right;">1.739130</td>
<td style="text-align: right;">0.135335</td>
<td style="text-align: right;">0.016564</td>
<td style="text-align: right;">1.673057</td>
</tr>
<tr class="even">
<td>regular 负二项候选回退 Poisson</td>
<td style="text-align: right;">2</td>
<td style="text-align: right;">1.739130</td>
<td style="text-align: right;">0.135335</td>
<td style="text-align: right;">0.016564</td>
<td style="text-align: right;">1.673057</td>
</tr>
</tbody>
</table>
<p>P(K≥6) 是“6 件及以上”的概率，等于 1 减去 0 至 5 件的概率之和。bursty
测试期零需求月占 50%，两种拟合都没有精确达到
50%；负二项损失较低，也不代表概率已完美校准。</p>
<p>输入 <code>branch_month_counts.csv</code>
一行是一网点一月，<code>known_at_month=period_month+1</code>。第 25
月时拟合，已能获得第 24 月记录；测试为第 25 至 36 月。参数在
<code>count_parameters.csv</code>。输出
<code>count_model_comparison.csv</code>。月度备件件数不与周度成品 MPS
相加。</p>
<h3 id="vmi-中保管货物与拥有货物不同">4 VMI
中保管货物与拥有货物不同</h3>
<p>VMI
是供应商管理库存的协作方式，<strong>不自动决定产权</strong>。买断货也可能由供应商管理。本课特别约定“寄售式
VMI”：供应商保留远端仓、在途和厂内寄售区的货权；厂方领用时才转移产权。</p>
<p>这只是例题合同假设。真实业务应依据合同、会计政策和适用法律确认。本账用于数量与价值责任核对，不是法定会计分录模板。</p>
<h4 id="先写清口径">4.1 先写清口径</h4>
<p>供应商期初有 100 件，每件教学价值 10
元。供应商账面成本和转移给厂方的价格都设为 10
元，忽略毛利、税费、汇率和减值，因而可以做简明的价值守恒。</p>
<ul>
<li>位置分为供应商远端、在途、厂内供应商货、厂内厂方货。</li>
<li>产权分为供应商与厂方。所有在途货在本例都由供应商持有产权，承运人保管不代表承运人拥有。</li>
<li>已消耗和已报废另列，不再计入实物库存。</li>
<li>领用产生厂方耗用责任；供应商质量问题报废由供应商承担。</li>
<li>厂方应付与供应商应收在产权转移时同时增加；付款时同时减少。</li>
</ul>
<h4 id="逐笔手算">4.2 逐笔手算</h4>
<table>
<colgroup>
<col style="width: 11%" />
<col style="width: 14%" />
<col style="width: 14%" />
<col style="width: 14%" />
<col style="width: 14%" />
<col style="width: 14%" />
<col style="width: 14%" />
</colgroup>
<thead>
<tr class="header">
<th>事件</th>
<th style="text-align: right;">实物库存</th>
<th style="text-align: right;">供应商持有数量</th>
<th style="text-align: right;">厂方持有数量</th>
<th style="text-align: right;">厂方应付</th>
<th style="text-align: right;">累计厂方耗用价值</th>
<th style="text-align: right;">累计供应商报废责任</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>期初</td>
<td style="text-align: right;">100</td>
<td style="text-align: right;">100</td>
<td style="text-align: right;">0</td>
<td style="text-align: right;">0</td>
<td style="text-align: right;">0</td>
<td style="text-align: right;">0</td>
</tr>
<tr class="even">
<td>发出 40 件</td>
<td style="text-align: right;">100</td>
<td style="text-align: right;">100</td>
<td style="text-align: right;">0</td>
<td style="text-align: right;">0</td>
<td style="text-align: right;">0</td>
<td style="text-align: right;">0</td>
</tr>
<tr class="odd">
<td>厂内收到 40 件</td>
<td style="text-align: right;">100</td>
<td style="text-align: right;">100</td>
<td style="text-align: right;">0</td>
<td style="text-align: right;">0</td>
<td style="text-align: right;">0</td>
<td style="text-align: right;">0</td>
</tr>
<tr class="even">
<td>领用触发产权转移 25 件</td>
<td style="text-align: right;">100</td>
<td style="text-align: right;">75</td>
<td style="text-align: right;">25</td>
<td style="text-align: right;">250</td>
<td style="text-align: right;">0</td>
<td style="text-align: right;">0</td>
</tr>
<tr class="odd">
<td>同日实际消耗 25 件</td>
<td style="text-align: right;">75</td>
<td style="text-align: right;">75</td>
<td style="text-align: right;">0</td>
<td style="text-align: right;">250</td>
<td style="text-align: right;">250</td>
<td style="text-align: right;">0</td>
</tr>
<tr class="even">
<td>供应商质量报废 5 件</td>
<td style="text-align: right;">70</td>
<td style="text-align: right;">70</td>
<td style="text-align: right;">0</td>
<td style="text-align: right;">250</td>
<td style="text-align: right;">250</td>
<td style="text-align: right;">50</td>
</tr>
<tr class="odd">
<td>剩余 10 件退运并收回</td>
<td style="text-align: right;">70</td>
<td style="text-align: right;">70</td>
<td style="text-align: right;">0</td>
<td style="text-align: right;">250</td>
<td style="text-align: right;">250</td>
<td style="text-align: right;">50</td>
</tr>
<tr class="even">
<td>厂方付款 100 元</td>
<td style="text-align: right;">70</td>
<td style="text-align: right;">70</td>
<td style="text-align: right;">0</td>
<td style="text-align: right;">150</td>
<td style="text-align: right;">250</td>
<td style="text-align: right;">50</td>
</tr>
</tbody>
</table>
<p>产权转移与使用在输入中是相邻、同日、同数量的两笔子记录，便于看清两个账的变化；完整业务处理要求它们匹配。第一笔只换所有者，第二笔才减少实物。程序拒绝缺少匹配使用、日期不匹配或数量不匹配的输入。</p>
<p>供应商最终远端库存=100−40+10=70，厂内寄售区=40−25−5−10=0，在途为
0。厂方应付=25×10−100=150；供应商应收也为
150。付款是模拟记录，不是实际转账。</p>
<h4 id="三条守恒必须同时成立">4.3 三条守恒必须同时成立</h4>
<p>设 I_s、I_f 为供应商和厂方拥有的实物件数；U 为累计耗用件数；W
为累计报废件数；v 为每件价值：</p>
<p><code>期初100 = I_s + I_f + U + W</code></p>
<p><code>期初价值1000 = I_s×v + I_f×v + 厂方累计耗用价值 + 供应商累计报废责任</code></p>
<p><code>厂方应付 = 供应商应收</code></p>
<p>期末代入：100=70+0+25+5；1000=700+0+250+50；应付=应收=150。不要把现金付款再加进库存价值式，它结算往来，没有再消耗
10 件货。</p>
<p><code>vmi_parameters.csv</code>
给期初数量和单位价值；<code>vmi_events.csv</code>
给有序事件、发生日、已知日、数量及付款金额。输出
<code>vmi_responsibility_ledger.csv</code>
逐行保留所有位置、产权、耗用、报废、应收、应付与两个守恒残差。残差应始终为
0。</p>
<h3 id="本课作业与精确验收">5 本课作业与精确验收</h3>
<p>每次实验先复制默认 <code>data/</code> 到新目录，编辑副本，然后用
<code>run</code> 计算。输入文件应保留模拟标签。</p>
<ol type="1">
<li><strong>原样复现。</strong> 13 与 52 周分别有 13、52
行；前四周产出都为 40、70、80、90；最大欠交 80；冻结变更请求 3
次；期末现货 20、欠交 0。两份计划前 13 周逐行相同。</li>
<li><strong>撤销需求冲击。</strong> 把 <code>mps_demand.csv</code> 第 2
周的 <code>revised_demand_units</code> 从 170 改回 70。重算后欠交峰值为
0、冻结变更请求为 0，前四周产出仍为 40、70、80、90。只改
<code>base_demand_units</code>
不会改变本次重排，这是留痕字段与实际输入字段的区别。</li>
<li><strong>检查分布。</strong> 手算 bursty 的
μ=2、s²=8、r=2/3；程序结果允许绝对误差 0.000001。解释为何 regular
不应得到负的 r。两类序列均为训练 24 月、测试 12
月，不允许把测试行混进均值和方差。</li>
<li><strong>改变付款。</strong> 将 VMI 最后一笔付款 100 改成
150。最终应付与应收均变为 100 元；库存仍为 70 件，耗用价值仍为
250，报废责任仍为 50；所有守恒残差仍为 0。</li>
<li><strong>故意破坏领用。</strong> 将 <code>USE</code> 的 25 改成
99，必须报错。程序不能产生负库存后继续声称账平。</li>
<li><strong>解释业务边界。</strong>
写出至少三点：冻结异常需要业务处理；月度计数不是周排产；VMI
不必然寄售；本账不替代法定会计；任意三点正确即通过。</li>
</ol>
