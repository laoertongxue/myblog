# 输入与输出数据字典

全部 CSV UTF-8、逗号分隔、有表头；列名与顺序必须完全一致。表不能为空，单元格不可空，不接受多余列。键不重复，数值使用0至1,000,000的普通十进制文本，最多6位小数，无指数；权重严格大于0。每文件最多1MiB/1000行。文件均为全新教学构造，不来自生产系统。

## 1. newsvendor.csv

| 字段 | 含义 |
|---|---|
| demand | 单周期需求件数，当前80、100、120、140；记录键 |
| weight | 情景相对权重，程序按总权重归一化；当前各1 |

## 2. newsvendor_config.csv

`key,value`，每个参数一行，不允许未知键或缺键。

| key | 单位及意义 |
|---|---|
| underage_cost | 每少供1件的缺货成本，6成本单位/件 |
| overage_cost | 每剩余1件的过量成本，2成本单位/件 |
| candidate_start | 候选起点80件 |
| candidate_stop | 候选上限160件（包含在枚举内） |
| candidate_step | 候选步长20件，严格大于0 |

两项成本均须严格大于0；零成本端点不在本练习支持范围。这些边际成本不是售价，已假设残值、缺货代价等被正确折算。成本仅用于报童例，不直接套入食材例。

## 3. paths.csv

| 字段 | 含义 |
|---|---|
| path | 联合情景唯一ID |
| day1/day2/day3 | 同一条路径连续三日需求，kg；不能把不同路径拼成一条未来 |
| weight | 整条路径的相对权重，当前10条等权 |

各日只有一条路径为30，其余为10；三个高值在不同路径。该表独立于禾味冻结需求表，虽然同为kg单位，也不能当作同一套情景。

## 4. demand.csv

| 字段 | 含义 |
|---|---|
| day | 从1开始连续整数，保护期内每天一条，无缺日或重复 |
| kg | A店SKU01事先冻结的当日计划需求，kg；允许小数 |

## 5. batches.csv

| 字段 | 含义 |
|---|---|
| batch | 唯一批次ID；`new_order` 为程序新单保留名，不可输入 |
| source_type | initial表示决策起点现货；transit表示指定日新到货 |
| arrival_day | 可用起始日，日初；initial必须为1，作为起点现货而非新到货 |
| expiry_day | 仍可用的最后一天，于该日日终报废 |
| kg | 批次数量，kg |

要求 1 ≤ arrival_day ≤ expiry_day ≤ H。保护期之外的批次不静默忽略，而是拒绝输入；扩展期外批次前需要扩展模型和测试。初始10kg第1日日终过期，旧在途8kg第3日日初到、当日日终到期。采购新单的数量由枚举生成，不写回此表。

## 6. inventory_config.csv

同样使用 `key,value`。

| key | 单位与含义 |
|---|---|
| lead_time | 完整日，整数，当前1 |
| review_period | 检查周期日数，正整数，当前2；两者之和必须等于需求覆盖天数 |
| new_arrival_day | 新单日初到货日，必须为1+lead_time，当前2 |
| new_expiry_day | 新单日终到期日，当前3，因此可用第2、3日 |
| pack_kg | 正包规kg，当前5 |
| moq_kg | 正订单最小起订量kg，当前10；零订单豁免 |
| capacity_kg | 严格正的可用物理容量kg，当前18；到货后、服务前检查全部残量与新到货 |
| candidate_max_kg | 枚举上限kg，当前30，必须是包规整数倍 |

## 7. apparel.csv

`key,value`，只描述一个款、一个码，期望情景数量而非概率分位数。

| key | 单位与含义 |
|---|---|
| pending_orders | 当前待发订单，100单；不含 additional_demand |
| pieces_per_order | 每单件数，1件/单 |
| conditional_retention | 已知当前待发状态下的未来留存比例，0.8，范围[0,1] |
| additional_demand | 另新增需求20件，明确不包含当前100单 |
| finished_stock | 可用成衣15件 |
| net_bom_m | 每件净耗2米/件 |
| yield | 材料利用率0.95，范围(0,1]，毛用料=净用料/利用率 |
| material_stock_m | 可用原料50米 |
| timely_transit_m | 可在用料截止前投入的在途30米 |
| late_transit_m | 晚到25米，仅用于展示，不能扣减当前缺口 |
| roll_m | 整卷长度20米，严格正；最终采购向上取整 |
| moq_m | 正采购最小40米，缺口为0时不强制采购 |
| production_capacity_pieces | 截止前可生产70件，仅报告产能差，不反向减少目标备料 |

## 输出字段

- `summary.json`：报童分位数与枚举最优并列集；每日P90和总需求P90；选中库存候选及naive总量公式；服装期望件数、待产件数、毛材料、缺口、采购米数、晚到排除量及产能缺口。
- `newsvendor.csv`：q（件）、expected_shortage/expected_surplus（件）、expected_cost（成本单位）。均为按输入权重计算的期望。
- `inventory_candidates.csv`：q（kg）；feasible（True/False）；reasons（`pack_or_moq` 或 `capacity_dayN`）；lost_kg、expired_kg、closing_kg（保护期累计失销、累计过期、末日库存）。
- `inventory_ledger.csv`：q（kg），day；opening_kg（第1日为起点现货，其余为上日末可用库存）；arrival_kg；peak_kg（到货后服务前占用）；demand_kg；served_kg；lost_kg；expired_kg；closing_kg；fefo_allocations（`批次:扣减kg`，按到期日、同到期批次ID排序，分号分隔）。初始库存通过source_type=initial识别，计入第1日opening_kg=10，第1日arrival_kg=0；仍与新到货共同接受服务前容量检查。候选不可行时账本仅为诊断，不代表执行。

每日日账满足 opening + arrival = served + expired + closing，以及 demand = served + lost。期望情景、分位数、确定性计划分别有不同语义，不可混用单位或合并评价。

## 新增实验及资源边界

`inputs_expiry_pressure/` 与基准输入结构完全相同，唯一数值差别为 `demand.csv` 第1日kg=6，输出保存在 `results_expiry_pressure/`。两套均为事先冻结的计划情景，不是实际实绩。

库存最多366日；单个报童/库存枚举最多1000候选；库存候选×天数最多100000行。输入和库存账本使用60位有效数字Decimal，CSV数值最大6位小数，避免此有限输入域中微小步长加法停滞。分位数、成本并列和包规上整使用Fraction精确比例；服装毛料/缺口保留精确分数直到上整。循环小数只在JSON/CSV展示时转换为60位Decimal。

`summary.json` 新增 `inventory_data_semantics` 声明冻结计划语义、`apparel_capacity_plan` 记录产能内计划。`apparel_plans.csv` 的 `plan` 区分完整目标备料与产能内情景；`production_pieces` 为相应方案待产量，`gross_material_m` 为毛用料，`shortage_m` 为及时净缺口，`purchase_m` 为MOQ/卷长取整后采购量，`capacity_or_unmet_gap_pieces` 为完整目标的产能差或产能内方案未覆盖情景量。二者在本例均为15件，但不等同履约实绩。

所有 path/batch 文本ID必须以ASCII字母开头，其余仅ASCII字母、数字、下划线或短横线，最多64字符；`new_order` 禁作输入批次ID。该白名单也防止导出CSV出现由用户输入ID形成的表格公式。

`inventory_enumeration` 输出起点、上限、步长和“仅限枚举可行集合”的选择范围。若上限低于容量可容纳的最大合规格订单量，并且该量满足MOQ，则 `potentially_truncated=true` 并附警告。该容量上界未扣已有占用，只用于保守提示漏搜可能，不是一定可行的订单建议。
