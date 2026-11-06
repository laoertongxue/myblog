{
  "title": "聚合复购窗口与先行指标滚动回归",
  "description": "聚合复购窗口与先行指标滚动回归：这里补齐生鲜基地到门店、鞋服地域颜色尺码、延迟制造、促销透支、活动类比、制造备件及医药聚合预测之间原来未展开的步骤。所有企业、商品、事件、数据、时间和参数均为明确构造的模拟。没有真实业务数据，没有连接采购、生产、财务、配送或医疗系统。本课中",
  "type": "forecast",
  "unit": "industry-aggregate-repurchase-leading-ols",
  "weight": 101,
  "outputs": [
    "HTML"
  ]
}

<p class="check">R2独立验收的行业教学扩展。<a href="/forecast/forecast-industry-gap-labs.zip" download>下载行业9课实验包</a>。所有数据均模拟；匿名模拟聚合购买事件，无患者/处方/治疗判断，固定滞后不证明因果。</p><details><summary>共同阅读约定</summary><h2 id="行业多层级预测与决策补课">行业多层级预测与决策补课</h2>
<p>这里补齐生鲜基地到门店、鞋服地域颜色尺码、延迟制造、促销透支、活动类比、制造备件及医药聚合预测之间原来未展开的步骤。所有企业、商品、事件、数据、时间和参数均为明确构造的模拟。没有真实业务数据，没有连接采购、生产、财务、配送或医疗系统。本课中的“订单”“分录”“锁产”均为离线建议或教学账，不代表已经执行。</p>
<p>R2补强了输入校验：重复主键、矛盾的组级份额、超出固定需求模板会报错；时间序列按时间键计算，不依赖CSV行顺序。默认手算答案不变。</p>
<p>先完成百分比、加权平均、库存收支和训练集/验证集的基础课，再按本课顺序学习。每课建议60到90分钟：读业务问题、逐项手算、跑代码、修改一个输入、写边界。数学只用高一可读的代数与概率；需要最小二乘时会解释其含义，代码负责重复算术，不把“调用了一个函数”当作理解。</p>
<p>项目包 forecast-industry-gap-labs.zip 只需 Python 3.10
或更新版本的标准库。解压并进入目录后执行：</p>
<div class="sourceCode" id="cb1"><pre class="sourceCode sh"><code class="sourceCode bash"><span id="cb1-1"><a href="#cb1-1" aria-hidden="true" tabindex="-1"></a><span class="ex">python</span> run_all.py</span>
<span id="cb1-2"><a href="#cb1-2" aria-hidden="true" tabindex="-1"></a><span class="ex">python</span> <span class="at">-m</span> unittest <span class="at">-v</span> test_industry</span>
<span id="cb1-3"><a href="#cb1-3" aria-hidden="true" tabindex="-1"></a><span class="ex">python</span> manufacture_pharma.py self-test</span></code></pre></div>
<p>首次解压已含模拟CSV。run_all.py仅重算，不覆盖输入。要另建一份原始输入，运行
<code>python generate_all.py --data fresh_data</code>，随后用
<code>python run_all.py --data fresh_data --out fresh_outputs</code>
重算。生成器拒绝覆盖非空目录；先复制目录再改参。生成数据与运行模型是两步，脚本输出由CSV计算，不从教材答案回填。统一参考结果在
outputs/，子项目结果在
outputs/manufacture_pharma/。仅运行上面第一条不等于跑过测试。</p>
</details><h2 id="行业补课九-从聚合间隔生成复购窗口并拟合先行回归">行业补课九
从聚合间隔生成复购窗口并拟合先行回归</h2>
<p>稳定
slug：<code>industry-aggregate-repurchase-leading-ols</code>。来源：C19，第二部分
L69。建议时间：两个 45 分钟单元，作业 30 分钟。</p>
<h3 id="本课只研究匿名聚合的流通量">1 本课只研究匿名聚合的流通量</h3>
<p>本课演示两个独立的需求准备问题：依据购买间隔的汇总分布估计下一段时间的复购次数；依据模拟外部指数预测每周聚合销量。两部分不把同一批需求重复相加，也不自动合成一个总预测。</p>
<p>所有队列、流感代理指数和气象代理指数都是人为构造。没有患者姓名、健康状况、处方、用药方案、个体购买记录或真实疾病监测数据；不据此调整个人用药、诊断、治疗或发送患者提醒。即使真实汇总数据也可能有小单元格和再识别风险，上线前仍需专门的数据治理。本项目没有做实际数据的匿名化认证。</p>
<h3 id="从间隔直方图生成窗口">2 从间隔直方图生成窗口</h3>
<p>“直方图”在这里就是“每种间隔出现多少次”的汇总。不是预先把人硬塞到购买窗口里。</p>
<table>
<thead>
<tr class="header">
<th style="text-align: right;">两次购买间隔 d</th>
<th style="text-align: right;">汇总次数 n_d</th>
<th style="text-align: right;">概率 p_d</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td style="text-align: right;">14 天</td>
<td style="text-align: right;">10</td>
<td style="text-align: right;">0.10</td>
</tr>
<tr class="even">
<td style="text-align: right;">21 天</td>
<td style="text-align: right;">20</td>
<td style="text-align: right;">0.20</td>
</tr>
<tr class="odd">
<td style="text-align: right;">28 天</td>
<td style="text-align: right;">40</td>
<td style="text-align: right;">0.40</td>
</tr>
<tr class="even">
<td style="text-align: right;">35 天</td>
<td style="text-align: right;">20</td>
<td style="text-align: right;">0.20</td>
</tr>
<tr class="odd">
<td style="text-align: right;">42 天</td>
<td style="text-align: right;">10</td>
<td style="text-align: right;">0.10</td>
</tr>
<tr class="even">
<td style="text-align: right;">合计</td>
<td style="text-align: right;">100</td>
<td style="text-align: right;">1.00</td>
</tr>
</tbody>
</table>
<p>d 是天数，n_d 是间隔为 d 天的汇总次数；总数 N=100，概率
<code>p_d=n_d/N</code>。比如 p_28=40/100=0.4，表示模型给“间隔 28
天”的概率为 40%。这些概率由表计算，不是对单个购买者的确定承诺。</p>
<p>本课假设每个队列成员最终会有一次下一次购买，间隔服从这张完整分布。这是简化条件。实际数据若只收集已经复购的人，会漏掉尚未观察到复购或从此不复购的人，产生完成间隔选择偏差；应考虑删失、流失与竞争事件，不能直接照搬这张表。</p>
<h4 id="最短-80-窗口怎样计算">2.1 最短 80% 窗口怎样计算</h4>
<p>目标是找一个连续的天数区间，使其中概率之和至少达到
80%，且区间宽度最小；宽度相同时选起点更早的区间。起点与终点都包含在区间内。</p>
<ul>
<li>21 至 28 天：20%+40%=60%，不够。</li>
<li>28 至 35 天：40%+20%=60%，也不够。</li>
<li>21 至 35 天：20%+40%+20%=80%，宽度 14 天。</li>
<li>14 至 28 天：10%+20%+40%=70%，不够。</li>
</ul>
<p>所以生成的最短窗口为购买后第 21 至 35 天，概率质量
80%。它不是对每个人都适用的“医嘱周期”。离散分布下最短窗口的实际概率可能超过目标，例如条件分布中的
88.89%，程序会报告实际质量，不硬写成 80%。</p>
<p>代码 <code>shortest_window</code>
枚举所有起点、累加各个终点，第一次达到目标后记录候选，再按“宽度、起点、终点”排序选最小。这里仅五个不同天数，直接枚举容易理解且足够快。</p>
<h3 id="已经等了一段时间的人要用条件概率">3
已经等了一段时间的人要用条件概率</h3>
<p>现在到第 20 天，计划接下来七天，即第 21 至 27 天的聚合复购。</p>
<table>
<colgroup>
<col style="width: 13%" />
<col style="width: 17%" />
<col style="width: 17%" />
<col style="width: 17%" />
<col style="width: 17%" />
<col style="width: 17%" />
</colgroup>
<thead>
<tr class="header">
<th>队列</th>
<th style="text-align: right;">上次购买日</th>
<th style="text-align: right;">最初人数</th>
<th style="text-align: right;">截止日已复购人数</th>
<th style="text-align: right;">还未复购人数</th>
<th style="text-align: right;">当前已等待</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>A</td>
<td style="text-align: right;">0</td>
<td style="text-align: right;">100</td>
<td style="text-align: right;">10</td>
<td style="text-align: right;">90</td>
<td style="text-align: right;">20 天</td>
</tr>
<tr class="even">
<td>B</td>
<td style="text-align: right;">7</td>
<td style="text-align: right;">80</td>
<td style="text-align: right;">0</td>
<td style="text-align: right;">80</td>
<td style="text-align: right;">13 天</td>
</tr>
<tr class="odd">
<td>C</td>
<td style="text-align: right;">14</td>
<td style="text-align: right;">60</td>
<td style="text-align: right;">0</td>
<td style="text-align: right;">60</td>
<td style="text-align: right;">6 天</td>
</tr>
</tbody>
</table>
<p>这些仅为模拟聚合人数，表中没有任何个人标识。已复购人数是截止日已知的队列观测，不能用未来结果回填。</p>
<p>符号说明：</p>
<ul>
<li>T：从上次到下一次购买的间隔天数。</li>
<li>a：到今天已经等过的天数。</li>
<li>H：预测往后多少天，本例 7。</li>
<li>S(a)=P(T&gt;a)：模型中截至等待 a 天还未复购的比例。</li>
<li>N_remaining：实际仍未复购的队列人数，等于最初人数减截止日已复购人数。</li>
</ul>
<p>下一段时间的条件概率为：</p>
<p><code>p_next = P(a&lt;T≤a+H) / P(T&gt;a)</code></p>
<p><code>预计复购次数 = N_remaining × p_next</code></p>
<p>分母的作用是把已经发生的早期购买排除，只在“截至今天仍未复购”的人群内重新归一化。</p>
<h4 id="手算三个队列">3.1 手算三个队列</h4>
<p>A：a=20。模型中尚未复购概率=0.2+0.4+0.2+0.1=0.9。未来七天对应间隔 21
至 27，只有 21 天这一格，概率 0.2。条件概率=0.2/0.9=2/9；预计=90×2/9=20
次。</p>
<p>B：a=13。未来七天对应间隔 14 至 20，只有 14 天，概率
0.1；之前没有更早间隔，分母为 1。预计=80×0.1=8 次。</p>
<p>C：a=6。未来七天对应间隔 7 至 13，分布没有这个范围，预计=0。</p>
<p>合计=20+8+0=28 次。若错把 A 的 90 直接乘以无条件 20%，只得到 18
次，少算了条件分母。</p>
<p>日历窗口由上次购买日加间隔生成：A 为第 21 至 35 天，B 为第 28 至 42
天，C 为第 35 至 49 天。程序还会从剩余条件分布重新找最短窗口。A
的条件窗口仍为 21 至 35，但质量=0.8/0.9=88.8889%。</p>
<p>如果等待天数已超过分布最大值 42
天，仍有人未复购，则模型支持范围与队列现实冲突。程序报错提醒检查流失或间隔尾部，不能把分母
0 改成 1，也不能对剩余人群默默预测零需求。</p>
<h3 id="最小二乘回归必须从训练数据求系数">4
最小二乘回归必须从训练数据求系数</h3>
<p>第二部分是每周聚合销量。不能先编出系数，再称它是训练结果。</p>
<p>设 t 为要预测的周；在 t−1 周末生成预测。预先约定使用：</p>
<ul>
<li>x_1,t：t−2 周的模拟流感代理指数。</li>
<li>x_2,t：t−3 周的模拟气象代理指数。</li>
<li>y_t：第 t 周的聚合实际销量，单位件。</li>
<li>b_0：截距，即指数都为 0
时直线模型的基准项，本例不把这种外推解释成实际销量。</li>
<li>b_1、b_2：斜率，表示其他输入相同时，某指数增加 1
个指数点，对预测值的模型变化。</li>
<li>ŷ_t：模型预测值。</li>
</ul>
<p>模型为：</p>
<p><code>ŷ_t = b_0 + b_1×x_1,t + b_2×x_2,t</code></p>
<p>“lag 2”表示用两周前的事件期，“lag
3”表示三周前；它不意味着数据已经发布。还必须检查
<code>known_at</code>。</p>
<h4 id="用最简单的数字理解拟合">4.1 用最简单的数字理解拟合</h4>
<p>先看只有一个 x 的例子：x 为 1、2、3，y 为 3、5、7。x 的平均为 2，y
的平均为 5。直线斜率可按：</p>
<p><code>b_1 = Σ[(x−平均x)×(y−平均y)] / Σ[(x−平均x)²]</code></p>
<p>Σ
是求和符号，意思是把每一行结果相加。分子=(-1)×(-2)+0×0+1×2=4，分母=1+0+1=2，所以
b_1=2。截距 b_0=平均y−b_1×平均x=5−2×2=1。预测式为 1+2x。</p>
<p>两特征手算用四行：</p>
<table>
<thead>
<tr class="header">
<th style="text-align: right;">x_1</th>
<th style="text-align: right;">x_2</th>
<th style="text-align: right;">y</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td style="text-align: right;">0</td>
<td style="text-align: right;">0</td>
<td style="text-align: right;">5</td>
</tr>
<tr class="even">
<td style="text-align: right;">1</td>
<td style="text-align: right;">0</td>
<td style="text-align: right;">7</td>
</tr>
<tr class="odd">
<td style="text-align: right;">0</td>
<td style="text-align: right;">1</td>
<td style="text-align: right;">8</td>
</tr>
<tr class="even">
<td style="text-align: right;">1</td>
<td style="text-align: right;">1</td>
<td style="text-align: right;">10</td>
</tr>
</tbody>
</table>
<p>第一行给 b_0=5；第二行减第一行给 b_1=2；第三行减第一行给
b_2=3；第四行核对 5+2+3=10。程序 <code>fit_ols</code> 会从这四行计算出
<code>[5,2,3]</code>，不是把答案预写进去。</p>
<p>实际数据通常没有这样完美的直线。残差 e_i=y_i−ŷ_i，平方 e_i²
可以防止正负抵消。最小二乘就是选 b_0、b_1、b_2，使所有训练行的残差平方和
<code>Σe_i²</code> 最小。</p>
<p>对于两特征，代码形成三个联立方程：</p>
<p><code>n×b_0 + (Σx_1)×b_1 + (Σx_2)×b_2 = Σy</code></p>
<p><code>(Σx_1)×b_0 + (Σx_1²)×b_1 + (Σx_1x_2)×b_2 = Σ(x_1y)</code></p>
<p><code>(Σx_2)×b_0 + (Σx_1x_2)×b_1 + (Σx_2²)×b_2 = Σ(x_2y)</code></p>
<p>n 为训练行数。求和中的 i
为行号，在式子中省略。代码用带选主元的高斯消元解方程。你不必先掌握矩阵，只要知道它确实把每行训练值累加进方程，再求未知系数。若输入特征完全重合、无法区分斜率，方程可能无唯一解，程序不伪造系数，转入明确基线回退。大型或病态矩阵更适合
QR/SVD，这个小程序不声称具有生产级数值稳定性。</p>
<h3 id="known_at-让预测只能看见当时的信息">5 known_at
让预测只能看见当时的信息</h3>
<p><code>leading_indicator_vintages.csv</code> 包含：</p>
<ul>
<li><code>series</code>：flu_proxy 或
weather_proxy，只是模拟指数名。</li>
<li><code>event_week</code>：指数描述的是哪周。</li>
<li><code>known_at_week</code>：该版本哪周可获得。</li>
<li><code>version</code>：第一发布版或后续修订版。</li>
<li><code>value</code>：指数值，单位是指数点，不是病例人数或摄氏度。</li>
</ul>
<p>通常首发比事件期晚一周；flu 每逢事件周是 11 的倍数，再晚一周；weather
每逢事件周是 13
的倍数，再晚两周。修订版在事件周后五周发布，并人为把指数加
2，用来测试误用最终版本的问题。</p>
<p>销量标签也延迟一周发布：<code>pharma_weekly_demand.csv</code> 的第 t
周销量在 t+1 周才知道。预测第 t 周时，截止 t−1，因此通常最多知道第 t−2
周销量。不能把 y_(t−1) 当作必然已知。</p>
<h4 id="第-41-周的完整时间线">5.1 第 41 周的完整时间线</h4>
<p>预测时间为第 40 周：</p>
<ol type="1">
<li>流感代理取事件周 39，首发 known_at=40，可用。</li>
<li>气象代理取事件周 38，首发 known_at=39，可用。</li>
<li>39 周销量 known_at=40，可用于训练；40 周销量
known_at=41，不可用。</li>
<li>每条历史训练行也还原该行自己的预测时点。例如预测历史第 j
周的特征只允许 known_at≤j−1。后来修订的数据不能回填旧快照。</li>
<li>删除历史上当时缺少任一特征的训练行，得到 32
条合法训练行，实际拟合系数约为 39.629099、1.194958、−0.760770。</li>
<li>输入指数约为 24.85 和
15.161342，预测=39.629099+1.194958×24.85−0.760770×15.161342≈57.789510
件。该周后来公布实际为 59。</li>
</ol>
<p>这些系数由真实运行计算得到。模拟销量的生成式包含一个人为的先行关系，用于让学习者看见拟合过程，但程序没有把生成式的系数直接拿来预测。</p>
<h4 id="第-42-周遇到迟报怎么办">5.2 第 42 周遇到迟报怎么办</h4>
<p>预测时点为第 41 周。weather 需要事件周 39；39 是 13
的倍数，首发已知时间为 39+3=42，截止第 41 周还没有。程序明确输出
<code>FALLBACK_LAST_AVAILABLE</code>，使用当时最后已发布销量，即第 40
周的 47 件。它不填入未来指数，不删掉这个难预测的测试周。</p>
<p>一条外部指数“描述过去”并不等于“当时已知”。<code>known_at</code>
过滤必须在拿数时发生，不能只在图表上写一句“没有数据泄漏”。</p>
<h3 id="逐周滚动验证和同目标基线">6 逐周滚动验证和同目标基线</h3>
<p>默认评价第 41 至 80 周，共 40 个目标周。每一周重复：</p>
<ol type="1">
<li>把预测截止设为目标前一周。</li>
<li>只用截止前已经公布的历史销量。</li>
<li>从固定历史快照取得合法特征。</li>
<li>用到目前为止的全部合法训练行重新拟合 OLS，称为扩展窗口。</li>
<li>当前特征缺失或训练不足/奇异时使用明确回退。</li>
<li>在后来实际发布后评价该目标周。</li>
</ol>
<p>lag 2 与 lag 3 是实验开始前声明的，不在 40
周测试结果中挑选。若以后尝试多个
lag，应再划分更早的验证期选参，保留新的最终测试期，不能挑完最好的 lag
后仍称同一时期“从未见过”。这里的滚动验证是逐时点回放评估，不是随机切分。</p>
<p>比较三种方法，三者都评价相同 40 周：</p>
<ul>
<li>OLS 加明确回退，包含 34 次 OLS 预测、6 次迟报回退。</li>
<li>Last_available_label：最后已发布的一周实际销量。</li>
<li>Last_four_available_mean：最后四个已发布周销量的平均数。</li>
</ul>
<p>评价符号：F_t 为预测、A_t 为实际、n
为评价周数；MAE=Σ|F_t−A_t|/n，单位件；RMSE=√[Σ(F_t−A_t)²/n]，对大误差惩罚更强；WAPE=Σ|F_t−A_t|/ΣA_t；Bias=Σ(F_t−A_t)/ΣA_t，正数为总体高估。|
| 表示绝对值，√表示平方根。实际总量为零时 WAPE 和 Bias
留空，不能除以零。</p>
<p>默认数据实跑：</p>
<table>
<thead>
<tr class="header">
<th>方法</th>
<th style="text-align: right;">周数</th>
<th style="text-align: right;">MAE 件</th>
<th style="text-align: right;">RMSE 件</th>
<th style="text-align: right;">WAPE</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>OLS 加回退</td>
<td style="text-align: right;">40</td>
<td style="text-align: right;">1.934583</td>
<td style="text-align: right;">2.981336</td>
<td style="text-align: right;">3.197657%</td>
</tr>
<tr class="even">
<td>最后已发布销量</td>
<td style="text-align: right;">40</td>
<td style="text-align: right;">4.850000</td>
<td style="text-align: right;">5.928744</td>
<td style="text-align: right;">8.016529%</td>
</tr>
<tr class="odd">
<td>最后四周已发布均值</td>
<td style="text-align: right;">40</td>
<td style="text-align: right;">6.743750</td>
<td style="text-align: right;">7.903026</td>
<td style="text-align: right;">11.146694%</td>
</tr>
</tbody>
</table>
<p>这是为教学而生成了相关关系后的模拟结果，只说明实现能使用这种关系。不能据此宣称真实医药业务改善
多少%、公共卫生指数有因果作用、或回归永远优于简单基线。模型只输出离线预测，没有改变下单或治疗。</p>
<h3 id="输入输出与代码阅读顺序">7 输入输出与代码阅读顺序</h3>
<p>复购部分：</p>
<ol type="1">
<li><code>repurchase_histogram.csv</code>：间隔天数与汇总频数。</li>
<li><code>repurchase_parameters.csv</code>：截止日 20、向后 7
天、窗口概率目标
0.8；<code>histogram_known_at_day=0</code>，须不晚于截止日。</li>
<li><code>repurchase_cohorts.csv</code>：最后购买日、初始人数、截止已复购人数与已知日。</li>
<li><code>repurchase_windows.csv</code>：年龄、剩余人数、无条件窗口、条件窗口、真实覆盖概率、条件分母、未来七天概率及预计复购。</li>
</ol>
<p>回归部分：</p>
<ol type="1">
<li><code>ols_parameters.csv</code>：评价周 41 至 80、两个
lag、最少训练行 12。</li>
<li><code>leading_indicator_vintages.csv</code>：83
个事件周，每周两个指数、每指数两个版本，共 332 行。</li>
<li><code>pharma_weekly_demand.csv</code>：80
周聚合销量与发布时间。</li>
<li><code>ols_historical_asof_features.csv</code>：80
条历史目标快照，保留每个特征的来源周、发布时间、版本与可用性。</li>
<li><code>ols_rolling_predictions.csv</code>：40
次预测的截止周、训练行数、最后训练标签期、标签可得时点、系数、预测、基线、实际与回退模式。</li>
<li><code>ols_rolling_metrics.csv</code>：三方法在同一 40
周的指标。</li>
</ol>
<p>建议代码顺序：先读 <code>distribution</code> 与
<code>shortest_window</code>，再读 <code>repurchase</code>；先读
<code>asof_indicator</code> 和 <code>feature_row</code>，再读
<code>fit_ols</code>，最后读
<code>rolling_ols</code>。<code>generate_inputs</code>
只负责构造例题，<code>run</code> 才是读取已有 CSV
的计算入口，两者不可混用。</p>
<h3 id="本课作业与精确验收">8 本课作业与精确验收</h3>
<ol type="1">
<li><strong>从原始频数生成。</strong> 无条件最短窗口应为 21 至 35
天，质量 0.8；三个队列未来七天预计为 20、8、0，合计 28；A 的条件概率应为
2/9。允许绝对误差 0.000001。</li>
<li><strong>改变期限。</strong> 只把 <code>forecast_days</code> 从 7
改为 14，重新运行。A 未来间隔 21 和 28，预计 60；B 为 14 和 21，预计
24；C 为 14，预计 6，合计 90 次。修改后的输入必须保留，不被
<code>run</code> 改回 7。</li>
<li><strong>检查拟合而不是硬编码。</strong> 向 <code>fit_ols</code>
输入四行特征 <code>[0,0]、[1,0]、[0,1]、[1,1]</code>，目标
<code>[5,7,8,10]</code>，返回系数应为 <code>[5,2,3]</code>。把所有目标加
4 后截距应为 9，两条斜率不变。</li>
<li><strong>检查时间边界。</strong> 40 行预测中，每个非空特征的 known_at
都不晚于 origin；每次训练使用的最大标签 known_at 也不晚于
origin；最后训练标签周不晚于目标周减 2。第 42 周必须回退，不能偷用第 42
周才发布的气象指数。</li>
<li><strong>检查评价公平性。</strong> 三模型评价行数都为 40，OLS 路线中
34 次回归、6 次回退。不得只在 34 个成功预测周上报结果，却和基线的 40
周指标比较。</li>
<li><strong>检查未来不影响过去。</strong> 固定第 41 周预测，把所有
known_at&gt;40 的指数值和销量标签各加
10000，再算该周预测。预测值应不变；评价所用未来实际可以变化，因此不要要求误差也不变。内置测试执行此反例。</li>
<li><strong>检查版本。</strong> 默认两个 lag
都只可能在预测时看到首发版，非空的 <code>flu_version</code> 应全为
1。把修订最终值不分时间地连接回历史属于信息泄漏。</li>
<li><strong>检查失效边界。</strong>
把一个仍有剩余人数的队列上次购买日改成 −30，截止日 20 意味着已等 50
天，超过分布最大 42
天，应报错。解释需要补充流失或尾部模型，不能从本例推断这些人不再需要任何商品。</li>
</ol>
<h3 id="制造医药子项目验收与边界">制造医药子项目验收与边界</h3>
<p>默认项目有 17 张输入 CSV、10 张结果 CSV 和一个结果 JSON。运行
<code>self-test</code> 应返回 <code>passed: true</code>，默认代码含 48
项实质检查。整合时可增加检查，不应删除冻结、守恒、时间边界、输入保留和未来扰动检查。</p>
<p>默认数值比较采用绝对误差
0.000001；产权数量、冻结数量、行数、输入不覆写应精确一致。重复
<code>run</code>
在相同运行环境中生成的结果字节应一致。跨平台最后几位浮点数可能略有差别，应使用数值容差比较而非把最后一位当业务差异。</p>
<p>三课共同的合格标准是：能指出输入在哪里，能解释每个主要符号与单位，能用纸笔复算关键数值，能改输入得到正确变化，能让违反假设的输入失败，能清楚说出模型没有证明什么。代码运行成功只是其中一项。</p>
