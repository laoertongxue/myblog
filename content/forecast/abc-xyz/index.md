{
  "title": "第一章 ABC-XYZ 不是九宫格背诵题",
  "description": "第一章 ABC-XYZ 不是九宫格背诵题：白皮书范围：第五部分阶段二。 本章回答：同样一百个商品，哪些值得优先管理，哪些需求较稳定？ABC 看选定口径下的价值贡献，XYZ 看需求波动；二者不能替代缺货代价、保质期和交期分析。",
  "type": "forecast",
  "unit": "abc-xyz",
  "weight": 20,
  "outputs": [
    "HTML"
  ]
}

<p class="check">本课使用模拟数据与明确假设。数学推导、枚举和数据核验不等于真实业务模型有效。配套包包含60天教学曲线及约束枚举，不是完整订单训练集。<br><a href="/forecast/planning-math-labs.zip" download>下载数学实验、完整教材与只读验证器</a></p><h2 id="第一章-abc-xyz-不是九宫格背诵题">第一章 ABC-XYZ
不是九宫格背诵题</h2>
<p><strong>白皮书范围：第五部分阶段二。</strong>
本章回答：同样一百个商品，哪些值得优先管理，哪些需求较稳定？ABC
看选定口径下的价值贡献，XYZ
看需求波动；二者不能替代缺货代价、保质期和交期分析。</p>
<p>方法出处：<a
href="https://help.sap.com/saphelp_SCM700_ehp02/helpdata/en/4d/33d92edb9e00d3e10000000a42189b/content.htm?no_cache=true">SAP
官方 ABC/XYZ
文档</a>说明按相对贡献与消费波动分类；下面的阈值和数字是本课程教学选择。</p>
<h3 id="abc-先确定用什么金额">1.1 ABC 先确定用什么金额</h3>
<p>这里采用年耗用金额：</p>
<p><strong>V_i = D_i × c_i；a_i = V_i / Σ_j V_j。</strong></p>
<ul>
<li>i、j：商品编号，没有单位。</li>
<li>D_i：商品 i 最近 12
个月耗用量，单位件/年，真实业务来自出库或消耗流水。</li>
<li>c_i：该商品用于分类的单位成本，单位元/件，真实业务来自成本主数据；需明确采用标准成本还是移动平均成本。</li>
<li>V_i：年耗用金额，单位元/年。</li>
<li>a_i：占所有纳入商品年耗用金额的比例，没有单位。</li>
<li>数学来源：金额等于数量乘单价，以及占比定义。</li>
</ul>
<p>不能把某些 SKU 的收入、另一些 SKU 的成本混在同一个 ABC
排序里。若目标是收入管理，可以统一改用收入，但必须重新命名口径。</p>
<table>
<colgroup>
<col style="width: 11%" />
<col style="width: 15%" />
<col style="width: 15%" />
<col style="width: 15%" />
<col style="width: 15%" />
<col style="width: 15%" />
<col style="width: 11%" />
</colgroup>
<thead>
<tr class="header">
<th>商品</th>
<th style="text-align: right;">年耗用量 件/年</th>
<th style="text-align: right;">成本 元/件</th>
<th style="text-align: right;">年耗用金额 元/年</th>
<th style="text-align: right;">金额占比</th>
<th style="text-align: right;">从大到小累计占比</th>
<th>ABC</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>A</td>
<td style="text-align: right;">1000</td>
<td style="text-align: right;">50</td>
<td style="text-align: right;">50000</td>
<td style="text-align: right;">50%</td>
<td style="text-align: right;">50%</td>
<td>A 类</td>
</tr>
<tr class="even">
<td>B</td>
<td style="text-align: right;">2000</td>
<td style="text-align: right;">15</td>
<td style="text-align: right;">30000</td>
<td style="text-align: right;">30%</td>
<td style="text-align: right;">80%</td>
<td>A 类</td>
</tr>
<tr class="odd">
<td>C</td>
<td style="text-align: right;">1000</td>
<td style="text-align: right;">10</td>
<td style="text-align: right;">10000</td>
<td style="text-align: right;">10%</td>
<td style="text-align: right;">90%</td>
<td>B 类</td>
</tr>
<tr class="even">
<td>D</td>
<td style="text-align: right;">1000</td>
<td style="text-align: right;">5</td>
<td style="text-align: right;">5000</td>
<td style="text-align: right;">5%</td>
<td style="text-align: right;">95%</td>
<td>B 类</td>
</tr>
<tr class="odd">
<td>E</td>
<td style="text-align: right;">600</td>
<td style="text-align: right;">5</td>
<td style="text-align: right;">3000</td>
<td style="text-align: right;">3%</td>
<td style="text-align: right;">98%</td>
<td>C 类</td>
</tr>
<tr class="even">
<td>F</td>
<td style="text-align: right;">1000</td>
<td style="text-align: right;">2</td>
<td style="text-align: right;">2000</td>
<td style="text-align: right;">2%</td>
<td style="text-align: right;">100%</td>
<td>C 类</td>
</tr>
</tbody>
</table>
<p>逐步计算： 1. A 的金额=1000×50=50000 元/年。 2.
总金额=50000+30000+10000+5000+3000+2000=100000 元/年。 3. A
的占比=50000/100000=50%；A、B 累计=80%。 4.
本例规则：排序后，累计金额首次达到或超过 80% 的那个商品也归
A；接下来直到首次达到或超过 95% 的商品归 B，其余归 C。若阈值落在一个大
SKU 中间，不拆开 SKU。</p>
<p>80% 与 95%
是教学阈值，不是统计定理。必须另行约定同金额商品的排序、退货负值、停产商品和新品的处理。年金额高不代表毛利高，也不代表可以无限备货。</p>
<h3 id="xyz-需要平均值和标准差">1.2 XYZ 需要平均值和标准差</h3>
<p>给每个商品取相同长度的 n 周需求 x_1,…,x_n：</p>
<p><strong>μ = (x_1+…+x_n)/n。</strong></p>
<p><strong>σ = √{[(x_1-μ)²+…+(x_n-μ)²]/n}。</strong></p>
<p><strong>CV = σ/μ，条件是 μ&gt;0。</strong></p>
<ul>
<li>x_t：第 t
周需求，单位件/周；真实业务来自经断货等问题处理后的需求序列。</li>
<li>n：周数，本例为 4。</li>
<li>μ、σ：平均需求和描述这段窗口波动的标准差，单位均为件/周。</li>
<li>CV：变异系数，没有单位，便于比较不同量级的商品。</li>
<li>数学来源：平均数、总体型描述标准差和变异系数的定义。</li>
</ul>
<p>本章是描述一个固定窗口，所以分母用 n。若在其他分析中用 n-1
估计总体方差，应明确换了口径；不能前后混用。4
周只是方便手算，生产分类需要足够长的可比窗口及稳定性检查。</p>
<table>
<thead>
<tr class="header">
<th>商品</th>
<th>四周模拟需求 件/周</th>
<th style="text-align: right;">μ</th>
<th style="text-align: right;">σ</th>
<th style="text-align: right;">CV</th>
<th>XYZ 教学分类</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>A</td>
<td>98,102,98,102</td>
<td style="text-align: right;">100</td>
<td style="text-align: right;">2</td>
<td style="text-align: right;">0.020</td>
<td>X</td>
</tr>
<tr class="even">
<td>B</td>
<td>0,0,0,200</td>
<td style="text-align: right;">50</td>
<td style="text-align: right;">86.603</td>
<td style="text-align: right;">1.732</td>
<td>Z</td>
</tr>
<tr class="odd">
<td>C</td>
<td>40,60,40,60</td>
<td style="text-align: right;">50</td>
<td style="text-align: right;">10</td>
<td style="text-align: right;">0.200</td>
<td>X</td>
</tr>
<tr class="even">
<td>D</td>
<td>20,40,20,40</td>
<td style="text-align: right;">30</td>
<td style="text-align: right;">10</td>
<td style="text-align: right;">0.333</td>
<td>Y</td>
</tr>
<tr class="odd">
<td>E</td>
<td>0,0,10,10</td>
<td style="text-align: right;">5</td>
<td style="text-align: right;">5</td>
<td style="text-align: right;">1.000</td>
<td>Z</td>
</tr>
<tr class="even">
<td>F</td>
<td>0,0,0,0</td>
<td style="text-align: right;">0</td>
<td style="text-align: right;">0</td>
<td style="text-align: right;">不定义</td>
<td>单列零需求状态</td>
</tr>
</tbody>
</table>
<p>本例 X：CV≤0.25；Y：0.25&lt;CV≤0.75；Z：CV&gt;0.75。F
过去一年有消耗而最近四周为零并不矛盾，但不能算
0/0，也不能自动判断它已经淘汰。</p>
<p>以 D 为例： 1. μ=(20+40+20+40)/4=30。 2. 四个离均差为
-10、10、-10、10，平方后都是 100。 3. σ=√(400/4)=10。 4.
CV=10/30≈0.333，因此是 Y；结合 ABC，它是 BY。</p>
<h3 id="如何把分类变成行动">1.3 如何把分类变成行动</h3>
<table>
<colgroup>
<col style="width: 33%" />
<col style="width: 33%" />
<col style="width: 33%" />
</colgroup>
<thead>
<tr class="header">
<th>组合</th>
<th>可先尝试的管理方式</th>
<th>还必须核查</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>AX</td>
<td>高频检查自动补货；人工看异常</td>
<td>交期、缺货成本、库存准确性</td>
</tr>
<tr class="even">
<td>AZ</td>
<td>加强情景和尾部风险分析；避免一次押满</td>
<td>间歇性、大促、预测不确定性</td>
</tr>
<tr class="odd">
<td>BX/BY</td>
<td>定期滚动补货；维护合理审核规则</td>
<td>箱规、补货周期、趋势变化</td>
</tr>
<tr class="even">
<td>CZ</td>
<td>小批量、按需或订单驱动的候选</td>
<td>是否关键备件、替代性、停机损失</td>
</tr>
</tbody>
</table>
<p>这不是强制策略表。一颗金额很低、却能让整条产线停机的零件，即使属于 C
类也可能需要高保障。</p>
<h3 id="误区与可检验小项目">1.4 误区与可检验小项目</h3>
<p>误区： -
周末固定卖得多是一种可预测的季节规律，不等于不可预测噪声。可以在去季节后评价波动，但要标清改用残差口径。例如用残差标准差除以原需求基线均值；不能除以通常接近
0 的残差均值。 - 断货造成的 0 不是没有需求。直接计入 CV
会同时扭曲均值和波动。 - 少量大额订单会把 CV
拉高；需要同时观察非零发生频率、订单集中度。 -
阈值一变就频繁换类会造成管理混乱。可以定期复核，并在边界使用稳定期规则。</p>
<p><strong>小项目</strong>：把 D 的四周需求换成
28、32、28、32，金额分类不变。算均值、标准差、CV
和新分类。再解释是否可以因此不留安全库存。</p>
<p><strong>答案</strong>：μ=30，σ=2，CV≈0.0667，D 从 BY 变为
BX。不能据此取消安全库存，因为交期、预测误差、需求相关性和服务要求仍可能存在。</p>
<hr />
