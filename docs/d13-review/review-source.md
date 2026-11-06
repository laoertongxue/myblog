# D13 v3 完整可读审查材料

包含正文、全部实践源代码、开发CSV、九份结果及冻结清单；配图见审查页附件。

# 文件 content/blog/rolling-backtest-stockout-censoring/index.md

SHA256 2630744df203c73ffb2d24b2e9cb0d24106db201c4e36c1fe857d2dfeedc65df

~~~~text
---
title: "滚动回测：预测时还不知道的事，不能提前用"
date: 2026-11-06T09:00:00+08:00
draft: false
slug: "rolling-backtest-stockout-censoring"
description: "用禾味与匿名服装的模拟案例，逐起点回放需求预测，区分一步与固定五步、防止未来信息泄漏，并以独立缺货反例说明销量不等于需求。"
summary: "每天都算一次预测，再把五天结果加起来，就能评价五天前的决策吗？D13沿用前140天模拟开发数据，记录每个预测的起点、日期、步长和参数，比较28个一步目标与24个固定起点五日窗口。用未来扰动检验信息边界，再通过独立缺货模拟区分真实零需求、休店、缺测与销量截断。附完整回测、测试、配置冻结回执和黑白图重绘包。"
categories: ["供应链"]
tags: ["供应链", "需求预测", "滚动回测", "缺货", "算法实践"]
images: ["images/d13-00_cover.png"]
monochromeImages: true
---

![滚动回测先固定起点，再检查当时可见的信息；销量还可能被缺货截断](images/d13-00_cover.png)

同样预测接下来五天，匿名服装模拟案例中的SES α＝0.8，合计可以是556.02件，也可以是847.40件。差别不是计算精度：前者在第117天日终一次发出，后者把随后几天看过新订单、重新修订的一步预测加在了一起。

如果报表只保留目标日期，不保留“这份预测是什么时候做的”，两种数字很容易被放进同一列。第二种结果可以回答每天更新之后的安排，却不能证明第117天就知道未来五天。

[D12讨论了误差大小和偏差方向](/blog/forecast-error-bias-metrics/)。这篇继续追问两件更早的事：**预测时能看到什么，以及评分时把什么当作需求。** 第一件靠滚动起点和攻击测试核验；第二件用独立的缺货截断反例说明。

## 一 这次回放使用什么数据

**两个案例和全部数据均为教学模拟。** 禾味是虚构的2店、8食材SKU餐饮连锁，本篇只处理A店SKU01，单位为公斤/日；匿名服装案例处理终端订单需求，单位为件/日，不是工厂排产量。日期、数量、活动均为模拟，不对应真实品牌、订单或业务收益；若延伸出订单单号，也只能作为模拟字段，不能冒充企业记录。

主实验沿用D9的180天模拟序列中已经使用过的前140天开发CSV，字节与D12一致。第1—112天为初始历史，第113—140天为验证段，对应2026年7月27日至8月23日。第112天为7月26日。这里只加载这两份140行文件，不读取或重新评价第141—180天标签。

这是一场**教学开发回放**。验证段在前几篇已经多次查看，不能称为新盲测；原40天测试段汇总也已在D9展示，不能重新包装为从未触碰的独立检验。避免在单个起点偷看未来，只解决信息时序错误，不会自动消除反复看验证结果带来的选择偏差。

主实验假定需求完全可见，没有缺货、休店或缺测；单日记录在当天日终即可得到。代码没有实现`available_at`字段或延迟到达过滤，只适用于这一日终记录均可得的假设。现实系统若有报表延迟，应先实现按实际可用时间筛选历史的逻辑，不能把自然日期直接等同于信息已到达。

七个既有候选全部保留：周期7的季节性朴素，MA3／MA7／MA14，以及SES α＝0.2／0.5／0.8。SES用第一个观测初始化。MA在固定起点内保持当时均值，SES保持当时平滑水平；季节性朴素重复最近已观测的七天。没有新模型、全样本标准化、双向插补或未来缺货标签输入。

## 二 滚动的是起点，已经发出的预测不能跟着改

起点t表示第t天日终，已知历史为第1—t天。目标t+h是提前h天预测的对象。预测记为ŷ(t+h｜t)，竖线右侧的t就是这份预测的信息截止点。

流程是：在第112天日终发布第113天预测；等第113天真实观测到达，才把它加入历史，发布第114天预测。每个起点可用历史扩展，MA仍只取最后k天，SES仍按固定α更新。这里没有每到一天重新搜索一个最优参数。

[FPP3第5章第5.10节](https://otexts.com/fpp3/tscv.html)介绍了这种滚动预测起点的评价：构造某次预测只能使用预测起点当时已获得的观测，也可按实际决策需要评价多步预测。本文把同一原则落实到日期字段、固定窗口和可复现代码。

[![每个起点先发布完整预测，得到新观测后才移动到下一起点；五日窗口不能跨验证边界](images/d13-01_origins.png)](images/d13-01_origins.png)

一步任务的起点为112—139，目标为113—140，共28个。固定起点五日任务的起点为112—135，窗口从113—117到136—140，共24个。计算为28−5＋1＝24；第136天日终若预测五天，会到第141天，所以不纳入本段。

“固定起点”不是整个实验只预测一次，而是**每个起点一次发出五个步长，中间不更新这份预测**。下一天可以另发一份新预测，但旧版本必须保留。比如第112天对第114天的h＝2预测，与第113天对第114天的h＝1预测，是两个不同版本。

实践包的`predictions.csv`逐行保留案例、实体、单位、方法、完整参数、起点日及日期、历史截止日、目标日及日期、步长h和任务长度。先由`issue`生成一个起点的全部预测，再由`replay`附上已实现的实际值和误差。预测函数先切历史前缀，连未来记录是否合法都不检查；离线入口另行检查开发文件完整性，这个检查不用于拟合或填补数值。

## 三 把五次一步预测拼起来，会悄悄改变问题

看匿名服装的第117天日终，即2026年7月31日。预测目标为8月1日至5日，对应第118—122天。SES α＝0.8在这个起点的平滑水平约111.2033件/日，五步都维持这个水平，合计556.0164件。

若每天等新订单到达后再做一步预测，同样五个目标的预测依次为111.2033、213.4407、224.2881、188.0576、110.4115件/日，合计847.4012件。其中第二个数字已经用到了第118天的观测，绝不属于第117天日终可发出的版本。

[![服装SES0.8第117天固定五步合计556.02件，随后逐日修订合计847.40件；两者信息集不同](images/d13-02_revisions.png)](images/d13-02_revisions.png)

两组预测不是谁算错了，而是适用决策时点不同。错误在于给逐日修订结果贴上“原起点五步”的标签。实践包把后者存为带有`WRONG_FOR_ORIGIN117`标记的负对照，只演示错误拼接，不让它进入五日成绩表。

对一个固定起点，五日累计误差定义为：

```text
E(t,5) = [y(t+1) + … + y(t+5)]
       − [ŷ(t+1|t) + … + ŷ(t+5|t)]
五日累计MAE = 24个窗口的 |E(t,5)| 的平均
```

这不是“第5天单点误差”，也不是五个逐日绝对误差的和。若五个日误差为[−2,+2,0,0,0]，累计绝对误差为0，逐日绝对误差之和为4。总量刚好并不意味着每天都有货；保质期短的食材尤其不能只盯累计总量。

24个窗口重叠，同一天可能被评分多次。它们代表24次按日启动的五天决策，不是24份独立样本；本篇不据此做独立样本置信区间或显著性检验。五日WAPE的分母是24个窗口实际合计的总和，包含重复覆盖，不是一次性的销量总额。

## 四 同一数据，改了决策长度，排序也可能变

以下表格完整列出七个候选的两类任务，均保留四位小数。一步的n＝28，五日累计的n＝24。误差为实际−预测；正ME表示低估，MAE和RMSE越小表示本任务下相应误差越小。WAPE＝绝对误差合计÷实际合计，实际总量为零时未定义。

### 禾味：星期结构在两类任务中都有效

一步的ME／MAE／RMSE单位为公斤/日；五日累计单位为公斤。一步实际合计738公斤，五日窗口实际合计3158公斤，后者有重复覆盖。两类MAE的大小不能直接当作相同任务的准确率比较。

手机端可左右滑动表格。

<div role="region" tabindex="0" aria-label="禾味一步与五日累计误差表（可横向滚动）" style="overflow-x:auto;max-width:100%;margin:28px 0">
<table style="min-width:700px;width:100%;max-width:none;display:table;margin:0;white-space:nowrap">
<thead><tr><th scope="col">方法</th><th scope="col">任务</th><th scope="col">n</th><th scope="col">ME</th><th scope="col">MAE</th><th scope="col">RMSE</th><th scope="col">WAPE</th></tr></thead>
<tbody>
<tr><td style="white-space:nowrap;text-align:left">SNaive7</td><td style="white-space:nowrap;text-align:left">一步</td><td style="white-space:nowrap;text-align:right">28</td><td style="white-space:nowrap;text-align:right">0.2143</td><td style="white-space:nowrap;text-align:right">1.7857</td><td style="white-space:nowrap;text-align:right">2.2678</td><td style="white-space:nowrap;text-align:right">6.7751%</td></tr>
<tr><td style="white-space:nowrap;text-align:left">SNaive7</td><td style="white-space:nowrap;text-align:left">五日累计</td><td style="white-space:nowrap;text-align:right">24</td><td style="white-space:nowrap;text-align:right">1.2083</td><td style="white-space:nowrap;text-align:right">3.2917</td><td style="white-space:nowrap;text-align:right">4.0260</td><td style="white-space:nowrap;text-align:right">2.5016%</td></tr>
<tr><td style="white-space:nowrap;text-align:left">MA3</td><td style="white-space:nowrap;text-align:left">一步</td><td style="white-space:nowrap;text-align:right">28</td><td style="white-space:nowrap;text-align:right">0.1429</td><td style="white-space:nowrap;text-align:right">6.7143</td><td style="white-space:nowrap;text-align:right">7.8189</td><td style="white-space:nowrap;text-align:right">25.4743%</td></tr>
<tr><td style="white-space:nowrap;text-align:left">MA3</td><td style="white-space:nowrap;text-align:left">五日累计</td><td style="white-space:nowrap;text-align:right">24</td><td style="white-space:nowrap;text-align:right">-0.8472</td><td style="white-space:nowrap;text-align:right">24.7083</td><td style="white-space:nowrap;text-align:right">28.2953</td><td style="white-space:nowrap;text-align:right">18.7777%</td></tr>
<tr><td style="white-space:nowrap;text-align:left">MA7</td><td style="white-space:nowrap;text-align:left">一步</td><td style="white-space:nowrap;text-align:right">28</td><td style="white-space:nowrap;text-align:right">0.2092</td><td style="white-space:nowrap;text-align:right">5.3214</td><td style="white-space:nowrap;text-align:right">5.9375</td><td style="white-space:nowrap;text-align:right">20.1897%</td></tr>
<tr><td style="white-space:nowrap;text-align:left">MA7</td><td style="white-space:nowrap;text-align:left">五日累计</td><td style="white-space:nowrap;text-align:right">24</td><td style="white-space:nowrap;text-align:right">0.9583</td><td style="white-space:nowrap;text-align:right">9.3750</td><td style="white-space:nowrap;text-align:right">10.6516</td><td style="white-space:nowrap;text-align:right">7.1248%</td></tr>
<tr><td style="white-space:nowrap;text-align:left">MA14</td><td style="white-space:nowrap;text-align:left">一步</td><td style="white-space:nowrap;text-align:right">28</td><td style="white-space:nowrap;text-align:right">0.1403</td><td style="white-space:nowrap;text-align:right">5.3852</td><td style="white-space:nowrap;text-align:right">5.9835</td><td style="white-space:nowrap;text-align:right">20.4317%</td></tr>
<tr><td style="white-space:nowrap;text-align:left">MA14</td><td style="white-space:nowrap;text-align:left">五日累计</td><td style="white-space:nowrap;text-align:right">24</td><td style="white-space:nowrap;text-align:right">0.4077</td><td style="white-space:nowrap;text-align:right">9.1518</td><td style="white-space:nowrap;text-align:right">10.2468</td><td style="white-space:nowrap;text-align:right">6.9551%</td></tr>
<tr><td style="white-space:nowrap;text-align:left">SES0.2</td><td style="white-space:nowrap;text-align:left">一步</td><td style="white-space:nowrap;text-align:right">28</td><td style="white-space:nowrap;text-align:right">0.1642</td><td style="white-space:nowrap;text-align:right">5.5652</td><td style="white-space:nowrap;text-align:right">6.4153</td><td style="white-space:nowrap;text-align:right">21.1145%</td></tr>
<tr><td style="white-space:nowrap;text-align:left">SES0.2</td><td style="white-space:nowrap;text-align:left">五日累计</td><td style="white-space:nowrap;text-align:right">24</td><td style="white-space:nowrap;text-align:right">0.2382</td><td style="white-space:nowrap;text-align:right">13.9983</td><td style="white-space:nowrap;text-align:right">16.2369</td><td style="white-space:nowrap;text-align:right">10.6384%</td></tr>
<tr><td style="white-space:nowrap;text-align:left">SES0.5</td><td style="white-space:nowrap;text-align:left">一步</td><td style="white-space:nowrap;text-align:right">28</td><td style="white-space:nowrap;text-align:right">0.1411</td><td style="white-space:nowrap;text-align:right">5.3391</td><td style="white-space:nowrap;text-align:right">6.6390</td><td style="white-space:nowrap;text-align:right">20.2569%</td></tr>
<tr><td style="white-space:nowrap;text-align:left">SES0.5</td><td style="white-space:nowrap;text-align:left">五日累计</td><td style="white-space:nowrap;text-align:right">24</td><td style="white-space:nowrap;text-align:right">0.3750</td><td style="white-space:nowrap;text-align:right">23.2535</td><td style="white-space:nowrap;text-align:right">26.5525</td><td style="white-space:nowrap;text-align:right">17.6721%</td></tr>
<tr><td style="white-space:nowrap;text-align:left">SES0.8</td><td style="white-space:nowrap;text-align:left">一步</td><td style="white-space:nowrap;text-align:right">28</td><td style="white-space:nowrap;text-align:right">0.1120</td><td style="white-space:nowrap;text-align:right">4.8633</td><td style="white-space:nowrap;text-align:right">6.4049</td><td style="white-space:nowrap;text-align:right">18.4517%</td></tr>
<tr><td style="white-space:nowrap;text-align:left">SES0.8</td><td style="white-space:nowrap;text-align:left">五日累计</td><td style="white-space:nowrap;text-align:right">24</td><td style="white-space:nowrap;text-align:right">1.2834</td><td style="white-space:nowrap;text-align:right">31.4695</td><td style="white-space:nowrap;text-align:right">33.8708</td><td style="white-space:nowrap;text-align:right">23.9160%</td></tr>
</tbody>
</table>
</div>

季节性朴素的一步MAE为1.7857公斤/日，五日累计MAE为3.2917公斤，在各自任务的候选中最低。MA7与MA14的五日累计MAE为9.3750、9.1518公斤；SES α＝0.8为31.4695公斤。这个序列具有稳定星期差异，单一水平在固定五步内无法表达每天的起伏。

这些只是当前模拟回放的描述性结果。若用于真实餐饮采购，还要区分到货日、保质期、库存和服务要求，不能把累计预测直接当作订单，也不能把误差差值写成节约金额。

### 匿名服装：一步赢家不等于五日累计赢家

一步的ME／MAE／RMSE单位为件/日；五日累计单位为件。一步实际合计3374件，五日窗口实际合计14642件，含重复覆盖。

手机端可左右滑动表格。

<div role="region" tabindex="0" aria-label="匿名服装一步与五日累计误差表（可横向滚动）" style="overflow-x:auto;max-width:100%;margin:28px 0">
<table style="min-width:700px;width:100%;max-width:none;display:table;margin:0;white-space:nowrap">
<thead><tr><th scope="col">方法</th><th scope="col">任务</th><th scope="col">n</th><th scope="col">ME</th><th scope="col">MAE</th><th scope="col">RMSE</th><th scope="col">WAPE</th></tr></thead>
<tbody>
<tr><td style="white-space:nowrap;text-align:left">SNaive7</td><td style="white-space:nowrap;text-align:left">一步</td><td style="white-space:nowrap;text-align:right">28</td><td style="white-space:nowrap;text-align:right">0.6071</td><td style="white-space:nowrap;text-align:right">21.1071</td><td style="white-space:nowrap;text-align:right">42.2717</td><td style="white-space:nowrap;text-align:right">17.5163%</td></tr>
<tr><td style="white-space:nowrap;text-align:left">SNaive7</td><td style="white-space:nowrap;text-align:left">五日累计</td><td style="white-space:nowrap;text-align:right">24</td><td style="white-space:nowrap;text-align:right">4.2917</td><td style="white-space:nowrap;text-align:right">115.8750</td><td style="white-space:nowrap;text-align:right">159.7541</td><td style="white-space:nowrap;text-align:right">18.9933%</td></tr>
<tr><td style="white-space:nowrap;text-align:left">MA3</td><td style="white-space:nowrap;text-align:left">一步</td><td style="white-space:nowrap;text-align:right">28</td><td style="white-space:nowrap;text-align:right">0.1667</td><td style="white-space:nowrap;text-align:right">35.5238</td><td style="white-space:nowrap;text-align:right">47.8544</td><td style="white-space:nowrap;text-align:right">29.4803%</td></tr>
<tr><td style="white-space:nowrap;text-align:left">MA3</td><td style="white-space:nowrap;text-align:left">五日累计</td><td style="white-space:nowrap;text-align:right">24</td><td style="white-space:nowrap;text-align:right">-6.0972</td><td style="white-space:nowrap;text-align:right">169.2361</td><td style="white-space:nowrap;text-align:right">218.7075</td><td style="white-space:nowrap;text-align:right">27.7398%</td></tr>
<tr><td style="white-space:nowrap;text-align:left">MA7</td><td style="white-space:nowrap;text-align:left">一步</td><td style="white-space:nowrap;text-align:right">28</td><td style="white-space:nowrap;text-align:right">0.3163</td><td style="white-space:nowrap;text-align:right">30.1531</td><td style="white-space:nowrap;text-align:right">41.4708</td><td style="white-space:nowrap;text-align:right">25.0233%</td></tr>
<tr><td style="white-space:nowrap;text-align:left">MA7</td><td style="white-space:nowrap;text-align:left">五日累计</td><td style="white-space:nowrap;text-align:right">24</td><td style="white-space:nowrap;text-align:right">2.3155</td><td style="white-space:nowrap;text-align:right">120.1964</td><td style="white-space:nowrap;text-align:right">151.6128</td><td style="white-space:nowrap;text-align:right">19.7016%</td></tr>
<tr><td style="white-space:nowrap;text-align:left">MA14</td><td style="white-space:nowrap;text-align:left">一步</td><td style="white-space:nowrap;text-align:right">28</td><td style="white-space:nowrap;text-align:right">0.7245</td><td style="white-space:nowrap;text-align:right">30.2143</td><td style="white-space:nowrap;text-align:right">41.0821</td><td style="white-space:nowrap;text-align:right">25.0741%</td></tr>
<tr><td style="white-space:nowrap;text-align:left">MA14</td><td style="white-space:nowrap;text-align:left">五日累计</td><td style="white-space:nowrap;text-align:right">24</td><td style="white-space:nowrap;text-align:right">4.3690</td><td style="white-space:nowrap;text-align:right">109.4524</td><td style="white-space:nowrap;text-align:right">138.5447</td><td style="white-space:nowrap;text-align:right">17.9406%</td></tr>
<tr><td style="white-space:nowrap;text-align:left">SES0.2</td><td style="white-space:nowrap;text-align:left">一步</td><td style="white-space:nowrap;text-align:right">28</td><td style="white-space:nowrap;text-align:right">0.5517</td><td style="white-space:nowrap;text-align:right">30.8933</td><td style="white-space:nowrap;text-align:right">41.0226</td><td style="white-space:nowrap;text-align:right">25.6376%</td></tr>
<tr><td style="white-space:nowrap;text-align:left">SES0.2</td><td style="white-space:nowrap;text-align:left">五日累计</td><td style="white-space:nowrap;text-align:right">24</td><td style="white-space:nowrap;text-align:right">1.9844</td><td style="white-space:nowrap;text-align:right">119.3056</td><td style="white-space:nowrap;text-align:right">155.0519</td><td style="white-space:nowrap;text-align:right">19.5556%</td></tr>
<tr><td style="white-space:nowrap;text-align:left">SES0.5</td><td style="white-space:nowrap;text-align:left">一步</td><td style="white-space:nowrap;text-align:right">28</td><td style="white-space:nowrap;text-align:right">0.1639</td><td style="white-space:nowrap;text-align:right">28.4215</td><td style="white-space:nowrap;text-align:right">40.4326</td><td style="white-space:nowrap;text-align:right">23.5863%</td></tr>
<tr><td style="white-space:nowrap;text-align:left">SES0.5</td><td style="white-space:nowrap;text-align:left">五日累计</td><td style="white-space:nowrap;text-align:right">24</td><td style="white-space:nowrap;text-align:right">-1.9116</td><td style="white-space:nowrap;text-align:right">155.9761</td><td style="white-space:nowrap;text-align:right">202.6959</td><td style="white-space:nowrap;text-align:right">25.5664%</td></tr>
<tr><td style="white-space:nowrap;text-align:left">SES0.8</td><td style="white-space:nowrap;text-align:left">一步</td><td style="white-space:nowrap;text-align:right">28</td><td style="white-space:nowrap;text-align:right">0.1144</td><td style="white-space:nowrap;text-align:right">24.0696</td><td style="white-space:nowrap;text-align:right">37.9167</td><td style="white-space:nowrap;text-align:right">19.9748%</td></tr>
<tr><td style="white-space:nowrap;text-align:left">SES0.8</td><td style="white-space:nowrap;text-align:left">五日累计</td><td style="white-space:nowrap;text-align:right">24</td><td style="white-space:nowrap;text-align:right">0.3860</td><td style="white-space:nowrap;text-align:right">191.1509</td><td style="white-space:nowrap;text-align:right">236.9220</td><td style="white-space:nowrap;text-align:right">31.3319%</td></tr>
</tbody>
</table>
</div>

按MAE看，一步最低仍是季节性朴素，21.1071件/日；五日累计最低则是MA14，109.4524件，低于季节性朴素的115.8750件。若只沿用一步排名，就会忽略决策长度改变后的结果。SES α＝0.8的一步RMSE最低，但它的五日累计MAE为191.1509件，又是另一种表现。

原模拟序列在第118—120天加入了活动扰动。多个五日窗口覆盖同一活动，不能把这一批窗口当作很多场独立活动的证据，更不能据此宣称服装企业普遍适用MA14。

本篇以“各案例、各任务内验证MAE最小；完全同分按方法标识排序”为教学选择规则，在全部回放结束后保存配置：禾味两类任务与服装一步均为季节性朴素7，服装五日累计为MA14。冻结回执保存参数、运行编号和输入哈希，**不会把选中的方法回灌到早期起点，假装当时就已选好**。

这是用已反复查看的开发段演示配置留痕，并非此前预注册的业务目标，也不是选中模型的独立效果证明。未来正式应用仍需提前约定损失、冻结规则，再使用另外获得的时序数据评价。

## 五 真正有用的防泄漏测试，要主动破坏未来

只看代码里有没有`shift`，不足以判断是否泄漏。全样本均值、居中移动平均、双向插补，甚至后来才知道的缺货标记，都可能把未来带回起点。

本实践对每个完整五日起点、每个候选、两个案例做三类攻击：把起点后的需求统一增加10000并篡改缺货与观测标记；把所有未来行换成无效对象；直接删掉全部未来行，只留下已知前缀。三种情况下，原起点的五步预测都必须逐值不变。共有2×7×24＝336组，每组包含三种攻击。

还对完整回放增加一道检查：从第121天起把标签改大，所有截至第120天日终已经发出的预测保持不变。评分结果可以变，因为实际标签变了；预测版本不能变。最后四个一步起点也单独覆盖。

反过来，若第113天需求增加10，α＝0.5的SES在第112天发出的预测应保持不变，第113天日终发出的下一预测应增加5。这一正对照说明我们没有通过“永远不更新”来蒙混过关。

上述测试验证了当前接口的信息边界，不代表所有现实数据管道都无泄漏。实践包另外用分数算术与SES几何权重展开复算全部预测与指标，防止两个实现共享同一个循环错误。日期缺失、重复、混合实体或非数值需求会被拒绝，不用零代替。

## 六 缺货反例：报表里的零，可能有四种含义

主实验需求完全可见。现在另造一组14天、2026年1月5日至18日的模拟记录，专门演示观测边界，不改主实验数据。禾味用公斤，服装用件；服装数量设为禾味的五倍，是同一机制的单位演示，不是第二份独立实证。

在这个简化反例中，正常开业且销售记录完整时：

```text
可观测销量 = min(模拟真实需求, 当日可售上限)
```

它忽略了替代、延后购买、退货与跨日补单，只用于展示截断机制。第6天禾味真实模拟需求40公斤，可售上限20公斤，于是销量20公斤；第12天可售上限为0，真实模拟需求35公斤，销量却为0。服装对应为200／100／100件和175／0／0件。

[![独立14天模拟中真实需求与销量因缺货分离，休店和缺测保留为空，缺货零销量不等于零需求](images/d13-03_stockout.png)](images/d13-03_stockout.png)

四种状态必须分开保存：第3天是真的零需求；第5天休店，目标不定义；第8天缺销售记录；第12天缺货导致零销量。第5、8天销量字段为空，不填零；图中也断开。第8天的真实值只是模拟作者知道，现实缺测并不会自动提供它。

给这组反例预先放一个固定的演示预测：禾味每天20公斤、服装每天100件，不拟合参数。第6天对销量评分时误差恰为0；对作者已知的模拟需求评分时，分别低估20公斤和100件。一个“完美预测销量”的数字，仍然可能漏掉需求。

更完整地看，在相同12个开业且有销量记录的日期上，禾味对销量的MAE为6.25公斤/日、ME为−0.75；对模拟真实需求的MAE为9.00、ME为+5.3333。评分对象一换，连平均偏差方向都变了。服装相应MAE为31.25与45.00件/日。这不是普遍的误差大小关系，只是可复算的反例；两边都排除相同的休店和缺测日期，避免样本集合变化干扰解释。

模拟里可以看到“真实需求−销量”，因为真值由我们编写。现实通常只能知道销量与部分缺货记录，不能从一个20公斤销量推出到底有40还是60公斤需求。缺货标记可以提示标签受截断，但不能自动还原失销量；未来才得到的标记更不能加入过去的预测输入。

因此，这个反例没有修复现实需求，没有把截断销量送进无缺货主实验，也没有给出真实收益。下一步若要估计未满足需求，需要额外观测、明确假设和另外的验证方案。

## 七 把回测交给别人复核，需要留下哪些证据

下载[D13滚动回测实践包](/downloads/d13-rolling-backtest-practice.zip)，使用Python 3.10或以上；计算和测试仅依赖标准库。解压后执行：

```bash
python -m unittest -v
python run.py
```

`predictions.csv`含2072条逐步预测：两个案例×七个候选×（28个一步目标＋24个窗口×五步）。`window_totals.csv`含728条任务总量，`metrics.csv`含28行指标。另有336组泄漏诊断、错误拼接负对照、独立缺货记录与评分、配置冻结回执和运行清单。运行编号为`D13-v2-development-replay`，数据哈希固定，输出不带运行时钟，便于逐字节比较。

预测和指标使用浮点数，正常舍入仍存在；本篇表格只显示四位小数。MA先用稳定求和聚合窗口，再除以窗口长度，避免三个最小正浮点数各自先除以3后消失。MA要求窗口聚合和有限，即使最终平均值可表示，聚合溢出也报错；正均值下溢成零同样报错。这个约定不提供任意精度保证。指标的非有限输入、溢出或非零指标下溢成零会报错，WAPE零分母返回空值及状态。文件入口坚持连续日期与112／28分块；不会自动补缺、合并重复日期或混加公斤与件。

还可下载[文章Markdown与配图](/downloads/d13-rolling-backtest-article.zip)、[黑白配图及重绘脚本](/downloads/d13-rolling-backtest-images.zip)。图形重绘需要Pillow、fontTools和Noto简体中文字体；读者运行预测实验不需要这些库。宽表在手机内可横向滚动，配图提供原图入口。

这次留下的关键证据是：同一目标日的预测必须带上起点；五日累计应使用同一版本的五步；销量为零还要追问是否开业、有记录、有货。模型可以很简单，这三处边界却必须清楚，后续模型选择才有可以复核的基础。

~~~~

# 文件 experiments/d13-rolling-backtest/practice/README.md

SHA256 32f275a5a98e07b74f20a397b6f551148236fdede8b2440da2d45b78dfb238bf

~~~~text
# D13 滚动回测与缺货截断

Python 3.10+，计算与22项测试仅用标准库。在解压目录运行：

```bash
python -m unittest -v
python run.py
```

入口也支持从任意工作目录执行绝对路径。结果稳定，不带运行时钟，运行编号D13-v2-development-replay。

## 数据及信息边界

开发CSV字节沿用D12，固定SHA见source_manifest.json：两案例各140天，初始历史112天、验证28天。禾味是虚构2店8食材SKU背景中的A店SKU01（公斤/日）；匿名服装为模拟终端订单需求（件/日），不是排产量。没有真实企业数据或收益。

原180天序列仅使用前140天，本包不含原40天测试标签、读取入口或评分命令。原测试汇总在D9已展示，开发验证也被多次查看，本次是教学开发回放，非新盲测或无偏泛化证明。

起点表示该日日终已知全部当日记录。每个起点一次发布完整预测，再附实际值评分；扩展历史时只吸收已发生观测，不将未来实际或预测递归填回固定版本。主实验没有缺货截断，不做全样本预处理。代码没有available_at字段或延迟到达过滤，真实系统必须另实现按实际可用时间过滤。

全部候选：季节性朴素周期7、MA3/7/14、SES0.2/0.5/0.8，SES首观测初始化。MA与SES固定起点内保持同一水平。一步起点112—139、目标113—140，28个；五步起点112—135、完整窗口113—117至136—140，24个；不跨块。

## 输出与评分

- predictions.csv：2072行，各行带运行编号、案例、实体、单位、参数、起点、日期、历史截止、目标日期、步长h与任务长度。固定五步中同一目标可有多个起点，不能去重。
- window_totals.csv：728行，其中392个一步目标、336个五日窗口；另存sum_daily_absolute_errors以区分累计抵消与逐日错配。
- metrics.csv：28行，2案例×7方法×2任务。e=实际−预测，ME=mean(e)，MAE=mean(|e|)，RMSE=sqrt(mean(e²))，WAPE=sum(|e|)/sum(实际)。WAPE保存比例，非百分数。n=28或24。
- leakage_diagnostics.csv：336组，每组3种攻击（未来标签及标记扰动、未来无效对象、仅历史前缀），要求预测不变。测试另覆盖最后4个一步起点及完整回放的未来扰动。
- negative_control.json：明确标记错误拼接的负对照，仅示范，不进入五日评分。
- stockout_simulation.csv、stockout_metrics.csv：独立14天一月反例，2案例共28行；服装是禾味数量五倍，不是独立样本。closed与missing的销量为None/CSV空白，不填零；closed的目标未定义，missing日的模拟真值只供作者理解。不把这组数据传入模型。相同12个开业且有销量日期分别对销量与模拟真值评分，固定演示预测20公斤/100件，无参数拟合。
- frozen_selection.json：回放之后，各案例各任务按MAE最小选择并冻结，同分按方法标识排序；不会回灌历史预测，不代表独立效果或业务部署。
- run_manifest.json：参数、数据哈希、边界与运行编号。

五日累计先合计实际与预测再评分，单位为公斤或件，不是公斤/日或件/日。24个窗口重叠，WAPE分母重复覆盖，不等于唯一日期销量。不能将五个不同起点的一步预测拼成固定五步，不做独立窗口显著性推断。两案例不同单位不能合并评分。

## 输入和数值契约

原CSV须为day,date,demand,split且连续、有序、唯一。缺数、负需求、混合实体、非有限值会报错。标准CSV读取器跳过完全空白物理行，空格行不合法；日期缺失仍报错。没有自动补零、插值或清洗。

模型沿用D12；v2将MA改为先math.fsum求和、再除以k。MA要求窗口聚合和有限，即使均值单独可表示，聚合溢出也报错；非零均值下溢成零报错。三个最小正浮点数5e-324的MA3保留5e-324，而[5e-324,0,0]的MA3下溢时明确报错。metrics.py仍沿用D12。浮点计算保留普通舍入，非任意精度。指标聚合必须有限；非零指标下溢成零报错。实际总量0时WAPE返回None、CSV空值、状态undefined_zero_actual_sum，即使全预测为0也不写0%。零需求行保留，负有限预测允许并保留真实误差。日期及单位对齐由回测入口负责，指标函数本身按数组位置配对。

测试以Fraction几何展开核对全部预测和28行指标，并攻击未来标签、未来标记、无效未来行、历史更新、不同起点拼接、缺货零值和缺测口径。通过测试不等于独立审查或真实业务有效。

~~~~

# 文件 experiments/d13-rolling-backtest/practice/baseline.py

SHA256 f9631b4753439da9c207306ebf16de8c251a9b5c10f7a1a50c010de60ae2c90b

~~~~text
"""D12-v1: existing causal moving-average, SES and seasonal-naive baselines.

Only complete, observed, daily demand is accepted. An origin is the one-based
last known day, not the target day. Fixed-origin forecasts never update their
history with either future actuals or their own predictions.
"""
from datetime import date, timedelta
import csv
import math
from pathlib import Path


def _positive_integer(value, name):
    if type(value) is not int or value < 1:
        raise ValueError(f'{name} must be a positive integer')


def validate(rows):
    """Validate one series of consecutive dates; zero demand is legitimate."""
    if not rows:
        raise ValueError('empty history')
    previous_date = None
    previous_day = None
    series = None
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError('each row must be a mapping')
        try:
            current_date = date.fromisoformat(row['date'])
            day = row['day']
            value = row['demand']
            current_series = row['series']
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError('missing or invalid row field') from exc
        if row['date'] != current_date.isoformat():
            raise ValueError('date must use canonical YYYY-MM-DD format')
        _positive_integer(day, 'day')
        if not isinstance(current_series, str) or not current_series.strip():
            raise ValueError('series must be a nonempty string')
        if series is None:
            series = current_series
        elif current_series != series:
            raise ValueError('cannot mix entities or measurement units')
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError('demand must be finite, numeric and nonnegative')
        try:
            finite = math.isfinite(value)
        except OverflowError as exc:
            raise ValueError('demand exceeds supported finite numeric range') from exc
        if not finite or value < 0:
            raise ValueError('demand must be finite, numeric and nonnegative')
        if previous_date is not None:
            if current_date != previous_date + timedelta(days=1) or day != previous_day + 1:
                raise ValueError('days and dates must be ordered, unique and continuous')
        previous_date, previous_day = current_date, day


def load_csv(path, series):
    """Read a single explicitly identified series without imputing bad records.

    DictReader skips empty physical lines; whitespace-only records are invalid.
    Skipping empty lines never permits a missing day in the date sequence.

    D9 CSVs have no entity column: the caller supplies the series identity.
    A separate metadata contract fixes case/unit; these files are not a
    multi-entity format and must never be concatenated.
    """
    rows = []
    try:
        with Path(path).open(encoding='utf-8', newline='') as handle:
            reader = csv.DictReader(handle, strict=True)
            if reader.fieldnames != ['day', 'date', 'demand', 'split']:
                raise ValueError('CSV header must be day,date,demand,split')
            for raw in reader:
                if set(raw) != {'day', 'date', 'demand', 'split'} or any(v is None for v in raw.values()):
                    raise ValueError('missing or surplus CSV field')
                try:
                    # int("True"), float("True"), empty and NULL all fail.
                    row = {'day': int(raw['day']), 'date': raw['date'],
                           'demand': float(raw['demand']), 'split': raw['split'],
                           'series': series}
                except (TypeError, ValueError) as exc:
                    raise ValueError('invalid numeric CSV value') from exc
                if raw['day'] != str(row['day']):
                    raise ValueError('day must be a canonical positive integer')
                if row['split'] not in {'train', 'validation'}:
                    raise ValueError('only train and validation rows are allowed')
                rows.append(row)
    except csv.Error as exc:
        raise ValueError(f'malformed CSV syntax: {exc}') from exc
    validate(rows)
    return rows


def validate_development(rows):
    """D9-v1 source contract; intentionally excludes all 40 test labels."""
    validate(rows)
    if len(rows) != 140 or rows[0]['day'] != 1 or rows[0]['date'] != '2026-04-06':
        raise ValueError('development data must be original days 1..140')
    for row in rows:
        expected = 'train' if row['day'] <= 112 else 'validation'
        if row.get('split') != expected:
            raise ValueError('112/28 development split mismatch')


def levels(history, alpha):
    """Post-observation levels; these are NOT same-day forecasts.

    First-observation initialization: l[0] = y[0]. No parameter fitting.
    """
    if isinstance(alpha, bool) or not isinstance(alpha, (int, float)):
        raise ValueError('alpha must be a finite number in [0, 1]')
    if not 0 <= alpha <= 1:
        raise ValueError('alpha must be a finite number in [0, 1]')
    validate(history)
    result = [float(history[0]['demand'])]
    for row in history[1:]:
        level = alpha * row['demand'] + (1 - alpha) * result[-1]
        if not math.isfinite(level):
            raise ValueError('nonfinite level')
        result.append(level)
    return result


def ses(history, horizon, alpha):
    _positive_integer(horizon, 'horizon')
    return [levels(history, alpha)[-1]] * horizon


def moving_average(history, horizon, k):
    _positive_integer(horizon, 'horizon')
    _positive_integer(k, 'k')
    validate(history)
    if len(history) < k:
        raise ValueError('insufficient history for full moving-average window')
    # Sum before dividing so representable subnormal means are not lost.
    try:
        total = math.fsum(row['demand'] for row in history[-k:])
    except OverflowError as exc:
        raise ValueError('moving-average sum exceeds finite numeric range') from exc
    mean = total / k
    if not math.isfinite(mean):
        raise ValueError('nonfinite forecast')
    if total != 0 and mean == 0:
        raise ValueError('nonzero moving average underflows supported numeric range')
    return [mean] * horizon


def seasonal_naive(history, horizon, period=7):
    _positive_integer(horizon, 'horizon')
    _positive_integer(period, 'period')
    validate(history)
    if len(history) < period:
        raise ValueError('insufficient history for full seasonal cycle')
    return [history[-period + h % period]['demand'] for h in range(horizon)]


def forecast_at(rows, origin, horizon, method='ses', alpha=0.5, k=7):
    """Slice at the information boundary BEFORE validation or forecasting.

    origin is the number of observations known, which equals day for the
    development data (starts at day 1). No row after origin is inspected here.
    """
    _positive_integer(origin, 'origin')
    if origin > len(rows):
        raise ValueError('origin beyond available data')
    history = rows[:origin]
    if method == 'moving_average':
        return moving_average(history, horizon, k)
    if method == 'ses':
        return ses(history, horizon, alpha)
    if method == 'seasonal_naive_7':
        return seasonal_naive(history, horizon, period=7)
    raise ValueError('unknown forecast method')


def windows(start, end, horizon):
    """Return (origin, first target, last target); never cross block edges."""
    for value, name in ((start, 'start'), (end, 'end'), (horizon, 'horizon')):
        _positive_integer(value, name)
    if end < start:
        raise ValueError('evaluation end precedes start')
    return [(first - 1, first, first + horizon - 1)
            for first in range(start, end - horizon + 2)]

~~~~

# 文件 experiments/d13-rolling-backtest/practice/data/apparel-development.csv

SHA256 56badd2fc37decd72b2f55a980acb7add2594b96c7b8d269f6aaae59ee7d47e5

~~~~text
day,date,demand,split
1,2026-04-06,78,train
2,2026-04-07,82,train
3,2026-04-08,87,train
4,2026-04-09,85,train
5,2026-04-10,108,train
6,2026-04-11,140,train
7,2026-04-12,128,train
8,2026-04-13,82,train
9,2026-04-14,85,train
10,2026-04-15,86,train
11,2026-04-16,85,train
12,2026-04-17,112,train
13,2026-04-18,142,train
14,2026-04-19,125,train
15,2026-04-20,80,train
16,2026-04-21,82,train
17,2026-04-22,84,train
18,2026-04-23,88,train
19,2026-04-24,108,train
20,2026-04-25,141,train
21,2026-04-26,125,train
22,2026-04-27,84,train
23,2026-04-28,86,train
24,2026-04-29,88,train
25,2026-04-30,92,train
26,2026-05-01,114,train
27,2026-05-02,139,train
28,2026-05-03,124,train
29,2026-05-04,81,train
30,2026-05-05,85,train
31,2026-05-06,90,train
32,2026-05-07,90,train
33,2026-05-08,112,train
34,2026-05-09,140,train
35,2026-05-10,126,train
36,2026-05-11,83,train
37,2026-05-12,88,train
38,2026-05-13,91,train
39,2026-05-14,90,train
40,2026-05-15,113,train
41,2026-05-16,143,train
42,2026-05-17,126,train
43,2026-05-18,84,train
44,2026-05-19,86,train
45,2026-05-20,90,train
46,2026-05-21,91,train
47,2026-05-22,112,train
48,2026-05-23,141,train
49,2026-05-24,126,train
50,2026-05-25,80,train
51,2026-05-26,84,train
52,2026-05-27,90,train
53,2026-05-28,88,train
54,2026-05-29,116,train
55,2026-05-30,140,train
56,2026-05-31,128,train
57,2026-06-01,86,train
58,2026-06-02,90,train
59,2026-06-03,89,train
60,2026-06-04,95,train
61,2026-06-05,116,train
62,2026-06-06,147,train
63,2026-06-07,127,train
64,2026-06-08,87,train
65,2026-06-09,88,train
66,2026-06-10,93,train
67,2026-06-11,92,train
68,2026-06-12,113,train
69,2026-06-13,145,train
70,2026-06-14,130,train
71,2026-06-15,88,train
72,2026-06-16,88,train
73,2026-06-17,90,train
74,2026-06-18,96,train
75,2026-06-19,117,train
76,2026-06-20,142,train
77,2026-06-21,132,train
78,2026-06-22,87,train
79,2026-06-23,86,train
80,2026-06-24,89,train
81,2026-06-25,90,train
82,2026-06-26,117,train
83,2026-06-27,144,train
84,2026-06-28,130,train
85,2026-06-29,89,train
86,2026-06-30,89,train
87,2026-07-01,89,train
88,2026-07-02,97,train
89,2026-07-03,114,train
90,2026-07-04,143,train
91,2026-07-05,131,train
92,2026-07-06,88,train
93,2026-07-07,89,train
94,2026-07-08,89,train
95,2026-07-09,93,train
96,2026-07-10,118,train
97,2026-07-11,143,train
98,2026-07-12,133,train
99,2026-07-13,84,train
100,2026-07-14,88,train
101,2026-07-15,96,train
102,2026-07-16,98,train
103,2026-07-17,120,train
104,2026-07-18,144,train
105,2026-07-19,130,train
106,2026-07-20,89,train
107,2026-07-21,89,train
108,2026-07-22,94,train
109,2026-07-23,94,train
110,2026-07-24,116,train
111,2026-07-25,146,train
112,2026-07-26,133,train
113,2026-07-27,89,validation
114,2026-07-28,91,validation
115,2026-07-29,92,validation
116,2026-07-30,97,validation
117,2026-07-31,115,validation
118,2026-08-01,239,validation
119,2026-08-02,227,validation
120,2026-08-03,179,validation
121,2026-08-04,91,validation
122,2026-08-05,94,validation
123,2026-08-06,99,validation
124,2026-08-07,115,validation
125,2026-08-08,147,validation
126,2026-08-09,136,validation
127,2026-08-10,92,validation
128,2026-08-11,95,validation
129,2026-08-12,93,validation
130,2026-08-13,96,validation
131,2026-08-14,120,validation
132,2026-08-15,151,validation
133,2026-08-16,138,validation
134,2026-08-17,91,validation
135,2026-08-18,96,validation
136,2026-08-19,94,validation
137,2026-08-20,94,validation
138,2026-08-21,121,validation
139,2026-08-22,146,validation
140,2026-08-23,136,validation

~~~~

# 文件 experiments/d13-rolling-backtest/practice/data/hewei-development.csv

SHA256 292072a63439529f22a73d41b83516928ae5a5b474b907b33d42e74962c23407

~~~~text
day,date,demand,split
1,2026-04-06,23,train
2,2026-04-07,20,train
3,2026-04-08,20,train
4,2026-04-09,24,train
5,2026-04-10,25,train
6,2026-04-11,36,train
7,2026-04-12,32,train
8,2026-04-13,17,train
9,2026-04-14,24,train
10,2026-04-15,22,train
11,2026-04-16,25,train
12,2026-04-17,28,train
13,2026-04-18,33,train
14,2026-04-19,31,train
15,2026-04-20,18,train
16,2026-04-21,19,train
17,2026-04-22,23,train
18,2026-04-23,24,train
19,2026-04-24,25,train
20,2026-04-25,33,train
21,2026-04-26,30,train
22,2026-04-27,22,train
23,2026-04-28,20,train
24,2026-04-29,19,train
25,2026-04-30,27,train
26,2026-05-01,31,train
27,2026-05-02,36,train
28,2026-05-03,31,train
29,2026-05-04,17,train
30,2026-05-05,21,train
31,2026-05-06,19,train
32,2026-05-07,23,train
33,2026-05-08,30,train
34,2026-05-09,35,train
35,2026-05-10,30,train
36,2026-05-11,21,train
37,2026-05-12,19,train
38,2026-05-13,24,train
39,2026-05-14,23,train
40,2026-05-15,27,train
41,2026-05-16,34,train
42,2026-05-17,30,train
43,2026-05-18,20,train
44,2026-05-19,23,train
45,2026-05-20,23,train
46,2026-05-21,27,train
47,2026-05-22,26,train
48,2026-05-23,35,train
49,2026-05-24,30,train
50,2026-05-25,21,train
51,2026-05-26,23,train
52,2026-05-27,22,train
53,2026-05-28,25,train
54,2026-05-29,28,train
55,2026-05-30,37,train
56,2026-05-31,34,train
57,2026-06-01,21,train
58,2026-06-02,22,train
59,2026-06-03,18,train
60,2026-06-04,23,train
61,2026-06-05,31,train
62,2026-06-06,37,train
63,2026-06-07,30,train
64,2026-06-08,21,train
65,2026-06-09,20,train
66,2026-06-10,19,train
67,2026-06-11,21,train
68,2026-06-12,27,train
69,2026-06-13,35,train
70,2026-06-14,30,train
71,2026-06-15,19,train
72,2026-06-16,19,train
73,2026-06-17,18,train
74,2026-06-18,27,train
75,2026-06-19,29,train
76,2026-06-20,33,train
77,2026-06-21,32,train
78,2026-06-22,17,train
79,2026-06-23,22,train
80,2026-06-24,22,train
81,2026-06-25,21,train
82,2026-06-26,26,train
83,2026-06-27,37,train
84,2026-06-28,35,train
85,2026-06-29,21,train
86,2026-06-30,24,train
87,2026-07-01,19,train
88,2026-07-02,22,train
89,2026-07-03,27,train
90,2026-07-04,33,train
91,2026-07-05,29,train
92,2026-07-06,18,train
93,2026-07-07,20,train
94,2026-07-08,19,train
95,2026-07-09,26,train
96,2026-07-10,30,train
97,2026-07-11,37,train
98,2026-07-12,32,train
99,2026-07-13,22,train
100,2026-07-14,21,train
101,2026-07-15,19,train
102,2026-07-16,26,train
103,2026-07-17,31,train
104,2026-07-18,35,train
105,2026-07-19,35,train
106,2026-07-20,19,train
107,2026-07-21,25,train
108,2026-07-22,19,train
109,2026-07-23,22,train
110,2026-07-24,28,train
111,2026-07-25,38,train
112,2026-07-26,29,train
113,2026-07-27,18,validation
114,2026-07-28,20,validation
115,2026-07-29,24,validation
116,2026-07-30,24,validation
117,2026-07-31,30,validation
118,2026-08-01,37,validation
119,2026-08-02,31,validation
120,2026-08-03,19,validation
121,2026-08-04,22,validation
122,2026-08-05,23,validation
123,2026-08-06,26,validation
124,2026-08-07,29,validation
125,2026-08-08,34,validation
126,2026-08-09,32,validation
127,2026-08-10,20,validation
128,2026-08-11,22,validation
129,2026-08-12,20,validation
130,2026-08-13,23,validation
131,2026-08-14,31,validation
132,2026-08-15,33,validation
133,2026-08-16,34,validation
134,2026-08-17,19,validation
135,2026-08-18,22,validation
136,2026-08-19,20,validation
137,2026-08-20,24,validation
138,2026-08-21,31,validation
139,2026-08-22,38,validation
140,2026-08-23,32,validation

~~~~

# 文件 experiments/d13-rolling-backtest/practice/metrics.py

SHA256 ecb4d15e0a46f272e9b954cb8bb42a4c22542117c9f1b90b2c3c8aaf052b23c3

~~~~text
"""Forecast errors are actual minus prediction. WAPE is a ratio, not percent."""
import math


def evaluate(actual, prediction):
    """Use finite binary64 aggregates; reject overflow and nonzero-to-zero underflow.

    Inputs and results retain ordinary floating-point rounding. In particular,
    this is not arbitrary-precision arithmetic. Aggregate sums must be finite,
    even if a mean alone could otherwise be representable.
    """
    actual, prediction = list(actual), list(prediction)
    if not actual or len(actual) != len(prediction):
        raise ValueError('nonempty, equally sized aligned inputs required')
    try:
        if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v)
               for v in actual + prediction):
            raise ValueError('finite numeric inputs required')
        if any(v < 0 for v in actual):
            raise ValueError('actual demand must be nonnegative')
        errors = [a - p for a, p in zip(actual, prediction)]
        if not all(math.isfinite(e) for e in errors):
            raise ValueError('error exceeds finite numeric range')
        n = len(errors)
        scale = max(abs(e) for e in errors)
        error_sum = math.fsum(errors)
        absolute_error_sum = math.fsum(abs(e) for e in errors)
        result = {'n': n, 'actual_sum': math.fsum(actual),
                  'absolute_error_sum': absolute_error_sum,
                  # Sum before dividing: dividing subnormal errors first loses them.
                  'me': error_sum / n,
                  'mae': absolute_error_sum / n,
                  'rmse': scale * math.sqrt(math.fsum((e / scale) ** 2 for e in errors) / n) if scale else 0.0}
        result['wape'] = (result['absolute_error_sum'] / result['actual_sum']
                          if result['actual_sum'] else None)
        result['wape_status'] = 'defined' if result['actual_sum'] else 'undefined_zero_actual_sum'
        if not all(v is None or not isinstance(v, (float, int)) or math.isfinite(v) for v in result.values()):
            raise ValueError('metric exceeds finite numeric range')
        if ((error_sum != 0 and result['me'] == 0)
                or (absolute_error_sum != 0 and (result['mae'] == 0 or result['rmse'] == 0
                    or result['wape'] == 0))):
            raise ValueError('nonzero metric underflows supported numeric range')
        return result
    except OverflowError as exc:
        raise ValueError('metric exceeds finite numeric range') from exc

~~~~

# 文件 experiments/d13-rolling-backtest/practice/results/frozen_selection.json

SHA256 49c30c39c21dd3f2268743c4a31824dc4b0ebeec936d1c81e80b612be634a23f

~~~~text
{
  "run_id": "D13-v2-development-replay",
  "selection_rule": "minimum validation MAE separately by case and task; tie: method lexical order",
  "selection_timing": "after full development replay, never fed back into historical issuance",
  "claim_limit": "retrospective teaching choice on repeatedly inspected data, not unbiased generalization or a new blind test",
  "source_sha256": {
    "data/hewei-development.csv": "292072a63439529f22a73d41b83516928ae5a5b474b907b33d42e74962c23407",
    "data/apparel-development.csv": "56badd2fc37decd72b2f55a980acb7add2594b96c7b8d269f6aaae59ee7d47e5"
  },
  "selected": [
    {
      "case": "hewei",
      "task_horizon": 1,
      "method": "SNaive7",
      "parameters": "{\"method\": \"seasonal_naive_7\"}",
      "mae": 1.7857142857142858,
      "unit": "kg/day"
    },
    {
      "case": "hewei",
      "task_horizon": 5,
      "method": "SNaive7",
      "parameters": "{\"method\": \"seasonal_naive_7\"}",
      "mae": 3.2916666666666665,
      "unit": "kg"
    },
    {
      "case": "apparel",
      "task_horizon": 1,
      "method": "SNaive7",
      "parameters": "{\"method\": \"seasonal_naive_7\"}",
      "mae": 21.107142857142858,
      "unit": "pieces/day"
    },
    {
      "case": "apparel",
      "task_horizon": 5,
      "method": "MA14",
      "parameters": "{\"k\": 14, \"method\": \"moving_average\"}",
      "mae": 109.45238095238095,
      "unit": "pieces"
    }
  ],
  "deployment_scope": "frozen teaching configurations only; no production order or replenishment action"
}

~~~~

# 文件 experiments/d13-rolling-backtest/practice/results/leakage_diagnostics.csv

SHA256 7dfcf056b3b687f1c8e06f4660c1a938bcd78173061e169ba6dc30fb3730f17d

~~~~text
case,method,origin_day,horizon,future_label_flag_attack,invalid_future_attack,prefix_only_attack
hewei,SNaive7,112,5,unchanged,unchanged,unchanged
hewei,MA3,112,5,unchanged,unchanged,unchanged
hewei,MA7,112,5,unchanged,unchanged,unchanged
hewei,MA14,112,5,unchanged,unchanged,unchanged
hewei,SES0.2,112,5,unchanged,unchanged,unchanged
hewei,SES0.5,112,5,unchanged,unchanged,unchanged
hewei,SES0.8,112,5,unchanged,unchanged,unchanged
hewei,SNaive7,113,5,unchanged,unchanged,unchanged
hewei,MA3,113,5,unchanged,unchanged,unchanged
hewei,MA7,113,5,unchanged,unchanged,unchanged
hewei,MA14,113,5,unchanged,unchanged,unchanged
hewei,SES0.2,113,5,unchanged,unchanged,unchanged
hewei,SES0.5,113,5,unchanged,unchanged,unchanged
hewei,SES0.8,113,5,unchanged,unchanged,unchanged
hewei,SNaive7,114,5,unchanged,unchanged,unchanged
hewei,MA3,114,5,unchanged,unchanged,unchanged
hewei,MA7,114,5,unchanged,unchanged,unchanged
hewei,MA14,114,5,unchanged,unchanged,unchanged
hewei,SES0.2,114,5,unchanged,unchanged,unchanged
hewei,SES0.5,114,5,unchanged,unchanged,unchanged
hewei,SES0.8,114,5,unchanged,unchanged,unchanged
hewei,SNaive7,115,5,unchanged,unchanged,unchanged
hewei,MA3,115,5,unchanged,unchanged,unchanged
hewei,MA7,115,5,unchanged,unchanged,unchanged
hewei,MA14,115,5,unchanged,unchanged,unchanged
hewei,SES0.2,115,5,unchanged,unchanged,unchanged
hewei,SES0.5,115,5,unchanged,unchanged,unchanged
hewei,SES0.8,115,5,unchanged,unchanged,unchanged
hewei,SNaive7,116,5,unchanged,unchanged,unchanged
hewei,MA3,116,5,unchanged,unchanged,unchanged
hewei,MA7,116,5,unchanged,unchanged,unchanged
hewei,MA14,116,5,unchanged,unchanged,unchanged
hewei,SES0.2,116,5,unchanged,unchanged,unchanged
hewei,SES0.5,116,5,unchanged,unchanged,unchanged
hewei,SES0.8,116,5,unchanged,unchanged,unchanged
hewei,SNaive7,117,5,unchanged,unchanged,unchanged
hewei,MA3,117,5,unchanged,unchanged,unchanged
hewei,MA7,117,5,unchanged,unchanged,unchanged
hewei,MA14,117,5,unchanged,unchanged,unchanged
hewei,SES0.2,117,5,unchanged,unchanged,unchanged
hewei,SES0.5,117,5,unchanged,unchanged,unchanged
hewei,SES0.8,117,5,unchanged,unchanged,unchanged
hewei,SNaive7,118,5,unchanged,unchanged,unchanged
hewei,MA3,118,5,unchanged,unchanged,unchanged
hewei,MA7,118,5,unchanged,unchanged,unchanged
hewei,MA14,118,5,unchanged,unchanged,unchanged
hewei,SES0.2,118,5,unchanged,unchanged,unchanged
hewei,SES0.5,118,5,unchanged,unchanged,unchanged
hewei,SES0.8,118,5,unchanged,unchanged,unchanged
hewei,SNaive7,119,5,unchanged,unchanged,unchanged
hewei,MA3,119,5,unchanged,unchanged,unchanged
hewei,MA7,119,5,unchanged,unchanged,unchanged
hewei,MA14,119,5,unchanged,unchanged,unchanged
hewei,SES0.2,119,5,unchanged,unchanged,unchanged
hewei,SES0.5,119,5,unchanged,unchanged,unchanged
hewei,SES0.8,119,5,unchanged,unchanged,unchanged
hewei,SNaive7,120,5,unchanged,unchanged,unchanged
hewei,MA3,120,5,unchanged,unchanged,unchanged
hewei,MA7,120,5,unchanged,unchanged,unchanged
hewei,MA14,120,5,unchanged,unchanged,unchanged
hewei,SES0.2,120,5,unchanged,unchanged,unchanged
hewei,SES0.5,120,5,unchanged,unchanged,unchanged
hewei,SES0.8,120,5,unchanged,unchanged,unchanged
hewei,SNaive7,121,5,unchanged,unchanged,unchanged
hewei,MA3,121,5,unchanged,unchanged,unchanged
hewei,MA7,121,5,unchanged,unchanged,unchanged
hewei,MA14,121,5,unchanged,unchanged,unchanged
hewei,SES0.2,121,5,unchanged,unchanged,unchanged
hewei,SES0.5,121,5,unchanged,unchanged,unchanged
hewei,SES0.8,121,5,unchanged,unchanged,unchanged
hewei,SNaive7,122,5,unchanged,unchanged,unchanged
hewei,MA3,122,5,unchanged,unchanged,unchanged
hewei,MA7,122,5,unchanged,unchanged,unchanged
hewei,MA14,122,5,unchanged,unchanged,unchanged
hewei,SES0.2,122,5,unchanged,unchanged,unchanged
hewei,SES0.5,122,5,unchanged,unchanged,unchanged
hewei,SES0.8,122,5,unchanged,unchanged,unchanged
hewei,SNaive7,123,5,unchanged,unchanged,unchanged
hewei,MA3,123,5,unchanged,unchanged,unchanged
hewei,MA7,123,5,unchanged,unchanged,unchanged
hewei,MA14,123,5,unchanged,unchanged,unchanged
hewei,SES0.2,123,5,unchanged,unchanged,unchanged
hewei,SES0.5,123,5,unchanged,unchanged,unchanged
hewei,SES0.8,123,5,unchanged,unchanged,unchanged
hewei,SNaive7,124,5,unchanged,unchanged,unchanged
hewei,MA3,124,5,unchanged,unchanged,unchanged
hewei,MA7,124,5,unchanged,unchanged,unchanged
hewei,MA14,124,5,unchanged,unchanged,unchanged
hewei,SES0.2,124,5,unchanged,unchanged,unchanged
hewei,SES0.5,124,5,unchanged,unchanged,unchanged
hewei,SES0.8,124,5,unchanged,unchanged,unchanged
hewei,SNaive7,125,5,unchanged,unchanged,unchanged
hewei,MA3,125,5,unchanged,unchanged,unchanged
hewei,MA7,125,5,unchanged,unchanged,unchanged
hewei,MA14,125,5,unchanged,unchanged,unchanged
hewei,SES0.2,125,5,unchanged,unchanged,unchanged
hewei,SES0.5,125,5,unchanged,unchanged,unchanged
hewei,SES0.8,125,5,unchanged,unchanged,unchanged
hewei,SNaive7,126,5,unchanged,unchanged,unchanged
hewei,MA3,126,5,unchanged,unchanged,unchanged
hewei,MA7,126,5,unchanged,unchanged,unchanged
hewei,MA14,126,5,unchanged,unchanged,unchanged
hewei,SES0.2,126,5,unchanged,unchanged,unchanged
hewei,SES0.5,126,5,unchanged,unchanged,unchanged
hewei,SES0.8,126,5,unchanged,unchanged,unchanged
hewei,SNaive7,127,5,unchanged,unchanged,unchanged
hewei,MA3,127,5,unchanged,unchanged,unchanged
hewei,MA7,127,5,unchanged,unchanged,unchanged
hewei,MA14,127,5,unchanged,unchanged,unchanged
hewei,SES0.2,127,5,unchanged,unchanged,unchanged
hewei,SES0.5,127,5,unchanged,unchanged,unchanged
hewei,SES0.8,127,5,unchanged,unchanged,unchanged
hewei,SNaive7,128,5,unchanged,unchanged,unchanged
hewei,MA3,128,5,unchanged,unchanged,unchanged
hewei,MA7,128,5,unchanged,unchanged,unchanged
hewei,MA14,128,5,unchanged,unchanged,unchanged
hewei,SES0.2,128,5,unchanged,unchanged,unchanged
hewei,SES0.5,128,5,unchanged,unchanged,unchanged
hewei,SES0.8,128,5,unchanged,unchanged,unchanged
hewei,SNaive7,129,5,unchanged,unchanged,unchanged
hewei,MA3,129,5,unchanged,unchanged,unchanged
hewei,MA7,129,5,unchanged,unchanged,unchanged
hewei,MA14,129,5,unchanged,unchanged,unchanged
hewei,SES0.2,129,5,unchanged,unchanged,unchanged
hewei,SES0.5,129,5,unchanged,unchanged,unchanged
hewei,SES0.8,129,5,unchanged,unchanged,unchanged
hewei,SNaive7,130,5,unchanged,unchanged,unchanged
hewei,MA3,130,5,unchanged,unchanged,unchanged
hewei,MA7,130,5,unchanged,unchanged,unchanged
hewei,MA14,130,5,unchanged,unchanged,unchanged
hewei,SES0.2,130,5,unchanged,unchanged,unchanged
hewei,SES0.5,130,5,unchanged,unchanged,unchanged
hewei,SES0.8,130,5,unchanged,unchanged,unchanged
hewei,SNaive7,131,5,unchanged,unchanged,unchanged
hewei,MA3,131,5,unchanged,unchanged,unchanged
hewei,MA7,131,5,unchanged,unchanged,unchanged
hewei,MA14,131,5,unchanged,unchanged,unchanged
hewei,SES0.2,131,5,unchanged,unchanged,unchanged
hewei,SES0.5,131,5,unchanged,unchanged,unchanged
hewei,SES0.8,131,5,unchanged,unchanged,unchanged
hewei,SNaive7,132,5,unchanged,unchanged,unchanged
hewei,MA3,132,5,unchanged,unchanged,unchanged
hewei,MA7,132,5,unchanged,unchanged,unchanged
hewei,MA14,132,5,unchanged,unchanged,unchanged
hewei,SES0.2,132,5,unchanged,unchanged,unchanged
hewei,SES0.5,132,5,unchanged,unchanged,unchanged
hewei,SES0.8,132,5,unchanged,unchanged,unchanged
hewei,SNaive7,133,5,unchanged,unchanged,unchanged
hewei,MA3,133,5,unchanged,unchanged,unchanged
hewei,MA7,133,5,unchanged,unchanged,unchanged
hewei,MA14,133,5,unchanged,unchanged,unchanged
hewei,SES0.2,133,5,unchanged,unchanged,unchanged
hewei,SES0.5,133,5,unchanged,unchanged,unchanged
hewei,SES0.8,133,5,unchanged,unchanged,unchanged
hewei,SNaive7,134,5,unchanged,unchanged,unchanged
hewei,MA3,134,5,unchanged,unchanged,unchanged
hewei,MA7,134,5,unchanged,unchanged,unchanged
hewei,MA14,134,5,unchanged,unchanged,unchanged
hewei,SES0.2,134,5,unchanged,unchanged,unchanged
hewei,SES0.5,134,5,unchanged,unchanged,unchanged
hewei,SES0.8,134,5,unchanged,unchanged,unchanged
hewei,SNaive7,135,5,unchanged,unchanged,unchanged
hewei,MA3,135,5,unchanged,unchanged,unchanged
hewei,MA7,135,5,unchanged,unchanged,unchanged
hewei,MA14,135,5,unchanged,unchanged,unchanged
hewei,SES0.2,135,5,unchanged,unchanged,unchanged
hewei,SES0.5,135,5,unchanged,unchanged,unchanged
hewei,SES0.8,135,5,unchanged,unchanged,unchanged
apparel,SNaive7,112,5,unchanged,unchanged,unchanged
apparel,MA3,112,5,unchanged,unchanged,unchanged
apparel,MA7,112,5,unchanged,unchanged,unchanged
apparel,MA14,112,5,unchanged,unchanged,unchanged
apparel,SES0.2,112,5,unchanged,unchanged,unchanged
apparel,SES0.5,112,5,unchanged,unchanged,unchanged
apparel,SES0.8,112,5,unchanged,unchanged,unchanged
apparel,SNaive7,113,5,unchanged,unchanged,unchanged
apparel,MA3,113,5,unchanged,unchanged,unchanged
apparel,MA7,113,5,unchanged,unchanged,unchanged
apparel,MA14,113,5,unchanged,unchanged,unchanged
apparel,SES0.2,113,5,unchanged,unchanged,unchanged
apparel,SES0.5,113,5,unchanged,unchanged,unchanged
apparel,SES0.8,113,5,unchanged,unchanged,unchanged
apparel,SNaive7,114,5,unchanged,unchanged,unchanged
apparel,MA3,114,5,unchanged,unchanged,unchanged
apparel,MA7,114,5,unchanged,unchanged,unchanged
apparel,MA14,114,5,unchanged,unchanged,unchanged
apparel,SES0.2,114,5,unchanged,unchanged,unchanged
apparel,SES0.5,114,5,unchanged,unchanged,unchanged
apparel,SES0.8,114,5,unchanged,unchanged,unchanged
apparel,SNaive7,115,5,unchanged,unchanged,unchanged
apparel,MA3,115,5,unchanged,unchanged,unchanged
apparel,MA7,115,5,unchanged,unchanged,unchanged
apparel,MA14,115,5,unchanged,unchanged,unchanged
apparel,SES0.2,115,5,unchanged,unchanged,unchanged
apparel,SES0.5,115,5,unchanged,unchanged,unchanged
apparel,SES0.8,115,5,unchanged,unchanged,unchanged
apparel,SNaive7,116,5,unchanged,unchanged,unchanged
apparel,MA3,116,5,unchanged,unchanged,unchanged
apparel,MA7,116,5,unchanged,unchanged,unchanged
apparel,MA14,116,5,unchanged,unchanged,unchanged
apparel,SES0.2,116,5,unchanged,unchanged,unchanged
apparel,SES0.5,116,5,unchanged,unchanged,unchanged
apparel,SES0.8,116,5,unchanged,unchanged,unchanged
apparel,SNaive7,117,5,unchanged,unchanged,unchanged
apparel,MA3,117,5,unchanged,unchanged,unchanged
apparel,MA7,117,5,unchanged,unchanged,unchanged
apparel,MA14,117,5,unchanged,unchanged,unchanged
apparel,SES0.2,117,5,unchanged,unchanged,unchanged
apparel,SES0.5,117,5,unchanged,unchanged,unchanged
apparel,SES0.8,117,5,unchanged,unchanged,unchanged
apparel,SNaive7,118,5,unchanged,unchanged,unchanged
apparel,MA3,118,5,unchanged,unchanged,unchanged
apparel,MA7,118,5,unchanged,unchanged,unchanged
apparel,MA14,118,5,unchanged,unchanged,unchanged
apparel,SES0.2,118,5,unchanged,unchanged,unchanged
apparel,SES0.5,118,5,unchanged,unchanged,unchanged
apparel,SES0.8,118,5,unchanged,unchanged,unchanged
apparel,SNaive7,119,5,unchanged,unchanged,unchanged
apparel,MA3,119,5,unchanged,unchanged,unchanged
apparel,MA7,119,5,unchanged,unchanged,unchanged
apparel,MA14,119,5,unchanged,unchanged,unchanged
apparel,SES0.2,119,5,unchanged,unchanged,unchanged
apparel,SES0.5,119,5,unchanged,unchanged,unchanged
apparel,SES0.8,119,5,unchanged,unchanged,unchanged
apparel,SNaive7,120,5,unchanged,unchanged,unchanged
apparel,MA3,120,5,unchanged,unchanged,unchanged
apparel,MA7,120,5,unchanged,unchanged,unchanged
apparel,MA14,120,5,unchanged,unchanged,unchanged
apparel,SES0.2,120,5,unchanged,unchanged,unchanged
apparel,SES0.5,120,5,unchanged,unchanged,unchanged
apparel,SES0.8,120,5,unchanged,unchanged,unchanged
apparel,SNaive7,121,5,unchanged,unchanged,unchanged
apparel,MA3,121,5,unchanged,unchanged,unchanged
apparel,MA7,121,5,unchanged,unchanged,unchanged
apparel,MA14,121,5,unchanged,unchanged,unchanged
apparel,SES0.2,121,5,unchanged,unchanged,unchanged
apparel,SES0.5,121,5,unchanged,unchanged,unchanged
apparel,SES0.8,121,5,unchanged,unchanged,unchanged
apparel,SNaive7,122,5,unchanged,unchanged,unchanged
apparel,MA3,122,5,unchanged,unchanged,unchanged
apparel,MA7,122,5,unchanged,unchanged,unchanged
apparel,MA14,122,5,unchanged,unchanged,unchanged
apparel,SES0.2,122,5,unchanged,unchanged,unchanged
apparel,SES0.5,122,5,unchanged,unchanged,unchanged
apparel,SES0.8,122,5,unchanged,unchanged,unchanged
apparel,SNaive7,123,5,unchanged,unchanged,unchanged
apparel,MA3,123,5,unchanged,unchanged,unchanged
apparel,MA7,123,5,unchanged,unchanged,unchanged
apparel,MA14,123,5,unchanged,unchanged,unchanged
apparel,SES0.2,123,5,unchanged,unchanged,unchanged
apparel,SES0.5,123,5,unchanged,unchanged,unchanged
apparel,SES0.8,123,5,unchanged,unchanged,unchanged
apparel,SNaive7,124,5,unchanged,unchanged,unchanged
apparel,MA3,124,5,unchanged,unchanged,unchanged
apparel,MA7,124,5,unchanged,unchanged,unchanged
apparel,MA14,124,5,unchanged,unchanged,unchanged
apparel,SES0.2,124,5,unchanged,unchanged,unchanged
apparel,SES0.5,124,5,unchanged,unchanged,unchanged
apparel,SES0.8,124,5,unchanged,unchanged,unchanged
apparel,SNaive7,125,5,unchanged,unchanged,unchanged
apparel,MA3,125,5,unchanged,unchanged,unchanged
apparel,MA7,125,5,unchanged,unchanged,unchanged
apparel,MA14,125,5,unchanged,unchanged,unchanged
apparel,SES0.2,125,5,unchanged,unchanged,unchanged
apparel,SES0.5,125,5,unchanged,unchanged,unchanged
apparel,SES0.8,125,5,unchanged,unchanged,unchanged
apparel,SNaive7,126,5,unchanged,unchanged,unchanged
apparel,MA3,126,5,unchanged,unchanged,unchanged
apparel,MA7,126,5,unchanged,unchanged,unchanged
apparel,MA14,126,5,unchanged,unchanged,unchanged
apparel,SES0.2,126,5,unchanged,unchanged,unchanged
apparel,SES0.5,126,5,unchanged,unchanged,unchanged
apparel,SES0.8,126,5,unchanged,unchanged,unchanged
apparel,SNaive7,127,5,unchanged,unchanged,unchanged
apparel,MA3,127,5,unchanged,unchanged,unchanged
apparel,MA7,127,5,unchanged,unchanged,unchanged
apparel,MA14,127,5,unchanged,unchanged,unchanged
apparel,SES0.2,127,5,unchanged,unchanged,unchanged
apparel,SES0.5,127,5,unchanged,unchanged,unchanged
apparel,SES0.8,127,5,unchanged,unchanged,unchanged
apparel,SNaive7,128,5,unchanged,unchanged,unchanged
apparel,MA3,128,5,unchanged,unchanged,unchanged
apparel,MA7,128,5,unchanged,unchanged,unchanged
apparel,MA14,128,5,unchanged,unchanged,unchanged
apparel,SES0.2,128,5,unchanged,unchanged,unchanged
apparel,SES0.5,128,5,unchanged,unchanged,unchanged
apparel,SES0.8,128,5,unchanged,unchanged,unchanged
apparel,SNaive7,129,5,unchanged,unchanged,unchanged
apparel,MA3,129,5,unchanged,unchanged,unchanged
apparel,MA7,129,5,unchanged,unchanged,unchanged
apparel,MA14,129,5,unchanged,unchanged,unchanged
apparel,SES0.2,129,5,unchanged,unchanged,unchanged
apparel,SES0.5,129,5,unchanged,unchanged,unchanged
apparel,SES0.8,129,5,unchanged,unchanged,unchanged
apparel,SNaive7,130,5,unchanged,unchanged,unchanged
apparel,MA3,130,5,unchanged,unchanged,unchanged
apparel,MA7,130,5,unchanged,unchanged,unchanged
apparel,MA14,130,5,unchanged,unchanged,unchanged
apparel,SES0.2,130,5,unchanged,unchanged,unchanged
apparel,SES0.5,130,5,unchanged,unchanged,unchanged
apparel,SES0.8,130,5,unchanged,unchanged,unchanged
apparel,SNaive7,131,5,unchanged,unchanged,unchanged
apparel,MA3,131,5,unchanged,unchanged,unchanged
apparel,MA7,131,5,unchanged,unchanged,unchanged
apparel,MA14,131,5,unchanged,unchanged,unchanged
apparel,SES0.2,131,5,unchanged,unchanged,unchanged
apparel,SES0.5,131,5,unchanged,unchanged,unchanged
apparel,SES0.8,131,5,unchanged,unchanged,unchanged
apparel,SNaive7,132,5,unchanged,unchanged,unchanged
apparel,MA3,132,5,unchanged,unchanged,unchanged
apparel,MA7,132,5,unchanged,unchanged,unchanged
apparel,MA14,132,5,unchanged,unchanged,unchanged
apparel,SES0.2,132,5,unchanged,unchanged,unchanged
apparel,SES0.5,132,5,unchanged,unchanged,unchanged
apparel,SES0.8,132,5,unchanged,unchanged,unchanged
apparel,SNaive7,133,5,unchanged,unchanged,unchanged
apparel,MA3,133,5,unchanged,unchanged,unchanged
apparel,MA7,133,5,unchanged,unchanged,unchanged
apparel,MA14,133,5,unchanged,unchanged,unchanged
apparel,SES0.2,133,5,unchanged,unchanged,unchanged
apparel,SES0.5,133,5,unchanged,unchanged,unchanged
apparel,SES0.8,133,5,unchanged,unchanged,unchanged
apparel,SNaive7,134,5,unchanged,unchanged,unchanged
apparel,MA3,134,5,unchanged,unchanged,unchanged
apparel,MA7,134,5,unchanged,unchanged,unchanged
apparel,MA14,134,5,unchanged,unchanged,unchanged
apparel,SES0.2,134,5,unchanged,unchanged,unchanged
apparel,SES0.5,134,5,unchanged,unchanged,unchanged
apparel,SES0.8,134,5,unchanged,unchanged,unchanged
apparel,SNaive7,135,5,unchanged,unchanged,unchanged
apparel,MA3,135,5,unchanged,unchanged,unchanged
apparel,MA7,135,5,unchanged,unchanged,unchanged
apparel,MA14,135,5,unchanged,unchanged,unchanged
apparel,SES0.2,135,5,unchanged,unchanged,unchanged
apparel,SES0.5,135,5,unchanged,unchanged,unchanged
apparel,SES0.8,135,5,unchanged,unchanged,unchanged

~~~~

# 文件 experiments/d13-rolling-backtest/practice/results/metrics.csv

SHA256 d5421abb6dc567ba4a431c45713e03f0e038557c4427df048e02556a3df87aef

~~~~text
case,method,parameters,task_horizon,unit,n,actual_sum,absolute_error_sum,me,mae,rmse,wape,wape_status
hewei,SNaive7,"{""method"": ""seasonal_naive_7""}",1,kg/day,28,738.0,50.0,0.21428571428571427,1.7857142857142858,2.2677868380553634,0.06775067750677506,defined
hewei,SNaive7,"{""method"": ""seasonal_naive_7""}",5,kg,24,3158.0,79.0,1.2083333333333333,3.2916666666666665,4.0259574430603875,0.025015832805573148,defined
hewei,MA3,"{""k"": 3, ""method"": ""moving_average""}",1,kg/day,28,738.0,188.0,0.14285714285714274,6.714285714285714,7.818882313663549,0.25474254742547425,defined
hewei,MA3,"{""k"": 3, ""method"": ""moving_average""}",5,kg,24,3158.0,593.0,-0.8472222222222238,24.708333333333332,28.295317633841822,0.18777707409753008,defined
hewei,MA7,"{""k"": 7, ""method"": ""moving_average""}",1,kg/day,28,738.0,149.0,0.20918367346938752,5.321428571428571,5.937539320109178,0.2018970189701897,defined
hewei,MA7,"{""k"": 7, ""method"": ""moving_average""}",5,kg,24,3158.0,224.99999999999994,0.9583333333333316,9.374999999999998,10.651602351433384,0.071247625079164,defined
hewei,MA14,"{""k"": 14, ""method"": ""moving_average""}",1,kg/day,28,738.0,150.78571428571428,0.14030612244897953,5.3852040816326525,5.9834715246987225,0.20431668602400307,defined
hewei,MA14,"{""k"": 14, ""method"": ""moving_average""}",5,kg,24,3158.0,219.64285714285714,0.40773809523809845,9.151785714285714,10.246795168465592,0.06955125305346964,defined
hewei,SES0.2,"{""alpha"": 0.2, ""method"": ""ses""}",1,kg/day,28,738.0,155.82526638473826,0.16423523372807544,5.565188085169224,6.415324769477774,0.21114534740479438,defined
hewei,SES0.2,"{""alpha"": 0.2, ""method"": ""ses""}",5,kg,24,3158.0,335.9602711980896,0.2381979618387208,13.998344633253732,16.236875007396545,0.10638387308362558,defined
hewei,SES0.5,"{""alpha"": 0.5, ""method"": ""ses""}",1,kg/day,28,738.0,149.49562407264574,0.1410928300845676,5.33912943116592,6.638957830319347,0.20256859630439802,defined
hewei,SES0.5,"{""alpha"": 0.5, ""method"": ""ses""}",5,kg,24,3158.0,558.0850202148459,0.3750256190455333,23.253542508951913,26.55251116763616,0.17672103236695566,defined
hewei,SES0.8,"{""alpha"": 0.8, ""method"": ""ses""}",1,kg/day,28,738.0,136.17355675124733,0.112022206986925,4.863341312544548,6.404872761980587,0.1845170145680858,defined
hewei,SES0.8,"{""alpha"": 0.8, ""method"": ""ses""}",5,kg,24,3158.0,755.2669969584662,1.2834054257538448,31.469458206602756,33.87084329578785,0.23915991037316853,defined
apparel,SNaive7,"{""method"": ""seasonal_naive_7""}",1,pieces/day,28,3374.0,591.0,0.6071428571428571,21.107142857142858,42.27165548145538,0.1751630112625963,defined
apparel,SNaive7,"{""method"": ""seasonal_naive_7""}",5,pieces,24,14642.0,2781.0,4.291666666666667,115.875,159.7541079284035,0.18993306925283432,defined
apparel,MA3,"{""k"": 3, ""method"": ""moving_average""}",1,pieces/day,28,3374.0,994.6666666666666,0.16666666666666785,35.523809523809526,47.85444199912501,0.2948033985378384,defined
apparel,MA3,"{""k"": 3, ""method"": ""moving_average""}",5,pieces,24,14642.0,4061.6666666666665,-6.097222222222214,169.23611111111111,218.70747205647393,0.27739835177343714,defined
apparel,MA7,"{""k"": 7, ""method"": ""moving_average""}",1,pieces/day,28,3374.0,844.2857142857142,0.3163265306122445,30.153061224489793,41.470773719407475,0.25023287323228044,defined
apparel,MA7,"{""k"": 7, ""method"": ""moving_average""}",5,pieces,24,14642.0,2884.714285714286,2.31547619047619,120.19642857142857,151.6127557993998,0.19701641071672488,defined
apparel,MA14,"{""k"": 14, ""method"": ""moving_average""}",1,pieces/day,28,3374.0,846.0,0.7244897959183676,30.214285714285715,41.08213702459122,0.25074096028452875,defined
apparel,MA14,"{""k"": 14, ""method"": ""moving_average""}",5,pieces,24,14642.0,2626.8571428571427,4.369047619047625,109.45238095238095,138.54472159181086,0.1794056237438289,defined
apparel,SES0.2,"{""alpha"": 0.2, ""method"": ""ses""}",1,pieces/day,28,3374.0,865.0125785610547,0.5516985393393286,30.893306377180526,41.02257319739383,0.25637598653261845,defined
apparel,SES0.2,"{""alpha"": 0.2, ""method"": ""ses""}",5,pieces,24,14642.0,2863.333821109762,1.9844056737898417,119.30557587957342,155.05190181282697,0.19555619595067356,defined
apparel,SES0.5,"{""alpha"": 0.5, ""method"": ""ses""}",1,pieces/day,28,3374.0,795.8006717546771,0.16391411060336022,28.42145256266704,40.43259082681276,0.23586267686860612,defined
apparel,SES0.5,"{""alpha"": 0.5, ""method"": ""ses""}",5,pieces,24,14642.0,3743.425877650444,-1.9115646625239602,155.97607823543515,202.6959401517002,0.25566356219440267,defined
apparel,SES0.8,"{""alpha"": 0.8, ""method"": ""ses""}",1,pieces/day,28,3374.0,673.9492942446366,0.11437457462853626,24.069617651594164,37.91669121619455,0.19974786432858227,defined
apparel,SES0.8,"{""alpha"": 0.8, ""method"": ""ses""}",5,pieces,24,14642.0,4587.62207664411,0.3860332656421737,191.15091986017126,236.92204139221332,0.31331936051387177,defined

~~~~

# 文件 experiments/d13-rolling-backtest/practice/results/negative_control.json

SHA256 ccfeffb0e7ec840a27788e550ed4fc4c5c0f6c4af28b91783fcec32dda5d726f

~~~~text
[
  {
    "case": "hewei",
    "method": "SES0.8",
    "origin_day": 117,
    "target_days": [
      118,
      119,
      120,
      121,
      122
    ],
    "fixed_origin_predictions": [
      28.76875166019437,
      28.76875166019437,
      28.76875166019437,
      28.76875166019437,
      28.76875166019437
    ],
    "later_one_step_revisions_WRONG_FOR_ORIGIN117": [
      28.76875166019437,
      35.35375033203887,
      31.870750066407773,
      21.574150013281553,
      21.91483000265631
    ],
    "fixed_total": 143.84375830097184,
    "revised_total": 139.48223207457886,
    "warning": "revisions use new observations; never used as five-day scores"
  },
  {
    "case": "apparel",
    "method": "SES0.8",
    "origin_day": 117,
    "target_days": [
      118,
      119,
      120,
      121,
      122
    ],
    "fixed_origin_predictions": [
      111.2032713427297,
      111.2032713427297,
      111.2032713427297,
      111.2032713427297,
      111.2032713427297
    ],
    "later_one_step_revisions_WRONG_FOR_ORIGIN117": [
      111.2032713427297,
      213.44065426854596,
      224.28813085370922,
      188.05762617074186,
      110.41152523414836
    ],
    "fixed_total": 556.0163567136485,
    "revised_total": 847.4012078698751,
    "warning": "revisions use new observations; never used as five-day scores"
  }
]

~~~~

# 文件 experiments/d13-rolling-backtest/practice/results/predictions.csv

SHA256 3e23a2dc6a69880e02864d88192f671c3ce88eb32d73540716dbba78bf45aecb

~~~~text
run_id,case,series,method,parameters,unit,task_horizon,origin_day,origin_date,history_last_day,target_day,target_date,h,prediction,actual,error
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,1,112,2026-07-26,112,113,2026-07-27,1,19.0,18.0,-1.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,1,113,2026-07-27,113,114,2026-07-28,1,25.0,20.0,-5.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,1,114,2026-07-28,114,115,2026-07-29,1,19.0,24.0,5.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,1,115,2026-07-29,115,116,2026-07-30,1,22.0,24.0,2.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,1,116,2026-07-30,116,117,2026-07-31,1,28.0,30.0,2.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,1,117,2026-07-31,117,118,2026-08-01,1,38.0,37.0,-1.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,1,118,2026-08-01,118,119,2026-08-02,1,29.0,31.0,2.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,1,119,2026-08-02,119,120,2026-08-03,1,18.0,19.0,1.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,1,120,2026-08-03,120,121,2026-08-04,1,20.0,22.0,2.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,1,121,2026-08-04,121,122,2026-08-05,1,24.0,23.0,-1.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,1,122,2026-08-05,122,123,2026-08-06,1,24.0,26.0,2.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,1,123,2026-08-06,123,124,2026-08-07,1,30.0,29.0,-1.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,1,124,2026-08-07,124,125,2026-08-08,1,37.0,34.0,-3.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,1,125,2026-08-08,125,126,2026-08-09,1,31.0,32.0,1.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,1,126,2026-08-09,126,127,2026-08-10,1,19.0,20.0,1.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,1,127,2026-08-10,127,128,2026-08-11,1,22.0,22.0,0.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,1,128,2026-08-11,128,129,2026-08-12,1,23.0,20.0,-3.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,1,129,2026-08-12,129,130,2026-08-13,1,26.0,23.0,-3.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,1,130,2026-08-13,130,131,2026-08-14,1,29.0,31.0,2.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,1,131,2026-08-14,131,132,2026-08-15,1,34.0,33.0,-1.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,1,132,2026-08-15,132,133,2026-08-16,1,32.0,34.0,2.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,1,133,2026-08-16,133,134,2026-08-17,1,20.0,19.0,-1.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,1,134,2026-08-17,134,135,2026-08-18,1,22.0,22.0,0.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,1,135,2026-08-18,135,136,2026-08-19,1,20.0,20.0,0.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,1,136,2026-08-19,136,137,2026-08-20,1,23.0,24.0,1.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,1,137,2026-08-20,137,138,2026-08-21,1,31.0,31.0,0.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,1,138,2026-08-21,138,139,2026-08-22,1,33.0,38.0,5.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,1,139,2026-08-22,139,140,2026-08-23,1,34.0,32.0,-2.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,112,2026-07-26,112,113,2026-07-27,1,19.0,18.0,-1.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,112,2026-07-26,112,114,2026-07-28,2,25.0,20.0,-5.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,112,2026-07-26,112,115,2026-07-29,3,19.0,24.0,5.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,112,2026-07-26,112,116,2026-07-30,4,22.0,24.0,2.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,112,2026-07-26,112,117,2026-07-31,5,28.0,30.0,2.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,113,2026-07-27,113,114,2026-07-28,1,25.0,20.0,-5.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,113,2026-07-27,113,115,2026-07-29,2,19.0,24.0,5.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,113,2026-07-27,113,116,2026-07-30,3,22.0,24.0,2.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,113,2026-07-27,113,117,2026-07-31,4,28.0,30.0,2.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,113,2026-07-27,113,118,2026-08-01,5,38.0,37.0,-1.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,114,2026-07-28,114,115,2026-07-29,1,19.0,24.0,5.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,114,2026-07-28,114,116,2026-07-30,2,22.0,24.0,2.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,114,2026-07-28,114,117,2026-07-31,3,28.0,30.0,2.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,114,2026-07-28,114,118,2026-08-01,4,38.0,37.0,-1.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,114,2026-07-28,114,119,2026-08-02,5,29.0,31.0,2.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,115,2026-07-29,115,116,2026-07-30,1,22.0,24.0,2.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,115,2026-07-29,115,117,2026-07-31,2,28.0,30.0,2.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,115,2026-07-29,115,118,2026-08-01,3,38.0,37.0,-1.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,115,2026-07-29,115,119,2026-08-02,4,29.0,31.0,2.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,115,2026-07-29,115,120,2026-08-03,5,18.0,19.0,1.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,116,2026-07-30,116,117,2026-07-31,1,28.0,30.0,2.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,116,2026-07-30,116,118,2026-08-01,2,38.0,37.0,-1.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,116,2026-07-30,116,119,2026-08-02,3,29.0,31.0,2.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,116,2026-07-30,116,120,2026-08-03,4,18.0,19.0,1.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,116,2026-07-30,116,121,2026-08-04,5,20.0,22.0,2.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,117,2026-07-31,117,118,2026-08-01,1,38.0,37.0,-1.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,117,2026-07-31,117,119,2026-08-02,2,29.0,31.0,2.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,117,2026-07-31,117,120,2026-08-03,3,18.0,19.0,1.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,117,2026-07-31,117,121,2026-08-04,4,20.0,22.0,2.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,117,2026-07-31,117,122,2026-08-05,5,24.0,23.0,-1.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,118,2026-08-01,118,119,2026-08-02,1,29.0,31.0,2.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,118,2026-08-01,118,120,2026-08-03,2,18.0,19.0,1.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,118,2026-08-01,118,121,2026-08-04,3,20.0,22.0,2.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,118,2026-08-01,118,122,2026-08-05,4,24.0,23.0,-1.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,118,2026-08-01,118,123,2026-08-06,5,24.0,26.0,2.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,119,2026-08-02,119,120,2026-08-03,1,18.0,19.0,1.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,119,2026-08-02,119,121,2026-08-04,2,20.0,22.0,2.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,119,2026-08-02,119,122,2026-08-05,3,24.0,23.0,-1.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,119,2026-08-02,119,123,2026-08-06,4,24.0,26.0,2.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,119,2026-08-02,119,124,2026-08-07,5,30.0,29.0,-1.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,120,2026-08-03,120,121,2026-08-04,1,20.0,22.0,2.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,120,2026-08-03,120,122,2026-08-05,2,24.0,23.0,-1.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,120,2026-08-03,120,123,2026-08-06,3,24.0,26.0,2.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,120,2026-08-03,120,124,2026-08-07,4,30.0,29.0,-1.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,120,2026-08-03,120,125,2026-08-08,5,37.0,34.0,-3.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,121,2026-08-04,121,122,2026-08-05,1,24.0,23.0,-1.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,121,2026-08-04,121,123,2026-08-06,2,24.0,26.0,2.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,121,2026-08-04,121,124,2026-08-07,3,30.0,29.0,-1.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,121,2026-08-04,121,125,2026-08-08,4,37.0,34.0,-3.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,121,2026-08-04,121,126,2026-08-09,5,31.0,32.0,1.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,122,2026-08-05,122,123,2026-08-06,1,24.0,26.0,2.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,122,2026-08-05,122,124,2026-08-07,2,30.0,29.0,-1.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,122,2026-08-05,122,125,2026-08-08,3,37.0,34.0,-3.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,122,2026-08-05,122,126,2026-08-09,4,31.0,32.0,1.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,122,2026-08-05,122,127,2026-08-10,5,19.0,20.0,1.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,123,2026-08-06,123,124,2026-08-07,1,30.0,29.0,-1.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,123,2026-08-06,123,125,2026-08-08,2,37.0,34.0,-3.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,123,2026-08-06,123,126,2026-08-09,3,31.0,32.0,1.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,123,2026-08-06,123,127,2026-08-10,4,19.0,20.0,1.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,123,2026-08-06,123,128,2026-08-11,5,22.0,22.0,0.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,124,2026-08-07,124,125,2026-08-08,1,37.0,34.0,-3.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,124,2026-08-07,124,126,2026-08-09,2,31.0,32.0,1.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,124,2026-08-07,124,127,2026-08-10,3,19.0,20.0,1.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,124,2026-08-07,124,128,2026-08-11,4,22.0,22.0,0.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,124,2026-08-07,124,129,2026-08-12,5,23.0,20.0,-3.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,125,2026-08-08,125,126,2026-08-09,1,31.0,32.0,1.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,125,2026-08-08,125,127,2026-08-10,2,19.0,20.0,1.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,125,2026-08-08,125,128,2026-08-11,3,22.0,22.0,0.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,125,2026-08-08,125,129,2026-08-12,4,23.0,20.0,-3.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,125,2026-08-08,125,130,2026-08-13,5,26.0,23.0,-3.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,126,2026-08-09,126,127,2026-08-10,1,19.0,20.0,1.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,126,2026-08-09,126,128,2026-08-11,2,22.0,22.0,0.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,126,2026-08-09,126,129,2026-08-12,3,23.0,20.0,-3.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,126,2026-08-09,126,130,2026-08-13,4,26.0,23.0,-3.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,126,2026-08-09,126,131,2026-08-14,5,29.0,31.0,2.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,127,2026-08-10,127,128,2026-08-11,1,22.0,22.0,0.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,127,2026-08-10,127,129,2026-08-12,2,23.0,20.0,-3.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,127,2026-08-10,127,130,2026-08-13,3,26.0,23.0,-3.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,127,2026-08-10,127,131,2026-08-14,4,29.0,31.0,2.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,127,2026-08-10,127,132,2026-08-15,5,34.0,33.0,-1.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,128,2026-08-11,128,129,2026-08-12,1,23.0,20.0,-3.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,128,2026-08-11,128,130,2026-08-13,2,26.0,23.0,-3.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,128,2026-08-11,128,131,2026-08-14,3,29.0,31.0,2.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,128,2026-08-11,128,132,2026-08-15,4,34.0,33.0,-1.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,128,2026-08-11,128,133,2026-08-16,5,32.0,34.0,2.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,129,2026-08-12,129,130,2026-08-13,1,26.0,23.0,-3.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,129,2026-08-12,129,131,2026-08-14,2,29.0,31.0,2.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,129,2026-08-12,129,132,2026-08-15,3,34.0,33.0,-1.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,129,2026-08-12,129,133,2026-08-16,4,32.0,34.0,2.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,129,2026-08-12,129,134,2026-08-17,5,20.0,19.0,-1.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,130,2026-08-13,130,131,2026-08-14,1,29.0,31.0,2.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,130,2026-08-13,130,132,2026-08-15,2,34.0,33.0,-1.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,130,2026-08-13,130,133,2026-08-16,3,32.0,34.0,2.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,130,2026-08-13,130,134,2026-08-17,4,20.0,19.0,-1.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,130,2026-08-13,130,135,2026-08-18,5,22.0,22.0,0.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,131,2026-08-14,131,132,2026-08-15,1,34.0,33.0,-1.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,131,2026-08-14,131,133,2026-08-16,2,32.0,34.0,2.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,131,2026-08-14,131,134,2026-08-17,3,20.0,19.0,-1.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,131,2026-08-14,131,135,2026-08-18,4,22.0,22.0,0.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,131,2026-08-14,131,136,2026-08-19,5,20.0,20.0,0.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,132,2026-08-15,132,133,2026-08-16,1,32.0,34.0,2.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,132,2026-08-15,132,134,2026-08-17,2,20.0,19.0,-1.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,132,2026-08-15,132,135,2026-08-18,3,22.0,22.0,0.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,132,2026-08-15,132,136,2026-08-19,4,20.0,20.0,0.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,132,2026-08-15,132,137,2026-08-20,5,23.0,24.0,1.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,133,2026-08-16,133,134,2026-08-17,1,20.0,19.0,-1.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,133,2026-08-16,133,135,2026-08-18,2,22.0,22.0,0.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,133,2026-08-16,133,136,2026-08-19,3,20.0,20.0,0.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,133,2026-08-16,133,137,2026-08-20,4,23.0,24.0,1.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,133,2026-08-16,133,138,2026-08-21,5,31.0,31.0,0.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,134,2026-08-17,134,135,2026-08-18,1,22.0,22.0,0.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,134,2026-08-17,134,136,2026-08-19,2,20.0,20.0,0.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,134,2026-08-17,134,137,2026-08-20,3,23.0,24.0,1.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,134,2026-08-17,134,138,2026-08-21,4,31.0,31.0,0.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,134,2026-08-17,134,139,2026-08-22,5,33.0,38.0,5.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,135,2026-08-18,135,136,2026-08-19,1,20.0,20.0,0.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,135,2026-08-18,135,137,2026-08-20,2,23.0,24.0,1.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,135,2026-08-18,135,138,2026-08-21,3,31.0,31.0,0.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,135,2026-08-18,135,139,2026-08-22,4,33.0,38.0,5.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",kg/day,5,135,2026-08-18,135,140,2026-08-23,5,34.0,32.0,-2.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,1,112,2026-07-26,112,113,2026-07-27,1,31.666666666666668,18.0,-13.666666666666668
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,1,113,2026-07-27,113,114,2026-07-28,1,28.333333333333332,20.0,-8.333333333333332
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,1,114,2026-07-28,114,115,2026-07-29,1,22.333333333333332,24.0,1.6666666666666679
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,1,115,2026-07-29,115,116,2026-07-30,1,20.666666666666668,24.0,3.333333333333332
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,1,116,2026-07-30,116,117,2026-07-31,1,22.666666666666668,30.0,7.333333333333332
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,1,117,2026-07-31,117,118,2026-08-01,1,26.0,37.0,11.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,1,118,2026-08-01,118,119,2026-08-02,1,30.333333333333332,31.0,0.6666666666666679
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,1,119,2026-08-02,119,120,2026-08-03,1,32.666666666666664,19.0,-13.666666666666664
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,1,120,2026-08-03,120,121,2026-08-04,1,29.0,22.0,-7.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,1,121,2026-08-04,121,122,2026-08-05,1,24.0,23.0,-1.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,1,122,2026-08-05,122,123,2026-08-06,1,21.333333333333332,26.0,4.666666666666668
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,1,123,2026-08-06,123,124,2026-08-07,1,23.666666666666668,29.0,5.333333333333332
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,1,124,2026-08-07,124,125,2026-08-08,1,26.0,34.0,8.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,1,125,2026-08-08,125,126,2026-08-09,1,29.666666666666668,32.0,2.333333333333332
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,1,126,2026-08-09,126,127,2026-08-10,1,31.666666666666668,20.0,-11.666666666666668
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,1,127,2026-08-10,127,128,2026-08-11,1,28.666666666666668,22.0,-6.666666666666668
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,1,128,2026-08-11,128,129,2026-08-12,1,24.666666666666668,20.0,-4.666666666666668
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,1,129,2026-08-12,129,130,2026-08-13,1,20.666666666666668,23.0,2.333333333333332
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,1,130,2026-08-13,130,131,2026-08-14,1,21.666666666666668,31.0,9.333333333333332
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,1,131,2026-08-14,131,132,2026-08-15,1,24.666666666666668,33.0,8.333333333333332
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,1,132,2026-08-15,132,133,2026-08-16,1,29.0,34.0,5.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,1,133,2026-08-16,133,134,2026-08-17,1,32.666666666666664,19.0,-13.666666666666664
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,1,134,2026-08-17,134,135,2026-08-18,1,28.666666666666668,22.0,-6.666666666666668
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,1,135,2026-08-18,135,136,2026-08-19,1,25.0,20.0,-5.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,1,136,2026-08-19,136,137,2026-08-20,1,20.333333333333332,24.0,3.666666666666668
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,1,137,2026-08-20,137,138,2026-08-21,1,22.0,31.0,9.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,1,138,2026-08-21,138,139,2026-08-22,1,25.0,38.0,13.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,1,139,2026-08-22,139,140,2026-08-23,1,31.0,32.0,1.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,112,2026-07-26,112,113,2026-07-27,1,31.666666666666668,18.0,-13.666666666666668
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,112,2026-07-26,112,114,2026-07-28,2,31.666666666666668,20.0,-11.666666666666668
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,112,2026-07-26,112,115,2026-07-29,3,31.666666666666668,24.0,-7.666666666666668
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,112,2026-07-26,112,116,2026-07-30,4,31.666666666666668,24.0,-7.666666666666668
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,112,2026-07-26,112,117,2026-07-31,5,31.666666666666668,30.0,-1.6666666666666679
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,113,2026-07-27,113,114,2026-07-28,1,28.333333333333332,20.0,-8.333333333333332
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,113,2026-07-27,113,115,2026-07-29,2,28.333333333333332,24.0,-4.333333333333332
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,113,2026-07-27,113,116,2026-07-30,3,28.333333333333332,24.0,-4.333333333333332
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,113,2026-07-27,113,117,2026-07-31,4,28.333333333333332,30.0,1.6666666666666679
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,113,2026-07-27,113,118,2026-08-01,5,28.333333333333332,37.0,8.666666666666668
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,114,2026-07-28,114,115,2026-07-29,1,22.333333333333332,24.0,1.6666666666666679
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,114,2026-07-28,114,116,2026-07-30,2,22.333333333333332,24.0,1.6666666666666679
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,114,2026-07-28,114,117,2026-07-31,3,22.333333333333332,30.0,7.666666666666668
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,114,2026-07-28,114,118,2026-08-01,4,22.333333333333332,37.0,14.666666666666668
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,114,2026-07-28,114,119,2026-08-02,5,22.333333333333332,31.0,8.666666666666668
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,115,2026-07-29,115,116,2026-07-30,1,20.666666666666668,24.0,3.333333333333332
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,115,2026-07-29,115,117,2026-07-31,2,20.666666666666668,30.0,9.333333333333332
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,115,2026-07-29,115,118,2026-08-01,3,20.666666666666668,37.0,16.333333333333332
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,115,2026-07-29,115,119,2026-08-02,4,20.666666666666668,31.0,10.333333333333332
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,115,2026-07-29,115,120,2026-08-03,5,20.666666666666668,19.0,-1.6666666666666679
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,116,2026-07-30,116,117,2026-07-31,1,22.666666666666668,30.0,7.333333333333332
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,116,2026-07-30,116,118,2026-08-01,2,22.666666666666668,37.0,14.333333333333332
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,116,2026-07-30,116,119,2026-08-02,3,22.666666666666668,31.0,8.333333333333332
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,116,2026-07-30,116,120,2026-08-03,4,22.666666666666668,19.0,-3.666666666666668
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,116,2026-07-30,116,121,2026-08-04,5,22.666666666666668,22.0,-0.6666666666666679
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,117,2026-07-31,117,118,2026-08-01,1,26.0,37.0,11.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,117,2026-07-31,117,119,2026-08-02,2,26.0,31.0,5.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,117,2026-07-31,117,120,2026-08-03,3,26.0,19.0,-7.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,117,2026-07-31,117,121,2026-08-04,4,26.0,22.0,-4.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,117,2026-07-31,117,122,2026-08-05,5,26.0,23.0,-3.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,118,2026-08-01,118,119,2026-08-02,1,30.333333333333332,31.0,0.6666666666666679
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,118,2026-08-01,118,120,2026-08-03,2,30.333333333333332,19.0,-11.333333333333332
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,118,2026-08-01,118,121,2026-08-04,3,30.333333333333332,22.0,-8.333333333333332
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,118,2026-08-01,118,122,2026-08-05,4,30.333333333333332,23.0,-7.333333333333332
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,118,2026-08-01,118,123,2026-08-06,5,30.333333333333332,26.0,-4.333333333333332
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,119,2026-08-02,119,120,2026-08-03,1,32.666666666666664,19.0,-13.666666666666664
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,119,2026-08-02,119,121,2026-08-04,2,32.666666666666664,22.0,-10.666666666666664
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,119,2026-08-02,119,122,2026-08-05,3,32.666666666666664,23.0,-9.666666666666664
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,119,2026-08-02,119,123,2026-08-06,4,32.666666666666664,26.0,-6.666666666666664
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,119,2026-08-02,119,124,2026-08-07,5,32.666666666666664,29.0,-3.6666666666666643
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,120,2026-08-03,120,121,2026-08-04,1,29.0,22.0,-7.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,120,2026-08-03,120,122,2026-08-05,2,29.0,23.0,-6.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,120,2026-08-03,120,123,2026-08-06,3,29.0,26.0,-3.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,120,2026-08-03,120,124,2026-08-07,4,29.0,29.0,0.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,120,2026-08-03,120,125,2026-08-08,5,29.0,34.0,5.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,121,2026-08-04,121,122,2026-08-05,1,24.0,23.0,-1.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,121,2026-08-04,121,123,2026-08-06,2,24.0,26.0,2.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,121,2026-08-04,121,124,2026-08-07,3,24.0,29.0,5.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,121,2026-08-04,121,125,2026-08-08,4,24.0,34.0,10.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,121,2026-08-04,121,126,2026-08-09,5,24.0,32.0,8.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,122,2026-08-05,122,123,2026-08-06,1,21.333333333333332,26.0,4.666666666666668
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,122,2026-08-05,122,124,2026-08-07,2,21.333333333333332,29.0,7.666666666666668
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,122,2026-08-05,122,125,2026-08-08,3,21.333333333333332,34.0,12.666666666666668
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,122,2026-08-05,122,126,2026-08-09,4,21.333333333333332,32.0,10.666666666666668
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,122,2026-08-05,122,127,2026-08-10,5,21.333333333333332,20.0,-1.3333333333333321
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,123,2026-08-06,123,124,2026-08-07,1,23.666666666666668,29.0,5.333333333333332
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,123,2026-08-06,123,125,2026-08-08,2,23.666666666666668,34.0,10.333333333333332
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,123,2026-08-06,123,126,2026-08-09,3,23.666666666666668,32.0,8.333333333333332
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,123,2026-08-06,123,127,2026-08-10,4,23.666666666666668,20.0,-3.666666666666668
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,123,2026-08-06,123,128,2026-08-11,5,23.666666666666668,22.0,-1.6666666666666679
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,124,2026-08-07,124,125,2026-08-08,1,26.0,34.0,8.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,124,2026-08-07,124,126,2026-08-09,2,26.0,32.0,6.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,124,2026-08-07,124,127,2026-08-10,3,26.0,20.0,-6.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,124,2026-08-07,124,128,2026-08-11,4,26.0,22.0,-4.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,124,2026-08-07,124,129,2026-08-12,5,26.0,20.0,-6.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,125,2026-08-08,125,126,2026-08-09,1,29.666666666666668,32.0,2.333333333333332
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,125,2026-08-08,125,127,2026-08-10,2,29.666666666666668,20.0,-9.666666666666668
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,125,2026-08-08,125,128,2026-08-11,3,29.666666666666668,22.0,-7.666666666666668
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,125,2026-08-08,125,129,2026-08-12,4,29.666666666666668,20.0,-9.666666666666668
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,125,2026-08-08,125,130,2026-08-13,5,29.666666666666668,23.0,-6.666666666666668
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,126,2026-08-09,126,127,2026-08-10,1,31.666666666666668,20.0,-11.666666666666668
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,126,2026-08-09,126,128,2026-08-11,2,31.666666666666668,22.0,-9.666666666666668
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,126,2026-08-09,126,129,2026-08-12,3,31.666666666666668,20.0,-11.666666666666668
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,126,2026-08-09,126,130,2026-08-13,4,31.666666666666668,23.0,-8.666666666666668
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,126,2026-08-09,126,131,2026-08-14,5,31.666666666666668,31.0,-0.6666666666666679
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,127,2026-08-10,127,128,2026-08-11,1,28.666666666666668,22.0,-6.666666666666668
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,127,2026-08-10,127,129,2026-08-12,2,28.666666666666668,20.0,-8.666666666666668
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,127,2026-08-10,127,130,2026-08-13,3,28.666666666666668,23.0,-5.666666666666668
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,127,2026-08-10,127,131,2026-08-14,4,28.666666666666668,31.0,2.333333333333332
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,127,2026-08-10,127,132,2026-08-15,5,28.666666666666668,33.0,4.333333333333332
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,128,2026-08-11,128,129,2026-08-12,1,24.666666666666668,20.0,-4.666666666666668
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,128,2026-08-11,128,130,2026-08-13,2,24.666666666666668,23.0,-1.6666666666666679
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,128,2026-08-11,128,131,2026-08-14,3,24.666666666666668,31.0,6.333333333333332
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,128,2026-08-11,128,132,2026-08-15,4,24.666666666666668,33.0,8.333333333333332
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,128,2026-08-11,128,133,2026-08-16,5,24.666666666666668,34.0,9.333333333333332
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,129,2026-08-12,129,130,2026-08-13,1,20.666666666666668,23.0,2.333333333333332
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,129,2026-08-12,129,131,2026-08-14,2,20.666666666666668,31.0,10.333333333333332
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,129,2026-08-12,129,132,2026-08-15,3,20.666666666666668,33.0,12.333333333333332
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,129,2026-08-12,129,133,2026-08-16,4,20.666666666666668,34.0,13.333333333333332
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,129,2026-08-12,129,134,2026-08-17,5,20.666666666666668,19.0,-1.6666666666666679
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,130,2026-08-13,130,131,2026-08-14,1,21.666666666666668,31.0,9.333333333333332
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,130,2026-08-13,130,132,2026-08-15,2,21.666666666666668,33.0,11.333333333333332
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,130,2026-08-13,130,133,2026-08-16,3,21.666666666666668,34.0,12.333333333333332
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,130,2026-08-13,130,134,2026-08-17,4,21.666666666666668,19.0,-2.666666666666668
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,130,2026-08-13,130,135,2026-08-18,5,21.666666666666668,22.0,0.33333333333333215
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,131,2026-08-14,131,132,2026-08-15,1,24.666666666666668,33.0,8.333333333333332
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,131,2026-08-14,131,133,2026-08-16,2,24.666666666666668,34.0,9.333333333333332
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,131,2026-08-14,131,134,2026-08-17,3,24.666666666666668,19.0,-5.666666666666668
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,131,2026-08-14,131,135,2026-08-18,4,24.666666666666668,22.0,-2.666666666666668
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,131,2026-08-14,131,136,2026-08-19,5,24.666666666666668,20.0,-4.666666666666668
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,132,2026-08-15,132,133,2026-08-16,1,29.0,34.0,5.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,132,2026-08-15,132,134,2026-08-17,2,29.0,19.0,-10.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,132,2026-08-15,132,135,2026-08-18,3,29.0,22.0,-7.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,132,2026-08-15,132,136,2026-08-19,4,29.0,20.0,-9.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,132,2026-08-15,132,137,2026-08-20,5,29.0,24.0,-5.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,133,2026-08-16,133,134,2026-08-17,1,32.666666666666664,19.0,-13.666666666666664
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,133,2026-08-16,133,135,2026-08-18,2,32.666666666666664,22.0,-10.666666666666664
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,133,2026-08-16,133,136,2026-08-19,3,32.666666666666664,20.0,-12.666666666666664
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,133,2026-08-16,133,137,2026-08-20,4,32.666666666666664,24.0,-8.666666666666664
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,133,2026-08-16,133,138,2026-08-21,5,32.666666666666664,31.0,-1.6666666666666643
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,134,2026-08-17,134,135,2026-08-18,1,28.666666666666668,22.0,-6.666666666666668
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,134,2026-08-17,134,136,2026-08-19,2,28.666666666666668,20.0,-8.666666666666668
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,134,2026-08-17,134,137,2026-08-20,3,28.666666666666668,24.0,-4.666666666666668
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,134,2026-08-17,134,138,2026-08-21,4,28.666666666666668,31.0,2.333333333333332
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,134,2026-08-17,134,139,2026-08-22,5,28.666666666666668,38.0,9.333333333333332
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,135,2026-08-18,135,136,2026-08-19,1,25.0,20.0,-5.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,135,2026-08-18,135,137,2026-08-20,2,25.0,24.0,-1.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,135,2026-08-18,135,138,2026-08-21,3,25.0,31.0,6.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,135,2026-08-18,135,139,2026-08-22,4,25.0,38.0,13.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",kg/day,5,135,2026-08-18,135,140,2026-08-23,5,25.0,32.0,7.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,1,112,2026-07-26,112,113,2026-07-27,1,25.714285714285715,18.0,-7.714285714285715
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,1,113,2026-07-27,113,114,2026-07-28,1,25.571428571428573,20.0,-5.571428571428573
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,1,114,2026-07-28,114,115,2026-07-29,1,24.857142857142858,24.0,-0.8571428571428577
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,1,115,2026-07-29,115,116,2026-07-30,1,25.571428571428573,24.0,-1.571428571428573
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,1,116,2026-07-30,116,117,2026-07-31,1,25.857142857142858,30.0,4.142857142857142
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,1,117,2026-07-31,117,118,2026-08-01,1,26.142857142857142,37.0,10.857142857142858
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,1,118,2026-08-01,118,119,2026-08-02,1,26.0,31.0,5.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,1,119,2026-08-02,119,120,2026-08-03,1,26.285714285714285,19.0,-7.285714285714285
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,1,120,2026-08-03,120,121,2026-08-04,1,26.428571428571427,22.0,-4.428571428571427
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,1,121,2026-08-04,121,122,2026-08-05,1,26.714285714285715,23.0,-3.7142857142857153
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,1,122,2026-08-05,122,123,2026-08-06,1,26.571428571428573,26.0,-0.571428571428573
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,1,123,2026-08-06,123,124,2026-08-07,1,26.857142857142858,29.0,2.1428571428571423
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,1,124,2026-08-07,124,125,2026-08-08,1,26.714285714285715,34.0,7.285714285714285
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,1,125,2026-08-08,125,126,2026-08-09,1,26.285714285714285,32.0,5.714285714285715
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,1,126,2026-08-09,126,127,2026-08-10,1,26.428571428571427,20.0,-6.428571428571427
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,1,127,2026-08-10,127,128,2026-08-11,1,26.571428571428573,22.0,-4.571428571428573
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,1,128,2026-08-11,128,129,2026-08-12,1,26.571428571428573,20.0,-6.571428571428573
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,1,129,2026-08-12,129,130,2026-08-13,1,26.142857142857142,23.0,-3.1428571428571423
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,1,130,2026-08-13,130,131,2026-08-14,1,25.714285714285715,31.0,5.285714285714285
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,1,131,2026-08-14,131,132,2026-08-15,1,26.0,33.0,7.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,1,132,2026-08-15,132,133,2026-08-16,1,25.857142857142858,34.0,8.142857142857142
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,1,133,2026-08-16,133,134,2026-08-17,1,26.142857142857142,19.0,-7.142857142857142
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,1,134,2026-08-17,134,135,2026-08-18,1,26.0,22.0,-4.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,1,135,2026-08-18,135,136,2026-08-19,1,26.0,20.0,-6.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,1,136,2026-08-19,136,137,2026-08-20,1,26.0,24.0,-2.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,1,137,2026-08-20,137,138,2026-08-21,1,26.142857142857142,31.0,4.857142857142858
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,1,138,2026-08-21,138,139,2026-08-22,1,26.142857142857142,38.0,11.857142857142858
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,1,139,2026-08-22,139,140,2026-08-23,1,26.857142857142858,32.0,5.142857142857142
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,112,2026-07-26,112,113,2026-07-27,1,25.714285714285715,18.0,-7.714285714285715
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,112,2026-07-26,112,114,2026-07-28,2,25.714285714285715,20.0,-5.714285714285715
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,112,2026-07-26,112,115,2026-07-29,3,25.714285714285715,24.0,-1.7142857142857153
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,112,2026-07-26,112,116,2026-07-30,4,25.714285714285715,24.0,-1.7142857142857153
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,112,2026-07-26,112,117,2026-07-31,5,25.714285714285715,30.0,4.285714285714285
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,113,2026-07-27,113,114,2026-07-28,1,25.571428571428573,20.0,-5.571428571428573
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,113,2026-07-27,113,115,2026-07-29,2,25.571428571428573,24.0,-1.571428571428573
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,113,2026-07-27,113,116,2026-07-30,3,25.571428571428573,24.0,-1.571428571428573
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,113,2026-07-27,113,117,2026-07-31,4,25.571428571428573,30.0,4.428571428571427
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,113,2026-07-27,113,118,2026-08-01,5,25.571428571428573,37.0,11.428571428571427
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,114,2026-07-28,114,115,2026-07-29,1,24.857142857142858,24.0,-0.8571428571428577
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,114,2026-07-28,114,116,2026-07-30,2,24.857142857142858,24.0,-0.8571428571428577
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,114,2026-07-28,114,117,2026-07-31,3,24.857142857142858,30.0,5.142857142857142
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,114,2026-07-28,114,118,2026-08-01,4,24.857142857142858,37.0,12.142857142857142
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,114,2026-07-28,114,119,2026-08-02,5,24.857142857142858,31.0,6.142857142857142
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,115,2026-07-29,115,116,2026-07-30,1,25.571428571428573,24.0,-1.571428571428573
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,115,2026-07-29,115,117,2026-07-31,2,25.571428571428573,30.0,4.428571428571427
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,115,2026-07-29,115,118,2026-08-01,3,25.571428571428573,37.0,11.428571428571427
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,115,2026-07-29,115,119,2026-08-02,4,25.571428571428573,31.0,5.428571428571427
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,115,2026-07-29,115,120,2026-08-03,5,25.571428571428573,19.0,-6.571428571428573
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,116,2026-07-30,116,117,2026-07-31,1,25.857142857142858,30.0,4.142857142857142
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,116,2026-07-30,116,118,2026-08-01,2,25.857142857142858,37.0,11.142857142857142
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,116,2026-07-30,116,119,2026-08-02,3,25.857142857142858,31.0,5.142857142857142
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,116,2026-07-30,116,120,2026-08-03,4,25.857142857142858,19.0,-6.857142857142858
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,116,2026-07-30,116,121,2026-08-04,5,25.857142857142858,22.0,-3.8571428571428577
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,117,2026-07-31,117,118,2026-08-01,1,26.142857142857142,37.0,10.857142857142858
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,117,2026-07-31,117,119,2026-08-02,2,26.142857142857142,31.0,4.857142857142858
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,117,2026-07-31,117,120,2026-08-03,3,26.142857142857142,19.0,-7.142857142857142
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,117,2026-07-31,117,121,2026-08-04,4,26.142857142857142,22.0,-4.142857142857142
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,117,2026-07-31,117,122,2026-08-05,5,26.142857142857142,23.0,-3.1428571428571423
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,118,2026-08-01,118,119,2026-08-02,1,26.0,31.0,5.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,118,2026-08-01,118,120,2026-08-03,2,26.0,19.0,-7.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,118,2026-08-01,118,121,2026-08-04,3,26.0,22.0,-4.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,118,2026-08-01,118,122,2026-08-05,4,26.0,23.0,-3.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,118,2026-08-01,118,123,2026-08-06,5,26.0,26.0,0.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,119,2026-08-02,119,120,2026-08-03,1,26.285714285714285,19.0,-7.285714285714285
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,119,2026-08-02,119,121,2026-08-04,2,26.285714285714285,22.0,-4.285714285714285
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,119,2026-08-02,119,122,2026-08-05,3,26.285714285714285,23.0,-3.2857142857142847
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,119,2026-08-02,119,123,2026-08-06,4,26.285714285714285,26.0,-0.2857142857142847
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,119,2026-08-02,119,124,2026-08-07,5,26.285714285714285,29.0,2.7142857142857153
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,120,2026-08-03,120,121,2026-08-04,1,26.428571428571427,22.0,-4.428571428571427
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,120,2026-08-03,120,122,2026-08-05,2,26.428571428571427,23.0,-3.428571428571427
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,120,2026-08-03,120,123,2026-08-06,3,26.428571428571427,26.0,-0.42857142857142705
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,120,2026-08-03,120,124,2026-08-07,4,26.428571428571427,29.0,2.571428571428573
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,120,2026-08-03,120,125,2026-08-08,5,26.428571428571427,34.0,7.571428571428573
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,121,2026-08-04,121,122,2026-08-05,1,26.714285714285715,23.0,-3.7142857142857153
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,121,2026-08-04,121,123,2026-08-06,2,26.714285714285715,26.0,-0.7142857142857153
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,121,2026-08-04,121,124,2026-08-07,3,26.714285714285715,29.0,2.2857142857142847
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,121,2026-08-04,121,125,2026-08-08,4,26.714285714285715,34.0,7.285714285714285
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,121,2026-08-04,121,126,2026-08-09,5,26.714285714285715,32.0,5.285714285714285
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,122,2026-08-05,122,123,2026-08-06,1,26.571428571428573,26.0,-0.571428571428573
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,122,2026-08-05,122,124,2026-08-07,2,26.571428571428573,29.0,2.428571428571427
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,122,2026-08-05,122,125,2026-08-08,3,26.571428571428573,34.0,7.428571428571427
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,122,2026-08-05,122,126,2026-08-09,4,26.571428571428573,32.0,5.428571428571427
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,122,2026-08-05,122,127,2026-08-10,5,26.571428571428573,20.0,-6.571428571428573
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,123,2026-08-06,123,124,2026-08-07,1,26.857142857142858,29.0,2.1428571428571423
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,123,2026-08-06,123,125,2026-08-08,2,26.857142857142858,34.0,7.142857142857142
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,123,2026-08-06,123,126,2026-08-09,3,26.857142857142858,32.0,5.142857142857142
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,123,2026-08-06,123,127,2026-08-10,4,26.857142857142858,20.0,-6.857142857142858
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,123,2026-08-06,123,128,2026-08-11,5,26.857142857142858,22.0,-4.857142857142858
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,124,2026-08-07,124,125,2026-08-08,1,26.714285714285715,34.0,7.285714285714285
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,124,2026-08-07,124,126,2026-08-09,2,26.714285714285715,32.0,5.285714285714285
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,124,2026-08-07,124,127,2026-08-10,3,26.714285714285715,20.0,-6.714285714285715
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,124,2026-08-07,124,128,2026-08-11,4,26.714285714285715,22.0,-4.714285714285715
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,124,2026-08-07,124,129,2026-08-12,5,26.714285714285715,20.0,-6.714285714285715
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,125,2026-08-08,125,126,2026-08-09,1,26.285714285714285,32.0,5.714285714285715
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,125,2026-08-08,125,127,2026-08-10,2,26.285714285714285,20.0,-6.285714285714285
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,125,2026-08-08,125,128,2026-08-11,3,26.285714285714285,22.0,-4.285714285714285
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,125,2026-08-08,125,129,2026-08-12,4,26.285714285714285,20.0,-6.285714285714285
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,125,2026-08-08,125,130,2026-08-13,5,26.285714285714285,23.0,-3.2857142857142847
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,126,2026-08-09,126,127,2026-08-10,1,26.428571428571427,20.0,-6.428571428571427
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,126,2026-08-09,126,128,2026-08-11,2,26.428571428571427,22.0,-4.428571428571427
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,126,2026-08-09,126,129,2026-08-12,3,26.428571428571427,20.0,-6.428571428571427
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,126,2026-08-09,126,130,2026-08-13,4,26.428571428571427,23.0,-3.428571428571427
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,126,2026-08-09,126,131,2026-08-14,5,26.428571428571427,31.0,4.571428571428573
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,127,2026-08-10,127,128,2026-08-11,1,26.571428571428573,22.0,-4.571428571428573
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,127,2026-08-10,127,129,2026-08-12,2,26.571428571428573,20.0,-6.571428571428573
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,127,2026-08-10,127,130,2026-08-13,3,26.571428571428573,23.0,-3.571428571428573
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,127,2026-08-10,127,131,2026-08-14,4,26.571428571428573,31.0,4.428571428571427
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,127,2026-08-10,127,132,2026-08-15,5,26.571428571428573,33.0,6.428571428571427
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,128,2026-08-11,128,129,2026-08-12,1,26.571428571428573,20.0,-6.571428571428573
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,128,2026-08-11,128,130,2026-08-13,2,26.571428571428573,23.0,-3.571428571428573
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,128,2026-08-11,128,131,2026-08-14,3,26.571428571428573,31.0,4.428571428571427
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,128,2026-08-11,128,132,2026-08-15,4,26.571428571428573,33.0,6.428571428571427
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,128,2026-08-11,128,133,2026-08-16,5,26.571428571428573,34.0,7.428571428571427
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,129,2026-08-12,129,130,2026-08-13,1,26.142857142857142,23.0,-3.1428571428571423
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,129,2026-08-12,129,131,2026-08-14,2,26.142857142857142,31.0,4.857142857142858
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,129,2026-08-12,129,132,2026-08-15,3,26.142857142857142,33.0,6.857142857142858
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,129,2026-08-12,129,133,2026-08-16,4,26.142857142857142,34.0,7.857142857142858
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,129,2026-08-12,129,134,2026-08-17,5,26.142857142857142,19.0,-7.142857142857142
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,130,2026-08-13,130,131,2026-08-14,1,25.714285714285715,31.0,5.285714285714285
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,130,2026-08-13,130,132,2026-08-15,2,25.714285714285715,33.0,7.285714285714285
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,130,2026-08-13,130,133,2026-08-16,3,25.714285714285715,34.0,8.285714285714285
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,130,2026-08-13,130,134,2026-08-17,4,25.714285714285715,19.0,-6.714285714285715
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,130,2026-08-13,130,135,2026-08-18,5,25.714285714285715,22.0,-3.7142857142857153
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,131,2026-08-14,131,132,2026-08-15,1,26.0,33.0,7.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,131,2026-08-14,131,133,2026-08-16,2,26.0,34.0,8.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,131,2026-08-14,131,134,2026-08-17,3,26.0,19.0,-7.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,131,2026-08-14,131,135,2026-08-18,4,26.0,22.0,-4.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,131,2026-08-14,131,136,2026-08-19,5,26.0,20.0,-6.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,132,2026-08-15,132,133,2026-08-16,1,25.857142857142858,34.0,8.142857142857142
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,132,2026-08-15,132,134,2026-08-17,2,25.857142857142858,19.0,-6.857142857142858
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,132,2026-08-15,132,135,2026-08-18,3,25.857142857142858,22.0,-3.8571428571428577
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,132,2026-08-15,132,136,2026-08-19,4,25.857142857142858,20.0,-5.857142857142858
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,132,2026-08-15,132,137,2026-08-20,5,25.857142857142858,24.0,-1.8571428571428577
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,133,2026-08-16,133,134,2026-08-17,1,26.142857142857142,19.0,-7.142857142857142
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,133,2026-08-16,133,135,2026-08-18,2,26.142857142857142,22.0,-4.142857142857142
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,133,2026-08-16,133,136,2026-08-19,3,26.142857142857142,20.0,-6.142857142857142
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,133,2026-08-16,133,137,2026-08-20,4,26.142857142857142,24.0,-2.1428571428571423
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,133,2026-08-16,133,138,2026-08-21,5,26.142857142857142,31.0,4.857142857142858
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,134,2026-08-17,134,135,2026-08-18,1,26.0,22.0,-4.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,134,2026-08-17,134,136,2026-08-19,2,26.0,20.0,-6.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,134,2026-08-17,134,137,2026-08-20,3,26.0,24.0,-2.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,134,2026-08-17,134,138,2026-08-21,4,26.0,31.0,5.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,134,2026-08-17,134,139,2026-08-22,5,26.0,38.0,12.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,135,2026-08-18,135,136,2026-08-19,1,26.0,20.0,-6.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,135,2026-08-18,135,137,2026-08-20,2,26.0,24.0,-2.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,135,2026-08-18,135,138,2026-08-21,3,26.0,31.0,5.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,135,2026-08-18,135,139,2026-08-22,4,26.0,38.0,12.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",kg/day,5,135,2026-08-18,135,140,2026-08-23,5,26.0,32.0,6.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,1,112,2026-07-26,112,113,2026-07-27,1,26.357142857142858,18.0,-8.357142857142858
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,1,113,2026-07-27,113,114,2026-07-28,1,26.071428571428573,20.0,-6.071428571428573
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,1,114,2026-07-28,114,115,2026-07-29,1,26.0,24.0,-2.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,1,115,2026-07-29,115,116,2026-07-30,1,26.357142857142858,24.0,-2.3571428571428577
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,1,116,2026-07-30,116,117,2026-07-31,1,26.214285714285715,30.0,3.7857142857142847
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,1,117,2026-07-31,117,118,2026-08-01,1,26.142857142857142,37.0,10.857142857142858
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,1,118,2026-08-01,118,119,2026-08-02,1,26.285714285714285,31.0,4.714285714285715
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,1,119,2026-08-02,119,120,2026-08-03,1,26.0,19.0,-7.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,1,120,2026-08-03,120,121,2026-08-04,1,26.0,22.0,-4.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,1,121,2026-08-04,121,122,2026-08-05,1,25.785714285714285,23.0,-2.7857142857142847
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,1,122,2026-08-05,122,123,2026-08-06,1,26.071428571428573,26.0,-0.07142857142857295
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,1,123,2026-08-06,123,124,2026-08-07,1,26.357142857142858,29.0,2.6428571428571423
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,1,124,2026-08-07,124,125,2026-08-08,1,26.428571428571427,34.0,7.571428571428573
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,1,125,2026-08-08,125,126,2026-08-09,1,26.142857142857142,32.0,5.857142857142858
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,1,126,2026-08-09,126,127,2026-08-10,1,26.357142857142858,20.0,-6.357142857142858
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,1,127,2026-08-10,127,128,2026-08-11,1,26.5,22.0,-4.5
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,1,128,2026-08-11,128,129,2026-08-12,1,26.642857142857142,20.0,-6.642857142857142
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,1,129,2026-08-12,129,130,2026-08-13,1,26.357142857142858,23.0,-3.3571428571428577
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,1,130,2026-08-13,130,131,2026-08-14,1,26.285714285714285,31.0,4.714285714285715
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,1,131,2026-08-14,131,132,2026-08-15,1,26.357142857142858,33.0,6.642857142857142
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,1,132,2026-08-15,132,133,2026-08-16,1,26.071428571428573,34.0,7.928571428571427
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,1,133,2026-08-16,133,134,2026-08-17,1,26.285714285714285,19.0,-7.285714285714285
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,1,134,2026-08-17,134,135,2026-08-18,1,26.285714285714285,22.0,-4.285714285714285
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,1,135,2026-08-18,135,136,2026-08-19,1,26.285714285714285,20.0,-6.285714285714285
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,1,136,2026-08-19,136,137,2026-08-20,1,26.071428571428573,24.0,-2.071428571428573
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,1,137,2026-08-20,137,138,2026-08-21,1,25.928571428571427,31.0,5.071428571428573
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,1,138,2026-08-21,138,139,2026-08-22,1,26.071428571428573,38.0,11.928571428571427
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,1,139,2026-08-22,139,140,2026-08-23,1,26.357142857142858,32.0,5.642857142857142
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,112,2026-07-26,112,113,2026-07-27,1,26.357142857142858,18.0,-8.357142857142858
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,112,2026-07-26,112,114,2026-07-28,2,26.357142857142858,20.0,-6.357142857142858
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,112,2026-07-26,112,115,2026-07-29,3,26.357142857142858,24.0,-2.3571428571428577
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,112,2026-07-26,112,116,2026-07-30,4,26.357142857142858,24.0,-2.3571428571428577
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,112,2026-07-26,112,117,2026-07-31,5,26.357142857142858,30.0,3.6428571428571423
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,113,2026-07-27,113,114,2026-07-28,1,26.071428571428573,20.0,-6.071428571428573
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,113,2026-07-27,113,115,2026-07-29,2,26.071428571428573,24.0,-2.071428571428573
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,113,2026-07-27,113,116,2026-07-30,3,26.071428571428573,24.0,-2.071428571428573
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,113,2026-07-27,113,117,2026-07-31,4,26.071428571428573,30.0,3.928571428571427
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,113,2026-07-27,113,118,2026-08-01,5,26.071428571428573,37.0,10.928571428571427
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,114,2026-07-28,114,115,2026-07-29,1,26.0,24.0,-2.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,114,2026-07-28,114,116,2026-07-30,2,26.0,24.0,-2.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,114,2026-07-28,114,117,2026-07-31,3,26.0,30.0,4.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,114,2026-07-28,114,118,2026-08-01,4,26.0,37.0,11.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,114,2026-07-28,114,119,2026-08-02,5,26.0,31.0,5.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,115,2026-07-29,115,116,2026-07-30,1,26.357142857142858,24.0,-2.3571428571428577
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,115,2026-07-29,115,117,2026-07-31,2,26.357142857142858,30.0,3.6428571428571423
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,115,2026-07-29,115,118,2026-08-01,3,26.357142857142858,37.0,10.642857142857142
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,115,2026-07-29,115,119,2026-08-02,4,26.357142857142858,31.0,4.642857142857142
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,115,2026-07-29,115,120,2026-08-03,5,26.357142857142858,19.0,-7.357142857142858
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,116,2026-07-30,116,117,2026-07-31,1,26.214285714285715,30.0,3.7857142857142847
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,116,2026-07-30,116,118,2026-08-01,2,26.214285714285715,37.0,10.785714285714285
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,116,2026-07-30,116,119,2026-08-02,3,26.214285714285715,31.0,4.785714285714285
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,116,2026-07-30,116,120,2026-08-03,4,26.214285714285715,19.0,-7.214285714285715
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,116,2026-07-30,116,121,2026-08-04,5,26.214285714285715,22.0,-4.214285714285715
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,117,2026-07-31,117,118,2026-08-01,1,26.142857142857142,37.0,10.857142857142858
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,117,2026-07-31,117,119,2026-08-02,2,26.142857142857142,31.0,4.857142857142858
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,117,2026-07-31,117,120,2026-08-03,3,26.142857142857142,19.0,-7.142857142857142
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,117,2026-07-31,117,121,2026-08-04,4,26.142857142857142,22.0,-4.142857142857142
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,117,2026-07-31,117,122,2026-08-05,5,26.142857142857142,23.0,-3.1428571428571423
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,118,2026-08-01,118,119,2026-08-02,1,26.285714285714285,31.0,4.714285714285715
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,118,2026-08-01,118,120,2026-08-03,2,26.285714285714285,19.0,-7.285714285714285
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,118,2026-08-01,118,121,2026-08-04,3,26.285714285714285,22.0,-4.285714285714285
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,118,2026-08-01,118,122,2026-08-05,4,26.285714285714285,23.0,-3.2857142857142847
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,118,2026-08-01,118,123,2026-08-06,5,26.285714285714285,26.0,-0.2857142857142847
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,119,2026-08-02,119,120,2026-08-03,1,26.0,19.0,-7.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,119,2026-08-02,119,121,2026-08-04,2,26.0,22.0,-4.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,119,2026-08-02,119,122,2026-08-05,3,26.0,23.0,-3.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,119,2026-08-02,119,123,2026-08-06,4,26.0,26.0,0.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,119,2026-08-02,119,124,2026-08-07,5,26.0,29.0,3.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,120,2026-08-03,120,121,2026-08-04,1,26.0,22.0,-4.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,120,2026-08-03,120,122,2026-08-05,2,26.0,23.0,-3.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,120,2026-08-03,120,123,2026-08-06,3,26.0,26.0,0.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,120,2026-08-03,120,124,2026-08-07,4,26.0,29.0,3.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,120,2026-08-03,120,125,2026-08-08,5,26.0,34.0,8.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,121,2026-08-04,121,122,2026-08-05,1,25.785714285714285,23.0,-2.7857142857142847
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,121,2026-08-04,121,123,2026-08-06,2,25.785714285714285,26.0,0.2142857142857153
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,121,2026-08-04,121,124,2026-08-07,3,25.785714285714285,29.0,3.2142857142857153
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,121,2026-08-04,121,125,2026-08-08,4,25.785714285714285,34.0,8.214285714285715
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,121,2026-08-04,121,126,2026-08-09,5,25.785714285714285,32.0,6.214285714285715
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,122,2026-08-05,122,123,2026-08-06,1,26.071428571428573,26.0,-0.07142857142857295
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,122,2026-08-05,122,124,2026-08-07,2,26.071428571428573,29.0,2.928571428571427
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,122,2026-08-05,122,125,2026-08-08,3,26.071428571428573,34.0,7.928571428571427
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,122,2026-08-05,122,126,2026-08-09,4,26.071428571428573,32.0,5.928571428571427
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,122,2026-08-05,122,127,2026-08-10,5,26.071428571428573,20.0,-6.071428571428573
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,123,2026-08-06,123,124,2026-08-07,1,26.357142857142858,29.0,2.6428571428571423
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,123,2026-08-06,123,125,2026-08-08,2,26.357142857142858,34.0,7.642857142857142
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,123,2026-08-06,123,126,2026-08-09,3,26.357142857142858,32.0,5.642857142857142
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,123,2026-08-06,123,127,2026-08-10,4,26.357142857142858,20.0,-6.357142857142858
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,123,2026-08-06,123,128,2026-08-11,5,26.357142857142858,22.0,-4.357142857142858
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,124,2026-08-07,124,125,2026-08-08,1,26.428571428571427,34.0,7.571428571428573
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,124,2026-08-07,124,126,2026-08-09,2,26.428571428571427,32.0,5.571428571428573
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,124,2026-08-07,124,127,2026-08-10,3,26.428571428571427,20.0,-6.428571428571427
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,124,2026-08-07,124,128,2026-08-11,4,26.428571428571427,22.0,-4.428571428571427
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,124,2026-08-07,124,129,2026-08-12,5,26.428571428571427,20.0,-6.428571428571427
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,125,2026-08-08,125,126,2026-08-09,1,26.142857142857142,32.0,5.857142857142858
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,125,2026-08-08,125,127,2026-08-10,2,26.142857142857142,20.0,-6.142857142857142
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,125,2026-08-08,125,128,2026-08-11,3,26.142857142857142,22.0,-4.142857142857142
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,125,2026-08-08,125,129,2026-08-12,4,26.142857142857142,20.0,-6.142857142857142
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,125,2026-08-08,125,130,2026-08-13,5,26.142857142857142,23.0,-3.1428571428571423
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,126,2026-08-09,126,127,2026-08-10,1,26.357142857142858,20.0,-6.357142857142858
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,126,2026-08-09,126,128,2026-08-11,2,26.357142857142858,22.0,-4.357142857142858
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,126,2026-08-09,126,129,2026-08-12,3,26.357142857142858,20.0,-6.357142857142858
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,126,2026-08-09,126,130,2026-08-13,4,26.357142857142858,23.0,-3.3571428571428577
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,126,2026-08-09,126,131,2026-08-14,5,26.357142857142858,31.0,4.642857142857142
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,127,2026-08-10,127,128,2026-08-11,1,26.5,22.0,-4.5
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,127,2026-08-10,127,129,2026-08-12,2,26.5,20.0,-6.5
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,127,2026-08-10,127,130,2026-08-13,3,26.5,23.0,-3.5
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,127,2026-08-10,127,131,2026-08-14,4,26.5,31.0,4.5
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,127,2026-08-10,127,132,2026-08-15,5,26.5,33.0,6.5
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,128,2026-08-11,128,129,2026-08-12,1,26.642857142857142,20.0,-6.642857142857142
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,128,2026-08-11,128,130,2026-08-13,2,26.642857142857142,23.0,-3.6428571428571423
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,128,2026-08-11,128,131,2026-08-14,3,26.642857142857142,31.0,4.357142857142858
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,128,2026-08-11,128,132,2026-08-15,4,26.642857142857142,33.0,6.357142857142858
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,128,2026-08-11,128,133,2026-08-16,5,26.642857142857142,34.0,7.357142857142858
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,129,2026-08-12,129,130,2026-08-13,1,26.357142857142858,23.0,-3.3571428571428577
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,129,2026-08-12,129,131,2026-08-14,2,26.357142857142858,31.0,4.642857142857142
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,129,2026-08-12,129,132,2026-08-15,3,26.357142857142858,33.0,6.642857142857142
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,129,2026-08-12,129,133,2026-08-16,4,26.357142857142858,34.0,7.642857142857142
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,129,2026-08-12,129,134,2026-08-17,5,26.357142857142858,19.0,-7.357142857142858
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,130,2026-08-13,130,131,2026-08-14,1,26.285714285714285,31.0,4.714285714285715
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,130,2026-08-13,130,132,2026-08-15,2,26.285714285714285,33.0,6.714285714285715
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,130,2026-08-13,130,133,2026-08-16,3,26.285714285714285,34.0,7.714285714285715
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,130,2026-08-13,130,134,2026-08-17,4,26.285714285714285,19.0,-7.285714285714285
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,130,2026-08-13,130,135,2026-08-18,5,26.285714285714285,22.0,-4.285714285714285
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,131,2026-08-14,131,132,2026-08-15,1,26.357142857142858,33.0,6.642857142857142
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,131,2026-08-14,131,133,2026-08-16,2,26.357142857142858,34.0,7.642857142857142
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,131,2026-08-14,131,134,2026-08-17,3,26.357142857142858,19.0,-7.357142857142858
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,131,2026-08-14,131,135,2026-08-18,4,26.357142857142858,22.0,-4.357142857142858
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,131,2026-08-14,131,136,2026-08-19,5,26.357142857142858,20.0,-6.357142857142858
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,132,2026-08-15,132,133,2026-08-16,1,26.071428571428573,34.0,7.928571428571427
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,132,2026-08-15,132,134,2026-08-17,2,26.071428571428573,19.0,-7.071428571428573
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,132,2026-08-15,132,135,2026-08-18,3,26.071428571428573,22.0,-4.071428571428573
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,132,2026-08-15,132,136,2026-08-19,4,26.071428571428573,20.0,-6.071428571428573
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,132,2026-08-15,132,137,2026-08-20,5,26.071428571428573,24.0,-2.071428571428573
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,133,2026-08-16,133,134,2026-08-17,1,26.285714285714285,19.0,-7.285714285714285
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,133,2026-08-16,133,135,2026-08-18,2,26.285714285714285,22.0,-4.285714285714285
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,133,2026-08-16,133,136,2026-08-19,3,26.285714285714285,20.0,-6.285714285714285
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,133,2026-08-16,133,137,2026-08-20,4,26.285714285714285,24.0,-2.2857142857142847
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,133,2026-08-16,133,138,2026-08-21,5,26.285714285714285,31.0,4.714285714285715
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,134,2026-08-17,134,135,2026-08-18,1,26.285714285714285,22.0,-4.285714285714285
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,134,2026-08-17,134,136,2026-08-19,2,26.285714285714285,20.0,-6.285714285714285
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,134,2026-08-17,134,137,2026-08-20,3,26.285714285714285,24.0,-2.2857142857142847
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,134,2026-08-17,134,138,2026-08-21,4,26.285714285714285,31.0,4.714285714285715
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,134,2026-08-17,134,139,2026-08-22,5,26.285714285714285,38.0,11.714285714285715
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,135,2026-08-18,135,136,2026-08-19,1,26.285714285714285,20.0,-6.285714285714285
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,135,2026-08-18,135,137,2026-08-20,2,26.285714285714285,24.0,-2.2857142857142847
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,135,2026-08-18,135,138,2026-08-21,3,26.285714285714285,31.0,4.714285714285715
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,135,2026-08-18,135,139,2026-08-22,4,26.285714285714285,38.0,11.714285714285715
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",kg/day,5,135,2026-08-18,135,140,2026-08-23,5,26.285714285714285,32.0,5.714285714285715
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,1,112,2026-07-26,112,113,2026-07-27,1,28.041724154615732,18.0,-10.041724154615732
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,1,113,2026-07-27,113,114,2026-07-28,1,26.03337932369259,20.0,-6.033379323692589
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,1,114,2026-07-28,114,115,2026-07-29,1,24.82670345895407,24.0,-0.8267034589540714
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,1,115,2026-07-29,115,116,2026-07-30,1,24.661362767163258,24.0,-0.6613627671632578
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,1,116,2026-07-30,116,117,2026-07-31,1,24.52909021373061,30.0,5.470909786269392
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,1,117,2026-07-31,117,118,2026-08-01,1,25.62327217098449,37.0,11.376727829015511
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,1,118,2026-08-01,118,119,2026-08-02,1,27.898617736787592,31.0,3.1013822632124075
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,1,119,2026-08-02,119,120,2026-08-03,1,28.518894189430075,19.0,-9.518894189430075
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,1,120,2026-08-03,120,121,2026-08-04,1,26.615115351544063,22.0,-4.615115351544063
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,1,121,2026-08-04,121,122,2026-08-05,1,25.692092281235254,23.0,-2.6920922812352543
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,1,122,2026-08-05,122,123,2026-08-06,1,25.153673824988207,26.0,0.846326175011793
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,1,123,2026-08-06,123,124,2026-08-07,1,25.322939059990567,29.0,3.677060940009433
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,1,124,2026-08-07,124,125,2026-08-08,1,26.058351247992455,34.0,7.941648752007545
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,1,125,2026-08-08,125,126,2026-08-09,1,27.646680998393965,32.0,4.353319001606035
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,1,126,2026-08-09,126,127,2026-08-10,1,28.517344798715172,20.0,-8.517344798715172
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,1,127,2026-08-10,127,128,2026-08-11,1,26.813875838972137,22.0,-4.8138758389721374
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,1,128,2026-08-11,128,129,2026-08-12,1,25.85110067117771,20.0,-5.851100671177711
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,1,129,2026-08-12,129,130,2026-08-13,1,24.68088053694217,23.0,-1.680880536942169
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,1,130,2026-08-13,130,131,2026-08-14,1,24.344704429553737,31.0,6.655295570446263
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,1,131,2026-08-14,131,132,2026-08-15,1,25.67576354364299,33.0,7.32423645635701
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,1,132,2026-08-15,132,133,2026-08-16,1,27.140610834914394,34.0,6.859389165085606
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,1,133,2026-08-16,133,134,2026-08-17,1,28.512488667931517,19.0,-9.512488667931517
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,1,134,2026-08-17,134,135,2026-08-18,1,26.609990934345216,22.0,-4.609990934345216
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,1,135,2026-08-18,135,136,2026-08-19,1,25.687992747476173,20.0,-5.687992747476173
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,1,136,2026-08-19,136,137,2026-08-20,1,24.55039419798094,24.0,-0.550394197980939
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,1,137,2026-08-20,137,138,2026-08-21,1,24.440315358384755,31.0,6.559684641615245
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,1,138,2026-08-21,138,139,2026-08-22,1,25.752252286707805,38.0,12.247747713292195
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,1,139,2026-08-22,139,140,2026-08-23,1,28.201801829366246,32.0,3.7981981706337535
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,112,2026-07-26,112,113,2026-07-27,1,28.041724154615732,18.0,-10.041724154615732
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,112,2026-07-26,112,114,2026-07-28,2,28.041724154615732,20.0,-8.041724154615732
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,112,2026-07-26,112,115,2026-07-29,3,28.041724154615732,24.0,-4.041724154615732
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,112,2026-07-26,112,116,2026-07-30,4,28.041724154615732,24.0,-4.041724154615732
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,112,2026-07-26,112,117,2026-07-31,5,28.041724154615732,30.0,1.958275845384268
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,113,2026-07-27,113,114,2026-07-28,1,26.03337932369259,20.0,-6.033379323692589
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,113,2026-07-27,113,115,2026-07-29,2,26.03337932369259,24.0,-2.0333793236925892
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,113,2026-07-27,113,116,2026-07-30,3,26.03337932369259,24.0,-2.0333793236925892
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,113,2026-07-27,113,117,2026-07-31,4,26.03337932369259,30.0,3.9666206763074108
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,113,2026-07-27,113,118,2026-08-01,5,26.03337932369259,37.0,10.96662067630741
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,114,2026-07-28,114,115,2026-07-29,1,24.82670345895407,24.0,-0.8267034589540714
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,114,2026-07-28,114,116,2026-07-30,2,24.82670345895407,24.0,-0.8267034589540714
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,114,2026-07-28,114,117,2026-07-31,3,24.82670345895407,30.0,5.173296541045929
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,114,2026-07-28,114,118,2026-08-01,4,24.82670345895407,37.0,12.173296541045929
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,114,2026-07-28,114,119,2026-08-02,5,24.82670345895407,31.0,6.173296541045929
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,115,2026-07-29,115,116,2026-07-30,1,24.661362767163258,24.0,-0.6613627671632578
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,115,2026-07-29,115,117,2026-07-31,2,24.661362767163258,30.0,5.338637232836742
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,115,2026-07-29,115,118,2026-08-01,3,24.661362767163258,37.0,12.338637232836742
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,115,2026-07-29,115,119,2026-08-02,4,24.661362767163258,31.0,6.338637232836742
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,115,2026-07-29,115,120,2026-08-03,5,24.661362767163258,19.0,-5.661362767163258
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,116,2026-07-30,116,117,2026-07-31,1,24.52909021373061,30.0,5.470909786269392
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,116,2026-07-30,116,118,2026-08-01,2,24.52909021373061,37.0,12.470909786269392
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,116,2026-07-30,116,119,2026-08-02,3,24.52909021373061,31.0,6.470909786269392
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,116,2026-07-30,116,120,2026-08-03,4,24.52909021373061,19.0,-5.529090213730608
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,116,2026-07-30,116,121,2026-08-04,5,24.52909021373061,22.0,-2.5290902137306084
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,117,2026-07-31,117,118,2026-08-01,1,25.62327217098449,37.0,11.376727829015511
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,117,2026-07-31,117,119,2026-08-02,2,25.62327217098449,31.0,5.376727829015511
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,117,2026-07-31,117,120,2026-08-03,3,25.62327217098449,19.0,-6.623272170984489
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,117,2026-07-31,117,121,2026-08-04,4,25.62327217098449,22.0,-3.623272170984489
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,117,2026-07-31,117,122,2026-08-05,5,25.62327217098449,23.0,-2.623272170984489
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,118,2026-08-01,118,119,2026-08-02,1,27.898617736787592,31.0,3.1013822632124075
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,118,2026-08-01,118,120,2026-08-03,2,27.898617736787592,19.0,-8.898617736787592
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,118,2026-08-01,118,121,2026-08-04,3,27.898617736787592,22.0,-5.8986177367875925
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,118,2026-08-01,118,122,2026-08-05,4,27.898617736787592,23.0,-4.8986177367875925
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,118,2026-08-01,118,123,2026-08-06,5,27.898617736787592,26.0,-1.8986177367875925
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,119,2026-08-02,119,120,2026-08-03,1,28.518894189430075,19.0,-9.518894189430075
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,119,2026-08-02,119,121,2026-08-04,2,28.518894189430075,22.0,-6.518894189430075
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,119,2026-08-02,119,122,2026-08-05,3,28.518894189430075,23.0,-5.518894189430075
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,119,2026-08-02,119,123,2026-08-06,4,28.518894189430075,26.0,-2.5188941894300747
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,119,2026-08-02,119,124,2026-08-07,5,28.518894189430075,29.0,0.4811058105699253
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,120,2026-08-03,120,121,2026-08-04,1,26.615115351544063,22.0,-4.615115351544063
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,120,2026-08-03,120,122,2026-08-05,2,26.615115351544063,23.0,-3.6151153515440626
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,120,2026-08-03,120,123,2026-08-06,3,26.615115351544063,26.0,-0.6151153515440626
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,120,2026-08-03,120,124,2026-08-07,4,26.615115351544063,29.0,2.3848846484559374
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,120,2026-08-03,120,125,2026-08-08,5,26.615115351544063,34.0,7.384884648455937
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,121,2026-08-04,121,122,2026-08-05,1,25.692092281235254,23.0,-2.6920922812352543
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,121,2026-08-04,121,123,2026-08-06,2,25.692092281235254,26.0,0.30790771876474565
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,121,2026-08-04,121,124,2026-08-07,3,25.692092281235254,29.0,3.3079077187647457
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,121,2026-08-04,121,125,2026-08-08,4,25.692092281235254,34.0,8.307907718764746
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,121,2026-08-04,121,126,2026-08-09,5,25.692092281235254,32.0,6.307907718764746
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,122,2026-08-05,122,123,2026-08-06,1,25.153673824988207,26.0,0.846326175011793
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,122,2026-08-05,122,124,2026-08-07,2,25.153673824988207,29.0,3.846326175011793
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,122,2026-08-05,122,125,2026-08-08,3,25.153673824988207,34.0,8.846326175011793
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,122,2026-08-05,122,126,2026-08-09,4,25.153673824988207,32.0,6.846326175011793
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,122,2026-08-05,122,127,2026-08-10,5,25.153673824988207,20.0,-5.153673824988207
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,123,2026-08-06,123,124,2026-08-07,1,25.322939059990567,29.0,3.677060940009433
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,123,2026-08-06,123,125,2026-08-08,2,25.322939059990567,34.0,8.677060940009433
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,123,2026-08-06,123,126,2026-08-09,3,25.322939059990567,32.0,6.677060940009433
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,123,2026-08-06,123,127,2026-08-10,4,25.322939059990567,20.0,-5.322939059990567
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,123,2026-08-06,123,128,2026-08-11,5,25.322939059990567,22.0,-3.322939059990567
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,124,2026-08-07,124,125,2026-08-08,1,26.058351247992455,34.0,7.941648752007545
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,124,2026-08-07,124,126,2026-08-09,2,26.058351247992455,32.0,5.941648752007545
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,124,2026-08-07,124,127,2026-08-10,3,26.058351247992455,20.0,-6.058351247992455
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,124,2026-08-07,124,128,2026-08-11,4,26.058351247992455,22.0,-4.058351247992455
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,124,2026-08-07,124,129,2026-08-12,5,26.058351247992455,20.0,-6.058351247992455
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,125,2026-08-08,125,126,2026-08-09,1,27.646680998393965,32.0,4.353319001606035
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,125,2026-08-08,125,127,2026-08-10,2,27.646680998393965,20.0,-7.646680998393965
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,125,2026-08-08,125,128,2026-08-11,3,27.646680998393965,22.0,-5.646680998393965
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,125,2026-08-08,125,129,2026-08-12,4,27.646680998393965,20.0,-7.646680998393965
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,125,2026-08-08,125,130,2026-08-13,5,27.646680998393965,23.0,-4.646680998393965
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,126,2026-08-09,126,127,2026-08-10,1,28.517344798715172,20.0,-8.517344798715172
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,126,2026-08-09,126,128,2026-08-11,2,28.517344798715172,22.0,-6.517344798715172
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,126,2026-08-09,126,129,2026-08-12,3,28.517344798715172,20.0,-8.517344798715172
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,126,2026-08-09,126,130,2026-08-13,4,28.517344798715172,23.0,-5.517344798715172
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,126,2026-08-09,126,131,2026-08-14,5,28.517344798715172,31.0,2.482655201284828
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,127,2026-08-10,127,128,2026-08-11,1,26.813875838972137,22.0,-4.8138758389721374
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,127,2026-08-10,127,129,2026-08-12,2,26.813875838972137,20.0,-6.8138758389721374
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,127,2026-08-10,127,130,2026-08-13,3,26.813875838972137,23.0,-3.8138758389721374
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,127,2026-08-10,127,131,2026-08-14,4,26.813875838972137,31.0,4.1861241610278626
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,127,2026-08-10,127,132,2026-08-15,5,26.813875838972137,33.0,6.1861241610278626
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,128,2026-08-11,128,129,2026-08-12,1,25.85110067117771,20.0,-5.851100671177711
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,128,2026-08-11,128,130,2026-08-13,2,25.85110067117771,23.0,-2.8511006711777114
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,128,2026-08-11,128,131,2026-08-14,3,25.85110067117771,31.0,5.148899328822289
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,128,2026-08-11,128,132,2026-08-15,4,25.85110067117771,33.0,7.148899328822289
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,128,2026-08-11,128,133,2026-08-16,5,25.85110067117771,34.0,8.148899328822289
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,129,2026-08-12,129,130,2026-08-13,1,24.68088053694217,23.0,-1.680880536942169
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,129,2026-08-12,129,131,2026-08-14,2,24.68088053694217,31.0,6.319119463057831
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,129,2026-08-12,129,132,2026-08-15,3,24.68088053694217,33.0,8.319119463057831
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,129,2026-08-12,129,133,2026-08-16,4,24.68088053694217,34.0,9.319119463057831
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,129,2026-08-12,129,134,2026-08-17,5,24.68088053694217,19.0,-5.680880536942169
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,130,2026-08-13,130,131,2026-08-14,1,24.344704429553737,31.0,6.655295570446263
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,130,2026-08-13,130,132,2026-08-15,2,24.344704429553737,33.0,8.655295570446263
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,130,2026-08-13,130,133,2026-08-16,3,24.344704429553737,34.0,9.655295570446263
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,130,2026-08-13,130,134,2026-08-17,4,24.344704429553737,19.0,-5.344704429553737
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,130,2026-08-13,130,135,2026-08-18,5,24.344704429553737,22.0,-2.3447044295537367
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,131,2026-08-14,131,132,2026-08-15,1,25.67576354364299,33.0,7.32423645635701
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,131,2026-08-14,131,133,2026-08-16,2,25.67576354364299,34.0,8.32423645635701
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,131,2026-08-14,131,134,2026-08-17,3,25.67576354364299,19.0,-6.67576354364299
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,131,2026-08-14,131,135,2026-08-18,4,25.67576354364299,22.0,-3.67576354364299
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,131,2026-08-14,131,136,2026-08-19,5,25.67576354364299,20.0,-5.67576354364299
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,132,2026-08-15,132,133,2026-08-16,1,27.140610834914394,34.0,6.859389165085606
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,132,2026-08-15,132,134,2026-08-17,2,27.140610834914394,19.0,-8.140610834914394
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,132,2026-08-15,132,135,2026-08-18,3,27.140610834914394,22.0,-5.140610834914394
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,132,2026-08-15,132,136,2026-08-19,4,27.140610834914394,20.0,-7.140610834914394
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,132,2026-08-15,132,137,2026-08-20,5,27.140610834914394,24.0,-3.140610834914394
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,133,2026-08-16,133,134,2026-08-17,1,28.512488667931517,19.0,-9.512488667931517
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,133,2026-08-16,133,135,2026-08-18,2,28.512488667931517,22.0,-6.5124886679315175
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,133,2026-08-16,133,136,2026-08-19,3,28.512488667931517,20.0,-8.512488667931517
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,133,2026-08-16,133,137,2026-08-20,4,28.512488667931517,24.0,-4.5124886679315175
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,133,2026-08-16,133,138,2026-08-21,5,28.512488667931517,31.0,2.4875113320684825
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,134,2026-08-17,134,135,2026-08-18,1,26.609990934345216,22.0,-4.609990934345216
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,134,2026-08-17,134,136,2026-08-19,2,26.609990934345216,20.0,-6.609990934345216
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,134,2026-08-17,134,137,2026-08-20,3,26.609990934345216,24.0,-2.609990934345216
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,134,2026-08-17,134,138,2026-08-21,4,26.609990934345216,31.0,4.390009065654784
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,134,2026-08-17,134,139,2026-08-22,5,26.609990934345216,38.0,11.390009065654784
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,135,2026-08-18,135,136,2026-08-19,1,25.687992747476173,20.0,-5.687992747476173
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,135,2026-08-18,135,137,2026-08-20,2,25.687992747476173,24.0,-1.687992747476173
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,135,2026-08-18,135,138,2026-08-21,3,25.687992747476173,31.0,5.312007252523827
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,135,2026-08-18,135,139,2026-08-22,4,25.687992747476173,38.0,12.312007252523827
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",kg/day,5,135,2026-08-18,135,140,2026-08-23,5,25.687992747476173,32.0,6.312007252523827
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,1,112,2026-07-26,112,113,2026-07-27,1,30.2663511697844,18.0,-12.2663511697844
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,1,113,2026-07-27,113,114,2026-07-28,1,24.1331755848922,20.0,-4.1331755848922
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,1,114,2026-07-28,114,115,2026-07-29,1,22.0665877924461,24.0,1.9334122075539
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,1,115,2026-07-29,115,116,2026-07-30,1,23.03329389622305,24.0,0.96670610377695
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,1,116,2026-07-30,116,117,2026-07-31,1,23.516646948111525,30.0,6.483353051888475
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,1,117,2026-07-31,117,118,2026-08-01,1,26.758323474055764,37.0,10.241676525944236
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,1,118,2026-08-01,118,119,2026-08-02,1,31.879161737027882,31.0,-0.8791617370278821
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,1,119,2026-08-02,119,120,2026-08-03,1,31.439580868513943,19.0,-12.439580868513943
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,1,120,2026-08-03,120,121,2026-08-04,1,25.21979043425697,22.0,-3.2197904342569714
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,1,121,2026-08-04,121,122,2026-08-05,1,23.609895217128486,23.0,-0.6098952171284857
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,1,122,2026-08-05,122,123,2026-08-06,1,23.30494760856424,26.0,2.695052391435759
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,1,123,2026-08-06,123,124,2026-08-07,1,24.65247380428212,29.0,4.3475261957178795
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,1,124,2026-08-07,124,125,2026-08-08,1,26.826236902141062,34.0,7.173763097858938
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,1,125,2026-08-08,125,126,2026-08-09,1,30.41311845107053,32.0,1.586881548929469
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,1,126,2026-08-09,126,127,2026-08-10,1,31.206559225535266,20.0,-11.206559225535266
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,1,127,2026-08-10,127,128,2026-08-11,1,25.603279612767633,22.0,-3.6032796127676328
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,1,128,2026-08-11,128,129,2026-08-12,1,23.801639806383818,20.0,-3.801639806383818
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,1,129,2026-08-12,129,130,2026-08-13,1,21.90081990319191,23.0,1.099180096808091
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,1,130,2026-08-13,130,131,2026-08-14,1,22.450409951595955,31.0,8.549590048404045
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,1,131,2026-08-14,131,132,2026-08-15,1,26.72520497579798,33.0,6.274795024202021
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,1,132,2026-08-15,132,133,2026-08-16,1,29.86260248789899,34.0,4.1373975121010105
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,1,133,2026-08-16,133,134,2026-08-17,1,31.931301243949495,19.0,-12.931301243949495
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,1,134,2026-08-17,134,135,2026-08-18,1,25.465650621974746,22.0,-3.4656506219747456
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,1,135,2026-08-18,135,136,2026-08-19,1,23.732825310987373,20.0,-3.732825310987373
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,1,136,2026-08-19,136,137,2026-08-20,1,21.866412655493686,24.0,2.1335873445063136
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,1,137,2026-08-20,137,138,2026-08-21,1,22.933206327746845,31.0,8.066793672253155
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,1,138,2026-08-21,138,139,2026-08-22,1,26.966603163873422,38.0,11.033396836126578
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,1,139,2026-08-22,139,140,2026-08-23,1,32.483301581936715,32.0,-0.4833015819367148
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,112,2026-07-26,112,113,2026-07-27,1,30.2663511697844,18.0,-12.2663511697844
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,112,2026-07-26,112,114,2026-07-28,2,30.2663511697844,20.0,-10.2663511697844
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,112,2026-07-26,112,115,2026-07-29,3,30.2663511697844,24.0,-6.2663511697844
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,112,2026-07-26,112,116,2026-07-30,4,30.2663511697844,24.0,-6.2663511697844
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,112,2026-07-26,112,117,2026-07-31,5,30.2663511697844,30.0,-0.2663511697844001
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,113,2026-07-27,113,114,2026-07-28,1,24.1331755848922,20.0,-4.1331755848922
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,113,2026-07-27,113,115,2026-07-29,2,24.1331755848922,24.0,-0.13317558489220005
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,113,2026-07-27,113,116,2026-07-30,3,24.1331755848922,24.0,-0.13317558489220005
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,113,2026-07-27,113,117,2026-07-31,4,24.1331755848922,30.0,5.8668244151078
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,113,2026-07-27,113,118,2026-08-01,5,24.1331755848922,37.0,12.8668244151078
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,114,2026-07-28,114,115,2026-07-29,1,22.0665877924461,24.0,1.9334122075539
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,114,2026-07-28,114,116,2026-07-30,2,22.0665877924461,24.0,1.9334122075539
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,114,2026-07-28,114,117,2026-07-31,3,22.0665877924461,30.0,7.9334122075539
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,114,2026-07-28,114,118,2026-08-01,4,22.0665877924461,37.0,14.9334122075539
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,114,2026-07-28,114,119,2026-08-02,5,22.0665877924461,31.0,8.9334122075539
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,115,2026-07-29,115,116,2026-07-30,1,23.03329389622305,24.0,0.96670610377695
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,115,2026-07-29,115,117,2026-07-31,2,23.03329389622305,30.0,6.96670610377695
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,115,2026-07-29,115,118,2026-08-01,3,23.03329389622305,37.0,13.96670610377695
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,115,2026-07-29,115,119,2026-08-02,4,23.03329389622305,31.0,7.96670610377695
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,115,2026-07-29,115,120,2026-08-03,5,23.03329389622305,19.0,-4.03329389622305
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,116,2026-07-30,116,117,2026-07-31,1,23.516646948111525,30.0,6.483353051888475
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,116,2026-07-30,116,118,2026-08-01,2,23.516646948111525,37.0,13.483353051888475
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,116,2026-07-30,116,119,2026-08-02,3,23.516646948111525,31.0,7.483353051888475
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,116,2026-07-30,116,120,2026-08-03,4,23.516646948111525,19.0,-4.516646948111525
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,116,2026-07-30,116,121,2026-08-04,5,23.516646948111525,22.0,-1.516646948111525
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,117,2026-07-31,117,118,2026-08-01,1,26.758323474055764,37.0,10.241676525944236
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,117,2026-07-31,117,119,2026-08-02,2,26.758323474055764,31.0,4.241676525944236
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,117,2026-07-31,117,120,2026-08-03,3,26.758323474055764,19.0,-7.758323474055764
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,117,2026-07-31,117,121,2026-08-04,4,26.758323474055764,22.0,-4.758323474055764
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,117,2026-07-31,117,122,2026-08-05,5,26.758323474055764,23.0,-3.7583234740557643
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,118,2026-08-01,118,119,2026-08-02,1,31.879161737027882,31.0,-0.8791617370278821
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,118,2026-08-01,118,120,2026-08-03,2,31.879161737027882,19.0,-12.879161737027882
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,118,2026-08-01,118,121,2026-08-04,3,31.879161737027882,22.0,-9.879161737027882
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,118,2026-08-01,118,122,2026-08-05,4,31.879161737027882,23.0,-8.879161737027882
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,118,2026-08-01,118,123,2026-08-06,5,31.879161737027882,26.0,-5.879161737027882
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,119,2026-08-02,119,120,2026-08-03,1,31.439580868513943,19.0,-12.439580868513943
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,119,2026-08-02,119,121,2026-08-04,2,31.439580868513943,22.0,-9.439580868513943
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,119,2026-08-02,119,122,2026-08-05,3,31.439580868513943,23.0,-8.439580868513943
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,119,2026-08-02,119,123,2026-08-06,4,31.439580868513943,26.0,-5.439580868513943
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,119,2026-08-02,119,124,2026-08-07,5,31.439580868513943,29.0,-2.439580868513943
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,120,2026-08-03,120,121,2026-08-04,1,25.21979043425697,22.0,-3.2197904342569714
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,120,2026-08-03,120,122,2026-08-05,2,25.21979043425697,23.0,-2.2197904342569714
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,120,2026-08-03,120,123,2026-08-06,3,25.21979043425697,26.0,0.7802095657430286
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,120,2026-08-03,120,124,2026-08-07,4,25.21979043425697,29.0,3.7802095657430286
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,120,2026-08-03,120,125,2026-08-08,5,25.21979043425697,34.0,8.780209565743029
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,121,2026-08-04,121,122,2026-08-05,1,23.609895217128486,23.0,-0.6098952171284857
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,121,2026-08-04,121,123,2026-08-06,2,23.609895217128486,26.0,2.3901047828715143
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,121,2026-08-04,121,124,2026-08-07,3,23.609895217128486,29.0,5.390104782871514
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,121,2026-08-04,121,125,2026-08-08,4,23.609895217128486,34.0,10.390104782871514
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,121,2026-08-04,121,126,2026-08-09,5,23.609895217128486,32.0,8.390104782871514
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,122,2026-08-05,122,123,2026-08-06,1,23.30494760856424,26.0,2.695052391435759
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,122,2026-08-05,122,124,2026-08-07,2,23.30494760856424,29.0,5.695052391435759
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,122,2026-08-05,122,125,2026-08-08,3,23.30494760856424,34.0,10.695052391435759
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,122,2026-08-05,122,126,2026-08-09,4,23.30494760856424,32.0,8.695052391435759
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,122,2026-08-05,122,127,2026-08-10,5,23.30494760856424,20.0,-3.304947608564241
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,123,2026-08-06,123,124,2026-08-07,1,24.65247380428212,29.0,4.3475261957178795
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,123,2026-08-06,123,125,2026-08-08,2,24.65247380428212,34.0,9.34752619571788
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,123,2026-08-06,123,126,2026-08-09,3,24.65247380428212,32.0,7.3475261957178795
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,123,2026-08-06,123,127,2026-08-10,4,24.65247380428212,20.0,-4.6524738042821205
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,123,2026-08-06,123,128,2026-08-11,5,24.65247380428212,22.0,-2.6524738042821205
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,124,2026-08-07,124,125,2026-08-08,1,26.826236902141062,34.0,7.173763097858938
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,124,2026-08-07,124,126,2026-08-09,2,26.826236902141062,32.0,5.173763097858938
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,124,2026-08-07,124,127,2026-08-10,3,26.826236902141062,20.0,-6.826236902141062
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,124,2026-08-07,124,128,2026-08-11,4,26.826236902141062,22.0,-4.826236902141062
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,124,2026-08-07,124,129,2026-08-12,5,26.826236902141062,20.0,-6.826236902141062
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,125,2026-08-08,125,126,2026-08-09,1,30.41311845107053,32.0,1.586881548929469
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,125,2026-08-08,125,127,2026-08-10,2,30.41311845107053,20.0,-10.413118451070531
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,125,2026-08-08,125,128,2026-08-11,3,30.41311845107053,22.0,-8.413118451070531
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,125,2026-08-08,125,129,2026-08-12,4,30.41311845107053,20.0,-10.413118451070531
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,125,2026-08-08,125,130,2026-08-13,5,30.41311845107053,23.0,-7.413118451070531
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,126,2026-08-09,126,127,2026-08-10,1,31.206559225535266,20.0,-11.206559225535266
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,126,2026-08-09,126,128,2026-08-11,2,31.206559225535266,22.0,-9.206559225535266
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,126,2026-08-09,126,129,2026-08-12,3,31.206559225535266,20.0,-11.206559225535266
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,126,2026-08-09,126,130,2026-08-13,4,31.206559225535266,23.0,-8.206559225535266
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,126,2026-08-09,126,131,2026-08-14,5,31.206559225535266,31.0,-0.2065592255352655
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,127,2026-08-10,127,128,2026-08-11,1,25.603279612767633,22.0,-3.6032796127676328
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,127,2026-08-10,127,129,2026-08-12,2,25.603279612767633,20.0,-5.603279612767633
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,127,2026-08-10,127,130,2026-08-13,3,25.603279612767633,23.0,-2.6032796127676328
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,127,2026-08-10,127,131,2026-08-14,4,25.603279612767633,31.0,5.396720387232367
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,127,2026-08-10,127,132,2026-08-15,5,25.603279612767633,33.0,7.396720387232367
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,128,2026-08-11,128,129,2026-08-12,1,23.801639806383818,20.0,-3.801639806383818
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,128,2026-08-11,128,130,2026-08-13,2,23.801639806383818,23.0,-0.8016398063838182
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,128,2026-08-11,128,131,2026-08-14,3,23.801639806383818,31.0,7.198360193616182
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,128,2026-08-11,128,132,2026-08-15,4,23.801639806383818,33.0,9.198360193616182
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,128,2026-08-11,128,133,2026-08-16,5,23.801639806383818,34.0,10.198360193616182
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,129,2026-08-12,129,130,2026-08-13,1,21.90081990319191,23.0,1.099180096808091
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,129,2026-08-12,129,131,2026-08-14,2,21.90081990319191,31.0,9.099180096808091
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,129,2026-08-12,129,132,2026-08-15,3,21.90081990319191,33.0,11.099180096808091
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,129,2026-08-12,129,133,2026-08-16,4,21.90081990319191,34.0,12.099180096808091
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,129,2026-08-12,129,134,2026-08-17,5,21.90081990319191,19.0,-2.900819903191909
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,130,2026-08-13,130,131,2026-08-14,1,22.450409951595955,31.0,8.549590048404045
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,130,2026-08-13,130,132,2026-08-15,2,22.450409951595955,33.0,10.549590048404045
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,130,2026-08-13,130,133,2026-08-16,3,22.450409951595955,34.0,11.549590048404045
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,130,2026-08-13,130,134,2026-08-17,4,22.450409951595955,19.0,-3.4504099515959545
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,130,2026-08-13,130,135,2026-08-18,5,22.450409951595955,22.0,-0.45040995159595454
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,131,2026-08-14,131,132,2026-08-15,1,26.72520497579798,33.0,6.274795024202021
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,131,2026-08-14,131,133,2026-08-16,2,26.72520497579798,34.0,7.274795024202021
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,131,2026-08-14,131,134,2026-08-17,3,26.72520497579798,19.0,-7.725204975797979
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,131,2026-08-14,131,135,2026-08-18,4,26.72520497579798,22.0,-4.725204975797979
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,131,2026-08-14,131,136,2026-08-19,5,26.72520497579798,20.0,-6.725204975797979
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,132,2026-08-15,132,133,2026-08-16,1,29.86260248789899,34.0,4.1373975121010105
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,132,2026-08-15,132,134,2026-08-17,2,29.86260248789899,19.0,-10.86260248789899
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,132,2026-08-15,132,135,2026-08-18,3,29.86260248789899,22.0,-7.8626024878989895
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,132,2026-08-15,132,136,2026-08-19,4,29.86260248789899,20.0,-9.86260248789899
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,132,2026-08-15,132,137,2026-08-20,5,29.86260248789899,24.0,-5.8626024878989895
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,133,2026-08-16,133,134,2026-08-17,1,31.931301243949495,19.0,-12.931301243949495
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,133,2026-08-16,133,135,2026-08-18,2,31.931301243949495,22.0,-9.931301243949495
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,133,2026-08-16,133,136,2026-08-19,3,31.931301243949495,20.0,-11.931301243949495
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,133,2026-08-16,133,137,2026-08-20,4,31.931301243949495,24.0,-7.931301243949495
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,133,2026-08-16,133,138,2026-08-21,5,31.931301243949495,31.0,-0.9313012439494948
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,134,2026-08-17,134,135,2026-08-18,1,25.465650621974746,22.0,-3.4656506219747456
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,134,2026-08-17,134,136,2026-08-19,2,25.465650621974746,20.0,-5.465650621974746
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,134,2026-08-17,134,137,2026-08-20,3,25.465650621974746,24.0,-1.4656506219747456
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,134,2026-08-17,134,138,2026-08-21,4,25.465650621974746,31.0,5.534349378025254
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,134,2026-08-17,134,139,2026-08-22,5,25.465650621974746,38.0,12.534349378025254
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,135,2026-08-18,135,136,2026-08-19,1,23.732825310987373,20.0,-3.732825310987373
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,135,2026-08-18,135,137,2026-08-20,2,23.732825310987373,24.0,0.2671746890126272
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,135,2026-08-18,135,138,2026-08-21,3,23.732825310987373,31.0,7.267174689012627
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,135,2026-08-18,135,139,2026-08-22,4,23.732825310987373,38.0,14.267174689012627
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",kg/day,5,135,2026-08-18,135,140,2026-08-23,5,23.732825310987373,32.0,8.267174689012627
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,1,112,2026-07-26,112,113,2026-07-27,1,30.348938107400542,18.0,-12.348938107400542
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,1,113,2026-07-27,113,114,2026-07-28,1,20.46978762148011,20.0,-0.46978762148010844
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,1,114,2026-07-28,114,115,2026-07-29,1,20.09395752429602,24.0,3.9060424757039804
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,1,115,2026-07-29,115,116,2026-07-30,1,23.218791504859205,24.0,0.7812084951407954
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,1,116,2026-07-30,116,117,2026-07-31,1,23.843758300971842,30.0,6.156241699028158
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,1,117,2026-07-31,117,118,2026-08-01,1,28.76875166019437,37.0,8.231248339805632
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,1,118,2026-08-01,118,119,2026-08-02,1,35.35375033203887,31.0,-4.353750332038871
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,1,119,2026-08-02,119,120,2026-08-03,1,31.870750066407773,19.0,-12.870750066407773
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,1,120,2026-08-03,120,121,2026-08-04,1,21.574150013281553,22.0,0.42584998671844687
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,1,121,2026-08-04,121,122,2026-08-05,1,21.91483000265631,23.0,1.0851699973436908
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,1,122,2026-08-05,122,123,2026-08-06,1,22.782966000531264,26.0,3.217033999468736
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,1,123,2026-08-06,123,124,2026-08-07,1,25.356593200106254,29.0,3.6434067998937465
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,1,124,2026-08-07,124,125,2026-08-08,1,28.271318640021253,34.0,5.728681359978747
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,1,125,2026-08-08,125,126,2026-08-09,1,32.854263728004256,32.0,-0.8542637280042555
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,1,126,2026-08-09,126,127,2026-08-10,1,32.170852745600854,20.0,-12.170852745600854
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,1,127,2026-08-10,127,128,2026-08-11,1,22.434170549120168,22.0,-0.43417054912016795
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,1,128,2026-08-11,128,129,2026-08-12,1,22.086834109824032,20.0,-2.086834109824032
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,1,129,2026-08-12,129,130,2026-08-13,1,20.417366821964805,23.0,2.582633178035195
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,1,130,2026-08-13,130,131,2026-08-14,1,22.483473364392964,31.0,8.516526635607036
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,1,131,2026-08-14,131,132,2026-08-15,1,29.296694672878594,33.0,3.703305327121406
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,1,132,2026-08-15,132,133,2026-08-16,1,32.25933893457572,34.0,1.740661065424277
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,1,133,2026-08-16,133,134,2026-08-17,1,33.65186778691515,19.0,-14.651867786915147
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,1,134,2026-08-17,134,135,2026-08-18,1,21.930373557383028,22.0,0.06962644261697193
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,1,135,2026-08-18,135,136,2026-08-19,1,21.986074711476604,20.0,-1.9860747114766042
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,1,136,2026-08-19,136,137,2026-08-20,1,20.39721494229532,24.0,3.602785057704679
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,1,137,2026-08-20,137,138,2026-08-21,1,23.279442988459067,31.0,7.720557011540933
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,1,138,2026-08-21,138,139,2026-08-22,1,29.455888597691814,38.0,8.544111402308186
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,1,139,2026-08-22,139,140,2026-08-23,1,36.29117771953836,32.0,-4.291177719538361
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,112,2026-07-26,112,113,2026-07-27,1,30.348938107400542,18.0,-12.348938107400542
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,112,2026-07-26,112,114,2026-07-28,2,30.348938107400542,20.0,-10.348938107400542
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,112,2026-07-26,112,115,2026-07-29,3,30.348938107400542,24.0,-6.348938107400542
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,112,2026-07-26,112,116,2026-07-30,4,30.348938107400542,24.0,-6.348938107400542
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,112,2026-07-26,112,117,2026-07-31,5,30.348938107400542,30.0,-0.3489381074005422
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,113,2026-07-27,113,114,2026-07-28,1,20.46978762148011,20.0,-0.46978762148010844
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,113,2026-07-27,113,115,2026-07-29,2,20.46978762148011,24.0,3.5302123785198916
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,113,2026-07-27,113,116,2026-07-30,3,20.46978762148011,24.0,3.5302123785198916
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,113,2026-07-27,113,117,2026-07-31,4,20.46978762148011,30.0,9.530212378519892
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,113,2026-07-27,113,118,2026-08-01,5,20.46978762148011,37.0,16.53021237851989
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,114,2026-07-28,114,115,2026-07-29,1,20.09395752429602,24.0,3.9060424757039804
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,114,2026-07-28,114,116,2026-07-30,2,20.09395752429602,24.0,3.9060424757039804
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,114,2026-07-28,114,117,2026-07-31,3,20.09395752429602,30.0,9.90604247570398
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,114,2026-07-28,114,118,2026-08-01,4,20.09395752429602,37.0,16.90604247570398
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,114,2026-07-28,114,119,2026-08-02,5,20.09395752429602,31.0,10.90604247570398
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,115,2026-07-29,115,116,2026-07-30,1,23.218791504859205,24.0,0.7812084951407954
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,115,2026-07-29,115,117,2026-07-31,2,23.218791504859205,30.0,6.781208495140795
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,115,2026-07-29,115,118,2026-08-01,3,23.218791504859205,37.0,13.781208495140795
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,115,2026-07-29,115,119,2026-08-02,4,23.218791504859205,31.0,7.781208495140795
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,115,2026-07-29,115,120,2026-08-03,5,23.218791504859205,19.0,-4.218791504859205
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,116,2026-07-30,116,117,2026-07-31,1,23.843758300971842,30.0,6.156241699028158
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,116,2026-07-30,116,118,2026-08-01,2,23.843758300971842,37.0,13.156241699028158
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,116,2026-07-30,116,119,2026-08-02,3,23.843758300971842,31.0,7.156241699028158
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,116,2026-07-30,116,120,2026-08-03,4,23.843758300971842,19.0,-4.843758300971842
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,116,2026-07-30,116,121,2026-08-04,5,23.843758300971842,22.0,-1.8437583009718423
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,117,2026-07-31,117,118,2026-08-01,1,28.76875166019437,37.0,8.231248339805632
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,117,2026-07-31,117,119,2026-08-02,2,28.76875166019437,31.0,2.2312483398056315
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,117,2026-07-31,117,120,2026-08-03,3,28.76875166019437,19.0,-9.768751660194368
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,117,2026-07-31,117,121,2026-08-04,4,28.76875166019437,22.0,-6.7687516601943685
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,117,2026-07-31,117,122,2026-08-05,5,28.76875166019437,23.0,-5.7687516601943685
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,118,2026-08-01,118,119,2026-08-02,1,35.35375033203887,31.0,-4.353750332038871
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,118,2026-08-01,118,120,2026-08-03,2,35.35375033203887,19.0,-16.35375033203887
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,118,2026-08-01,118,121,2026-08-04,3,35.35375033203887,22.0,-13.35375033203887
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,118,2026-08-01,118,122,2026-08-05,4,35.35375033203887,23.0,-12.35375033203887
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,118,2026-08-01,118,123,2026-08-06,5,35.35375033203887,26.0,-9.35375033203887
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,119,2026-08-02,119,120,2026-08-03,1,31.870750066407773,19.0,-12.870750066407773
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,119,2026-08-02,119,121,2026-08-04,2,31.870750066407773,22.0,-9.870750066407773
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,119,2026-08-02,119,122,2026-08-05,3,31.870750066407773,23.0,-8.870750066407773
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,119,2026-08-02,119,123,2026-08-06,4,31.870750066407773,26.0,-5.870750066407773
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,119,2026-08-02,119,124,2026-08-07,5,31.870750066407773,29.0,-2.8707500664077727
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,120,2026-08-03,120,121,2026-08-04,1,21.574150013281553,22.0,0.42584998671844687
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,120,2026-08-03,120,122,2026-08-05,2,21.574150013281553,23.0,1.4258499867184469
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,120,2026-08-03,120,123,2026-08-06,3,21.574150013281553,26.0,4.425849986718447
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,120,2026-08-03,120,124,2026-08-07,4,21.574150013281553,29.0,7.425849986718447
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,120,2026-08-03,120,125,2026-08-08,5,21.574150013281553,34.0,12.425849986718447
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,121,2026-08-04,121,122,2026-08-05,1,21.91483000265631,23.0,1.0851699973436908
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,121,2026-08-04,121,123,2026-08-06,2,21.91483000265631,26.0,4.085169997343691
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,121,2026-08-04,121,124,2026-08-07,3,21.91483000265631,29.0,7.085169997343691
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,121,2026-08-04,121,125,2026-08-08,4,21.91483000265631,34.0,12.08516999734369
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,121,2026-08-04,121,126,2026-08-09,5,21.91483000265631,32.0,10.08516999734369
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,122,2026-08-05,122,123,2026-08-06,1,22.782966000531264,26.0,3.217033999468736
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,122,2026-08-05,122,124,2026-08-07,2,22.782966000531264,29.0,6.217033999468736
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,122,2026-08-05,122,125,2026-08-08,3,22.782966000531264,34.0,11.217033999468736
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,122,2026-08-05,122,126,2026-08-09,4,22.782966000531264,32.0,9.217033999468736
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,122,2026-08-05,122,127,2026-08-10,5,22.782966000531264,20.0,-2.782966000531264
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,123,2026-08-06,123,124,2026-08-07,1,25.356593200106254,29.0,3.6434067998937465
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,123,2026-08-06,123,125,2026-08-08,2,25.356593200106254,34.0,8.643406799893746
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,123,2026-08-06,123,126,2026-08-09,3,25.356593200106254,32.0,6.6434067998937465
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,123,2026-08-06,123,127,2026-08-10,4,25.356593200106254,20.0,-5.3565932001062535
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,123,2026-08-06,123,128,2026-08-11,5,25.356593200106254,22.0,-3.3565932001062535
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,124,2026-08-07,124,125,2026-08-08,1,28.271318640021253,34.0,5.728681359978747
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,124,2026-08-07,124,126,2026-08-09,2,28.271318640021253,32.0,3.728681359978747
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,124,2026-08-07,124,127,2026-08-10,3,28.271318640021253,20.0,-8.271318640021253
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,124,2026-08-07,124,128,2026-08-11,4,28.271318640021253,22.0,-6.271318640021253
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,124,2026-08-07,124,129,2026-08-12,5,28.271318640021253,20.0,-8.271318640021253
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,125,2026-08-08,125,126,2026-08-09,1,32.854263728004256,32.0,-0.8542637280042555
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,125,2026-08-08,125,127,2026-08-10,2,32.854263728004256,20.0,-12.854263728004256
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,125,2026-08-08,125,128,2026-08-11,3,32.854263728004256,22.0,-10.854263728004256
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,125,2026-08-08,125,129,2026-08-12,4,32.854263728004256,20.0,-12.854263728004256
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,125,2026-08-08,125,130,2026-08-13,5,32.854263728004256,23.0,-9.854263728004256
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,126,2026-08-09,126,127,2026-08-10,1,32.170852745600854,20.0,-12.170852745600854
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,126,2026-08-09,126,128,2026-08-11,2,32.170852745600854,22.0,-10.170852745600854
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,126,2026-08-09,126,129,2026-08-12,3,32.170852745600854,20.0,-12.170852745600854
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,126,2026-08-09,126,130,2026-08-13,4,32.170852745600854,23.0,-9.170852745600854
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,126,2026-08-09,126,131,2026-08-14,5,32.170852745600854,31.0,-1.170852745600854
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,127,2026-08-10,127,128,2026-08-11,1,22.434170549120168,22.0,-0.43417054912016795
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,127,2026-08-10,127,129,2026-08-12,2,22.434170549120168,20.0,-2.434170549120168
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,127,2026-08-10,127,130,2026-08-13,3,22.434170549120168,23.0,0.565829450879832
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,127,2026-08-10,127,131,2026-08-14,4,22.434170549120168,31.0,8.565829450879832
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,127,2026-08-10,127,132,2026-08-15,5,22.434170549120168,33.0,10.565829450879832
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,128,2026-08-11,128,129,2026-08-12,1,22.086834109824032,20.0,-2.086834109824032
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,128,2026-08-11,128,130,2026-08-13,2,22.086834109824032,23.0,0.9131658901759678
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,128,2026-08-11,128,131,2026-08-14,3,22.086834109824032,31.0,8.913165890175968
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,128,2026-08-11,128,132,2026-08-15,4,22.086834109824032,33.0,10.913165890175968
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,128,2026-08-11,128,133,2026-08-16,5,22.086834109824032,34.0,11.913165890175968
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,129,2026-08-12,129,130,2026-08-13,1,20.417366821964805,23.0,2.582633178035195
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,129,2026-08-12,129,131,2026-08-14,2,20.417366821964805,31.0,10.582633178035195
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,129,2026-08-12,129,132,2026-08-15,3,20.417366821964805,33.0,12.582633178035195
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,129,2026-08-12,129,133,2026-08-16,4,20.417366821964805,34.0,13.582633178035195
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,129,2026-08-12,129,134,2026-08-17,5,20.417366821964805,19.0,-1.417366821964805
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,130,2026-08-13,130,131,2026-08-14,1,22.483473364392964,31.0,8.516526635607036
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,130,2026-08-13,130,132,2026-08-15,2,22.483473364392964,33.0,10.516526635607036
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,130,2026-08-13,130,133,2026-08-16,3,22.483473364392964,34.0,11.516526635607036
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,130,2026-08-13,130,134,2026-08-17,4,22.483473364392964,19.0,-3.483473364392964
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,130,2026-08-13,130,135,2026-08-18,5,22.483473364392964,22.0,-0.48347336439296384
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,131,2026-08-14,131,132,2026-08-15,1,29.296694672878594,33.0,3.703305327121406
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,131,2026-08-14,131,133,2026-08-16,2,29.296694672878594,34.0,4.703305327121406
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,131,2026-08-14,131,134,2026-08-17,3,29.296694672878594,19.0,-10.296694672878594
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,131,2026-08-14,131,135,2026-08-18,4,29.296694672878594,22.0,-7.296694672878594
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,131,2026-08-14,131,136,2026-08-19,5,29.296694672878594,20.0,-9.296694672878594
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,132,2026-08-15,132,133,2026-08-16,1,32.25933893457572,34.0,1.740661065424277
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,132,2026-08-15,132,134,2026-08-17,2,32.25933893457572,19.0,-13.259338934575723
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,132,2026-08-15,132,135,2026-08-18,3,32.25933893457572,22.0,-10.259338934575723
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,132,2026-08-15,132,136,2026-08-19,4,32.25933893457572,20.0,-12.259338934575723
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,132,2026-08-15,132,137,2026-08-20,5,32.25933893457572,24.0,-8.259338934575723
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,133,2026-08-16,133,134,2026-08-17,1,33.65186778691515,19.0,-14.651867786915147
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,133,2026-08-16,133,135,2026-08-18,2,33.65186778691515,22.0,-11.651867786915147
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,133,2026-08-16,133,136,2026-08-19,3,33.65186778691515,20.0,-13.651867786915147
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,133,2026-08-16,133,137,2026-08-20,4,33.65186778691515,24.0,-9.651867786915147
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,133,2026-08-16,133,138,2026-08-21,5,33.65186778691515,31.0,-2.6518677869151475
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,134,2026-08-17,134,135,2026-08-18,1,21.930373557383028,22.0,0.06962644261697193
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,134,2026-08-17,134,136,2026-08-19,2,21.930373557383028,20.0,-1.930373557383028
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,134,2026-08-17,134,137,2026-08-20,3,21.930373557383028,24.0,2.069626442616972
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,134,2026-08-17,134,138,2026-08-21,4,21.930373557383028,31.0,9.069626442616972
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,134,2026-08-17,134,139,2026-08-22,5,21.930373557383028,38.0,16.069626442616972
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,135,2026-08-18,135,136,2026-08-19,1,21.986074711476604,20.0,-1.9860747114766042
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,135,2026-08-18,135,137,2026-08-20,2,21.986074711476604,24.0,2.013925288523396
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,135,2026-08-18,135,138,2026-08-21,3,21.986074711476604,31.0,9.013925288523396
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,135,2026-08-18,135,139,2026-08-22,4,21.986074711476604,38.0,16.013925288523396
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",kg/day,5,135,2026-08-18,135,140,2026-08-23,5,21.986074711476604,32.0,10.013925288523396
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,1,112,2026-07-26,112,113,2026-07-27,1,89.0,89.0,0.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,1,113,2026-07-27,113,114,2026-07-28,1,89.0,91.0,2.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,1,114,2026-07-28,114,115,2026-07-29,1,94.0,92.0,-2.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,1,115,2026-07-29,115,116,2026-07-30,1,94.0,97.0,3.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,1,116,2026-07-30,116,117,2026-07-31,1,116.0,115.0,-1.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,1,117,2026-07-31,117,118,2026-08-01,1,146.0,239.0,93.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,1,118,2026-08-01,118,119,2026-08-02,1,133.0,227.0,94.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,1,119,2026-08-02,119,120,2026-08-03,1,89.0,179.0,90.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,1,120,2026-08-03,120,121,2026-08-04,1,91.0,91.0,0.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,1,121,2026-08-04,121,122,2026-08-05,1,92.0,94.0,2.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,1,122,2026-08-05,122,123,2026-08-06,1,97.0,99.0,2.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,1,123,2026-08-06,123,124,2026-08-07,1,115.0,115.0,0.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,1,124,2026-08-07,124,125,2026-08-08,1,239.0,147.0,-92.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,1,125,2026-08-08,125,126,2026-08-09,1,227.0,136.0,-91.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,1,126,2026-08-09,126,127,2026-08-10,1,179.0,92.0,-87.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,1,127,2026-08-10,127,128,2026-08-11,1,91.0,95.0,4.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,1,128,2026-08-11,128,129,2026-08-12,1,94.0,93.0,-1.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,1,129,2026-08-12,129,130,2026-08-13,1,99.0,96.0,-3.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,1,130,2026-08-13,130,131,2026-08-14,1,115.0,120.0,5.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,1,131,2026-08-14,131,132,2026-08-15,1,147.0,151.0,4.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,1,132,2026-08-15,132,133,2026-08-16,1,136.0,138.0,2.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,1,133,2026-08-16,133,134,2026-08-17,1,92.0,91.0,-1.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,1,134,2026-08-17,134,135,2026-08-18,1,95.0,96.0,1.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,1,135,2026-08-18,135,136,2026-08-19,1,93.0,94.0,1.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,1,136,2026-08-19,136,137,2026-08-20,1,96.0,94.0,-2.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,1,137,2026-08-20,137,138,2026-08-21,1,120.0,121.0,1.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,1,138,2026-08-21,138,139,2026-08-22,1,151.0,146.0,-5.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,1,139,2026-08-22,139,140,2026-08-23,1,138.0,136.0,-2.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,112,2026-07-26,112,113,2026-07-27,1,89.0,89.0,0.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,112,2026-07-26,112,114,2026-07-28,2,89.0,91.0,2.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,112,2026-07-26,112,115,2026-07-29,3,94.0,92.0,-2.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,112,2026-07-26,112,116,2026-07-30,4,94.0,97.0,3.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,112,2026-07-26,112,117,2026-07-31,5,116.0,115.0,-1.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,113,2026-07-27,113,114,2026-07-28,1,89.0,91.0,2.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,113,2026-07-27,113,115,2026-07-29,2,94.0,92.0,-2.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,113,2026-07-27,113,116,2026-07-30,3,94.0,97.0,3.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,113,2026-07-27,113,117,2026-07-31,4,116.0,115.0,-1.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,113,2026-07-27,113,118,2026-08-01,5,146.0,239.0,93.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,114,2026-07-28,114,115,2026-07-29,1,94.0,92.0,-2.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,114,2026-07-28,114,116,2026-07-30,2,94.0,97.0,3.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,114,2026-07-28,114,117,2026-07-31,3,116.0,115.0,-1.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,114,2026-07-28,114,118,2026-08-01,4,146.0,239.0,93.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,114,2026-07-28,114,119,2026-08-02,5,133.0,227.0,94.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,115,2026-07-29,115,116,2026-07-30,1,94.0,97.0,3.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,115,2026-07-29,115,117,2026-07-31,2,116.0,115.0,-1.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,115,2026-07-29,115,118,2026-08-01,3,146.0,239.0,93.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,115,2026-07-29,115,119,2026-08-02,4,133.0,227.0,94.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,115,2026-07-29,115,120,2026-08-03,5,89.0,179.0,90.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,116,2026-07-30,116,117,2026-07-31,1,116.0,115.0,-1.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,116,2026-07-30,116,118,2026-08-01,2,146.0,239.0,93.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,116,2026-07-30,116,119,2026-08-02,3,133.0,227.0,94.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,116,2026-07-30,116,120,2026-08-03,4,89.0,179.0,90.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,116,2026-07-30,116,121,2026-08-04,5,91.0,91.0,0.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,117,2026-07-31,117,118,2026-08-01,1,146.0,239.0,93.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,117,2026-07-31,117,119,2026-08-02,2,133.0,227.0,94.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,117,2026-07-31,117,120,2026-08-03,3,89.0,179.0,90.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,117,2026-07-31,117,121,2026-08-04,4,91.0,91.0,0.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,117,2026-07-31,117,122,2026-08-05,5,92.0,94.0,2.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,118,2026-08-01,118,119,2026-08-02,1,133.0,227.0,94.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,118,2026-08-01,118,120,2026-08-03,2,89.0,179.0,90.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,118,2026-08-01,118,121,2026-08-04,3,91.0,91.0,0.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,118,2026-08-01,118,122,2026-08-05,4,92.0,94.0,2.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,118,2026-08-01,118,123,2026-08-06,5,97.0,99.0,2.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,119,2026-08-02,119,120,2026-08-03,1,89.0,179.0,90.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,119,2026-08-02,119,121,2026-08-04,2,91.0,91.0,0.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,119,2026-08-02,119,122,2026-08-05,3,92.0,94.0,2.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,119,2026-08-02,119,123,2026-08-06,4,97.0,99.0,2.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,119,2026-08-02,119,124,2026-08-07,5,115.0,115.0,0.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,120,2026-08-03,120,121,2026-08-04,1,91.0,91.0,0.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,120,2026-08-03,120,122,2026-08-05,2,92.0,94.0,2.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,120,2026-08-03,120,123,2026-08-06,3,97.0,99.0,2.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,120,2026-08-03,120,124,2026-08-07,4,115.0,115.0,0.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,120,2026-08-03,120,125,2026-08-08,5,239.0,147.0,-92.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,121,2026-08-04,121,122,2026-08-05,1,92.0,94.0,2.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,121,2026-08-04,121,123,2026-08-06,2,97.0,99.0,2.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,121,2026-08-04,121,124,2026-08-07,3,115.0,115.0,0.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,121,2026-08-04,121,125,2026-08-08,4,239.0,147.0,-92.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,121,2026-08-04,121,126,2026-08-09,5,227.0,136.0,-91.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,122,2026-08-05,122,123,2026-08-06,1,97.0,99.0,2.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,122,2026-08-05,122,124,2026-08-07,2,115.0,115.0,0.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,122,2026-08-05,122,125,2026-08-08,3,239.0,147.0,-92.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,122,2026-08-05,122,126,2026-08-09,4,227.0,136.0,-91.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,122,2026-08-05,122,127,2026-08-10,5,179.0,92.0,-87.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,123,2026-08-06,123,124,2026-08-07,1,115.0,115.0,0.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,123,2026-08-06,123,125,2026-08-08,2,239.0,147.0,-92.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,123,2026-08-06,123,126,2026-08-09,3,227.0,136.0,-91.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,123,2026-08-06,123,127,2026-08-10,4,179.0,92.0,-87.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,123,2026-08-06,123,128,2026-08-11,5,91.0,95.0,4.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,124,2026-08-07,124,125,2026-08-08,1,239.0,147.0,-92.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,124,2026-08-07,124,126,2026-08-09,2,227.0,136.0,-91.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,124,2026-08-07,124,127,2026-08-10,3,179.0,92.0,-87.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,124,2026-08-07,124,128,2026-08-11,4,91.0,95.0,4.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,124,2026-08-07,124,129,2026-08-12,5,94.0,93.0,-1.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,125,2026-08-08,125,126,2026-08-09,1,227.0,136.0,-91.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,125,2026-08-08,125,127,2026-08-10,2,179.0,92.0,-87.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,125,2026-08-08,125,128,2026-08-11,3,91.0,95.0,4.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,125,2026-08-08,125,129,2026-08-12,4,94.0,93.0,-1.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,125,2026-08-08,125,130,2026-08-13,5,99.0,96.0,-3.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,126,2026-08-09,126,127,2026-08-10,1,179.0,92.0,-87.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,126,2026-08-09,126,128,2026-08-11,2,91.0,95.0,4.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,126,2026-08-09,126,129,2026-08-12,3,94.0,93.0,-1.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,126,2026-08-09,126,130,2026-08-13,4,99.0,96.0,-3.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,126,2026-08-09,126,131,2026-08-14,5,115.0,120.0,5.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,127,2026-08-10,127,128,2026-08-11,1,91.0,95.0,4.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,127,2026-08-10,127,129,2026-08-12,2,94.0,93.0,-1.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,127,2026-08-10,127,130,2026-08-13,3,99.0,96.0,-3.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,127,2026-08-10,127,131,2026-08-14,4,115.0,120.0,5.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,127,2026-08-10,127,132,2026-08-15,5,147.0,151.0,4.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,128,2026-08-11,128,129,2026-08-12,1,94.0,93.0,-1.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,128,2026-08-11,128,130,2026-08-13,2,99.0,96.0,-3.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,128,2026-08-11,128,131,2026-08-14,3,115.0,120.0,5.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,128,2026-08-11,128,132,2026-08-15,4,147.0,151.0,4.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,128,2026-08-11,128,133,2026-08-16,5,136.0,138.0,2.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,129,2026-08-12,129,130,2026-08-13,1,99.0,96.0,-3.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,129,2026-08-12,129,131,2026-08-14,2,115.0,120.0,5.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,129,2026-08-12,129,132,2026-08-15,3,147.0,151.0,4.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,129,2026-08-12,129,133,2026-08-16,4,136.0,138.0,2.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,129,2026-08-12,129,134,2026-08-17,5,92.0,91.0,-1.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,130,2026-08-13,130,131,2026-08-14,1,115.0,120.0,5.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,130,2026-08-13,130,132,2026-08-15,2,147.0,151.0,4.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,130,2026-08-13,130,133,2026-08-16,3,136.0,138.0,2.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,130,2026-08-13,130,134,2026-08-17,4,92.0,91.0,-1.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,130,2026-08-13,130,135,2026-08-18,5,95.0,96.0,1.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,131,2026-08-14,131,132,2026-08-15,1,147.0,151.0,4.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,131,2026-08-14,131,133,2026-08-16,2,136.0,138.0,2.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,131,2026-08-14,131,134,2026-08-17,3,92.0,91.0,-1.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,131,2026-08-14,131,135,2026-08-18,4,95.0,96.0,1.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,131,2026-08-14,131,136,2026-08-19,5,93.0,94.0,1.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,132,2026-08-15,132,133,2026-08-16,1,136.0,138.0,2.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,132,2026-08-15,132,134,2026-08-17,2,92.0,91.0,-1.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,132,2026-08-15,132,135,2026-08-18,3,95.0,96.0,1.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,132,2026-08-15,132,136,2026-08-19,4,93.0,94.0,1.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,132,2026-08-15,132,137,2026-08-20,5,96.0,94.0,-2.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,133,2026-08-16,133,134,2026-08-17,1,92.0,91.0,-1.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,133,2026-08-16,133,135,2026-08-18,2,95.0,96.0,1.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,133,2026-08-16,133,136,2026-08-19,3,93.0,94.0,1.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,133,2026-08-16,133,137,2026-08-20,4,96.0,94.0,-2.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,133,2026-08-16,133,138,2026-08-21,5,120.0,121.0,1.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,134,2026-08-17,134,135,2026-08-18,1,95.0,96.0,1.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,134,2026-08-17,134,136,2026-08-19,2,93.0,94.0,1.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,134,2026-08-17,134,137,2026-08-20,3,96.0,94.0,-2.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,134,2026-08-17,134,138,2026-08-21,4,120.0,121.0,1.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,134,2026-08-17,134,139,2026-08-22,5,151.0,146.0,-5.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,135,2026-08-18,135,136,2026-08-19,1,93.0,94.0,1.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,135,2026-08-18,135,137,2026-08-20,2,96.0,94.0,-2.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,135,2026-08-18,135,138,2026-08-21,3,120.0,121.0,1.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,135,2026-08-18,135,139,2026-08-22,4,151.0,146.0,-5.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",pieces/day,5,135,2026-08-18,135,140,2026-08-23,5,138.0,136.0,-2.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,1,112,2026-07-26,112,113,2026-07-27,1,131.66666666666666,89.0,-42.66666666666666
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,1,113,2026-07-27,113,114,2026-07-28,1,122.66666666666667,91.0,-31.66666666666667
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,1,114,2026-07-28,114,115,2026-07-29,1,104.33333333333333,92.0,-12.333333333333329
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,1,115,2026-07-29,115,116,2026-07-30,1,90.66666666666667,97.0,6.333333333333329
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,1,116,2026-07-30,116,117,2026-07-31,1,93.33333333333333,115.0,21.66666666666667
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,1,117,2026-07-31,117,118,2026-08-01,1,101.33333333333333,239.0,137.66666666666669
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,1,118,2026-08-01,118,119,2026-08-02,1,150.33333333333334,227.0,76.66666666666666
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,1,119,2026-08-02,119,120,2026-08-03,1,193.66666666666666,179.0,-14.666666666666657
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,1,120,2026-08-03,120,121,2026-08-04,1,215.0,91.0,-124.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,1,121,2026-08-04,121,122,2026-08-05,1,165.66666666666666,94.0,-71.66666666666666
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,1,122,2026-08-05,122,123,2026-08-06,1,121.33333333333333,99.0,-22.33333333333333
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,1,123,2026-08-06,123,124,2026-08-07,1,94.66666666666667,115.0,20.33333333333333
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,1,124,2026-08-07,124,125,2026-08-08,1,102.66666666666667,147.0,44.33333333333333
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,1,125,2026-08-08,125,126,2026-08-09,1,120.33333333333333,136.0,15.666666666666671
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,1,126,2026-08-09,126,127,2026-08-10,1,132.66666666666666,92.0,-40.66666666666666
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,1,127,2026-08-10,127,128,2026-08-11,1,125.0,95.0,-30.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,1,128,2026-08-11,128,129,2026-08-12,1,107.66666666666667,93.0,-14.666666666666671
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,1,129,2026-08-12,129,130,2026-08-13,1,93.33333333333333,96.0,2.6666666666666714
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,1,130,2026-08-13,130,131,2026-08-14,1,94.66666666666667,120.0,25.33333333333333
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,1,131,2026-08-14,131,132,2026-08-15,1,103.0,151.0,48.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,1,132,2026-08-15,132,133,2026-08-16,1,122.33333333333333,138.0,15.666666666666671
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,1,133,2026-08-16,133,134,2026-08-17,1,136.33333333333334,91.0,-45.33333333333334
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,1,134,2026-08-17,134,135,2026-08-18,1,126.66666666666667,96.0,-30.66666666666667
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,1,135,2026-08-18,135,136,2026-08-19,1,108.33333333333333,94.0,-14.333333333333329
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,1,136,2026-08-19,136,137,2026-08-20,1,93.66666666666667,94.0,0.3333333333333286
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,1,137,2026-08-20,137,138,2026-08-21,1,94.66666666666667,121.0,26.33333333333333
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,1,138,2026-08-21,138,139,2026-08-22,1,103.0,146.0,43.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,1,139,2026-08-22,139,140,2026-08-23,1,120.33333333333333,136.0,15.666666666666671
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,112,2026-07-26,112,113,2026-07-27,1,131.66666666666666,89.0,-42.66666666666666
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,112,2026-07-26,112,114,2026-07-28,2,131.66666666666666,91.0,-40.66666666666666
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,112,2026-07-26,112,115,2026-07-29,3,131.66666666666666,92.0,-39.66666666666666
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,112,2026-07-26,112,116,2026-07-30,4,131.66666666666666,97.0,-34.66666666666666
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,112,2026-07-26,112,117,2026-07-31,5,131.66666666666666,115.0,-16.666666666666657
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,113,2026-07-27,113,114,2026-07-28,1,122.66666666666667,91.0,-31.66666666666667
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,113,2026-07-27,113,115,2026-07-29,2,122.66666666666667,92.0,-30.66666666666667
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,113,2026-07-27,113,116,2026-07-30,3,122.66666666666667,97.0,-25.66666666666667
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,113,2026-07-27,113,117,2026-07-31,4,122.66666666666667,115.0,-7.666666666666671
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,113,2026-07-27,113,118,2026-08-01,5,122.66666666666667,239.0,116.33333333333333
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,114,2026-07-28,114,115,2026-07-29,1,104.33333333333333,92.0,-12.333333333333329
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,114,2026-07-28,114,116,2026-07-30,2,104.33333333333333,97.0,-7.333333333333329
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,114,2026-07-28,114,117,2026-07-31,3,104.33333333333333,115.0,10.666666666666671
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,114,2026-07-28,114,118,2026-08-01,4,104.33333333333333,239.0,134.66666666666669
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,114,2026-07-28,114,119,2026-08-02,5,104.33333333333333,227.0,122.66666666666667
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,115,2026-07-29,115,116,2026-07-30,1,90.66666666666667,97.0,6.333333333333329
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,115,2026-07-29,115,117,2026-07-31,2,90.66666666666667,115.0,24.33333333333333
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,115,2026-07-29,115,118,2026-08-01,3,90.66666666666667,239.0,148.33333333333331
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,115,2026-07-29,115,119,2026-08-02,4,90.66666666666667,227.0,136.33333333333331
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,115,2026-07-29,115,120,2026-08-03,5,90.66666666666667,179.0,88.33333333333333
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,116,2026-07-30,116,117,2026-07-31,1,93.33333333333333,115.0,21.66666666666667
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,116,2026-07-30,116,118,2026-08-01,2,93.33333333333333,239.0,145.66666666666669
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,116,2026-07-30,116,119,2026-08-02,3,93.33333333333333,227.0,133.66666666666669
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,116,2026-07-30,116,120,2026-08-03,4,93.33333333333333,179.0,85.66666666666667
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,116,2026-07-30,116,121,2026-08-04,5,93.33333333333333,91.0,-2.3333333333333286
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,117,2026-07-31,117,118,2026-08-01,1,101.33333333333333,239.0,137.66666666666669
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,117,2026-07-31,117,119,2026-08-02,2,101.33333333333333,227.0,125.66666666666667
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,117,2026-07-31,117,120,2026-08-03,3,101.33333333333333,179.0,77.66666666666667
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,117,2026-07-31,117,121,2026-08-04,4,101.33333333333333,91.0,-10.333333333333329
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,117,2026-07-31,117,122,2026-08-05,5,101.33333333333333,94.0,-7.333333333333329
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,118,2026-08-01,118,119,2026-08-02,1,150.33333333333334,227.0,76.66666666666666
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,118,2026-08-01,118,120,2026-08-03,2,150.33333333333334,179.0,28.666666666666657
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,118,2026-08-01,118,121,2026-08-04,3,150.33333333333334,91.0,-59.33333333333334
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,118,2026-08-01,118,122,2026-08-05,4,150.33333333333334,94.0,-56.33333333333334
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,118,2026-08-01,118,123,2026-08-06,5,150.33333333333334,99.0,-51.33333333333334
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,119,2026-08-02,119,120,2026-08-03,1,193.66666666666666,179.0,-14.666666666666657
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,119,2026-08-02,119,121,2026-08-04,2,193.66666666666666,91.0,-102.66666666666666
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,119,2026-08-02,119,122,2026-08-05,3,193.66666666666666,94.0,-99.66666666666666
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,119,2026-08-02,119,123,2026-08-06,4,193.66666666666666,99.0,-94.66666666666666
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,119,2026-08-02,119,124,2026-08-07,5,193.66666666666666,115.0,-78.66666666666666
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,120,2026-08-03,120,121,2026-08-04,1,215.0,91.0,-124.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,120,2026-08-03,120,122,2026-08-05,2,215.0,94.0,-121.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,120,2026-08-03,120,123,2026-08-06,3,215.0,99.0,-116.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,120,2026-08-03,120,124,2026-08-07,4,215.0,115.0,-100.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,120,2026-08-03,120,125,2026-08-08,5,215.0,147.0,-68.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,121,2026-08-04,121,122,2026-08-05,1,165.66666666666666,94.0,-71.66666666666666
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,121,2026-08-04,121,123,2026-08-06,2,165.66666666666666,99.0,-66.66666666666666
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,121,2026-08-04,121,124,2026-08-07,3,165.66666666666666,115.0,-50.66666666666666
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,121,2026-08-04,121,125,2026-08-08,4,165.66666666666666,147.0,-18.666666666666657
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,121,2026-08-04,121,126,2026-08-09,5,165.66666666666666,136.0,-29.666666666666657
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,122,2026-08-05,122,123,2026-08-06,1,121.33333333333333,99.0,-22.33333333333333
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,122,2026-08-05,122,124,2026-08-07,2,121.33333333333333,115.0,-6.333333333333329
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,122,2026-08-05,122,125,2026-08-08,3,121.33333333333333,147.0,25.66666666666667
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,122,2026-08-05,122,126,2026-08-09,4,121.33333333333333,136.0,14.666666666666671
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,122,2026-08-05,122,127,2026-08-10,5,121.33333333333333,92.0,-29.33333333333333
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,123,2026-08-06,123,124,2026-08-07,1,94.66666666666667,115.0,20.33333333333333
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,123,2026-08-06,123,125,2026-08-08,2,94.66666666666667,147.0,52.33333333333333
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,123,2026-08-06,123,126,2026-08-09,3,94.66666666666667,136.0,41.33333333333333
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,123,2026-08-06,123,127,2026-08-10,4,94.66666666666667,92.0,-2.6666666666666714
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,123,2026-08-06,123,128,2026-08-11,5,94.66666666666667,95.0,0.3333333333333286
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,124,2026-08-07,124,125,2026-08-08,1,102.66666666666667,147.0,44.33333333333333
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,124,2026-08-07,124,126,2026-08-09,2,102.66666666666667,136.0,33.33333333333333
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,124,2026-08-07,124,127,2026-08-10,3,102.66666666666667,92.0,-10.666666666666671
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,124,2026-08-07,124,128,2026-08-11,4,102.66666666666667,95.0,-7.666666666666671
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,124,2026-08-07,124,129,2026-08-12,5,102.66666666666667,93.0,-9.666666666666671
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,125,2026-08-08,125,126,2026-08-09,1,120.33333333333333,136.0,15.666666666666671
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,125,2026-08-08,125,127,2026-08-10,2,120.33333333333333,92.0,-28.33333333333333
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,125,2026-08-08,125,128,2026-08-11,3,120.33333333333333,95.0,-25.33333333333333
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,125,2026-08-08,125,129,2026-08-12,4,120.33333333333333,93.0,-27.33333333333333
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,125,2026-08-08,125,130,2026-08-13,5,120.33333333333333,96.0,-24.33333333333333
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,126,2026-08-09,126,127,2026-08-10,1,132.66666666666666,92.0,-40.66666666666666
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,126,2026-08-09,126,128,2026-08-11,2,132.66666666666666,95.0,-37.66666666666666
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,126,2026-08-09,126,129,2026-08-12,3,132.66666666666666,93.0,-39.66666666666666
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,126,2026-08-09,126,130,2026-08-13,4,132.66666666666666,96.0,-36.66666666666666
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,126,2026-08-09,126,131,2026-08-14,5,132.66666666666666,120.0,-12.666666666666657
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,127,2026-08-10,127,128,2026-08-11,1,125.0,95.0,-30.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,127,2026-08-10,127,129,2026-08-12,2,125.0,93.0,-32.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,127,2026-08-10,127,130,2026-08-13,3,125.0,96.0,-29.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,127,2026-08-10,127,131,2026-08-14,4,125.0,120.0,-5.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,127,2026-08-10,127,132,2026-08-15,5,125.0,151.0,26.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,128,2026-08-11,128,129,2026-08-12,1,107.66666666666667,93.0,-14.666666666666671
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,128,2026-08-11,128,130,2026-08-13,2,107.66666666666667,96.0,-11.666666666666671
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,128,2026-08-11,128,131,2026-08-14,3,107.66666666666667,120.0,12.333333333333329
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,128,2026-08-11,128,132,2026-08-15,4,107.66666666666667,151.0,43.33333333333333
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,128,2026-08-11,128,133,2026-08-16,5,107.66666666666667,138.0,30.33333333333333
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,129,2026-08-12,129,130,2026-08-13,1,93.33333333333333,96.0,2.6666666666666714
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,129,2026-08-12,129,131,2026-08-14,2,93.33333333333333,120.0,26.66666666666667
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,129,2026-08-12,129,132,2026-08-15,3,93.33333333333333,151.0,57.66666666666667
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,129,2026-08-12,129,133,2026-08-16,4,93.33333333333333,138.0,44.66666666666667
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,129,2026-08-12,129,134,2026-08-17,5,93.33333333333333,91.0,-2.3333333333333286
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,130,2026-08-13,130,131,2026-08-14,1,94.66666666666667,120.0,25.33333333333333
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,130,2026-08-13,130,132,2026-08-15,2,94.66666666666667,151.0,56.33333333333333
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,130,2026-08-13,130,133,2026-08-16,3,94.66666666666667,138.0,43.33333333333333
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,130,2026-08-13,130,134,2026-08-17,4,94.66666666666667,91.0,-3.6666666666666714
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,130,2026-08-13,130,135,2026-08-18,5,94.66666666666667,96.0,1.3333333333333286
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,131,2026-08-14,131,132,2026-08-15,1,103.0,151.0,48.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,131,2026-08-14,131,133,2026-08-16,2,103.0,138.0,35.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,131,2026-08-14,131,134,2026-08-17,3,103.0,91.0,-12.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,131,2026-08-14,131,135,2026-08-18,4,103.0,96.0,-7.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,131,2026-08-14,131,136,2026-08-19,5,103.0,94.0,-9.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,132,2026-08-15,132,133,2026-08-16,1,122.33333333333333,138.0,15.666666666666671
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,132,2026-08-15,132,134,2026-08-17,2,122.33333333333333,91.0,-31.33333333333333
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,132,2026-08-15,132,135,2026-08-18,3,122.33333333333333,96.0,-26.33333333333333
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,132,2026-08-15,132,136,2026-08-19,4,122.33333333333333,94.0,-28.33333333333333
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,132,2026-08-15,132,137,2026-08-20,5,122.33333333333333,94.0,-28.33333333333333
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,133,2026-08-16,133,134,2026-08-17,1,136.33333333333334,91.0,-45.33333333333334
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,133,2026-08-16,133,135,2026-08-18,2,136.33333333333334,96.0,-40.33333333333334
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,133,2026-08-16,133,136,2026-08-19,3,136.33333333333334,94.0,-42.33333333333334
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,133,2026-08-16,133,137,2026-08-20,4,136.33333333333334,94.0,-42.33333333333334
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,133,2026-08-16,133,138,2026-08-21,5,136.33333333333334,121.0,-15.333333333333343
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,134,2026-08-17,134,135,2026-08-18,1,126.66666666666667,96.0,-30.66666666666667
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,134,2026-08-17,134,136,2026-08-19,2,126.66666666666667,94.0,-32.66666666666667
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,134,2026-08-17,134,137,2026-08-20,3,126.66666666666667,94.0,-32.66666666666667
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,134,2026-08-17,134,138,2026-08-21,4,126.66666666666667,121.0,-5.666666666666671
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,134,2026-08-17,134,139,2026-08-22,5,126.66666666666667,146.0,19.33333333333333
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,135,2026-08-18,135,136,2026-08-19,1,108.33333333333333,94.0,-14.333333333333329
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,135,2026-08-18,135,137,2026-08-20,2,108.33333333333333,94.0,-14.333333333333329
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,135,2026-08-18,135,138,2026-08-21,3,108.33333333333333,121.0,12.666666666666671
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,135,2026-08-18,135,139,2026-08-22,4,108.33333333333333,146.0,37.66666666666667
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",pieces/day,5,135,2026-08-18,135,140,2026-08-23,5,108.33333333333333,136.0,27.66666666666667
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,1,112,2026-07-26,112,113,2026-07-27,1,108.71428571428571,89.0,-19.714285714285708
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,1,113,2026-07-27,113,114,2026-07-28,1,108.71428571428571,91.0,-17.714285714285708
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,1,114,2026-07-28,114,115,2026-07-29,1,109.0,92.0,-17.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,1,115,2026-07-29,115,116,2026-07-30,1,108.71428571428571,97.0,-11.714285714285708
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,1,116,2026-07-30,116,117,2026-07-31,1,109.14285714285714,115.0,5.857142857142861
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,1,117,2026-07-31,117,118,2026-08-01,1,109.0,239.0,130.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,1,118,2026-08-01,118,119,2026-08-02,1,122.28571428571429,227.0,104.71428571428571
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,1,119,2026-08-02,119,120,2026-08-03,1,135.71428571428572,179.0,43.28571428571428
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,1,120,2026-08-03,120,121,2026-08-04,1,148.57142857142858,91.0,-57.571428571428584
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,1,121,2026-08-04,121,122,2026-08-05,1,148.57142857142858,94.0,-54.571428571428584
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,1,122,2026-08-05,122,123,2026-08-06,1,148.85714285714286,99.0,-49.85714285714286
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,1,123,2026-08-06,123,124,2026-08-07,1,149.14285714285714,115.0,-34.14285714285714
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,1,124,2026-08-07,124,125,2026-08-08,1,149.14285714285714,147.0,-2.142857142857139
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,1,125,2026-08-08,125,126,2026-08-09,1,136.0,136.0,0.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,1,126,2026-08-09,126,127,2026-08-10,1,123.0,92.0,-31.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,1,127,2026-08-10,127,128,2026-08-11,1,110.57142857142857,95.0,-15.57142857142857
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,1,128,2026-08-11,128,129,2026-08-12,1,111.14285714285714,93.0,-18.14285714285714
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,1,129,2026-08-12,129,130,2026-08-13,1,111.0,96.0,-15.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,1,130,2026-08-13,130,131,2026-08-14,1,110.57142857142857,120.0,9.42857142857143
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,1,131,2026-08-14,131,132,2026-08-15,1,111.28571428571429,151.0,39.71428571428571
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,1,132,2026-08-15,132,133,2026-08-16,1,111.85714285714286,138.0,26.14285714285714
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,1,133,2026-08-16,133,134,2026-08-17,1,112.14285714285714,91.0,-21.14285714285714
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,1,134,2026-08-17,134,135,2026-08-18,1,112.0,96.0,-16.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,1,135,2026-08-18,135,136,2026-08-19,1,112.14285714285714,94.0,-18.14285714285714
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,1,136,2026-08-19,136,137,2026-08-20,1,112.28571428571429,94.0,-18.285714285714292
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,1,137,2026-08-20,137,138,2026-08-21,1,112.0,121.0,9.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,1,138,2026-08-21,138,139,2026-08-22,1,112.14285714285714,146.0,33.85714285714286
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,1,139,2026-08-22,139,140,2026-08-23,1,111.42857142857143,136.0,24.57142857142857
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,112,2026-07-26,112,113,2026-07-27,1,108.71428571428571,89.0,-19.714285714285708
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,112,2026-07-26,112,114,2026-07-28,2,108.71428571428571,91.0,-17.714285714285708
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,112,2026-07-26,112,115,2026-07-29,3,108.71428571428571,92.0,-16.714285714285708
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,112,2026-07-26,112,116,2026-07-30,4,108.71428571428571,97.0,-11.714285714285708
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,112,2026-07-26,112,117,2026-07-31,5,108.71428571428571,115.0,6.285714285714292
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,113,2026-07-27,113,114,2026-07-28,1,108.71428571428571,91.0,-17.714285714285708
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,113,2026-07-27,113,115,2026-07-29,2,108.71428571428571,92.0,-16.714285714285708
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,113,2026-07-27,113,116,2026-07-30,3,108.71428571428571,97.0,-11.714285714285708
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,113,2026-07-27,113,117,2026-07-31,4,108.71428571428571,115.0,6.285714285714292
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,113,2026-07-27,113,118,2026-08-01,5,108.71428571428571,239.0,130.28571428571428
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,114,2026-07-28,114,115,2026-07-29,1,109.0,92.0,-17.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,114,2026-07-28,114,116,2026-07-30,2,109.0,97.0,-12.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,114,2026-07-28,114,117,2026-07-31,3,109.0,115.0,6.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,114,2026-07-28,114,118,2026-08-01,4,109.0,239.0,130.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,114,2026-07-28,114,119,2026-08-02,5,109.0,227.0,118.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,115,2026-07-29,115,116,2026-07-30,1,108.71428571428571,97.0,-11.714285714285708
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,115,2026-07-29,115,117,2026-07-31,2,108.71428571428571,115.0,6.285714285714292
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,115,2026-07-29,115,118,2026-08-01,3,108.71428571428571,239.0,130.28571428571428
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,115,2026-07-29,115,119,2026-08-02,4,108.71428571428571,227.0,118.28571428571429
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,115,2026-07-29,115,120,2026-08-03,5,108.71428571428571,179.0,70.28571428571429
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,116,2026-07-30,116,117,2026-07-31,1,109.14285714285714,115.0,5.857142857142861
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,116,2026-07-30,116,118,2026-08-01,2,109.14285714285714,239.0,129.85714285714286
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,116,2026-07-30,116,119,2026-08-02,3,109.14285714285714,227.0,117.85714285714286
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,116,2026-07-30,116,120,2026-08-03,4,109.14285714285714,179.0,69.85714285714286
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,116,2026-07-30,116,121,2026-08-04,5,109.14285714285714,91.0,-18.14285714285714
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,117,2026-07-31,117,118,2026-08-01,1,109.0,239.0,130.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,117,2026-07-31,117,119,2026-08-02,2,109.0,227.0,118.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,117,2026-07-31,117,120,2026-08-03,3,109.0,179.0,70.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,117,2026-07-31,117,121,2026-08-04,4,109.0,91.0,-18.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,117,2026-07-31,117,122,2026-08-05,5,109.0,94.0,-15.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,118,2026-08-01,118,119,2026-08-02,1,122.28571428571429,227.0,104.71428571428571
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,118,2026-08-01,118,120,2026-08-03,2,122.28571428571429,179.0,56.71428571428571
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,118,2026-08-01,118,121,2026-08-04,3,122.28571428571429,91.0,-31.285714285714292
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,118,2026-08-01,118,122,2026-08-05,4,122.28571428571429,94.0,-28.285714285714292
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,118,2026-08-01,118,123,2026-08-06,5,122.28571428571429,99.0,-23.285714285714292
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,119,2026-08-02,119,120,2026-08-03,1,135.71428571428572,179.0,43.28571428571428
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,119,2026-08-02,119,121,2026-08-04,2,135.71428571428572,91.0,-44.71428571428572
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,119,2026-08-02,119,122,2026-08-05,3,135.71428571428572,94.0,-41.71428571428572
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,119,2026-08-02,119,123,2026-08-06,4,135.71428571428572,99.0,-36.71428571428572
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,119,2026-08-02,119,124,2026-08-07,5,135.71428571428572,115.0,-20.714285714285722
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,120,2026-08-03,120,121,2026-08-04,1,148.57142857142858,91.0,-57.571428571428584
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,120,2026-08-03,120,122,2026-08-05,2,148.57142857142858,94.0,-54.571428571428584
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,120,2026-08-03,120,123,2026-08-06,3,148.57142857142858,99.0,-49.571428571428584
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,120,2026-08-03,120,124,2026-08-07,4,148.57142857142858,115.0,-33.571428571428584
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,120,2026-08-03,120,125,2026-08-08,5,148.57142857142858,147.0,-1.5714285714285836
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,121,2026-08-04,121,122,2026-08-05,1,148.57142857142858,94.0,-54.571428571428584
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,121,2026-08-04,121,123,2026-08-06,2,148.57142857142858,99.0,-49.571428571428584
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,121,2026-08-04,121,124,2026-08-07,3,148.57142857142858,115.0,-33.571428571428584
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,121,2026-08-04,121,125,2026-08-08,4,148.57142857142858,147.0,-1.5714285714285836
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,121,2026-08-04,121,126,2026-08-09,5,148.57142857142858,136.0,-12.571428571428584
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,122,2026-08-05,122,123,2026-08-06,1,148.85714285714286,99.0,-49.85714285714286
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,122,2026-08-05,122,124,2026-08-07,2,148.85714285714286,115.0,-33.85714285714286
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,122,2026-08-05,122,125,2026-08-08,3,148.85714285714286,147.0,-1.8571428571428612
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,122,2026-08-05,122,126,2026-08-09,4,148.85714285714286,136.0,-12.857142857142861
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,122,2026-08-05,122,127,2026-08-10,5,148.85714285714286,92.0,-56.85714285714286
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,123,2026-08-06,123,124,2026-08-07,1,149.14285714285714,115.0,-34.14285714285714
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,123,2026-08-06,123,125,2026-08-08,2,149.14285714285714,147.0,-2.142857142857139
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,123,2026-08-06,123,126,2026-08-09,3,149.14285714285714,136.0,-13.142857142857139
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,123,2026-08-06,123,127,2026-08-10,4,149.14285714285714,92.0,-57.14285714285714
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,123,2026-08-06,123,128,2026-08-11,5,149.14285714285714,95.0,-54.14285714285714
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,124,2026-08-07,124,125,2026-08-08,1,149.14285714285714,147.0,-2.142857142857139
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,124,2026-08-07,124,126,2026-08-09,2,149.14285714285714,136.0,-13.142857142857139
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,124,2026-08-07,124,127,2026-08-10,3,149.14285714285714,92.0,-57.14285714285714
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,124,2026-08-07,124,128,2026-08-11,4,149.14285714285714,95.0,-54.14285714285714
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,124,2026-08-07,124,129,2026-08-12,5,149.14285714285714,93.0,-56.14285714285714
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,125,2026-08-08,125,126,2026-08-09,1,136.0,136.0,0.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,125,2026-08-08,125,127,2026-08-10,2,136.0,92.0,-44.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,125,2026-08-08,125,128,2026-08-11,3,136.0,95.0,-41.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,125,2026-08-08,125,129,2026-08-12,4,136.0,93.0,-43.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,125,2026-08-08,125,130,2026-08-13,5,136.0,96.0,-40.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,126,2026-08-09,126,127,2026-08-10,1,123.0,92.0,-31.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,126,2026-08-09,126,128,2026-08-11,2,123.0,95.0,-28.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,126,2026-08-09,126,129,2026-08-12,3,123.0,93.0,-30.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,126,2026-08-09,126,130,2026-08-13,4,123.0,96.0,-27.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,126,2026-08-09,126,131,2026-08-14,5,123.0,120.0,-3.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,127,2026-08-10,127,128,2026-08-11,1,110.57142857142857,95.0,-15.57142857142857
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,127,2026-08-10,127,129,2026-08-12,2,110.57142857142857,93.0,-17.57142857142857
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,127,2026-08-10,127,130,2026-08-13,3,110.57142857142857,96.0,-14.57142857142857
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,127,2026-08-10,127,131,2026-08-14,4,110.57142857142857,120.0,9.42857142857143
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,127,2026-08-10,127,132,2026-08-15,5,110.57142857142857,151.0,40.42857142857143
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,128,2026-08-11,128,129,2026-08-12,1,111.14285714285714,93.0,-18.14285714285714
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,128,2026-08-11,128,130,2026-08-13,2,111.14285714285714,96.0,-15.142857142857139
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,128,2026-08-11,128,131,2026-08-14,3,111.14285714285714,120.0,8.857142857142861
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,128,2026-08-11,128,132,2026-08-15,4,111.14285714285714,151.0,39.85714285714286
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,128,2026-08-11,128,133,2026-08-16,5,111.14285714285714,138.0,26.85714285714286
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,129,2026-08-12,129,130,2026-08-13,1,111.0,96.0,-15.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,129,2026-08-12,129,131,2026-08-14,2,111.0,120.0,9.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,129,2026-08-12,129,132,2026-08-15,3,111.0,151.0,40.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,129,2026-08-12,129,133,2026-08-16,4,111.0,138.0,27.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,129,2026-08-12,129,134,2026-08-17,5,111.0,91.0,-20.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,130,2026-08-13,130,131,2026-08-14,1,110.57142857142857,120.0,9.42857142857143
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,130,2026-08-13,130,132,2026-08-15,2,110.57142857142857,151.0,40.42857142857143
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,130,2026-08-13,130,133,2026-08-16,3,110.57142857142857,138.0,27.42857142857143
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,130,2026-08-13,130,134,2026-08-17,4,110.57142857142857,91.0,-19.57142857142857
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,130,2026-08-13,130,135,2026-08-18,5,110.57142857142857,96.0,-14.57142857142857
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,131,2026-08-14,131,132,2026-08-15,1,111.28571428571429,151.0,39.71428571428571
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,131,2026-08-14,131,133,2026-08-16,2,111.28571428571429,138.0,26.714285714285708
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,131,2026-08-14,131,134,2026-08-17,3,111.28571428571429,91.0,-20.285714285714292
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,131,2026-08-14,131,135,2026-08-18,4,111.28571428571429,96.0,-15.285714285714292
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,131,2026-08-14,131,136,2026-08-19,5,111.28571428571429,94.0,-17.285714285714292
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,132,2026-08-15,132,133,2026-08-16,1,111.85714285714286,138.0,26.14285714285714
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,132,2026-08-15,132,134,2026-08-17,2,111.85714285714286,91.0,-20.85714285714286
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,132,2026-08-15,132,135,2026-08-18,3,111.85714285714286,96.0,-15.857142857142861
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,132,2026-08-15,132,136,2026-08-19,4,111.85714285714286,94.0,-17.85714285714286
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,132,2026-08-15,132,137,2026-08-20,5,111.85714285714286,94.0,-17.85714285714286
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,133,2026-08-16,133,134,2026-08-17,1,112.14285714285714,91.0,-21.14285714285714
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,133,2026-08-16,133,135,2026-08-18,2,112.14285714285714,96.0,-16.14285714285714
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,133,2026-08-16,133,136,2026-08-19,3,112.14285714285714,94.0,-18.14285714285714
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,133,2026-08-16,133,137,2026-08-20,4,112.14285714285714,94.0,-18.14285714285714
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,133,2026-08-16,133,138,2026-08-21,5,112.14285714285714,121.0,8.857142857142861
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,134,2026-08-17,134,135,2026-08-18,1,112.0,96.0,-16.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,134,2026-08-17,134,136,2026-08-19,2,112.0,94.0,-18.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,134,2026-08-17,134,137,2026-08-20,3,112.0,94.0,-18.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,134,2026-08-17,134,138,2026-08-21,4,112.0,121.0,9.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,134,2026-08-17,134,139,2026-08-22,5,112.0,146.0,34.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,135,2026-08-18,135,136,2026-08-19,1,112.14285714285714,94.0,-18.14285714285714
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,135,2026-08-18,135,137,2026-08-20,2,112.14285714285714,94.0,-18.14285714285714
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,135,2026-08-18,135,138,2026-08-21,3,112.14285714285714,121.0,8.857142857142861
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,135,2026-08-18,135,139,2026-08-22,4,112.14285714285714,146.0,33.85714285714286
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",pieces/day,5,135,2026-08-18,135,140,2026-08-23,5,112.14285714285714,136.0,23.85714285714286
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,1,112,2026-07-26,112,113,2026-07-27,1,108.64285714285714,89.0,-19.64285714285714
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,1,113,2026-07-27,113,114,2026-07-28,1,109.0,91.0,-18.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,1,114,2026-07-28,114,115,2026-07-29,1,109.21428571428571,92.0,-17.214285714285708
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,1,115,2026-07-29,115,116,2026-07-30,1,108.92857142857143,97.0,-11.92857142857143
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,1,116,2026-07-30,116,117,2026-07-31,1,108.85714285714286,115.0,6.142857142857139
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,1,117,2026-07-31,117,118,2026-08-01,1,108.5,239.0,130.5
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,1,118,2026-08-01,118,119,2026-08-02,1,115.28571428571429,227.0,111.71428571428571
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,1,119,2026-08-02,119,120,2026-08-03,1,122.21428571428571,179.0,56.78571428571429
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,1,120,2026-08-03,120,121,2026-08-04,1,128.64285714285714,91.0,-37.64285714285714
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,1,121,2026-08-04,121,122,2026-08-05,1,128.78571428571428,94.0,-34.78571428571428
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,1,122,2026-08-05,122,123,2026-08-06,1,128.78571428571428,99.0,-29.785714285714278
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,1,123,2026-08-06,123,124,2026-08-07,1,129.14285714285714,115.0,-14.142857142857139
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,1,124,2026-08-07,124,125,2026-08-08,1,129.07142857142858,147.0,17.928571428571416
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,1,125,2026-08-08,125,126,2026-08-09,1,129.14285714285714,136.0,6.857142857142861
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,1,126,2026-08-09,126,127,2026-08-10,1,129.35714285714286,92.0,-37.35714285714286
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,1,127,2026-08-10,127,128,2026-08-11,1,129.57142857142858,95.0,-34.571428571428584
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,1,128,2026-08-11,128,129,2026-08-12,1,129.85714285714286,93.0,-36.85714285714286
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,1,129,2026-08-12,129,130,2026-08-13,1,129.92857142857142,96.0,-33.928571428571416
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,1,130,2026-08-13,130,131,2026-08-14,1,129.85714285714286,120.0,-9.857142857142861
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,1,131,2026-08-14,131,132,2026-08-15,1,130.21428571428572,151.0,20.785714285714278
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,1,132,2026-08-15,132,133,2026-08-16,1,123.92857142857143,138.0,14.07142857142857
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,1,133,2026-08-16,133,134,2026-08-17,1,117.57142857142857,91.0,-26.57142857142857
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,1,134,2026-08-17,134,135,2026-08-18,1,111.28571428571429,96.0,-15.285714285714292
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,1,135,2026-08-18,135,136,2026-08-19,1,111.64285714285714,94.0,-17.64285714285714
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,1,136,2026-08-19,136,137,2026-08-20,1,111.64285714285714,94.0,-17.64285714285714
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,1,137,2026-08-20,137,138,2026-08-21,1,111.28571428571429,121.0,9.714285714285708
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,1,138,2026-08-21,138,139,2026-08-22,1,111.71428571428571,146.0,34.28571428571429
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,1,139,2026-08-22,139,140,2026-08-23,1,111.64285714285714,136.0,24.35714285714286
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,112,2026-07-26,112,113,2026-07-27,1,108.64285714285714,89.0,-19.64285714285714
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,112,2026-07-26,112,114,2026-07-28,2,108.64285714285714,91.0,-17.64285714285714
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,112,2026-07-26,112,115,2026-07-29,3,108.64285714285714,92.0,-16.64285714285714
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,112,2026-07-26,112,116,2026-07-30,4,108.64285714285714,97.0,-11.642857142857139
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,112,2026-07-26,112,117,2026-07-31,5,108.64285714285714,115.0,6.357142857142861
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,113,2026-07-27,113,114,2026-07-28,1,109.0,91.0,-18.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,113,2026-07-27,113,115,2026-07-29,2,109.0,92.0,-17.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,113,2026-07-27,113,116,2026-07-30,3,109.0,97.0,-12.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,113,2026-07-27,113,117,2026-07-31,4,109.0,115.0,6.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,113,2026-07-27,113,118,2026-08-01,5,109.0,239.0,130.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,114,2026-07-28,114,115,2026-07-29,1,109.21428571428571,92.0,-17.214285714285708
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,114,2026-07-28,114,116,2026-07-30,2,109.21428571428571,97.0,-12.214285714285708
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,114,2026-07-28,114,117,2026-07-31,3,109.21428571428571,115.0,5.785714285714292
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,114,2026-07-28,114,118,2026-08-01,4,109.21428571428571,239.0,129.78571428571428
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,114,2026-07-28,114,119,2026-08-02,5,109.21428571428571,227.0,117.78571428571429
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,115,2026-07-29,115,116,2026-07-30,1,108.92857142857143,97.0,-11.92857142857143
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,115,2026-07-29,115,117,2026-07-31,2,108.92857142857143,115.0,6.071428571428569
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,115,2026-07-29,115,118,2026-08-01,3,108.92857142857143,239.0,130.07142857142856
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,115,2026-07-29,115,119,2026-08-02,4,108.92857142857143,227.0,118.07142857142857
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,115,2026-07-29,115,120,2026-08-03,5,108.92857142857143,179.0,70.07142857142857
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,116,2026-07-30,116,117,2026-07-31,1,108.85714285714286,115.0,6.142857142857139
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,116,2026-07-30,116,118,2026-08-01,2,108.85714285714286,239.0,130.14285714285714
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,116,2026-07-30,116,119,2026-08-02,3,108.85714285714286,227.0,118.14285714285714
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,116,2026-07-30,116,120,2026-08-03,4,108.85714285714286,179.0,70.14285714285714
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,116,2026-07-30,116,121,2026-08-04,5,108.85714285714286,91.0,-17.85714285714286
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,117,2026-07-31,117,118,2026-08-01,1,108.5,239.0,130.5
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,117,2026-07-31,117,119,2026-08-02,2,108.5,227.0,118.5
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,117,2026-07-31,117,120,2026-08-03,3,108.5,179.0,70.5
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,117,2026-07-31,117,121,2026-08-04,4,108.5,91.0,-17.5
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,117,2026-07-31,117,122,2026-08-05,5,108.5,94.0,-14.5
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,118,2026-08-01,118,119,2026-08-02,1,115.28571428571429,227.0,111.71428571428571
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,118,2026-08-01,118,120,2026-08-03,2,115.28571428571429,179.0,63.71428571428571
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,118,2026-08-01,118,121,2026-08-04,3,115.28571428571429,91.0,-24.285714285714292
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,118,2026-08-01,118,122,2026-08-05,4,115.28571428571429,94.0,-21.285714285714292
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,118,2026-08-01,118,123,2026-08-06,5,115.28571428571429,99.0,-16.285714285714292
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,119,2026-08-02,119,120,2026-08-03,1,122.21428571428571,179.0,56.78571428571429
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,119,2026-08-02,119,121,2026-08-04,2,122.21428571428571,91.0,-31.214285714285708
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,119,2026-08-02,119,122,2026-08-05,3,122.21428571428571,94.0,-28.214285714285708
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,119,2026-08-02,119,123,2026-08-06,4,122.21428571428571,99.0,-23.214285714285708
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,119,2026-08-02,119,124,2026-08-07,5,122.21428571428571,115.0,-7.214285714285708
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,120,2026-08-03,120,121,2026-08-04,1,128.64285714285714,91.0,-37.64285714285714
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,120,2026-08-03,120,122,2026-08-05,2,128.64285714285714,94.0,-34.64285714285714
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,120,2026-08-03,120,123,2026-08-06,3,128.64285714285714,99.0,-29.64285714285714
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,120,2026-08-03,120,124,2026-08-07,4,128.64285714285714,115.0,-13.642857142857139
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,120,2026-08-03,120,125,2026-08-08,5,128.64285714285714,147.0,18.35714285714286
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,121,2026-08-04,121,122,2026-08-05,1,128.78571428571428,94.0,-34.78571428571428
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,121,2026-08-04,121,123,2026-08-06,2,128.78571428571428,99.0,-29.785714285714278
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,121,2026-08-04,121,124,2026-08-07,3,128.78571428571428,115.0,-13.785714285714278
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,121,2026-08-04,121,125,2026-08-08,4,128.78571428571428,147.0,18.214285714285722
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,121,2026-08-04,121,126,2026-08-09,5,128.78571428571428,136.0,7.214285714285722
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,122,2026-08-05,122,123,2026-08-06,1,128.78571428571428,99.0,-29.785714285714278
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,122,2026-08-05,122,124,2026-08-07,2,128.78571428571428,115.0,-13.785714285714278
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,122,2026-08-05,122,125,2026-08-08,3,128.78571428571428,147.0,18.214285714285722
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,122,2026-08-05,122,126,2026-08-09,4,128.78571428571428,136.0,7.214285714285722
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,122,2026-08-05,122,127,2026-08-10,5,128.78571428571428,92.0,-36.78571428571428
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,123,2026-08-06,123,124,2026-08-07,1,129.14285714285714,115.0,-14.142857142857139
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,123,2026-08-06,123,125,2026-08-08,2,129.14285714285714,147.0,17.85714285714286
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,123,2026-08-06,123,126,2026-08-09,3,129.14285714285714,136.0,6.857142857142861
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,123,2026-08-06,123,127,2026-08-10,4,129.14285714285714,92.0,-37.14285714285714
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,123,2026-08-06,123,128,2026-08-11,5,129.14285714285714,95.0,-34.14285714285714
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,124,2026-08-07,124,125,2026-08-08,1,129.07142857142858,147.0,17.928571428571416
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,124,2026-08-07,124,126,2026-08-09,2,129.07142857142858,136.0,6.928571428571416
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,124,2026-08-07,124,127,2026-08-10,3,129.07142857142858,92.0,-37.071428571428584
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,124,2026-08-07,124,128,2026-08-11,4,129.07142857142858,95.0,-34.071428571428584
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,124,2026-08-07,124,129,2026-08-12,5,129.07142857142858,93.0,-36.071428571428584
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,125,2026-08-08,125,126,2026-08-09,1,129.14285714285714,136.0,6.857142857142861
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,125,2026-08-08,125,127,2026-08-10,2,129.14285714285714,92.0,-37.14285714285714
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,125,2026-08-08,125,128,2026-08-11,3,129.14285714285714,95.0,-34.14285714285714
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,125,2026-08-08,125,129,2026-08-12,4,129.14285714285714,93.0,-36.14285714285714
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,125,2026-08-08,125,130,2026-08-13,5,129.14285714285714,96.0,-33.14285714285714
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,126,2026-08-09,126,127,2026-08-10,1,129.35714285714286,92.0,-37.35714285714286
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,126,2026-08-09,126,128,2026-08-11,2,129.35714285714286,95.0,-34.35714285714286
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,126,2026-08-09,126,129,2026-08-12,3,129.35714285714286,93.0,-36.35714285714286
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,126,2026-08-09,126,130,2026-08-13,4,129.35714285714286,96.0,-33.35714285714286
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,126,2026-08-09,126,131,2026-08-14,5,129.35714285714286,120.0,-9.357142857142861
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,127,2026-08-10,127,128,2026-08-11,1,129.57142857142858,95.0,-34.571428571428584
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,127,2026-08-10,127,129,2026-08-12,2,129.57142857142858,93.0,-36.571428571428584
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,127,2026-08-10,127,130,2026-08-13,3,129.57142857142858,96.0,-33.571428571428584
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,127,2026-08-10,127,131,2026-08-14,4,129.57142857142858,120.0,-9.571428571428584
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,127,2026-08-10,127,132,2026-08-15,5,129.57142857142858,151.0,21.428571428571416
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,128,2026-08-11,128,129,2026-08-12,1,129.85714285714286,93.0,-36.85714285714286
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,128,2026-08-11,128,130,2026-08-13,2,129.85714285714286,96.0,-33.85714285714286
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,128,2026-08-11,128,131,2026-08-14,3,129.85714285714286,120.0,-9.857142857142861
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,128,2026-08-11,128,132,2026-08-15,4,129.85714285714286,151.0,21.14285714285714
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,128,2026-08-11,128,133,2026-08-16,5,129.85714285714286,138.0,8.142857142857139
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,129,2026-08-12,129,130,2026-08-13,1,129.92857142857142,96.0,-33.928571428571416
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,129,2026-08-12,129,131,2026-08-14,2,129.92857142857142,120.0,-9.928571428571416
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,129,2026-08-12,129,132,2026-08-15,3,129.92857142857142,151.0,21.071428571428584
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,129,2026-08-12,129,133,2026-08-16,4,129.92857142857142,138.0,8.071428571428584
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,129,2026-08-12,129,134,2026-08-17,5,129.92857142857142,91.0,-38.928571428571416
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,130,2026-08-13,130,131,2026-08-14,1,129.85714285714286,120.0,-9.857142857142861
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,130,2026-08-13,130,132,2026-08-15,2,129.85714285714286,151.0,21.14285714285714
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,130,2026-08-13,130,133,2026-08-16,3,129.85714285714286,138.0,8.142857142857139
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,130,2026-08-13,130,134,2026-08-17,4,129.85714285714286,91.0,-38.85714285714286
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,130,2026-08-13,130,135,2026-08-18,5,129.85714285714286,96.0,-33.85714285714286
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,131,2026-08-14,131,132,2026-08-15,1,130.21428571428572,151.0,20.785714285714278
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,131,2026-08-14,131,133,2026-08-16,2,130.21428571428572,138.0,7.785714285714278
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,131,2026-08-14,131,134,2026-08-17,3,130.21428571428572,91.0,-39.21428571428572
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,131,2026-08-14,131,135,2026-08-18,4,130.21428571428572,96.0,-34.21428571428572
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,131,2026-08-14,131,136,2026-08-19,5,130.21428571428572,94.0,-36.21428571428572
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,132,2026-08-15,132,133,2026-08-16,1,123.92857142857143,138.0,14.07142857142857
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,132,2026-08-15,132,134,2026-08-17,2,123.92857142857143,91.0,-32.92857142857143
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,132,2026-08-15,132,135,2026-08-18,3,123.92857142857143,96.0,-27.92857142857143
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,132,2026-08-15,132,136,2026-08-19,4,123.92857142857143,94.0,-29.92857142857143
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,132,2026-08-15,132,137,2026-08-20,5,123.92857142857143,94.0,-29.92857142857143
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,133,2026-08-16,133,134,2026-08-17,1,117.57142857142857,91.0,-26.57142857142857
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,133,2026-08-16,133,135,2026-08-18,2,117.57142857142857,96.0,-21.57142857142857
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,133,2026-08-16,133,136,2026-08-19,3,117.57142857142857,94.0,-23.57142857142857
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,133,2026-08-16,133,137,2026-08-20,4,117.57142857142857,94.0,-23.57142857142857
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,133,2026-08-16,133,138,2026-08-21,5,117.57142857142857,121.0,3.4285714285714306
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,134,2026-08-17,134,135,2026-08-18,1,111.28571428571429,96.0,-15.285714285714292
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,134,2026-08-17,134,136,2026-08-19,2,111.28571428571429,94.0,-17.285714285714292
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,134,2026-08-17,134,137,2026-08-20,3,111.28571428571429,94.0,-17.285714285714292
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,134,2026-08-17,134,138,2026-08-21,4,111.28571428571429,121.0,9.714285714285708
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,134,2026-08-17,134,139,2026-08-22,5,111.28571428571429,146.0,34.71428571428571
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,135,2026-08-18,135,136,2026-08-19,1,111.64285714285714,94.0,-17.64285714285714
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,135,2026-08-18,135,137,2026-08-20,2,111.64285714285714,94.0,-17.64285714285714
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,135,2026-08-18,135,138,2026-08-21,3,111.64285714285714,121.0,9.357142857142861
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,135,2026-08-18,135,139,2026-08-22,4,111.64285714285714,146.0,34.35714285714286
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",pieces/day,5,135,2026-08-18,135,140,2026-08-23,5,111.64285714285714,136.0,24.35714285714286
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,1,112,2026-07-26,112,113,2026-07-27,1,117.13025108591563,89.0,-28.13025108591563
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,1,113,2026-07-27,113,114,2026-07-28,1,111.50420086873251,91.0,-20.50420086873251
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,1,114,2026-07-28,114,115,2026-07-29,1,107.40336069498602,92.0,-15.40336069498602
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,1,115,2026-07-29,115,116,2026-07-30,1,104.32268855598883,97.0,-7.322688555988833
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,1,116,2026-07-30,116,117,2026-07-31,1,102.85815084479108,115.0,12.141849155208916
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,1,117,2026-07-31,117,118,2026-08-01,1,105.28652067583288,239.0,133.7134793241671
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,1,118,2026-08-01,118,119,2026-08-02,1,132.0292165406663,227.0,94.97078345933369
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,1,119,2026-08-02,119,120,2026-08-03,1,151.02337323253306,179.0,27.97662676746694
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,1,120,2026-08-03,120,121,2026-08-04,1,156.61869858602645,91.0,-65.61869858602645
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,1,121,2026-08-04,121,122,2026-08-05,1,143.49495886882116,94.0,-49.49495886882116
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,1,122,2026-08-05,122,123,2026-08-06,1,133.59596709505695,99.0,-34.59596709505695
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,1,123,2026-08-06,123,124,2026-08-07,1,126.67677367604556,115.0,-11.676773676045556
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,1,124,2026-08-07,124,125,2026-08-08,1,124.34141894083645,147.0,22.658581059163552
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,1,125,2026-08-08,125,126,2026-08-09,1,128.87313515266916,136.0,7.126864847330836
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,1,126,2026-08-09,126,127,2026-08-10,1,130.29850812213533,92.0,-38.29850812213533
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,1,127,2026-08-10,127,128,2026-08-11,1,122.63880649770827,95.0,-27.638806497708273
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,1,128,2026-08-11,128,129,2026-08-12,1,117.11104519816662,93.0,-24.11104519816662
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,1,129,2026-08-12,129,130,2026-08-13,1,112.28883615853331,96.0,-16.288836158533314
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,1,130,2026-08-13,130,131,2026-08-14,1,109.03106892682666,120.0,10.968931073173337
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,1,131,2026-08-14,131,132,2026-08-15,1,111.22485514146133,151.0,39.77514485853867
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,1,132,2026-08-15,132,133,2026-08-16,1,119.17988411316908,138.0,18.82011588683092
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,1,133,2026-08-16,133,134,2026-08-17,1,122.94390729053526,91.0,-31.943907290535265
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,1,134,2026-08-17,134,135,2026-08-18,1,116.55512583242822,96.0,-20.555125832428217
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,1,135,2026-08-18,135,136,2026-08-19,1,112.44410066594259,94.0,-18.444100665942585
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,1,136,2026-08-19,136,137,2026-08-20,1,108.75528053275407,94.0,-14.755280532754071
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,1,137,2026-08-20,137,138,2026-08-21,1,105.80422442620326,121.0,15.195775573796737
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,1,138,2026-08-21,138,139,2026-08-22,1,108.84337954096262,146.0,37.156620459037384
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,1,139,2026-08-22,139,140,2026-08-23,1,116.2747036327701,136.0,19.7252963672299
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,112,2026-07-26,112,113,2026-07-27,1,117.13025108591563,89.0,-28.13025108591563
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,112,2026-07-26,112,114,2026-07-28,2,117.13025108591563,91.0,-26.13025108591563
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,112,2026-07-26,112,115,2026-07-29,3,117.13025108591563,92.0,-25.13025108591563
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,112,2026-07-26,112,116,2026-07-30,4,117.13025108591563,97.0,-20.13025108591563
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,112,2026-07-26,112,117,2026-07-31,5,117.13025108591563,115.0,-2.1302510859156314
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,113,2026-07-27,113,114,2026-07-28,1,111.50420086873251,91.0,-20.50420086873251
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,113,2026-07-27,113,115,2026-07-29,2,111.50420086873251,92.0,-19.50420086873251
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,113,2026-07-27,113,116,2026-07-30,3,111.50420086873251,97.0,-14.50420086873251
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,113,2026-07-27,113,117,2026-07-31,4,111.50420086873251,115.0,3.495799131267489
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,113,2026-07-27,113,118,2026-08-01,5,111.50420086873251,239.0,127.49579913126749
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,114,2026-07-28,114,115,2026-07-29,1,107.40336069498602,92.0,-15.40336069498602
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,114,2026-07-28,114,116,2026-07-30,2,107.40336069498602,97.0,-10.40336069498602
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,114,2026-07-28,114,117,2026-07-31,3,107.40336069498602,115.0,7.59663930501398
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,114,2026-07-28,114,118,2026-08-01,4,107.40336069498602,239.0,131.59663930501398
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,114,2026-07-28,114,119,2026-08-02,5,107.40336069498602,227.0,119.59663930501398
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,115,2026-07-29,115,116,2026-07-30,1,104.32268855598883,97.0,-7.322688555988833
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,115,2026-07-29,115,117,2026-07-31,2,104.32268855598883,115.0,10.677311444011167
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,115,2026-07-29,115,118,2026-08-01,3,104.32268855598883,239.0,134.67731144401117
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,115,2026-07-29,115,119,2026-08-02,4,104.32268855598883,227.0,122.67731144401117
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,115,2026-07-29,115,120,2026-08-03,5,104.32268855598883,179.0,74.67731144401117
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,116,2026-07-30,116,117,2026-07-31,1,102.85815084479108,115.0,12.141849155208916
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,116,2026-07-30,116,118,2026-08-01,2,102.85815084479108,239.0,136.14184915520892
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,116,2026-07-30,116,119,2026-08-02,3,102.85815084479108,227.0,124.14184915520892
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,116,2026-07-30,116,120,2026-08-03,4,102.85815084479108,179.0,76.14184915520892
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,116,2026-07-30,116,121,2026-08-04,5,102.85815084479108,91.0,-11.858150844791084
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,117,2026-07-31,117,118,2026-08-01,1,105.28652067583288,239.0,133.7134793241671
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,117,2026-07-31,117,119,2026-08-02,2,105.28652067583288,227.0,121.71347932416712
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,117,2026-07-31,117,120,2026-08-03,3,105.28652067583288,179.0,73.71347932416712
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,117,2026-07-31,117,121,2026-08-04,4,105.28652067583288,91.0,-14.286520675832875
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,117,2026-07-31,117,122,2026-08-05,5,105.28652067583288,94.0,-11.286520675832875
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,118,2026-08-01,118,119,2026-08-02,1,132.0292165406663,227.0,94.97078345933369
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,118,2026-08-01,118,120,2026-08-03,2,132.0292165406663,179.0,46.97078345933369
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,118,2026-08-01,118,121,2026-08-04,3,132.0292165406663,91.0,-41.02921654066631
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,118,2026-08-01,118,122,2026-08-05,4,132.0292165406663,94.0,-38.02921654066631
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,118,2026-08-01,118,123,2026-08-06,5,132.0292165406663,99.0,-33.02921654066631
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,119,2026-08-02,119,120,2026-08-03,1,151.02337323253306,179.0,27.97662676746694
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,119,2026-08-02,119,121,2026-08-04,2,151.02337323253306,91.0,-60.02337323253306
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,119,2026-08-02,119,122,2026-08-05,3,151.02337323253306,94.0,-57.02337323253306
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,119,2026-08-02,119,123,2026-08-06,4,151.02337323253306,99.0,-52.02337323253306
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,119,2026-08-02,119,124,2026-08-07,5,151.02337323253306,115.0,-36.02337323253306
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,120,2026-08-03,120,121,2026-08-04,1,156.61869858602645,91.0,-65.61869858602645
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,120,2026-08-03,120,122,2026-08-05,2,156.61869858602645,94.0,-62.618698586026454
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,120,2026-08-03,120,123,2026-08-06,3,156.61869858602645,99.0,-57.618698586026454
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,120,2026-08-03,120,124,2026-08-07,4,156.61869858602645,115.0,-41.618698586026454
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,120,2026-08-03,120,125,2026-08-08,5,156.61869858602645,147.0,-9.618698586026454
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,121,2026-08-04,121,122,2026-08-05,1,143.49495886882116,94.0,-49.49495886882116
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,121,2026-08-04,121,123,2026-08-06,2,143.49495886882116,99.0,-44.49495886882116
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,121,2026-08-04,121,124,2026-08-07,3,143.49495886882116,115.0,-28.494958868821158
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,121,2026-08-04,121,125,2026-08-08,4,143.49495886882116,147.0,3.5050411311788423
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,121,2026-08-04,121,126,2026-08-09,5,143.49495886882116,136.0,-7.494958868821158
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,122,2026-08-05,122,123,2026-08-06,1,133.59596709505695,99.0,-34.59596709505695
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,122,2026-08-05,122,124,2026-08-07,2,133.59596709505695,115.0,-18.59596709505695
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,122,2026-08-05,122,125,2026-08-08,3,133.59596709505695,147.0,13.404032904943051
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,122,2026-08-05,122,126,2026-08-09,4,133.59596709505695,136.0,2.404032904943051
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,122,2026-08-05,122,127,2026-08-10,5,133.59596709505695,92.0,-41.59596709505695
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,123,2026-08-06,123,124,2026-08-07,1,126.67677367604556,115.0,-11.676773676045556
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,123,2026-08-06,123,125,2026-08-08,2,126.67677367604556,147.0,20.323226323954444
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,123,2026-08-06,123,126,2026-08-09,3,126.67677367604556,136.0,9.323226323954444
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,123,2026-08-06,123,127,2026-08-10,4,126.67677367604556,92.0,-34.676773676045556
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,123,2026-08-06,123,128,2026-08-11,5,126.67677367604556,95.0,-31.676773676045556
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,124,2026-08-07,124,125,2026-08-08,1,124.34141894083645,147.0,22.658581059163552
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,124,2026-08-07,124,126,2026-08-09,2,124.34141894083645,136.0,11.658581059163552
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,124,2026-08-07,124,127,2026-08-10,3,124.34141894083645,92.0,-32.34141894083645
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,124,2026-08-07,124,128,2026-08-11,4,124.34141894083645,95.0,-29.341418940836448
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,124,2026-08-07,124,129,2026-08-12,5,124.34141894083645,93.0,-31.341418940836448
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,125,2026-08-08,125,126,2026-08-09,1,128.87313515266916,136.0,7.126864847330836
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,125,2026-08-08,125,127,2026-08-10,2,128.87313515266916,92.0,-36.873135152669164
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,125,2026-08-08,125,128,2026-08-11,3,128.87313515266916,95.0,-33.873135152669164
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,125,2026-08-08,125,129,2026-08-12,4,128.87313515266916,93.0,-35.873135152669164
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,125,2026-08-08,125,130,2026-08-13,5,128.87313515266916,96.0,-32.873135152669164
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,126,2026-08-09,126,127,2026-08-10,1,130.29850812213533,92.0,-38.29850812213533
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,126,2026-08-09,126,128,2026-08-11,2,130.29850812213533,95.0,-35.29850812213533
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,126,2026-08-09,126,129,2026-08-12,3,130.29850812213533,93.0,-37.29850812213533
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,126,2026-08-09,126,130,2026-08-13,4,130.29850812213533,96.0,-34.29850812213533
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,126,2026-08-09,126,131,2026-08-14,5,130.29850812213533,120.0,-10.298508122135331
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,127,2026-08-10,127,128,2026-08-11,1,122.63880649770827,95.0,-27.638806497708273
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,127,2026-08-10,127,129,2026-08-12,2,122.63880649770827,93.0,-29.638806497708273
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,127,2026-08-10,127,130,2026-08-13,3,122.63880649770827,96.0,-26.638806497708273
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,127,2026-08-10,127,131,2026-08-14,4,122.63880649770827,120.0,-2.6388064977082735
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,127,2026-08-10,127,132,2026-08-15,5,122.63880649770827,151.0,28.361193502291727
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,128,2026-08-11,128,129,2026-08-12,1,117.11104519816662,93.0,-24.11104519816662
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,128,2026-08-11,128,130,2026-08-13,2,117.11104519816662,96.0,-21.11104519816662
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,128,2026-08-11,128,131,2026-08-14,3,117.11104519816662,120.0,2.8889548018333784
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,128,2026-08-11,128,132,2026-08-15,4,117.11104519816662,151.0,33.88895480183338
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,128,2026-08-11,128,133,2026-08-16,5,117.11104519816662,138.0,20.88895480183338
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,129,2026-08-12,129,130,2026-08-13,1,112.28883615853331,96.0,-16.288836158533314
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,129,2026-08-12,129,131,2026-08-14,2,112.28883615853331,120.0,7.711163841466686
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,129,2026-08-12,129,132,2026-08-15,3,112.28883615853331,151.0,38.711163841466686
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,129,2026-08-12,129,133,2026-08-16,4,112.28883615853331,138.0,25.711163841466686
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,129,2026-08-12,129,134,2026-08-17,5,112.28883615853331,91.0,-21.288836158533314
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,130,2026-08-13,130,131,2026-08-14,1,109.03106892682666,120.0,10.968931073173337
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,130,2026-08-13,130,132,2026-08-15,2,109.03106892682666,151.0,41.96893107317334
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,130,2026-08-13,130,133,2026-08-16,3,109.03106892682666,138.0,28.968931073173337
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,130,2026-08-13,130,134,2026-08-17,4,109.03106892682666,91.0,-18.031068926826663
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,130,2026-08-13,130,135,2026-08-18,5,109.03106892682666,96.0,-13.031068926826663
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,131,2026-08-14,131,132,2026-08-15,1,111.22485514146133,151.0,39.77514485853867
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,131,2026-08-14,131,133,2026-08-16,2,111.22485514146133,138.0,26.775144858538667
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,131,2026-08-14,131,134,2026-08-17,3,111.22485514146133,91.0,-20.224855141461333
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,131,2026-08-14,131,135,2026-08-18,4,111.22485514146133,96.0,-15.224855141461333
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,131,2026-08-14,131,136,2026-08-19,5,111.22485514146133,94.0,-17.224855141461333
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,132,2026-08-15,132,133,2026-08-16,1,119.17988411316908,138.0,18.82011588683092
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,132,2026-08-15,132,134,2026-08-17,2,119.17988411316908,91.0,-28.17988411316908
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,132,2026-08-15,132,135,2026-08-18,3,119.17988411316908,96.0,-23.17988411316908
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,132,2026-08-15,132,136,2026-08-19,4,119.17988411316908,94.0,-25.17988411316908
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,132,2026-08-15,132,137,2026-08-20,5,119.17988411316908,94.0,-25.17988411316908
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,133,2026-08-16,133,134,2026-08-17,1,122.94390729053526,91.0,-31.943907290535265
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,133,2026-08-16,133,135,2026-08-18,2,122.94390729053526,96.0,-26.943907290535265
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,133,2026-08-16,133,136,2026-08-19,3,122.94390729053526,94.0,-28.943907290535265
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,133,2026-08-16,133,137,2026-08-20,4,122.94390729053526,94.0,-28.943907290535265
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,133,2026-08-16,133,138,2026-08-21,5,122.94390729053526,121.0,-1.9439072905352646
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,134,2026-08-17,134,135,2026-08-18,1,116.55512583242822,96.0,-20.555125832428217
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,134,2026-08-17,134,136,2026-08-19,2,116.55512583242822,94.0,-22.555125832428217
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,134,2026-08-17,134,137,2026-08-20,3,116.55512583242822,94.0,-22.555125832428217
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,134,2026-08-17,134,138,2026-08-21,4,116.55512583242822,121.0,4.444874167571783
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,134,2026-08-17,134,139,2026-08-22,5,116.55512583242822,146.0,29.444874167571783
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,135,2026-08-18,135,136,2026-08-19,1,112.44410066594259,94.0,-18.444100665942585
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,135,2026-08-18,135,137,2026-08-20,2,112.44410066594259,94.0,-18.444100665942585
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,135,2026-08-18,135,138,2026-08-21,3,112.44410066594259,121.0,8.555899334057415
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,135,2026-08-18,135,139,2026-08-22,4,112.44410066594259,146.0,33.555899334057415
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",pieces/day,5,135,2026-08-18,135,140,2026-08-23,5,112.44410066594259,136.0,23.555899334057415
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,1,112,2026-07-26,112,113,2026-07-27,1,129.39969893565262,89.0,-40.39969893565262
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,1,113,2026-07-27,113,114,2026-07-28,1,109.19984946782631,91.0,-18.19984946782631
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,1,114,2026-07-28,114,115,2026-07-29,1,100.09992473391316,92.0,-8.099924733913156
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,1,115,2026-07-29,115,116,2026-07-30,1,96.04996236695658,97.0,0.9500376330434221
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,1,116,2026-07-30,116,117,2026-07-31,1,96.52498118347829,115.0,18.47501881652171
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,1,117,2026-07-31,117,118,2026-08-01,1,105.76249059173915,239.0,133.23750940826085
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,1,118,2026-08-01,118,119,2026-08-02,1,172.38124529586958,227.0,54.618754704130424
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,1,119,2026-08-02,119,120,2026-08-03,1,199.6906226479348,179.0,-20.690622647934788
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,1,120,2026-08-03,120,121,2026-08-04,1,189.3453113239674,91.0,-98.3453113239674
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,1,121,2026-08-04,121,122,2026-08-05,1,140.1726556619837,94.0,-46.1726556619837
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,1,122,2026-08-05,122,123,2026-08-06,1,117.08632783099185,99.0,-18.08632783099185
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,1,123,2026-08-06,123,124,2026-08-07,1,108.04316391549592,115.0,6.956836084504076
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,1,124,2026-08-07,124,125,2026-08-08,1,111.52158195774797,147.0,35.47841804225203
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,1,125,2026-08-08,125,126,2026-08-09,1,129.26079097887398,136.0,6.739209021126015
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,1,126,2026-08-09,126,127,2026-08-10,1,132.63039548943698,92.0,-40.63039548943698
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,1,127,2026-08-10,127,128,2026-08-11,1,112.31519774471849,95.0,-17.31519774471849
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,1,128,2026-08-11,128,129,2026-08-12,1,103.65759887235924,93.0,-10.657598872359245
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,1,129,2026-08-12,129,130,2026-08-13,1,98.32879943617962,96.0,-2.3287994361796223
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,1,130,2026-08-13,130,131,2026-08-14,1,97.16439971808981,120.0,22.83560028191019
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,1,131,2026-08-14,131,132,2026-08-15,1,108.5821998590449,151.0,42.417800140955094
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,1,132,2026-08-15,132,133,2026-08-16,1,129.79109992952246,138.0,8.20890007047754
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,1,133,2026-08-16,133,134,2026-08-17,1,133.89554996476124,91.0,-42.895549964761244
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,1,134,2026-08-17,134,135,2026-08-18,1,112.44777498238062,96.0,-16.447774982380622
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,1,135,2026-08-18,135,136,2026-08-19,1,104.22388749119031,94.0,-10.223887491190311
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,1,136,2026-08-19,136,137,2026-08-20,1,99.11194374559516,94.0,-5.1119437455951555
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,1,137,2026-08-20,137,138,2026-08-21,1,96.55597187279758,121.0,24.444028127202415
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,1,138,2026-08-21,138,139,2026-08-22,1,108.77798593639879,146.0,37.22201406360121
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,1,139,2026-08-22,139,140,2026-08-23,1,127.3889929681994,136.0,8.611007031800597
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,112,2026-07-26,112,113,2026-07-27,1,129.39969893565262,89.0,-40.39969893565262
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,112,2026-07-26,112,114,2026-07-28,2,129.39969893565262,91.0,-38.39969893565262
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,112,2026-07-26,112,115,2026-07-29,3,129.39969893565262,92.0,-37.39969893565262
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,112,2026-07-26,112,116,2026-07-30,4,129.39969893565262,97.0,-32.39969893565262
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,112,2026-07-26,112,117,2026-07-31,5,129.39969893565262,115.0,-14.399698935652623
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,113,2026-07-27,113,114,2026-07-28,1,109.19984946782631,91.0,-18.19984946782631
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,113,2026-07-27,113,115,2026-07-29,2,109.19984946782631,92.0,-17.19984946782631
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,113,2026-07-27,113,116,2026-07-30,3,109.19984946782631,97.0,-12.199849467826311
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,113,2026-07-27,113,117,2026-07-31,4,109.19984946782631,115.0,5.800150532173689
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,113,2026-07-27,113,118,2026-08-01,5,109.19984946782631,239.0,129.8001505321737
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,114,2026-07-28,114,115,2026-07-29,1,100.09992473391316,92.0,-8.099924733913156
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,114,2026-07-28,114,116,2026-07-30,2,100.09992473391316,97.0,-3.0999247339131557
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,114,2026-07-28,114,117,2026-07-31,3,100.09992473391316,115.0,14.900075266086844
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,114,2026-07-28,114,118,2026-08-01,4,100.09992473391316,239.0,138.90007526608684
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,114,2026-07-28,114,119,2026-08-02,5,100.09992473391316,227.0,126.90007526608684
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,115,2026-07-29,115,116,2026-07-30,1,96.04996236695658,97.0,0.9500376330434221
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,115,2026-07-29,115,117,2026-07-31,2,96.04996236695658,115.0,18.950037633043422
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,115,2026-07-29,115,118,2026-08-01,3,96.04996236695658,239.0,142.95003763304342
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,115,2026-07-29,115,119,2026-08-02,4,96.04996236695658,227.0,130.95003763304342
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,115,2026-07-29,115,120,2026-08-03,5,96.04996236695658,179.0,82.95003763304342
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,116,2026-07-30,116,117,2026-07-31,1,96.52498118347829,115.0,18.47501881652171
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,116,2026-07-30,116,118,2026-08-01,2,96.52498118347829,239.0,142.4750188165217
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,116,2026-07-30,116,119,2026-08-02,3,96.52498118347829,227.0,130.4750188165217
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,116,2026-07-30,116,120,2026-08-03,4,96.52498118347829,179.0,82.47501881652171
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,116,2026-07-30,116,121,2026-08-04,5,96.52498118347829,91.0,-5.524981183478289
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,117,2026-07-31,117,118,2026-08-01,1,105.76249059173915,239.0,133.23750940826085
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,117,2026-07-31,117,119,2026-08-02,2,105.76249059173915,227.0,121.23750940826085
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,117,2026-07-31,117,120,2026-08-03,3,105.76249059173915,179.0,73.23750940826085
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,117,2026-07-31,117,121,2026-08-04,4,105.76249059173915,91.0,-14.762490591739152
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,117,2026-07-31,117,122,2026-08-05,5,105.76249059173915,94.0,-11.762490591739152
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,118,2026-08-01,118,119,2026-08-02,1,172.38124529586958,227.0,54.618754704130424
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,118,2026-08-01,118,120,2026-08-03,2,172.38124529586958,179.0,6.618754704130424
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,118,2026-08-01,118,121,2026-08-04,3,172.38124529586958,91.0,-81.38124529586958
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,118,2026-08-01,118,122,2026-08-05,4,172.38124529586958,94.0,-78.38124529586958
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,118,2026-08-01,118,123,2026-08-06,5,172.38124529586958,99.0,-73.38124529586958
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,119,2026-08-02,119,120,2026-08-03,1,199.6906226479348,179.0,-20.690622647934788
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,119,2026-08-02,119,121,2026-08-04,2,199.6906226479348,91.0,-108.69062264793479
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,119,2026-08-02,119,122,2026-08-05,3,199.6906226479348,94.0,-105.69062264793479
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,119,2026-08-02,119,123,2026-08-06,4,199.6906226479348,99.0,-100.69062264793479
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,119,2026-08-02,119,124,2026-08-07,5,199.6906226479348,115.0,-84.69062264793479
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,120,2026-08-03,120,121,2026-08-04,1,189.3453113239674,91.0,-98.3453113239674
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,120,2026-08-03,120,122,2026-08-05,2,189.3453113239674,94.0,-95.3453113239674
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,120,2026-08-03,120,123,2026-08-06,3,189.3453113239674,99.0,-90.3453113239674
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,120,2026-08-03,120,124,2026-08-07,4,189.3453113239674,115.0,-74.3453113239674
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,120,2026-08-03,120,125,2026-08-08,5,189.3453113239674,147.0,-42.345311323967394
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,121,2026-08-04,121,122,2026-08-05,1,140.1726556619837,94.0,-46.1726556619837
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,121,2026-08-04,121,123,2026-08-06,2,140.1726556619837,99.0,-41.1726556619837
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,121,2026-08-04,121,124,2026-08-07,3,140.1726556619837,115.0,-25.172655661983697
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,121,2026-08-04,121,125,2026-08-08,4,140.1726556619837,147.0,6.827344338016303
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,121,2026-08-04,121,126,2026-08-09,5,140.1726556619837,136.0,-4.172655661983697
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,122,2026-08-05,122,123,2026-08-06,1,117.08632783099185,99.0,-18.08632783099185
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,122,2026-08-05,122,124,2026-08-07,2,117.08632783099185,115.0,-2.0863278309918485
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,122,2026-08-05,122,125,2026-08-08,3,117.08632783099185,147.0,29.91367216900815
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,122,2026-08-05,122,126,2026-08-09,4,117.08632783099185,136.0,18.91367216900815
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,122,2026-08-05,122,127,2026-08-10,5,117.08632783099185,92.0,-25.08632783099185
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,123,2026-08-06,123,124,2026-08-07,1,108.04316391549592,115.0,6.956836084504076
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,123,2026-08-06,123,125,2026-08-08,2,108.04316391549592,147.0,38.956836084504076
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,123,2026-08-06,123,126,2026-08-09,3,108.04316391549592,136.0,27.956836084504076
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,123,2026-08-06,123,127,2026-08-10,4,108.04316391549592,92.0,-16.043163915495924
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,123,2026-08-06,123,128,2026-08-11,5,108.04316391549592,95.0,-13.043163915495924
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,124,2026-08-07,124,125,2026-08-08,1,111.52158195774797,147.0,35.47841804225203
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,124,2026-08-07,124,126,2026-08-09,2,111.52158195774797,136.0,24.47841804225203
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,124,2026-08-07,124,127,2026-08-10,3,111.52158195774797,92.0,-19.52158195774797
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,124,2026-08-07,124,128,2026-08-11,4,111.52158195774797,95.0,-16.52158195774797
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,124,2026-08-07,124,129,2026-08-12,5,111.52158195774797,93.0,-18.52158195774797
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,125,2026-08-08,125,126,2026-08-09,1,129.26079097887398,136.0,6.739209021126015
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,125,2026-08-08,125,127,2026-08-10,2,129.26079097887398,92.0,-37.260790978873985
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,125,2026-08-08,125,128,2026-08-11,3,129.26079097887398,95.0,-34.260790978873985
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,125,2026-08-08,125,129,2026-08-12,4,129.26079097887398,93.0,-36.260790978873985
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,125,2026-08-08,125,130,2026-08-13,5,129.26079097887398,96.0,-33.260790978873985
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,126,2026-08-09,126,127,2026-08-10,1,132.63039548943698,92.0,-40.63039548943698
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,126,2026-08-09,126,128,2026-08-11,2,132.63039548943698,95.0,-37.63039548943698
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,126,2026-08-09,126,129,2026-08-12,3,132.63039548943698,93.0,-39.63039548943698
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,126,2026-08-09,126,130,2026-08-13,4,132.63039548943698,96.0,-36.63039548943698
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,126,2026-08-09,126,131,2026-08-14,5,132.63039548943698,120.0,-12.630395489436978
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,127,2026-08-10,127,128,2026-08-11,1,112.31519774471849,95.0,-17.31519774471849
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,127,2026-08-10,127,129,2026-08-12,2,112.31519774471849,93.0,-19.31519774471849
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,127,2026-08-10,127,130,2026-08-13,3,112.31519774471849,96.0,-16.31519774471849
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,127,2026-08-10,127,131,2026-08-14,4,112.31519774471849,120.0,7.684802255281511
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,127,2026-08-10,127,132,2026-08-15,5,112.31519774471849,151.0,38.68480225528151
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,128,2026-08-11,128,129,2026-08-12,1,103.65759887235924,93.0,-10.657598872359245
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,128,2026-08-11,128,130,2026-08-13,2,103.65759887235924,96.0,-7.6575988723592445
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,128,2026-08-11,128,131,2026-08-14,3,103.65759887235924,120.0,16.342401127640755
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,128,2026-08-11,128,132,2026-08-15,4,103.65759887235924,151.0,47.342401127640755
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,128,2026-08-11,128,133,2026-08-16,5,103.65759887235924,138.0,34.342401127640755
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,129,2026-08-12,129,130,2026-08-13,1,98.32879943617962,96.0,-2.3287994361796223
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,129,2026-08-12,129,131,2026-08-14,2,98.32879943617962,120.0,21.671200563820378
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,129,2026-08-12,129,132,2026-08-15,3,98.32879943617962,151.0,52.67120056382038
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,129,2026-08-12,129,133,2026-08-16,4,98.32879943617962,138.0,39.67120056382038
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,129,2026-08-12,129,134,2026-08-17,5,98.32879943617962,91.0,-7.328799436179622
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,130,2026-08-13,130,131,2026-08-14,1,97.16439971808981,120.0,22.83560028191019
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,130,2026-08-13,130,132,2026-08-15,2,97.16439971808981,151.0,53.83560028191019
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,130,2026-08-13,130,133,2026-08-16,3,97.16439971808981,138.0,40.83560028191019
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,130,2026-08-13,130,134,2026-08-17,4,97.16439971808981,91.0,-6.164399718089811
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,130,2026-08-13,130,135,2026-08-18,5,97.16439971808981,96.0,-1.1643997180898111
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,131,2026-08-14,131,132,2026-08-15,1,108.5821998590449,151.0,42.417800140955094
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,131,2026-08-14,131,133,2026-08-16,2,108.5821998590449,138.0,29.417800140955094
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,131,2026-08-14,131,134,2026-08-17,3,108.5821998590449,91.0,-17.582199859044906
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,131,2026-08-14,131,135,2026-08-18,4,108.5821998590449,96.0,-12.582199859044906
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,131,2026-08-14,131,136,2026-08-19,5,108.5821998590449,94.0,-14.582199859044906
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,132,2026-08-15,132,133,2026-08-16,1,129.79109992952246,138.0,8.20890007047754
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,132,2026-08-15,132,134,2026-08-17,2,129.79109992952246,91.0,-38.79109992952246
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,132,2026-08-15,132,135,2026-08-18,3,129.79109992952246,96.0,-33.79109992952246
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,132,2026-08-15,132,136,2026-08-19,4,129.79109992952246,94.0,-35.79109992952246
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,132,2026-08-15,132,137,2026-08-20,5,129.79109992952246,94.0,-35.79109992952246
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,133,2026-08-16,133,134,2026-08-17,1,133.89554996476124,91.0,-42.895549964761244
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,133,2026-08-16,133,135,2026-08-18,2,133.89554996476124,96.0,-37.895549964761244
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,133,2026-08-16,133,136,2026-08-19,3,133.89554996476124,94.0,-39.895549964761244
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,133,2026-08-16,133,137,2026-08-20,4,133.89554996476124,94.0,-39.895549964761244
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,133,2026-08-16,133,138,2026-08-21,5,133.89554996476124,121.0,-12.895549964761244
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,134,2026-08-17,134,135,2026-08-18,1,112.44777498238062,96.0,-16.447774982380622
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,134,2026-08-17,134,136,2026-08-19,2,112.44777498238062,94.0,-18.447774982380622
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,134,2026-08-17,134,137,2026-08-20,3,112.44777498238062,94.0,-18.447774982380622
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,134,2026-08-17,134,138,2026-08-21,4,112.44777498238062,121.0,8.552225017619378
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,134,2026-08-17,134,139,2026-08-22,5,112.44777498238062,146.0,33.55222501761938
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,135,2026-08-18,135,136,2026-08-19,1,104.22388749119031,94.0,-10.223887491190311
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,135,2026-08-18,135,137,2026-08-20,2,104.22388749119031,94.0,-10.223887491190311
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,135,2026-08-18,135,138,2026-08-21,3,104.22388749119031,121.0,16.77611250880969
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,135,2026-08-18,135,139,2026-08-22,4,104.22388749119031,146.0,41.77611250880969
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",pieces/day,5,135,2026-08-18,135,140,2026-08-23,5,104.22388749119031,136.0,31.77611250880969
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,1,112,2026-07-26,112,113,2026-07-27,1,134.22294603035346,89.0,-45.222946030353455
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,1,113,2026-07-27,113,114,2026-07-28,1,98.0445892060707,91.0,-7.044589206070697
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,1,114,2026-07-28,114,115,2026-07-29,1,92.40891784121413,92.0,-0.40891784121413366
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,1,115,2026-07-29,115,116,2026-07-30,1,92.08178356824283,97.0,4.918216431757173
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,1,116,2026-07-30,116,117,2026-07-31,1,96.01635671364858,115.0,18.983643286351423
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,1,117,2026-07-31,117,118,2026-08-01,1,111.2032713427297,239.0,127.7967286572703
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,1,118,2026-08-01,118,119,2026-08-02,1,213.44065426854596,227.0,13.559345731454044
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,1,119,2026-08-02,119,120,2026-08-03,1,224.28813085370922,179.0,-45.28813085370922
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,1,120,2026-08-03,120,121,2026-08-04,1,188.05762617074186,91.0,-97.05762617074186
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,1,121,2026-08-04,121,122,2026-08-05,1,110.41152523414836,94.0,-16.411525234148357
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,1,122,2026-08-05,122,123,2026-08-06,1,97.28230504682966,99.0,1.7176949531703372
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,1,123,2026-08-06,123,124,2026-08-07,1,98.65646100936593,115.0,16.343538990634073
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,1,124,2026-08-07,124,125,2026-08-08,1,111.73129220187317,147.0,35.268707798126826
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,1,125,2026-08-08,125,126,2026-08-09,1,139.94625844037463,136.0,-3.946258440374635
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,1,126,2026-08-09,126,127,2026-08-10,1,136.78925168807493,92.0,-44.78925168807493
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,1,127,2026-08-10,127,128,2026-08-11,1,100.95785033761499,95.0,-5.957850337614985
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,1,128,2026-08-11,128,129,2026-08-12,1,96.19157006752299,93.0,-3.1915700675229886
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,1,129,2026-08-12,129,130,2026-08-13,1,93.6383140135046,96.0,2.3616859864954023
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,1,130,2026-08-13,130,131,2026-08-14,1,95.52766280270093,120.0,24.47233719729907
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,1,131,2026-08-14,131,132,2026-08-15,1,115.10553256054018,151.0,35.89446743945982
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,1,132,2026-08-15,132,133,2026-08-16,1,143.82110651210803,138.0,-5.821106512108031
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,1,133,2026-08-16,133,134,2026-08-17,1,139.1642213024216,91.0,-48.164221302421595
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,1,134,2026-08-17,134,135,2026-08-18,1,100.6328442604843,96.0,-4.632844260484305
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,1,135,2026-08-18,135,136,2026-08-19,1,96.92656885209686,94.0,-2.926568852096864
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,1,136,2026-08-19,136,137,2026-08-20,1,94.58531377041938,94.0,-0.5853137704193756
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,1,137,2026-08-20,137,138,2026-08-21,1,94.11706275408388,121.0,26.882937245916125
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,1,138,2026-08-21,138,139,2026-08-22,1,115.62341255081678,146.0,30.37658744918322
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,1,139,2026-08-22,139,140,2026-08-23,1,139.92468251016336,136.0,-3.9246825101633647
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,112,2026-07-26,112,113,2026-07-27,1,134.22294603035346,89.0,-45.222946030353455
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,112,2026-07-26,112,114,2026-07-28,2,134.22294603035346,91.0,-43.222946030353455
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,112,2026-07-26,112,115,2026-07-29,3,134.22294603035346,92.0,-42.222946030353455
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,112,2026-07-26,112,116,2026-07-30,4,134.22294603035346,97.0,-37.222946030353455
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,112,2026-07-26,112,117,2026-07-31,5,134.22294603035346,115.0,-19.222946030353455
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,113,2026-07-27,113,114,2026-07-28,1,98.0445892060707,91.0,-7.044589206070697
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,113,2026-07-27,113,115,2026-07-29,2,98.0445892060707,92.0,-6.044589206070697
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,113,2026-07-27,113,116,2026-07-30,3,98.0445892060707,97.0,-1.0445892060706967
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,113,2026-07-27,113,117,2026-07-31,4,98.0445892060707,115.0,16.955410793929303
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,113,2026-07-27,113,118,2026-08-01,5,98.0445892060707,239.0,140.9554107939293
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,114,2026-07-28,114,115,2026-07-29,1,92.40891784121413,92.0,-0.40891784121413366
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,114,2026-07-28,114,116,2026-07-30,2,92.40891784121413,97.0,4.591082158785866
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,114,2026-07-28,114,117,2026-07-31,3,92.40891784121413,115.0,22.591082158785866
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,114,2026-07-28,114,118,2026-08-01,4,92.40891784121413,239.0,146.59108215878587
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,114,2026-07-28,114,119,2026-08-02,5,92.40891784121413,227.0,134.59108215878587
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,115,2026-07-29,115,116,2026-07-30,1,92.08178356824283,97.0,4.918216431757173
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,115,2026-07-29,115,117,2026-07-31,2,92.08178356824283,115.0,22.918216431757173
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,115,2026-07-29,115,118,2026-08-01,3,92.08178356824283,239.0,146.91821643175717
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,115,2026-07-29,115,119,2026-08-02,4,92.08178356824283,227.0,134.91821643175717
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,115,2026-07-29,115,120,2026-08-03,5,92.08178356824283,179.0,86.91821643175717
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,116,2026-07-30,116,117,2026-07-31,1,96.01635671364858,115.0,18.983643286351423
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,116,2026-07-30,116,118,2026-08-01,2,96.01635671364858,239.0,142.98364328635142
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,116,2026-07-30,116,119,2026-08-02,3,96.01635671364858,227.0,130.98364328635142
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,116,2026-07-30,116,120,2026-08-03,4,96.01635671364858,179.0,82.98364328635142
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,116,2026-07-30,116,121,2026-08-04,5,96.01635671364858,91.0,-5.016356713648577
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,117,2026-07-31,117,118,2026-08-01,1,111.2032713427297,239.0,127.7967286572703
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,117,2026-07-31,117,119,2026-08-02,2,111.2032713427297,227.0,115.7967286572703
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,117,2026-07-31,117,120,2026-08-03,3,111.2032713427297,179.0,67.7967286572703
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,117,2026-07-31,117,121,2026-08-04,4,111.2032713427297,91.0,-20.203271342729707
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,117,2026-07-31,117,122,2026-08-05,5,111.2032713427297,94.0,-17.203271342729707
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,118,2026-08-01,118,119,2026-08-02,1,213.44065426854596,227.0,13.559345731454044
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,118,2026-08-01,118,120,2026-08-03,2,213.44065426854596,179.0,-34.440654268545956
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,118,2026-08-01,118,121,2026-08-04,3,213.44065426854596,91.0,-122.44065426854596
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,118,2026-08-01,118,122,2026-08-05,4,213.44065426854596,94.0,-119.44065426854596
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,118,2026-08-01,118,123,2026-08-06,5,213.44065426854596,99.0,-114.44065426854596
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,119,2026-08-02,119,120,2026-08-03,1,224.28813085370922,179.0,-45.28813085370922
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,119,2026-08-02,119,121,2026-08-04,2,224.28813085370922,91.0,-133.28813085370922
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,119,2026-08-02,119,122,2026-08-05,3,224.28813085370922,94.0,-130.28813085370922
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,119,2026-08-02,119,123,2026-08-06,4,224.28813085370922,99.0,-125.28813085370922
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,119,2026-08-02,119,124,2026-08-07,5,224.28813085370922,115.0,-109.28813085370922
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,120,2026-08-03,120,121,2026-08-04,1,188.05762617074186,91.0,-97.05762617074186
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,120,2026-08-03,120,122,2026-08-05,2,188.05762617074186,94.0,-94.05762617074186
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,120,2026-08-03,120,123,2026-08-06,3,188.05762617074186,99.0,-89.05762617074186
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,120,2026-08-03,120,124,2026-08-07,4,188.05762617074186,115.0,-73.05762617074186
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,120,2026-08-03,120,125,2026-08-08,5,188.05762617074186,147.0,-41.057626170741855
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,121,2026-08-04,121,122,2026-08-05,1,110.41152523414836,94.0,-16.411525234148357
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,121,2026-08-04,121,123,2026-08-06,2,110.41152523414836,99.0,-11.411525234148357
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,121,2026-08-04,121,124,2026-08-07,3,110.41152523414836,115.0,4.588474765851643
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,121,2026-08-04,121,125,2026-08-08,4,110.41152523414836,147.0,36.58847476585164
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,121,2026-08-04,121,126,2026-08-09,5,110.41152523414836,136.0,25.588474765851643
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,122,2026-08-05,122,123,2026-08-06,1,97.28230504682966,99.0,1.7176949531703372
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,122,2026-08-05,122,124,2026-08-07,2,97.28230504682966,115.0,17.717694953170337
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,122,2026-08-05,122,125,2026-08-08,3,97.28230504682966,147.0,49.71769495317034
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,122,2026-08-05,122,126,2026-08-09,4,97.28230504682966,136.0,38.71769495317034
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,122,2026-08-05,122,127,2026-08-10,5,97.28230504682966,92.0,-5.282305046829663
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,123,2026-08-06,123,124,2026-08-07,1,98.65646100936593,115.0,16.343538990634073
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,123,2026-08-06,123,125,2026-08-08,2,98.65646100936593,147.0,48.34353899063407
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,123,2026-08-06,123,126,2026-08-09,3,98.65646100936593,136.0,37.34353899063407
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,123,2026-08-06,123,127,2026-08-10,4,98.65646100936593,92.0,-6.656461009365927
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,123,2026-08-06,123,128,2026-08-11,5,98.65646100936593,95.0,-3.656461009365927
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,124,2026-08-07,124,125,2026-08-08,1,111.73129220187317,147.0,35.268707798126826
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,124,2026-08-07,124,126,2026-08-09,2,111.73129220187317,136.0,24.268707798126826
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,124,2026-08-07,124,127,2026-08-10,3,111.73129220187317,92.0,-19.731292201873174
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,124,2026-08-07,124,128,2026-08-11,4,111.73129220187317,95.0,-16.731292201873174
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,124,2026-08-07,124,129,2026-08-12,5,111.73129220187317,93.0,-18.731292201873174
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,125,2026-08-08,125,126,2026-08-09,1,139.94625844037463,136.0,-3.946258440374635
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,125,2026-08-08,125,127,2026-08-10,2,139.94625844037463,92.0,-47.946258440374635
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,125,2026-08-08,125,128,2026-08-11,3,139.94625844037463,95.0,-44.946258440374635
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,125,2026-08-08,125,129,2026-08-12,4,139.94625844037463,93.0,-46.946258440374635
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,125,2026-08-08,125,130,2026-08-13,5,139.94625844037463,96.0,-43.946258440374635
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,126,2026-08-09,126,127,2026-08-10,1,136.78925168807493,92.0,-44.78925168807493
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,126,2026-08-09,126,128,2026-08-11,2,136.78925168807493,95.0,-41.78925168807493
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,126,2026-08-09,126,129,2026-08-12,3,136.78925168807493,93.0,-43.78925168807493
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,126,2026-08-09,126,130,2026-08-13,4,136.78925168807493,96.0,-40.78925168807493
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,126,2026-08-09,126,131,2026-08-14,5,136.78925168807493,120.0,-16.789251688074927
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,127,2026-08-10,127,128,2026-08-11,1,100.95785033761499,95.0,-5.957850337614985
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,127,2026-08-10,127,129,2026-08-12,2,100.95785033761499,93.0,-7.957850337614985
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,127,2026-08-10,127,130,2026-08-13,3,100.95785033761499,96.0,-4.957850337614985
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,127,2026-08-10,127,131,2026-08-14,4,100.95785033761499,120.0,19.042149662385015
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,127,2026-08-10,127,132,2026-08-15,5,100.95785033761499,151.0,50.042149662385015
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,128,2026-08-11,128,129,2026-08-12,1,96.19157006752299,93.0,-3.1915700675229886
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,128,2026-08-11,128,130,2026-08-13,2,96.19157006752299,96.0,-0.19157006752298855
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,128,2026-08-11,128,131,2026-08-14,3,96.19157006752299,120.0,23.80842993247701
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,128,2026-08-11,128,132,2026-08-15,4,96.19157006752299,151.0,54.80842993247701
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,128,2026-08-11,128,133,2026-08-16,5,96.19157006752299,138.0,41.80842993247701
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,129,2026-08-12,129,130,2026-08-13,1,93.6383140135046,96.0,2.3616859864954023
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,129,2026-08-12,129,131,2026-08-14,2,93.6383140135046,120.0,26.361685986495402
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,129,2026-08-12,129,132,2026-08-15,3,93.6383140135046,151.0,57.3616859864954
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,129,2026-08-12,129,133,2026-08-16,4,93.6383140135046,138.0,44.3616859864954
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,129,2026-08-12,129,134,2026-08-17,5,93.6383140135046,91.0,-2.6383140135045977
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,130,2026-08-13,130,131,2026-08-14,1,95.52766280270093,120.0,24.47233719729907
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,130,2026-08-13,130,132,2026-08-15,2,95.52766280270093,151.0,55.47233719729907
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,130,2026-08-13,130,133,2026-08-16,3,95.52766280270093,138.0,42.47233719729907
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,130,2026-08-13,130,134,2026-08-17,4,95.52766280270093,91.0,-4.527662802700931
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,130,2026-08-13,130,135,2026-08-18,5,95.52766280270093,96.0,0.4723371972990691
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,131,2026-08-14,131,132,2026-08-15,1,115.10553256054018,151.0,35.89446743945982
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,131,2026-08-14,131,133,2026-08-16,2,115.10553256054018,138.0,22.894467439459817
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,131,2026-08-14,131,134,2026-08-17,3,115.10553256054018,91.0,-24.105532560540183
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,131,2026-08-14,131,135,2026-08-18,4,115.10553256054018,96.0,-19.105532560540183
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,131,2026-08-14,131,136,2026-08-19,5,115.10553256054018,94.0,-21.105532560540183
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,132,2026-08-15,132,133,2026-08-16,1,143.82110651210803,138.0,-5.821106512108031
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,132,2026-08-15,132,134,2026-08-17,2,143.82110651210803,91.0,-52.82110651210803
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,132,2026-08-15,132,135,2026-08-18,3,143.82110651210803,96.0,-47.82110651210803
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,132,2026-08-15,132,136,2026-08-19,4,143.82110651210803,94.0,-49.82110651210803
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,132,2026-08-15,132,137,2026-08-20,5,143.82110651210803,94.0,-49.82110651210803
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,133,2026-08-16,133,134,2026-08-17,1,139.1642213024216,91.0,-48.164221302421595
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,133,2026-08-16,133,135,2026-08-18,2,139.1642213024216,96.0,-43.164221302421595
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,133,2026-08-16,133,136,2026-08-19,3,139.1642213024216,94.0,-45.164221302421595
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,133,2026-08-16,133,137,2026-08-20,4,139.1642213024216,94.0,-45.164221302421595
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,133,2026-08-16,133,138,2026-08-21,5,139.1642213024216,121.0,-18.164221302421595
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,134,2026-08-17,134,135,2026-08-18,1,100.6328442604843,96.0,-4.632844260484305
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,134,2026-08-17,134,136,2026-08-19,2,100.6328442604843,94.0,-6.632844260484305
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,134,2026-08-17,134,137,2026-08-20,3,100.6328442604843,94.0,-6.632844260484305
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,134,2026-08-17,134,138,2026-08-21,4,100.6328442604843,121.0,20.367155739515695
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,134,2026-08-17,134,139,2026-08-22,5,100.6328442604843,146.0,45.367155739515695
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,135,2026-08-18,135,136,2026-08-19,1,96.92656885209686,94.0,-2.926568852096864
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,135,2026-08-18,135,137,2026-08-20,2,96.92656885209686,94.0,-2.926568852096864
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,135,2026-08-18,135,138,2026-08-21,3,96.92656885209686,121.0,24.073431147903136
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,135,2026-08-18,135,139,2026-08-22,4,96.92656885209686,146.0,49.073431147903136
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",pieces/day,5,135,2026-08-18,135,140,2026-08-23,5,96.92656885209686,136.0,39.073431147903136

~~~~

# 文件 experiments/d13-rolling-backtest/practice/results/run_manifest.json

SHA256 f15a366e3e28f5475831922b75ae62199fc55e4db1bf51a0f8b01d387cad885d

~~~~text
{
  "run_id": "D13-v2-development-replay",
  "source": {
    "source_version": "D9-v1",
    "public_zip_sha256": "0063b6ddae7459eff9dc7779c0a0a6c9ecef8d0bd48320c653eae1c072ce1c31",
    "files": {
      "data/hewei-development.csv": "292072a63439529f22a73d41b83516928ae5a5b474b907b33d42e74962c23407",
      "data/apparel-development.csv": "56badd2fc37decd72b2f55a980acb7add2594b96c7b8d269f6aaae59ee7d47e5"
    },
    "copy_policy": "Development CSV bytes copied from D12 at repository HEAD 8fc0bdf14d695ca074736d26357094acf63644fe; inherited D9 hashes verified. Only days 1..140.",
    "public_zip_hash_status": "Inherited declaration only; original D9 ZIP not opened or reverified for D13."
  },
  "methods": [
    [
      "SNaive7",
      {
        "method": "seasonal_naive_7"
      }
    ],
    [
      "MA3",
      {
        "method": "moving_average",
        "k": 3
      }
    ],
    [
      "MA7",
      {
        "method": "moving_average",
        "k": 7
      }
    ],
    [
      "MA14",
      {
        "method": "moving_average",
        "k": 14
      }
    ],
    [
      "SES0.2",
      {
        "method": "ses",
        "alpha": 0.2
      }
    ],
    [
      "SES0.5",
      {
        "method": "ses",
        "alpha": 0.5
      }
    ],
    [
      "SES0.8",
      {
        "method": "ses",
        "alpha": 0.8
      }
    ]
  ],
  "initial_history": [
    1,
    112
  ],
  "validation": [
    113,
    140
  ],
  "forecasts": 2072,
  "one_day_targets_per_method_case": 28,
  "five_day_windows_per_method_case": 24,
  "forecast_order": "issue all h at an origin before attach labels; expanding observed history across origins",
  "test_labels": "not included or accessed",
  "main_experiment": "fully observed simulated demand",
  "stockout_counterexample": "separate January data, never passed to forecasting models",
  "five_day_wape_denominator": "sum of actual totals across 24 overlapping windows, not unique volume"
}

~~~~

# 文件 experiments/d13-rolling-backtest/practice/results/stockout_metrics.csv

SHA256 94b1ed2797ac658bfc37d6f190de4d6c3ed655f7afd4efbebcb0736ec0ffdd68

~~~~text
case,unit,target,mask,n,actual_sum,absolute_error_sum,me,mae,rmse,wape,wape_status
hewei,kg/day,observed_sales,same 12 open days with observed sales; no missing or closed day,12,231.0,75.0,-0.75,6.25,9.205976319760985,0.3246753246753247,defined
hewei,kg/day,latent_simulated_demand,same 12 open days with observed sales; no missing or closed day,12,304.0,108.0,5.333333333333333,9.0,11.423659658795861,0.35526315789473684,defined
apparel,pieces/day,observed_sales,same 12 open days with observed sales; no missing or closed day,12,1155.0,375.0,-3.75,31.25,46.02988159880492,0.3246753246753247,defined
apparel,pieces/day,latent_simulated_demand,same 12 open days with observed sales; no missing or closed day,12,1520.0,540.0,26.666666666666668,45.0,57.11829829397931,0.35526315789473684,defined

~~~~

# 文件 experiments/d13-rolling-backtest/practice/results/stockout_simulation.csv

SHA256 125758a180f33a64096ada34d2ab855165a9c2d92564518372a7c93f34a3f28b

~~~~text
case,unit,simulation_day,date,status,latent_simulated_demand,capacity,observed_sales,fixed_demo_prediction,lost_simulated_demand
hewei,kg/day,1,2026-01-05,observed,18,60,18,20,0
hewei,kg/day,2,2026-01-06,observed,22,60,22,20,0
hewei,kg/day,3,2026-01-07,observed,0,60,0,20,0
hewei,kg/day,4,2026-01-08,observed,24,60,24,20,0
hewei,kg/day,5,2026-01-09,closed,,60,,20,
hewei,kg/day,6,2026-01-10,stockout,40,20,20,20,20
hewei,kg/day,7,2026-01-11,stockout,38,20,20,20,18
hewei,kg/day,8,2026-01-12,missing,26,60,,20,
hewei,kg/day,9,2026-01-13,observed,22,60,22,20,0
hewei,kg/day,10,2026-01-14,observed,24,60,24,20,0
hewei,kg/day,11,2026-01-15,observed,28,60,28,20,0
hewei,kg/day,12,2026-01-16,stockout,35,0,0,20,35
hewei,kg/day,13,2026-01-17,observed,30,60,30,20,0
hewei,kg/day,14,2026-01-18,observed,23,60,23,20,0
apparel,pieces/day,1,2026-01-05,observed,90,300,90,100,0
apparel,pieces/day,2,2026-01-06,observed,110,300,110,100,0
apparel,pieces/day,3,2026-01-07,observed,0,300,0,100,0
apparel,pieces/day,4,2026-01-08,observed,120,300,120,100,0
apparel,pieces/day,5,2026-01-09,closed,,300,,100,
apparel,pieces/day,6,2026-01-10,stockout,200,100,100,100,100
apparel,pieces/day,7,2026-01-11,stockout,190,100,100,100,90
apparel,pieces/day,8,2026-01-12,missing,130,300,,100,
apparel,pieces/day,9,2026-01-13,observed,110,300,110,100,0
apparel,pieces/day,10,2026-01-14,observed,120,300,120,100,0
apparel,pieces/day,11,2026-01-15,observed,140,300,140,100,0
apparel,pieces/day,12,2026-01-16,stockout,175,0,0,100,175
apparel,pieces/day,13,2026-01-17,observed,150,300,150,100,0
apparel,pieces/day,14,2026-01-18,observed,115,300,115,100,0

~~~~

# 文件 experiments/d13-rolling-backtest/practice/results/window_totals.csv

SHA256 650b120923de275485dcabcf09b370ea3cef13480babd2c454166e3ce61ea82d

~~~~text
run_id,case,series,method,parameters,origin_day,origin_date,task_horizon,unit,first_target_day,last_target_day,first_target_date,last_target_date,actual,prediction,error,sum_daily_absolute_errors
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",112,2026-07-26,1,kg/day,113,113,2026-07-27,2026-07-27,18.0,19.0,-1.0,1.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",113,2026-07-27,1,kg/day,114,114,2026-07-28,2026-07-28,20.0,25.0,-5.0,5.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",114,2026-07-28,1,kg/day,115,115,2026-07-29,2026-07-29,24.0,19.0,5.0,5.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",115,2026-07-29,1,kg/day,116,116,2026-07-30,2026-07-30,24.0,22.0,2.0,2.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",116,2026-07-30,1,kg/day,117,117,2026-07-31,2026-07-31,30.0,28.0,2.0,2.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",117,2026-07-31,1,kg/day,118,118,2026-08-01,2026-08-01,37.0,38.0,-1.0,1.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",118,2026-08-01,1,kg/day,119,119,2026-08-02,2026-08-02,31.0,29.0,2.0,2.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",119,2026-08-02,1,kg/day,120,120,2026-08-03,2026-08-03,19.0,18.0,1.0,1.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",120,2026-08-03,1,kg/day,121,121,2026-08-04,2026-08-04,22.0,20.0,2.0,2.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",121,2026-08-04,1,kg/day,122,122,2026-08-05,2026-08-05,23.0,24.0,-1.0,1.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",122,2026-08-05,1,kg/day,123,123,2026-08-06,2026-08-06,26.0,24.0,2.0,2.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",123,2026-08-06,1,kg/day,124,124,2026-08-07,2026-08-07,29.0,30.0,-1.0,1.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",124,2026-08-07,1,kg/day,125,125,2026-08-08,2026-08-08,34.0,37.0,-3.0,3.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",125,2026-08-08,1,kg/day,126,126,2026-08-09,2026-08-09,32.0,31.0,1.0,1.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",126,2026-08-09,1,kg/day,127,127,2026-08-10,2026-08-10,20.0,19.0,1.0,1.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",127,2026-08-10,1,kg/day,128,128,2026-08-11,2026-08-11,22.0,22.0,0.0,0.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",128,2026-08-11,1,kg/day,129,129,2026-08-12,2026-08-12,20.0,23.0,-3.0,3.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",129,2026-08-12,1,kg/day,130,130,2026-08-13,2026-08-13,23.0,26.0,-3.0,3.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",130,2026-08-13,1,kg/day,131,131,2026-08-14,2026-08-14,31.0,29.0,2.0,2.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",131,2026-08-14,1,kg/day,132,132,2026-08-15,2026-08-15,33.0,34.0,-1.0,1.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",132,2026-08-15,1,kg/day,133,133,2026-08-16,2026-08-16,34.0,32.0,2.0,2.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",133,2026-08-16,1,kg/day,134,134,2026-08-17,2026-08-17,19.0,20.0,-1.0,1.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",134,2026-08-17,1,kg/day,135,135,2026-08-18,2026-08-18,22.0,22.0,0.0,0.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",135,2026-08-18,1,kg/day,136,136,2026-08-19,2026-08-19,20.0,20.0,0.0,0.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",136,2026-08-19,1,kg/day,137,137,2026-08-20,2026-08-20,24.0,23.0,1.0,1.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",137,2026-08-20,1,kg/day,138,138,2026-08-21,2026-08-21,31.0,31.0,0.0,0.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",138,2026-08-21,1,kg/day,139,139,2026-08-22,2026-08-22,38.0,33.0,5.0,5.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",139,2026-08-22,1,kg/day,140,140,2026-08-23,2026-08-23,32.0,34.0,-2.0,2.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",112,2026-07-26,5,kg,113,117,2026-07-27,2026-07-31,116.0,113.0,3.0,15.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",113,2026-07-27,5,kg,114,118,2026-07-28,2026-08-01,135.0,132.0,3.0,15.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",114,2026-07-28,5,kg,115,119,2026-07-29,2026-08-02,146.0,136.0,10.0,12.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",115,2026-07-29,5,kg,116,120,2026-07-30,2026-08-03,141.0,135.0,6.0,8.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",116,2026-07-30,5,kg,117,121,2026-07-31,2026-08-04,139.0,133.0,6.0,8.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",117,2026-07-31,5,kg,118,122,2026-08-01,2026-08-05,132.0,129.0,3.0,7.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",118,2026-08-01,5,kg,119,123,2026-08-02,2026-08-06,121.0,115.0,6.0,8.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",119,2026-08-02,5,kg,120,124,2026-08-03,2026-08-07,119.0,116.0,3.0,7.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",120,2026-08-03,5,kg,121,125,2026-08-04,2026-08-08,134.0,135.0,-1.0,9.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",121,2026-08-04,5,kg,122,126,2026-08-05,2026-08-09,144.0,146.0,-2.0,8.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",122,2026-08-05,5,kg,123,127,2026-08-06,2026-08-10,141.0,141.0,0.0,8.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",123,2026-08-06,5,kg,124,128,2026-08-07,2026-08-11,137.0,139.0,-2.0,6.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",124,2026-08-07,5,kg,125,129,2026-08-08,2026-08-12,128.0,132.0,-4.0,8.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",125,2026-08-08,5,kg,126,130,2026-08-09,2026-08-13,117.0,121.0,-4.0,8.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",126,2026-08-09,5,kg,127,131,2026-08-10,2026-08-14,116.0,119.0,-3.0,9.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",127,2026-08-10,5,kg,128,132,2026-08-11,2026-08-15,129.0,134.0,-5.0,9.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",128,2026-08-11,5,kg,129,133,2026-08-12,2026-08-16,141.0,144.0,-3.0,11.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",129,2026-08-12,5,kg,130,134,2026-08-13,2026-08-17,140.0,141.0,-1.0,9.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",130,2026-08-13,5,kg,131,135,2026-08-14,2026-08-18,139.0,137.0,2.0,6.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",131,2026-08-14,5,kg,132,136,2026-08-15,2026-08-19,128.0,128.0,0.0,4.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",132,2026-08-15,5,kg,133,137,2026-08-16,2026-08-20,119.0,117.0,2.0,4.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",133,2026-08-16,5,kg,134,138,2026-08-17,2026-08-21,116.0,116.0,0.0,2.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",134,2026-08-17,5,kg,135,139,2026-08-18,2026-08-22,135.0,129.0,6.0,6.0
D13-v2-development-replay,hewei,hewei/A/SKU01,SNaive7,"{""method"":""seasonal_naive_7""}",135,2026-08-18,5,kg,136,140,2026-08-19,2026-08-23,145.0,141.0,4.0,8.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",112,2026-07-26,1,kg/day,113,113,2026-07-27,2026-07-27,18.0,31.666666666666668,-13.666666666666668,13.666666666666668
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",113,2026-07-27,1,kg/day,114,114,2026-07-28,2026-07-28,20.0,28.333333333333332,-8.333333333333332,8.333333333333332
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",114,2026-07-28,1,kg/day,115,115,2026-07-29,2026-07-29,24.0,22.333333333333332,1.6666666666666679,1.6666666666666679
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",115,2026-07-29,1,kg/day,116,116,2026-07-30,2026-07-30,24.0,20.666666666666668,3.333333333333332,3.333333333333332
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",116,2026-07-30,1,kg/day,117,117,2026-07-31,2026-07-31,30.0,22.666666666666668,7.333333333333332,7.333333333333332
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",117,2026-07-31,1,kg/day,118,118,2026-08-01,2026-08-01,37.0,26.0,11.0,11.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",118,2026-08-01,1,kg/day,119,119,2026-08-02,2026-08-02,31.0,30.333333333333332,0.6666666666666679,0.6666666666666679
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",119,2026-08-02,1,kg/day,120,120,2026-08-03,2026-08-03,19.0,32.666666666666664,-13.666666666666664,13.666666666666664
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",120,2026-08-03,1,kg/day,121,121,2026-08-04,2026-08-04,22.0,29.0,-7.0,7.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",121,2026-08-04,1,kg/day,122,122,2026-08-05,2026-08-05,23.0,24.0,-1.0,1.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",122,2026-08-05,1,kg/day,123,123,2026-08-06,2026-08-06,26.0,21.333333333333332,4.666666666666668,4.666666666666668
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",123,2026-08-06,1,kg/day,124,124,2026-08-07,2026-08-07,29.0,23.666666666666668,5.333333333333332,5.333333333333332
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",124,2026-08-07,1,kg/day,125,125,2026-08-08,2026-08-08,34.0,26.0,8.0,8.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",125,2026-08-08,1,kg/day,126,126,2026-08-09,2026-08-09,32.0,29.666666666666668,2.333333333333332,2.333333333333332
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",126,2026-08-09,1,kg/day,127,127,2026-08-10,2026-08-10,20.0,31.666666666666668,-11.666666666666668,11.666666666666668
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",127,2026-08-10,1,kg/day,128,128,2026-08-11,2026-08-11,22.0,28.666666666666668,-6.666666666666668,6.666666666666668
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",128,2026-08-11,1,kg/day,129,129,2026-08-12,2026-08-12,20.0,24.666666666666668,-4.666666666666668,4.666666666666668
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",129,2026-08-12,1,kg/day,130,130,2026-08-13,2026-08-13,23.0,20.666666666666668,2.333333333333332,2.333333333333332
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",130,2026-08-13,1,kg/day,131,131,2026-08-14,2026-08-14,31.0,21.666666666666668,9.333333333333332,9.333333333333332
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",131,2026-08-14,1,kg/day,132,132,2026-08-15,2026-08-15,33.0,24.666666666666668,8.333333333333332,8.333333333333332
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",132,2026-08-15,1,kg/day,133,133,2026-08-16,2026-08-16,34.0,29.0,5.0,5.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",133,2026-08-16,1,kg/day,134,134,2026-08-17,2026-08-17,19.0,32.666666666666664,-13.666666666666664,13.666666666666664
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",134,2026-08-17,1,kg/day,135,135,2026-08-18,2026-08-18,22.0,28.666666666666668,-6.666666666666668,6.666666666666668
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",135,2026-08-18,1,kg/day,136,136,2026-08-19,2026-08-19,20.0,25.0,-5.0,5.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",136,2026-08-19,1,kg/day,137,137,2026-08-20,2026-08-20,24.0,20.333333333333332,3.666666666666668,3.666666666666668
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",137,2026-08-20,1,kg/day,138,138,2026-08-21,2026-08-21,31.0,22.0,9.0,9.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",138,2026-08-21,1,kg/day,139,139,2026-08-22,2026-08-22,38.0,25.0,13.0,13.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",139,2026-08-22,1,kg/day,140,140,2026-08-23,2026-08-23,32.0,31.0,1.0,1.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",112,2026-07-26,5,kg,113,117,2026-07-27,2026-07-31,116.0,158.33333333333334,-42.33333333333334,42.33333333333334
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",113,2026-07-27,5,kg,114,118,2026-07-28,2026-08-01,135.0,141.66666666666666,-6.666666666666657,27.333333333333332
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",114,2026-07-28,5,kg,115,119,2026-07-29,2026-08-02,146.0,111.66666666666666,34.33333333333334,34.33333333333334
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",115,2026-07-29,5,kg,116,120,2026-07-30,2026-08-03,141.0,103.33333333333334,37.66666666666666,41.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",116,2026-07-30,5,kg,117,121,2026-07-31,2026-08-04,139.0,113.33333333333334,25.666666666666657,34.33333333333333
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",117,2026-07-31,5,kg,118,122,2026-08-01,2026-08-05,132.0,130.0,2.0,30.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",118,2026-08-01,5,kg,119,123,2026-08-02,2026-08-06,121.0,151.66666666666666,-30.666666666666657,31.999999999999996
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",119,2026-08-02,5,kg,120,124,2026-08-03,2026-08-07,119.0,163.33333333333331,-44.333333333333314,44.33333333333332
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",120,2026-08-03,5,kg,121,125,2026-08-04,2026-08-08,134.0,145.0,-11.0,21.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",121,2026-08-04,5,kg,122,126,2026-08-05,2026-08-09,144.0,120.0,24.0,26.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",122,2026-08-05,5,kg,123,127,2026-08-06,2026-08-10,141.0,106.66666666666666,34.33333333333334,37.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",123,2026-08-06,5,kg,124,128,2026-08-07,2026-08-11,137.0,118.33333333333334,18.666666666666657,29.333333333333332
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",124,2026-08-07,5,kg,125,129,2026-08-08,2026-08-12,128.0,130.0,-2.0,30.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",125,2026-08-08,5,kg,126,130,2026-08-09,2026-08-13,117.0,148.33333333333334,-31.333333333333343,36.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",126,2026-08-09,5,kg,127,131,2026-08-10,2026-08-14,116.0,158.33333333333334,-42.33333333333334,42.33333333333334
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",127,2026-08-10,5,kg,128,132,2026-08-11,2026-08-15,129.0,143.33333333333334,-14.333333333333343,27.666666666666668
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",128,2026-08-11,5,kg,129,133,2026-08-12,2026-08-16,141.0,123.33333333333334,17.666666666666657,30.333333333333332
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",129,2026-08-12,5,kg,130,134,2026-08-13,2026-08-17,140.0,103.33333333333334,36.66666666666666,40.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",130,2026-08-13,5,kg,131,135,2026-08-14,2026-08-18,139.0,108.33333333333334,30.666666666666657,36.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",131,2026-08-14,5,kg,132,136,2026-08-15,2026-08-19,128.0,123.33333333333334,4.666666666666657,30.666666666666668
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",132,2026-08-15,5,kg,133,137,2026-08-16,2026-08-20,119.0,145.0,-26.0,36.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",133,2026-08-16,5,kg,134,138,2026-08-17,2026-08-21,116.0,163.33333333333331,-47.333333333333314,47.33333333333332
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",134,2026-08-17,5,kg,135,139,2026-08-18,2026-08-22,135.0,143.33333333333334,-8.333333333333343,31.666666666666668
D13-v2-development-replay,hewei,hewei/A/SKU01,MA3,"{""k"":3,""method"":""moving_average""}",135,2026-08-18,5,kg,136,140,2026-08-19,2026-08-23,145.0,125.0,20.0,32.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",112,2026-07-26,1,kg/day,113,113,2026-07-27,2026-07-27,18.0,25.714285714285715,-7.714285714285715,7.714285714285715
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",113,2026-07-27,1,kg/day,114,114,2026-07-28,2026-07-28,20.0,25.571428571428573,-5.571428571428573,5.571428571428573
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",114,2026-07-28,1,kg/day,115,115,2026-07-29,2026-07-29,24.0,24.857142857142858,-0.8571428571428577,0.8571428571428577
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",115,2026-07-29,1,kg/day,116,116,2026-07-30,2026-07-30,24.0,25.571428571428573,-1.571428571428573,1.571428571428573
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",116,2026-07-30,1,kg/day,117,117,2026-07-31,2026-07-31,30.0,25.857142857142858,4.142857142857142,4.142857142857142
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",117,2026-07-31,1,kg/day,118,118,2026-08-01,2026-08-01,37.0,26.142857142857142,10.857142857142858,10.857142857142858
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",118,2026-08-01,1,kg/day,119,119,2026-08-02,2026-08-02,31.0,26.0,5.0,5.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",119,2026-08-02,1,kg/day,120,120,2026-08-03,2026-08-03,19.0,26.285714285714285,-7.285714285714285,7.285714285714285
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",120,2026-08-03,1,kg/day,121,121,2026-08-04,2026-08-04,22.0,26.428571428571427,-4.428571428571427,4.428571428571427
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",121,2026-08-04,1,kg/day,122,122,2026-08-05,2026-08-05,23.0,26.714285714285715,-3.7142857142857153,3.7142857142857153
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",122,2026-08-05,1,kg/day,123,123,2026-08-06,2026-08-06,26.0,26.571428571428573,-0.571428571428573,0.571428571428573
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",123,2026-08-06,1,kg/day,124,124,2026-08-07,2026-08-07,29.0,26.857142857142858,2.1428571428571423,2.1428571428571423
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",124,2026-08-07,1,kg/day,125,125,2026-08-08,2026-08-08,34.0,26.714285714285715,7.285714285714285,7.285714285714285
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",125,2026-08-08,1,kg/day,126,126,2026-08-09,2026-08-09,32.0,26.285714285714285,5.714285714285715,5.714285714285715
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",126,2026-08-09,1,kg/day,127,127,2026-08-10,2026-08-10,20.0,26.428571428571427,-6.428571428571427,6.428571428571427
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",127,2026-08-10,1,kg/day,128,128,2026-08-11,2026-08-11,22.0,26.571428571428573,-4.571428571428573,4.571428571428573
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",128,2026-08-11,1,kg/day,129,129,2026-08-12,2026-08-12,20.0,26.571428571428573,-6.571428571428573,6.571428571428573
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",129,2026-08-12,1,kg/day,130,130,2026-08-13,2026-08-13,23.0,26.142857142857142,-3.1428571428571423,3.1428571428571423
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",130,2026-08-13,1,kg/day,131,131,2026-08-14,2026-08-14,31.0,25.714285714285715,5.285714285714285,5.285714285714285
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",131,2026-08-14,1,kg/day,132,132,2026-08-15,2026-08-15,33.0,26.0,7.0,7.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",132,2026-08-15,1,kg/day,133,133,2026-08-16,2026-08-16,34.0,25.857142857142858,8.142857142857142,8.142857142857142
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",133,2026-08-16,1,kg/day,134,134,2026-08-17,2026-08-17,19.0,26.142857142857142,-7.142857142857142,7.142857142857142
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",134,2026-08-17,1,kg/day,135,135,2026-08-18,2026-08-18,22.0,26.0,-4.0,4.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",135,2026-08-18,1,kg/day,136,136,2026-08-19,2026-08-19,20.0,26.0,-6.0,6.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",136,2026-08-19,1,kg/day,137,137,2026-08-20,2026-08-20,24.0,26.0,-2.0,2.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",137,2026-08-20,1,kg/day,138,138,2026-08-21,2026-08-21,31.0,26.142857142857142,4.857142857142858,4.857142857142858
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",138,2026-08-21,1,kg/day,139,139,2026-08-22,2026-08-22,38.0,26.142857142857142,11.857142857142858,11.857142857142858
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",139,2026-08-22,1,kg/day,140,140,2026-08-23,2026-08-23,32.0,26.857142857142858,5.142857142857142,5.142857142857142
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",112,2026-07-26,5,kg,113,117,2026-07-27,2026-07-31,116.0,128.57142857142858,-12.571428571428584,21.142857142857146
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",113,2026-07-27,5,kg,114,118,2026-07-28,2026-08-01,135.0,127.85714285714286,7.142857142857139,24.571428571428573
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",114,2026-07-28,5,kg,115,119,2026-07-29,2026-08-02,146.0,124.28571428571429,21.714285714285708,25.142857142857142
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",115,2026-07-29,5,kg,116,120,2026-07-30,2026-08-03,141.0,127.85714285714286,13.142857142857139,29.428571428571427
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",116,2026-07-30,5,kg,117,121,2026-07-31,2026-08-04,139.0,129.28571428571428,9.714285714285722,31.142857142857142
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",117,2026-07-31,5,kg,118,122,2026-08-01,2026-08-05,132.0,130.71428571428572,1.2857142857142776,30.142857142857142
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",118,2026-08-01,5,kg,119,123,2026-08-02,2026-08-06,121.0,130.0,-9.0,19.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",119,2026-08-02,5,kg,120,124,2026-08-03,2026-08-07,119.0,131.42857142857142,-12.428571428571416,17.857142857142854
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",120,2026-08-03,5,kg,121,125,2026-08-04,2026-08-08,134.0,132.14285714285714,1.8571428571428612,18.428571428571427
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",121,2026-08-04,5,kg,122,126,2026-08-05,2026-08-09,144.0,133.57142857142858,10.428571428571416,19.285714285714285
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",122,2026-08-05,5,kg,123,127,2026-08-06,2026-08-10,141.0,132.85714285714286,8.142857142857139,22.428571428571427
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",123,2026-08-06,5,kg,124,128,2026-08-07,2026-08-11,137.0,134.28571428571428,2.7142857142857224,26.142857142857142
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",124,2026-08-07,5,kg,125,129,2026-08-08,2026-08-12,128.0,133.57142857142858,-5.571428571428584,30.714285714285715
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",125,2026-08-08,5,kg,126,130,2026-08-09,2026-08-13,117.0,131.42857142857142,-14.428571428571416,25.857142857142854
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",126,2026-08-09,5,kg,127,131,2026-08-10,2026-08-14,116.0,132.14285714285714,-16.14285714285714,25.28571428571428
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",127,2026-08-10,5,kg,128,132,2026-08-11,2026-08-15,129.0,132.85714285714286,-3.857142857142861,25.571428571428573
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",128,2026-08-11,5,kg,129,133,2026-08-12,2026-08-16,141.0,132.85714285714286,8.142857142857139,28.428571428571427
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",129,2026-08-12,5,kg,130,134,2026-08-13,2026-08-17,140.0,130.71428571428572,9.285714285714278,29.857142857142858
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",130,2026-08-13,5,kg,131,135,2026-08-14,2026-08-18,139.0,128.57142857142858,10.428571428571416,31.285714285714285
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",131,2026-08-14,5,kg,132,136,2026-08-15,2026-08-19,128.0,130.0,-2.0,32.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",132,2026-08-15,5,kg,133,137,2026-08-16,2026-08-20,119.0,129.28571428571428,-10.285714285714278,26.571428571428573
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",133,2026-08-16,5,kg,134,138,2026-08-17,2026-08-21,116.0,130.71428571428572,-14.714285714285722,24.428571428571427
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",134,2026-08-17,5,kg,135,139,2026-08-18,2026-08-22,135.0,130.0,5.0,29.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA7,"{""k"":7,""method"":""moving_average""}",135,2026-08-18,5,kg,136,140,2026-08-19,2026-08-23,145.0,130.0,15.0,31.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",112,2026-07-26,1,kg/day,113,113,2026-07-27,2026-07-27,18.0,26.357142857142858,-8.357142857142858,8.357142857142858
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",113,2026-07-27,1,kg/day,114,114,2026-07-28,2026-07-28,20.0,26.071428571428573,-6.071428571428573,6.071428571428573
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",114,2026-07-28,1,kg/day,115,115,2026-07-29,2026-07-29,24.0,26.0,-2.0,2.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",115,2026-07-29,1,kg/day,116,116,2026-07-30,2026-07-30,24.0,26.357142857142858,-2.3571428571428577,2.3571428571428577
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",116,2026-07-30,1,kg/day,117,117,2026-07-31,2026-07-31,30.0,26.214285714285715,3.7857142857142847,3.7857142857142847
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",117,2026-07-31,1,kg/day,118,118,2026-08-01,2026-08-01,37.0,26.142857142857142,10.857142857142858,10.857142857142858
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",118,2026-08-01,1,kg/day,119,119,2026-08-02,2026-08-02,31.0,26.285714285714285,4.714285714285715,4.714285714285715
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",119,2026-08-02,1,kg/day,120,120,2026-08-03,2026-08-03,19.0,26.0,-7.0,7.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",120,2026-08-03,1,kg/day,121,121,2026-08-04,2026-08-04,22.0,26.0,-4.0,4.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",121,2026-08-04,1,kg/day,122,122,2026-08-05,2026-08-05,23.0,25.785714285714285,-2.7857142857142847,2.7857142857142847
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",122,2026-08-05,1,kg/day,123,123,2026-08-06,2026-08-06,26.0,26.071428571428573,-0.07142857142857295,0.07142857142857295
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",123,2026-08-06,1,kg/day,124,124,2026-08-07,2026-08-07,29.0,26.357142857142858,2.6428571428571423,2.6428571428571423
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",124,2026-08-07,1,kg/day,125,125,2026-08-08,2026-08-08,34.0,26.428571428571427,7.571428571428573,7.571428571428573
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",125,2026-08-08,1,kg/day,126,126,2026-08-09,2026-08-09,32.0,26.142857142857142,5.857142857142858,5.857142857142858
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",126,2026-08-09,1,kg/day,127,127,2026-08-10,2026-08-10,20.0,26.357142857142858,-6.357142857142858,6.357142857142858
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",127,2026-08-10,1,kg/day,128,128,2026-08-11,2026-08-11,22.0,26.5,-4.5,4.5
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",128,2026-08-11,1,kg/day,129,129,2026-08-12,2026-08-12,20.0,26.642857142857142,-6.642857142857142,6.642857142857142
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",129,2026-08-12,1,kg/day,130,130,2026-08-13,2026-08-13,23.0,26.357142857142858,-3.3571428571428577,3.3571428571428577
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",130,2026-08-13,1,kg/day,131,131,2026-08-14,2026-08-14,31.0,26.285714285714285,4.714285714285715,4.714285714285715
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",131,2026-08-14,1,kg/day,132,132,2026-08-15,2026-08-15,33.0,26.357142857142858,6.642857142857142,6.642857142857142
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",132,2026-08-15,1,kg/day,133,133,2026-08-16,2026-08-16,34.0,26.071428571428573,7.928571428571427,7.928571428571427
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",133,2026-08-16,1,kg/day,134,134,2026-08-17,2026-08-17,19.0,26.285714285714285,-7.285714285714285,7.285714285714285
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",134,2026-08-17,1,kg/day,135,135,2026-08-18,2026-08-18,22.0,26.285714285714285,-4.285714285714285,4.285714285714285
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",135,2026-08-18,1,kg/day,136,136,2026-08-19,2026-08-19,20.0,26.285714285714285,-6.285714285714285,6.285714285714285
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",136,2026-08-19,1,kg/day,137,137,2026-08-20,2026-08-20,24.0,26.071428571428573,-2.071428571428573,2.071428571428573
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",137,2026-08-20,1,kg/day,138,138,2026-08-21,2026-08-21,31.0,25.928571428571427,5.071428571428573,5.071428571428573
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",138,2026-08-21,1,kg/day,139,139,2026-08-22,2026-08-22,38.0,26.071428571428573,11.928571428571427,11.928571428571427
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",139,2026-08-22,1,kg/day,140,140,2026-08-23,2026-08-23,32.0,26.357142857142858,5.642857142857142,5.642857142857142
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",112,2026-07-26,5,kg,113,117,2026-07-27,2026-07-31,116.0,131.78571428571428,-15.785714285714278,23.071428571428573
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",113,2026-07-27,5,kg,114,118,2026-07-28,2026-08-01,135.0,130.35714285714286,4.642857142857139,25.071428571428573
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",114,2026-07-28,5,kg,115,119,2026-07-29,2026-08-02,146.0,130.0,16.0,24.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",115,2026-07-29,5,kg,116,120,2026-07-30,2026-08-03,141.0,131.78571428571428,9.214285714285722,28.642857142857142
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",116,2026-07-30,5,kg,117,121,2026-07-31,2026-08-04,139.0,131.07142857142858,7.928571428571416,30.785714285714285
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",117,2026-07-31,5,kg,118,122,2026-08-01,2026-08-05,132.0,130.71428571428572,1.2857142857142776,30.142857142857142
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",118,2026-08-01,5,kg,119,123,2026-08-02,2026-08-06,121.0,131.42857142857142,-10.428571428571416,19.857142857142854
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",119,2026-08-02,5,kg,120,124,2026-08-03,2026-08-07,119.0,130.0,-11.0,17.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",120,2026-08-03,5,kg,121,125,2026-08-04,2026-08-08,134.0,130.0,4.0,18.0
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",121,2026-08-04,5,kg,122,126,2026-08-05,2026-08-09,144.0,128.92857142857142,15.071428571428584,20.642857142857146
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",122,2026-08-05,5,kg,123,127,2026-08-06,2026-08-10,141.0,130.35714285714286,10.642857142857139,22.928571428571427
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",123,2026-08-06,5,kg,124,128,2026-08-07,2026-08-11,137.0,131.78571428571428,5.214285714285722,26.642857142857142
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",124,2026-08-07,5,kg,125,129,2026-08-08,2026-08-12,128.0,132.14285714285714,-4.142857142857139,30.428571428571427
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",125,2026-08-08,5,kg,126,130,2026-08-09,2026-08-13,117.0,130.71428571428572,-13.714285714285722,25.428571428571427
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",126,2026-08-09,5,kg,127,131,2026-08-10,2026-08-14,116.0,131.78571428571428,-15.785714285714278,25.071428571428573
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",127,2026-08-10,5,kg,128,132,2026-08-11,2026-08-15,129.0,132.5,-3.5,25.5
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",128,2026-08-11,5,kg,129,133,2026-08-12,2026-08-16,141.0,133.21428571428572,7.785714285714278,28.357142857142858
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",129,2026-08-12,5,kg,130,134,2026-08-13,2026-08-17,140.0,131.78571428571428,8.214285714285722,29.642857142857142
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",130,2026-08-13,5,kg,131,135,2026-08-14,2026-08-18,139.0,131.42857142857142,7.571428571428584,30.714285714285715
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",131,2026-08-14,5,kg,132,136,2026-08-15,2026-08-19,128.0,131.78571428571428,-3.7857142857142776,32.35714285714286
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",132,2026-08-15,5,kg,133,137,2026-08-16,2026-08-20,119.0,130.35714285714286,-11.357142857142861,27.21428571428572
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",133,2026-08-16,5,kg,134,138,2026-08-17,2026-08-21,116.0,131.42857142857142,-15.428571428571416,24.857142857142854
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",134,2026-08-17,5,kg,135,139,2026-08-18,2026-08-22,135.0,131.42857142857142,3.5714285714285836,29.285714285714285
D13-v2-development-replay,hewei,hewei/A/SKU01,MA14,"{""k"":14,""method"":""moving_average""}",135,2026-08-18,5,kg,136,140,2026-08-19,2026-08-23,145.0,131.42857142857142,13.571428571428584,30.714285714285715
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",112,2026-07-26,1,kg/day,113,113,2026-07-27,2026-07-27,18.0,28.041724154615732,-10.041724154615732,10.041724154615732
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",113,2026-07-27,1,kg/day,114,114,2026-07-28,2026-07-28,20.0,26.03337932369259,-6.033379323692589,6.033379323692589
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",114,2026-07-28,1,kg/day,115,115,2026-07-29,2026-07-29,24.0,24.82670345895407,-0.8267034589540714,0.8267034589540714
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",115,2026-07-29,1,kg/day,116,116,2026-07-30,2026-07-30,24.0,24.661362767163258,-0.6613627671632578,0.6613627671632578
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",116,2026-07-30,1,kg/day,117,117,2026-07-31,2026-07-31,30.0,24.52909021373061,5.470909786269392,5.470909786269392
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",117,2026-07-31,1,kg/day,118,118,2026-08-01,2026-08-01,37.0,25.62327217098449,11.376727829015511,11.376727829015511
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",118,2026-08-01,1,kg/day,119,119,2026-08-02,2026-08-02,31.0,27.898617736787592,3.1013822632124075,3.1013822632124075
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",119,2026-08-02,1,kg/day,120,120,2026-08-03,2026-08-03,19.0,28.518894189430075,-9.518894189430075,9.518894189430075
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",120,2026-08-03,1,kg/day,121,121,2026-08-04,2026-08-04,22.0,26.615115351544063,-4.615115351544063,4.615115351544063
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",121,2026-08-04,1,kg/day,122,122,2026-08-05,2026-08-05,23.0,25.692092281235254,-2.6920922812352543,2.6920922812352543
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",122,2026-08-05,1,kg/day,123,123,2026-08-06,2026-08-06,26.0,25.153673824988207,0.846326175011793,0.846326175011793
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",123,2026-08-06,1,kg/day,124,124,2026-08-07,2026-08-07,29.0,25.322939059990567,3.677060940009433,3.677060940009433
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",124,2026-08-07,1,kg/day,125,125,2026-08-08,2026-08-08,34.0,26.058351247992455,7.941648752007545,7.941648752007545
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",125,2026-08-08,1,kg/day,126,126,2026-08-09,2026-08-09,32.0,27.646680998393965,4.353319001606035,4.353319001606035
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",126,2026-08-09,1,kg/day,127,127,2026-08-10,2026-08-10,20.0,28.517344798715172,-8.517344798715172,8.517344798715172
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",127,2026-08-10,1,kg/day,128,128,2026-08-11,2026-08-11,22.0,26.813875838972137,-4.8138758389721374,4.8138758389721374
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",128,2026-08-11,1,kg/day,129,129,2026-08-12,2026-08-12,20.0,25.85110067117771,-5.851100671177711,5.851100671177711
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",129,2026-08-12,1,kg/day,130,130,2026-08-13,2026-08-13,23.0,24.68088053694217,-1.680880536942169,1.680880536942169
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",130,2026-08-13,1,kg/day,131,131,2026-08-14,2026-08-14,31.0,24.344704429553737,6.655295570446263,6.655295570446263
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",131,2026-08-14,1,kg/day,132,132,2026-08-15,2026-08-15,33.0,25.67576354364299,7.32423645635701,7.32423645635701
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",132,2026-08-15,1,kg/day,133,133,2026-08-16,2026-08-16,34.0,27.140610834914394,6.859389165085606,6.859389165085606
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",133,2026-08-16,1,kg/day,134,134,2026-08-17,2026-08-17,19.0,28.512488667931517,-9.512488667931517,9.512488667931517
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",134,2026-08-17,1,kg/day,135,135,2026-08-18,2026-08-18,22.0,26.609990934345216,-4.609990934345216,4.609990934345216
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",135,2026-08-18,1,kg/day,136,136,2026-08-19,2026-08-19,20.0,25.687992747476173,-5.687992747476173,5.687992747476173
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",136,2026-08-19,1,kg/day,137,137,2026-08-20,2026-08-20,24.0,24.55039419798094,-0.550394197980939,0.550394197980939
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",137,2026-08-20,1,kg/day,138,138,2026-08-21,2026-08-21,31.0,24.440315358384755,6.559684641615245,6.559684641615245
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",138,2026-08-21,1,kg/day,139,139,2026-08-22,2026-08-22,38.0,25.752252286707805,12.247747713292195,12.247747713292195
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",139,2026-08-22,1,kg/day,140,140,2026-08-23,2026-08-23,32.0,28.201801829366246,3.7981981706337535,3.7981981706337535
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",112,2026-07-26,5,kg,113,117,2026-07-27,2026-07-31,116.0,140.20862077307865,-24.20862077307865,28.125172463847196
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",113,2026-07-27,5,kg,114,118,2026-07-28,2026-08-01,135.0,130.16689661846294,4.833103381537057,25.03337932369259
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",114,2026-07-28,5,kg,115,119,2026-07-29,2026-08-02,146.0,124.13351729477036,21.866482705229643,25.17329654104593
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",115,2026-07-29,5,kg,116,120,2026-07-30,2026-08-03,141.0,123.30681383581629,17.693186164183714,30.338637232836742
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",116,2026-07-30,5,kg,117,121,2026-07-31,2026-08-04,139.0,122.64545106865305,16.354548931346955,32.47090978626939
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",117,2026-07-31,5,kg,118,122,2026-08-01,2026-08-05,132.0,128.11636085492245,3.8836391450775523,29.62327217098449
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",118,2026-08-01,5,kg,119,123,2026-08-02,2026-08-06,121.0,139.49308868393797,-18.49308868393797,24.695853210362777
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",119,2026-08-02,5,kg,120,124,2026-08-03,2026-08-07,119.0,142.59447094715037,-23.59447094715037,24.556682568290224
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",120,2026-08-03,5,kg,121,125,2026-08-04,2026-08-08,134.0,133.0755767577203,0.924423242279687,18.615115351544063
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",121,2026-08-04,5,kg,122,126,2026-08-05,2026-08-09,144.0,128.46046140617628,15.539538593823721,20.923723156294237
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",122,2026-08-05,5,kg,123,127,2026-08-06,2026-08-10,141.0,125.76836912494103,15.231630875058968,25.53897852503538
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",123,2026-08-06,5,kg,124,128,2026-08-07,2026-08-11,137.0,126.61469529995284,10.385304700047158,27.677060940009433
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",124,2026-08-07,5,kg,125,129,2026-08-08,2026-08-12,128.0,130.29175623996227,-2.291756239962268,30.058351247992455
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",125,2026-08-08,5,kg,126,130,2026-08-09,2026-08-13,117.0,138.23340499196982,-21.23340499196982,29.940042995181894
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",126,2026-08-09,5,kg,127,131,2026-08-10,2026-08-14,116.0,142.58672399357584,-26.586723993575845,31.552034396145515
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",127,2026-08-10,5,kg,128,132,2026-08-11,2026-08-15,129.0,134.0693791948607,-5.069379194860687,25.813875838972137
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",128,2026-08-11,5,kg,129,133,2026-08-12,2026-08-16,141.0,129.25550335588855,11.74449664411145,29.14889932882229
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",129,2026-08-12,5,kg,130,134,2026-08-13,2026-08-17,140.0,123.40440268471085,16.595597315289154,31.31911946305783
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",130,2026-08-13,5,kg,131,135,2026-08-14,2026-08-18,139.0,121.72352214776868,17.276477852231324,32.65529557044626
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",131,2026-08-14,5,kg,132,136,2026-08-15,2026-08-19,128.0,128.37881771821495,-0.3788177182149468,31.67576354364299
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",132,2026-08-15,5,kg,133,137,2026-08-16,2026-08-20,119.0,135.70305417457197,-16.703054174571974,30.421832504743183
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",133,2026-08-16,5,kg,134,138,2026-08-17,2026-08-21,116.0,142.5624433396576,-26.56244333965759,31.537466003794552
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",134,2026-08-17,5,kg,135,139,2026-08-18,2026-08-22,135.0,133.04995467172608,1.9500453282739159,29.609990934345216
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.2,"{""alpha"":0.2,""method"":""ses""}",135,2026-08-18,5,kg,136,140,2026-08-19,2026-08-23,145.0,128.43996373738088,16.56003626261912,31.312007252523827
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",112,2026-07-26,1,kg/day,113,113,2026-07-27,2026-07-27,18.0,30.2663511697844,-12.2663511697844,12.2663511697844
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",113,2026-07-27,1,kg/day,114,114,2026-07-28,2026-07-28,20.0,24.1331755848922,-4.1331755848922,4.1331755848922
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",114,2026-07-28,1,kg/day,115,115,2026-07-29,2026-07-29,24.0,22.0665877924461,1.9334122075539,1.9334122075539
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",115,2026-07-29,1,kg/day,116,116,2026-07-30,2026-07-30,24.0,23.03329389622305,0.96670610377695,0.96670610377695
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",116,2026-07-30,1,kg/day,117,117,2026-07-31,2026-07-31,30.0,23.516646948111525,6.483353051888475,6.483353051888475
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",117,2026-07-31,1,kg/day,118,118,2026-08-01,2026-08-01,37.0,26.758323474055764,10.241676525944236,10.241676525944236
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",118,2026-08-01,1,kg/day,119,119,2026-08-02,2026-08-02,31.0,31.879161737027882,-0.8791617370278821,0.8791617370278821
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",119,2026-08-02,1,kg/day,120,120,2026-08-03,2026-08-03,19.0,31.439580868513943,-12.439580868513943,12.439580868513943
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",120,2026-08-03,1,kg/day,121,121,2026-08-04,2026-08-04,22.0,25.21979043425697,-3.2197904342569714,3.2197904342569714
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",121,2026-08-04,1,kg/day,122,122,2026-08-05,2026-08-05,23.0,23.609895217128486,-0.6098952171284857,0.6098952171284857
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",122,2026-08-05,1,kg/day,123,123,2026-08-06,2026-08-06,26.0,23.30494760856424,2.695052391435759,2.695052391435759
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",123,2026-08-06,1,kg/day,124,124,2026-08-07,2026-08-07,29.0,24.65247380428212,4.3475261957178795,4.3475261957178795
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",124,2026-08-07,1,kg/day,125,125,2026-08-08,2026-08-08,34.0,26.826236902141062,7.173763097858938,7.173763097858938
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",125,2026-08-08,1,kg/day,126,126,2026-08-09,2026-08-09,32.0,30.41311845107053,1.586881548929469,1.586881548929469
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",126,2026-08-09,1,kg/day,127,127,2026-08-10,2026-08-10,20.0,31.206559225535266,-11.206559225535266,11.206559225535266
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",127,2026-08-10,1,kg/day,128,128,2026-08-11,2026-08-11,22.0,25.603279612767633,-3.6032796127676328,3.6032796127676328
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",128,2026-08-11,1,kg/day,129,129,2026-08-12,2026-08-12,20.0,23.801639806383818,-3.801639806383818,3.801639806383818
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",129,2026-08-12,1,kg/day,130,130,2026-08-13,2026-08-13,23.0,21.90081990319191,1.099180096808091,1.099180096808091
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",130,2026-08-13,1,kg/day,131,131,2026-08-14,2026-08-14,31.0,22.450409951595955,8.549590048404045,8.549590048404045
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",131,2026-08-14,1,kg/day,132,132,2026-08-15,2026-08-15,33.0,26.72520497579798,6.274795024202021,6.274795024202021
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",132,2026-08-15,1,kg/day,133,133,2026-08-16,2026-08-16,34.0,29.86260248789899,4.1373975121010105,4.1373975121010105
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",133,2026-08-16,1,kg/day,134,134,2026-08-17,2026-08-17,19.0,31.931301243949495,-12.931301243949495,12.931301243949495
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",134,2026-08-17,1,kg/day,135,135,2026-08-18,2026-08-18,22.0,25.465650621974746,-3.4656506219747456,3.4656506219747456
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",135,2026-08-18,1,kg/day,136,136,2026-08-19,2026-08-19,20.0,23.732825310987373,-3.732825310987373,3.732825310987373
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",136,2026-08-19,1,kg/day,137,137,2026-08-20,2026-08-20,24.0,21.866412655493686,2.1335873445063136,2.1335873445063136
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",137,2026-08-20,1,kg/day,138,138,2026-08-21,2026-08-21,31.0,22.933206327746845,8.066793672253155,8.066793672253155
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",138,2026-08-21,1,kg/day,139,139,2026-08-22,2026-08-22,38.0,26.966603163873422,11.033396836126578,11.033396836126578
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",139,2026-08-22,1,kg/day,140,140,2026-08-23,2026-08-23,32.0,32.483301581936715,-0.4833015819367148,0.4833015819367148
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",112,2026-07-26,5,kg,113,117,2026-07-27,2026-07-31,116.0,151.331755848922,-35.331755848922,35.331755848922
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",113,2026-07-27,5,kg,114,118,2026-07-28,2026-08-01,135.0,120.665877924461,14.334122075539,23.1331755848922
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",114,2026-07-28,5,kg,115,119,2026-07-29,2026-08-02,146.0,110.3329389622305,35.6670610377695,35.6670610377695
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",115,2026-07-29,5,kg,116,120,2026-07-30,2026-08-03,141.0,115.16646948111526,25.833530518884743,33.90011831133085
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",116,2026-07-30,5,kg,117,121,2026-07-31,2026-08-04,139.0,117.58323474055763,21.41676525944237,33.48335305188847
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",117,2026-07-31,5,kg,118,122,2026-08-01,2026-08-05,132.0,133.79161737027883,-1.7916173702788285,30.758323474055764
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",118,2026-08-01,5,kg,119,123,2026-08-02,2026-08-06,121.0,159.3958086851394,-38.3958086851394,38.395808685139414
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",119,2026-08-02,5,kg,120,124,2026-08-03,2026-08-07,119.0,157.1979043425697,-38.1979043425697,38.197904342569714
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",120,2026-08-03,5,kg,121,125,2026-08-04,2026-08-08,134.0,126.09895217128485,7.90104782871515,18.78020956574303
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",121,2026-08-04,5,kg,122,126,2026-08-05,2026-08-09,144.0,118.04947608564243,25.950523914357575,27.170314348614543
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",122,2026-08-05,5,kg,123,127,2026-08-06,2026-08-10,141.0,116.52473804282121,24.475261957178787,31.085157174307277
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",123,2026-08-06,5,kg,124,128,2026-08-07,2026-08-11,137.0,123.2623690214106,13.737630978589394,28.34752619571788
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",124,2026-08-07,5,kg,125,129,2026-08-08,2026-08-12,128.0,134.1311845107053,-6.13118451070531,30.826236902141062
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",125,2026-08-08,5,kg,126,130,2026-08-09,2026-08-13,117.0,152.06559225535267,-35.06559225535267,38.23935535321159
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",126,2026-08-09,5,kg,127,131,2026-08-10,2026-08-14,116.0,156.03279612767633,-40.032796127676335,40.03279612767633
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",127,2026-08-10,5,kg,128,132,2026-08-11,2026-08-15,129.0,128.01639806383815,0.9836019361618469,24.603279612767633
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",128,2026-08-11,5,kg,129,133,2026-08-12,2026-08-16,141.0,119.00819903191909,21.99180096808091,31.198360193616182
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",129,2026-08-12,5,kg,130,134,2026-08-13,2026-08-17,140.0,109.50409951595955,30.495900484040448,36.29754029042427
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",130,2026-08-13,5,kg,131,135,2026-08-14,2026-08-18,139.0,112.25204975797978,26.747950242020224,34.54959004840404
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",131,2026-08-14,5,kg,132,136,2026-08-15,2026-08-19,128.0,133.62602487898988,-5.626024878989881,32.72520497579798
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",132,2026-08-15,5,kg,133,137,2026-08-16,2026-08-20,119.0,149.31301243949494,-30.31301243949494,38.58780746369697
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",133,2026-08-16,5,kg,134,138,2026-08-17,2026-08-21,116.0,159.65650621974748,-43.656506219747484,43.65650621974747
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",134,2026-08-17,5,kg,135,139,2026-08-18,2026-08-22,135.0,127.32825310987373,7.671746890126272,28.465650621974746
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.5,"{""alpha"":0.5,""method"":""ses""}",135,2026-08-18,5,kg,136,140,2026-08-19,2026-08-23,145.0,118.66412655493687,26.33587344506313,33.80152406703788
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",112,2026-07-26,1,kg/day,113,113,2026-07-27,2026-07-27,18.0,30.348938107400542,-12.348938107400542,12.348938107400542
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",113,2026-07-27,1,kg/day,114,114,2026-07-28,2026-07-28,20.0,20.46978762148011,-0.46978762148010844,0.46978762148010844
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",114,2026-07-28,1,kg/day,115,115,2026-07-29,2026-07-29,24.0,20.09395752429602,3.9060424757039804,3.9060424757039804
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",115,2026-07-29,1,kg/day,116,116,2026-07-30,2026-07-30,24.0,23.218791504859205,0.7812084951407954,0.7812084951407954
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",116,2026-07-30,1,kg/day,117,117,2026-07-31,2026-07-31,30.0,23.843758300971842,6.156241699028158,6.156241699028158
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",117,2026-07-31,1,kg/day,118,118,2026-08-01,2026-08-01,37.0,28.76875166019437,8.231248339805632,8.231248339805632
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",118,2026-08-01,1,kg/day,119,119,2026-08-02,2026-08-02,31.0,35.35375033203887,-4.353750332038871,4.353750332038871
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",119,2026-08-02,1,kg/day,120,120,2026-08-03,2026-08-03,19.0,31.870750066407773,-12.870750066407773,12.870750066407773
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",120,2026-08-03,1,kg/day,121,121,2026-08-04,2026-08-04,22.0,21.574150013281553,0.42584998671844687,0.42584998671844687
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",121,2026-08-04,1,kg/day,122,122,2026-08-05,2026-08-05,23.0,21.91483000265631,1.0851699973436908,1.0851699973436908
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",122,2026-08-05,1,kg/day,123,123,2026-08-06,2026-08-06,26.0,22.782966000531264,3.217033999468736,3.217033999468736
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",123,2026-08-06,1,kg/day,124,124,2026-08-07,2026-08-07,29.0,25.356593200106254,3.6434067998937465,3.6434067998937465
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",124,2026-08-07,1,kg/day,125,125,2026-08-08,2026-08-08,34.0,28.271318640021253,5.728681359978747,5.728681359978747
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",125,2026-08-08,1,kg/day,126,126,2026-08-09,2026-08-09,32.0,32.854263728004256,-0.8542637280042555,0.8542637280042555
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",126,2026-08-09,1,kg/day,127,127,2026-08-10,2026-08-10,20.0,32.170852745600854,-12.170852745600854,12.170852745600854
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",127,2026-08-10,1,kg/day,128,128,2026-08-11,2026-08-11,22.0,22.434170549120168,-0.43417054912016795,0.43417054912016795
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",128,2026-08-11,1,kg/day,129,129,2026-08-12,2026-08-12,20.0,22.086834109824032,-2.086834109824032,2.086834109824032
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",129,2026-08-12,1,kg/day,130,130,2026-08-13,2026-08-13,23.0,20.417366821964805,2.582633178035195,2.582633178035195
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",130,2026-08-13,1,kg/day,131,131,2026-08-14,2026-08-14,31.0,22.483473364392964,8.516526635607036,8.516526635607036
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",131,2026-08-14,1,kg/day,132,132,2026-08-15,2026-08-15,33.0,29.296694672878594,3.703305327121406,3.703305327121406
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",132,2026-08-15,1,kg/day,133,133,2026-08-16,2026-08-16,34.0,32.25933893457572,1.740661065424277,1.740661065424277
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",133,2026-08-16,1,kg/day,134,134,2026-08-17,2026-08-17,19.0,33.65186778691515,-14.651867786915147,14.651867786915147
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",134,2026-08-17,1,kg/day,135,135,2026-08-18,2026-08-18,22.0,21.930373557383028,0.06962644261697193,0.06962644261697193
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",135,2026-08-18,1,kg/day,136,136,2026-08-19,2026-08-19,20.0,21.986074711476604,-1.9860747114766042,1.9860747114766042
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",136,2026-08-19,1,kg/day,137,137,2026-08-20,2026-08-20,24.0,20.39721494229532,3.602785057704679,3.602785057704679
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",137,2026-08-20,1,kg/day,138,138,2026-08-21,2026-08-21,31.0,23.279442988459067,7.720557011540933,7.720557011540933
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",138,2026-08-21,1,kg/day,139,139,2026-08-22,2026-08-22,38.0,29.455888597691814,8.544111402308186,8.544111402308186
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",139,2026-08-22,1,kg/day,140,140,2026-08-23,2026-08-23,32.0,36.29117771953836,-4.291177719538361,4.291177719538361
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",112,2026-07-26,5,kg,113,117,2026-07-27,2026-07-31,116.0,151.74469053700273,-35.744690537002725,35.74469053700271
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",113,2026-07-27,5,kg,114,118,2026-07-28,2026-08-01,135.0,102.34893810740054,32.65106189259946,33.590637135559675
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",114,2026-07-28,5,kg,115,119,2026-07-29,2026-08-02,146.0,100.4697876214801,45.530212378519906,45.530212378519906
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",115,2026-07-29,5,kg,116,120,2026-07-30,2026-08-03,141.0,116.09395752429603,24.90604247570397,33.343625485422386
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",116,2026-07-30,5,kg,117,121,2026-07-31,2026-08-04,139.0,119.21879150485921,19.78120849514079,33.15624169902816
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",117,2026-07-31,5,kg,118,122,2026-08-01,2026-08-05,132.0,143.84375830097184,-11.843758300971842,32.76875166019437
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",118,2026-08-01,5,kg,119,123,2026-08-02,2026-08-06,121.0,176.76875166019437,-55.76875166019437,55.768751660194354
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",119,2026-08-02,5,kg,120,124,2026-08-03,2026-08-07,119.0,159.35375033203886,-40.35375033203886,40.353750332038864
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",120,2026-08-03,5,kg,121,125,2026-08-04,2026-08-08,134.0,107.87075006640777,26.129249933592234,26.129249933592234
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",121,2026-08-04,5,kg,122,126,2026-08-05,2026-08-09,144.0,109.57415001328155,34.42584998671845,34.425849986718454
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",122,2026-08-05,5,kg,123,127,2026-08-06,2026-08-10,141.0,113.91483000265632,27.085169997343684,32.651101998406205
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",123,2026-08-06,5,kg,124,128,2026-08-07,2026-08-11,137.0,126.78296600053127,10.217033999468725,27.643406799893746
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",124,2026-08-07,5,kg,125,129,2026-08-08,2026-08-12,128.0,141.35659320010626,-13.35659320010626,32.27131864002125
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",125,2026-08-08,5,kg,126,130,2026-08-09,2026-08-13,117.0,164.27131864002126,-47.27131864002126,47.27131864002128
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",126,2026-08-09,5,kg,127,131,2026-08-10,2026-08-14,116.0,160.85426372800427,-44.85426372800427,44.85426372800427
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",127,2026-08-10,5,kg,128,132,2026-08-11,2026-08-15,129.0,112.17085274560084,16.82914725439916,22.565829450879832
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",128,2026-08-11,5,kg,129,133,2026-08-12,2026-08-16,141.0,110.43417054912015,30.565829450879846,34.7394976705279
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",129,2026-08-12,5,kg,130,134,2026-08-13,2026-08-17,140.0,102.08683410982403,37.913165890175975,40.747899534105585
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",130,2026-08-13,5,kg,131,135,2026-08-14,2026-08-18,139.0,112.41736682196482,26.58263317803518,34.516526635607036
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",131,2026-08-14,5,kg,132,136,2026-08-15,2026-08-19,128.0,146.48347336439298,-18.483473364392978,35.296694672878594
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",132,2026-08-15,5,kg,133,137,2026-08-16,2026-08-20,119.0,161.29669467287863,-42.29669467287863,45.77801680372717
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",133,2026-08-16,5,kg,134,138,2026-08-17,2026-08-21,116.0,168.25933893457574,-52.25933893457574,52.25933893457574
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",134,2026-08-17,5,kg,135,139,2026-08-18,2026-08-22,135.0,109.65186778691515,25.348132213084853,29.208879327850916
D13-v2-development-replay,hewei,hewei/A/SKU01,SES0.8,"{""alpha"":0.8,""method"":""ses""}",135,2026-08-18,5,kg,136,140,2026-08-19,2026-08-23,145.0,109.93037355738302,35.06962644261698,39.04177586557019
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",112,2026-07-26,1,pieces/day,113,113,2026-07-27,2026-07-27,89.0,89.0,0.0,0.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",113,2026-07-27,1,pieces/day,114,114,2026-07-28,2026-07-28,91.0,89.0,2.0,2.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",114,2026-07-28,1,pieces/day,115,115,2026-07-29,2026-07-29,92.0,94.0,-2.0,2.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",115,2026-07-29,1,pieces/day,116,116,2026-07-30,2026-07-30,97.0,94.0,3.0,3.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",116,2026-07-30,1,pieces/day,117,117,2026-07-31,2026-07-31,115.0,116.0,-1.0,1.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",117,2026-07-31,1,pieces/day,118,118,2026-08-01,2026-08-01,239.0,146.0,93.0,93.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",118,2026-08-01,1,pieces/day,119,119,2026-08-02,2026-08-02,227.0,133.0,94.0,94.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",119,2026-08-02,1,pieces/day,120,120,2026-08-03,2026-08-03,179.0,89.0,90.0,90.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",120,2026-08-03,1,pieces/day,121,121,2026-08-04,2026-08-04,91.0,91.0,0.0,0.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",121,2026-08-04,1,pieces/day,122,122,2026-08-05,2026-08-05,94.0,92.0,2.0,2.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",122,2026-08-05,1,pieces/day,123,123,2026-08-06,2026-08-06,99.0,97.0,2.0,2.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",123,2026-08-06,1,pieces/day,124,124,2026-08-07,2026-08-07,115.0,115.0,0.0,0.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",124,2026-08-07,1,pieces/day,125,125,2026-08-08,2026-08-08,147.0,239.0,-92.0,92.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",125,2026-08-08,1,pieces/day,126,126,2026-08-09,2026-08-09,136.0,227.0,-91.0,91.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",126,2026-08-09,1,pieces/day,127,127,2026-08-10,2026-08-10,92.0,179.0,-87.0,87.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",127,2026-08-10,1,pieces/day,128,128,2026-08-11,2026-08-11,95.0,91.0,4.0,4.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",128,2026-08-11,1,pieces/day,129,129,2026-08-12,2026-08-12,93.0,94.0,-1.0,1.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",129,2026-08-12,1,pieces/day,130,130,2026-08-13,2026-08-13,96.0,99.0,-3.0,3.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",130,2026-08-13,1,pieces/day,131,131,2026-08-14,2026-08-14,120.0,115.0,5.0,5.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",131,2026-08-14,1,pieces/day,132,132,2026-08-15,2026-08-15,151.0,147.0,4.0,4.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",132,2026-08-15,1,pieces/day,133,133,2026-08-16,2026-08-16,138.0,136.0,2.0,2.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",133,2026-08-16,1,pieces/day,134,134,2026-08-17,2026-08-17,91.0,92.0,-1.0,1.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",134,2026-08-17,1,pieces/day,135,135,2026-08-18,2026-08-18,96.0,95.0,1.0,1.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",135,2026-08-18,1,pieces/day,136,136,2026-08-19,2026-08-19,94.0,93.0,1.0,1.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",136,2026-08-19,1,pieces/day,137,137,2026-08-20,2026-08-20,94.0,96.0,-2.0,2.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",137,2026-08-20,1,pieces/day,138,138,2026-08-21,2026-08-21,121.0,120.0,1.0,1.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",138,2026-08-21,1,pieces/day,139,139,2026-08-22,2026-08-22,146.0,151.0,-5.0,5.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",139,2026-08-22,1,pieces/day,140,140,2026-08-23,2026-08-23,136.0,138.0,-2.0,2.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",112,2026-07-26,5,pieces,113,117,2026-07-27,2026-07-31,484.0,482.0,2.0,8.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",113,2026-07-27,5,pieces,114,118,2026-07-28,2026-08-01,634.0,539.0,95.0,101.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",114,2026-07-28,5,pieces,115,119,2026-07-29,2026-08-02,770.0,583.0,187.0,193.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",115,2026-07-29,5,pieces,116,120,2026-07-30,2026-08-03,857.0,578.0,279.0,281.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",116,2026-07-30,5,pieces,117,121,2026-07-31,2026-08-04,851.0,575.0,276.0,278.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",117,2026-07-31,5,pieces,118,122,2026-08-01,2026-08-05,830.0,551.0,279.0,279.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",118,2026-08-01,5,pieces,119,123,2026-08-02,2026-08-06,690.0,502.0,188.0,188.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",119,2026-08-02,5,pieces,120,124,2026-08-03,2026-08-07,578.0,484.0,94.0,94.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",120,2026-08-03,5,pieces,121,125,2026-08-04,2026-08-08,546.0,634.0,-88.0,96.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",121,2026-08-04,5,pieces,122,126,2026-08-05,2026-08-09,591.0,770.0,-179.0,187.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",122,2026-08-05,5,pieces,123,127,2026-08-06,2026-08-10,589.0,857.0,-268.0,272.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",123,2026-08-06,5,pieces,124,128,2026-08-07,2026-08-11,585.0,851.0,-266.0,274.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",124,2026-08-07,5,pieces,125,129,2026-08-08,2026-08-12,563.0,830.0,-267.0,275.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",125,2026-08-08,5,pieces,126,130,2026-08-09,2026-08-13,512.0,690.0,-178.0,186.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",126,2026-08-09,5,pieces,127,131,2026-08-10,2026-08-14,496.0,578.0,-82.0,100.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",127,2026-08-10,5,pieces,128,132,2026-08-11,2026-08-15,555.0,546.0,9.0,17.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",128,2026-08-11,5,pieces,129,133,2026-08-12,2026-08-16,598.0,591.0,7.0,15.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",129,2026-08-12,5,pieces,130,134,2026-08-13,2026-08-17,596.0,589.0,7.0,15.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",130,2026-08-13,5,pieces,131,135,2026-08-14,2026-08-18,596.0,585.0,11.0,13.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",131,2026-08-14,5,pieces,132,136,2026-08-15,2026-08-19,570.0,563.0,7.0,9.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",132,2026-08-15,5,pieces,133,137,2026-08-16,2026-08-20,513.0,512.0,1.0,7.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",133,2026-08-16,5,pieces,134,138,2026-08-17,2026-08-21,496.0,496.0,0.0,6.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",134,2026-08-17,5,pieces,135,139,2026-08-18,2026-08-22,551.0,555.0,-4.0,10.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SNaive7,"{""method"":""seasonal_naive_7""}",135,2026-08-18,5,pieces,136,140,2026-08-19,2026-08-23,591.0,598.0,-7.0,11.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",112,2026-07-26,1,pieces/day,113,113,2026-07-27,2026-07-27,89.0,131.66666666666666,-42.66666666666666,42.66666666666666
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",113,2026-07-27,1,pieces/day,114,114,2026-07-28,2026-07-28,91.0,122.66666666666667,-31.66666666666667,31.66666666666667
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",114,2026-07-28,1,pieces/day,115,115,2026-07-29,2026-07-29,92.0,104.33333333333333,-12.333333333333329,12.333333333333329
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",115,2026-07-29,1,pieces/day,116,116,2026-07-30,2026-07-30,97.0,90.66666666666667,6.333333333333329,6.333333333333329
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",116,2026-07-30,1,pieces/day,117,117,2026-07-31,2026-07-31,115.0,93.33333333333333,21.66666666666667,21.66666666666667
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",117,2026-07-31,1,pieces/day,118,118,2026-08-01,2026-08-01,239.0,101.33333333333333,137.66666666666669,137.66666666666669
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",118,2026-08-01,1,pieces/day,119,119,2026-08-02,2026-08-02,227.0,150.33333333333334,76.66666666666666,76.66666666666666
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",119,2026-08-02,1,pieces/day,120,120,2026-08-03,2026-08-03,179.0,193.66666666666666,-14.666666666666657,14.666666666666657
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",120,2026-08-03,1,pieces/day,121,121,2026-08-04,2026-08-04,91.0,215.0,-124.0,124.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",121,2026-08-04,1,pieces/day,122,122,2026-08-05,2026-08-05,94.0,165.66666666666666,-71.66666666666666,71.66666666666666
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",122,2026-08-05,1,pieces/day,123,123,2026-08-06,2026-08-06,99.0,121.33333333333333,-22.33333333333333,22.33333333333333
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",123,2026-08-06,1,pieces/day,124,124,2026-08-07,2026-08-07,115.0,94.66666666666667,20.33333333333333,20.33333333333333
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",124,2026-08-07,1,pieces/day,125,125,2026-08-08,2026-08-08,147.0,102.66666666666667,44.33333333333333,44.33333333333333
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",125,2026-08-08,1,pieces/day,126,126,2026-08-09,2026-08-09,136.0,120.33333333333333,15.666666666666671,15.666666666666671
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",126,2026-08-09,1,pieces/day,127,127,2026-08-10,2026-08-10,92.0,132.66666666666666,-40.66666666666666,40.66666666666666
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",127,2026-08-10,1,pieces/day,128,128,2026-08-11,2026-08-11,95.0,125.0,-30.0,30.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",128,2026-08-11,1,pieces/day,129,129,2026-08-12,2026-08-12,93.0,107.66666666666667,-14.666666666666671,14.666666666666671
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",129,2026-08-12,1,pieces/day,130,130,2026-08-13,2026-08-13,96.0,93.33333333333333,2.6666666666666714,2.6666666666666714
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",130,2026-08-13,1,pieces/day,131,131,2026-08-14,2026-08-14,120.0,94.66666666666667,25.33333333333333,25.33333333333333
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",131,2026-08-14,1,pieces/day,132,132,2026-08-15,2026-08-15,151.0,103.0,48.0,48.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",132,2026-08-15,1,pieces/day,133,133,2026-08-16,2026-08-16,138.0,122.33333333333333,15.666666666666671,15.666666666666671
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",133,2026-08-16,1,pieces/day,134,134,2026-08-17,2026-08-17,91.0,136.33333333333334,-45.33333333333334,45.33333333333334
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",134,2026-08-17,1,pieces/day,135,135,2026-08-18,2026-08-18,96.0,126.66666666666667,-30.66666666666667,30.66666666666667
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",135,2026-08-18,1,pieces/day,136,136,2026-08-19,2026-08-19,94.0,108.33333333333333,-14.333333333333329,14.333333333333329
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",136,2026-08-19,1,pieces/day,137,137,2026-08-20,2026-08-20,94.0,93.66666666666667,0.3333333333333286,0.3333333333333286
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",137,2026-08-20,1,pieces/day,138,138,2026-08-21,2026-08-21,121.0,94.66666666666667,26.33333333333333,26.33333333333333
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",138,2026-08-21,1,pieces/day,139,139,2026-08-22,2026-08-22,146.0,103.0,43.0,43.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",139,2026-08-22,1,pieces/day,140,140,2026-08-23,2026-08-23,136.0,120.33333333333333,15.666666666666671,15.666666666666671
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",112,2026-07-26,5,pieces,113,117,2026-07-27,2026-07-31,484.0,658.3333333333333,-174.33333333333326,174.3333333333333
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",113,2026-07-27,5,pieces,114,118,2026-07-28,2026-08-01,634.0,613.3333333333334,20.66666666666663,212.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",114,2026-07-28,5,pieces,115,119,2026-07-29,2026-08-02,770.0,521.6666666666666,248.33333333333337,287.6666666666667
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",115,2026-07-29,5,pieces,116,120,2026-07-30,2026-08-03,857.0,453.33333333333337,403.66666666666663,403.66666666666663
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",116,2026-07-30,5,pieces,117,121,2026-07-31,2026-08-04,851.0,466.66666666666663,384.33333333333337,389.00000000000006
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",117,2026-07-31,5,pieces,118,122,2026-08-01,2026-08-05,830.0,506.66666666666663,323.33333333333337,358.6666666666667
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",118,2026-08-01,5,pieces,119,123,2026-08-02,2026-08-06,690.0,751.6666666666667,-61.66666666666674,272.33333333333337
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",119,2026-08-02,5,pieces,120,124,2026-08-03,2026-08-07,578.0,968.3333333333333,-390.33333333333326,390.33333333333326
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",120,2026-08-03,5,pieces,121,125,2026-08-04,2026-08-08,546.0,1075.0,-529.0,529.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",121,2026-08-04,5,pieces,122,126,2026-08-05,2026-08-09,591.0,828.3333333333333,-237.33333333333326,237.3333333333333
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",122,2026-08-05,5,pieces,123,127,2026-08-06,2026-08-10,589.0,606.6666666666666,-17.66666666666663,98.33333333333333
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",123,2026-08-06,5,pieces,124,128,2026-08-07,2026-08-11,585.0,473.33333333333337,111.66666666666663,116.99999999999999
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",124,2026-08-07,5,pieces,125,129,2026-08-08,2026-08-12,563.0,513.3333333333334,49.66666666666663,105.66666666666667
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",125,2026-08-08,5,pieces,126,130,2026-08-09,2026-08-13,512.0,601.6666666666666,-89.66666666666663,120.99999999999999
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",126,2026-08-09,5,pieces,127,131,2026-08-10,2026-08-14,496.0,663.3333333333333,-167.33333333333326,167.3333333333333
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",127,2026-08-10,5,pieces,128,132,2026-08-11,2026-08-15,555.0,625.0,-70.0,122.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",128,2026-08-11,5,pieces,129,133,2026-08-12,2026-08-16,598.0,538.3333333333334,59.66666666666663,112.33333333333333
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",129,2026-08-12,5,pieces,130,134,2026-08-13,2026-08-17,596.0,466.66666666666663,129.33333333333337,134.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",130,2026-08-13,5,pieces,131,135,2026-08-14,2026-08-18,596.0,473.33333333333337,122.66666666666663,130.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",131,2026-08-14,5,pieces,132,136,2026-08-15,2026-08-19,570.0,515.0,55.0,111.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",132,2026-08-15,5,pieces,133,137,2026-08-16,2026-08-20,513.0,611.6666666666666,-98.66666666666663,130.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",133,2026-08-16,5,pieces,134,138,2026-08-17,2026-08-21,496.0,681.6666666666667,-185.66666666666674,185.6666666666667
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",134,2026-08-17,5,pieces,135,139,2026-08-18,2026-08-22,551.0,633.3333333333334,-82.33333333333337,121.00000000000001
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA3,"{""k"":3,""method"":""moving_average""}",135,2026-08-18,5,pieces,136,140,2026-08-19,2026-08-23,591.0,541.6666666666666,49.33333333333337,106.66666666666667
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",112,2026-07-26,1,pieces/day,113,113,2026-07-27,2026-07-27,89.0,108.71428571428571,-19.714285714285708,19.714285714285708
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",113,2026-07-27,1,pieces/day,114,114,2026-07-28,2026-07-28,91.0,108.71428571428571,-17.714285714285708,17.714285714285708
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",114,2026-07-28,1,pieces/day,115,115,2026-07-29,2026-07-29,92.0,109.0,-17.0,17.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",115,2026-07-29,1,pieces/day,116,116,2026-07-30,2026-07-30,97.0,108.71428571428571,-11.714285714285708,11.714285714285708
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",116,2026-07-30,1,pieces/day,117,117,2026-07-31,2026-07-31,115.0,109.14285714285714,5.857142857142861,5.857142857142861
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",117,2026-07-31,1,pieces/day,118,118,2026-08-01,2026-08-01,239.0,109.0,130.0,130.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",118,2026-08-01,1,pieces/day,119,119,2026-08-02,2026-08-02,227.0,122.28571428571429,104.71428571428571,104.71428571428571
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",119,2026-08-02,1,pieces/day,120,120,2026-08-03,2026-08-03,179.0,135.71428571428572,43.28571428571428,43.28571428571428
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",120,2026-08-03,1,pieces/day,121,121,2026-08-04,2026-08-04,91.0,148.57142857142858,-57.571428571428584,57.571428571428584
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",121,2026-08-04,1,pieces/day,122,122,2026-08-05,2026-08-05,94.0,148.57142857142858,-54.571428571428584,54.571428571428584
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",122,2026-08-05,1,pieces/day,123,123,2026-08-06,2026-08-06,99.0,148.85714285714286,-49.85714285714286,49.85714285714286
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",123,2026-08-06,1,pieces/day,124,124,2026-08-07,2026-08-07,115.0,149.14285714285714,-34.14285714285714,34.14285714285714
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",124,2026-08-07,1,pieces/day,125,125,2026-08-08,2026-08-08,147.0,149.14285714285714,-2.142857142857139,2.142857142857139
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",125,2026-08-08,1,pieces/day,126,126,2026-08-09,2026-08-09,136.0,136.0,0.0,0.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",126,2026-08-09,1,pieces/day,127,127,2026-08-10,2026-08-10,92.0,123.0,-31.0,31.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",127,2026-08-10,1,pieces/day,128,128,2026-08-11,2026-08-11,95.0,110.57142857142857,-15.57142857142857,15.57142857142857
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",128,2026-08-11,1,pieces/day,129,129,2026-08-12,2026-08-12,93.0,111.14285714285714,-18.14285714285714,18.14285714285714
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",129,2026-08-12,1,pieces/day,130,130,2026-08-13,2026-08-13,96.0,111.0,-15.0,15.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",130,2026-08-13,1,pieces/day,131,131,2026-08-14,2026-08-14,120.0,110.57142857142857,9.42857142857143,9.42857142857143
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",131,2026-08-14,1,pieces/day,132,132,2026-08-15,2026-08-15,151.0,111.28571428571429,39.71428571428571,39.71428571428571
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",132,2026-08-15,1,pieces/day,133,133,2026-08-16,2026-08-16,138.0,111.85714285714286,26.14285714285714,26.14285714285714
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",133,2026-08-16,1,pieces/day,134,134,2026-08-17,2026-08-17,91.0,112.14285714285714,-21.14285714285714,21.14285714285714
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",134,2026-08-17,1,pieces/day,135,135,2026-08-18,2026-08-18,96.0,112.0,-16.0,16.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",135,2026-08-18,1,pieces/day,136,136,2026-08-19,2026-08-19,94.0,112.14285714285714,-18.14285714285714,18.14285714285714
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",136,2026-08-19,1,pieces/day,137,137,2026-08-20,2026-08-20,94.0,112.28571428571429,-18.285714285714292,18.285714285714292
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",137,2026-08-20,1,pieces/day,138,138,2026-08-21,2026-08-21,121.0,112.0,9.0,9.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",138,2026-08-21,1,pieces/day,139,139,2026-08-22,2026-08-22,146.0,112.14285714285714,33.85714285714286,33.85714285714286
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",139,2026-08-22,1,pieces/day,140,140,2026-08-23,2026-08-23,136.0,111.42857142857143,24.57142857142857,24.57142857142857
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",112,2026-07-26,5,pieces,113,117,2026-07-27,2026-07-31,484.0,543.5714285714286,-59.571428571428555,72.14285714285712
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",113,2026-07-27,5,pieces,114,118,2026-07-28,2026-08-01,634.0,543.5714285714286,90.42857142857144,182.7142857142857
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",114,2026-07-28,5,pieces,115,119,2026-07-29,2026-08-02,770.0,545.0,225.0,283.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",115,2026-07-29,5,pieces,116,120,2026-07-30,2026-08-03,857.0,543.5714285714286,313.42857142857144,336.8571428571429
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",116,2026-07-30,5,pieces,117,121,2026-07-31,2026-08-04,851.0,545.7142857142857,305.28571428571433,341.57142857142856
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",117,2026-07-31,5,pieces,118,122,2026-08-01,2026-08-05,830.0,545.0,285.0,351.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",118,2026-08-01,5,pieces,119,123,2026-08-02,2026-08-06,690.0,611.4285714285714,78.57142857142856,244.28571428571428
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",119,2026-08-02,5,pieces,120,124,2026-08-03,2026-08-07,578.0,678.5714285714287,-100.57142857142867,187.14285714285717
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",120,2026-08-03,5,pieces,121,125,2026-08-04,2026-08-08,546.0,742.8571428571429,-196.8571428571429,196.85714285714292
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",121,2026-08-04,5,pieces,122,126,2026-08-05,2026-08-09,591.0,742.8571428571429,-151.8571428571429,151.85714285714292
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",122,2026-08-05,5,pieces,123,127,2026-08-06,2026-08-10,589.0,744.2857142857143,-155.28571428571433,155.2857142857143
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",123,2026-08-06,5,pieces,124,128,2026-08-07,2026-08-11,585.0,745.7142857142857,-160.71428571428567,160.7142857142857
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",124,2026-08-07,5,pieces,125,129,2026-08-08,2026-08-12,563.0,745.7142857142857,-182.71428571428567,182.7142857142857
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",125,2026-08-08,5,pieces,126,130,2026-08-09,2026-08-13,512.0,680.0,-168.0,168.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",126,2026-08-09,5,pieces,127,131,2026-08-10,2026-08-14,496.0,615.0,-119.0,119.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",127,2026-08-10,5,pieces,128,132,2026-08-11,2026-08-15,555.0,552.8571428571429,2.1428571428571104,97.57142857142857
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",128,2026-08-11,5,pieces,129,133,2026-08-12,2026-08-16,598.0,555.7142857142857,42.285714285714334,108.85714285714286
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",129,2026-08-12,5,pieces,130,134,2026-08-13,2026-08-17,596.0,555.0,41.0,111.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",130,2026-08-13,5,pieces,131,135,2026-08-14,2026-08-18,596.0,552.8571428571429,43.14285714285711,111.42857142857143
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",131,2026-08-14,5,pieces,132,136,2026-08-15,2026-08-19,570.0,556.4285714285714,13.571428571428555,119.28571428571429
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",132,2026-08-15,5,pieces,133,137,2026-08-16,2026-08-20,513.0,559.2857142857143,-46.285714285714334,98.57142857142858
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",133,2026-08-16,5,pieces,134,138,2026-08-17,2026-08-21,496.0,560.7142857142857,-64.71428571428567,82.42857142857142
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",134,2026-08-17,5,pieces,135,139,2026-08-18,2026-08-22,551.0,560.0,-9.0,95.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA7,"{""k"":7,""method"":""moving_average""}",135,2026-08-18,5,pieces,136,140,2026-08-19,2026-08-23,591.0,560.7142857142857,30.285714285714334,102.85714285714286
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",112,2026-07-26,1,pieces/day,113,113,2026-07-27,2026-07-27,89.0,108.64285714285714,-19.64285714285714,19.64285714285714
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",113,2026-07-27,1,pieces/day,114,114,2026-07-28,2026-07-28,91.0,109.0,-18.0,18.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",114,2026-07-28,1,pieces/day,115,115,2026-07-29,2026-07-29,92.0,109.21428571428571,-17.214285714285708,17.214285714285708
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",115,2026-07-29,1,pieces/day,116,116,2026-07-30,2026-07-30,97.0,108.92857142857143,-11.92857142857143,11.92857142857143
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",116,2026-07-30,1,pieces/day,117,117,2026-07-31,2026-07-31,115.0,108.85714285714286,6.142857142857139,6.142857142857139
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",117,2026-07-31,1,pieces/day,118,118,2026-08-01,2026-08-01,239.0,108.5,130.5,130.5
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",118,2026-08-01,1,pieces/day,119,119,2026-08-02,2026-08-02,227.0,115.28571428571429,111.71428571428571,111.71428571428571
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",119,2026-08-02,1,pieces/day,120,120,2026-08-03,2026-08-03,179.0,122.21428571428571,56.78571428571429,56.78571428571429
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",120,2026-08-03,1,pieces/day,121,121,2026-08-04,2026-08-04,91.0,128.64285714285714,-37.64285714285714,37.64285714285714
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",121,2026-08-04,1,pieces/day,122,122,2026-08-05,2026-08-05,94.0,128.78571428571428,-34.78571428571428,34.78571428571428
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",122,2026-08-05,1,pieces/day,123,123,2026-08-06,2026-08-06,99.0,128.78571428571428,-29.785714285714278,29.785714285714278
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",123,2026-08-06,1,pieces/day,124,124,2026-08-07,2026-08-07,115.0,129.14285714285714,-14.142857142857139,14.142857142857139
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",124,2026-08-07,1,pieces/day,125,125,2026-08-08,2026-08-08,147.0,129.07142857142858,17.928571428571416,17.928571428571416
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",125,2026-08-08,1,pieces/day,126,126,2026-08-09,2026-08-09,136.0,129.14285714285714,6.857142857142861,6.857142857142861
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",126,2026-08-09,1,pieces/day,127,127,2026-08-10,2026-08-10,92.0,129.35714285714286,-37.35714285714286,37.35714285714286
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",127,2026-08-10,1,pieces/day,128,128,2026-08-11,2026-08-11,95.0,129.57142857142858,-34.571428571428584,34.571428571428584
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",128,2026-08-11,1,pieces/day,129,129,2026-08-12,2026-08-12,93.0,129.85714285714286,-36.85714285714286,36.85714285714286
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",129,2026-08-12,1,pieces/day,130,130,2026-08-13,2026-08-13,96.0,129.92857142857142,-33.928571428571416,33.928571428571416
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",130,2026-08-13,1,pieces/day,131,131,2026-08-14,2026-08-14,120.0,129.85714285714286,-9.857142857142861,9.857142857142861
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",131,2026-08-14,1,pieces/day,132,132,2026-08-15,2026-08-15,151.0,130.21428571428572,20.785714285714278,20.785714285714278
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",132,2026-08-15,1,pieces/day,133,133,2026-08-16,2026-08-16,138.0,123.92857142857143,14.07142857142857,14.07142857142857
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",133,2026-08-16,1,pieces/day,134,134,2026-08-17,2026-08-17,91.0,117.57142857142857,-26.57142857142857,26.57142857142857
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",134,2026-08-17,1,pieces/day,135,135,2026-08-18,2026-08-18,96.0,111.28571428571429,-15.285714285714292,15.285714285714292
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",135,2026-08-18,1,pieces/day,136,136,2026-08-19,2026-08-19,94.0,111.64285714285714,-17.64285714285714,17.64285714285714
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",136,2026-08-19,1,pieces/day,137,137,2026-08-20,2026-08-20,94.0,111.64285714285714,-17.64285714285714,17.64285714285714
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",137,2026-08-20,1,pieces/day,138,138,2026-08-21,2026-08-21,121.0,111.28571428571429,9.714285714285708,9.714285714285708
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",138,2026-08-21,1,pieces/day,139,139,2026-08-22,2026-08-22,146.0,111.71428571428571,34.28571428571429,34.28571428571429
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",139,2026-08-22,1,pieces/day,140,140,2026-08-23,2026-08-23,136.0,111.64285714285714,24.35714285714286,24.35714285714286
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",112,2026-07-26,5,pieces,113,117,2026-07-27,2026-07-31,484.0,543.2142857142857,-59.214285714285666,71.92857142857142
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",113,2026-07-27,5,pieces,114,118,2026-07-28,2026-08-01,634.0,545.0,89.0,183.0
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",114,2026-07-28,5,pieces,115,119,2026-07-29,2026-08-02,770.0,546.0714285714286,223.92857142857144,282.7857142857143
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",115,2026-07-29,5,pieces,116,120,2026-07-30,2026-08-03,857.0,544.6428571428571,312.3571428571429,336.21428571428567
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",116,2026-07-30,5,pieces,117,121,2026-07-31,2026-08-04,851.0,544.2857142857143,306.71428571428567,342.42857142857144
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",117,2026-07-31,5,pieces,118,122,2026-08-01,2026-08-05,830.0,542.5,287.5,351.5
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",118,2026-08-01,5,pieces,119,123,2026-08-02,2026-08-06,690.0,576.4285714285714,113.57142857142856,237.28571428571428
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",119,2026-08-02,5,pieces,120,124,2026-08-03,2026-08-07,578.0,611.0714285714286,-33.071428571428555,146.6428571428571
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",120,2026-08-03,5,pieces,121,125,2026-08-04,2026-08-08,546.0,643.2142857142857,-97.21428571428567,133.92857142857142
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",121,2026-08-04,5,pieces,122,126,2026-08-05,2026-08-09,591.0,643.9285714285713,-52.92857142857133,103.78571428571428
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",122,2026-08-05,5,pieces,123,127,2026-08-06,2026-08-10,589.0,643.9285714285713,-54.92857142857133,105.78571428571428
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",123,2026-08-06,5,pieces,124,128,2026-08-07,2026-08-11,585.0,645.7142857142857,-60.714285714285666,110.14285714285714
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",124,2026-08-07,5,pieces,125,129,2026-08-08,2026-08-12,563.0,645.3571428571429,-82.35714285714289,132.07142857142858
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",125,2026-08-08,5,pieces,126,130,2026-08-09,2026-08-13,512.0,645.7142857142857,-133.71428571428567,147.42857142857142
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",126,2026-08-09,5,pieces,127,131,2026-08-10,2026-08-14,496.0,646.7857142857143,-150.78571428571433,150.7857142857143
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",127,2026-08-10,5,pieces,128,132,2026-08-11,2026-08-15,555.0,647.8571428571429,-92.85714285714289,135.71428571428575
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",128,2026-08-11,5,pieces,129,133,2026-08-12,2026-08-16,598.0,649.2857142857143,-51.285714285714334,109.85714285714286
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",129,2026-08-12,5,pieces,130,134,2026-08-13,2026-08-17,596.0,649.6428571428571,-53.64285714285711,111.92857142857142
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",130,2026-08-13,5,pieces,131,135,2026-08-14,2026-08-18,596.0,649.2857142857143,-53.285714285714334,111.85714285714286
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",131,2026-08-14,5,pieces,132,136,2026-08-15,2026-08-19,570.0,651.0714285714287,-81.07142857142867,138.21428571428572
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",132,2026-08-15,5,pieces,133,137,2026-08-16,2026-08-20,513.0,619.6428571428571,-106.64285714285711,134.78571428571428
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",133,2026-08-16,5,pieces,134,138,2026-08-17,2026-08-21,496.0,587.8571428571429,-91.85714285714289,98.71428571428571
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",134,2026-08-17,5,pieces,135,139,2026-08-18,2026-08-22,551.0,556.4285714285714,-5.428571428571445,94.28571428571429
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,MA14,"{""k"":14,""method"":""moving_average""}",135,2026-08-18,5,pieces,136,140,2026-08-19,2026-08-23,591.0,558.2142857142857,32.785714285714334,103.35714285714286
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",112,2026-07-26,1,pieces/day,113,113,2026-07-27,2026-07-27,89.0,117.13025108591563,-28.13025108591563,28.13025108591563
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",113,2026-07-27,1,pieces/day,114,114,2026-07-28,2026-07-28,91.0,111.50420086873251,-20.50420086873251,20.50420086873251
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",114,2026-07-28,1,pieces/day,115,115,2026-07-29,2026-07-29,92.0,107.40336069498602,-15.40336069498602,15.40336069498602
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",115,2026-07-29,1,pieces/day,116,116,2026-07-30,2026-07-30,97.0,104.32268855598883,-7.322688555988833,7.322688555988833
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",116,2026-07-30,1,pieces/day,117,117,2026-07-31,2026-07-31,115.0,102.85815084479108,12.141849155208916,12.141849155208916
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",117,2026-07-31,1,pieces/day,118,118,2026-08-01,2026-08-01,239.0,105.28652067583288,133.7134793241671,133.7134793241671
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",118,2026-08-01,1,pieces/day,119,119,2026-08-02,2026-08-02,227.0,132.0292165406663,94.97078345933369,94.97078345933369
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",119,2026-08-02,1,pieces/day,120,120,2026-08-03,2026-08-03,179.0,151.02337323253306,27.97662676746694,27.97662676746694
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",120,2026-08-03,1,pieces/day,121,121,2026-08-04,2026-08-04,91.0,156.61869858602645,-65.61869858602645,65.61869858602645
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",121,2026-08-04,1,pieces/day,122,122,2026-08-05,2026-08-05,94.0,143.49495886882116,-49.49495886882116,49.49495886882116
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",122,2026-08-05,1,pieces/day,123,123,2026-08-06,2026-08-06,99.0,133.59596709505695,-34.59596709505695,34.59596709505695
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",123,2026-08-06,1,pieces/day,124,124,2026-08-07,2026-08-07,115.0,126.67677367604556,-11.676773676045556,11.676773676045556
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",124,2026-08-07,1,pieces/day,125,125,2026-08-08,2026-08-08,147.0,124.34141894083645,22.658581059163552,22.658581059163552
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",125,2026-08-08,1,pieces/day,126,126,2026-08-09,2026-08-09,136.0,128.87313515266916,7.126864847330836,7.126864847330836
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",126,2026-08-09,1,pieces/day,127,127,2026-08-10,2026-08-10,92.0,130.29850812213533,-38.29850812213533,38.29850812213533
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",127,2026-08-10,1,pieces/day,128,128,2026-08-11,2026-08-11,95.0,122.63880649770827,-27.638806497708273,27.638806497708273
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",128,2026-08-11,1,pieces/day,129,129,2026-08-12,2026-08-12,93.0,117.11104519816662,-24.11104519816662,24.11104519816662
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",129,2026-08-12,1,pieces/day,130,130,2026-08-13,2026-08-13,96.0,112.28883615853331,-16.288836158533314,16.288836158533314
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",130,2026-08-13,1,pieces/day,131,131,2026-08-14,2026-08-14,120.0,109.03106892682666,10.968931073173337,10.968931073173337
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",131,2026-08-14,1,pieces/day,132,132,2026-08-15,2026-08-15,151.0,111.22485514146133,39.77514485853867,39.77514485853867
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",132,2026-08-15,1,pieces/day,133,133,2026-08-16,2026-08-16,138.0,119.17988411316908,18.82011588683092,18.82011588683092
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",133,2026-08-16,1,pieces/day,134,134,2026-08-17,2026-08-17,91.0,122.94390729053526,-31.943907290535265,31.943907290535265
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",134,2026-08-17,1,pieces/day,135,135,2026-08-18,2026-08-18,96.0,116.55512583242822,-20.555125832428217,20.555125832428217
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",135,2026-08-18,1,pieces/day,136,136,2026-08-19,2026-08-19,94.0,112.44410066594259,-18.444100665942585,18.444100665942585
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",136,2026-08-19,1,pieces/day,137,137,2026-08-20,2026-08-20,94.0,108.75528053275407,-14.755280532754071,14.755280532754071
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",137,2026-08-20,1,pieces/day,138,138,2026-08-21,2026-08-21,121.0,105.80422442620326,15.195775573796737,15.195775573796737
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",138,2026-08-21,1,pieces/day,139,139,2026-08-22,2026-08-22,146.0,108.84337954096262,37.156620459037384,37.156620459037384
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",139,2026-08-22,1,pieces/day,140,140,2026-08-23,2026-08-23,136.0,116.2747036327701,19.7252963672299,19.7252963672299
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",112,2026-07-26,5,pieces,113,117,2026-07-27,2026-07-31,484.0,585.6512554295782,-101.65125542957821,101.65125542957816
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",113,2026-07-27,5,pieces,114,118,2026-07-28,2026-08-01,634.0,557.5210043436625,76.47899565633747,185.5042008687325
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",114,2026-07-28,5,pieces,115,119,2026-07-29,2026-08-02,770.0,537.0168034749302,232.98319652506984,284.596639305014
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",115,2026-07-29,5,pieces,116,120,2026-07-30,2026-08-03,857.0,521.6134427799442,335.3865572200558,350.03193433203353
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",116,2026-07-30,5,pieces,117,121,2026-07-31,2026-08-04,851.0,514.2907542239554,336.70924577604455,360.4255474656268
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",117,2026-07-31,5,pieces,118,122,2026-08-01,2026-08-05,830.0,526.4326033791643,303.56739662083567,354.7134793241671
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",118,2026-08-01,5,pieces,119,123,2026-08-02,2026-08-06,690.0,660.1460827033316,29.853917296668442,254.0292165406663
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",119,2026-08-02,5,pieces,120,124,2026-08-03,2026-08-07,578.0,755.1168661626652,-177.11686616266525,233.07011969759918
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",120,2026-08-03,5,pieces,121,125,2026-08-04,2026-08-08,546.0,783.0934929301322,-237.09349293013224,237.09349293013227
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",121,2026-08-04,5,pieces,122,126,2026-08-05,2026-08-09,591.0,717.4747943441058,-126.47479434410582,133.48487660646347
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",122,2026-08-05,5,pieces,123,127,2026-08-06,2026-08-10,589.0,667.9798354752847,-78.97983547528474,110.59596709505695
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",123,2026-08-06,5,pieces,124,128,2026-08-07,2026-08-11,585.0,633.3838683802278,-48.383868380227796,107.67677367604556
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",124,2026-08-07,5,pieces,125,129,2026-08-08,2026-08-12,563.0,621.7070947041823,-58.70709470418228,127.34141894083645
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",125,2026-08-08,5,pieces,126,130,2026-08-09,2026-08-13,512.0,644.3656757633458,-132.36567576334585,146.6194054580075
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",126,2026-08-09,5,pieces,127,131,2026-08-10,2026-08-14,496.0,651.4925406106767,-155.49254061067666,155.49254061067666
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",127,2026-08-10,5,pieces,128,132,2026-08-11,2026-08-15,555.0,613.1940324885413,-58.194032488541325,114.91641949312482
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",128,2026-08-11,5,pieces,129,133,2026-08-12,2026-08-16,598.0,585.5552259908332,12.44477400916685,102.88895480183338
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",129,2026-08-12,5,pieces,130,134,2026-08-13,2026-08-17,596.0,561.4441807926665,34.55581920733346,109.71116384146669
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",130,2026-08-13,5,pieces,131,135,2026-08-14,2026-08-18,596.0,545.1553446341334,50.84465536586663,112.96893107317334
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",131,2026-08-14,5,pieces,132,136,2026-08-15,2026-08-19,570.0,556.1242757073067,13.875724292693349,119.22485514146133
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",132,2026-08-15,5,pieces,133,137,2026-08-16,2026-08-20,513.0,595.8994205658454,-82.89942056584539,120.53965233950724
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",133,2026-08-16,5,pieces,134,138,2026-08-17,2026-08-21,496.0,614.7195364526763,-118.71953645267627,118.71953645267632
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",134,2026-08-17,5,pieces,135,139,2026-08-18,2026-08-22,551.0,582.7756291621411,-31.77562916214106,99.55512583242822
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.2,"{""alpha"":0.2,""method"":""ses""}",135,2026-08-18,5,pieces,136,140,2026-08-19,2026-08-23,591.0,562.220503329713,28.779496670287017,102.55589933405741
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",112,2026-07-26,1,pieces/day,113,113,2026-07-27,2026-07-27,89.0,129.39969893565262,-40.39969893565262,40.39969893565262
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",113,2026-07-27,1,pieces/day,114,114,2026-07-28,2026-07-28,91.0,109.19984946782631,-18.19984946782631,18.19984946782631
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",114,2026-07-28,1,pieces/day,115,115,2026-07-29,2026-07-29,92.0,100.09992473391316,-8.099924733913156,8.099924733913156
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",115,2026-07-29,1,pieces/day,116,116,2026-07-30,2026-07-30,97.0,96.04996236695658,0.9500376330434221,0.9500376330434221
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",116,2026-07-30,1,pieces/day,117,117,2026-07-31,2026-07-31,115.0,96.52498118347829,18.47501881652171,18.47501881652171
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",117,2026-07-31,1,pieces/day,118,118,2026-08-01,2026-08-01,239.0,105.76249059173915,133.23750940826085,133.23750940826085
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",118,2026-08-01,1,pieces/day,119,119,2026-08-02,2026-08-02,227.0,172.38124529586958,54.618754704130424,54.618754704130424
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",119,2026-08-02,1,pieces/day,120,120,2026-08-03,2026-08-03,179.0,199.6906226479348,-20.690622647934788,20.690622647934788
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",120,2026-08-03,1,pieces/day,121,121,2026-08-04,2026-08-04,91.0,189.3453113239674,-98.3453113239674,98.3453113239674
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",121,2026-08-04,1,pieces/day,122,122,2026-08-05,2026-08-05,94.0,140.1726556619837,-46.1726556619837,46.1726556619837
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",122,2026-08-05,1,pieces/day,123,123,2026-08-06,2026-08-06,99.0,117.08632783099185,-18.08632783099185,18.08632783099185
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",123,2026-08-06,1,pieces/day,124,124,2026-08-07,2026-08-07,115.0,108.04316391549592,6.956836084504076,6.956836084504076
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",124,2026-08-07,1,pieces/day,125,125,2026-08-08,2026-08-08,147.0,111.52158195774797,35.47841804225203,35.47841804225203
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",125,2026-08-08,1,pieces/day,126,126,2026-08-09,2026-08-09,136.0,129.26079097887398,6.739209021126015,6.739209021126015
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",126,2026-08-09,1,pieces/day,127,127,2026-08-10,2026-08-10,92.0,132.63039548943698,-40.63039548943698,40.63039548943698
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",127,2026-08-10,1,pieces/day,128,128,2026-08-11,2026-08-11,95.0,112.31519774471849,-17.31519774471849,17.31519774471849
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",128,2026-08-11,1,pieces/day,129,129,2026-08-12,2026-08-12,93.0,103.65759887235924,-10.657598872359245,10.657598872359245
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",129,2026-08-12,1,pieces/day,130,130,2026-08-13,2026-08-13,96.0,98.32879943617962,-2.3287994361796223,2.3287994361796223
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",130,2026-08-13,1,pieces/day,131,131,2026-08-14,2026-08-14,120.0,97.16439971808981,22.83560028191019,22.83560028191019
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",131,2026-08-14,1,pieces/day,132,132,2026-08-15,2026-08-15,151.0,108.5821998590449,42.417800140955094,42.417800140955094
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",132,2026-08-15,1,pieces/day,133,133,2026-08-16,2026-08-16,138.0,129.79109992952246,8.20890007047754,8.20890007047754
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",133,2026-08-16,1,pieces/day,134,134,2026-08-17,2026-08-17,91.0,133.89554996476124,-42.895549964761244,42.895549964761244
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",134,2026-08-17,1,pieces/day,135,135,2026-08-18,2026-08-18,96.0,112.44777498238062,-16.447774982380622,16.447774982380622
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",135,2026-08-18,1,pieces/day,136,136,2026-08-19,2026-08-19,94.0,104.22388749119031,-10.223887491190311,10.223887491190311
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",136,2026-08-19,1,pieces/day,137,137,2026-08-20,2026-08-20,94.0,99.11194374559516,-5.1119437455951555,5.1119437455951555
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",137,2026-08-20,1,pieces/day,138,138,2026-08-21,2026-08-21,121.0,96.55597187279758,24.444028127202415,24.444028127202415
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",138,2026-08-21,1,pieces/day,139,139,2026-08-22,2026-08-22,146.0,108.77798593639879,37.22201406360121,37.22201406360121
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",139,2026-08-22,1,pieces/day,140,140,2026-08-23,2026-08-23,136.0,127.3889929681994,8.611007031800597,8.611007031800597
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",112,2026-07-26,5,pieces,113,117,2026-07-27,2026-07-31,484.0,646.9984946782631,-162.9984946782631,162.9984946782631
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",113,2026-07-27,5,pieces,114,118,2026-07-28,2026-08-01,634.0,545.9992473391316,88.00075266086844,183.1998494678263
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",114,2026-07-28,5,pieces,115,119,2026-07-29,2026-08-02,770.0,500.4996236695658,269.5003763304342,291.90007526608684
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",115,2026-07-29,5,pieces,116,120,2026-07-30,2026-08-03,857.0,480.2498118347829,376.7501881652171,376.7501881652171
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",116,2026-07-30,5,pieces,117,121,2026-07-31,2026-08-04,851.0,482.62490591739146,368.37509408260854,379.4250564495651
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",117,2026-07-31,5,pieces,118,122,2026-08-01,2026-08-05,830.0,528.8124529586958,301.18754704130424,354.23750940826085
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",118,2026-08-01,5,pieces,119,123,2026-08-02,2026-08-06,690.0,861.9062264793479,-171.90622647934788,294.3812452958696
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",119,2026-08-02,5,pieces,120,124,2026-08-03,2026-08-07,578.0,998.4531132396739,-420.45311323967394,420.45311323967394
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",120,2026-08-03,5,pieces,121,125,2026-08-04,2026-08-08,546.0,946.726556619837,-400.72655661983697,400.72655661983697
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",121,2026-08-04,5,pieces,122,126,2026-08-05,2026-08-09,591.0,700.8632783099185,-109.86327830991854,123.51796698595109
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",122,2026-08-05,5,pieces,123,127,2026-08-06,2026-08-10,589.0,585.4316391549593,3.568360845040729,94.08632783099185
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",123,2026-08-06,5,pieces,124,128,2026-08-07,2026-08-11,585.0,540.2158195774796,44.78418042252042,102.95683608450408
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",124,2026-08-07,5,pieces,125,129,2026-08-08,2026-08-12,563.0,557.6079097887398,5.392090211260211,114.52158195774797
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",125,2026-08-08,5,pieces,126,130,2026-08-09,2026-08-13,512.0,646.3039548943699,-134.3039548943699,147.78237293662195
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",126,2026-08-09,5,pieces,127,131,2026-08-10,2026-08-14,496.0,663.1519774471849,-167.1519774471849,167.1519774471849
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",127,2026-08-10,5,pieces,128,132,2026-08-11,2026-08-15,555.0,561.5759887235924,-6.575988723592445,99.31519774471849
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",128,2026-08-11,5,pieces,129,133,2026-08-12,2026-08-16,598.0,518.2879943617962,79.71200563820378,116.34240112764076
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",129,2026-08-12,5,pieces,130,134,2026-08-13,2026-08-17,596.0,491.6439971808981,104.35600281910189,123.67120056382038
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",130,2026-08-13,5,pieces,131,135,2026-08-14,2026-08-18,596.0,485.8219985904491,110.17800140955092,124.83560028191019
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",131,2026-08-14,5,pieces,132,136,2026-08-15,2026-08-19,570.0,542.9109992952245,27.089000704775458,116.5821998590449
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",132,2026-08-15,5,pieces,133,137,2026-08-16,2026-08-20,513.0,648.9554996476123,-135.95549964761233,152.37329978856738
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",133,2026-08-16,5,pieces,134,138,2026-08-17,2026-08-21,496.0,669.4777498238062,-173.47774982380622,173.47774982380622
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",134,2026-08-17,5,pieces,135,139,2026-08-18,2026-08-22,551.0,562.2388749119032,-11.238874911903167,95.44777498238062
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.5,"{""alpha"":0.5,""method"":""ses""}",135,2026-08-18,5,pieces,136,140,2026-08-19,2026-08-23,591.0,521.1194374559516,69.88056254404842,110.77611250880969
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",112,2026-07-26,1,pieces/day,113,113,2026-07-27,2026-07-27,89.0,134.22294603035346,-45.222946030353455,45.222946030353455
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",113,2026-07-27,1,pieces/day,114,114,2026-07-28,2026-07-28,91.0,98.0445892060707,-7.044589206070697,7.044589206070697
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",114,2026-07-28,1,pieces/day,115,115,2026-07-29,2026-07-29,92.0,92.40891784121413,-0.40891784121413366,0.40891784121413366
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",115,2026-07-29,1,pieces/day,116,116,2026-07-30,2026-07-30,97.0,92.08178356824283,4.918216431757173,4.918216431757173
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",116,2026-07-30,1,pieces/day,117,117,2026-07-31,2026-07-31,115.0,96.01635671364858,18.983643286351423,18.983643286351423
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",117,2026-07-31,1,pieces/day,118,118,2026-08-01,2026-08-01,239.0,111.2032713427297,127.7967286572703,127.7967286572703
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",118,2026-08-01,1,pieces/day,119,119,2026-08-02,2026-08-02,227.0,213.44065426854596,13.559345731454044,13.559345731454044
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",119,2026-08-02,1,pieces/day,120,120,2026-08-03,2026-08-03,179.0,224.28813085370922,-45.28813085370922,45.28813085370922
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",120,2026-08-03,1,pieces/day,121,121,2026-08-04,2026-08-04,91.0,188.05762617074186,-97.05762617074186,97.05762617074186
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",121,2026-08-04,1,pieces/day,122,122,2026-08-05,2026-08-05,94.0,110.41152523414836,-16.411525234148357,16.411525234148357
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",122,2026-08-05,1,pieces/day,123,123,2026-08-06,2026-08-06,99.0,97.28230504682966,1.7176949531703372,1.7176949531703372
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",123,2026-08-06,1,pieces/day,124,124,2026-08-07,2026-08-07,115.0,98.65646100936593,16.343538990634073,16.343538990634073
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",124,2026-08-07,1,pieces/day,125,125,2026-08-08,2026-08-08,147.0,111.73129220187317,35.268707798126826,35.268707798126826
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",125,2026-08-08,1,pieces/day,126,126,2026-08-09,2026-08-09,136.0,139.94625844037463,-3.946258440374635,3.946258440374635
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",126,2026-08-09,1,pieces/day,127,127,2026-08-10,2026-08-10,92.0,136.78925168807493,-44.78925168807493,44.78925168807493
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",127,2026-08-10,1,pieces/day,128,128,2026-08-11,2026-08-11,95.0,100.95785033761499,-5.957850337614985,5.957850337614985
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",128,2026-08-11,1,pieces/day,129,129,2026-08-12,2026-08-12,93.0,96.19157006752299,-3.1915700675229886,3.1915700675229886
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",129,2026-08-12,1,pieces/day,130,130,2026-08-13,2026-08-13,96.0,93.6383140135046,2.3616859864954023,2.3616859864954023
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",130,2026-08-13,1,pieces/day,131,131,2026-08-14,2026-08-14,120.0,95.52766280270093,24.47233719729907,24.47233719729907
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",131,2026-08-14,1,pieces/day,132,132,2026-08-15,2026-08-15,151.0,115.10553256054018,35.89446743945982,35.89446743945982
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",132,2026-08-15,1,pieces/day,133,133,2026-08-16,2026-08-16,138.0,143.82110651210803,-5.821106512108031,5.821106512108031
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",133,2026-08-16,1,pieces/day,134,134,2026-08-17,2026-08-17,91.0,139.1642213024216,-48.164221302421595,48.164221302421595
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",134,2026-08-17,1,pieces/day,135,135,2026-08-18,2026-08-18,96.0,100.6328442604843,-4.632844260484305,4.632844260484305
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",135,2026-08-18,1,pieces/day,136,136,2026-08-19,2026-08-19,94.0,96.92656885209686,-2.926568852096864,2.926568852096864
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",136,2026-08-19,1,pieces/day,137,137,2026-08-20,2026-08-20,94.0,94.58531377041938,-0.5853137704193756,0.5853137704193756
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",137,2026-08-20,1,pieces/day,138,138,2026-08-21,2026-08-21,121.0,94.11706275408388,26.882937245916125,26.882937245916125
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",138,2026-08-21,1,pieces/day,139,139,2026-08-22,2026-08-22,146.0,115.62341255081678,30.37658744918322,30.37658744918322
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",139,2026-08-22,1,pieces/day,140,140,2026-08-23,2026-08-23,136.0,139.92468251016336,-3.9246825101633647,3.9246825101633647
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",112,2026-07-26,5,pieces,113,117,2026-07-27,2026-07-31,484.0,671.1147301517673,-187.11473015176728,187.11473015176728
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",113,2026-07-27,5,pieces,114,118,2026-07-28,2026-08-01,634.0,490.22294603035346,143.77705396964654,172.0445892060707
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",114,2026-07-28,5,pieces,115,119,2026-07-29,2026-08-02,770.0,462.04458920607067,307.95541079392933,308.7732464763576
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",115,2026-07-29,5,pieces,116,120,2026-07-30,2026-08-03,857.0,460.40891784121413,396.59108215878587,396.59108215878587
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",116,2026-07-30,5,pieces,117,121,2026-07-31,2026-08-04,851.0,480.0817835682429,370.9182164317571,380.95092985905427
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",117,2026-07-31,5,pieces,118,122,2026-08-01,2026-08-05,830.0,556.0163567136485,273.9836432863515,348.7967286572703
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",118,2026-08-01,5,pieces,119,123,2026-08-02,2026-08-06,690.0,1067.2032713427297,-377.20327134272975,404.3219628056379
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",119,2026-08-02,5,pieces,120,124,2026-08-03,2026-08-07,578.0,1121.440654268546,-543.440654268546,543.440654268546
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",120,2026-08-03,5,pieces,121,125,2026-08-04,2026-08-08,546.0,940.2881308537093,-394.2881308537093,394.2881308537093
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",121,2026-08-04,5,pieces,122,126,2026-08-05,2026-08-09,591.0,552.0576261707417,38.94237382925826,94.58847476585164
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",122,2026-08-05,5,pieces,123,127,2026-08-06,2026-08-10,589.0,486.4115252341483,102.58847476585169,113.15308485951101
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",123,2026-08-06,5,pieces,124,128,2026-08-07,2026-08-11,585.0,493.2823050468296,91.7176949531704,112.34353899063407
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",124,2026-08-07,5,pieces,125,129,2026-08-08,2026-08-12,563.0,558.6564610093659,4.3435389906341015,114.73129220187317
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",125,2026-08-08,5,pieces,126,130,2026-08-09,2026-08-13,512.0,699.7312922018732,-187.7312922018732,187.73129220187317
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",126,2026-08-09,5,pieces,127,131,2026-08-10,2026-08-14,496.0,683.9462584403747,-187.94625844037466,187.94625844037463
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",127,2026-08-10,5,pieces,128,132,2026-08-11,2026-08-15,555.0,504.78925168807496,50.210748311925045,87.95785033761499
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",128,2026-08-11,5,pieces,129,133,2026-08-12,2026-08-16,598.0,480.95785033761496,117.04214966238504,123.80842993247701
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",129,2026-08-12,5,pieces,130,134,2026-08-13,2026-08-17,596.0,468.191570067523,127.808429932477,133.08505795948622
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",130,2026-08-13,5,pieces,131,135,2026-08-14,2026-08-18,596.0,477.63831401350467,118.36168598649533,127.41701159189721
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",131,2026-08-14,5,pieces,132,136,2026-08-15,2026-08-19,570.0,575.5276628027009,-5.527662802700888,123.10553256054018
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",132,2026-08-15,5,pieces,133,137,2026-08-16,2026-08-20,513.0,719.1055325605402,-206.10553256054015,206.10553256054015
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",133,2026-08-16,5,pieces,134,138,2026-08-17,2026-08-21,496.0,695.8211065121079,-199.82110651210792,199.82110651210797
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",134,2026-08-17,5,pieces,135,139,2026-08-18,2026-08-22,551.0,503.16422130242154,47.83577869757846,83.6328442604843
D13-v2-development-replay,apparel,anonymous-apparel/terminal-order-demand,SES0.8,"{""alpha"":0.8,""method"":""ses""}",135,2026-08-18,5,pieces,136,140,2026-08-19,2026-08-23,591.0,484.6328442604843,106.36715573951568,118.07343114790314

~~~~

# 文件 experiments/d13-rolling-backtest/practice/run.py

SHA256 640efed76a08a58c263209823483de231f05dad643ae653526da70cb3ee7ca5d

~~~~text
"""D13 development replay. Forecast issuance and later scoring are separate."""
from pathlib import Path
from datetime import date, timedelta
import argparse
import csv
import hashlib
import json
import math
from baseline import forecast_at, load_csv, validate_development, windows
from metrics import evaluate

ROOT = Path(__file__).resolve().parent
RUN_ID = 'D13-v2-development-replay'
METHODS = [('SNaive7', {'method': 'seasonal_naive_7'})] + [
    (f'MA{k}', {'method': 'moving_average', 'k': k}) for k in (3, 7, 14)] + [
    (f'SES{a}', {'method': 'ses', 'alpha': a}) for a in (.2, .5, .8)]
CASES = {'hewei': ('hewei/A/SKU01', 'kg/day', 'kg'),
         'apparel': ('anonymous-apparel/terminal-order-demand', 'pieces/day', 'pieces')}


def dump_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8', newline='\n')


def write_csv(path, records):
    with path.open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(records[0]), lineterminator='\n')
        writer.writeheader()
        writer.writerows(records)


def verify_source():
    manifest = json.loads((ROOT/'source_manifest.json').read_text(encoding='utf-8'))
    for name, expected in manifest['files'].items():
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest() != expected:
            raise ValueError(f'source bytes changed: {name}')
    return manifest


def issue(rows, origin, horizon, case, label, args):
    """No future labels, flags or dates are consulted to issue this vintage."""
    predictions = forecast_at(rows, origin, horizon, **args)
    origin_date = date.fromisoformat(rows[origin-1]['date'])
    identity, daily_unit, _ = CASES[case]
    return [{'run_id': RUN_ID, 'case': case, 'series': identity, 'method': label,
             'parameters': json.dumps(args, sort_keys=True, separators=(',', ':')),
             'unit': daily_unit, 'task_horizon': horizon, 'origin_day': origin,
             'origin_date': origin_date.isoformat(), 'history_last_day': origin,
             'target_day': origin+h, 'target_date': (origin_date+timedelta(days=h)).isoformat(),
             'h': h, 'prediction': value}
            for h, value in enumerate(predictions, 1)]


def replay(rows, case):
    # This validates the offline file, not a fitted transformation or forecast.
    validate_development(rows)
    forecasts, totals, scores = [], [], []
    for label, args in METHODS:
        for horizon in (1, 5):
            scored = []
            for origin, first, last in windows(113, 140, horizon):
                vintage = issue(rows, origin, horizon, case, label, args)
                # Only after the entire vintage is issued are targets attached.
                for record in vintage:
                    target = rows[record['target_day']-1]
                    assert target['date'] == record['target_date']
                    record.update(actual=target['demand'], error=target['demand']-record['prediction'])
                forecasts.extend(vintage)
                actual = math.fsum(r['actual'] for r in vintage)
                prediction = math.fsum(r['prediction'] for r in vintage)
                row = {key: vintage[0][key] for key in ('run_id','case','series','method','parameters','origin_day','origin_date')}
                row.update(task_horizon=horizon, unit=CASES[case][1 if horizon == 1 else 2],
                           first_target_day=first, last_target_day=last,
                           first_target_date=vintage[0]['target_date'], last_target_date=vintage[-1]['target_date'],
                           actual=actual, prediction=prediction, error=actual-prediction,
                           sum_daily_absolute_errors=math.fsum(abs(r['error']) for r in vintage))
                scored.append(row)
                totals.append(row)
            scores.append({'case':case, 'method':label, 'parameters':json.dumps(args, sort_keys=True),
                           'task_horizon':horizon, 'unit':CASES[case][1 if horizon == 1 else 2],
                           **evaluate([r['actual'] for r in scored], [r['prediction'] for r in scored])})
    return forecasts, totals, scores


def leakage_diagnostics(rows, case):
    reports = []
    for origin in range(112, 136):
        for label, args in METHODS:
            original = issue(rows, origin, 5, case, label, args)
            # Poison labels and flags, then also remove future mappings entirely.
            altered = [dict(r) for r in rows]
            for r in altered[origin:]:
                r.update(demand=r['demand']+10000, stockout=True, observed=False)
            assert original == issue(altered, origin, 5, case, label, args)
            assert original == issue(rows[:origin]+[None]*(len(rows)-origin), origin, 5, case, label, args)
            assert original == issue(rows[:origin], origin, 5, case, label, args)
            reports.append({'case':case,'method':label,'origin_day':origin,'horizon':5,
                            'future_label_flag_attack':'unchanged', 'invalid_future_attack':'unchanged',
                            'prefix_only_attack':'unchanged'})
    # A deliberately WRONG negative control: five later revisions are not a vintage.
    origin = 117
    label, args = METHODS[-1]
    fixed = [r['prediction'] for r in issue(rows, origin, 5, case, label, args)]
    revised = [issue(rows, origin+h, 1, case, label, args)[0]['prediction'] for h in range(5)]
    return reports, {'case':case,'method':label,'origin_day':origin,'target_days':[118,119,120,121,122],
                     'fixed_origin_predictions':fixed, 'later_one_step_revisions_WRONG_FOR_ORIGIN117':revised,
                     'fixed_total':math.fsum(fixed),'revised_total':math.fsum(revised),
                     'warning':'revisions use new observations; never used as five-day scores'}


def stockout_counterexample():
    """Separate synthetic January series; no main-experiment row is modified.

    Open-day latent demand is known ONLY because we authored this simulation.
    Closed days have no target; missing sales are None, never zero-imputed.
    """
    records, scores = [], []
    pattern = [18,22,0,24,None,40,38,26,22,24,28,35,30,23]
    for case in CASES:
        factor = 1 if case == 'hewei' else 5
        for i, demand in enumerate(pattern, 1):
            status = 'closed' if i == 5 else 'missing' if i == 8 else 'stockout' if i in (6,7,12) else 'observed'
            truth = None if demand is None else demand*factor
            capacity = 0 if i == 12 else 20*factor if i in (6,7) else 60*factor
            sales = None if status in ('closed','missing') else min(truth,capacity)
            records.append({'case':case, 'unit':CASES[case][1], 'simulation_day':i,
                            'date':(date(2026,1,5)+timedelta(days=i-1)).isoformat(),
                            'status':status,'latent_simulated_demand':truth,'capacity':capacity,
                            'observed_sales':sales,'fixed_demo_prediction':20*factor,
                            'lost_simulated_demand':None if sales is None else truth-sales})
        usable = [r for r in records if r['case']==case and r['observed_sales'] is not None]
        for target in ('observed_sales','latent_simulated_demand'):
            scores.append({'case':case,'unit':CASES[case][1],'target':target,
                           'mask':'same 12 open days with observed sales; no missing or closed day',
                           **evaluate([r[target] for r in usable], [r['fixed_demo_prediction'] for r in usable])})
    return records, scores


def freeze(scores, source):
    selected = []
    for case in CASES:
        for horizon in (1,5):
            options = [r for r in scores if r['case']==case and r['task_horizon']==horizon]
            best = min(options, key=lambda r:(r['mae'],r['method']))
            selected.append({key:best[key] for key in ('case','task_horizon','method','parameters','mae','unit')})
    return {'run_id':RUN_ID,'selection_rule':'minimum validation MAE separately by case and task; tie: method lexical order',
            'selection_timing':'after full development replay, never fed back into historical issuance',
            'claim_limit':'retrospective teaching choice on repeatedly inspected data, not unbiased generalization or a new blind test',
            'source_sha256':source['files'], 'selected':selected,
            'deployment_scope':'frozen teaching configurations only; no production order or replenishment action'}


def main():
    source = verify_source()
    forecasts, totals, scores, attacks, negative = [], [], [], [], []
    for case, (identity, _, _) in CASES.items():
        rows = load_csv(ROOT/'data'/f'{case}-development.csv', identity)
        f,t,s = replay(rows,case)
        forecasts.extend(f); totals.extend(t); scores.extend(s)
        a,n = leakage_diagnostics(rows,case)
        attacks.extend(a); negative.append(n)
    stock, stock_scores = stockout_counterexample()
    out = ROOT/'results'; out.mkdir(exist_ok=True)
    for name, data in [('predictions',forecasts),('window_totals',totals),('metrics',scores),
                       ('leakage_diagnostics',attacks),('stockout_simulation',stock),('stockout_metrics',stock_scores)]:
        write_csv(out/f'{name}.csv',data)
    dump_json(out/'negative_control.json',negative)
    dump_json(out/'frozen_selection.json',freeze(scores,source))
    dump_json(out/'run_manifest.json',{'run_id':RUN_ID,'source':source,'methods':METHODS,
              'initial_history':[1,112],'validation':[113,140], 'forecasts':len(forecasts),
              'one_day_targets_per_method_case':28,'five_day_windows_per_method_case':24,
              'forecast_order':'issue all h at an origin before attach labels; expanding observed history across origins',
              'test_labels':'not included or accessed', 'main_experiment':'fully observed simulated demand',
              'stockout_counterexample':'separate January data, never passed to forecasting models',
              'five_day_wape_denominator':'sum of actual totals across 24 overlapping windows, not unique volume'})
    print(f'{len(forecasts)} forecast rows, {len(totals)} totals, {len(scores)} scores, {len(attacks)} attack cases.')


if __name__ == '__main__':
    argparse.ArgumentParser(description=__doc__).parse_args()
    main()

~~~~

# 文件 experiments/d13-rolling-backtest/practice/source_manifest.json

SHA256 1058e120ac4c2d9b2d8e41ac6e5211cec6e7c07f34cc9ce58a25e60d26cd1261

~~~~text
{
  "source_version": "D9-v1",
  "public_zip_sha256": "0063b6ddae7459eff9dc7779c0a0a6c9ecef8d0bd48320c653eae1c072ce1c31",
  "files": {
    "data/hewei-development.csv": "292072a63439529f22a73d41b83516928ae5a5b474b907b33d42e74962c23407",
    "data/apparel-development.csv": "56badd2fc37decd72b2f55a980acb7add2594b96c7b8d269f6aaae59ee7d47e5"
  },
  "copy_policy": "Development CSV bytes copied from D12 at repository HEAD 8fc0bdf14d695ca074736d26357094acf63644fe; inherited D9 hashes verified. Only days 1..140.",
  "public_zip_hash_status": "Inherited declaration only; original D9 ZIP not opened or reverified for D13."
}

~~~~

# 文件 experiments/d13-rolling-backtest/practice/test_backtest.py

SHA256 407300b6b758ff90fcf09efbb7f6cdbf80155ad905fd6c4c1a887ea020e2bc90

~~~~text
"""Independent exact-arithmetic oracle and attacks on the issuance boundary."""
import copy
from datetime import date,timedelta
from fractions import Fraction as F
import math
import unittest
from baseline import forecast_at, load_csv, validate_development, windows
from metrics import evaluate
from run import ROOT, METHODS, CASES, issue, replay, leakage_diagnostics, stockout_counterexample, freeze, verify_source


def oracle(values, label, h):
    values = [F(str(v)) for v in values]
    if label == 'SNaive7':
        return values[-7+(h-1)%7]
    if label.startswith('MA'):
        k = int(label[2:]); return sum(values[-k:])/k
    a=F(label[3:]); n=len(values)
    return values[0]*(1-a)**(n-1)+sum(a*(1-a)**(n-1-i)*values[i] for i in range(1,n))


class BacktestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows={c:load_csv(ROOT/'data'/f'{c}-development.csv',meta[0]) for c,meta in CASES.items()}
        cls.results={c:replay(rows,c) for c,rows in cls.rows.items()}

    def test_source_hashes_and_only_development(self):
        self.assertEqual(len(verify_source()['files']),2)
        self.assertEqual(sorted(p.name for p in (ROOT/'data').iterdir()),['apparel-development.csv','hewei-development.csv'])
        for rows in self.rows.values():
            validate_development(rows)
            self.assertEqual(len(rows),140)

    def test_window_counts_and_edges(self):
        self.assertEqual(windows(113,140,1),[(i-1,i,i) for i in range(113,141)])
        self.assertEqual(windows(113,140,5),[(i-1,i,i+4) for i in range(113,137)])
        self.assertEqual(windows(113,114,5),[])
        for args in [(0,140,5),(113,112,1),(113,140,0),(113,140,True)]:
            with self.assertRaises(ValueError): windows(*args)

    def test_all_forecasts_with_fraction_oracle(self):
        for case,(forecasts,_,_) in self.results.items():
            self.assertEqual(len(forecasts),7*(28+24*5))
            rows=self.rows[case]
            for r in forecasts:
                expected=oracle([v['demand'] for v in rows[:r['origin_day']]],r['method'],r['h'])
                self.assertAlmostEqual(r['prediction'],float(expected),places=10)

    def test_all_dates_horizons_parameters_and_no_cross_block(self):
        for case,(forecasts,_,_) in self.results.items():
            for r in forecasts:
                self.assertEqual(r['target_day'],r['origin_day']+r['h'])
                self.assertEqual(date.fromisoformat(r['target_date']),date.fromisoformat(r['origin_date'])+timedelta(days=r['h']))
                self.assertEqual(r['history_last_day'],r['origin_day'])
                self.assertTrue(113<=r['target_day']<=140)
                self.assertTrue(1<=r['h']<=r['task_horizon'])
                self.assertTrue(r['parameters'])
                self.assertEqual(r['series'],CASES[case][0])

    def test_totals_equal_same_origin_forecasts(self):
        for _,(forecasts,totals,_) in self.results.items():
            self.assertEqual(len(totals),7*(28+24))
            for t in totals:
                rs=[r for r in forecasts if (r['method'],r['origin_day'],r['task_horizon'])==(t['method'],t['origin_day'],t['task_horizon'])]
                self.assertEqual(len(rs),t['task_horizon'])
                self.assertEqual(t['prediction'],math.fsum(r['prediction'] for r in rs))
                self.assertEqual(t['actual'],math.fsum(r['actual'] for r in rs))
                self.assertLessEqual(abs(t['error']),t['sum_daily_absolute_errors']+1e-12)

    def test_scores_against_exact_oracle(self):
        for case,(_,totals,scores) in self.results.items():
            rows=self.rows[case]
            for s in scores:
                ts=[t for t in totals if (t['method'],t['task_horizon'])==(s['method'],s['task_horizon'])]
                actual=[sum(F(str(v['demand'])) for v in rows[t['first_target_day']-1:t['last_target_day']]) for t in ts]
                pred=[sum(oracle([v['demand'] for v in rows[:t['origin_day']]],s['method'],h) for h in range(1,s['task_horizon']+1)) for t in ts]
                errors=[a-p for a,p in zip(actual,pred)]
                expected={'me':sum(errors)/len(errors),'mae':sum(map(abs,errors))/len(errors),
                          'rmse':math.sqrt(float(sum(e*e for e in errors)/len(errors))),
                          'wape':sum(map(abs,errors))/sum(actual)}
                for key,value in expected.items():self.assertAlmostEqual(s[key],float(value),places=10)
                self.assertEqual(s['n'],28 if s['task_horizon']==1 else 24)

    def test_all_future_and_prefix_attacks(self):
        for case,rows in self.rows.items():
            reports,_=leakage_diagnostics(rows,case)
            self.assertEqual(len(reports),24*7)
            # Cover the final four one-step origins as well.
            for origin in range(136,140):
                for label,args in METHODS:
                    self.assertEqual(issue(rows,origin,1,case,label,args),issue(rows[:origin]+[None]*4,origin,1,case,label,args))

    def test_full_replay_future_change_cannot_rewrite_prior_vintages(self):
        for case,rows in self.rows.items():
            altered=copy.deepcopy(rows)
            for r in altered[120:]:r.update(demand=r['demand']+1000,stockout=True)
            old=self.results[case][0];new=replay(altered,case)[0]
            for a,b in zip(old,new):
                if a['origin_day']<=120:self.assertEqual(a['prediction'],b['prediction'])

    def test_observed_history_can_update_next_origin(self):
        for case,rows in self.rows.items():
            altered=copy.deepcopy(rows);altered[112]['demand']+=10
            a={'method':'ses','alpha':.5}
            self.assertEqual(forecast_at(rows,112,5,**a),forecast_at(altered,112,5,**a))
            self.assertAlmostEqual(forecast_at(altered,113,1,**a)[0]-forecast_at(rows,113,1,**a)[0],5)

    def test_revisions_negative_control_is_detectably_wrong(self):
        for case,rows in self.rows.items():
            _,n=leakage_diagnostics(rows,case)
            self.assertNotAlmostEqual(n['fixed_total'],n['revised_total'])

    def test_no_full_sample_preprocessing(self):
        rows=self.rows['hewei']
        with self.assertRaises(ValueError):
            forecast_at([dict(r,demand=None) if i==20 else r for i,r in enumerate(rows)],112,1)
        self.assertEqual(forecast_at(rows,112,5),forecast_at(rows[:112]+[{'demand':'poison','stockout':True}],112,5))

    def test_reject_missing_duplicate_and_foreign_series(self):
        for change in ('missing','duplicate','foreign'):
            rows=copy.deepcopy(self.rows['hewei'])
            if change=='missing':rows[20]['demand']=None
            if change=='duplicate':rows[20]['date']=rows[19]['date']
            if change=='foreign':rows[20]['series']='other'
            with self.assertRaises(ValueError):replay(rows,'hewei')

    def test_sum_error_is_not_sum_absolute_error(self):
        actual=[0,4,2,2,2];pred=[2,2,2,2,2]
        self.assertEqual(abs(sum(actual)-sum(pred)),0)
        self.assertEqual(sum(abs(a-p) for a,p in zip(actual,pred)),4)

    def test_overlap_denominator_not_unique_volume(self):
        for case,(_,totals,scores) in self.results.items():
            unique=sum(r['demand'] for r in self.rows[case][112:])
            for s in scores:
                if s['task_horizon']==5:self.assertGreater(s['actual_sum'],unique)

    def test_stockout_different_statuses_not_zero_imputation(self):
        records,scores=stockout_counterexample()
        for case in CASES:
            rs={r['simulation_day']:r for r in records if r['case']==case}
            self.assertEqual(rs[3]['observed_sales'],0)
            self.assertEqual(rs[3]['latent_simulated_demand'],0)
            for day in (5,8):self.assertIsNone(rs[day]['observed_sales'])
            self.assertIsNone(rs[5]['latent_simulated_demand'])
            self.assertGreater(rs[8]['latent_simulated_demand'],0)
            self.assertEqual(rs[12]['observed_sales'],0)
            self.assertGreater(rs[12]['latent_simulated_demand'],0)
            for day in (6,7,12):self.assertEqual(rs[day]['observed_sales'],min(rs[day]['latent_simulated_demand'],rs[day]['capacity']))
        self.assertTrue(all(s['n']==12 for s in scores))

    def test_sales_perfect_does_not_imply_demand_perfect(self):
        records,_=stockout_counterexample()
        for r in records:
            if r['simulation_day']==6:
                self.assertEqual(r['observed_sales'],r['fixed_demo_prediction'])
                self.assertGreater(r['latent_simulated_demand'],r['fixed_demo_prediction'])

    def test_separate_stockout_does_not_mutate_main(self):
        before=copy.deepcopy(self.rows)
        stockout_counterexample()
        self.assertEqual(before,self.rows)

    def test_freeze_is_post_replay_min_mae_per_task(self):
        scores=sum((r[2] for r in self.results.values()),[])
        result=freeze(scores,verify_source())
        self.assertEqual(len(result['selected']),4)
        for selected in result['selected']:
            subset=[r for r in scores if (r['case'],r['task_horizon'])==(selected['case'],selected['task_horizon'])]
            self.assertEqual(selected['mae'],min(r['mae'] for r in subset))

    def test_metric_manual_zero_denominator_and_invalid(self):
        r=evaluate([0,10],[2,8])
        self.assertEqual([r[k] for k in ('mae','rmse','me','wape')],[2,2,0,.4])
        self.assertIsNone(evaluate([0,0],[2,0])['wape'])
        for actual,pred in [([],[]),([1],[1,2]),([None],[0]),([float('nan')],[0]),([-1],[0])]:
            with self.assertRaises(ValueError):evaluate(actual,pred)

    def test_moving_average_preserves_subnormal_mean(self):
        tiny = math.nextafter(0.0, 1.0)
        rows = [dict(r, demand=tiny) for r in self.rows['hewei'][:3]]
        self.assertEqual(forecast_at(rows,3,5,method='moving_average',k=3),[tiny]*5)

    def test_moving_average_rejects_unrepresentable_mean(self):
        tiny = math.nextafter(0.0, 1.0)
        rows = [dict(r,demand=v) for r,v in zip(self.rows['hewei'][:3],[tiny,0,0])]
        with self.assertRaisesRegex(ValueError,'underflows'):
            forecast_at(rows,3,1,method='moving_average',k=3)
        self.assertEqual(forecast_at([dict(r,demand=0) for r in rows],3,1,method='moving_average',k=3),[0])

    def test_moving_average_requires_finite_aggregate(self):
        rows = [dict(r,demand=1e308) for r in self.rows['hewei'][:3]]
        with self.assertRaisesRegex(ValueError,'sum exceeds'):
            forecast_at(rows,3,1,method='moving_average',k=3)
        for r in rows:r['demand']=1e307
        self.assertEqual(forecast_at(rows,3,1,method='moving_average',k=3),[1e307])


if __name__=='__main__':unittest.main()

~~~~

# 文件 experiments/d13-rolling-backtest/figure-tools/render_figures.py

SHA256 ec44bff307bcff9dbe801a2b9d6717d2736868a071cdbf4c8effde622e7fef68

~~~~text
#!/usr/bin/env python3
"""D13 monochrome publication figures from replay and separate simulation."""
from pathlib import Path
import argparse, csv, hashlib, json, math
from itertools import combinations
from PIL import Image, ImageDraw, ImageFont, ImageChops
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parents[1]
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--font-path', type=Path, required=True, help='Standalone Noto Sans SC TTF/OTF font')
a = p.parse_args()
FONT = str(a.font_path.expanduser().resolve())
font = TTFont(FONT)
families = {n.toUnicode() for n in font['name'].names if n.nameID in (1, 16)}
if not any(n in families for n in ['Noto Sans SC', 'Noto Sans CJK SC']):
    raise ValueError(f'Simplified Chinese Noto font required, got {families}')
cmap = font.getBestCmap()
OUT = ROOT / 'images'; OUT.mkdir(exist_ok=True)
SCALE = 2
REPORT = []
CURVES = {}
def line(draw, points, style='solid', width=3, fill=0):
    if style == 'solid':
        draw.line([(round(x*SCALE),round(y*SCALE)) for x,y in points], fill=fill, width=round(width*SCALE), joint='curve')
        return
    pattern = {'dash': [20,12], 'dot': [4,12], 'dashdot': [24,8,4,8]}[style]
    i=0; remaining=pattern[0]
    for (x,y),(xx,yy) in zip(points,points[1:]):
        length=math.hypot(xx-x,yy-y); used=0
        while used < length-1e-8:
            take=min(remaining,length-used)
            if i%2==0:
                q=[(x+(xx-x)*u/length,y+(yy-y)*u/length) for u in [used,used+take]]
                line(draw,q,'solid',width,fill)
            used+=take;remaining-=take
            if remaining<1e-8:
                i=(i+1)%len(pattern);remaining=pattern[i]

class Figure:
    def __init__(self,name,w,h):
        self.name=name; self.w=w;self.h=h;self.texts=[]
        self.im=Image.new('L',(w*SCALE,h*SCALE),255);self.d=ImageDraw.Draw(self.im)
    def text(self,x,y,s,size=52,fill=0,anchor='lt'):
        assert all(ord(c) in cmap or c.isspace() for c in s), ('missing glyph',s)
        f=ImageFont.truetype(FONT,round(size*SCALE))
        xy=(round(x*SCALE),round(y*SCALE));b=self.d.textbbox(xy,s,font=f,anchor=anchor)
        assert b[0]>=0 and b[1]>=0 and b[2]<=self.w*SCALE and b[3]<=self.h*SCALE,(self.name,s,b)
        self.d.text(xy,s,font=f,fill=fill,anchor=anchor)
        self.texts.append({'text':s,'font_size':size,'bbox':[v/SCALE for v in b]})
    def path(self,points,style='solid',width=3,fill=0):
        line(self.d,points,style,width,fill)
    def rect(self,b,fill=246):
        self.d.rectangle(tuple(round(v*SCALE) for v in b),fill=fill,outline=0,width=2*SCALE)
    def save(self):
        for x,y in combinations(self.texts,2):
            b=x['bbox'];c=y['bbox']
            assert not (min(b[2],c[2])>max(b[0],c[0]) and min(b[3],c[3])>max(b[1],c[1])),(self.name,x['text'],y['text'])
        im=self.im.resize((self.w,self.h),Image.Resampling.LANCZOS).convert('RGB')
        for width in [self.w,350,280]:
            folder=OUT if width==self.w else OUT/f'preview-{width}'
            folder.mkdir(exist_ok=True)
            target=folder/self.name
            rendered=im if width==self.w else im.resize((width,round(self.h*width/self.w)),Image.Resampling.LANCZOS)
            rendered.save(target,optimize=True)
            r,g,b=rendered.split()
            assert ImageChops.difference(r,g).getbbox() is None and ImageChops.difference(g,b).getbbox() is None
        REPORT.append({'file':self.name,'size':[self.w,self.h],'sha256':hashlib.sha256((OUT/self.name).read_bytes()).hexdigest(),'text_boxes':self.texts,'text_overlap':False,'grayscale':True})

negative=json.loads((ROOT/'practice/results/negative_control.json').read_text())
with (ROOT/'practice/results/stockout_simulation.csv').open() as h:
    stock=list(csv.DictReader(h))

f=Figure('d13-00_cover.png',900,383)
f.text(40,26,'D13  /  ROLLING BACKTEST',23,70)
f.text(40,85,'预测时，还不知道的事',54)
f.path([(65,242),(835,242)],width=3)
f.path([(440,188),(440,300)],width=4)
f.text(78,200,'已知历史',30)
f.text(540,200,'未来观测',30,90)
f.text(365,320,'先预测，再更新',29)
f.save()

f=Figure('d13-01_origins.png',1200,1280)
f.text(60,45,'每个起点，都保存当时的版本',56)
f.text(60,150,'第 112 天日终：只看 1—112 天',50)
for y,title,sub in [(300,'一步：目标 113','得到 113 天实际后，才进入下一起点'),(585,'五步：目标 113—117','五个预测一起发出，中间不改旧版本')]:
    f.rect((45,y-30,1155,y+175))
    f.text(75,y,title,56)
    f.text(75,y+100,sub,46)
f.text(60,880,'一步：112—139 起点，28 个目标',49)
f.text(60,990,'五步：112—135 起点，24 个窗口',49)
f.text(60,1110,'只到第 140 天；窗口重叠非独立样本',48)
f.save()

f=Figure('d13-02_revisions.png',1200,1390)
f.text(60,45,'同样五天，却不是同一份预测',56)
f.text(60,150,'匿名服装模拟｜SES α=0.8｜件',49,65)
r=next(r for r in negative if r['case']=='apparel')
f.text(60,290,'第 117 天日终一次发出',54)
f.text(60,395,'五步均为 111.2033 件/日',52)
f.rect((55,510,1145,680))
f.text(85,555,f'固定起点合计：{r["fixed_total"]:.2f} 件',58)
f.text(60,795,'随后每天吸收新订单，再修订',52)
f.rect((55,910,1145,1080),fill=225)
f.text(85,955,f'逐日修订合计：{r["revised_total"]:.2f} 件',58)
f.text(60,1195,'后者不能冒充第 117 天发出的五步。',48)
f.text(60,1290,'目标 118—122 天；不将负对照用于评分。',46,65)
f.save()

f=Figure('d13-03_stockout.png',1200,1890)
f.text(60,45,'缺货截断：销量低，不代表需求低',55)
f.text(60,145,'独立 14 天模拟，服装为禾味数量五倍',46,65)
f.path([(65,255),(200,255)],width=5)
f.text(230,224,'模拟需求',48)
f.path([(615,255),(750,255)],style='dash',width=5,fill=95)
f.text(780,224,'可观测销量',48)
for top,case,title,maxv,ticks in [(405,'hewei','禾味｜公斤/日',45,[0,20,40]),(1000,'apparel','匿名服装｜件/日',225,[0,100,200])]:
    f.text(60,top-55,title,50)
    left,right,base,height=150,1130,top+360,325
    f.path([(left,top+25),(left,base),(right,base)],width=3)
    for v in ticks:
        y=base-v/maxv*height
        f.path([(left,y),(right,y)],width=1,fill=205)
        f.text(120,y,str(v),40,anchor='rm')
    rs=[r for r in stock if r['case']==case]
    for key,style,gray in [('latent_simulated_demand','solid',0),('observed_sales','dash',95)]:
        segments=[];points=[]
        for r in rs:
            if not r[key]:
                if points:segments.append(points);points=[]
                continue
            points.append((left+(int(r['simulation_day'])-1)*(right-left)/13,base-float(r[key])/maxv*height))
        if points:segments.append(points)
        for pts in segments:
            f.path(pts,style,width=4,fill=gray)
            for x,y in pts:
                f.d.ellipse(((x-5)*SCALE,(y-5)*SCALE,(x+5)*SCALE,(y+5)*SCALE),fill=gray)
    for d in [1,3,5,8,12,14]:
        x=left+(d-1)*(right-left)/13
        f.text(x,base+30,str(d),38,anchor='mt')
    f.text(620,base+100,'模拟日（1 月 5—18 日）',42,anchor='mt')
f.text(60,1540,'第 3 天真零；第 12 天缺货零销量。',48)
f.text(60,1640,'第 5 天休店、第 8 天缺测：销量留空。',48)
f.text(60,1740,'实线真值仅模拟作者知道，现实不能照搬。',46)
f.save()

(ROOT/'figure-tools/render-quality-report.json').write_text(json.dumps({'font_families':sorted(families),'font_sha256':hashlib.sha256(Path(FONT).read_bytes()).hexdigest(),'inputs_sha256':{name:hashlib.sha256((ROOT/'practice/results'/name).read_bytes()).hexdigest() for name in ['negative_control.json','stockout_simulation.csv']},'figures':REPORT},ensure_ascii=False,indent=2)+'\n')
print('Four grayscale figures rendered; glyph, bounds and text overlap checks passed.')

~~~~

# 文件 experiments/d13-rolling-backtest/figure-tools/README.md

SHA256 215829d435deca6fab972c705a3e093814c363cb2efca4f5de1614876242ae8f

~~~~text
# D13 黑白图重绘

Python、Pillow、fontTools及独立TTF/OTF的Noto Sans SC或Noto Sans CJK SC字体。字体不随包分发。

```bash
python -m pip install Pillow fontTools
python practice/run.py
python figure-tools/render_figures.py --font-path /path/to/NotoSansSC.ttf
```

脚本按自身位置查找输入，输出4张灰度图与280/350px预览到images。封面原生900×383，正文按内容排版；无裁切拉伸。图2读negative_control.json；缺货图读stockout_simulation.csv，空白值断线、零值保留。数据曲线点标记、实虚线与文字共同区分，不仅靠灰度。图中文字、字形、边界和重叠检查结果在render-quality-report.json。

使用环境：Python 3.14、Pillow 13.0.0、fontTools 4.68.0；字体文件SHA见报告。其他版本可能产生像素差异，指标计算不依赖绘图库。主图、280px和350px均应人工复核，机器检查不能替代审查。

~~~~

# 文件 docs/d13-review/README.md

SHA256 13ba7c5523703dbc0868f3be61273e769eeab0aa6eef88a2860e38b4b24eb67a

~~~~text
# D13 v3 文字修正与打包差异交接

状态：主审线程已通知v2第二轮数学、下载包及图文审查通过。v3仅将“把第121天之后的标签改大”改为“从第121天起把标签改大”，同步文章包，等待这处文字及打包差异的独立复核。未提交、未推送，未迁入原仓库。

原仓库 /Users/laoer/Documents/12lab.cn，HEAD 8fc0bdf14d695ca074736d26357094acf63644fe，制作前后git status均为空。隔离副本为 /Users/laoer/Documents/Codex/2026-11-06/task/d13-candidate。复制排除.git、sealed、缓存与构建目录；未打开原测试标签或D9下载包。完整检查沿用D11审查通过的规则，只对D9既有测试结果做固定哈希完整性校验、复算前140天中的验证段。

## 集成范围

仅新增 content/blog/rolling-backtest-stockout-censoring/、experiments/d13-rolling-backtest/、scripts/package-d13.py、static/downloads/d13-rolling-backtest-{practice,article,images}.zip、docs/d13-review/。不应同步整个副本，不应修改原仓库其他变更。AGENTS.md、scripts/check.sh、D9回归脚本及CI逐字节不变，证据见unchanged-release-checks.json。

第一轮处理见round1-resolution.md。v1、v2冻结包保持原字节；v3单独命名。发布载荷相比v2仅正文和文章ZIP变化，40个其他载荷文件完全一致。文章ZIP内部仅index.md和MANIFEST.sha256变化，见v2-v3-payload-diff.json及v2-v3-article.patch。实践代码、开发CSV、九份结果、图表和两个其他读者ZIP不变，运行编号仍为D13-v2-development-replay。v3是文稿包版本，不是一次新实验。

## 实际检查

22项实践测试通过；Fraction独立算术展开核对2072条预测、28行指标。728条总量含392个一步和336个固定五日窗口；336组未来攻击每组3种，外加完整回放未来扰动、最后4个一步起点、已观测值应能更新的正对照。7个候选全展示，原测试不重评。

3个ZIP无重复成员、清单集合完整、每成员SHA256匹配。干净解压22项测试通过，从另一个工作目录运行入口，九份结果全部逐字节一致。见package-verification.json及verify_packages.py。最终打包后重新清洁构建；从实际文章href通过HTTP获取三个下载包，与源ZIP及构建ZIP逐字节一致，且图包含重绘README，见served-download-verification.json。

Hugo 0.166.0 extended，和CI版本一致。HUGO_CACHEDIR=/tmp/d13-hugo-cache BROWSER_CHECKS=require make check完整通过，含7项浏览器检查、20项D9测试、2条开发回归。首轮沙箱因127.0.0.1监听EPERM中止，未弱化检查，在允许本机监听环境重跑成功。见make-check.txt。

D13专项浏览器检查1440/390/320px通过：页面无横向溢出，2表可键盘聚焦、手机内部滚动，4图均完整加载。截图保存在output/playwright（不入版本库）；浏览器报告在browser-review.txt。作者查看1440页首、320表格，以及四图280px预览。现有全站悬浮目录按钮仍可能在窄屏某个滚动位置遮住局部正文，本篇不修改主题。

四图纯灰度，封面原生900×383；正文按内容独立尺寸。重绘使用Python3.14、Pillow13.0.0、fontTools4.68.0及Noto Sans SC，字体与输入哈希、边界和文字不重叠检查见render-quality-report.json。封面和所有配图由Python排版源码重绘，不通过旧图裁切或拉伸生成。

## 审查必须攻击的边界

1. 预测函数在检查数值前切历史前缀；离线完整性验证和事后评分不能变成拟合或插补。
2. 五日窗口同一起点一次发布，不准用后续一步修订拼接；输出起点、日期、步长、参数与单位逐条可核对。
3. 先选参数再在同段报分会有选择偏差。本篇明确反复查看的教学开发回放，冻结在全部回放之后，不回灌历史，也不称新盲测或独立泛化证据。
4. 缺货另造14天一月反例，未改主数据。闭店目标未定义，缺测销量空白，真零与缺货零分离；模拟真值不可称现实已恢复。服装是五倍单位演示，不是独立实证。
5. 28个一步目标、24个重叠五日窗口；窗口WAPE分母重复覆盖，不同单位不合并；误差符号为实际减预测。

已访问一手来源 https://otexts.com/fpp3/tscv.html ，跳转第5章并核验5.10滚动起点段落。正文按该稳定链接引用，不依赖未核验锚点。

## 私人材料

Space 已核验 shares=[]，继承来源完整且为空，仅所有者。v1审查页 https://chatgpt.com/space/page_6aed32583ebc8191bc5c9ee6133c64d9 作为历史冻结记录保留；v2审查页为 https://chatgpt.com/space/page_6aed372e52ec819195467d3d1f7cfff3 。v3另建文字与打包差异审查页。附件将包含完整候选ZIP、可读文本整包、正文、4图和冻结回执。Space自身渲染预览未目视检查，保存及附件回读另行核验；本机文章渲染已检查。

~~~~

# 文件 docs/d13-review/v2-v3-payload-diff.json

SHA256 d019b1fee032ab8e9adf00324c3feee04625837c191d677f420d1df346291cfb

~~~~text
{
  "scope": "Only article wording and article ZIP changed in deliverable payload; model, data, results, figures, practice ZIP, images ZIP and packaging script unchanged",
  "changes": [
    {
      "path": "content/blog/rolling-backtest-stockout-censoring/index.md",
      "v2_sha256": "992e1f759a3c861b72c852c6a1bae579e87505ac6ef35dd8726b27cc73a6d513",
      "v3_sha256": "2630744df203c73ffb2d24b2e9cb0d24106db201c4e36c1fe857d2dfeedc65df"
    },
    {
      "path": "static/downloads/d13-rolling-backtest-article.zip",
      "v2_sha256": "c811768b896dee8c7f5ddc204c39c0cb49aade3d2ec016832af119bca5262392",
      "v3_sha256": "1f9247ceea88beeb51e0902341bf73fa40a9b51d6e0efa2a16fbd0bde3733317"
    }
  ],
  "article_zip_changed_members": [
    "MANIFEST.sha256",
    "index.md"
  ],
  "unchanged_payload_files": 40
}

~~~~

# 文件 docs/d13-review/v2-v3-article.patch

SHA256 f0368c7e97061684ec1185a3642d36a5171a865eba502d498e07f93fbaad181a

~~~~text
--- v2/content/blog/rolling-backtest-stockout-censoring/index.md
+++ v3/content/blog/rolling-backtest-stockout-censoring/index.md
@@ -150 +150 @@
-还对完整回放增加一道检查：把第121天之后的标签改大，所有截至第120天日终已经发出的预测保持不变。评分结果可以变，因为实际标签变了；预测版本不能变。最后四个一步起点也单独覆盖。
+还对完整回放增加一道检查：从第121天起把标签改大，所有截至第120天日终已经发出的预测保持不变。评分结果可以变，因为实际标签变了；预测版本不能变。最后四个一步起点也单独覆盖。

~~~~

# 文件 docs/d13-review/round1-resolution.md

SHA256 4c716a8e675d45089a5989e11dfa245283e31d2800e53ebc15ee558b21543379

~~~~text
# D13 第一轮修订说明

本文件记录作者处理结果，第二轮独立审查尚未进行。v1完整冻结包保留为工作目录上一级d13-review-v1.zip，不改其字节。

## 实际下载包与冻结包不一致

根因是操作顺序：图形README补入并重新打包晚于上一轮Hugo构建，.hugo-check保留旧ZIP。不是HTTP随机错误，也不应以源目录哈希替代实际服务验证。修复前证据在v1-download-mismatch.json：static图包4b6536…含README，而构建图包884237…缺README。

v2执行顺序固定为：源修改和实验重算 → 最终打包 → 干净解压验证 → 完整make check（清空并重新构建.hugo-check）→ 从实际页面href通过HTTP下载 → 核对源ZIP、构建ZIP和HTTP字节完全一致 → 冻结。verify_served_downloads.py启动仅监听127.0.0.1的临时服务，从实际文章提取三个下载链接，校验每个HTTP响应200、字节、成员集合与SHA，并断言图包含figure-tools/README.md。结果在served-download-verification.json。

后续若任一读者包重新打包，必须重新构建、重新实际下载核验再冻结，不允许沿用旧页面服务。

## MA3极小数下溢

原代码先逐项除以k再求和，三个最小正浮点数5e-324均先除成0。v2改为math.fsum窗口后再除以k。数值契约明确：MA窗口聚合和必须有限；聚合溢出即报错，即使最终均值理论上可表示。非零均值下溢成0也报错；合法全零仍返回0。不是任意精度保证。

新增3项回归覆盖三个5e-324的MA3仍为5e-324、[5e-324,0,0]下溢拒绝及合法零、聚合溢出拒绝及可表示大值。共22项测试通过。全部实验重算后19个全精度指标字段发生普通舍入差异，正文四位小数与模型选择均不变，见v2-numeric-comparison.json。

## 措辞与信息到达边界

FPP3引介改为“预测起点当时已获得的观测”；“禾味真实采购”改为“若用于真实餐饮采购”。正文和实践README明确没有available_at字段或延迟过滤，只适用于当日日终全部记录已可得的假设。真实延迟系统需要另实现可用时间过滤，不能宣称当前代码支持。

## 既有目录按钮

320及390视口的全站悬浮目录按钮可能局部遮挡正文，列为现有主题限制；本次没有改任何全局样式或模板。专项页面检查验证无横向溢出、图完整加载、表内滚动，不将其写成“无任何遮挡”。

原仓库及发布检查均未修改。未提交、未推送，v2等待第二轮独立审查。

~~~~

# 文件 docs/d13-review/served-download-verification.json

SHA256 31f9a6f9c66f6dd7392f4947ea1b1a13aeac5a37aae2adf38cc751df71fa90d9

~~~~text
{
  "page": "/blog/rolling-backtest-stockout-censoring/",
  "page_sha256": "c8b5d7a9c6d886b0d090c3dc9a80047e8649d17bb1850d5ab4709b4d4eac0ad5",
  "downloads": [
    {
      "href": "/downloads/d13-rolling-backtest-article.zip",
      "source_sha256": "1f9247ceea88beeb51e0902341bf73fa40a9b51d6e0efa2a16fbd0bde3733317",
      "build_sha256": "1f9247ceea88beeb51e0902341bf73fa40a9b51d6e0efa2a16fbd0bde3733317",
      "http_sha256": "1f9247ceea88beeb51e0902341bf73fa40a9b51d6e0efa2a16fbd0bde3733317",
      "bytes": 649288,
      "manifest": "complete, all members verified"
    },
    {
      "href": "/downloads/d13-rolling-backtest-images.zip",
      "source_sha256": "cf112cad7e5ab481f44f0395b996c980e6e639c865e0e9a980876d5bd817555b",
      "build_sha256": "cf112cad7e5ab481f44f0395b996c980e6e639c865e0e9a980876d5bd817555b",
      "http_sha256": "cf112cad7e5ab481f44f0395b996c980e6e639c865e0e9a980876d5bd817555b",
      "bytes": 1007384,
      "manifest": "complete, all members verified"
    },
    {
      "href": "/downloads/d13-rolling-backtest-practice.zip",
      "source_sha256": "6bafac220cad3a33e86d5486a6ea45f512d4d4a24f64071bb8a33d28d263d7dc",
      "build_sha256": "6bafac220cad3a33e86d5486a6ea45f512d4d4a24f64071bb8a33d28d263d7dc",
      "http_sha256": "6bafac220cad3a33e86d5486a6ea45f512d4d4a24f64071bb8a33d28d263d7dc",
      "bytes": 61098,
      "manifest": "complete, all members verified"
    }
  ]
}

~~~~

# 文件 docs/d13-review/FREEZE.json

SHA256 ef6b74617c17e12cfde759aa30e26fb72d4636b6900daf37f0cba504f566ccca

~~~~text
{
  "status": "v3: v2 round 2 passed per parent; wording and packaging delta awaiting independent check; not submitted or pushed",
  "version": "D13-v3",
  "source_repo_head": "8fc0bdf14d695ca074736d26357094acf63644fe",
  "files": {
    "experiments/d13-rolling-backtest/figure-tools/README.md": "215829d435deca6fab972c705a3e093814c363cb2efca4f5de1614876242ae8f",
    "experiments/d13-rolling-backtest/figure-tools/render-quality-report.json": "9ad597225bf0cae6b2b77447d82b022a7d131cc29c1bd56408bc8d441b5e6bb1",
    "experiments/d13-rolling-backtest/figure-tools/render_figures.py": "ec44bff307bcff9dbe801a2b9d6717d2736868a071cdbf4c8effde622e7fef68",
    "experiments/d13-rolling-backtest/images/d13-00_cover.png": "b706f84f877022c6e3e218900c557bfbe8d665cfec160a47c3e2e6d0af8d2f46",
    "experiments/d13-rolling-backtest/images/d13-01_origins.png": "89e1d46f98827d4784adc8384bff9f20e9ba9607a6601f53cdd053d46422ecf4",
    "experiments/d13-rolling-backtest/images/d13-02_revisions.png": "83c804fbd957a50c827a6c0c56a8e2a2e7b71892bcb93a10a260c00de6fe8b3f",
    "experiments/d13-rolling-backtest/images/d13-03_stockout.png": "e40e2776c4089551adbbd8b18bf59670e220b53a9936ea09d8872b96562d0d49",
    "experiments/d13-rolling-backtest/images/preview-280/d13-00_cover.png": "49961b5f5b4ebc22f18eec6f53293f959e52cc111b54d39d8c94b6520bf5c989",
    "experiments/d13-rolling-backtest/images/preview-280/d13-01_origins.png": "247a88ebd7018f33645452c1ebe4da91e88a0100f149e0fc212674ace6d04b5e",
    "experiments/d13-rolling-backtest/images/preview-280/d13-02_revisions.png": "51c7866063c24e1285e221433cbd5ba3f0085d9911936fcb7f2bc732d048f95b",
    "experiments/d13-rolling-backtest/images/preview-280/d13-03_stockout.png": "d0b36e84caf7d8b321e5ce90e50a53bb3e19c558e2040a1d5d4557d8f0fb9b58",
    "experiments/d13-rolling-backtest/images/preview-350/d13-00_cover.png": "939b3ee31adfd12e3508eceed32206b9325cc1b5e64530b444db38605c5128f4",
    "experiments/d13-rolling-backtest/images/preview-350/d13-01_origins.png": "6ba602b28949a81a737054eba8d9f2ab01d7a88d425a7ca2061123f507762bb9",
    "experiments/d13-rolling-backtest/images/preview-350/d13-02_revisions.png": "0b03e6029e9926defce6a06317d8576c15a4f604928b75f9bfdc1f7686fa9c0f",
    "experiments/d13-rolling-backtest/images/preview-350/d13-03_stockout.png": "afb96083ac3a3cdeebedd77f728987487f1dea7e08f94d88eee1fe94f736e87c",
    "experiments/d13-rolling-backtest/practice/MANIFEST.sha256": "b6628f22a863675b983c34ece8eadcfd034622f347d663bc350eed946bfa2006",
    "experiments/d13-rolling-backtest/practice/README.md": "32f275a5a98e07b74f20a397b6f551148236fdede8b2440da2d45b78dfb238bf",
    "experiments/d13-rolling-backtest/practice/baseline.py": "f9631b4753439da9c207306ebf16de8c251a9b5c10f7a1a50c010de60ae2c90b",
    "experiments/d13-rolling-backtest/practice/data/apparel-development.csv": "56badd2fc37decd72b2f55a980acb7add2594b96c7b8d269f6aaae59ee7d47e5",
    "experiments/d13-rolling-backtest/practice/data/hewei-development.csv": "292072a63439529f22a73d41b83516928ae5a5b474b907b33d42e74962c23407",
    "experiments/d13-rolling-backtest/practice/metrics.py": "ecb4d15e0a46f272e9b954cb8bb42a4c22542117c9f1b90b2c3c8aaf052b23c3",
    "experiments/d13-rolling-backtest/practice/results/frozen_selection.json": "49c30c39c21dd3f2268743c4a31824dc4b0ebeec936d1c81e80b612be634a23f",
    "experiments/d13-rolling-backtest/practice/results/leakage_diagnostics.csv": "7dfcf056b3b687f1c8e06f4660c1a938bcd78173061e169ba6dc30fb3730f17d",
    "experiments/d13-rolling-backtest/practice/results/metrics.csv": "d5421abb6dc567ba4a431c45713e03f0e038557c4427df048e02556a3df87aef",
    "experiments/d13-rolling-backtest/practice/results/negative_control.json": "ccfeffb0e7ec840a27788e550ed4fc4c5c0f6c4af28b91783fcec32dda5d726f",
    "experiments/d13-rolling-backtest/practice/results/predictions.csv": "3e23a2dc6a69880e02864d88192f671c3ce88eb32d73540716dbba78bf45aecb",
    "experiments/d13-rolling-backtest/practice/results/run_manifest.json": "f15a366e3e28f5475831922b75ae62199fc55e4db1bf51a0f8b01d387cad885d",
    "experiments/d13-rolling-backtest/practice/results/stockout_metrics.csv": "94b1ed2797ac658bfc37d6f190de4d6c3ed655f7afd4efbebcb0736ec0ffdd68",
    "experiments/d13-rolling-backtest/practice/results/stockout_simulation.csv": "125758a180f33a64096ada34d2ab855165a9c2d92564518372a7c93f34a3f28b",
    "experiments/d13-rolling-backtest/practice/results/window_totals.csv": "650b120923de275485dcabcf09b370ea3cef13480babd2c454166e3ce61ea82d",
    "experiments/d13-rolling-backtest/practice/run.py": "640efed76a08a58c263209823483de231f05dad643ae653526da70cb3ee7ca5d",
    "experiments/d13-rolling-backtest/practice/source_manifest.json": "1058e120ac4c2d9b2d8e41ac6e5211cec6e7c07f34cc9ce58a25e60d26cd1261",
    "experiments/d13-rolling-backtest/practice/test_backtest.py": "407300b6b758ff90fcf09efbb7f6cdbf80155ad905fd6c4c1a887ea020e2bc90",
    "content/blog/rolling-backtest-stockout-censoring/images/d13-00_cover.png": "b706f84f877022c6e3e218900c557bfbe8d665cfec160a47c3e2e6d0af8d2f46",
    "content/blog/rolling-backtest-stockout-censoring/images/d13-01_origins.png": "89e1d46f98827d4784adc8384bff9f20e9ba9607a6601f53cdd053d46422ecf4",
    "content/blog/rolling-backtest-stockout-censoring/images/d13-02_revisions.png": "83c804fbd957a50c827a6c0c56a8e2a2e7b71892bcb93a10a260c00de6fe8b3f",
    "content/blog/rolling-backtest-stockout-censoring/images/d13-03_stockout.png": "e40e2776c4089551adbbd8b18bf59670e220b53a9936ea09d8872b96562d0d49",
    "content/blog/rolling-backtest-stockout-censoring/index.md": "2630744df203c73ffb2d24b2e9cb0d24106db201c4e36c1fe857d2dfeedc65df",
    "scripts/package-d13.py": "a40d25fb513bc35e2f51052a2f059b7014ae11e0ca09d2d63f1c08dbe020f137",
    "static/downloads/d13-rolling-backtest-article.zip": "1f9247ceea88beeb51e0902341bf73fa40a9b51d6e0efa2a16fbd0bde3733317",
    "static/downloads/d13-rolling-backtest-images.zip": "cf112cad7e5ab481f44f0395b996c980e6e639c865e0e9a980876d5bd817555b",
    "static/downloads/d13-rolling-backtest-practice.zip": "6bafac220cad3a33e86d5486a6ea45f512d4d4a24f64071bb8a33d28d263d7dc"
  }
}

~~~~
