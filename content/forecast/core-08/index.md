{
  "title": "账面 实盘 质量与报废对账",
  "description": "账面 实盘 质量与报废对账：这套补课把同一瓶合成的柠檬茶，从销售记录、订单、仓库、工厂、物料清单一直追到预测、建议单、审批和模拟反馈。读者只需会四则运算、百分数和平方根。每章先手算，再运行程序，最后故意破坏一个输入，看系统有没有拒绝错误。",
  "type": "forecast",
  "unit": "core-08",
  "weight": 88,
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
</details><h2 id="core-08-账面-实盘-质量与报废对账">core-08 账面 实盘
质量与报废对账</h2>
<p>覆盖
G02。目标是看出一个“98%账实准确率”为什么仍可能掩盖10瓶幽灵可售库存。</p>
<h3 id="先分互不重叠的桶">1 先分互不重叠的桶</h3>
<table>
<thead>
<tr class="header">
<th>状态桶</th>
<th style="text-align: right;">账面瓶数</th>
<th style="text-align: right;">实盘瓶数</th>
<th style="text-align: right;">实盘减账面</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>可售good</td>
<td style="text-align: right;">190</td>
<td style="text-align: right;">180</td>
<td style="text-align: right;">−10</td>
</tr>
<tr class="even">
<td>质量隔离quarantine</td>
<td style="text-align: right;">8</td>
<td style="text-align: right;">10</td>
<td style="text-align: right;">+2</td>
</tr>
<tr class="odd">
<td>待报废scrap</td>
<td style="text-align: right;">2</td>
<td style="text-align: right;">6</td>
<td style="text-align: right;">+4</td>
</tr>
<tr class="even">
<td>合计</td>
<td style="text-align: right;">200</td>
<td style="text-align: right;">196</td>
<td style="text-align: right;">−4</td>
</tr>
</tbody>
</table>
<p>每瓶只能在一个桶里。待报废这里仍在现场，所以包含在实盘总量，但不能卖；一旦真正销毁，再通过单独出库事件减少实物。隔离库存不等于已经报废，也不能自动移回可售。</p>
<p>本例差异可以由4瓶实物盘亏加6瓶质量状态未及时重分类解释：190−4−2−4=180可售；隔离增加2；待报废增加4。这是<strong>与数字一致的候选解释</strong>，不是已经找到真实根因。还应核查漏记出库、漏记报损、重复入库、跨仓错挂、单位错误和盘点误差的证据。</p>
<h3 id="三种口径逐步计算">2 三种口径逐步计算</h3>
<p><code>净数量准确率 = 1 − |账面总量−实盘总量|/账面总量</code>。竖线表示绝对值，不看正负。1−|200−196|/200=1−4/200=98%。</p>
<p><code>分桶准确率 = 1 − Σ|每桶账实差|/账面总量</code>。绝对差10+2+4=16，所以1−16/200=92%。这能减少不同状态之间互相抵消的遮蔽。本包把最低值截在0，避免严重差异出现负准确率；原始差异仍保留。</p>
<p><code>完全一致桶比例 = 完全一致桶数/全部桶数</code>。本例0/3=0%。它与98%衡量的东西完全不同。</p>
<p>可售幽灵库存=账面可售−实盘可售=190−180=10瓶。总量差只有4，并不能说明超卖风险只有4瓶。</p>
<h3 id="如何进入补货">3 如何进入补货</h3>
<p>08:00之前完成并可得的本次盘点，作为本模拟WMS180瓶可售快照的依据。质量隔离10和待报废6都不进可售。若误把实盘196全当可售，库存位置多16瓶，补货可能不足。若连账面200都直接当可售，会多20瓶。</p>
<p>调整账目应有盘点单、差异原因、审批人、可得时点及关联库存版本。本包计算差异并使用明确给定的盘点后快照，不会自动把推测原因记成真实冲销。</p>
<h3 id="项目和答案">4 项目和答案</h3>
<p>输入 <code>inventory.csv</code>，输出
<code>inventory</code>。跨表验收还要求当时盘点可售量与WMS快照一致；只改其中一表会报
<code>WMS_COUNT_SNAPSHOT_MISMATCH</code>，须先解释差异，不会照着旧快照继续模拟发单。先手算三个准确率，再运行核对。将账面可售190改180但其余账面不改，账面合计变190；净误差反而由−4变为+6，不能继续拿原来的200作分母。</p>
<p>故障注入：把隔离库存也加进可售，检查是否造成超卖；把一瓶同时登记good与quarantine，会重复计数。对负库存或零分母，程序应报错。对于跨行重复物理对象，本包没有序列号，无法自动识别，须扩展批次/容器主键。</p>
<p><strong>边界：</strong>
98%只是本组合成数的一个净量口径，不是达到企业98%里程碑的证据；没有财务损益分录、责任归属或真实食品质量判断。</p>
