# D9-v1 季节性朴素需求预测

全部情景为教学模拟；禾味为虚构餐饮连锁。核心只生成 A店 SKU01 一条公斤/日需求；其余15条没有运行。服装为匿名协同背景的独立件/日终端订单需求，不是生产排程；SIM-LIVE-001为虚构单号。没有真实品牌、业务收益或生产连接。

Python >=3.10，标准库，无需Docker。日常仓库回归执行：

```sh
python -m unittest -v
python check_regression.py
```

日常检查只用前140天开发数据运行模型与输入边界测试，并复算第113—140天验证结果。既有`results/test.json`只按已提交版本的固定SHA-256核验完整性，不解析其中标签、不重新评分、不改写结果。冻结回执、六个代码/政策/开发文件也需哈希一致；`sealed/`无需存在。它不证明旧测试结论有效性或历史访问情况，也不再验证原测试CSV的完整性。

`python run.py finalize`仍保留为**单独的显式测试集重评操作**，会读取`sealed/`第141—180天并覆盖`results/test.json`；它不属于`make check`或自动发布步骤。确需重评时须另行明确授权，不能在日常检查失败后自动刷新固定哈希。固定哈希基于提交`6e78881ec5cace564c101ca4dca85cb58254dfae`中的既有产物；任何有意更新须审查。

以下是历史完整重建流程，会重新生成全部180天并评分原测试段，**不作为日常发布检查执行**。完整重建：先保存原包，将 `freeze.json` 与 `results/test.json` 移至包外备份（否则prepare拒绝旧候选），再运行（会覆盖其余同名CSV与JSON）：

```sh
python run.py prepare
python -m unittest -v
python run.py freeze
python run.py finalize
```

- `generate.py` 定义种子20261102、LCG整数递推、2026-04-06起180天；服装种子+1。
- 禾味周基础[20,22,21,24,28,36,32]公斤，噪声state%7−3，需求max(0,base+noise)。
- 服装周基础[80,84,86,88,110,140,126]件，加floor((day−1)/14)趋势，第118–120天各加90。所有扰动为事先写定模拟机制。
- 连续完整日期、非负有限需求、无缺货、完全可观测；库存快照或截断销量不等于需求。
- `policy.json`：初始训练1–112，验证113–140，封存测试141–180；周期7事先固定，不选参。
- `data/` 开发前140天，`sealed/` 测试40天。`prepare`只评验证；`freeze`记录代码政策与CSV SHA-256；`finalize`先核对字节，再打开测试文件评分。此为可审计流程而非访问控制或可信时间戳；完整包所有标签均可读。
- 每天滚动做h=1：验证28天，测试40天（含已发生测试历史更新）。不是在T=140一次预测40天。
- 五天累计窗口须完整在本块：验证24个（113–117至136–140）；测试36个（141–145至176–180）。窗口重叠，不独立。
- `baseline.py` 固定起点循环最后7天，h=8/15取相同的第一个值，拒绝不足7天、非法步长、坏日期和坏需求；零合法。
- `results/hand.json` 是T=112对113–119的七步演示，不属于五天评价。数值[19,25,19,22,28,38,29]。
- `results/*validation.json` 与 `results/test.json` 保留完整实际、预测、起点和窗口，MAE精度不截断。不同单位不可相加。
- CSV与JSON明确输出LF；仓库`.gitattributes`固定实验目录为LF，确保Windows/Linux checkout保留冻结哈希。发布前为修复换行曾重新冻结，所有数值与规则未改，见审查补记。

原理来源：https://otexts.com/fpp3/toolbox.html#seasonal-na%C3%AFve-method （2026-11-02核对），非书籍案例译本。可编辑SVG与PNG另见独立配图包。根目录实验文件可独立运行；配图作者工具位于站点仓库的 `scripts/generate-d9-figures.py` 与 `scripts/render-d9-images.cjs`，需在仓库根运行，预测计算无需Node。独立审查归档见交付包 review/；其中原始审查脚本依赖完整仓库路径，运行位置见review/README.txt，不是本包的实验入口。
