# D23 四点时间窗模拟

所有数据模拟。输入保留 D22 仓库 0 与点 1–4 的距离、需求、两车容量；新增时间与卸货假设。输入含 D22 原文件 SHA256，可与公开 D22 实验包核对。

时间为午夜起整数分钟，距离米，载荷箱。窗口限制服务开始，端点包含。两车 8:00 出发，10:00 前回仓，允许等待/空车。目标仅最小化距离，无用车固定费。未建模温层/取货/排队/工时。

## 已发布证据复核（Python 标准库，无需安装依赖）

在解压目录执行：
```
python routing.py
python -m unittest -v
```

不要用 `python -O`，校验使用断言。11 个测试方法覆盖多个参数化失败及两案例四种结果。

## 独立重跑（需要 Python 3.11+）
```
python -m venv .venv
# Windows 使用 .venv\Scripts\activate；macOS/Linux 使用 source .venv/bin/activate
pip install -r requirements.txt
python routing.py --solve --out rerun
```
发布输出在 outputs，不覆盖。OR-Tools 9.14.6206；PATH_CHEAPEST_ARC + GUIDED_LOCAL_SEARCH，5秒。不同机器/版本/时间预算可能有不同路线或状态。保存结果中的 rows 为独立检查器对路线作最早开始服务的排程，不是求解器内部累计变量的复制。

每组 JSON 保存原始状态（整数）、参数、版本、测量耗时、路线、检查结果及旧路线检查。CSV 包含到达、等待、开始服务、离开；回仓行 service_start/departure 等于到达只为统一格式，无实际卸货；文章显示不适用。

窗口收紧至点 2 [510,510] 是合法零宽压力测试。枚举为 24 个四点排列 × 5 个两车切分，计车辆标签不去重。它与求解器实现独立，但使用同一检查器；不能当作第二个完全独立业务规则实现。

没有路线时 routes=null，不能声称最优或已证明不可行。原始状态语义参见 https://developers.google.com/optimization/routing/routing_options 。非法输入抛 AssertionError，不进入求解。到达时间不能当成服务开始。

每条求解证据保存规范 JSON 输入的 SHA256，复核要求四份指定输出均存在且输入哈希一致。重新求解没有路线时保存状态 JSON，不生成排程 CSV；禁止把空结果当作成功。
