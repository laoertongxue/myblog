{
  "title": "2 温度积分与动态货架期的可识别限制",
  "description": "2 温度积分与动态货架期的可识别限制：本课把白皮书中的温度动态货架期、鞋服贝叶斯测款与生命周期追单、VMI协同、生鲜小时缺货和联名首二配补成完整小实验。读者只需会百分比、乘除、比较大小和按时间记账。先用本文数字手算，再运行同目录项目包，最后故意修改输入，看结论是否随约束改变。",
  "type": "forecast",
  "unit": "temperature-shelf-life",
  "weight": 77,
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
</details><h2 id="温度积分与动态货架期的可识别限制">2
温度积分与动态货架期的可识别限制</h2>
<h3 id="业务问题和安全边界">2.1 业务问题和安全边界</h3>
<p>三批模拟商品从采摘到判断时点共12小时，每批分成6个连续2小时温度段。要生成品质风险情景，并说明哪些批次需要人工复核。这里没有任何真实食品检测、微生物实验或法律标准。</p>
<p><strong>本节不能判断食物是否可食用，不能放行、自动报废或延长标签效期。</strong>“品质分数”只是人为定义的教学刻度，与病原菌风险不等价。</p>
<p>温度表如下。每个温度假设在整段内恒定，并非拿一段均温冒充段内所有变化。</p>
<table>
<colgroup>
<col style="width: 9%" />
<col style="width: 12%" />
<col style="width: 12%" />
<col style="width: 12%" />
<col style="width: 12%" />
<col style="width: 12%" />
<col style="width: 12%" />
<col style="width: 12%" />
</colgroup>
<thead>
<tr class="header">
<th>批次</th>
<th style="text-align: right;">0—2小时</th>
<th style="text-align: right;">2—4小时</th>
<th style="text-align: right;">4—6小时</th>
<th style="text-align: right;">6—8小时</th>
<th style="text-align: right;">8—10小时</th>
<th style="text-align: right;">10—12小时</th>
<th style="text-align: right;">判断时剩余标签小时</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>A</td>
<td style="text-align: right;">4℃</td>
<td style="text-align: right;">4℃</td>
<td style="text-align: right;">8℃</td>
<td style="text-align: right;">8℃</td>
<td style="text-align: right;">4℃</td>
<td style="text-align: right;">4℃</td>
<td style="text-align: right;">60</td>
</tr>
<tr class="even">
<td>B</td>
<td style="text-align: right;">4℃</td>
<td style="text-align: right;">4℃</td>
<td style="text-align: right;">4℃</td>
<td style="text-align: right;">4℃</td>
<td style="text-align: right;">4℃</td>
<td style="text-align: right;">4℃</td>
<td style="text-align: right;">36</td>
</tr>
<tr class="odd">
<td>C</td>
<td style="text-align: right;">4℃</td>
<td style="text-align: right;">缺测</td>
<td style="text-align: right;">10℃</td>
<td style="text-align: right;">4℃</td>
<td style="text-align: right;">4℃</td>
<td style="text-align: right;">4℃</td>
<td style="text-align: right;">60</td>
</tr>
</tbody>
</table>
<p>所有批次初始品质Q₀=100分，模拟提醒阈值Q警=70分。参数是为了手算而设，不是从白皮书推导或用食品实测拟合的。</p>
<h3 id="从每段矩形面积理解积分">2.2 从每段矩形面积理解积分</h3>
<p>设T为温度，单位℃；r(T)为每小时消耗的品质分，单位分/小时。教学模型：</p>
<p>r(T)=0.5+0.125×max(T−4,0)。</p>
<p>max(a,0)表示a小于0就取0。因此4℃每小时消耗0.5分，8℃每小时消耗0.5+0.125×4=1分，10℃每小时消耗1.25分。模型只在0—12℃的教学范围使用；30℃输入会拒绝计算，不外推安全结论。</p>
<p>第j段时长记作Δtⱼ，单位小时；第j段消耗eⱼ=r(Tⱼ)×Δtⱼ，单位分。总消耗E=Σeⱼ，Σ就是把每段加起来。更密集地采样时，人们写成E=∫r(T(t))dt；积分在这里就是沿时间累计面积，先掌握“高度×宽度再相加”即可。</p>
<p>剩余品质Q=max(100−E,0)。</p>
<p>A有4个4℃段、2个8℃段：E_A=4×0.5×2+2×1×2=4+4=8分，Q_A=92分。</p>
<p>B全程4℃：E_B=6×0.5×2=6分，Q_B=94分。</p>
<p>不要使用“最高8℃持续12小时”替代整条轨迹，那会把A算成消耗12分。也不能先把温度平均后随便套非线性模型；分段跨过阈值时，平均温度的降解率未必等于平均降解率。</p>
<h3 id="还剩多少小时取决于未来温度假设">2.3
还剩多少小时取决于未来温度假设</h3>
<p>假设未来一直4℃，每小时再消耗0.5分。达到教学阈值的时间R模型=(Q−70)÷0.5，若已低于70则取0。</p>
<ul>
<li>A：(92−70)÷0.5=44小时。</li>
<li>B：(94−70)÷0.5=48小时。</li>
</ul>
<p>这不是实际到期时间。计划用的情景截止只能取模型提醒与标签硬截止较早者：R计划=min(R模型,R标签)。于是A为min(44,60)=44，B为min(48,36)=36。按本例风险情景，B更早需要处理。</p>
<p>若未来改为8℃，消耗率为1分/小时：A为22小时，B为24小时，情景顺序翻成A在前。结论改变来自未来储运条件假设，不是算法知道未来。脚本scenario_priority只作教学风险排序，不自动替换企业必须遵守的标签FEFO或质量流程。</p>
<p>温度轨迹 → 累计消耗 → 模拟品质 → 未来储存情景 → 风险提示 →
人工质量审核。</p>
<p>标签已到期时，模型算出再多小时也不能恢复可售状态。脚本返回label_expired，planning_hours为空。</p>
<h3 id="缺测不能补成安全温度">2.4 缺测不能补成安全温度</h3>
<p>C缺一段2小时。已知5段累计消耗：4个4℃段消耗4分，1个10℃段消耗2.5分，合计6.5分。</p>
<p>只有在额外假设“缺测段温度确实落在0—12℃”时，未知段消耗才在2×0.5=1到2×1.5=3分之间。因此：</p>
<ul>
<li>总消耗E在7.5—9.5分。</li>
<li>剩余品质Q在90.5—92.5分。</li>
<li>未来4℃的阈值时间在(90.5−70)÷0.5=41到(92.5−70)÷0.5=45小时。</li>
</ul>
<p>这仍不是安全保证。程序输出unknown_temperature_review，不给C单一计划小时或自动排序资格。若0—12℃这一边界也没有依据，连这个条件范围都不能当可靠边界。</p>
<p>晚到读数同样处理：即使文件里能看见数值，available_at晚于判断时点，就当当时未知。缺段、重叠段、结束早于开始、缺时区和超出有效温度范围均不能静默通过。</p>
<h3 id="为什么光有温度还不够">2.5 为什么光有温度还不够</h3>
<p>温度历史能提供暴露特征，却不能单独识别真实品质变化函数。仍缺少：初始品质、品种/成熟度/包装、温度传感器校准、湿度和气体条件、按批次采集的品质/安全检测标签、模型验证范围、漏报与误报代价，以及适用质量规范。</p>
<p>即使两种模型都能拟合现有少量温度，它们可能预测不同的剩余时长；没有相应质量结果就无法区分。某一品质阈值也不等于食品安全阈值。训练/验证时要按批次和时间切分，不能把同批相邻小时随机拆到两边，再宣称可推广。</p>
<p>作业：复算A/B/C，画温度阶梯图与累计消耗图；把未来温度改8℃，核对22/24与排序反转；把A标签截止改到判断前1小时，核对不可恢复；删掉一个温度段，核对程序报错。验收必须保留安全边界，不得把本节命名为“已验证保鲜模型”。</p>
