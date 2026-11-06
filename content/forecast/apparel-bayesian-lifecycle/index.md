{
  "title": "3 鞋服测款后验与生命周期追单",
  "description": "3 鞋服测款后验与生命周期追单：本课把白皮书中的温度动态货架期、鞋服贝叶斯测款与生命周期追单、VMI协同、生鲜小时缺货和联名首二配补成完整小实验。读者只需会百分比、乘除、比较大小和按时间记账。先用本文数字手算，再运行同目录项目包，最后故意修改输入，看结论是否随约束改变。",
  "type": "forecast",
  "unit": "apparel-bayesian-lifecycle",
  "weight": 78,
  "outputs": [
    "HTML"
  ]
}

<p class="check">R3模拟教学实验，16份CSV/149行。<a href="/forecast/forecast-industry-expanded.zip" download>下载行业机制扩展 R3</a>。温度风险不授权延长标签效期；缺货需求不可直接观测；VMI实物账与当时可见信息分开。程序结果不是自动补货、食品放行或实际收益证据。</p><details><summary>共同运行与验收方法</summary><h2 id="行业缺口补课与五个可复算实验">行业缺口补课与五个可复算实验</h2>
<p>本课把白皮书中的温度动态货架期、鞋服贝叶斯测款与生命周期追单、VMI协同、生鲜小时缺货和联名首二配补成完整小实验。读者只需会百分比、乘除、比较大小和按时间记账。先用本文数字手算，再运行同目录项目包，最后故意修改输入，看结论是否随约束改变。</p>
<p>所有企业、日期、温度、数量、参数和历史活动均为独立模拟。它们不是食品安全验证数据、真实商业预测或收益证据。脚本仅在本地读写CSV/JSON，不登录业务系统、不发采购单、不改标签效期、不放行食品、不调价或配送。</p>
<p>阅读顺序：小时销量与不可观测需求 → 温度累计与批次 →
测款概率与生命周期 → VMI物理账 →
联名分配。每节约60—90分钟：15分钟读题，20分钟手算，25分钟运行与改参，15分钟写清边界。不要先背模型名。</p>
<p>配套包为
forecast-industry-expanded-r3.zip。第三版补强小时完整性、实物与信息分账、主键/外键与活动时钟校验。解压后在包内依次执行：</p>
<div class="sourceCode" id="cb1"><pre class="sourceCode sh"><code class="sourceCode bash"><span id="cb1-1"><a href="#cb1-1" aria-hidden="true" tabindex="-1"></a><span class="ex">python</span> generate_data.py</span>
<span id="cb1-2"><a href="#cb1-2" aria-hidden="true" tabindex="-1"></a><span class="ex">python</span> run_labs.py</span>
<span id="cb1-3"><a href="#cb1-3" aria-hidden="true" tabindex="-1"></a><span class="ex">python</span> <span class="at">-m</span> unittest <span class="at">-v</span> test_labs</span></code></pre></div>
<p>仅需Python
3.10或更新版本的标准库。生成器会重建data中的原始模拟输入，因此想保留改参实验时先复制目录。run_labs.py始终从CSV重新算，数值不从固定答案抄回。参考结果在outputs/results.json，异常测试记录在outputs/test_report.txt。建议把原始版与改参版分别输出到不同目录：<code>python run_labs.py --data data --out outputs/my_run</code>。</p>
<p>本课覆盖白皮书§3.1的小时断货/清仓与温度轨迹、§3.2的测款/生命周期/返单、第二部分制造业VMI、§3.4的联名首二配。它不替代多级库存优化、两阶段面料、尺码纠偏、多层BOM、完整APS等其他课程，也不把这五个项目宣称为整本白皮书所有内容都已验收。</p>
<h2 id="完成标准与如何使用项目包">6 完成标准与如何使用项目包</h2>
<p>每节都要交四件东西：原始输入、逐符号手算、程序结果、假设和失败情景。脚本跑通不代表理解；会手算也不代表已验证模型有真实预测能力。</p>
<p>data内有16个CSV与config.json；输入记录共149行，不计表头和JSON。精确文件行数/字段见包内DATA_DICTIONARY.md与MANIFEST.json。outputs包含完整JSON、两份VMI逐事件账、小时估计、联名分配和测试记录。模拟真值文件只用于评分/回放，绝不能作为决策时点已知特征。</p>
<p>第三版55项正常路径和异常路径均由test_labs.py执行，包含独立审查发现问题的回归：温度缺测/晚到/标签截止；漏斗分母/无数据/季末到货；VMI延误/晚通知/守恒/待检；小时样本缺失/PV误用；联名晚到核销/重复事件/运力改变/非法时段份额。还共同拒绝NaN和无穷大。</p>
<p>课程采用的是可解释的最小模型，不要求每个领域都训练复杂网络。以后增加树模型、温度非线性模型或联合优化，仍必须保留这里的时点、单位、口径与库存账。任何“精度提高”“更安全”“利润改善”都需要另外设计真实数据验证或授权试验；本包不给这类外推结论。</p>
<p>概念出处：用户上传《供应链预测与计划全景白皮书》的行业场景。原文未核实的收益比例没有转写为事实。Beta—二项共轭、区间累计和库存收支式是本课明确给定模型的数学推导；所有具体参数及数值由本包模拟生成。范围索引：C01/C02小时缺货与清仓、C04温度累计、B02/C08测款到返单、B05的VMI子机制、C14联名首二配。</p>
</details><h2 id="鞋服测款后验与生命周期追单">3 鞋服测款后验与生命周期追单</h2>
<h3 id="先分清漏斗与件数">3.1 先分清漏斗与件数</h3>
<p>本例新品X在第0日上架，第3日结束72小时观察后决定是否追单。库存表明确款号style与上架时点launch_at，只允许一款和一条库存快照；生命周期第一段起点必须等于(origin−launch_at)换算的天数。只改决策日期而不改阶段窗口会被拒绝，不能仍从第3日机械算交期。原白皮书“上架前72小时”与使用上架后转化信息相冲突，本课明确使用上架后72小时，不据原文歧义倒填数据。</p>
<p>三行是三个不重叠的24小时窗口：</p>
<table>
<colgroup>
<col style="width: 8%" />
<col style="width: 11%" />
<col style="width: 11%" />
<col style="width: 11%" />
<col style="width: 11%" />
<col style="width: 11%" />
<col style="width: 11%" />
<col style="width: 11%" />
<col style="width: 11%" />
</colgroup>
<thead>
<tr class="header">
<th>窗口</th>
<th style="text-align: right;">曝光</th>
<th style="text-align: right;">点击</th>
<th style="text-align: right;">加购会话</th>
<th style="text-align: right;">收藏会话</th>
<th style="text-align: right;">合格独立会话n</th>
<th style="text-align: right;">首单件数x</th>
<th style="text-align: right;">缺货点击</th>
<th style="text-align: right;">重复点击</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>0—24小时</td>
<td style="text-align: right;">1000</td>
<td style="text-align: right;">100</td>
<td style="text-align: right;">25</td>
<td style="text-align: right;">20</td>
<td style="text-align: right;">80</td>
<td style="text-align: right;">8</td>
<td style="text-align: right;">10</td>
<td style="text-align: right;">10</td>
</tr>
<tr class="even">
<td>24—48小时</td>
<td style="text-align: right;">1600</td>
<td style="text-align: right;">160</td>
<td style="text-align: right;">40</td>
<td style="text-align: right;">32</td>
<td style="text-align: right;">120</td>
<td style="text-align: right;">18</td>
<td style="text-align: right;">25</td>
<td style="text-align: right;">15</td>
</tr>
<tr class="odd">
<td>48—72小时</td>
<td style="text-align: right;">2000</td>
<td style="text-align: right;">200</td>
<td style="text-align: right;">50</td>
<td style="text-align: right;">40</td>
<td style="text-align: right;">100</td>
<td style="text-align: right;">20</td>
<td style="text-align: right;">55</td>
<td style="text-align: right;">45</td>
</tr>
</tbody>
</table>
<p>合格会话定义为去重后、在可买库存/选项下被完整观察的会话，每个会话最多买1件。每行合格+缺货+重复=点击。收藏和加购可以重叠，不能互相相减或强行视为同一个严格串行漏斗。</p>
<p>CTR=点击÷曝光=460÷4600=10%。加购/点击=115÷460=25%；收藏/点击=92÷460=20%。本节贝叶斯模型估计的是合格会话的购买概率p，不是CTR，也不是全流量买家比例，更不是生命周期总销量。</p>
<h3 id="beta更新可以理解为累加两本计数账">3.2
Beta更新可以理解为累加两本计数账</h3>
<p>先验取Beta(α,β)=Beta(2,18)。α、β是正数、无单位。可把2和18理解为固定教学先验中的成功/未成功权重，先验均值为2÷(2+18)=10%。不是额外观测到20个真实顾客。</p>
<p>观察n个合格会话，其中x个购买。在条件独立、同一p、无重复计数的模型下：</p>
<p>α后=α前+x；β后=β前+(n−x)；p后均值=α后÷(α后+β后)。</p>
<p>逐步算：</p>
<ul>
<li>第1天n=80、x=8：α=2+8=10；β=18+72=90；均值10÷100=10%。</li>
<li>第2天再n=120、x=18：α=10+18=28；β=90+102=192；均值28÷220≈12.727%。</li>
<li>第3天再n=100、x=20：α=28+20=48；β=192+80=272；均值48÷320=15%。</li>
</ul>
<p>也可一次汇总：n=300，x=46；(2+46)÷(2+18+300)=48÷320=0.15。原始46÷300≈15.333%，先验轻微拉回。不能把三个每日百分比简单平均，因为每日分母不同。</p>
<p>为什么加起来合理？若你先学了幂次，Beta先验对p的相对权重含p<sup>(α−1)(1−p)</sup>(β−1)，n次中x次成功带来p<sup>x(1−p)</sup>(n−x)。同底数相乘指数相加，新的指数就是α+x−1与β+n−x−1。不需要先学积分证明，先理解“成功加到α，失败加到β”。</p>
<p>脚本还计算在该模型和先验条件下的95%后验区间，约[0.11308,0.19107]。这是p的可信区间，不是未来销量必在某两个整数之间，也不涵盖错误人群匹配、季节过时或流量计划失准。后验概率P(p≥0.12)≈0.94055；算法用整数参数的Beta/二项恒等式数值计算，不能靠四舍五入的0.15替代这一步。</p>
<p>缺货会话被排除并不自动消除偏差。如果买得最快的尺码缺货，合格会话可能偏向其他尺码。把这个p推广到将来，必须假设未来可售选项和人群足够可比，或另分层建模。本例不声称已经恢复缺货顾客的真实偏好。</p>
<h3 id="从转化概率走到生命周期数量">3.3 从转化概率走到生命周期数量</h3>
<p>第3日以后还有9天销售期。未来合格会话量是业务情景，不是已观测事实。生命周期阶段的转化倍率也是预先冻结的模拟参数，不能利用当前款未来销量反推。</p>
<table>
<thead>
<tr class="header">
<th>阶段</th>
<th style="text-align: right;">天数</th>
<th style="text-align: right;">每日合格会话</th>
<th style="text-align: right;">转化倍率g</th>
<th style="text-align: right;">购买概率p×g</th>
<th style="text-align: right;">阶段期望件数</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>第3—6日</td>
<td style="text-align: right;">3</td>
<td style="text-align: right;">400</td>
<td style="text-align: right;">1</td>
<td style="text-align: right;">0.15</td>
<td style="text-align: right;">3×400×0.15=180</td>
</tr>
<tr class="even">
<td>第6—9日</td>
<td style="text-align: right;">3</td>
<td style="text-align: right;">300</td>
<td style="text-align: right;">0.8</td>
<td style="text-align: right;">0.12</td>
<td style="text-align: right;">3×300×0.12=108</td>
</tr>
<tr class="odd">
<td>第9—12日</td>
<td style="text-align: right;">3</td>
<td style="text-align: right;">100</td>
<td style="text-align: right;">0.4</td>
<td style="text-align: right;">0.06</td>
<td style="text-align: right;">3×100×0.06=18</td>
</tr>
</tbody>
</table>
<p>公式D̂阶段=天数×每日会话×p×g。剩余期望306件，已售46件，加总生命周期期望352件。不能写成“15%转化，所以生命周期352件必定卖完”。曝光少一半，p不变，数量仍会明显减少。</p>
<p>若中期会话300改成0，剩余期望从306降到198件，追单建议也可变0；这是真正区分“测款概率”与“销量计划”的测试。</p>
<h3 id="追单只能服务到货之后">3.4 追单只能服务到货之后</h3>
<p>首单100件，已售46件，现存54件。新订单交期3天，第6日到货；另有20件已确认在第6日到货。第12日季末结束。每箱10件，MOQ50件，供应上限120件。</p>
<p>先算时间：追单到货前的均值需求情景为180件，现存只有54件，差126件。这126不能用第6日以后的追单倒回去满足。没有延期交付、替代购买和跨期等待是本例假设。</p>
<p>到货时原库存剩余的均值情景为max(54−180,0)=0；加确认在途20件，追单前可用20件。到货后需求情景108+18=126件，净缺口126−20=106件。</p>
<p>按整箱向上取整：ceil(106÷10)×10=11×10=110件。ceil表示向上取最近整数。110满足MOQ50与上限120。</p>
<p>教学追单门槛预先设为P(p≥0.12)≥0.8。0.94055≥0.8通过，最终输出110件草稿建议，均值情景期末余20+110−126=4件。</p>
<p>这里max(现存−平均需求,0)不等于“剩余库存的数学期望”。库存截断是非线性的；我们明确在均值情景上演示计划，并未积分全部需求不确定性。真正比较期望利润或缺货风险，需对需求、曝光与到货时间联合采样，再逐情景回放库存。0.12和0.8是教学门槛，不是已优化的商业最优阈值，不能宣称110件利润最优。</p>
<h3 id="必须做的失败测试">3.5 必须做的失败测试</h3>
<ul>
<li>第3天漏斗到第74小时才到达：第72小时只能用前两行，后验变Beta(28,192)，不能读未来窗口。</li>
<li>所有合格会话为0：保留先验，但状态必须为insufficient_observations，不凭先验自动追单。</li>
<li>将新交期改到季末：到货第12日，输出arrival_after_lifecycle与0追单。</li>
<li>购买数大于合格会话，或重复窗口重叠：拒绝输入，不能得到大于100%的“转化率”。</li>
</ul>
<p>作业提交漏斗分母对账、三次后验更新、三阶段需求、到货前后库存时间线、改参结果。验收答案为48/272、0.15、306/352、到货前缺126、到货后净缺106、整箱追单110。不要把352当成发货承诺。</p>
