# 数据字典

## 输入JSON

所有数量必须为非负整数，batch与material_per_unit必须为正整数；布尔值不算整数。金额和概率用整数或精确数字字符串，拒绝浮点、NaN、Infinity。未知字段拒绝，避免默默丢掉重要约束。

|字段|含义与单位|
|---|---|
|case_id|仅hewei/apparel，防止单位与案例错配|
|title|匿名案例说明|
|unit|hewei=kg，apparel=piece；每个案例只处理一种可互换品|
|decision_at|新增来源决策时刻，带时区|
|deadline|统一交付与需求结算截止，晚于decision_at|
|known_at|整份输入快照在决策前可知的时间；不等于真实性证明|
|batch|三来源统一批量kg或件；不同来源不同包装未建模|
|receive_capacity|截止时点新增来源总接收容量kg或件，不是原物理库容|
|shortage_cost|每单位未满足净缺口的教学罚损，元/单位|
|surplus_cost|每单位剩余的额外费用，元/单位，不含已付来源成本|
|scenarios[].name|独立唯一情景标签|
|scenarios[].demand|剩余净缺口，已经扣去现存及既有及时在途，kg或件|
|scenarios[].probability|指定情景概率，严格正数且精确合计1|
|purchase.capacity|新采购能按期交付的上限，kg或件|
|transfer.donor_stock|调出方本例可用库存，kg或件|
|transfer.donor_reserve|调出方必须保留量，不能大于库存；不是新预测|
|production.capacity|给定期限内机器可产量，kg或件|
|production.material_available|生产可用唯一材料资源：服装为米；禾味禁用为0|
|production.material_per_unit|每成品固定毛料用量，服装为2米/件，既定损耗已内含，不另算损耗；禾味禁用填1避免除零|
|各来源unit_cost|每来源单位全部可变费用，元/单位|
|各来源fixed_cost|该来源正量启用一次的费用，元|
|各来源arrival_at|新来源预计到达时刻，晚于截止则可用上界0；不得早于决策|

生产有效上界为 min(机器上限,材料量整除单位用量)，再受总接收容量与及时到达约束。枚举时按batch向下取可行批次数。模型不允许负库存，不把调出保留量当成可供量。

## 候选CSV

purchase、transfer、production、quantity为各来源量和总量；正文生产变量m对应代码w及production，三者含义一致；supply_cost为无论哪种需求都要付的来源费用；expected_cost为按给定概率加权的总成本；expected_shortage、expected_surplus分别为期望缺口和余货。精确分数a/b保留运算语义，读者可用Fraction转换。

## 结果JSON

candidate_count是枚举的可行组合数，不是训练样本数；effective_caps是及时性及接收容量过滤后的来源上界；expected与high_service各有status、all_optimal_plans和selected。selected中scenarios逐一保留需求、概率、缺口、余货和总成本。INFEASIBLE不等于缺货为零。

## 全候选情景CSV

purchase、transfer、production组成候选主键，scenario是情景标签；probability为给定概率，demand为该情景净缺口。quantity、shortage、surplus均为本案例单位，supply_cost、total_cost、weighted_cost单位为元；weighted_cost=probability×total_cost。对同候选汇总weighted_cost应等于候选CSV的expected_cost。

反例输入counterexample.json独立于hewei.json。反例输出的cheap_unit_first与all_purchase是两个固定手算探测量，各自有status和evaluation；修改后不可行则evaluation为null并说明reason，不冒充可执行结果。

## 追溯与不可行说明

input_snapshot为完整输入副本；input_sha256按README规范化JSON规则计算。bound_explanation保留接收容量、批量、采购上限、调出库存与保留量、机器容量、材料可支持量及各来源及时性。策略结果required_quantity为该策略最低要求，max_feasible_quantity为所有可行组合的实际最大总量。不可行时reason说明两者的冲突；这不是最小冲突集合，也不诊断本模型未表达的业务条件。
