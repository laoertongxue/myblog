# D22：容量约束与配送载荷（全部业务数据模拟）

## 范围

两个十点双车案例的 inputs/*.json **逐字复制 D21**。每点2箱，每车12箱，单次闭合配送，不拆单、不丢点、不回仓补装，无取货、时间窗或司机工时限制。禾味原2店8食材SKU/14天样本不变，本十点网络为独立教学扩展；服装企业仅匿名模拟物料交接，非真实订单。

## 不安装求解器也可验算

Python >=3.10，在本目录运行：

```bash
python -B -m unittest -v
python -B run.py
```

默认用独立检查器重新核验保存路线，生成 comparison.json 和 delivery_legs.csv，不调用求解器，不读取任何预测封存数据。固定输出应字节一致。可使用 `--output-dir /tmp/d22-replay` 把复算结果写到其他目录。run.py 所有输入相对于脚本目录，与当前工作目录无关。

## 重新求解（另存，不覆盖发布证据）

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements-lock.txt
.venv/bin/python run.py --solve --output-dir new-results
```

Windows 使用 `.venv\Scripts\python`。如当前平台无法安装锁定版本，请选 Python3.12，不要静默升级 OR-Tools 后称结果完全相同。作者实际环境 macOS arm64 / Python3.12.13 / OR-Tools9.14.6206，完整依赖记录 requirements-lock.txt。最小需求文件 requirements.txt 只固定求解器。

搜索使用 PATH_CHEAPEST_ARC 初解与 GREEDY_DESCENT 局部改进，10秒是上限，不是最优性证明。无解返回只记 `no_solution_returned_not_a_proof`，不得和可行基线计算节省率。算法版本、平台、搜索限时可能影响同成本路线次序；复现实验应重新核验路线可行性与目标，不要求重新求解的路径逐字相同。

已保存路线两案例均与编号基线等距：禾味20000米，匿名服装28000米；差值均0。不是收益实验。没有改差基线、添加车辆、放宽容量或删减客户来制造改善。运行 `--solve` 必须指定独立输出目录。

## 字段口径

`capacity_cumul_before_service` 是 OR-Tools Capacity.CumulVar 在节点**服务之前**的累计需求。例如路线0→1→2→5→4→3→0为 [0,0,2,4,6,8,10]，并非车上剩余货。出发10箱，交货后剩余 [8,6,4,2,0]箱；最后回仓仍0箱。`delivery_legs.csv` 记录每段出发载荷、到站交货量、交货后剩余（after_service_remaining_box，不是抵达但尚未卸货的数量）、累计已交量及含回仓距离。每行满足出发载荷减交货量等于交货后剩余。纯配送的容量判断为出发装载总量≤该车容量。

3个客户各6箱、2车各10箱，即使总需求18≤20，也不可行：每车最多装一个完整客户，共最多服务2个客户。测试穷举全部8种分车分配，独立于求解器证明此反例，而不是用超时证明不可行。

## 官方例子

reference/vrp_capacity.py 是 Google OR-Tools v9.14 原始样例（保留 Apache2.0版权和LICENSE），来源：
https://github.com/google/or-tools/blob/v9.14/ortools/constraint_solver/samples/vrp_capacity.py
官方解释：https://developers.google.com/optimization/routing/cvrp

实际运行：`python reference/vrp_capacity.py`。官方样例 GUIDED_LOCAL_SEARCH /1秒，保存此次输出 official_output.txt，目标6208米；独立测试从原函数提取数据，核验4车容量、16客户覆盖、每段距离及累计量。**官方样例是取货口径**，打印的Load随访问增加；不要把它直接当作本配送案例的车上剩余。该限时样例重新运行不保证相同路线。

## 文件

- inputs：D21两案原始JSON，单位米/箱，固定矩阵。
- outputs/*_solver.json：求解配置、版本、原始状态码、输入SHA256、路线与服务前累计量；状态1仅为此次工具返回值，不作最优性结论。
- outputs/comparison.json：独立复算的基线和求解路线总账。
- outputs/delivery_legs.csv：24段交货/距离流水。
- d21_checker.py：复用D21输入/路线/距离检查，不访问求解器目标内部。
- test_run.py：错误输入、重复遗漏超载、回仓、累计时点、装箱反例、官方例和字节复现测试。
