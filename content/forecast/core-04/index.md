{
  "title": "从感知到模拟反馈的四层合同",
  "description": "从感知到模拟反馈的四层合同：这套补课把同一瓶合成的柠檬茶，从销售记录、订单、仓库、工厂、物料清单一直追到预测、建议单、审批和模拟反馈。读者只需会四则运算、百分数和平方根。每章先手算，再运行程序，最后故意破坏一个输入，看系统有没有拒绝错误。",
  "type": "forecast",
  "unit": "core-04",
  "weight": 84,
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
</details><h2 id="core-04-从感知到模拟反馈的四层合同">core-04
从感知到模拟反馈的四层合同</h2>
<p>覆盖
A02。目标是能沿着一张建议单找回全部输入，不把预测当作已下单。</p>
<h3 id="四层分别回答什么">1 四层分别回答什么</h3>
<p>|层|输入|输出|不允许混淆的边界|
|感知|POS事件、OMS订单、WMS盘点/在途、MES产能、BOM及外部快照|统一单位且带cutoff的数据包|实盘数量不等于可售数量|
|预测|可得POS历史、星期系数、已知情景|F08：未来三天117、117、156瓶|预测销量不等于采购量|
|计划|预测、SS、库存位置、箱规、来源/材料/产能|补210瓶；候选PO60、STO60、WO90|成本最低候选不等于批准|
|模拟执行与反馈|版本锁定且批准的候选|MOCK_ACCEPTED、部分到货、完成、本地守恒账|模拟回执不等于真实系统执行|</p>
<p>完整 <code>asof_bundle</code>
汇集POS、OMS、WMS、MES、天气、竞价、IoT及BOM，摘要只覆盖此数据包；<code>pipeline.input_hash</code>
还覆盖配置参数（含z、箱规与MOQ）和可见快照；<code>plan_input_hash</code>
再覆盖BOM、MES产能、库存及主数据，并进入单据批准详情。<code>input_file_hashes</code>
保存所有CSV/JSON的文件哈希。每一层的真实接口至少应保存：<code>sku</code>、位置、基础单位、目标日期、cutoff、版本、来源业务键、数量、状态、计算方法和输入哈希。上一层升级版本时，下一层不能继续声称自己基于“最新数据”，必须明确采用哪个版本。</p>
<h3 id="从需求到物料的具体数值">2 从需求到物料的具体数值</h3>
<ol type="1">
<li>POS只预测散客渠道三天390瓶，不含OMS独立渠道的30瓶。</li>
<li>WMS可售180瓶，确定在途60瓶。先为OMS保留30瓶，剩余库存位置180+60−30=210瓶。</li>
<li>加入POS误差缓冲28.5788瓶，目标为390+28.5788=418.5788瓶。</li>
<li>净缺418.5788−210=208.5788瓶，按6瓶/箱向上取整得到210瓶。</li>
<li>三来源小规模枚举选PO60、STO60、WO90。WO90对应糖浆18kg、膜22.5m、空瓶90个。</li>
<li>日级可行性另外检查：原在途60瓶约定06-16开门前可用，新210瓶约定06-17开门前可用，OMS30瓶约定06-17交付。06-15结余180−117=63；06-16结余63+60−117=6；06-17结余6+210−156−30=30。三个日末都非负。若把原在途推迟到06-17，06-16会缺54瓶，程序输出BLOCKED_DAILY_SHORTAGE且不模拟派发。</li>
<li>本地收货账只演示新单的增量、尚未扣除未来销量，它使本仓可售从180增加到390瓶；这是新三张单的210瓶到齐。原有在途60瓶仍单列，不能因发送建议就提前入库。若它也按约到齐，预计实物450瓶；保留OMS30瓶后420瓶，略高于POS目标418.5788。</li>
</ol>
<p>日级投影见
<code>calendar_check</code>，到货/预留日偏移见config；它只验证这三天给定计划，并未求解一般多期排程。这里每次相加都在“瓶”这一单位下。18kg糖浆不能直接加进成品390瓶中。</p>
<h3 id="审批与回写怎样追溯">3 审批与回写怎样追溯</h3>
<p><code>orders.csv</code>
的三条单据都有cutoff=08:00、forecast_version=F08、bom_version=B1。模拟适配器收到批准单时只登记
<code>MOCK_ACCEPTED_NO_PHYSICAL_ACTION</code>。真正改变<strong>模拟</strong>库存的是之后的唯一反馈事件。PO60先收到36，状态为部分到货，再收到24，才完成。</p>
<p>回写不是修改原始预测，而是在单据、反馈和库存之间建立引用：哪条建议、哪次审批、哪个回执、多少瓶发生了变化。重放同一个回执，不得再加一遍库存。</p>
<h3 id="项目和答案">4 项目和答案</h3>
<p>运行 <code>python core_lab.py --self-test</code>，打开
<code>orders.csv</code> 与
<code>approval_audit.csv</code>。用计算器验算：180+60+60+90=390；远仓84−60=24；糖浆20−18=2kg；膜24−22.5=1.5m；空瓶100−90=10个。三类单数量合计210，来源成本467元。</p>
<p>练习：有人说“程序运行后库存450，所以确实采购成功了”。答案：错误。390是本地新单的模拟入库，450还假设原在途60按约到达；没有任何真实系统被调用。</p>
<p>故障注入：删除某张单的批准，尝试发送，应失败；重复反馈36瓶，应仍只增加36而不是72；把F11的新数量塞进F08的批准，哈希不匹配，应重新审批。</p>
<p><strong>边界：</strong>
已建立一条离线端到端证据链。没有POS/ERP/WMS/MES真实连接器、正式凭证、真实账户权限或分布式事务保障。日级投影假定按期到货，不保证随机延迟下仍可行。</p>
