# D23 第一轮独立对抗式审查

结论：正文计算与已生成结果正确，但实践代码有 3 项交付前应修复的问题，因此暂不建议通过。

## 已验证
- 标准库 10 个测试方法全通过，发布路线复核通过。
- 独立另写循环（不调用 routing.check）枚举全部 120 种候选。服装 base/tightened 可行数 66/28、最短 14000/18000 米；禾味 88/52、最短均 10000 米。文章数字吻合，且文章没有夸大为通用最优证明。
- D22 两输入 SHA256、四点距离子矩阵继承通过。容量、需求和服务开始窗口口径清楚。
- 实际查看 cover/timeline/comparison 三张 PNG，无裁切或缺字；900×383 封面、900×500 正文符合近期约定。标题“四个时点”的图实际画三个区间，有四个边界，意义可理解。

## 阻断修复
1. **无解路径崩溃**：solve 可以返回 routes=null，但 CLI 紧接着读取 result['audit']['rows']，无解时 KeyError，无法按承诺保留状态与失败证据。应显式分支，没有路线不写伪造排程 CSV，并在 replay 处理 no-solution record。
2. **可覆盖公开证据**：README 说“发布输出在 outputs，不覆盖”，CLI 却允许 `python routing.py --solve` 默认为 outputs。请禁止 --solve 输出到 ROOT/outputs，要求独立目录。不要用说明代替保护。
3. **证据缺失假通过**：replay 只 glob 所有现存 JSON。删空 outputs 会打印 passed，缺一组也不报错。应固定检查两案例×两情景的期望文件集合，并验证 objective_m 与独立计算一致、enumeration_count 与重算一致、基线证据一致。

## 非阻断建议
- validate 检查 distance_unit/load_unit 却不检查 time_unit，文章称检查单位。补上 time_unit 精确值及相应变异测试。
- 长期可用 ValueError 替代输入 assert（-O 会禁用）；当前 README 已披露限制，教学版本可接受。
- CSV 回仓行重复 service_start/departure 已在 README 解释，无实际卸货，不构成错误。
- 允许两辆车而只有一辆出车、零宽窗口、时间假设非真实导航均已充分说明。

本轮未改正文或实现，未部署。
