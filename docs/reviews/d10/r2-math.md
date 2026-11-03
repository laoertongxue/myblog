# D10 第二轮独立对抗审查：数学、代码与实际下载包（R2）

**PASS（本报告限定范围）。无未解决 P1/P2；R1-01 的 P2 CSV 缺陷已关闭。**

本轮依据冻结最终 integration ZIP，而非作者工作目录的浮动副本。审查时间：2026-11-03 01:44–01:46 UTC。未部署、未修改冻结文件；所有执行与投毒实验在 `/workspace/shared/d10-review-r2-scratch`。

## 精确冻结身份

- integration ZIP：`8fc53c283bba0c8287c61c043fbaa3263df5700f0dd2daf13aca9845230f0ff0`
- `content/blog/moving-average-demand-forecast/index.md`：`cfcb9ee4eb579cc9f3d99947b60cddc1c15d5bbedac80135a5db34ac7ab797c8`
- 外部 `CANDIDATE_MANIFEST.sha256`：`5113407f1aaffa54566b60b79db27809ba3f747a9797ca80d6e6d26986c6bce1`
- integration 内 `docs/reviews/d10/INTEGRATION_MANIFEST.sha256`：`5e46cc479b5e030cd6907912ca26b831b4e117a68c028c53aa4e44925f2aca1d`（与外部 candidate manifest 是两个不同文件，非身份冲突）。
- 实际公开下载路径 `static/downloads/d10-moving-average-practice.zip`：`53f2692e0f934d7717ceb2d02b3433a53e1f7eeca04c661445f530adf9b4c949`
- 下载包 `baseline.py`：`9e567490e2674f7f175531cf1fca838d53a41467d8ba2153c4007ac1bf83190d`
- 下载包 `run.py`：`d499cc430c3ae2f4980e4309550366059610fd4a0612eade9dc14951448198de`
- 下载包 `test_baseline.py`：`4e13c469c56b40401ffeb952be9717c752502539b73bfead24fd76f57f6ddb31`

已逐项验证外部 candidate manifest、integration manifest、下载实践包 MANIFEST 与 ARCHIVE_MANIFEST 的全部摘要，不仅比对 manifest 本身。

## R1 缺陷关闭证据

已阅读冻结 `r1-closure.md`，但不以作者声称作为通过证据。对实际下载包独立复现：
```python
body = 'day,date,demand,split\n1,2026-01-01,3,"train'
```
`load_csv` 现在明确抛出 ValueError。源码为 `csv.DictReader(..., strict=True)`，在读取及表头阶段捕获 csv.Error 并转换为 `malformed CSV syntax`。25 项标准库单元测试全部通过，包括未闭合引号、错误闭合字符和表头引号。独立 13 类恶意 CSV 输入全部拒绝；零需求仍合法。

## 数学与时间边界

- 独立 Fraction 实现，不调用作者预测或窗口函数来生成期望值；全部 16 项指标与 416 条持久化明细重新核对通过。
- 224 行单步记录＝两案例×四方法×28 日；192 行五日窗口记录＝两案例×四方法×24 起点。
- 日起点 112…139；五日起点 112…135，首末目标 113…117、136…140；候选与比较基线具有相同起点。
- MA 固定起点五步均值恒定，不递归、不居中、不读取未来；起点向前滚动后允许新实测历史进入。
- 单步 MAE 与五日总量 MAE 分开。五日总量计算先加总再取绝对值；不是逐点 MAE，亦不是拼接五个不同起点的一步预测。
- 正文披露重叠窗口非独立样本，不将 120 个目标位置称为 120 个独立日期；公斤和件不混合。

## 正文数字与解释核验

- 两张结果表全部 16 格与独立结果四舍五入到四位一致。
- 禾味第106…112日 `[19,25,19,22,28,38,29]`；最后3/7/14日合计95/180/369；对应均值与五日总量、季节性朴素五日113公斤全部正确。
- 第112日为2026-07-26；连续180日从2026-04-06到2026-10-02，日期正确。
- 服装活动日第118…120日为239/227/179；第117日起点MA3=304/3；第120日起点MA3=215，而第121日实际91；同起点MA7=148.5714、MA14=128.6429均正确。
- 三次90件冲击全部在窗口中时附加量90、270/7、270/14正确；第120日到第134日起点退出14日窗口的边界正确。
- 正文正确陈述服装MA14五日总量MAE109.4524低于季节性朴素115.8750，但日MAE30.2143高于21.1071；没有宣称全面胜出。
- 正文说明D9测试汇总已经公开，D10不重读、不重评不等于真正新盲测；没有最终测试或真实经营收益主张。

## 数据、归档与重生成

- 只从原D9 ZIP打开两个development.csv成员进行字节比对；没有打开sealed/test标签成员。
- 两份开发数据哈希仍为禾味 `292072a63439529f22a73d41b83516928ae5a5b474b907b33d42e74962c23407`、服装 `56badd2fc37decd72b2f55a980acb7add2594b96c7b8d269f6aaae59ee7d47e5`。
- 公开integration和三个下载ZIP无重复条目、绝对路径、路径上溯、反斜杠路径或符号链接；无sealed目录、测试标签CSV、缓存或原D9压缩包。
- 下载包只带140日开发标签；配图包中同名开发CSV也逐字节相同。预测代码没有测试读取或评分入口。
- 将五个真正生成的结果文件全部替换为STALE SENTINEL，然后执行实际下载包的 `python run.py`，全部五文件逐字节恢复冻结值。附带console_summary与unit_test_log为已有运行记录，不冒称run.py每次重生成它们。
- 副本源CSV增加一个换行后，runner以source bytes changed明确拒绝；恢复后再次核对字节。
- 解压的下载实践包与integration里的practice镜像相同（下载包新增ARCHIVE_MANIFEST除外）；确认审查的是实际交付代码而非另一版本。

## 证据文件与范围限制

独立脚本和日志保存在 `d10-review-r2-scratch/independent_review.py`、`independent-results.txt`、`invalid_csv_review.py`、`invalid-csv-results.txt`、`unittest.txt`。本次25项测试实际运行通过，不依赖包内旧日志。

本PASS覆盖代码/数学/数据/数值文案/归档路径安全/可复算性。未在本报告中审批PNG视觉质量、简体字形、移动端主题渲染、站点构建或部署；这些需由相应独立审查和发布门禁确认。没有授权提前部署，也没有修改冻结内容。对本轮通过后发生的实质更改，必须重新核对摘要和受影响项目。
