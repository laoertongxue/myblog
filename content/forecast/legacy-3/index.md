{
  "title": "误差、偏差与公平回测",
  "description": "误差、偏差与公平回测：评估区间是第8至14天；每次预测步长都是1天。这不是站在第7天一次预测整整一周。两种任务能使用的信息不同，不能把成绩混为一谈。",
  "type": "forecast",
  "unit": "legacy-3",
  "weight": 4,
  "outputs": [
    "HTML"
  ]
}

<p class="check">本阶段可直接下载：<a href="/forecast/data-quality-backtest.zip" download>P01/P03输入、生成器、操作说明与参考答案</a>。先做题再看answers目录。</p><h2 id="第4章-回测让你知道方法究竟有没有用">第4章
回测让你知道方法究竟有没有用</h2>
<h3 id="回测就是回到过去作出当时能够作出的预测">4.1
回测就是回到过去作出当时能够作出的预测</h3>
<p>对14天样本，我们先做逐日滚动的次日预测：</p>
<ul>
<li>在第7天结束时，只看第1至7天，预测第8天。</li>
<li>第8天实际值到达后，在第8天结束时预测第9天。</li>
<li>一直重复到第14天。</li>
</ul>
<p>评估区间是第8至14天；每次预测步长都是1天。这不是站在第7天一次预测整整一周。两种任务能使用的信息不同，不能把成绩混为一谈。</p>
<h3 id="用同一张评分表比较">4.2 用同一张评分表比较</h3>
<table>
<thead>
<tr class="header">
<th>目标日</th>
<th style="text-align: right;">实际kg</th>
<th style="text-align: right;">昨日法kg</th>
<th style="text-align: right;">上周同日法kg</th>
<th style="text-align: right;">7日移动平均kg</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>8</td>
<td style="text-align: right;">22</td>
<td style="text-align: right;">28</td>
<td style="text-align: right;">20</td>
<td style="text-align: right;">25.43</td>
</tr>
<tr class="even">
<td>9</td>
<td style="text-align: right;">24</td>
<td style="text-align: right;">22</td>
<td style="text-align: right;">22</td>
<td style="text-align: right;">25.71</td>
</tr>
<tr class="odd">
<td>10</td>
<td style="text-align: right;">23</td>
<td style="text-align: right;">24</td>
<td style="text-align: right;">21</td>
<td style="text-align: right;">26.00</td>
</tr>
<tr class="even">
<td>11</td>
<td style="text-align: right;">25</td>
<td style="text-align: right;">23</td>
<td style="text-align: right;">23</td>
<td style="text-align: right;">26.29</td>
</tr>
<tr class="odd">
<td>12</td>
<td style="text-align: right;">32</td>
<td style="text-align: right;">25</td>
<td style="text-align: right;">30</td>
<td style="text-align: right;">26.57</td>
</tr>
<tr class="even">
<td>13</td>
<td style="text-align: right;">36</td>
<td style="text-align: right;">32</td>
<td style="text-align: right;">34</td>
<td style="text-align: right;">26.86</td>
</tr>
<tr class="odd">
<td>14</td>
<td style="text-align: right;">30</td>
<td style="text-align: right;">36</td>
<td style="text-align: right;">28</td>
<td style="text-align: right;">27.14</td>
</tr>
</tbody>
</table>
<p>表中预测显示两位小数，评分使用未四舍五入的数值。不要把展示精度当作模型精度。</p>
<p>昨日法的误差依次是−6、2、−1、2、7、4、−6kg。绝对误差合计28kg，实际总量为192kg。</p>
<p>上周同日法每天的误差都是2kg。绝对误差合计14kg，但这14kg全部来自低估，不存在高估与低估抵消。</p>
<h3 id="四个先学会就够用的指标">4.3 四个先学会就够用的指标</h3>
<p><strong>MAE 平均绝对误差。</strong>
计算每次偏差的绝对值，再取平均：</p>
<p>MAE=Σ|实际−预测|÷预测次数。</p>
<p>昨日法MAE=28÷7=4kg。可以读成：“在这7次次日预测里，每次平均偏差4kg。”它与目标单位一致，容易和业务讨论。</p>
<p><strong>RMSE 均方根误差。</strong> 先平方，求平均，最后开平方：</p>
<p>RMSE=√[Σ(实际−预测)²÷预测次数]。</p>
<p>昨日法平方误差合计146，因此RMSE=√(146÷7)≈4.57kg。它对少数大偏差更加敏感。如果一次严重短缺比多次小偏差更难接受，可以把它作为补充，但最终仍应检查真实成本。</p>
<p><strong>WAPE 加权绝对百分比误差。</strong>
本文在实际值非负的口径下采用：</p>
<p>WAPE=Σ|实际−预测|÷Σ实际。</p>
<p>昨日法WAPE=28÷192≈14.58%。上周同日法WAPE=14÷192≈7.29%。它不是“每次误差百分比的简单平均”，也不是“预测正确的概率”。不建议把1−WAPE直接包装成普遍意义的“预测准确率”。</p>
<p>如果一个评估分组的实际总量是0，WAPE未定义，不能随意报成0%。应单独报告绝对误差与零需求样本情况。若目标允许负值，例如净退货量，要重新约定分母和评价方式，不能机械沿用这一定义。</p>
<p><strong>Bias 平均有符号误差。</strong> 本文定义为：</p>
<p>Bias=Σ(实际−预测)÷预测次数。</p>
<p>大于0表示平均低估，小于0表示平均高估。不同系统可能用相反方向，所以报表必须写清定义。平均低估可能增加缺货风险，但是否真的缺货还取决于库存与补货策略。</p>
<p>为避免与后续专项的百分比偏差混淆，这里的量也称ME（mean
error，平均误差），单位kg，方向为实际减预测。另一个常用量“相对预测偏差率”定义为Σ(预测−实际)/Σ实际，单位为百分比，正值表示高估。两者名称、方向和单位都应同时标出，不能在同一图里只写Bias。</p>
<table>
<thead>
<tr class="header">
<th>方法</th>
<th style="text-align: right;">MAE kg</th>
<th style="text-align: right;">RMSE kg</th>
<th style="text-align: right;">WAPE</th>
<th style="text-align: right;">Bias kg</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>昨日法</td>
<td style="text-align: right;">4.00</td>
<td style="text-align: right;">4.57</td>
<td style="text-align: right;">14.58%</td>
<td style="text-align: right;">0.29</td>
</tr>
<tr class="even">
<td>7日移动平均</td>
<td style="text-align: right;">3.84</td>
<td style="text-align: right;">4.58</td>
<td style="text-align: right;">13.99%</td>
<td style="text-align: right;">1.14</td>
</tr>
<tr class="odd">
<td>上周同日法</td>
<td style="text-align: right;">2.00</td>
<td style="text-align: right;">2.00</td>
<td style="text-align: right;">7.29%</td>
<td style="text-align: right;">2.00</td>
</tr>
</tbody>
</table>
<p>这个结果支持的结论是：“在这个刻意带有周周期的7次教学回测中，同周法的绝对误差更低，但持续低估。”它不支持“同周法适用于所有餐饮企业”，也不支持“预计真实业务能降低一半损耗”。</p>
<h3 id="为什么不优先用mape">4.4 为什么不优先用MAPE</h3>
<p>MAPE先计算每一行|实际−预测|÷实际，再平均。实际为0时无法直接计算，实际接近0时比值会非常大。例如实际1件、预测3件，误差为200%；实际100件、预测102件，误差为2%，虽然两次都偏了2件。</p>
<p>服装尺码SKU或低频食材经常存在0销量日，MAPE会让评价失真或无法计算。WAPE缓解了单行0值问题，但它更受大销量对象影响，不能代表每个SKU都表现不错。MAE、RMSE与百分比误差的基本定义和零值限制见<a
href="https://otexts.com/fpp3/toolbox.html">Forecasting Principles and
Practice 第5章的评估部分</a>。</p>
<p>同时预测多店多SKU时，至少报告三层结果：全体汇总指标、门店或商品分组指标、低量与高量对象分组指标。不同食材都以kg计量，也不意味着它们每kg短缺或报损的经济成本相同。</p>
<h3 id="未来7天一次预测与每天更新要分开">4.5
未来7天一次预测与每天更新要分开</h3>
<p>假设站在第7天要一次生成第8至14天的预测：</p>
<ul>
<li>昨日法可以把28kg延续到7天。</li>
<li>同周法可以直接重复第1至7天的星期模式。</li>
<li>移动平均若做递推，就必须把先前预测值放入后面的窗口，而不能偷用尚未发生的实际值。</li>
</ul>
<p>如果站在第7天，却给第9天的预测用了第8天真实耗用，那就是用更容易的“每天更新”任务伪装成“提前一周预测”。应在每条结果里保存origin_date、target_date、horizon和model_version。</p>
<h3 id="统一180天切分并识别已经暴露的测试区间">4.6
统一180天切分并识别已经暴露的测试区间</h3>
<p>180天实验统一采用112天训练、28天验证、40天历史测试的边界：</p>
<ul>
<li>第1至112天：初始训练区间。</li>
<li>第113至140天：验证区间，用于比较特征、窗口和模型设置。</li>
<li>第141至180天：历史已暴露测试区间，用于复现、复核和诊断既有结果，不能再称为未见过的独立最终测试。</li>
</ul>
<p>“已经暴露”是指开发者已经看过这段数据或成绩，并可能据此形成模型、特征或参数选择。即使文件仍叫test，或者把预测重新跑一遍，它也不会自动恢复独立性。本文14天手算样本与这份180天实验仍是两个不同数据集，不能拼接或互称截取。</p>
<p>若任务是每周生成未来7天预测，验证起点可用第112、119、126、133天，正好覆盖第113至140天。历史复核区间可用第140、147、154、161、168天作为起点，覆盖第141至175天的5个完整7天批次；剩余第176至180天只能作为从第175天起点出发的1至5步部分结果，单独标明步长与样本数，不能伪装成完整第6周的7步成绩。若任务是每天更新次日预测，则可在第140至179天逐日起算，评价第141至180天的全部40次预测。两种任务分别报分，不混算。</p>
<p>每个历史起点只能使用当时已知的数据。是否允许每周重新训练，也要提前写定。如果生产方案确实每周更新训练数据，评价时可以按固定规则纳入已经发生、已经到达的历史记录。但看过成绩后又更换特征或调整超参数，再在同一时间段报告结果，只能称为进一步的开发或历史复核。</p>
<p>需要评价新的独立泛化效果时，应另生成并保护一份尚未查看的模拟测试序列，或收集后续新时间段数据。先锁定数据生成或采集规则、模型选择与评价协议，再揭开测试；不能反复选择随机种子直到得到好成绩。新的模拟测试也只能检验指定生成机制下的表现，不能替代真实业务验证。</p>
<p>所有门店与SKU应按共同的时间边界切分。不要把整个长表随机抽80%训练、20%测试，否则同一天其他门店、未来星期或同一对象未来记录可能进入训练。另有“新店泛化”目标时，还需要专门保留未见过门店进行检验，这与普通时间外推是不同实验。</p>
<p>时间滚动验证只允许历史预测未来。工具使用时还要注意采样间隔与测试持续时间的一致性，见<a
href="https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.TimeSeriesSplit.html">scikit-learn
TimeSeriesSplit文档</a>。对多门店长表，通常应按唯一日期构造切分，再映射回记录，而不是直接按任意行顺序切。</p>
<h3 id="五种常见的数据穿越">4.7 五种常见的数据穿越</h3>
<ol type="1">
<li>用未来实际天气代替当时可见的天气预报。</li>
<li>预测明天时，把明天总订单数作为输入。</li>
<li>先用全部数据计算均值、补缺或标准化，再切训练测试。</li>
<li>计算过去7天平均时，窗口包含了待预测当天的目标。</li>
<li>用后续盘点、促销修订或商品最终生命周期标签回填过去的特征。</li>
</ol>
<p>正确顺序是先切分，再在训练区间学习处理规则，最后将同一规则应用于后续区间。每轮滚动实验都应重新遵守这条顺序。官方防泄漏说明见<a
href="https://scikit-learn.org/stable/common_pitfalls.html">scikit-learn
Common pitfalls</a>。</p>
<h3 id="电子表格评分做法">4.8 电子表格评分做法</h3>
<p>假设A2:A8是真实值，B2:B8是某模型预测值：</p>
<ul>
<li>C2写=A2-B2，向下填充，得到有符号误差。</li>
<li>D2写=ABS(C2)，向下填充，得到绝对误差。</li>
<li>E2写=C2^2，向下填充，得到平方误差。</li>
<li>MAE：<code>=AVERAGE(D2:D8)</code></li>
<li>RMSE：<code>=SQRT(AVERAGE(E2:E8))</code></li>
<li>WAPE：<code>=SUM(D2:D8)/SUM(A2:A8)，将单元格设置为百分比。</code></li>
<li>Bias：<code>=AVERAGE(C2:C8)</code></li>
</ul>
<p><strong>本章练习。</strong>
模型A的MAE是2kg、Bias是2kg；模型B的MAE是2kg、Bias是0kg。是否可以说两者同样好？</p>
<p><strong>参考答案。</strong>
只能说平均绝对偏差相同。A持续偏低，B可能高低抵消。两者对库存的影响可能不同，还应看误差分布、发生在哪些SKU以及采购策略。Bias为0也不代表每次都准确。</p>
<h2 id="本阶段项目与验收">本阶段项目与验收</h2>
<h3
id="阶段3先证明没有偷看答案3课">阶段3：先证明没有偷看答案（3课）</h3>
<p>课程：①MAE/RMSE/WAPE/Bias；②时间切分与滚动原点；③未来特征、快照与泄漏测试。</p>
<p>项目P03“给好得离谱的模型找作弊点”：读取project-fixtures/P03/input的2,880条数据与故障特征/切分文件，已实际设置centered滚动、target未来销量、全数据归一化、随机切分4类缺陷，逐一修复；并制作单步与固定5步两种预测账本。</p>
<p>交付：evaluation_protocol.md、forecast_ledger.csv、leakage_tests.py、误差分布图。</p>
<p>验收：所有feature.available_at≤origin；训练最大目标日期≤原点可观察时点；验证单步28目标、5步24窗口；4类已注入泄漏均检出；全零实际值时WAPE显示“未定义”而非0或无限大。</p>
