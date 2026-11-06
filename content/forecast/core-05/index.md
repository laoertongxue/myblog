{
  "title": "把 WMA 星期 安全库存和箱规接在一起",
  "description": "把 WMA 星期 安全库存和箱规接在一起：这套补课把同一瓶合成的柠檬茶，从销售记录、订单、仓库、工厂、物料清单一直追到预测、建议单、审批和模拟反馈。读者只需会四则运算、百分数和平方根。每章先手算，再运行程序，最后故意破坏一个输入，看系统有没有拒绝错误。",
  "type": "forecast",
  "unit": "core-05",
  "weight": 85,
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
</details><h2 id="core-05-把-wma-星期-安全库存和箱规接在一起">core-05 把 WMA 星期
安全库存和箱规接在一起</h2>
<p>覆盖
G05。目标是用同一输入从历史销量算到最终补货，同时保留每一步造成的增量和冲突。</p>
<h3 id="先去掉星期效应">1 先去掉星期效应</h3>
<p>WMA
是加权移动平均，越近的数据给更大权重。若原销量含星期高低，就先除星期系数再求趋势，最后乘未来星期系数，避免把周末效应重复算两遍。</p>
<p><code>b_t = y_t / s_t</code>。y_t 为第t天销量，单位瓶；s_t
为该星期的无量纲系数；b_t
为去星期的日基准，单位瓶/日。固定七天系数为0.9、0.9、1.2、1.0、1.1、1.0、0.9，平均为1。</p>
<p>最近三天为：周五132÷1.1=120，周六120÷1=120，周日126÷0.9=140。</p>
<p><code>B = (w1×b1 + w2×b2 + w3×b3)/(w1+w2+w3)</code>。B是新日基准，权重无单位。用1、2、3：分子120+240+420=780，分母6，所以B=130。</p>
<p><code>预测_t = B × 未来星期系数_t</code>。周一130×0.9=117，周二117，周三130×1.2=156；三天总计390瓶。</p>
<h3 id="再估计误差缓冲">2 再估计误差缓冲</h3>
<p>四次已到期、无泄漏的单日误差为−10、10、−10、10瓶。此处误差定义为实际减预测。每个误差平方100，均值100，开平方得到10瓶。</p>
<p><code>σ = sqrt[Σ(e_i²)/n]</code>。σ是本实验使用的残差均方根，单位瓶；e_i是误差；n=4。它不是已知总体真实标准差，仅是极小教学样本的估计。</p>
<p><code>SS = z × σ × sqrt(H)</code>。SS为安全库存，单位瓶；z=1.65是本实验指定的无量纲风险系数；H=L+R=3；所以SS=1.65×10×√3=28.5788瓶。平方根成立依赖每日误差近似无偏且互相独立。残差有关联、交期随机或需求非正态时，这个式子不能直接保证95%服务。</p>
<p>动态的意思是每个新的决策cutoff，都可以用当时已到期的新误差重新估计σ。不能用尚未发生的未来误差更新今天SS。若σ变20，其他相同，SS变57.1577瓶。</p>
<h3 id="库存位置与整箱">3 库存位置与整箱</h3>
<p><code>IP = 可售 + 可靠在途 − 独立已承诺数量</code>。IP=180+60−30=210瓶。POS目标不含那30瓶OMS需求，因此减预留没有重复计数；如果预测已包含OMS，就不能再这样减一次。</p>
<p><code>Q_raw = max(0, Σ预测 + SS − IP)</code>。<code>max</code>表示若结果为负就取0，不能订负数。Q_raw=390+28.5788−210=208.5788瓶。</p>
<p>MOQ是“有下单时的最低量”，本例12瓶。箱规c=6瓶/箱：</p>
<p><code>Q = 0（当Q_raw=0）；否则 Q = c × ceil[max(Q_raw, MOQ)/c]</code>。</p>
<p>ceil是向上取到整数。208.5788÷6=34.7631箱，取35箱，再乘6=210瓶。多出的210−208.5788=1.4212瓶是包装约束造成的，不是预测需求。</p>
<h3 id="冲突账">4 冲突账</h3>
<table>
<thead>
<tr class="header">
<th>步骤</th>
<th style="text-align: right;">数量或状态</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>三天POS预测</td>
<td style="text-align: right;">390瓶</td>
</tr>
<tr class="even">
<td>误差缓冲</td>
<td style="text-align: right;">28.5788瓶</td>
</tr>
<tr class="odd">
<td>库存位置</td>
<td style="text-align: right;">210瓶</td>
</tr>
<tr class="even">
<td>未取整缺口</td>
<td style="text-align: right;">208.5788瓶</td>
</tr>
<tr class="odd">
<td>MOQ/箱规后</td>
<td style="text-align: right;">210瓶</td>
</tr>
<tr class="even">
<td>基准收货容量</td>
<td style="text-align: right;">210瓶，正好可容纳</td>
</tr>
<tr class="odd">
<td>故障容量180</td>
<td style="text-align: right;">BLOCKED_CAPACITY，缺30瓶容量</td>
</tr>
</tbody>
</table>
<p>如果容量只有180，不能悄悄把210改为180又显示“成功”。要输出冲突，再讨论分批、不同日期或降低服务目标。本包只报冲突，不替人决定如何承担后果。</p>
<h3 id="项目与答案">5 项目与答案</h3>
<p>输入
<code>pos.csv</code>、<code>snapshots.csv</code>、<code>config.json</code>，输出
<code>pipeline</code>、<code>capacity_conflict</code>。将最近误差幅度从10改20，未取整量237.1577，取整240瓶，超过210容量，应挡住。若Q_raw=1、MOQ=12、箱规6，答案12；Q_raw=0时答案0，而不是强行凑MOQ。</p>
<p>故障注入：交期改3但未来系数仍只有三天，<code>HORIZON_MISMATCH</code>。正确修复是新增第四天的合法预测和信息契约，不是关掉断言。</p>
<p><strong>边界：</strong>
星期系数、权重、z及误差样本都是合成给定参数，没有通过真实回测确定；输入准备与模型选择仍需独立验证。</p>
