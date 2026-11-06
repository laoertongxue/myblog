{
  "title": "设备入退网与三阶段浴盆先验",
  "description": "设备入退网与三阶段浴盆先验：这里补齐生鲜基地到门店、鞋服地域颜色尺码、延迟制造、促销透支、活动类比、制造备件及医药聚合预测之间原来未展开的步骤。所有企业、商品、事件、数据、时间和参数均为明确构造的模拟。没有真实业务数据，没有连接采购、生产、财务、配送或医疗系统。本课中",
  "type": "forecast",
  "unit": "industry-installed-base-bathtub",
  "weight": 100,
  "outputs": [
    "HTML"
  ]
}

<p class="check">R2独立验收的行业教学扩展。<a href="/forecast/forecast-industry-gap-labs.zip" download>下载行业9课实验包</a>。所有数据均模拟；修复设备、每月一次故障指示，先验非真实拟合可靠性曲线。</p><details><summary>共同阅读约定</summary><h2 id="行业多层级预测与决策补课">行业多层级预测与决策补课</h2>
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
</details><h2 id="行业补课八-从入退网队列算分龄备件需求">行业补课八
从入退网队列算分龄备件需求</h2>
<p>稳定
slug：<code>industry-installed-base-bathtub</code>。来源：C17，§3.5
L125。建议时间：50 分钟学习，25 分钟实验。</p>
<h3 id="保有量不是出厂累计销量">1 保有量不是出厂累计销量</h3>
<p>Installed Base 是某个时点仍在使用的设备集合。累计卖出 1000
台，可能已有一部分退网，新的设备也可能刚安装。备件预测需要知道“还在服役的设备有多少、分别多老”，而不只知道历史销量。</p>
<p>本课不用单台序列号。把同月安装、使用同一先验的设备合成一个队列
cohort。队列记录的是匿名设备数量，不是个人信息。</p>
<p>每月先做四步：</p>
<ol type="1">
<li>读上月末仍在网数量。</li>
<li>加本月月初入网、减本月月初退网。</li>
<li>按安装月份计算年龄，把队列分进早期、稳定、磨损阶段。</li>
<li>每组数量乘本月故障概率、服务覆盖比例、每次故障用件量，再合计。</li>
</ol>
<p>这里假设月初完成入退网，当月全部设备有完整一个月的风险暴露。若实际在月中安装，必须按设备天数等方式折算暴露，本例没有这么做。</p>
<h3 id="入退网和分龄的逐符号公式">2 入退网和分龄的逐符号公式</h3>
<p>对队列 c、月份 t：</p>
<ul>
<li>N_start,c,t：本月月初调整前在网数量，单位台。</li>
<li>E_c,t：本月新入网台数。</li>
<li>R_c,t：本月退网台数。</li>
<li>N_c,t：调整后的当月风险暴露台数。</li>
<li>m_c：该队列安装的月份编号。</li>
<li>a_c,t：月龄，即自安装经过了几个完整月。</li>
</ul>
<p><code>N_c,t = N_start,c,t + E_c,t − R_c,t</code></p>
<p><code>a_c,t = t − m_c</code></p>
<p>第 1 月安装的设备在第 1 月年龄为 0，在第 2 月年龄为 1，在第 4
月年龄为 3。月龄不要误写成“第几个月”的计数。</p>
<p>期初两组设备：安装于 −4 月的 200 台、安装于 −12 月的 50
台。负月份只是教学时间原点之前，不是负年龄。第 1 月又安装 100
台，并退掉老设备 10 台，因此当月在网=250+100−10=340 台。</p>
<p>退网不能超过当时在网数量。把 50 台老设备退掉 51
台必须报错。一次故障本例假设可以维修，<strong>不会自动从在网数量中扣减</strong>；更换整机退出必须另记退网事件。</p>
<h3 id="浴盆形状是一种先验">3 浴盆形状是一种先验</h3>
<p>“浴盆”描述一种可能的风险形状：新设备早期可能出现制造、安装问题，随后进入低故障期，老化后磨损风险增加。不是每类设备都呈这种形状，更不能把设备的浴盆曲线直接套到人的健康上。</p>
<p>本课用三段常数近似，不声称拟合了连续寿命分布：</p>
<table>
<thead>
<tr class="header">
<th>阶段</th>
<th>月龄 a</th>
<th style="text-align: right;">Beta 先验 α</th>
<th style="text-align: right;">Beta 先验 β</th>
<th style="text-align: right;">每台每月先验故障概率</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>early 早期</td>
<td>0、1、2</td>
<td style="text-align: right;">3</td>
<td style="text-align: right;">47</td>
<td style="text-align: right;">3/50=6%</td>
</tr>
<tr class="even">
<td>stable 稳定</td>
<td>3 至 11</td>
<td style="text-align: right;">1</td>
<td style="text-align: right;">99</td>
<td style="text-align: right;">1/100=1%</td>
</tr>
<tr class="odd">
<td>wear 磨损</td>
<td>12 及以上</td>
<td style="text-align: right;">4</td>
<td style="text-align: right;">96</td>
<td style="text-align: right;">4/100=4%</td>
</tr>
</tbody>
</table>
<p>α（alpha）可想象为先验的“故障支持量”，β（beta）为“未故障支持量”。它们表达建模前的信念强度，不是偷偷伪装成观测的真实设备。先验均值为
<code>h_0=α/(α+β)</code>，h_0 是本月发生至少一次目标故障的概率。</p>
<p>本课每台每月用一个“故障或未故障”指标，所以概率必须在 0 至
1。如果同一设备一个月会反复发生很多故障，需要计数过程或重复事件模型，不能直接把次数塞进这个二项式例子。</p>
<h4 id="可以用已知历史修正先验">3.1 可以用已知历史修正先验</h4>
<p>设 E_hist 为此前观测到的设备月暴露数，F_hist
为其中出现目标故障的设备月数，要求 F_hist≤E_hist。后验均值为：</p>
<p><code>h_1 = (α + F_hist) / (α + β + E_hist)</code></p>
<p>early 的此前历史为 50 个设备月、2 个故障设备月，所以：</p>
<p><code>h_1 = (3+2)/(3+47+50) = 5/100 = 5%</code></p>
<p>这是把先验支持与新证据相加。本课的历史全部在第 0 月已知；stable
历史为 100/1，后验仍为 1%；wear 历史为
25/2，后验=(4+2)/(4+96+25)=4.8%。输出同时保留先验版与后验版，不能混称同一组参数。</p>
<p>不同队列进入同一个阶段时共用该阶段先验。这里没有估计不同品牌、环境或维护策略的差别，也没有置信区间，因此是透明的小模型而非寿命认证。</p>
<h3 id="从故障概率换成备件需求">4 从故障概率换成备件需求</h3>
<p>设覆盖比例 c=0.8，表示 80%
的设备故障由本服务体系承担；每次目标故障平均使用 q=1
件备件。对每个队列：</p>
<p><code>预期用件量 = 在网台数 N × 故障概率 h × 覆盖比例 c × 每次用件量 q</code></p>
<p>然后把各队列相加。预期用件量允许为小数，它是很多可能结果的平均值，不是要求仓库发出
0.68
件实物。库存下单还需要考虑风险分位数、提前期、包装等，本课不直接输出订货量。</p>
<h4 id="第-1-月手算">4.1 第 1 月手算</h4>
<ul>
<li>新入网 100 台，年龄 0，early：100×0.06×0.8×1=4.8 件。</li>
<li>安装于 −4 月的 200 台，年龄 5，stable：200×0.01×0.8=1.6 件。</li>
<li>安装于 −12 月的 50 台，月初退出 10 台，年龄
13，wear：40×0.04×0.8=1.28 件。</li>
<li>先验合计=4.8+1.6+1.28=7.68 件。</li>
</ul>
<p>若忘记退网 10 台，会多算 10×0.04×0.8=0.32 件，得到 8
件。这个错误来自安装基数，而不来自需求模型公式。</p>
<p>后验版为 100×0.05×0.8 + 200×0.01×0.8 + 40×0.048×0.8=7.136 件。</p>
<h4 id="年龄会自动跨阶段">4.2 年龄会自动跨阶段</h4>
<p>第 1 月入网的队列到第 4 月年龄为 3，进入 stable。安装于 −4
月的队列到第 8 月年龄为 12，进入
wear。不能把“购买时属于新设备”标签永久贴在队列上。</p>
<p>完整 12 月还有：第 3 月稳定老队列退出 20 台；第 4 月入网 60 台；第 6
月第 1 月队列退出 5 台；第 7 月入网 40 台；第 9 月磨损老队列退出 15
台。第 12 月：</p>
<table>
<thead>
<tr class="header">
<th>队列</th>
<th style="text-align: right;">月龄</th>
<th style="text-align: right;">在网数</th>
<th>阶段</th>
<th style="text-align: right;">先验预期备件</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>old_stable</td>
<td style="text-align: right;">16</td>
<td style="text-align: right;">180</td>
<td>wear</td>
<td style="text-align: right;">5.76</td>
</tr>
<tr class="even">
<td>old_wear</td>
<td style="text-align: right;">24</td>
<td style="text-align: right;">25</td>
<td>wear</td>
<td style="text-align: right;">0.80</td>
</tr>
<tr class="odd">
<td>entry_1</td>
<td style="text-align: right;">11</td>
<td style="text-align: right;">95</td>
<td>stable</td>
<td style="text-align: right;">0.76</td>
</tr>
<tr class="even">
<td>entry_4</td>
<td style="text-align: right;">8</td>
<td style="text-align: right;">60</td>
<td>stable</td>
<td style="text-align: right;">0.48</td>
</tr>
<tr class="odd">
<td>entry_7</td>
<td style="text-align: right;">5</td>
<td style="text-align: right;">40</td>
<td>stable</td>
<td style="text-align: right;">0.32</td>
</tr>
<tr class="even">
<td>合计</td>
<td style="text-align: right;">不相加</td>
<td style="text-align: right;">400</td>
<td>不合并标签</td>
<td style="text-align: right;">8.12</td>
</tr>
</tbody>
</table>
<p>逐月的风险增加可能来自设备老化、入网或退网，不能只看总台数判断。</p>
<h3 id="输入输出字段">5 输入输出字段</h3>
<ul>
<li><code>installed_cohorts.csv</code>：<code>cohort</code>
为队列名，<code>installed_month</code>
为安装月，<code>opening_count_units</code> 为第 1
月之前已在网台数。未来队列期初为 0。</li>
<li><code>installed_movements.csv</code>：一条 ENTER 或 EXIT
事件、台数、发生月份和
<code>known_at_month</code>。程序在月初情景中使用本月已知事件，不提前把未来月的退网用于本月数量；<code>known_at_month</code>
晚于事件月的输入会被拒绝。本例不是“第 0
月已准确预知十二个月”的实际运营预测。</li>
<li><code>bathtub_priors.csv</code>：三段的 α、β；边界在
<code>age_stage()</code> 中明确为 3 月和 12 月。</li>
<li><code>bathtub_history.csv</code>：按阶段汇总的历史暴露、故障与已知月份；只能使用当月已知的历史。</li>
<li><code>installed_base_parameters.csv</code>：12 个月、覆盖
0.8、每故障 1 件。</li>
<li><code>installed_base_by_age.csv</code>：每月每队列的年龄、阶段、入退网、在网数和两种风险需求。</li>
<li><code>installed_base_monthly.csv</code>：各月汇总，用于核对数量守恒与需求变化。</li>
</ul>
<h3 id="本课作业与精确验收">6 本课作业与精确验收</h3>
<ol type="1">
<li>第 1 月在网应为 340，先验需求 7.68，后验需求 7.136；第 12 月在网
400，先验需求 8.12。需求的允许绝对误差为 0.000001。</li>
<li>检查每个队列每个月
<code>at_risk_units=opening_units+entered_units−exited_units</code>。所有队列必须满足，不能只检查总数。</li>
<li>写出年龄 2、3、11、12 的阶段，依次应是
early、stable、stable、wear。核对 <code>entry_1</code> 第 4 月和
<code>old_stable</code> 第 8 月实际跨段。</li>
<li>将第 1 月 old_wear 的退网数从 10 改成 0，重算第 1 月在网应为
350，先验需求应为 8.00；两次结果差正好 0.32 件。</li>
<li>保持原输入，把覆盖比例由 0.8 改为 0.5，第 1 月先验需求应为
4.80，设备数量仍为 340。覆盖是服务范围，不能当作设备报废比例。</li>
<li>将第 1 月 old_wear 的退出量改成 51，应报错。不能以
<code>max(0,...)</code> 悄悄吞掉不存在的设备退出。</li>
<li>解释为什么“故障 6%”不会自动让本例设备数乘以 94%，以及为何不能直接把
7.68
件四舍五入成唯一正确的采购量。答案必须提到可维修假设、风险平均值与库存决策不同。</li>
</ol>
