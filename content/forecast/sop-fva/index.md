{
  "title": "第二章 S&OP 与 FVA 先分清预测和承诺",
  "description": "第二章 S&OP 与 FVA 先分清预测和承诺：白皮书范围：第一部分第四层、第五部分阶段三、第六部分 FVA。 S&OP 是把需求、供给和资金约束放在同一张决策表上的产销协同，不是把销售愿望、预算、产能和预测揉成一个数字。",
  "type": "forecast",
  "unit": "sop-fva",
  "weight": 21,
  "outputs": [
    "HTML"
  ]
}

<p class="check">本课使用模拟数据与明确假设。数学推导、枚举和数据核验不等于真实业务模型有效。配套包包含60天教学曲线及约束枚举，不是完整订单训练集。<br><a href="/forecast/planning-math-labs.zip" download>下载数学实验、完整教材与只读验证器</a></p><h2 id="第二章-sop-与-fva-先分清预测和承诺">第二章 S&amp;OP 与 FVA
先分清预测和承诺</h2>
<p><strong>白皮书范围：第一部分第四层、第五部分阶段三、第六部分
FVA。</strong> S&amp;OP
是把需求、供给和资金约束放在同一张决策表上的产销协同，不是把销售愿望、预算、产能和预测揉成一个数字。</p>
<p>方法出处：<a
href="https://www.sas.com/content/dam/SAS/en_us/doc/whitepaper1/forecast-value-added-analysis-106186.pdf">Michael
Gilliland 撰写的 SAS FVA 原始白皮书</a>，见“What Is Forecast Value
Added?”与“Collecting the
Data”。它支持逐环节比较和保留预测版本；本章采用自设的 WMAPE 数例。</p>
<h3 id="四个数字可以不同">2.1 四个数字可以不同</h3>
<p>假设下月不受供给限制的需求预测为 1200 件，供给最多 1000
件，销售目标是 1400 件，当前承诺交付 950
件。这四个数字分别回答“预计有人要多少”“最多能做多少”“希望做到多少”“已答应多少”，不应互相覆盖。</p>
<p>最简单的单期供给模型：</p>
<p><strong>计划销售量 s = min(d, a)；未满足需求 u =
max(d-a,0)。</strong></p>
<ul>
<li>d：不受供给限制的需求预测，件/月。</li>
<li>a：在服务时间窗内真正可用的供给，件/月。</li>
<li>s：可实现的销售/交付计划，件/月。</li>
<li>u：该简化模型下未满足的需求，件/月。</li>
<li>来源：需求与可用供给的数量边界；假设无替代品、无跨期延期和无新增补救供应。</li>
</ul>
<p>代入 d=1200、a=1000，得到
s=1000、u=200。不能为了让供需“看起来一致”把预测改成
1000，再宣称预测变准。</p>
<p>一个可审计的 S&amp;OP
周期至少保留：数据截至时间、系统原始预测、人工调整预测、调整原因、约束后计划、审批结论和实际结果。可调整预测，不可覆盖原版本；供应受限造成的低销量也不能直接当作真实需求。</p>
<h3 id="fva-的分子到底在比较什么">2.2 FVA 的分子到底在比较什么</h3>
<p><strong>WMAPE(F) = Σ_t |A_t-F_t| / Σ_t A_t。</strong></p>
<p><strong>Bias(F) = Σ_t(F_t-A_t) / Σ_t A_t。</strong></p>
<p><strong>FVA(前→后) = WMAPE(前) - WMAPE(后)。</strong></p>
<ul>
<li>t：同一验证集中的商品-地点-目标期记录编号。</li>
<li>A_t：最终用于评价的实际需求，件；若只能得到受限销量，必须标明评价的是销量。</li>
<li>F_t：在固定预测起点冻结的预测，件。</li>
<li>WMAPE：绝对误差总量除以实际总量，没有单位。要求实际总量&gt;0，且这里需求非负。</li>
<li>Bias：带方向的总误差比例；本章正值代表高估。</li>
<li>FVA：差值；以百分比显示时应使用“百分点”。正值代表后一个环节在本指标上更好。</li>
<li>来源：白皮书第六部分的定义；为教学增加统一验证集与冻结版本要求。</li>
</ul>
<table>
<colgroup>
<col style="width: 9%" />
<col style="width: 12%" />
<col style="width: 12%" />
<col style="width: 12%" />
<col style="width: 12%" />
<col style="width: 12%" />
<col style="width: 12%" />
<col style="width: 12%" />
</colgroup>
<thead>
<tr class="header">
<th>周</th>
<th style="text-align: right;">实际 A</th>
<th style="text-align: right;">简单基线</th>
<th style="text-align: right;">系统预测</th>
<th style="text-align: right;">人工调整后</th>
<th style="text-align: right;">基线绝对误差</th>
<th style="text-align: right;">系统绝对误差</th>
<th style="text-align: right;">人工绝对误差</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>1</td>
<td style="text-align: right;">100</td>
<td style="text-align: right;">100</td>
<td style="text-align: right;">90</td>
<td style="text-align: right;">105</td>
<td style="text-align: right;">0</td>
<td style="text-align: right;">10</td>
<td style="text-align: right;">5</td>
</tr>
<tr class="even">
<td>2</td>
<td style="text-align: right;">120</td>
<td style="text-align: right;">100</td>
<td style="text-align: right;">130</td>
<td style="text-align: right;">125</td>
<td style="text-align: right;">20</td>
<td style="text-align: right;">10</td>
<td style="text-align: right;">5</td>
</tr>
<tr class="odd">
<td>3</td>
<td style="text-align: right;">80</td>
<td style="text-align: right;">100</td>
<td style="text-align: right;">85</td>
<td style="text-align: right;">100</td>
<td style="text-align: right;">20</td>
<td style="text-align: right;">5</td>
<td style="text-align: right;">20</td>
</tr>
<tr class="even">
<td>4</td>
<td style="text-align: right;">100</td>
<td style="text-align: right;">100</td>
<td style="text-align: right;">95</td>
<td style="text-align: right;">110</td>
<td style="text-align: right;">0</td>
<td style="text-align: right;">5</td>
<td style="text-align: right;">10</td>
</tr>
<tr class="odd">
<td>合计</td>
<td style="text-align: right;">400</td>
<td style="text-align: right;">400</td>
<td style="text-align: right;">400</td>
<td style="text-align: right;">440</td>
<td style="text-align: right;">40</td>
<td style="text-align: right;">30</td>
<td style="text-align: right;">40</td>
</tr>
</tbody>
</table>
<p>逐步计算： 1. 基线 WMAPE=40/400=10%。 2. 系统
WMAPE=30/400=7.5%。系统相对基线的 FVA=10%-7.5%=+2.5 个百分点。 3. 人工
WMAPE=40/400=10%。人工相对系统的 FVA=7.5%-10%=-2.5 个百分点。 4. 系统
Bias=(-10+10+5-5)/400=0%，但其 WMAPE 仍为 7.5%。正负误差抵消不代表准确。
5. 人工 Bias=(5+5+20+10)/400=10%。本例人工调整有整体高估。</p>
<p>不能把逐 SKU 的百分比误差简单平均后冒充这个
WMAPE，也不能让分母随比较对象改变。若当期实际总量为 0，WMAPE
不定义，应报告绝对误差等替代指标。</p>
<h3 id="怎么判断调整真的有价值">2.3 怎么判断调整真的有价值</h3>
<p>每个版本必须对应相同商品、相同目标期、相同预测提前期。提前一天的预测与提前一月的预测，拥有不同信息，不应直接归因于算法或某位计划员。</p>
<p>滚动验证的操作是：在起点 o 冻结一份未来 h 周预测；等 h
周后结果完整；记录误差；将起点向后移动，再重复。o 是预测起点日期，h
是预测跨度，均来自版本表。还应分促销、常规、缺货和新品等场景看结果。</p>
<p>FVA
是所选误差指标的增值，不是货币利润。缺货罚损不对称时，预测绝对误差略增的调整，仍可能改善决策成本；必须同时评价缺货、报损和持有成本，并清楚区分两类结论。只有足够多的可比时间段、稳定的分组证据和成本检查，才能支持权限调整；四周负
FVA 不能自动成为剥夺权限的依据。</p>
<h3 id="小项目与答案">2.4 小项目与答案</h3>
<p><strong>任务</strong>：只把系统的第 3 周预测从 85 改为
80，其余不变。求新 WMAPE、该次修改 FVA 和
Bias。问：可以声称“这次修改赚了 5 元”吗？</p>
<p><strong>答案</strong>：绝对误差=10+10+0+5=25
件，WMAPE=25/400=6.25%；FVA=7.5%-6.25%=+1.25
个百分点；Bias=(-10+10+0-5)/400=-1.25%。不能声称赚了 5 元：改善的是 5
件预测绝对误差，还没有价格、成本及决策后果的证据。</p>
<hr />
