{
  "title": "预售取消：风险集到条件待发情景",
  "description": "预售取消：风险集到条件待发情景：问题：100单预售，第1天10单取消、20单发货，第2天7单取消。第2天取消率是多少？",
  "type": "forecast",
  "unit": "presale-full",
  "weight": 61,
  "outputs": [
    "HTML"
  ]
}

<p class="check">完全模拟的可复现实验，不连接生产。<a href="/forecast/forecast-specialty-projects.zip" download>下载四专项完整工程包（20,000/12,000/10,000/2,000实体）</a>。运行前阅读覆盖data/outputs的说明。固定模拟世界的指标不是企业收益。</p><p><a href="/forecast/specialty-start/">运行方法</a> · <a href="/forecast/specialty-time/">时间协议</a> · <a href="/forecast/specialty-data/">字段字典</a></p><h2 id="练习1预售取消的正确分母">练习1：预售取消的正确分母</h2>
<p><strong>问题</strong>：100单预售，第1天10单取消、20单发货，第2天7单取消。第2天取消率是多少？</p>
<ol type="1">
<li>纸上写：第2天仍在等待=100−10−20=70，条件取消率=7/70=10%。不能继续用100当分母。</li>
<li>写下“如果两天自然取消率都10%、而没有发货，留存比例=0.9×0.9=0.81”。这不是实际等待池；实际第2天末等待63单。</li>
<li>打开 <code>outputs/presale/independent_risk_table.csv</code>，筛
<code>group=ALL</code>、<code>age=1/2</code>。用本包真实生成的计数再算一次。模拟结果不要求恰好10%。</li>
<li>打开
<code>survival.svg</code>，寻找信息性发货估计与oracle曲线的距离。回答：为什么发得越早，留下的订单看起来越不容易取消？</li>
<li>在条件需求表挑一个当前年龄a的订单，查其SKU曲线。计算S(b)/S(a)，而不是再乘S(b)。核对跨60日强关时的规则。</li>
</ol>
<p><strong>交付</strong>：一张风险集复核表，一句话说明“无发货情景”依赖的假设，以及一个订单的条件留存计算。</p>
<p><strong>手算答案</strong>：70、10%、81%、63单；如果已有80单、S(a)=0.72、S(b)=0.54，预计60单。不能把80×0.54=43.2当正确条件结果。</p>
<p><strong>验收</strong>：风险集不为负；取消、发货、强关不重叠；S不增加；第60日强关不被解释为自然hazard。</p>
<h2>模型实现及未实现范围</h2><h2 id="a.-预售取消">A. 预售取消</h2>
<p><strong>实现</strong>：年龄1–59日风险集；未平滑hazard；SKU分组向总体hazard收缩；m取0/20/100/500，在验证集选择；训练总体hazard基线；测试在风险订单日Brier；S(b)/S(a)条件留存；第60日强制关单；两种发货机制与Oracle诊断；订单数/件数双重守恒。</p>
<p>公式：h=(取消数+m×总体当日hazard)/(风险订单数+m)。S(t)是截至t日的(1−h)连乘。分母必须只含当天仍在风险集的订单。无支持时概率留空，不伪造尾部。</p>
<p><strong>关键假设</strong>：若把发货当删失、再解释成“假如不发货的取消留存”，必须有条件独立删失等识别前提。信息性场景故意违反这个前提。较低的订单日Brier不能证明这个反事实曲线正确。</p>
<p><strong>未实现</strong>：离散logit
hazard、Cox比例风险、Fine–Gray、Aalen–Johansen竞争风险累计发生率、逆概率删失加权、随机化发货干预、按订单动态更新承诺时间、部分取消与部分发货。程序绝不把分组平滑hazard称为Cox。</p>
<p><strong>当下净需求边界</strong>：输出的是“当前未发订单在无发货情景下剩余等待量”，不是包含发货过程的实际未来等待池预测，不是可承诺库存。已发货订单已退出当前待发队列，不能重复计算。</p>
<h2>实际运行结果与解释</h2><h2 id="预售预测误差小不等于假设正确">1.
预售：预测误差小不等于假设正确</h2>
<ul>
<li>同一批20,000订单，各有独立发货/信息性发货两个场景。每个场景训练6858单、验证1676单、测试4907单；其他日期记录保留作成熟空档和事件账。</li>
<li>独立发货：测试每日hazard
Brier，平滑模型0.009135，总体基线0.009136。</li>
<li>信息性发货：测试每日hazard
Brier，平滑模型0.007620，总体基线0.007613。本次平滑误差不低于总体。</li>
<li>第59日“无发货自然留存”估计减模拟潜在真值：独立场景0.06个百分点，信息性场景9.23个百分点。正数表示高估，负数表示低估。</li>
<li>两场景的风险集不同，不能拿两种场景的Brier直接排名。Oracle比较是模拟诊断，不是现实可以拿到的答案。</li>
</ul>
<p>查看：<code>presale/survival.svg</code>、<code>presale/oracle_diagnostic_survival.csv</code>、<code>presale/conditional_pending_demand_scenario.csv</code>。</p>
<figure><img loading="lazy" src="/forecast/specialty-outputs/presale/survival.svg" alt="预售取消：风险集到条件待发情景：survival.svg，固定种子模拟输出"><figcaption>固定种子20261106的实际程序输出，仅反映教学模拟。survival.svg</figcaption></figure>
