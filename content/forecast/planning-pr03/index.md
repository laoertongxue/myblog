{
  "title": "五节点多级库存：库存放哪儿，与总共有多少不同",
  "description": "五节点多级库存：库存放哪儿，与总共有多少不同：本章提供6个可以离线运行的合成实验。其中生产实验又分央厨与制造两个小案例。它们补的是“怎样把预测变成需求、供应、财务与库存账”，不是企业实施方案。所有日期、价格、概率、产能与业务记录均为教学设定，没有客户真实资料。",
  "type": "forecast",
  "unit": "planning-pr03",
  "weight": 72,
  "outputs": [
    "HTML"
  ]
}

<p class="check">已独立审查的模拟计划实验。<a href="/forecast/planning-remaining-labs.zip" download>下载计划侧6个实验</a>。固定优先级或有限枚举的结果不是通用MILP/APS全局最优，不代表真实收益。包内pending为冻结时记录，第二版独立审查已通过其注明范围。</p><details><summary>共同运行方法与教学边界</summary><h2
id="计划侧补全课从预测数字走到能检查的计划">计划侧补全课：从预测数字走到能检查的计划</h2>
<h2 id="这次真正能完成什么">这次真正能完成什么</h2>
<p>本章提供6个可以离线运行的合成实验。其中生产实验又分央厨与制造两个小案例。它们补的是“怎样把预测变成需求、供应、财务与库存账”，不是企业实施方案。所有日期、价格、概率、产能与业务记录均为教学设定，没有客户真实资料。</p>
<ul>
<li>已完成：两版各12个月的需求／供应／财务并列表、CPFR协商时点；两层BOM与3周排程；1CDC＋2RDC＋2FDC的多日库存和在途账；双供应商分单枚举；COD应收与回款日账；30日库存、预测、调整与业务指标重算。</li>
<li>已运行：Python标准库程序，6份JSON输入，8份CSV结果，完整JSON结果，71项作者测试。测试覆盖基准答案、守恒、31个非法输入、合法参数变化及零分母。作者测试不等于独立审计。</li>
<li>未完成、也不冒充完成：没有训练预测模型，没有调用MILP求解器，没有证明通用APS或MEIO全局最优，没有接企业ERP/WMS，没有下采购单、生产单或调拨单，没有真实业务收益证据。</li>
<li>数值上的“最优”只在明确有限候选集合内成立。生产采用先A后B的启发式。网络采用固定补货启发式，再穷举210种起始库存配置。供应商对给定订货日的7种合法分单全部比较，因此只在该小模型中可证明最优。</li>
</ul>
<p><strong>配套包：planning-remaining-labs.zip。</strong>
解压后运行：</p>
<pre class="text"><code>python run.py
python test_labs.py</code></pre>
<p>需要Python
3.10或更新版，无需安装第三方库。第一次命令从data目录读取输入并生成outputs；第二次命令把计算结果与教学答案、约束和已交付结果比对。成功末行分别显示6个实验已完成和71项检查通过。参数示例：<code>python run.py --data data --out my_results</code>。修改数据后先看my_results，不要把旧答案当新结果；test_labs.py的基准答案有意固定于原始教学输入。</p>
<h2 id="先学会看公式和代码">先学会看公式和代码</h2>
<ul>
<li><code>t</code>是第几期。例如t=2指第二个月，不是乘以2；下标<code>t−1</code>表示上一期。</li>
<li><code>min(a,b)</code>表示取两个数较小者。例如min(12,8)=8。</li>
<li><code>max(a,0)</code>表示负数改为0。例如max(−3,0)=0。</li>
<li><code>floor(a)</code>表示向下取整。例如floor(8÷0.3)=26。只能交付完整一份菜，不能把26.666份写成27份。</li>
<li><code>Σ</code>表示把指定各项相加。<code>Σd_t</code>就是把每期需求d_t加起来，不是另一种神秘运算。</li>
<li><code>p×c</code>表示概率p乘以某情景成本c。它是许多次同类试验的平均成本贡献，不意味着一次一定支付这个金额。</li>
<li>数量必须带单位。件可以加件，kg可以加kg；不能把100件＋20kg写成120。</li>
<li>程序里的<code>=</code>是赋值。例如<code>stock = stock - sold</code>是更新库存。公式中的等号则表示两边数值相同。</li>
</ul>
<p>每个实验都遵循：先写假设和输入 → 手算一行 → 计算全表 → 验证守恒 →
改一个条件观察变化 → 承认模型边界。</p>
</details><h2
id="pr03五节点多级库存库存放哪儿与总共有多少不同">PR03｜五节点多级库存：库存放哪儿，与总共有多少不同</h2>
<h2 id="网络时间与公平比较">1. 网络、时间与公平比较</h2>
<p>network.json包含五个节点：CDC总仓、R1/R2两个区域仓、F1/F2两个前置仓。货走CDC→R1→F1或CDC→R2→F2。每条边运输1天，消费者只从F1/F2买货。</p>
<p>每天固定顺序：早上到货 → 当天消费者购买 → 晚上申请调拨 →
次日早上到货。本课未满足需求视为丢失，不延期交。没有外部供应补入、没有过期、没有退货；实验只运行6天。</p>
<p>三种起始配置总量都是60件，单位采购成本相同，才可以公平比较：</p>
<table>
<thead>
<tr class="header">
<th>配置</th>
<th style="text-align: right;">CDC</th>
<th style="text-align: right;">R1</th>
<th style="text-align: right;">R2</th>
<th style="text-align: right;">F1</th>
<th style="text-align: right;">F2</th>
<th style="text-align: right;">合计</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>集中</td>
<td style="text-align: right;">60</td>
<td style="text-align: right;">0</td>
<td style="text-align: right;">0</td>
<td style="text-align: right;">0</td>
<td style="text-align: right;">0</td>
<td style="text-align: right;">60</td>
</tr>
<tr class="even">
<td>分散</td>
<td style="text-align: right;">0</td>
<td style="text-align: right;">0</td>
<td style="text-align: right;">0</td>
<td style="text-align: right;">30</td>
<td style="text-align: right;">30</td>
<td style="text-align: right;">60</td>
</tr>
<tr class="odd">
<td>混合</td>
<td style="text-align: right;">20</td>
<td style="text-align: right;">10</td>
<td style="text-align: right;">10</td>
<td style="text-align: right;">10</td>
<td style="text-align: right;">10</td>
<td style="text-align: right;">60</td>
</tr>
</tbody>
</table>
<p>没有把集中方案的起始60件与分散方案的起始100件比较，也没有给某个方案免费加急运输。初始货值是共同常数，成本表不重复加入；剩余库存保留，不计废弃，没有额外终值奖励。期末在途仍计库存和持有成本，不允许最后一天“发货就从成本中消失”。</p>
<h2 id="需求独立与正相关究竟改变什么">2.
需求独立与正相关，究竟改变什么</h2>
<p>每个前置仓有两种完整6日需求路径：</p>
<ul>
<li>低需求L=[2,4,2,4,2,4]，合计18件。</li>
<li>高需求H=[6,8,6,8,6,8]，合计42件。</li>
</ul>
<p>每个前置仓本身都是50%遇L、50%遇H。改变的是两个仓之间的共同情景：</p>
<table>
<thead>
<tr class="header">
<th>依赖关系</th>
<th>F1路径</th>
<th>F2路径</th>
<th style="text-align: right;">概率</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>相互独立的路径选择</td>
<td>L</td>
<td>L</td>
<td style="text-align: right;">0.25</td>
</tr>
<tr class="even">
<td>相互独立的路径选择</td>
<td>L</td>
<td>H</td>
<td style="text-align: right;">0.25</td>
</tr>
<tr class="odd">
<td>相互独立的路径选择</td>
<td>H</td>
<td>L</td>
<td style="text-align: right;">0.25</td>
</tr>
<tr class="even">
<td>相互独立的路径选择</td>
<td>H</td>
<td>H</td>
<td style="text-align: right;">0.25</td>
</tr>
<tr class="odd">
<td>完全正相关的路径选择</td>
<td>L</td>
<td>L</td>
<td style="text-align: right;">0.50</td>
</tr>
<tr class="even">
<td>完全正相关的路径选择</td>
<td>H</td>
<td>H</td>
<td style="text-align: right;">0.50</td>
</tr>
</tbody>
</table>
<p>这里“独立”指两个地区的高／低路径选择独立，不是说同一个地区每天需求都相互独立。两组期望总需求都等于60件，但缺货分布可不同。</p>
<p>独立组的总需求D取36、60、84，概率分别0.25、0.50、0.25。平均值为36×0.25+60×0.5+84×0.25=60。方差是对“与平均值之差的平方”求平均：(36−60)²×0.25+0²×0.5+(84−60)²×0.25=288。正相关组方差=(36−60)²×0.5+(84−60)²×0.5=576。这里平方是先算差，再把差乘以自己，不是再把概率平方。</p>
<p>这说明相关性改变总需求波动，却没有证明总仓一定更好：货若来不及到门店，风险池化优势未必抵得过交期。</p>
<h2 id="补货启发式与一条节点守恒式">3. 补货启发式与一条节点守恒式</h2>
<p>R1/R2/F1/F2的目标库存位置都设10件。晚上先处理R→F，再处理CDC→R。节点库存位置=现在可用库存＋已发往该节点的在途；不把消费者未满足需求计为欠交。</p>
<p>对一条运输边：</p>
<ul>
<li>T：目的地目标库存位置，本例10件。</li>
<li>I：目的地当前库存，件。</li>
<li>P：已发往目的地但未到的在途，件。</li>
<li>H：起点仓当前可发库存，件。</li>
<li>补货请求R=max(0,T−I−P)。</li>
<li>真正发出Q=min(H,R)。</li>
</ul>
<p>必须扣在途P；否则一批10件已经在路上，每天又重复要求10件，容易越补越多。</p>
<p>节点日账：<code>期初库存＋今日到货−今日销售−今日发出=期末库存</code>。</p>
<p>全系统日账：<code>60=五节点期末库存之和＋全部在途＋累计已售</code>。未满足需求没有消耗实物，不应当减库存。</p>
<p><strong>集中配置第一天，低低情景手算</strong>：</p>
<ol type="1">
<li>F1/F2无货，各想买2件，都买不到。丢失4件，罚成本4×5=20元。</li>
<li>R1/R2也无货，不能给F仓发货。</li>
<li>CDC各给R1/R2发10件，总仓从60变40，产生20件在途。</li>
<li>总库存核对：仓内40＋在途20＋已售0=60。</li>
<li>运输费20件×0.2元／件／边=4元。</li>
<li>日末持有费(40+20)×0.1=6元。</li>
</ol>
<p>第二天区域仓收到10件，晚上才能发给F仓；第三天F仓才可销售。因此集中配置前两天销售均为0，不存在“总仓有货，所以门店马上有货”。</p>
<h2 id="成本函数逐项读">4. 成本函数逐项读</h2>
<p>单情景总成本C=持有成本＋缺货成本＋运输成本。</p>
<ul>
<li>持有成本=Σ每天(五仓存量＋在途)×0.1元／件／日。</li>
<li>缺货成本=累计未满足件数×5元／件。它是人为指定的机会损失罚成本，不是已验证真实赔偿金额。</li>
<li>运输成本=每条边累计发货件数×0.2元／件／边。一件货经过两条边会计两次运输，不是重复算错。</li>
<li>期望成本E[C]=Σ情景概率×该情景成本。这里E表示按概率加权平均。</li>
</ul>
<p>例如混合配置在独立情景中的期望持有费16.85、期望运输费11.80、期望缺货10件×5=50，合计78.65元。</p>
<h2 id="实际程序结果服务高不保证总成本低">5.
实际程序结果：服务高不保证总成本低</h2>
<table>
<colgroup>
<col style="width: 13%" />
<col style="width: 13%" />
<col style="width: 18%" />
<col style="width: 18%" />
<col style="width: 18%" />
<col style="width: 18%" />
</colgroup>
<thead>
<tr class="header">
<th>情景关系</th>
<th>起始配置</th>
<th style="text-align: right;">期望满足量/件</th>
<th style="text-align: right;">期望丢失/件</th>
<th style="text-align: right;">期望成本/元</th>
<th style="text-align: right;">总量口径满足率</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>独立</td>
<td>集中</td>
<td style="text-align: right;">39.5</td>
<td style="text-align: right;">20.5</td>
<td style="text-align: right;">151.75</td>
<td style="text-align: right;">65.83%</td>
</tr>
<tr class="even">
<td>独立</td>
<td>分散</td>
<td style="text-align: right;">48</td>
<td style="text-align: right;">12</td>
<td style="text-align: right;">77.20</td>
<td style="text-align: right;">80.00%</td>
</tr>
<tr class="odd">
<td>独立</td>
<td>混合</td>
<td style="text-align: right;">50</td>
<td style="text-align: right;">10</td>
<td style="text-align: right;">78.65</td>
<td style="text-align: right;">83.33%</td>
</tr>
<tr class="even">
<td>正相关</td>
<td>集中</td>
<td style="text-align: right;">39</td>
<td style="text-align: right;">21</td>
<td style="text-align: right;">153.90</td>
<td style="text-align: right;">65.00%</td>
</tr>
<tr class="odd">
<td>正相关</td>
<td>分散</td>
<td style="text-align: right;">48</td>
<td style="text-align: right;">12</td>
<td style="text-align: right;">77.20</td>
<td style="text-align: right;">80.00%</td>
</tr>
<tr class="even">
<td>正相关</td>
<td>混合</td>
<td style="text-align: right;">48</td>
<td style="text-align: right;">12</td>
<td style="text-align: right;">88.90</td>
<td style="text-align: right;">80.00%</td>
</tr>
</tbody>
</table>
<p>满足率按“期望满足件数÷期望需求件数”计算，例如50÷60=83.33%，不是对四个情景的比率做不加权平均。不同聚合口径可以得到不同数。</p>
<p>独立时，混合比纯分散多满足2件，但运输费使总成本高1.45元。服务目标优先与总成本目标优先会给不同选择，必须先定业务目标。</p>
<h2 id="种配置穷举是什么不是什么">6. 210种配置穷举是什么，不是什么</h2>
<p>让五个节点起始库存只能取0、10、20……60，合计60。程序枚举所有满足条件的210种配置，对每种运行同一个固定补货规则及相同情景。</p>
<p>在这210种配置中，两种依赖情景下成本最低的都是[0,0,0,30,30]，期望成本77.20元。它是<strong>该离散配置集合、该6天需求情景、该贪心补货政策和该成本设定下的精确最小值</strong>。</p>
<p>这不是MEIO全局最优证明。原因是：没有搜索每一天所有调拨动作，没有连续库存量，没有更多服务约束、交期分布、供应补入或终值假设。固定政策先分配R1再R2，稀缺货的顺序本身也可能影响结果，应当披露。不能把层级预测的加总一致性当成库存优化。</p>
<p>练习：只把每边运输费从0.2改成0，其余不变。混合成本变16.85+50=66.85元，分散仍77.20元，三候选排序就变了。这比背诵“集中总是好”更有用。</p>
<p>输入network.json；程序network、simulate_network；network_ledger.csv共有540行=3种固定配置×(4+2)种情景×6天×5节点。所有行均检查节点守恒和全局在途守恒；210配置也实际逐一计算，不是只打印210这个数字。</p>
