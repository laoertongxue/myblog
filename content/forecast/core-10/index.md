{
  "title": "在同一十四天账本比较三项业务指标",
  "description": "在同一十四天账本比较三项业务指标：这套补课把同一瓶合成的柠檬茶，从销售记录、订单、仓库、工厂、物料清单一直追到预测、建议单、审批和模拟反馈。读者只需会四则运算、百分数和平方根。每章先手算，再运行程序，最后故意破坏一个输入，看系统有没有拒绝错误。",
  "type": "forecast",
  "unit": "core-10",
  "weight": 90,
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
</details><h2 id="core-10-在同一十四天账本比较三项业务指标">core-10
在同一十四天账本比较三项业务指标</h2>
<p>覆盖
G11。目标是把预测改动放进同一库存规则中，比较缺货、损耗和周转，而不是只报告预测误差。</p>
<h3 id="公平比较先固定什么">1 公平比较先固定什么</h3>
<p>两个方案使用相同需求、初始20瓶、交期1天、每天收盘下单、次日开门到货、1瓶包装单位、MOQ=0、同样的一日标签有效期以及相同先销售再清理规则。每日剩余必须在当天闭店报废，不能留给第二天。这个极短保质期是<strong>专门的压力情景</strong>，不是前面主商品10天期限的默认参数。</p>
<p>共同补货规则：<code>次日订单=max(0,次日预测+SS−次日可用结转)</code>。一日效期下结转为0。旧方案用固定预测20、SS=0；新方案用7日前同星期实际销量、SS=2。新旧改变的是预测/缓冲参数，库存执行规则不变。首日库存20相同，不能让新方案偷偷换一个更合适的起点。</p>
<p>需求14天为8、32、9、30、11、28、10，再重复一次。第0天前的七天历史为10、30、10、30、10、30、10。新方案下第1天预测使用历史30而不是明天实际32。第7天以后才使用已经发生的第0天以后数据。</p>
<h3 id="每天的守恒">2 每天的守恒</h3>
<p><code>销售 = min(开门库存,需求)</code>；<code>缺货 = 需求−销售</code>；<code>闭店报废 = 开门库存−销售</code>。本例无退货，无跨日剩货，所以开门库存=销售+报废。</p>
<p>第0天两方案都是20瓶，需求8，销售8，缺货0，报废12。</p>
<p>第1天旧方案到货20，需求32，销售20、缺货12、报废0。新方案前一天只知道同星期历史30，加SS2订32，到货32，销售32、缺货0、报废0。</p>
<p>第2天旧方案20对需求9，销售9、报废11；新方案12对需求9，销售9、报废3。每个数都可以在
<code>policy_daily.csv</code> 找到，不能只看汇总好看的那几天。</p>
<h3 id="三个指标与各自分母">3 三个指标与各自分母</h3>
<p><code>缺货率=累计未满足瓶数/累计需求瓶数</code>。旧60/256=23.4375%；新0/256=0%。本包是假定缺货丢失销量，没有延期欠交。</p>
<p><code>损耗率=累计报废瓶数/期间全部可用瓶数</code>。旧84/280=30%；新38/294≈12.9252%。这里分母包含相同首日20瓶和期间实际到货，不是销售额或订单数。</p>
<p>先估算每日平均在手：<code>(开门库存+报废前剩余)/2</code>，单位瓶。它是线性耗用近似，不是真实逐秒积分。将14个日均值取平均，旧为13瓶，新为11.8571瓶。</p>
<p><code>14天周转次数=期间销售瓶数/平均在手瓶数</code>。旧196/13=15.0769次；新256/11.8571=21.5904次。这是14天窗口，不是年周转。销售和库存同为同一SKU瓶数，才能约掉单位；多个不同成本商品通常要用一致的金额口径。</p>
<table>
<thead>
<tr class="header">
<th>指标</th>
<th style="text-align: right;">旧方案</th>
<th style="text-align: right;">新方案</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>需求</td>
<td style="text-align: right;">256</td>
<td style="text-align: right;">256</td>
</tr>
<tr class="even">
<td>销售</td>
<td style="text-align: right;">196</td>
<td style="text-align: right;">256</td>
</tr>
<tr class="odd">
<td>缺货瓶数</td>
<td style="text-align: right;">60</td>
<td style="text-align: right;">0</td>
</tr>
<tr class="even">
<td>报废瓶数</td>
<td style="text-align: right;">84</td>
<td style="text-align: right;">38</td>
</tr>
<tr class="odd">
<td>缺货率</td>
<td style="text-align: right;">23.4375%</td>
<td style="text-align: right;">0%</td>
</tr>
<tr class="even">
<td>损耗率</td>
<td style="text-align: right;">30%</td>
<td style="text-align: right;">12.9252%</td>
</tr>
<tr class="odd">
<td>平均在手</td>
<td style="text-align: right;">13</td>
<td style="text-align: right;">11.8571</td>
</tr>
<tr class="even">
<td>14天周转</td>
<td style="text-align: right;">15.0769</td>
<td style="text-align: right;">21.5904</td>
</tr>
</tbody>
</table>
<h3 id="结果怎样表述才准确">4 结果怎样表述才准确</h3>
<p>这个可复算场景中三个指标都改善，但合成需求含强星期重复，恰好有利于lag7方法。不能外推为真实企业必然降低多少成本，也不能宣称全年周转提升42%。还要在不重复的需求、促销、缺货截尾、交期波动、误差相关及真实成本上重新验证。</p>
<h3 id="项目与答案">5 项目与答案</h3>
<p>输入
<code>policy_demand.csv</code>；输出逐日账和两组汇总。把第6天实际改999，检查第5天给第6天的订单是否跟着改。答案不应改变，因为第5天并不知道第6天实际值；第13天的lag7预测可以在第6天发生后受影响。</p>
<p>练习：为什么新方案供给294比旧280更多，平均库存反而低？答案：到货更贴近高需求日，卖出了更多，低需求日积压较少；“总进货少”与“在手少”不是同一指标。</p>
<p><strong>边界：</strong>
已实现14天同规则回放，不含多批次FIFO、随机寿命、真实销售漏斗、欠交或资本成本；它提供机制证据，不是原文经营改善里程碑的验证。</p>
