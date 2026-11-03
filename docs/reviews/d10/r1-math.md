# D10 第一轮对抗审查：代码、数学、数据（R1）

审查结论：**数值、时间边界、数据来源、结果重生成通过；发现 1 项 P2 输入校验缺陷，修复后须第二轮复核。不是全文或发布通过证明。**

## 审查范围与隔离

- 候选来源：`/workspace/shared/d10-work/practice`，约 2026-11-03 01:36 UTC 冻结副本。
- 所有执行、投毒和源变更实验均在 `/workspace/shared/d10-review-r1-scratch/practice`；未修改作者文件。
- 只读取 D9 ZIP 的目录及 `data/hewei-development.csv`、`data/apparel-development.csv` 两个成员，逐字节比对完全一致。未打开任何 sealed/test 数据成员。
- D9 测试总结已公开，不应声称此教学测试集是真正从未见过的独立 holdout。本轮只能确认 D10 交付目录无测试标签、执行不读测试集。
- 正文、图片、README、最终 ZIP 尚未纳入本轮；B/W 与简体字形、文案对数字和局限的表述须另外审查。

## R1-01 — P2：未闭合引号 CSV 被静默接受

目标：`baseline.py::load_csv` 的 `csv.DictReader(handle)`。

精确输入（末尾没有闭合引号）：
```python
body = 'day,date,demand,split\n1,2026-01-01,3,"train'
```
将上述内容写入临时文件后调用 `load_csv(path, 'case')`，返回正常行（demand 3.0、split train），没有报错。原因是 Python CSV 读取器默认 `strict=False`。这不改变既有开发数据结果，但不满足“拒绝非法 CSV，不静默修复”的输入契约。

建议：使用 `csv.DictReader(..., strict=True)`，把读取期间的 `csv.Error` 转为明确输入异常，并增加该输入的回归测试。R2 验收应直接复现并断言拒绝，同时重跑整个包。

## 已通过的独立证据

1. 不调用作者预测或窗口函数，用标准 CSV + Fraction 独立计算所有 16 个汇总值；全部一致。
2. 独立校验持久化 CSV 全部 416 条记录（224 个单步、192 个五日窗口）：预测、目标值、目标边界、五日总量绝对误差均正确。
3. 每种方法单步起点 112…139，共 28 个；五日起点 112…135，共 24 个。比较方法起点完全相同，所有目标在验证日 113…140。
4. MA3/7/14 固定起点五步均为最后 k 个真实观测的同一均值，无递归、居中平滑、未来实值更新。周朴素使用起点前的对应星期值。
5. 五日指标为 `mean(abs(sum(actual_h)-sum(pred_h)))`，不是五日逐点绝对误差平均；两者不能混称。五日窗口重叠，不能当作 24 个独立实验。
6. 两个 development.csv 与原 D9 ZIP 成员逐字节一致；140 日、112/28 分区一致；kg/day 与 pieces/day 分开处理。
7. 将五个已有结果文件内容替换为 STALE SENTINEL 后执行副本 `python run.py`，全部输出逐字节恢复冻结值；没有依赖旧结果。
8. 修改副本源 CSV 一个换行符，`python run.py` 非零退出并明确提示 source bytes changed；之后恢复副本源数据。
9. 作者 23 项单元测试通过。独立恶意 CSV 试验：缺值、NULL、负值、NaN、Inf、重复日、缺日、日/日期不一致、多字段、少字段、重复表头、test 标签均拒绝；零需求接受。仅未闭合引号试验失败。

## 独立精确指标

|案例|方法|逐日 MAE（每日量纲）|五日总量 MAE（总量量纲）|
|---|---|---:|---:|
|禾味|MA3|47/7 = 6.7142857143|593/24 = 24.7083333333|
|禾味|MA7|149/28 = 5.3214285714|75/8 = 9.375|
|禾味|MA14|2111/392 = 5.3852040816|1025/112 = 9.1517857143|
|禾味|SNaive7|25/14 = 1.7857142857|79/24 = 3.2916666667|
|服装|MA3|746/21 = 35.5238095238|12185/72 = 169.2361111111|
|服装|MA7|2955/98 = 30.1530612245|6731/56 = 120.1964285714|
|服装|MA14|423/14 = 30.2142857143|4597/42 = 109.4523809524|
|服装|SNaive7|591/28 = 21.1071428571|927/8 = 115.875|

这支持“服装 MA14 五日总量误差低于 SNaive7，但逐日误差更高”，不支持“MA14 全面更优”。禾味 MA7 是三个 MA 的逐日最优，而 MA14 是三个 MA 的五日总量最优；SNaive7 在两个指标上均优于三个 MA。不得只写一个不注明任务的“最佳 k”。

## 可复现材料

- `d10-review-r1-scratch/independent_review.py` 与 `independent-results.txt`
- `d10-review-r1-scratch/invalid_csv_review.py` 与 `invalid-csv-results.txt`
- `d10-review-r1-scratch/unittest.txt`
- `d10-review-r1-scratch/inspected-sha256.json`

## 冻结文件 SHA-256

- `baseline.py`: `13ec2e245bb31b402bd3a3c9e5595740a6e1272db69122faba7a3d6e70f8401c`
- `data/apparel-development.csv`: `56badd2fc37decd72b2f55a980acb7add2594b96c7b8d269f6aaae59ee7d47e5`
- `data/hewei-development.csv`: `292072a63439529f22a73d41b83516928ae5a5b474b907b33d42e74962c23407`
- `policy.json`: `315150a3ad91230d5adb99124dd1e8dda12e98010a63f87185c70c368aeb7672`
- `results/daily_predictions.csv`: `a828db575289780a35730e7c4734b549ad09789a900b04613d88f08abdb4fd0f`
- `results/five_day_windows.csv`: `fdb2d720e68367fa068c6089593bf0bfed3a1777303604129b3a67bf0ae8e167`
- `results/manual_oracle.json`: `3a8fc8a3341715b37ec28c9291e06d477983cbc1ce91bf1a0f0e4bc9dd7e4e27`
- `results/origin112_examples.json`: `80825d5923f4a5d4175036339cc0885d614025acab3f0ee9cd7a15713e920ecb`
- `results/validation_summary.json`: `d8ab0ab7039f6d3d25a1666157c230fa7fc95308a82d7ab26f68c286086b86ba`
- `run.py`: `cfef47cf4675c57f42d936d3c166a8c43a62edfac084ef470fa0e57fe3d9af93`
- `source_manifest.json`: `b45d8b30c55eac46795ae0f0d68f8675f2925db5597192aa6d6ded265c24c8da`
- `test_baseline.py`: `6a1fda0eebf699110cadcb89728d2dd40b237399e6b748f95cfe5017051fd1fc`
