# D16 固定批量、日末触发实践包

Python 3.10+，只用标准库，不依赖仓库其他目录。解压后进入本目录：

```bash
python3 run.py
python3 -m unittest -v
shasum -a 256 -c MANIFEST.sha256
```

也可从任意工作目录执行 `python3 /绝对路径/practice/run.py` 和 `python3 -m unittest discover -s /绝对路径/practice -v`。结果不含运行时钟，输出字节确定；测试的 CLI 扰动只写临时副本，不修改冻结输入或已发布结果。Windows 可用 `python` 替代 `python3`，若无 shasum，输入与结果哈希仍由脚本和测试核验。

## 只做七日机制测试

这不是经营回测、参数优化或未来28天测试。两条需求、日期、订单及身份都是教学模拟，原样复制D15的七日需求和初始状态；不读取D9 sealed，不使用原测试段，不复用预测结果。四组参数在首次生成结果前写入策略卡和冻结JSON并记录哈希，目的只是观察规则如何改变逐日订单。这个本地顺序不是第三方预注册或不可否认的外部时间证明。没有成本、损耗、资金约束、置信区间，也不从七天推导长期服务水平、最优Q/r、节约金额或业务改善。

- **禾味**：虚构两店八SKU背景中的A店SKU01一条记录，单位kg（公斤）。其他15条店×SKU组合没有生成或评估。初始OH=12、初始在途8于day2到，L=2；需求 `[7,9,8,4,5,6,3]`。比较Q=6/r=10与Q=12/r=10。
- **匿名服装**：一个终端单SKU独立沙盘，单位pieces（件）。初始OH=6、初始在途4于day1到，L=1；需求 `[5,8,4,7,3,6,2]`。比较Q=6/r=8与Q=12/r=8。不是对实际工厂在制、生产交期或欠交规则的判断，也不产生排产指令。
- 两条需求都完整给定，不以销量代替被截断的真实需求；公斤与件绝不合并统计。日期2026-01-01至2026-01-07只是教学标记。

## 冻结合同与生产边界

每日：**日初全量准时到货 → 当日需求及即时履约/失销 → 日末一次复核、最多一张新单**。

- OH为当前可用现货，OO为已确认未到货订单；本例失销不累积欠交，IP=OH+OO。
- 到货从OO移出，同量加入OH。到货本身不改变IP。
- served=min(到货后OH,demand)，lost_sales=demand−served。没有负现货；新单不能满足当天需求。
- 日末下单前IP≤r时下固定Q，否则0。等号触发，不是只在IP=r时触发。
- 这是每日一次复核，不是连续复核。一天内需求可能使IP从13下穿到4，不能假设总在r处下单，也不能假设订后IP=r+Q。
- 订后IP仍≤r也不循环追单：孤立例IP=3、r=10、Q=6，单次仅下6，订后IP=9，当天停止。禾味Q6的day2订后IP=10，也不会再下第二单。
- L是下单之后完整等待日数，arrival_day=placed_day+L+1。L=2时t日末单在t+3日初可用；L=0也是次日日初。初始订单的placed_day=-1表示窗口前下单。
- 期末未到货逐笔保留，不强制清空，不推断窗口外无成本。
- `order_qr(on_hand,on_order,fixed_quantity,reorder_point)`是对已验证Decimal状态的纯函数，仅返回0或Q；重复调用会重复返回同一个Q，并不提供业务幂等性。模拟器以唯一连续day循环每个策略一次，并使用稳定订单键；跨进程重试、数据库唯一约束及幂等写入没有实现，不能把本包当生产防重系统。
- 每份输出文件是一次独立策略运行。订单ID只在这次策略运行内唯一；跨策略合并时必须带上文件所标识的strategy，不可只按order_id联表。

不支持部分到货、取消、退货、损耗、质检冻结、预留、调拨、欠交、随机交期、产能或BOM。不支持字段和partial/cancelled事件拒绝输入；扩展真实业务必须另建事件模型和测试。

## 文件与冻结校验

- `data/hewei-demand.csv`、`data/apparel-demand.csv`：原始七日教学需求，与D15对应文件字节相同。
- `POLICY_CARD.md`：给读者的冻结策略卡。
- `frozen_policy.json`：合同说明与四组固定参数；本包不另有可变参数入口。
- `source_manifest.json`：上述四文件的固定SHA-256。其本身的SHA-256固定写在run.py中，防止改输入后只改manifest就悄悄放行。
- `run.py`：先核验固定manifest与全部输入哈希，通过后才输出；不自动重写输入哈希。实现纯规则、仿真、独立事件重放及逐日守恒审计；审计不用assert，`python -O`不关闭它。
- `test_inventory.py`：48项单元测试，覆盖两案手算、等号与阈值两侧、下穿、单单限制、事件先后、收货移出在途、失销、未来扰动/前缀不变、等比例变形、零需求、L0、多单同日到货、非法bool/NaN/负/缺日/身份单位、损坏事件、尾单、冻结篡改及独立确定性CLI。
- `results/<strategy>-ledger.csv`：四份逐日账；strategy为hewei-q6、hewei-q12、apparel-q6、apparel-q12。
- `results/<strategy>-order-events.csv`：四份完整订单事件；无事件时仍写表头。
- `results/summary.json`：每策略累计、期末状态、逐笔尾单及输入哈希。
- `results/output_hashes.json`：九份结果文件的SHA-256，不自包含，不把其他误放的文件纳入输出。
- `MANIFEST.sha256`：完整实践包SHA-256，不自包含，不含__pycache__。输入或规则变化时应保留原包，另建实验并审查、冻结新输入，不能刷新本实验固定哈希冒充同一次结果。哈希用来检测变化，不是防止恶意同时篡改代码和所有清单的数字签名。

数值输入限0～1,000,000；kg最多三位小数，pieces为整数；Q必须大于0，r可为0。运算用Decimal精确加减，累计值不受单条输入上限限制。days为1～1000整数，L为0～1000整数，不接受bool；本实验固定days=7。日期连续；day、身份及单位不匹配、重复订单、非有限数、负数和缺失/额外字段均拒绝。边界测试会在内存或临时副本构造其他参数，这些不是已发布四组结果或额外的参数搜索。

## 全部字段说明

原始需求CSV：`case`案例标识，`series`实体/SKU，`unit`数量单位，`day`从1起的日序，`date`日历日期，`demand`当日完整教学需求（对应unit）。

冻结配置：`case/series/unit`同上；`start_date`起始日期；`days`日数；`initial_on_hand`窗口起点到货前现货（unit）；`lead_time`完整等待日数；`fixed_quantity`固定批量Q（unit）；`reorder_point`日末阈值r（unit）；`shortage_mode`固定lost_sales；`initial_orders`窗口开始前已下、尚未收货的订单列表。列表的`order_id`、`placed_day`、`arrival_day`、`quantity`与事件字段相同，case/series/unit必须匹配配置。

逐日台账字段中，除身份、日序和日期外，以下数量都使用该行unit：

| 字段 | 时点和含义 |
|---|---|
| opening_on_hand / opening_on_order | 当日日初收货之前的现货/在途 |
| arrivals | 当日日初实际收到的数量 |
| available_before_demand | 当日收货之后、需求之前的可用现货 |
| demand / served / lost_sales | 当日需求/履约/失销 |
| closing_on_hand | 需求处理后的日末现货，下单不会增加它 |
| on_order_before_order | 到货已移出、日末新单尚未加入的在途 |
| ip_before_order | closing_on_hand + on_order_before_order |
| order_quantity | 当日日末新单量，严格为0或Q |
| on_order_after_order | on_order_before_order + order_quantity |
| ip_after_order | ip_before_order + order_quantity |

事件CSV：`order_id`本策略运行内唯一键；`case/series/unit`身份与数量单位；`placed_day`真实下单日序；`arrival_day`预计且本例实际到货日序；`quantity`订单完整数量（unit）；`event_day`事件被记入模拟的日序；`event`为initial_open（day0登记既有未到货单，不是day0下单）、placed（日末新单）、arrival（日初实际收货）。初始登记、下单、到货有独立事件行，汇总时不可把所有事件行的quantity相加当采购量。

汇总：`run_id`实验身份；`boundary`解释边界；`strategies`按策略分别保存case/series/unit/days、fixed_quantity/reorder_point/lead_time；`total_demand/total_served/total_lost_sales/total_arrivals/total_new_orders`分别累计需求、履约、失销、窗口内到货、新下单量（对应unit）；`order_count`新订单张数，不含初始单；`closing_on_hand/closing_on_order/closing_inventory_position`为最后一日下单后状态（unit）；`closing_pending_orders`逐笔保留order_id、placed_day、arrival_day、quantity；`input_sha256`与`source_manifest_sha256`标识冻结输入，无业务单位。

## 手算结果与尾部在途

| 策略 | 单位 | 需求 | 履约 | 失销 | 新单张数 | 新单量 | 窗口内到货 | 末OH | 末OO | 末IP |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 禾味Q6/r10 | kg | 42 | 32 | 10 | 4 | 24 | 20 | 0 | 12 | 12 |
| 禾味Q12/r10 | kg | 42 | 32 | 10 | 2 | 24 | 20 | 0 | 12 | 12 |
| 服装Q6/r8 | pieces | 35 | 32 | 3 | 6 | 36 | 28 | 2 | 12 | 14 |
| 服装Q12/r8 | pieces | 35 | 32 | 3 | 3 | 36 | 28 | 2 | 12 | 14 |

禾味Q6尾单是day5下6kg于day8到、day6下6kg于day9到；Q12尾单是day5下12kg于day8到。服装Q6尾单是day6下6件于day8到、day7下6件于day9到；Q12尾单是day6下12件于day8到。

同一案例两策略七日合计恰好相同，订单节奏、部分日末现货和尾单日期不同。这不说明任意轨迹都相同，也不证明大批量更优；未给订单固定成本或持有成本，不能把张数减少直接写成经营节约。

守恒：禾味现货12+20−32=0，在途8+24−20=12；服装现货6+28−32=2，在途4+36−28=12。总量对上仍须核对日期与订单事件，不能替代逐日审计。

## 第一轮对抗审查修复

数量的小数位校验改为读取Decimal.as_tuple()的原始系数和指数并忽略无意义尾零，不做乘法或normalize，避免默认28位运算精度把极小非零尾数舍入掉。新增4项回归测试覆盖超长非零小数、科学计数法、尾零、件的严格整数条件及不同Decimal上下文精度。冻结输入与四组结果字节不变；共43项测试通过。

## 第二轮对抗审查修复

导入调用simulate、audit或order_qr时，运算各自进入完整指定的Decimal上下文，不继承调用者的精度、舍入、指数范围、标志或异常traps。初始订单最多1000笔，模拟最多1000天且每天最多一笔新单；每笔及初始现货最多1,000,000。因此总流入含初始现货最多2,001,000,000，最多三位小数，需要最多13位有效数字。内部明确使用16位精度，足够精确计算这个受限模型，不宣称任意大数精确。纯策略入口分别限制OH/OO不超过2,001,000,000，两者之和最多4,002,000,000，仍在13位有效数字内；Q/r仍按原单条上限验证。数量以原始Decimal元组去无意义尾零并规范零，不使用会舍入的normalize。

新增5项回归覆盖精度1/2、不同舍入模式、极窄指数范围、全部异常traps开启、调用者上下文不被改写、独立审计拒绝被舍入的错误轨迹、初始订单数边界及纯策略精确阈值。冻结输入和四组结果不变；共48项测试通过。
