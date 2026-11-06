{
  "title": "双供应商分单：便宜、快和已经承诺的订单一起算",
  "description": "双供应商分单：便宜、快和已经承诺的订单一起算：本章提供6个可以离线运行的合成实验。其中生产实验又分央厨与制造两个小案例。它们补的是“怎样把预测变成需求、供应、财务与库存账”，不是企业实施方案。所有日期、价格、概率、产能与业务记录均为教学设定，没有客户真实资料。",
  "type": "forecast",
  "unit": "planning-pr04",
  "weight": 73,
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
id="pr04双供应商分单便宜快和已经承诺的订单一起算">PR04｜双供应商分单：便宜、快和已经承诺的订单一起算</h2>
<h2 id="输入和决策变量">1. 输入和决策变量</h2>
<p>在第6日需要100件。已经向A订了20件，不能假装这20件不存在或任意转给B。现在追加80件，两家都按10件一批订，最小起订量MOQ仅对本次新增订单为正时生效。</p>
<table>
<thead>
<tr class="header">
<th>项目</th>
<th style="text-align: right;">A供应商</th>
<th style="text-align: right;">B供应商</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>新增采购单价/元</td>
<td style="text-align: right;">8</td>
<td style="text-align: right;">11</td>
</tr>
<tr class="even">
<td>本次下单固定费/元</td>
<td style="text-align: right;">30</td>
<td style="text-align: right;">50</td>
</tr>
<tr class="odd">
<td>本次MOQ/件</td>
<td style="text-align: right;">20</td>
<td style="text-align: right;">10</td>
</tr>
<tr class="even">
<td>总供货容量/件</td>
<td style="text-align: right;">100，含已承诺20</td>
<td style="text-align: right;">60</td>
</tr>
<tr class="odd">
<td>正常情景到达日</td>
<td style="text-align: right;">第4日</td>
<td style="text-align: right;">第3日</td>
</tr>
<tr class="even">
<td>A延期情景到达日</td>
<td style="text-align: right;">第7日</td>
<td style="text-align: right;">第5日</td>
</tr>
</tbody>
</table>
<p>正常情景概率0.7，A延期情景概率0.3；两家的到货日通过同一行联合情景给出。不要分别取两家的P90再相加，然后称“联合P90”。</p>
<p>本课缺货罚成本为20元／件；迟到货并没有消失，只是不满足第6日的承诺。模型不计第6日以后的持有／处置成本，也没有允许变更原已承诺20件的下单日期。</p>
<p>设q_A为本次加给A的件数，q_B为加给B的件数：</p>
<ul>
<li>q_A+q_B=80。</li>
<li>q_A、q_B必须是10的整数倍。</li>
<li>q_A=0或q_A≥20；q_B=0或q_B≥10。</li>
<li>q_A+20≤100；q_B≤60。</li>
</ul>
<p>“整数倍”不是“取整后就一定合法”。例如A10/B70同时违反A的MOQ和B的容量，应直接排除。</p>
<h2 id="手算a20b60">2. 手算A20/B60</h2>
<p>采购与固定费：20×8+60×11+30+50=160+660+80=900元。</p>
<p>正常情景：已订A20＋新订A20＋新订B60=100件按时到，缺0。</p>
<p>延期情景：A两批共40件均第7日到，截止第6日只有B60件，因此缺40件。不能只计算新增A20的迟交，而忘记旧A20。</p>
<p>期望缺货=0.7×0+0.3×40=12件。</p>
<p>期望罚成本=12×20=240元。</p>
<p>总期望相关成本=900+240=1140元。已承诺20件的采购款是所有候选相同的既定成本，本表不重复加；若要计算整个订单完整财务成本，应把它统一加回所有候选。</p>
<h2 id="七种合法候选全部比较">3. 七种合法候选全部比较</h2>
<table>
<thead>
<tr class="header">
<th style="text-align: right;">新增A</th>
<th style="text-align: right;">新增B</th>
<th style="text-align: right;">采购＋固定费/元</th>
<th style="text-align: right;">期望缺货/件</th>
<th style="text-align: right;">总期望成本/元</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td style="text-align: right;">20</td>
<td style="text-align: right;">60</td>
<td style="text-align: right;">900</td>
<td style="text-align: right;">12</td>
<td style="text-align: right;">1140</td>
</tr>
<tr class="even">
<td style="text-align: right;">30</td>
<td style="text-align: right;">50</td>
<td style="text-align: right;">870</td>
<td style="text-align: right;">15</td>
<td style="text-align: right;">1170</td>
</tr>
<tr class="odd">
<td style="text-align: right;">40</td>
<td style="text-align: right;">40</td>
<td style="text-align: right;">840</td>
<td style="text-align: right;">18</td>
<td style="text-align: right;">1200</td>
</tr>
<tr class="even">
<td style="text-align: right;">50</td>
<td style="text-align: right;">30</td>
<td style="text-align: right;">810</td>
<td style="text-align: right;">21</td>
<td style="text-align: right;">1230</td>
</tr>
<tr class="odd">
<td style="text-align: right;">60</td>
<td style="text-align: right;">20</td>
<td style="text-align: right;">780</td>
<td style="text-align: right;">24</td>
<td style="text-align: right;">1260</td>
</tr>
<tr class="even">
<td style="text-align: right;">70</td>
<td style="text-align: right;">10</td>
<td style="text-align: right;">750</td>
<td style="text-align: right;">27</td>
<td style="text-align: right;">1290</td>
</tr>
<tr class="odd">
<td style="text-align: right;">80</td>
<td style="text-align: right;">0</td>
<td style="text-align: right;">670</td>
<td style="text-align: right;">30</td>
<td style="text-align: right;">1270</td>
</tr>
</tbody>
</table>
<p>A80/B0只需670元采购及固定费，但期望迟交成本600元，总1270，反而比A20/B60高130元。注意70/10切换到80/0时，不再产生B固定费50元，所以表不是严格线性递增。</p>
<p>本例最佳分单20/60仍只有70%的概率全量按时到。最低期望成本不代表100%准时，更不代表风险已解决。若业务要求95%以上全量准时，这7个候选全不合格，应报告“当前供应与已承诺订单下无满足该条件的方案”，再讨论提前订货或新供应商，而不是把70%写成95%。</p>
<h2 id="最优性和参数敏感性">4. 最优性和参数敏感性</h2>
<p>因为所有合法候选都被列出、逐一计算，1140是这个有限模型的最小值；不是调用商业求解器得到的通用全球最优。若允许提前下单、拆成多个到货批次或改变供应商集合，候选集就变了，必须重算。</p>
<p>练习：把缺货罚成本20改成0。最佳变A80/B0，成本670。程序真的读取输入并改答案，不是硬编码“永远20/60”。这不等于建议业务忽略缺货，而是说明目标函数决定选择。</p>
<p>输入sourcing.json；结果sourcing_candidates.csv；详细情景见results.json。验收MOQ、批量、两家容量、已承诺量、情景概率之和为1；没有合法解时抛出明确错误，不输出假的最优分单。</p>
