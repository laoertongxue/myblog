{
  "title": "12个月S&OP与CPFR：先协调口径，再看供应缺口",
  "description": "12个月S&OP与CPFR：先协调口径，再看供应缺口：本章提供6个可以离线运行的合成实验。其中生产实验又分央厨与制造两个小案例。它们补的是“怎样把预测变成需求、供应、财务与库存账”，不是企业实施方案。所有日期、价格、概率、产能与业务记录均为教学设定，没有客户真实资料。",
  "type": "forecast",
  "unit": "planning-pr01",
  "weight": 70,
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
id="pr0112个月sop与cpfr先协调口径再看供应缺口">PR01｜12个月S&amp;OP与CPFR：先协调口径，再看供应缺口</h2>
<h2 id="业务问题与数据契约">1. 业务问题与数据契约</h2>
<p>一家快消企业准备从2026年12月滚动计划到2027年11月。销售说的是“顾客可能想买多少”，生产说的是“我们最多能做多少”，财务说的是“希望实现多少收入”。这三件事必须并列，不能取较小值之后把它命名为需求预测。</p>
<p>S&amp;OP是销售与运营计划；CPFR是与客户／供应商协同进行计划、预测与补货。这里用合成的单商品客户协同练习其数据和决策流程，不假装双方真的开过会。</p>
<p>输入data/sop.json包含：</p>
<ul>
<li><code>version</code>：计划版本号；<code>cutoff</code>：本版能采用的信息截止日。</li>
<li><code>system_demand</code>：系统工作预测，单位件；<code>customer_demand</code>：客户共享预测，单位同样是件。</li>
<li><code>capacity</code>：本月最大可生产量，单位件／月；本课假定当月生产可供当月交付，不模拟月内天数。</li>
<li><code>finance_target_revenue</code>：财务希望实现的收入，单位元；<code>unit_price=20</code>元／件。</li>
<li><code>cpfr</code>：记录编号、对应月份、可得日期、批准后的需求值、原因与责任角色。</li>
<li>欠交不是丢单。本例未交需求全部进入下一月；现实若会取消，需另建取消流程。</li>
</ul>
<p>工作责任卡：需求计划员维护预测；客户协同员核对客户差异及证据；供应计划员填写产能与可供量；财务核对收入和生产支出；最终审批人决定是否接受欠交、加班、外采等候选方案。程序只出草案，不代替审批。</p>
<h2 id="个月输入不从短数据硬猜年度季节">2.
12个月输入，不从短数据硬猜年度季节</h2>
<table>
<thead>
<tr class="header">
<th>月份</th>
<th style="text-align: right;">系统需求/件</th>
<th style="text-align: right;">客户需求/件</th>
<th style="text-align: right;">产能/件</th>
<th style="text-align: right;">财务目标/元</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>2026-12</td>
<td style="text-align: right;">100</td>
<td style="text-align: right;">100</td>
<td style="text-align: right;">115</td>
<td style="text-align: right;">2200</td>
</tr>
<tr class="even">
<td>2027-01</td>
<td style="text-align: right;">110</td>
<td style="text-align: right;">130</td>
<td style="text-align: right;">115</td>
<td style="text-align: right;">2400</td>
</tr>
<tr class="odd">
<td>2027-02</td>
<td style="text-align: right;">120</td>
<td style="text-align: right;">120</td>
<td style="text-align: right;">125</td>
<td style="text-align: right;">2600</td>
</tr>
<tr class="even">
<td>2027-03</td>
<td style="text-align: right;">125</td>
<td style="text-align: right;">115</td>
<td style="text-align: right;">120</td>
<td style="text-align: right;">2700</td>
</tr>
<tr class="odd">
<td>2027-04</td>
<td style="text-align: right;">130</td>
<td style="text-align: right;">160</td>
<td style="text-align: right;">130</td>
<td style="text-align: right;">2800</td>
</tr>
<tr class="even">
<td>2027-05</td>
<td style="text-align: right;">140</td>
<td style="text-align: right;">140</td>
<td style="text-align: right;">130</td>
<td style="text-align: right;">3000</td>
</tr>
<tr class="odd">
<td>2027-06</td>
<td style="text-align: right;">145</td>
<td style="text-align: right;">145</td>
<td style="text-align: right;">140</td>
<td style="text-align: right;">3100</td>
</tr>
<tr class="even">
<td>2027-07</td>
<td style="text-align: right;">135</td>
<td style="text-align: right;">115</td>
<td style="text-align: right;">140</td>
<td style="text-align: right;">2900</td>
</tr>
<tr class="odd">
<td>2027-08</td>
<td style="text-align: right;">130</td>
<td style="text-align: right;">130</td>
<td style="text-align: right;">125</td>
<td style="text-align: right;">2800</td>
</tr>
<tr class="even">
<td>2027-09</td>
<td style="text-align: right;">125</td>
<td style="text-align: right;">135</td>
<td style="text-align: right;">125</td>
<td style="text-align: right;">2700</td>
</tr>
<tr class="odd">
<td>2027-10</td>
<td style="text-align: right;">120</td>
<td style="text-align: right;">120</td>
<td style="text-align: right;">130</td>
<td style="text-align: right;">2600</td>
</tr>
<tr class="even">
<td>2027-11</td>
<td style="text-align: right;">150</td>
<td style="text-align: right;">180</td>
<td style="text-align: right;">140</td>
<td style="text-align: right;">3200</td>
</tr>
</tbody>
</table>
<p>这是人为给出的12月情景，不是从180天数据识别出的年度季节性。需要真实年度季节结论时，应有跨年数据、可解释事件和样本外验证。</p>
<h2 id="协商记录不能穿越截止日">3. 协商记录不能穿越截止日</h2>
<p>本版名为SOP-2026-11-v1，截止2026-11-30。差异异常规则为：<code>|客户需求−系统需求| &gt; 10%×系统需求</code>。这里的绝对值符号<code>| |</code>表示不考虑正负，只看相差多少。</p>
<ul>
<li>2027-01：差异130−110=20件，20÷110≈18.18%，超阈值。11月28日批准新增铺货10件，因此本版工作需求为120，而非客户全部130。</li>
<li>2027-04：差异160−130=30件，30÷130≈23.08%。11月29日批准活动增量15件，因此取145。</li>
<li>2027-07：差异115−135=−20件，绝对差异20÷135≈14.81%。没有已批准协商记录，保留系统135为<strong>未解决异常的暂定需求</strong>，不是双方已达成共识。</li>
<li>2027-11：客户希望180；名为CPFR-LATE的记录在12月2日才可得，晚于截止。旧版只能暂用150并标异常，不能拿未来记录改写过去。</li>
</ul>
<p>输出<code>demand_status</code>区分已批准CPFR、普通系统工作计划、未解决异常暂定值。客户共享值永远保留，便于复查为什么没采纳。</p>
<h2 id="逐符号计算供应版">4. 逐符号计算供应版</h2>
<p>设：</p>
<ul>
<li>d_t：第t月的工作需求，件。</li>
<li>B_(t−1)：上月留下的欠交，件。</li>
<li>I_(t−1)：月初可用库存，件。</li>
<li>C_t：当月产能，件。</li>
<li>S：希望保留的期末库存，本例10件；它是本课策略参数，不是统计估计的安全库存。</li>
<li>P_t：计划生产量；F_t：计划交付量；I_t：月末库存；B_t：月末欠交，单位全是件。</li>
</ul>
<p>计算顺序：</p>
<ol type="1">
<li>待交量U_t=d_t+B_(t−1)。旧欠交仍需要交。</li>
<li>想生产的数量=max(0,U_t+S−I_(t−1))。</li>
<li>真实可排生产P_t=min(C_t,想生产的数量)。</li>
<li>可用总量A_t=I_(t−1)+P_t。</li>
<li>交付F_t=min(A_t,U_t)。</li>
<li>期末库存I_t=A_t−F_t；期末欠交B_t=U_t−F_t。</li>
</ol>
<p><strong>12月手算</strong>：d=100，B初=0，I初=20，C=115，S=10。</p>
<ul>
<li>待交=100+0=100。</li>
<li>想生产=max(0,100+10−20)=90。</li>
<li>实际排产=min(115,90)=90。</li>
<li>可用=20+90=110；交付=min(110,100)=100。</li>
<li>月末库存110−100=10；欠交100−100=0。</li>
<li>可实现销售收入=100件×20元／件=2000元；财务目标仍是2200元，相差200元。</li>
</ul>
<p><strong>4月手算</strong>：上月库存5，工作需求145，旧欠交0，产能130。</p>
<ul>
<li>想生产145+10−5=150件，但产能只准130件。</li>
<li>可用5+130=135件，交付135件，欠交145−135=10件。</li>
<li>需求仍记145，不能改成135。否则缺口会从报表里“消失”。</li>
</ul>
<h2 id="全期输出与下一轮">5. 全期输出与下一轮</h2>
<table>
<thead>
<tr class="header">
<th>月份</th>
<th style="text-align: right;">工作需求</th>
<th style="text-align: right;">排产</th>
<th style="text-align: right;">交付</th>
<th style="text-align: right;">期末库存</th>
<th style="text-align: right;">期末欠交</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>2026-12</td>
<td style="text-align: right;">100</td>
<td style="text-align: right;">90</td>
<td style="text-align: right;">100</td>
<td style="text-align: right;">10</td>
<td style="text-align: right;">0</td>
</tr>
<tr class="even">
<td>2027-01</td>
<td style="text-align: right;">120</td>
<td style="text-align: right;">115</td>
<td style="text-align: right;">120</td>
<td style="text-align: right;">5</td>
<td style="text-align: right;">0</td>
</tr>
<tr class="odd">
<td>2027-02</td>
<td style="text-align: right;">120</td>
<td style="text-align: right;">125</td>
<td style="text-align: right;">120</td>
<td style="text-align: right;">10</td>
<td style="text-align: right;">0</td>
</tr>
<tr class="even">
<td>2027-03</td>
<td style="text-align: right;">125</td>
<td style="text-align: right;">120</td>
<td style="text-align: right;">125</td>
<td style="text-align: right;">5</td>
<td style="text-align: right;">0</td>
</tr>
<tr class="odd">
<td>2027-04</td>
<td style="text-align: right;">145</td>
<td style="text-align: right;">130</td>
<td style="text-align: right;">135</td>
<td style="text-align: right;">0</td>
<td style="text-align: right;">10</td>
</tr>
<tr class="even">
<td>2027-05</td>
<td style="text-align: right;">140</td>
<td style="text-align: right;">130</td>
<td style="text-align: right;">130</td>
<td style="text-align: right;">0</td>
<td style="text-align: right;">20</td>
</tr>
<tr class="odd">
<td>2027-06</td>
<td style="text-align: right;">145</td>
<td style="text-align: right;">140</td>
<td style="text-align: right;">140</td>
<td style="text-align: right;">0</td>
<td style="text-align: right;">25</td>
</tr>
<tr class="even">
<td>2027-07</td>
<td style="text-align: right;">135</td>
<td style="text-align: right;">140</td>
<td style="text-align: right;">140</td>
<td style="text-align: right;">0</td>
<td style="text-align: right;">20</td>
</tr>
<tr class="odd">
<td>2027-08</td>
<td style="text-align: right;">130</td>
<td style="text-align: right;">125</td>
<td style="text-align: right;">125</td>
<td style="text-align: right;">0</td>
<td style="text-align: right;">25</td>
</tr>
<tr class="even">
<td>2027-09</td>
<td style="text-align: right;">125</td>
<td style="text-align: right;">125</td>
<td style="text-align: right;">125</td>
<td style="text-align: right;">0</td>
<td style="text-align: right;">25</td>
</tr>
<tr class="odd">
<td>2027-10</td>
<td style="text-align: right;">120</td>
<td style="text-align: right;">130</td>
<td style="text-align: right;">130</td>
<td style="text-align: right;">0</td>
<td style="text-align: right;">15</td>
</tr>
<tr class="even">
<td>2027-11</td>
<td style="text-align: right;">150</td>
<td style="text-align: right;">140</td>
<td style="text-align: right;">140</td>
<td style="text-align: right;">0</td>
<td style="text-align: right;">25</td>
</tr>
</tbody>
</table>
<p>全年工作需求1555件，交付1530件，末期欠交25件。财务目标合计33000元，按20元／件相当于1650件；收入愿望不能自动创造产能。</p>
<p>下一版SOP-2026-12-v1在12月31日截止，窗口移动为2027年1月至12月。删除已过去的12月，增加未来2027年12月，并保留旧版文件；不覆盖旧预测。</p>
<p>12月实际是期初20＋实际生产94−实际交付104=期末10。下一版从实际10开始，不从旧版计划生产90倒推。1月新系统预测122，12月28日的批准协商值125进入新版。新版12月需求总计1600件、可交1580件、期末欠交20件。新旧窗口不同，不能仅凭1555变1600说预测改善。</p>
<h2 id="代码验收与练习">6. 代码、验收与练习</h2>
<p>核心代码在run.py的<code>plan_version</code>和<code>sop</code>；输入sop.json；输出sop_base.csv、sop_rolling.csv及results.json中的sop字段。</p>
<p>验收：每版12个不同月份；CPFR-LATE被拒；4月145件需求不被130件产能覆盖；各月满足“月初库存＋生产=交付＋月末库存”和“旧欠交＋新需求=交付＋新欠交”；新版起点等于实际库存。</p>
<p>练习：把12月产能改成50件，其余不动。答案：需求仍100，可供20+50=70，欠交30，不是需求减少30。它展示的是供应风险，不是预测误差。</p>
<p>限制：没有拟合年度需求，没有月内日历、冻结区、真实资金预算或自动审批；月度S&amp;OP与后面的日度网络实验是独立练习，不声称已经完成月周日自动分解系统。</p>
