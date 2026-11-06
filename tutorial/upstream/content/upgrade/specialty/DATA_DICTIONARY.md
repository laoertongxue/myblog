# 数据字典

## 通用口径

所有主键都是虚构标识，所有日期以2025-01-01为第0日。整数日期列的单位是**日**；`*_date` 是同一日期的ISO文本。CSV空单元格表示未知、不适用或不可估计，**不等于0**。行排序不表示允许看到未来，必须使用截止日过滤。

### 四个 `features.csv` 的公共字段

| 字段 | 类型/单位 | 定义及何时可用 |
|---|---|---|
| entity_id | 文本主键 | PRE/RET/COD/PO前缀加流水号；只用于关联，不作为模型特征 |
| created_day | 整数/日 | 预售、COD、PO创建日；退货项目指发货日 |
| created_date | 日期 | created_day对应日期 |
| feature_available_day | 整数/日 | 静态特征首次可用日，生成器设为创建日 |
| score_day | 整数/日 | 本次订单初始打分日，等于创建日 |
| feature_available_at | UTC时间戳 | 模拟创建日08:00，静态输入已经可得 |
| score_at | UTC时间戳 | 模拟创建日09:00，严格晚于输入可得时刻 |
| split | 枚举 | train、validation、test、gap_not_used_for_model_selection |
| synthetic | 0/1 | 全部为1，表示模拟数据 |

创建日、分块标记和主键用于时间控制或关联，不把未来日期、测试身份或编号顺序拿来拟合业务结果。

### 预售追加字段

| 字段 | 单位/取值 | 含义 |
|---|---|---|
| sku | SKU00–SKU19 | 20个虚构SKU；分组hazard模型唯一静态特征 |
| campaign | C0–C3 | 虚构活动；生成但当前基线不用 |
| units | 件，1–3 | 订单件数，整单取消或发货 |
| listed_price | 元 | 模拟标价，当前基线不用 |
| promised_ship_days | 日 | 固定45日承诺，仅模拟字段，不等于实际发货时长 |

每单有 `independent` 与 `informative` 两种场景。在每个场景里只能出现创建加一个终止事件。没有拆单/部分发货。

### 退货追加字段

| 字段 | 单位/取值 | 含义 |
|---|---|---|
| category | CAT0–CAT3 | 四个虚构品类，决定模拟退货倾向和质检良率 |
| route | R0–R2 | 模拟路线；当前基线不使用 |
| units | 件 | 固定1件/发货行，因此一行不会部分退货 |
| listed_price | 元 | 模拟标价，当前基线不使用 |

真实“一行多件、部分退货、换货后再退”等流程没有实现，不应把本包的一行一件口径误搬过去。

### COD追加字段

| 字段 | 单位/取值 | 含义 |
|---|---|---|
| route | R0–R2 | 计划路线，类别编码为两个0/1输入 |
| distance_km | 千米，5–250 | 创建时已知的模拟距离，建模除以100 |
| units | 件，1–4 | 包裹件数，整包签收或拒收，建模除以4 |
| cod_amount_yuan | 元 | 79×件数，当前模型不用，避免与件数重复 |
| planned_delivery_days | 日 | 计划配送时长，建模除以10；不是实际结果 |

没有姓名、手机号、地址、个人信用数据。第140日后生成拒收风险时logit增加0.25，作为明确的时间漂移压力测试。真实发生的送达日、拒收原因不可作发货前输入。

### PO追加字段

| 字段 | 单位/取值 | 含义 |
|---|---|---|
| supplier | SUP00–SUP09 | 10个虚构供应商，分组KM使用 |
| material | MAT00–MAT19 | 20种虚构物料，当前基线不用 |
| ordered_units | 模拟件，50–500 | PO订购数量，每条PO一种物料 |
| promised_lead_days | 日 | 12+2×供应商编号，创建时已知的模拟承诺 |

所有物料为了教学统一用模拟“件”，不能当作现实公斤、米、箱直接相加。总收货等于订购量时才叫“收齐”，不以首次到货为完成。

## `events.csv`：四项目完全相同的列

| 字段 | 类型/单位 | 含义 |
|---|---|---|
| entity_id | 文本外键 | 对应features主键 |
| scenario | 枚举 | 预售为independent/informative，其余为base |
| event_day | 整数/日 | 该事件真正发生日 |
| event_date | 日期 | event_day对应日期 |
| sequence | 非负整数 | 同实体内事件顺序；同一天也按它排序 |
| event_type | 枚举 | 见下方事件列表 |
| units | 正整数/件 | 本事件涉及数量；PO received是本次增量，不是累计 |

### 事件类型及数量含义

- 预售：`created`建单；`cancelled`第1–59日自然取消；`shipped`发货；`forced_cancel`第60日规则关单。所有事件涉及整单件数。
- 退货：`shipped`发出；`delivered`送达；`return_requested`申请；`warehouse_received`退到仓；`quality_passed`/`quality_failed`质检结果二选一；仅合格件次日出现`restocked`可售上架。各事件1件。仅质检合格但尚未上架也不算现有可售。
- COD：`created`建单；次日`shipped`；`delivered_paid`与`refused`二选一；拒收后可出现`warehouse_received`、质检、合格次日`restocked`。件数为整包数量。
- PO：`ordered`订购；一个或多个`received`实际部分收货。模拟没有取消事件。尚未收齐就是订购减累计已收，不用未来潜在完成日填补。

## `ORACLE_DO_NOT_TRAIN.csv`：禁止建模的真相表

所有表含entity_id和notice，notice明确写明不能作特征。预售另含scenario、latent_natural_cancel_age（1–59；空表示59日前没有自然取消）、latent_frailty（未观测风险倍率）、latent_ship_age（潜在发货年龄）。退货含true_return_probability；COD含true_refusal_probability；PO含latent_complete_age（潜在收齐日龄，结构性未完成为空）和structurally_unfilled（0/1）。

模拟器知道结构性未完成，不代表模型在任何观察截止日知道。模型只能看到未完成和等待时间。当前评估只有预售曲线诊断读取oracle，其余oracle附带便于课堂审计，未用于建模。

## 重建标签公共字段

`as_of_day`：本行标签观察截止日；`observed_age=as_of_day-created_day`。`status`是截止时最近事件或pending。`censored=1`表示截止时未见终点，不是结局0。标签文件可同时包含features列，仍须坚持特征白名单。

- 预售：`exit_age`终止事件年龄，未结束为空；`status`区分自然取消、发货、强制取消、等待。
- 退货：`label_mature`是否满30日；`returned`申请已发生为1，未申请且成熟为0，未成熟为空；`restocked`已上架为1，成熟未上架或已质检失败为0，其余空。`return_requested_age`、`warehouse_received_age`、`quality_passed_age`、`quality_failed_age`、`restocked_age`为自发货起日龄，事件未发生则空。
- COD：`refused`拒收1、已签收付款0、未决空；`restocked`可售回流1、签收或质检失败0、其他空；`label_mature`满30日标记。
- PO：`ordered_units`订购；`received_units`累计已收；`outstanding_units`未收；`completed`收齐0/1；`complete_age`收齐时长，未收齐空。`observed_age`是随访长度，已完成样本的事件时长仍取complete_age。

## 关键输出字段

### 预售

- `at_risk_start`：当天开始仍可能自然取消的订单数；`natural_cancelled`、`shipped`、`forced_cancelled`、`right_censored`分别退出；`at_risk_next`为相减后的下一天风险集。
- `raw_hazard`：当天自然取消/当天风险集；`smoothed_hazard`：向总体收缩的条件概率；第60日这两列为空。
- `no_shipping_natural_survival`：仅自然取消hazard的连乘，依赖删失假设，不是实际等待池比例。
- `conditional_natural_survival`：S(b)/S(a)，其中b最多59；`natural_survival_supported_through_age`明确支持到哪天。
- `day60_policy_applies`：7日目标是否跨过强关日；`expected_waiting_units_if_no_shipping`为无发货情景期待件数，跨强关日记0，不等于真实履约需求。

### 退货

- `p_return`：最终申请退货概率；`conditional_quality_yield`：退回条件下可售比例；`p_eventual_restock`为两者乘积。
- `expected_supply_not_on_hand`：预测供应，不是实物库存。
- `stage`：当前terminal/no_request/in_transit/qc/putaway；`analogue_count`：同状态、等待条件的历史路径数；不足时`pooled_fallback=1`表示跨品类回退。
- `expected_restock_units`：目标日预期可售回流；空值表示没有历史支持，不强记0；本次运行会报告unsupported_entities。
- `fresh_food_no_resale_scenario_units`：不可再售食品情景，恒为0。

### COD

- `raw_probability`/`calibrated_probability`/`baseline_probability`：未校准逻辑回归、验证集截距校准后、训练均值基线拒收概率。
- `review_suggestion_only`：是否建议人工复核，没有执行任何订单动作。
- `expected_net_sales_units`：件数×(1−拒收概率)，不影响当前出库。
- 校准表`n`是该概率组样本量；`mean_prediction`与`observed_fraction`应一起看。空组这两列为空。
- 成本表`simulated_cost_yuan`是假设复核有效率后的模拟成本，不是已实现收入或利润。
- 库存表`on_hand`现有可售、`outbound`出库在途、`refused_returning`拒收退运、`in_qc`待质检/待上架、`scrapped`报损；`delivered_paid`已签收付款。

### PO

- `predicted_full_receipt_p50_days`/`p90_days`：预测收齐时间分位数；无法识别尾部留空，`p90_estimable=0`。
- `coverage_lower`：已确认在预测天数内收齐的数量/有预测样本数；`coverage_upper`再加截止时无法判定的样本数。上下界不是置信区间。
- `predictions_available`：分母；须与总n一起报告，不能只展示容易预测的部分。
- `pinball_completed_only`：仅已收齐样本的分位数损失，存在完成样本选择偏差。不能用它单独宣称KM优于所有模型。
- KM表`at_risk`是该日之前未完成且未删失的PO数；`completed`、`censored`是当天数量；`survival_not_fully_received`是尚未收齐概率估计。
