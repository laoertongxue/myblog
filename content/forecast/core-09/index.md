{
  "title": "把采纳记录变成可解释的分母",
  "description": "把采纳记录变成可解释的分母：这套补课把同一瓶合成的柠檬茶，从销售记录、订单、仓库、工厂、物料清单一直追到预测、建议单、审批和模拟反馈。读者只需会四则运算、百分数和平方根。每章先手算，再运行程序，最后故意破坏一个输入，看系统有没有拒绝错误。",
  "type": "forecast",
  "unit": "core-09",
  "weight": 89,
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
</details><h2 id="core-09-把采纳记录变成可解释的分母">core-09
把采纳记录变成可解释的分母</h2>
<p>覆盖 G07。目标是防止删去未处理建议后，把采纳率从60%抬成75%。</p>
<h3 id="四类事件">1 四类事件</h3>
<p>原样采纳as_is：数量没有改变，原因NO_CHANGE。调整后采纳adjusted：保留原数量、最终数量和枚举原因。拒绝rejected：明确拒绝及原因。未处理unhandled：截止前没有可得的最终决定，不能默认为拒绝，也不能从分母消失。</p>
<p>本包允许的原因是NO_CHANGE、CAPACITY、QUALITY_HOLD、DUPLICATE_PLAN、SUPPLIER_UNAVAILABLE、DEMAND_CHANGE。调整后的采纳不能用NO_CHANGE敷衍。自由文本可辅助说明，但不能替代可汇总的原因类别。</p>
<p>十条建议在08:00发布，10:00到处理截止，11:00统计。4条原样，2条调整，2条拒绝，2条未处理。全部十条都已到期且符合统计范围。</p>
<h3 id="四个比例">2 四个比例</h3>
<p><code>严格采纳率 = 原样采纳/符合范围且已到期建议数 = 4/10 = 40%</code>。</p>
<p><code>宽口径采纳率 = (原样+调整)/同一分母 = 6/10 = 60%</code>。</p>
<p><code>决策完成率 = (原样+调整+拒绝)/同一分母 = 8/10 = 80%</code>。</p>
<p><code>已处理中的宽采纳率 = (原样+调整)/已处理 = 6/8 = 75%</code>。</p>
<p>75%不是计算错误，但它回答了另一个问题。报告必须写清“已处理中的”，不能拿75%替代全部建议的60%。统计09:00时，10:00截止尚未到，程序报空分母，不能填0%假装没有采纳。</p>
<p>采纳也不等于正确：人可能机械照单接受，导致损耗；拒绝也不等于系统没用，可能发现质量风险。需要同时看原因、实际结果和FVA，不能只把70%当成冲刺目标。</p>
<h3 id="项目和答案">3 项目和答案</h3>
<p>输入 <code>adoption.csv</code>，输出
<code>adoption</code>。把第二条原样60的最终量改54，应该报
<code>AS_IS_CHANGED</code>。把调整30→24的原因清空，应该报
<code>MISSING_REASON_ENUM</code>。在实际业务里，一条建议的重复事件应按唯一建议ID和最终可得状态折叠，本包CSV每个ID只给一条最终记录。</p>
<p>练习：新增一条11:00发布、12:00截止的未处理建议，仍在11:00统计，是否让采纳率变6/11？答案：不应。它尚未到期，不进入这期到期分母；若改用“全部已发布建议”，必须另立口径。</p>
<p><strong>边界：</strong>
本包验证离线原因枚举与分母，不连接审批产品、不评价员工绩效，也不证明70%采纳目标已被达成。</p>
