{
  "title": "让四个系统说同一种数量语言",
  "description": "让四个系统说同一种数量语言：这套补课把同一瓶合成的柠檬茶，从销售记录、订单、仓库、工厂、物料清单一直追到预测、建议单、审批和模拟反馈。读者只需会四则运算、百分数和平方根。每章先手算，再运行程序，最后故意破坏一个输入，看系统有没有拒绝错误。",
  "type": "forecast",
  "unit": "core-02",
  "weight": 82,
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
</details><h2 id="core-02-让四个系统说同一种数量语言">core-02
让四个系统说同一种数量语言</h2>
<p>覆盖
G01。目标是阻止“5箱被当成5瓶”“200克被当成200千克”和主表重复导致销量翻倍。</p>
<h3 id="一条主数据记录要说明什么">1 一条主数据记录要说明什么</h3>
<p><code>master.csv</code> 每行包括系统、原编码、统一
SKU、SPU、原单位、基础单位、换算倍数、量纲、生效起止日期及可得时点。POS
的 <code>LEMON500</code>、OMS 的 <code>L-CASE</code>、WMS 的
<code>L-WH</code>、MES 的 <code>L-FIN</code> 都指向
<code>T-L</code>，但原单位并不一定相同。</p>
<p>主键不能只用原编码。不同系统可能都叫“001”，它们未必是同一商品。此处按“系统+原编码+生效区间”识别，每条输入只能匹配一条有效主数据。生效区间采用左闭右开：<code>valid_from ≤ 日期 &lt; valid_to</code>。</p>
<h3 id="单位换算逐步计算">2 单位换算逐步计算</h3>
<p><code>基础数量 = 原数量 × 换算倍数</code>。原数量与基础数量的量纲必须相同。</p>
<ul>
<li>5 箱柠檬茶 × 6 瓶/箱 = 30 瓶。箱单位约掉，剩瓶。</li>
<li>18,000 克糖浆 × 0.001 千克/克 = 18 千克。</li>
<li>2,250 厘米包装膜 × 0.01 米/厘米 = 22.5 米。</li>
</ul>
<p>不能把“米”和“千克”用一个通用倍率相连。若业务必须按密度或每米重量换算，需要额外且适用该物料版本的物理参数，本包不提供这种推断。</p>
<p>BOM 是做一瓶成品所需的材料。B1
生效到06-20之前：糖浆200克/瓶、膜25厘米/瓶、空瓶1个/瓶。先把单位统一为
0.2千克/瓶、0.25米/瓶和1个/瓶，再乘生产数量。生产90瓶需要18千克糖浆、22.5米膜和90个空瓶。这里用量已经是本实验的标准投入量，不能再随意除一个“成品率”，否则可能重复计损。</p>
<p>B2 从06-20生效，用量改为220克和30厘米，但它到06-15
09:00才可得。08:00为06-21制订计划时，没有“当时已知且在生产日有效”的完整BOM，必须报缺版本，不能回退到已失效B1。</p>
<h3 id="连接膨胀为什么危险">3 连接膨胀为什么危险</h3>
<p>一条销量5箱若连接到两条重叠主数据，就变成两条30瓶。相加得到60瓶，表面上没有空值，结果却错了一倍。连接后应验收“每个输入业务键恰好一个匹配”；BOM
则按“父件+组件”应各一行，不能把B1和B2同时展开。</p>
<h3 id="输入-输出和项目">4 输入 输出和项目</h3>
<p>输入 <code>master.csv</code>、<code>bom.csv</code>。程序
<code>unique_master</code> 检查重叠；<code>convert</code>
检查唯一匹配及原单位；<code>bom_at</code> 按生产日和 cutoff
选择版本。输出 <code>report.json</code> 的 <code>master_examples</code>
与 <code>bom</code>。主表和BOM原文件哈希进入
<code>input_file_hashes</code>，可与本次输入包一同留存。</p>
<p>练习：将5箱改成7箱。答案42瓶。把原单位由box改ea但仍用
<code>L-CASE</code> 主记录，答案不是7瓶，应该得到
<code>UNIT_MISMATCH</code>。复制一行主数据再运行，应该失败
<code>OVERLAPPING_MASTER</code>。复制一个有效BOM组件，应该失败
<code>BOM_JOIN_EXPLOSION</code>。</p>
<p><strong>边界：</strong>
这是一份小型有效期映射，不覆盖真实企业的所有包装层级、称重商品、替代料、产权、序列号或主数据审批系统。</p>
