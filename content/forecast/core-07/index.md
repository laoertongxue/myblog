{
  "title": "三类建议单的状态与幂等",
  "description": "三类建议单的状态与幂等：这套补课把同一瓶合成的柠檬茶，从销售记录、订单、仓库、工厂、物料清单一直追到预测、建议单、审批和模拟反馈。读者只需会四则运算、百分数和平方根。每章先手算，再运行程序，最后故意破坏一个输入，看系统有没有拒绝错误。",
  "type": "forecast",
  "unit": "core-07",
  "weight": 87,
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
</details><h2 id="core-07-三类建议单的状态与幂等">core-07
三类建议单的状态与幂等</h2>
<p>覆盖
A09。目标是在断网重试、重复回执和修改数量时，账本仍只记一次正确变化。</p>
<h3 id="状态是门而不是标签">1 状态是门而不是标签</h3>
<p>基本路径：<code>DRAFT → VALIDATED → PENDING_APPROVAL → APPROVED → MOCK_SENT → PARTIALLY_FILLED → COMPLETED</code>。审批也可到
<code>REJECTED</code>。箭头表示允许的一步；不能从草稿直接跳完成。</p>
<ul>
<li>DRAFT：数量和版本仍可修改。</li>
<li>VALIDATED：通过单位、箱规和适用的资源检查。</li>
<li>PENDING_APPROVAL：等待对应职责角色。</li>
<li>APPROVED：批准的是确切版本和数量。</li>
<li>MOCK_SENT：本地适配器已接受，不代表货到。</li>
<li>PARTIALLY_FILLED：有唯一反馈，但累计数量未满。</li>
<li>COMPLETED：反馈累计等于批准数量。</li>
</ul>
<p>PO由采购经理批准，STO由物流经理，WO由生产经理。提出者planner不能自己批准。角色只是模拟字符串，不是身份认证。</p>
<h3 id="修改后为什么要重新批准">2 修改后为什么要重新批准</h3>
<p>批准摘要包括种类、业务ID、数量、修订号和动作详情。摘要hash可以理解为内容指纹：内容变了，指纹也应变。原单60瓶批准后改66瓶，旧批准不能沿用；<code>STALE_OR_MISSING_APPROVAL</code>会挡住。</p>
<p>正规修改会增加revision、保留修改理由并退回DRAFT。已经发出或部分完成的单不能直接重写；需要另外的撤回/冲销流程，本包没有实现真实撤销。</p>
<h3 id="两层幂等">3 两层幂等</h3>
<p>“幂等”就是同一件事重复传来，效果仍只有一次。</p>
<p>发送键：<code>种类:业务ID:修订号</code>。重复相同键和相同内容返回原回执；相同键内容不同必须冲突，不能把它当新单。</p>
<p>反馈键：唯一event_id。PO60第一条反馈36瓶，再来一次同一event_id的36瓶，不重复增加库存。第二个event_id反馈24瓶后累计36+24=60。若同一反馈ID从36改30，必须报告冲突。</p>
<p>数量守恒：<code>未完成量 = 批准量 − 已完成量</code>。第一条后60−36=24；第二条后0。不能接受66瓶回执，不能产生负的未完成量。</p>
<h3 id="超时不是失败的证明">4 超时不是失败的证明</h3>
<p>故障模式“适配器接受后回执丢失”会抛超时。此时不能新建第二个业务ID再发一单。先查/重用原幂等键，拿回已经存在的接受记录。测试
<code>test_uncertain_ack</code> 模拟了这个顺序。</p>
<h3 id="项目与答案">5 项目与答案</h3>
<p>输入基础计划三张单；输出
<code>approval_audit.csv</code>、订单状态及模拟账。三张单只产生三个发送接受记录，PO两次到货加STO一次、WO一次，共四次库存效果。全部发送和反馈再播一次，库存摘要完全相同。</p>
<p>练习：PO已经收36，还能把批准量直接改24吗？答案：不能；24是剩余未完成量，不是新的总批准量。调拨60以后远仓应为84−60=24，重放不得变为−36。</p>
<p>故障注入：错误角色批准、跳过提交、批准后直接改数量、重复不同内容的反馈、超额反馈，均有拒绝测试。</p>
<p><strong>边界：</strong>
幂等表在单次Python进程内保存，示范事件重播，不保证进程重启后持久化恢复；没有数据库事务、分布式锁、真实鉴权或外部系统的exactly-once承诺。</p>
