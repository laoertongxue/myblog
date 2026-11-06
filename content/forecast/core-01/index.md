{
  "title": "同一商品的四个业务限制",
  "description": "同一商品的四个业务限制：这套补课把同一瓶合成的柠檬茶，从销售记录、订单、仓库、工厂、物料清单一直追到预测、建议单、审批和模拟反馈。读者只需会四则运算、百分数和平方根。每章先手算，再运行程序，最后故意破坏一个输入，看系统有没有拒绝错误。",
  "type": "forecast",
  "unit": "core-01",
  "weight": 81,
  "outputs": [
    "HTML"
  ]
}

<p class="check">新增离线教学实验，非生产流程。<a href="/forecast/forecast-core-gap-labs.zip" download>下载核心12章实验包</a>。core-13已新增有限预售/PO/STO/WO联合实验；通用跨期联合优化未实现，审批、回写和执行仅在本地模拟。</p><details><summary>共同运行方法与边界</summary><h2
id="从数据到离线决策的十二个补充实验">从数据到离线决策的十二个补充实验</h2>
<p>这套补课把同一瓶合成的柠檬茶，从销售记录、订单、仓库、工厂、物料清单一直追到预测、建议单、审批和模拟反馈。读者只需会四则运算、百分数和平方根。每章先手算，再运行程序，最后故意破坏一个输入，看系统有没有拒绝错误。</p>
<p><strong>所有商品、销量、价格、人物角色和指标都是合成数据。所有订单、价格、曝光与反馈都只写入本地模拟账本。没有真实采购、调拨、制造、营销、食品放行或对外发送。</strong>
这些实验展示机制，不能作为生产就绪、真实收益、质量安全认证或完整企业系统的证明。</p>
<p>主商品是 SPU <code>TEA</code> 下的 SKU <code>T-L</code>（500 ml
柠檬茶一瓶）。另一 SKU <code>T-P</code> 只在流量实验作为桃茶对照。SKU
是可独立计数的商品，SPU 是产品家族。这里“一瓶”记作 <code>ea</code>；6
瓶为一箱。原料有糖浆 <code>R-SYRUP</code>、包装膜 <code>R-FILM</code>
和空瓶 <code>R-BOTTLE</code>。</p>
<p>统一决策时点为 2026-06-15 08:00 UTC，主要计划到货日为
06-17。<code>event_date</code> 是业务发生日期；<code>target_date</code>
是记录适用的预测/计划日期；<code>known_at</code>
是我们最早能使用这条记录的时间。三个字段不能互换。</p>
<h2 id="阅读与运行">阅读与运行</h2>
<p>解压 <code>forecast-core-gap-labs.zip</code>，进入包目录，用 Python
3.10 或更高版本运行：</p>
<div class="sourceCode" id="cb1"><pre
class="sourceCode bash"><code class="sourceCode bash"><span id="cb1-1"><a href="#cb1-1" aria-hidden="true" tabindex="-1"></a><span class="ex">python</span> core_lab.py <span class="at">--self-test</span></span></code></pre></div>
<p>只依赖 Python 标准库，不需要联网、账号、密钥或安装第三方包。程序读取
<code>data/</code> 下的 CSV/JSON，输出
<code>output/report.json</code>、<code>policy_daily.csv</code>、<code>orders.csv</code>、<code>approval_audit.csv</code>
和 <code>four_dimensions.csv</code>。正常运行不会重建输入，所以修改 CSV
后能观察结果变化。<code>--generate-fixtures</code>
会<strong>明确重建</strong>合成输入，只在想恢复初始数据时使用。非法选项退出码为
2，不能当作实验通过。</p>
<p>所有练习修改都应在复制出来的实验目录做。<code>--self-test</code>
包含初始数据的标准答案断言，修改数据后这些断言可能失败，这正是需要解释的差异。想只计算修改后的输入，用
<code>python core_lab.py --output-dir output_changed</code>。不要为了得到“全部通过”而把错误答案写进断言。</p>
<p>预期阅读顺序：业务限制 → 主数据 → 可得时点 → 四层链路 → 补货算式 →
预售与来源分配 → 状态机 → 库存差异 → 采纳 → 三指标 → 流量 →
事件联动。每章的需求编号用于追溯原范围，不代表该范围已由独立审查判定完整。</p>
</details><h2 id="core-01-同一商品的四个业务限制">core-01
同一商品的四个业务限制</h2>
<p>覆盖
A01。目标是解释：同一个模型为什么在不同业务条件下需要不同的预测期限和行动限制。</p>
<h3 id="什么是四维">1 什么是四维</h3>
<p>PLC（产品生命周期）在这里用“活动还剩几天”表示。物理保质期表示在指定合规条件下能保存多久；审美有效期表示包装、款式或主题还能吸引顾客多久；Lead
Time
表示现在决定到货要等几天；履约确定性用按约到齐的情景概率表示。审美有效期短不等于食品不安全，物理期限也不能因审美受欢迎而延长。</p>
<p>本章把保质期当作已知的模拟硬限制，不预测食品是否安全。现实中必须以标签、质量制度和有权人员判断为准。</p>
<h3 id="两个简单公式">2 两个简单公式</h3>
<p><code>H = L + R</code>。H 是需要覆盖的天数；L 是交期，单位天；R
是复查间隔，单位天。本例 L=2，R=1，所以 H=3
天。每天才检查一次，今天没买到的缺口不能假设下一秒就修复。</p>
<p><code>W = min(P, S, A)</code>。W 是剩余可销售窗口，单位天；P
是生命周期剩余天数；S 是物理剩余天数；A 是审美剩余天数。<code>min</code>
就是取最小数。基准 W=min(30,10,14)=10 天。</p>
<p>若
<code>L ≥ W</code>，本实验挡住常规补货：货到时销售窗口已关闭或刚到边界。边界采用保守的“必须在窗口结束前到货”，不能自行把等号改为安全。</p>
<h3 id="同商品敏感性对照">3 同商品敏感性对照</h3>
<table style="width:100%;">
<colgroup>
<col style="width: 10%" />
<col style="width: 13%" />
<col style="width: 13%" />
<col style="width: 13%" />
<col style="width: 13%" />
<col style="width: 13%" />
<col style="width: 13%" />
<col style="width: 10%" />
</colgroup>
<thead>
<tr class="header">
<th>情景</th>
<th style="text-align: right;">P 天</th>
<th style="text-align: right;">S 天</th>
<th style="text-align: right;">A 天</th>
<th style="text-align: right;">L 天</th>
<th style="text-align: right;">按时到齐概率</th>
<th style="text-align: right;">H 天</th>
<th>模型与动作</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>基准</td>
<td style="text-align: right;">30</td>
<td style="text-align: right;">10</td>
<td style="text-align: right;">14</td>
<td style="text-align: right;">2</td>
<td style="text-align: right;">0.9</td>
<td style="text-align: right;">3</td>
<td>去星期后的 WMA 作基线，再查库存约束</td>
</tr>
<tr class="even">
<td>物理期限变短</td>
<td style="text-align: right;">30</td>
<td style="text-align: right;">1</td>
<td style="text-align: right;">14</td>
<td style="text-align: right;">2</td>
<td style="text-align: right;">0.9</td>
<td style="text-align: right;">3</td>
<td>W=1，挡住常规补货，考虑更短交期且重新核验</td>
</tr>
<tr class="odd">
<td>主题即将过时</td>
<td style="text-align: right;">30</td>
<td style="text-align: right;">10</td>
<td style="text-align: right;">2</td>
<td style="text-align: right;">2</td>
<td style="text-align: right;">0.9</td>
<td style="text-align: right;">3</td>
<td>W=2，挡住常规补货，不能因有销量就追单</td>
</tr>
<tr class="even">
<td>交期变长</td>
<td style="text-align: right;">30</td>
<td style="text-align: right;">10</td>
<td style="text-align: right;">14</td>
<td style="text-align: right;">5</td>
<td style="text-align: right;">0.9</td>
<td style="text-align: right;">6</td>
<td>预测至少覆盖6天，必须重新估计累计误差</td>
</tr>
<tr class="odd">
<td>履约变不稳</td>
<td style="text-align: right;">30</td>
<td style="text-align: right;">10</td>
<td style="text-align: right;">14</td>
<td style="text-align: right;">2</td>
<td style="text-align: right;">0.6</td>
<td style="text-align: right;">3</td>
<td>保留需求预测，增加供应情景和应急来源审查</td>
</tr>
<tr class="even">
<td>上市初期短窗口</td>
<td style="text-align: right;">5</td>
<td style="text-align: right;">10</td>
<td style="text-align: right;">14</td>
<td style="text-align: right;">2</td>
<td style="text-align: right;">0.9</td>
<td style="text-align: right;">3</td>
<td>历史少，用类比和区间情景；不能照抄稳定品 WMA</td>
</tr>
</tbody>
</table>
<p>概率 0.6
的意思是教学情景里十次有六次按约到齐，不是“实际总能收到订单量的60%”。例如订100瓶，供应可能是100或0，平均60瓶并不保证今天有60瓶。把需求预测除以0.6也不自动解决这个风险，可能制造更大的到货过量。</p>
<h3 id="输入-输出和项目">4 输入 输出和项目</h3>
<p>输入为 <code>four_dimensions()</code> 中六组明确参数。输出见
<code>four_dimensions.csv</code>，包括
H、W、风险标记和动作限制。程序只是规则判断，不会训练一个适合所有生命周期阶段的模型。</p>
<p>练习：把基准交期改为12天，哪个约束先失败？答案：W仍是10天，12≥10，常规补货被挡住；H变成13天，但预测得更远不能使过期货重新可卖。再把履约概率从0.9改0.6，W不会变化，应新增供应风险审查，而不是偷偷更改销量。</p>
<p>故障注入：把物理保质期当成审美期限互换，检查是否误导了质量解释；把“按时概率”当成“可售比例”，解释为什么单次供应不是平均数。</p>
<p><strong>边界：</strong>
六种情景有可执行输出，但没有自动选择/训练生命周期模型，也没有交期分布或供应相关性的估计。</p>
