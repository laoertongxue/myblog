{
  "title": "四专项：字段、事件与单位字典",
  "description": "四专项：字段、事件与单位字典：所有主键都是虚构标识，所有日期以2025-01-01为第0日。整数日期列的单位是日；*_date 是同一日期的ISO文本。CSV空单元格表示未知、不适用或不可估计，不等于0。行排序不表示允许看到未来，必须使用截止日过滤。",
  "type": "forecast",
  "unit": "specialty-data",
  "weight": 60,
  "outputs": [
    "HTML"
  ]
}

<p class="check">完全模拟的可复现实验，不连接生产。<a href="/forecast/forecast-specialty-projects.zip" download>下载四专项完整工程包（20,000/12,000/10,000/2,000实体）</a>。运行前阅读覆盖data/outputs的说明。固定模拟世界的指标不是企业收益。</p><h2 id="数据字典">数据字典</h2>
<h2 id="通用口径">通用口径</h2>
<p>所有主键都是虚构标识，所有日期以2025-01-01为第0日。整数日期列的单位是<strong>日</strong>；<code>*_date</code>
是同一日期的ISO文本。CSV空单元格表示未知、不适用或不可估计，<strong>不等于0</strong>。行排序不表示允许看到未来，必须使用截止日过滤。</p>
<h3 id="四个-features.csv-的公共字段">四个 <code>features.csv</code>
的公共字段</h3>
<table>
<colgroup>
<col style="width: 33%" />
<col style="width: 33%" />
<col style="width: 33%" />
</colgroup>
<thead>
<tr class="header">
<th>字段</th>
<th>类型/单位</th>
<th>定义及何时可用</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>entity_id</td>
<td>文本主键</td>
<td>PRE/RET/COD/PO前缀加流水号；只用于关联，不作为模型特征</td>
</tr>
<tr class="even">
<td>created_day</td>
<td>整数/日</td>
<td>预售、COD、PO创建日；退货项目指发货日</td>
</tr>
<tr class="odd">
<td>created_date</td>
<td>日期</td>
<td>created_day对应日期</td>
</tr>
<tr class="even">
<td>feature_available_day</td>
<td>整数/日</td>
<td>静态特征首次可用日，生成器设为创建日</td>
</tr>
<tr class="odd">
<td>score_day</td>
<td>整数/日</td>
<td>本次订单初始打分日，等于创建日</td>
</tr>
<tr class="even">
<td>feature_available_at</td>
<td>UTC时间戳</td>
<td>模拟创建日08:00，静态输入已经可得</td>
</tr>
<tr class="odd">
<td>score_at</td>
<td>UTC时间戳</td>
<td>模拟创建日09:00，严格晚于输入可得时刻</td>
</tr>
<tr class="even">
<td>split</td>
<td>枚举</td>
<td>train、validation、test、gap_not_used_for_model_selection</td>
</tr>
<tr class="odd">
<td>synthetic</td>
<td>0/1</td>
<td>全部为1，表示模拟数据</td>
</tr>
</tbody>
</table>
<p>创建日、分块标记和主键用于时间控制或关联，不把未来日期、测试身份或编号顺序拿来拟合业务结果。</p>
<h3 id="预售追加字段">预售追加字段</h3>
<table>
<colgroup>
<col style="width: 33%" />
<col style="width: 33%" />
<col style="width: 33%" />
</colgroup>
<thead>
<tr class="header">
<th>字段</th>
<th>单位/取值</th>
<th>含义</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>sku</td>
<td>SKU00–SKU19</td>
<td>20个虚构SKU；分组hazard模型唯一静态特征</td>
</tr>
<tr class="even">
<td>campaign</td>
<td>C0–C3</td>
<td>虚构活动；生成但当前基线不用</td>
</tr>
<tr class="odd">
<td>units</td>
<td>件，1–3</td>
<td>订单件数，整单取消或发货</td>
</tr>
<tr class="even">
<td>listed_price</td>
<td>元</td>
<td>模拟标价，当前基线不用</td>
</tr>
<tr class="odd">
<td>promised_ship_days</td>
<td>日</td>
<td>固定45日承诺，仅模拟字段，不等于实际发货时长</td>
</tr>
</tbody>
</table>
<p>每单有 <code>independent</code> 与 <code>informative</code>
两种场景。在每个场景里只能出现创建加一个终止事件。没有拆单/部分发货。</p>
<h3 id="退货追加字段">退货追加字段</h3>
<table>
<thead>
<tr class="header">
<th>字段</th>
<th>单位/取值</th>
<th>含义</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>category</td>
<td>CAT0–CAT3</td>
<td>四个虚构品类，决定模拟退货倾向和质检良率</td>
</tr>
<tr class="even">
<td>route</td>
<td>R0–R2</td>
<td>模拟路线；当前基线不使用</td>
</tr>
<tr class="odd">
<td>units</td>
<td>件</td>
<td>固定1件/发货行，因此一行不会部分退货</td>
</tr>
<tr class="even">
<td>listed_price</td>
<td>元</td>
<td>模拟标价，当前基线不使用</td>
</tr>
</tbody>
</table>
<p>真实“一行多件、部分退货、换货后再退”等流程没有实现，不应把本包的一行一件口径误搬过去。</p>
<h3 id="cod追加字段">COD追加字段</h3>
<table>
<thead>
<tr class="header">
<th>字段</th>
<th>单位/取值</th>
<th>含义</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>route</td>
<td>R0–R2</td>
<td>计划路线，类别编码为两个0/1输入</td>
</tr>
<tr class="even">
<td>distance_km</td>
<td>千米，5–250</td>
<td>创建时已知的模拟距离，建模除以100</td>
</tr>
<tr class="odd">
<td>units</td>
<td>件，1–4</td>
<td>包裹件数，整包签收或拒收，建模除以4</td>
</tr>
<tr class="even">
<td>cod_amount_yuan</td>
<td>元</td>
<td>79×件数，当前模型不用，避免与件数重复</td>
</tr>
<tr class="odd">
<td>planned_delivery_days</td>
<td>日</td>
<td>计划配送时长，建模除以10；不是实际结果</td>
</tr>
</tbody>
</table>
<p>没有姓名、手机号、地址、个人信用数据。第140日后生成拒收风险时logit增加0.25，作为明确的时间漂移压力测试。真实发生的送达日、拒收原因不可作发货前输入。</p>
<h3 id="po追加字段">PO追加字段</h3>
<table>
<thead>
<tr class="header">
<th>字段</th>
<th>单位/取值</th>
<th>含义</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>supplier</td>
<td>SUP00–SUP09</td>
<td>10个虚构供应商，分组KM使用</td>
</tr>
<tr class="even">
<td>material</td>
<td>MAT00–MAT19</td>
<td>20种虚构物料，当前基线不用</td>
</tr>
<tr class="odd">
<td>ordered_units</td>
<td>模拟件，50–500</td>
<td>PO订购数量，每条PO一种物料</td>
</tr>
<tr class="even">
<td>promised_lead_days</td>
<td>日</td>
<td>12+2×供应商编号，创建时已知的模拟承诺</td>
</tr>
</tbody>
</table>
<p>所有物料为了教学统一用模拟“件”，不能当作现实公斤、米、箱直接相加。总收货等于订购量时才叫“收齐”，不以首次到货为完成。</p>
<h2
id="events.csv四项目完全相同的列"><code>events.csv</code>：四项目完全相同的列</h2>
<table>
<thead>
<tr class="header">
<th>字段</th>
<th>类型/单位</th>
<th>含义</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>entity_id</td>
<td>文本外键</td>
<td>对应features主键</td>
</tr>
<tr class="even">
<td>scenario</td>
<td>枚举</td>
<td>预售为independent/informative，其余为base</td>
</tr>
<tr class="odd">
<td>event_day</td>
<td>整数/日</td>
<td>该事件真正发生日</td>
</tr>
<tr class="even">
<td>event_date</td>
<td>日期</td>
<td>event_day对应日期</td>
</tr>
<tr class="odd">
<td>sequence</td>
<td>非负整数</td>
<td>同实体内事件顺序；同一天也按它排序</td>
</tr>
<tr class="even">
<td>event_type</td>
<td>枚举</td>
<td>见下方事件列表</td>
</tr>
<tr class="odd">
<td>units</td>
<td>正整数/件</td>
<td>本事件涉及数量；PO received是本次增量，不是累计</td>
</tr>
</tbody>
</table>
<h3 id="事件类型及数量含义">事件类型及数量含义</h3>
<ul>
<li>预售：<code>created</code>建单；<code>cancelled</code>第1–59日自然取消；<code>shipped</code>发货；<code>forced_cancel</code>第60日规则关单。所有事件涉及整单件数。</li>
<li>退货：<code>shipped</code>发出；<code>delivered</code>送达；<code>return_requested</code>申请；<code>warehouse_received</code>退到仓；<code>quality_passed</code>/<code>quality_failed</code>质检结果二选一；仅合格件次日出现<code>restocked</code>可售上架。各事件1件。仅质检合格但尚未上架也不算现有可售。</li>
<li>COD：<code>created</code>建单；次日<code>shipped</code>；<code>delivered_paid</code>与<code>refused</code>二选一；拒收后可出现<code>warehouse_received</code>、质检、合格次日<code>restocked</code>。件数为整包数量。</li>
<li>PO：<code>ordered</code>订购；一个或多个<code>received</code>实际部分收货。模拟没有取消事件。尚未收齐就是订购减累计已收，不用未来潜在完成日填补。</li>
</ul>
<h2
id="oracle_do_not_train.csv禁止建模的真相表"><code>ORACLE_DO_NOT_TRAIN.csv</code>：禁止建模的真相表</h2>
<p>所有表含entity_id和notice，notice明确写明不能作特征。预售另含scenario、latent_natural_cancel_age（1–59；空表示59日前没有自然取消）、latent_frailty（未观测风险倍率）、latent_ship_age（潜在发货年龄）。退货含true_return_probability；COD含true_refusal_probability；PO含latent_complete_age（潜在收齐日龄，结构性未完成为空）和structurally_unfilled（0/1）。</p>
<p>模拟器知道结构性未完成，不代表模型在任何观察截止日知道。模型只能看到未完成和等待时间。当前评估只有预售曲线诊断读取oracle，其余oracle附带便于课堂审计，未用于建模。</p>
<h2 id="重建标签公共字段">重建标签公共字段</h2>
<p><code>as_of_day</code>：本行标签观察截止日；<code>observed_age=as_of_day-created_day</code>。<code>status</code>是截止时最近事件或pending。<code>censored=1</code>表示截止时未见终点，不是结局0。标签文件可同时包含features列，仍须坚持特征白名单。</p>
<ul>
<li>预售：<code>exit_age</code>终止事件年龄，未结束为空；<code>status</code>区分自然取消、发货、强制取消、等待。</li>
<li>退货：<code>label_mature</code>是否满30日；<code>returned</code>申请已发生为1，未申请且成熟为0，未成熟为空；<code>restocked</code>已上架为1，成熟未上架或已质检失败为0，其余空。<code>return_requested_age</code>、<code>warehouse_received_age</code>、<code>quality_passed_age</code>、<code>quality_failed_age</code>、<code>restocked_age</code>为自发货起日龄，事件未发生则空。</li>
<li>COD：<code>refused</code>拒收1、已签收付款0、未决空；<code>restocked</code>可售回流1、签收或质检失败0、其他空；<code>label_mature</code>满30日标记。</li>
<li>PO：<code>ordered_units</code>订购；<code>received_units</code>累计已收；<code>outstanding_units</code>未收；<code>completed</code>收齐0/1；<code>complete_age</code>收齐时长，未收齐空。<code>observed_age</code>是随访长度，已完成样本的事件时长仍取complete_age。</li>
</ul>
<h2 id="关键输出字段">关键输出字段</h2>
<h3 id="预售">预售</h3>
<ul>
<li><code>at_risk_start</code>：当天开始仍可能自然取消的订单数；<code>natural_cancelled</code>、<code>shipped</code>、<code>forced_cancelled</code>、<code>right_censored</code>分别退出；<code>at_risk_next</code>为相减后的下一天风险集。</li>
<li><code>raw_hazard</code>：当天自然取消/当天风险集；<code>smoothed_hazard</code>：向总体收缩的条件概率；第60日这两列为空。</li>
<li><code>no_shipping_natural_survival</code>：仅自然取消hazard的连乘，依赖删失假设，不是实际等待池比例。</li>
<li><code>conditional_natural_survival</code>：S(b)/S(a)，其中b最多59；<code>natural_survival_supported_through_age</code>明确支持到哪天。</li>
<li><code>day60_policy_applies</code>：7日目标是否跨过强关日；<code>expected_waiting_units_if_no_shipping</code>为无发货情景期待件数，跨强关日记0，不等于真实履约需求。</li>
</ul>
<h3 id="退货">退货</h3>
<ul>
<li><code>p_return</code>：最终申请退货概率；<code>conditional_quality_yield</code>：退回条件下可售比例；<code>p_eventual_restock</code>为两者乘积。</li>
<li><code>expected_supply_not_on_hand</code>：预测供应，不是实物库存。</li>
<li><code>stage</code>：当前terminal/no_request/in_transit/qc/putaway；<code>analogue_count</code>：同状态、等待条件的历史路径数；不足时<code>pooled_fallback=1</code>表示跨品类回退。</li>
<li><code>expected_restock_units</code>：目标日预期可售回流；空值表示没有历史支持，不强记0；本次运行会报告unsupported_entities。</li>
<li><code>fresh_food_no_resale_scenario_units</code>：不可再售食品情景，恒为0。</li>
</ul>
<h3 id="cod">COD</h3>
<ul>
<li><code>raw_probability</code>/<code>calibrated_probability</code>/<code>baseline_probability</code>：未校准逻辑回归、验证集截距校准后、训练均值基线拒收概率。</li>
<li><code>review_suggestion_only</code>：是否建议人工复核，没有执行任何订单动作。</li>
<li><code>expected_net_sales_units</code>：件数×(1−拒收概率)，不影响当前出库。</li>
<li>校准表<code>n</code>是该概率组样本量；<code>mean_prediction</code>与<code>observed_fraction</code>应一起看。空组这两列为空。</li>
<li>成本表<code>simulated_cost_yuan</code>是假设复核有效率后的模拟成本，不是已实现收入或利润。</li>
<li>库存表<code>on_hand</code>现有可售、<code>outbound</code>出库在途、<code>refused_returning</code>拒收退运、<code>in_qc</code>待质检/待上架、<code>scrapped</code>报损；<code>delivered_paid</code>已签收付款。</li>
</ul>
<h3 id="po">PO</h3>
<ul>
<li><code>predicted_full_receipt_p50_days</code>/<code>p90_days</code>：预测收齐时间分位数；无法识别尾部留空，<code>p90_estimable=0</code>。</li>
<li><code>coverage_lower</code>：已确认在预测天数内收齐的数量/有预测样本数；<code>coverage_upper</code>再加截止时无法判定的样本数。上下界不是置信区间。</li>
<li><code>predictions_available</code>：分母；须与总n一起报告，不能只展示容易预测的部分。</li>
<li><code>pinball_completed_only</code>：仅已收齐样本的分位数损失，存在完成样本选择偏差。不能用它单独宣称KM优于所有模型。</li>
<li>KM表<code>at_risk</code>是该日之前未完成且未删失的PO数；<code>completed</code>、<code>censored</code>是当天数量；<code>survival_not_fully_received</code>是尚未收齐概率估计。</li>
</ul>
