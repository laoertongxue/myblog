# D17 定期复核（R,S）实践包

Python 3.10+，仅标准库。解压后进入本目录：

```bash
python3 run.py
python3 -m unittest -v
shasum -a 256 -c MANIFEST.sha256
```

也可任意工作目录执行 `python3 /绝对路径/practice/run.py`，测试用 `python3 -m unittest discover -s /绝对路径/practice -v`。Windows可换成python。无shasum时，脚本核验冻结输入，测试核验结果哈希。不含运行时钟，结果字节确定；CLI篡改测试只操作临时副本。

## 实验边界

这是七日机制演示，不是经营回测、参数搜索、盲测、未来验证或生产系统。全部身份、日期、需求和订单号均为教学模拟。需求输入与D15/16逐字节相同；不读取D9 sealed。无成本、损耗、容量、预留、退货、取消、部分收货、随机交期、BOM或跨店调拨，不据此推出长期服务水平、节约金额或最优R/S。

- 禾味是虚构两店八SKU背景，仅生成A店SKU01，其他15个店×SKU组合未生成或评估。单位kg；OH12、OO8于day2到；需求7/9/8/4/5/6/3；S20。
- 匿名服装是独立单节点单SKU沙盘，单位pieces（件）。OH6、OO4于day1到；需求5/8/4/7/3/6/2；S24。不声称覆盖工厂真实WIP、生产交期或欠交流程，不产生排产指令。
- 每案比较R2、首次day2与R3、首次day3，均L2。服装L与D16不同，禁止把跨篇差异只归因于补货规则。
- 四组参数事先指定，以观察复核节奏，不根据结果挑选或优化。两种单位独立汇总，禁止相加。

## 时序、规则和边界

每日：日初全量准时收货 → 完整教学需求及即时履约/失销 → 日末复核与至多一张新订单。

一般定义 IP=on_hand+outstanding-backlog。复核日 q=max(0,S−IP)，非复核日 q=0。复核日条件为day≥first_review_day且(day−first_review_day)能被R整除。R不是交期；S不是固定订单量或现货目标。

本主模拟严格失销模式，backlog恒0。served=min(到货后OH,demand)，lost_sales=demand−served；失销不滚成欠交。独立纯规则测试仅用OH3/OO5/backlog10得到IP−2、q22（S20），说明一般公式，不声称已有欠交仿真；模拟器拒绝backorders配置。非复核日即使IP<0，纯规则也返回0。

复核后IP=max(复核前IP,S)，已有IP超过S不退货、不下负订单；有正单时IP补到S，但OH不因下单增加。IP=S时订单为0。服装R2的day4虽是复核日且OH=0，OO=24已达到S，不重复下单。一次复核不保证有一张订单。

L定义为下单后完整等待日数：arrival_day=placed_day+L+1。L2即t日末下单于t+3日初到，L0也只能次晨到；当天新单不能满足当天需求。到货同量减OO、增OH，收货本身不改变IP。初始单为窗口前订单，禾味placed_day−1，服装−2，均与L2一致。

未到货订单保留到期末，不清零，不补入第七日现货；窗口外不代表无成本。订单ID只在单策略运行内唯一，合并必须带strategy。纯函数重复调用仍返回同一个q，不具数据库幂等性；本模拟一次顺序day循环、每天至多一张新单，不可当作生产防重系统。

## 冻结与文件

POLICY_CARD.md、frozen_policy.json与两份输入CSV在首次运行前落盘并计算SHA-256，source_manifest.json记录这四项。其SHA-256固定在run.py；脚本先完整验证后输出，不自动刷新冻结哈希。这是本地顺序回执，不是第三方预注册、外部时间证明或数字签名。若输入变更，应另建、审查并冻结新实验；不可重算哈希伪装原实验。

- data/*.csv：输入，case/series/unit为身份及单位，day为从1开始的日序，date为连续教学日期，demand为完整需求，非被销量截断的需求。
- frozen_policy.json：四组参数。initial_on_hand是首次收货前OH；initial_orders为已确认未到货订单；days=7，lead_time=L，review_interval=R，first_review_day为首次复核，target_level=S，shortage_mode固定lost_sales。
- run.py：严格验证、Decimal精确运算、独立事件重放与日账审计；审计不用assert，python -O也生效。
- test_inventory.py：43项测试，包括四组独立手算、一般欠交边界、复核日/非复核日、IP高于/等于/低于S、在途防重复、日期与交期、尾单、守恒、未来需求扰动前缀不变、等比例变形、零需求、L0、同日多单到货、身份单位混用拒绝、篡改和独立CLI确定性。
- results/*-ledger.csv：四份完整逐日日账，字段见下。
- results/*-order-events.csv：初始在途登记、日末下单、日初到货事件。没有事件仍保留表头。
- results/summary.json：四组单独汇总、逐笔期末在途与冻结哈希。
- results/output_hashes.json：九份结果文件哈希，不自包含。
- MANIFEST.sha256：完整实践包清单，不含自身、缓存。

数量输入0～1,000,000，kg最多三位小数，pieces为整数；S可为0。R与首次复核日1～1000，L为0～1000，days为1～1000，最多1000笔初始单；不接受bool冒充数值、NaN、负数、身份单位混用、缺日或额外字段。初始到货日1～1000且与L相符。边界测试构造的参数不是四组结果外的调参。纯规则状态OH/OO/backlog各限2,001,000,000；S仍限1,000,000。内部固定16位Decimal上下文，隔离调用者精度、舍入、指数范围和traps，不宣称任意大数精确。主失销模型新单不超过S；一般欠交纯函数可返回大于S的q。

## 日账和事件字段

日账每行case/series/unit/day/date标识唯一案例与日期；所有数量按该行unit：

- opening_on_hand、opening_on_order：日初收货前OH/OO。
- arrivals：当天日初收货量；available_before_demand：收货后需求前OH。
- demand、served、lost_sales：当日完整需求、即时履约、失销。
- closing_on_hand：需求处理后的OH，也是下单后的OH。
- on_order_before_order、ip_before_order：日末新单前OO与IP。
- is_review_day：是否复核日（CSV True/False）；backlog：主模拟恒0。
- order_quantity：日末新单量；on_order_after_order、ip_after_order：订后OO与IP。

事件字段：order_id为本策略内唯一号；case/series/unit为身份单位；placed_day为实际下单日；arrival_day为计划且本例实际到货日；quantity为完整订单数量；event为initial_open/placed/arrival；event_day为记录事件的日序。initial_open的event_day0只登记原在途，不代表day0下单。不要把初始登记、下单、到货三类事件量相加当采购量。

summary按strategy分开列出参数、total_demand/served/lost_sales/arrivals/new_orders、order_count（不含初始单）、closing_on_hand/on_order/inventory_position和closing_pending_orders。尾单含order_id、placed_day、arrival_day、quantity。哈希没有业务单位。

## 七日手算核验

|策略|单位|需求|履约|失销|新单张数|新单量|到货|末OH|末OO|末IP|
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
|禾味R2/S20|kg|42|34|8|3|31|28|6|11|17|
|禾味R3/S20|kg|42|29|13|2|26|28|11|6|17|
|服装R2/S24|pieces|35|21|14|2|33|28|13|9|22|
|服装R3/S24|pieces|35|18|17|2|30|28|16|6|22|

禾味R2新单day2/4/6为16/4/11kg，到day5/7/9；R3新单day3/6为20/6kg，到day6/9。服装R2新单day2/6为24/9件，到day5/9；R3新单day3/6为24/6件，到day6/9。四组均只留day6一张尾单，day9到，数量依次11kg、6kg、9件、6件。

守恒：禾味R2现货12+28−34=6，在途8+31−28=11；R3现货12+28−29=11，在途8+26−28=6。服装R2现货6+28−21=13，在途4+33−28=9；R3现货6+28−18=16，在途4+30−28=6。总量相符不代替逐日日序与事件核验。

这两条指定轨迹中R2失销较少，但R2/3同时改变了首次复核日；比较对象是这两套完整日历，不单独识别频率的因果效果。S相同仅用于机制对照，不表示两个R有相同服务目标：定期复核的保护期通常涉及R+L，并须明确时间端点。本包没有需求分布或服务目标，不估计安全库存，不据此选最优R。末OH较大也不代表整体更好，早期失销已无法挽回。
