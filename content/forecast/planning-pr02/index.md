{
  "title": "两层BOM与多期APS：先看物料在哪天可用",
  "description": "两层BOM与多期APS：先看物料在哪天可用：本章提供6个可以离线运行的合成实验。其中生产实验又分央厨与制造两个小案例。它们补的是“怎样把预测变成需求、供应、财务与库存账”，不是企业实施方案。所有日期、价格、概率、产能与业务记录均为教学设定，没有客户真实资料。",
  "type": "forecast",
  "unit": "planning-pr02",
  "weight": 71,
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
id="pr02两层bom与多期aps先看物料在哪天可用">PR02｜两层BOM与多期APS：先看物料在哪天可用</h2>
<h2 id="两层是什么意思">1. 两层是什么意思</h2>
<p>BOM是物料清单。这里的“两层”指成品先消耗半成品，半成品再消耗原料，而不是把同一损耗乘两遍。</p>
<p>央厨链：A／B菜品 → 酱料半成品 → 番茄与香料。</p>
<p>制造链：A／B成品 → 核心模组 →
芯片与树脂；另有每台一只外壳。两种成品共享芯片，不能各自拿同一份芯片计算一遍可产数量后再相加。</p>
<p>MRP主要回答物料何时需要多少；本课APS小排程还会检查半成品产能和成品产能。它采用固定优先级启发式，不是通用生产优化器。</p>
<h2 id="央厨由份数走到kg">2. 央厨：由份数走到kg</h2>
<p>data/production.json的kitchen部分给出：</p>
<ul>
<li>A每份用0.2kg成品酱料，B每份用0.3kg。</li>
<li>每1kg合格酱料消耗1.25kg番茄和0.02kg香料。本课番茄系数1.25已包含80%出成率，即1÷0.8=1.25；不能再除0.8。</li>
<li>期初酱料2kg、番茄80kg、香料5kg。</li>
<li>第1周12月3日生产、4日配送；第2周10日生产、11日配送；第3周17日生产、18日配送。</li>
<li>番茄15kg在12月9日到货，25kg在12月18日到货。后者赶不上17日生产，即使能赶上18日配送，也不能拿它倒填生产。</li>
<li>本例酱料允许跨周留存，假定已验证覆盖整个实验期的货架期与适当储存。本课不模拟微生物风险和温控，不是食品安全放行指南。</li>
</ul>
<table>
<thead>
<tr class="header">
<th>周</th>
<th style="text-align: right;">A需求/份</th>
<th style="text-align: right;">B需求/份</th>
<th style="text-align: right;">酱料产能/kg</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>1</td>
<td style="text-align: right;">50</td>
<td style="text-align: right;">40</td>
<td style="text-align: right;">24</td>
</tr>
<tr class="even">
<td>2</td>
<td style="text-align: right;">60</td>
<td style="text-align: right;">40</td>
<td style="text-align: right;">20</td>
</tr>
<tr class="odd">
<td>3</td>
<td style="text-align: right;">70</td>
<td style="text-align: right;">40</td>
<td style="text-align: right;">28</td>
</tr>
</tbody>
</table>
<h2 id="央厨逐步演算">3. 央厨逐步演算</h2>
<p>设q_A、q_B为需求份数；b_A=0.2、b_B=0.3，单位kg／份。酱料毛需求G=q_A×b_A+q_B×b_B。“毛”在这里是未扣库存的需求，不是又一次含损耗。</p>
<p>第一周：</p>
<ol type="1">
<li>酱料需求G=50×0.2+40×0.3=10+12=22kg。</li>
<li>有2kg可用酱料，只需新做22−2=20kg。</li>
<li>酱料产能24kg，番茄支持80÷1.25=64kg酱料，香料支持5÷0.02=250kg，因此可生产min(20,24,64,250)=20kg。</li>
<li>新耗番茄20×1.25=25kg；番茄结存80−25=55kg。香料新耗20×0.02=0.4kg，结存4.6kg。</li>
<li>可用酱料2+20=22kg，足够A50份、B40份，期末酱料0。</li>
</ol>
<p>第二周：</p>
<ol type="1">
<li>番茄55+15=70kg；15kg到货日期早于10日生产，可以使用。</li>
<li>酱料需求60×0.2+40×0.3=24kg，产能只有20kg。</li>
<li>先给A60份，用12kg；还剩8kg。</li>
<li>B能做floor(8÷0.3)=26份，使用7.8kg，余酱0.2kg。</li>
<li>B缺40−26=14份。本例餐饮未满足需求视为流失，不在下一周自动补做旧菜。</li>
</ol>
<p>第三周：</p>
<ul>
<li>需求70×0.2+40×0.3=26kg；期初有0.2kg，所以新做25.8kg。</li>
<li>番茄生产前只有45kg，足够25.8×1.25=32.25kg用量，末尾12.75kg。</li>
<li>18日才到的25kg被列为本次生产窗口未使用到货，不是消失，也不能提前扣。</li>
</ul>
<p>每周盘存是某一时点的“存量”。把周一库存和周二库存相加，不会变成一周需要购买的量。只有每天消耗、到货等“流量”才可按期相加。已消耗的2kg旧酱料无需再次展开成番茄采购需求，因为原料已经在以前生产时投入。</p>
<h2 id="制造3周到货与共享芯片">4. 制造：3周到货与共享芯片</h2>
<p>期初10颗芯片中有2颗已为外部订单保留，当前可用仅8颗；另有2个现成模组、20kg树脂、20只外壳。每个模组用1颗芯片＋0.5kg树脂。每台A用1个模组，每台B用2个模组，二者各用1只外壳。</p>
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
<th>周</th>
<th style="text-align: right;">新A需求/台</th>
<th style="text-align: right;">新B需求/台</th>
<th style="text-align: right;">本周初芯片到货/颗</th>
<th style="text-align: right;">模组产能/个</th>
<th style="text-align: right;">成品产能/台</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>1</td>
<td style="text-align: right;">4</td>
<td style="text-align: right;">2</td>
<td style="text-align: right;">0</td>
<td style="text-align: right;">8</td>
<td style="text-align: right;">6</td>
</tr>
<tr class="even">
<td>2</td>
<td style="text-align: right;">4</td>
<td style="text-align: right;">3</td>
<td style="text-align: right;">3</td>
<td style="text-align: right;">8</td>
<td style="text-align: right;">6</td>
</tr>
<tr class="odd">
<td>3</td>
<td style="text-align: right;">2</td>
<td style="text-align: right;">2</td>
<td style="text-align: right;">5</td>
<td style="text-align: right;">8</td>
<td style="text-align: right;">6</td>
</tr>
</tbody>
</table>
<p>本课把表中到货定义为周初已经可用，且先做A，再做B；制造欠交会滚到下一周。树脂、外壳没有额外到货。芯片保留量2颗不属于本实验可消耗资源。</p>
<p>第一周：可用芯片8、已有模组2。</p>
<ul>
<li>A4台共需4模组，先用旧2个，再造2个，耗芯片2颗，剩芯片6颗。</li>
<li>B2台共需4模组，新造4个，耗芯片4颗，剩芯片2颗。</li>
<li>一共造6个新模组，没超过模组产能8；完成6台，没超过成品产能6；外壳剩20−6=14只。</li>
</ul>
<p>第二周：芯片2+3=5颗。</p>
<ul>
<li>A4台需要4个模组，造4个后余芯片1颗。</li>
<li>B每台需2个模组，只有1颗芯片不能拼成一台B，所以B产0台、欠交3台。</li>
<li>不能把第三周的5颗提前拿来用；也不能说“A能做4台，B单独能做2台，因此合计6台”，因为那样芯片被重复分配。</li>
</ul>
<p>第三周：芯片1+5=6颗。</p>
<ul>
<li>先做A2台，用2颗；剩4颗支持B2台。</li>
<li>B待交是旧3+新2=5台，只完成2，最后仍欠3台。</li>
</ul>
<p>全部新需求为A(4+4+2)=10台、B(2+3+2)=7台，共17台；实际完成14台。原需求17没有被改写成14。</p>
<h2 id="齐套率必须说清楚分母">5. 齐套率必须说清楚分母</h2>
<p>第二周有两条待办订单行：A4台、B3台。在A优先分配后，A行完整齐套，B行没有完整一台：</p>
<ul>
<li>订单行齐套率=完整齐套的订单行数÷待办订单行数=1÷2=50%。</li>
<li>计划台数可齐套率=可齐套台数÷计划台数=4÷7≈57.14%。</li>
</ul>
<p>一条大订单与一条小订单在第一种指标中各算一票，在第二种指标中按台数计数。物料齐套与产能可排是不同检验；本例第二周成品产能6台大于物料可做4台，所以这两个瓶颈没有冲突。换数据后不能直接拿实际产量代替物料齐套量。</p>
<p>outputs里的三周期单位完成率14÷17≈82.35%，分母是期间新增需求。另一个4÷6≈66.67%是<strong>周内待办SKU任务行完成率</strong>，分母只数本周待交量大于0的活动行。此例3周各有A/B两行，因此共6行；零任务行不算，完全无任务时返回null。欠交会在后周再次出现，所以它不是去重后的客户订单行齐套率。不要把三种数互换标签。</p>
<h2 id="非瓶颈采购也要重算但不能偷偷删掉欠交">6.
非瓶颈采购也要重算，但不能偷偷删掉欠交</h2>
<p>实际样例初始外壳20只，本来就足够17台需求，因此没有需要发出的新增外壳采购单。</p>
<p>另做明确的“如果只有10只外壳可用”的采购计划敏感性分析：</p>
<ul>
<li>未考虑芯片约束的17台计划会提出max(17−10,0)=7只净需求。</li>
<li>按当前可行14台计划，短期只需max(14−10,0)=4只。</li>
<li>差额3只可以建议暂缓释放，不等于取消客户仍欠的3台。它是另一情景下的建议，不是声称实际取消了采购单，也不是把外壳库存改成10后重新证明同一生产计划可行。</li>
</ul>
<p>本模型没有对“提前多生产是否更好”或“先B后A能否降低总延期成本”进行全局搜索。启发式优点是过程清楚、约束可核；缺点是可能错过更好的跨期安排。</p>
<h2 id="程序与验收">7. 程序与验收</h2>
<p>输入production.json；程序函数kitchen、manufacturing；结果kitchen.csv、manufacturing.csv。检查：酱料2+20=22；第二周B26份且余0.2kg；晚到25kg不入17日可用量；制造芯片不重复用；第二周A4/B0；第三周A2/B2；保留2颗芯片不动；最终B欠3台。</p>
<p>练习：把第二周芯片到货从3改为0。答案：第二周只有2颗可用，A也只能产2台，程序将重新计算后续欠交。先算当期，再看后期，不能为了保持旧答案而跳过守恒。</p>
