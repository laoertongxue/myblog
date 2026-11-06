{
  "title": "第五章 完整 60 天曲线和删失能告诉我们的边界",
  "description": "第五章 完整 60 天曲线和删失能告诉我们的边界：白皮书范围：专项场景一。 本章必须区分三个不同问题：历史上实际发生多少取消；还未发货订单未来会取消多少；如果从不发货，原始订单会怎样。最后一个是反事实问题，不能只靠除法就无条件识别。",
  "type": "forecast",
  "unit": "presale-60days",
  "weight": 24,
  "outputs": [
    "HTML"
  ]
}

<p class="check">本课使用模拟数据与明确假设。数学推导、枚举和数据核验不等于真实业务模型有效。配套包包含60天教学曲线及约束枚举，不是完整订单训练集。<br><a href="/forecast/planning-math-labs.zip" download>下载数学实验、完整教材与只读验证器</a></p><h2 id="第五章-完整-60-天曲线和删失能告诉我们的边界">第五章 完整 60
天曲线和删失能告诉我们的边界</h2>
<p><strong>白皮书范围：专项场景一。</strong>
本章必须区分三个不同问题：历史上实际发生多少取消；还未发货订单未来会取消多少；如果从不发货，原始订单会怎样。最后一个是反事实问题，不能只靠除法就无条件识别。</p>
<p>本章是独立的确定性手算案例。它与另一个使用大量订单、随机风险差异和信息性发货的专项模拟项目不是同一批数据，不应把两个结果拼成同一条“真值曲线”。</p>
<h3 id="先把风险集的时钟定好">5.1 先把风险集的时钟定好</h3>
<p>在本章的离散教学约定中，每天先记录取消，再在日末记录发货；没有新订单中途加入同一批次。</p>
<p><strong>R_1=N；R_(t+1)=R_t-C_t-H_t。</strong></p>
<p><strong>原始日风险率 h_t=C_t/R_t，仅当 R_t&gt;0。</strong></p>
<ul>
<li>N：批次初始订单数，单。</li>
<li>R_t：第 t 天天初尚未取消且尚未发货的可观察订单数，单。</li>
<li>C_t：当日先发生的取消数，单。</li>
<li>H_t：当日日末发货删失数，单。</li>
<li>h_t：在第 t
天天初仍处于风险中的订单，当天取消的条件概率，无单位。</li>
<li>来源：人数守恒和条件概率定义；业务数据来自订单创建、取消、发货时间戳与状态日志。</li>
</ul>
<p>必须有
C_t+H_t≤R_t。同一订单不能同一天同时记为发货前取消和发货。若现实中发货和取消交错发生，应使用准确时间戳、明确先后顺序或更细时间段；不能未经说明就把全天都当作完整暴露。数据截取日造成的未观察未来也是右删失。</p>
<p>小例子：10 单，第一天取消 2 单、日末发货 4 单，所以第二天天初
R_2=10-2-4=4；第二天取消 1 单，风险率 h_2=1/4=25%，不是 1/10=10%。1/10
是“占初始订单的当日观察取消比例”，回答的是另一个问题。</p>
<h3 id="从条件风险率乘出留存概率">5.2 从条件风险率乘出留存概率</h3>
<p><strong>S_0=1；S_t=S_(t-1)(1-h_t)=Π(k=1 到 t)(1-h_k)。</strong></p>
<ul>
<li>S_t：在目标机制下撑过第 t
天仍未发生目标取消事件的概率，无单位。</li>
<li>h_k：同一目标机制下的第 k 天条件风险率。</li>
<li>数学来源：条件概率链式法则。相乘不要求“每一天相互独立”；关键是每个
h_k 已经条件化在此前仍留存。</li>
</ul>
<p>前一个 10 单例子的合并估计为
S_1=0.8、S_2=0.8×0.75=0.6。<strong>只有合并人群本身满足相应的非信息性删失条件，或其风险足够同质且满足其他识别条件时，才可用这种不分层的
Π(1-C_t/R_t) 估计目标总体的未发货留存曲线。</strong>
此时第二天留存点估计约为 10×0.6=6
单；这不是有限样本必然无偏的保证。历史上实际尚未取消且尚未发货的仅有 3
单，不应混淆两种数量。</p>
<p>如果独立性只在给定 X
后成立，必须先估计条件曲线，再按<strong>原始目标人群</strong>的 X
分布标准化，或正确使用逆删失概率加权。不能一边声称只需要条件独立，一边仍直接使用未经调整的总体
C_t/R_t。</p>
<h3 id="反事实解释额外需要什么">5.3 反事实解释额外需要什么</h3>
<p>删掉发货记录后直接相乘，并不会自动得到真实的“完全不发货”世界。至少需要检查：</p>
<ol type="1">
<li><strong>一致性与明确干预</strong>：定义“从不发货但其他规则如何保持”。被纳入观测的等待经历应与所设干预在对应时段相符。改变交付承诺、客服通知或赔付规则，可能同时改变取消概率。</li>
<li><strong>删失独立性与所用估计器匹配</strong>：未经调整的总体乘积极限估计需要总体层面的适当独立删失条件。若只能假设给定商品、价格、会员、活动及已知历史
X 后可交换，则必须使用相应分层标准化、正确条件模型/g-formula 或正确
IPCW；条件独立本身不保证合并 C_t/R_t
有效。建模方法还要求模型正确设定。</li>
<li><strong>重叠/可观察支持</strong>：对目标人群及目标天数，必须还有一定概率留在未发货可观察状态。若某类订单第
10 天全部发货，数据无法单独识别该类第 11～59 天的自然风险。</li>
<li><strong>事件和数据准确</strong>：创建时间、取消类型、发货时间、观察结束时间及可用特征应准确，不能使用预测时点之后的信息。</li>
</ol>
<p>仅凭观察数据不能证明“没有未观测混杂”。可以检查发货选择是否依赖已有风险特征、比较政策变化前后、做敏感性分析，并在合理情况下做前瞻设计。不能按“最终
1～3 天发货、4～7 天发货、8
天后发货”分组就宣称验证了独立性，因为最终能发货本身要求之前没取消，会引入生存选择偏差。</p>
<p>可用的升级方式包括：按观测协变量分层；拟合时变条件风险；在假设成立且有支持时使用逆删失概率权重。若
G_t 表示给定已知历史到 t 时仍未被删失的概率，权重可涉及 1/G_t。G_t 接近
0 会使方差极大，G_t=0 时不能靠加权创造信息。</p>
<h4
id="条件独立却不能直接合并的两天反例">条件独立却不能直接合并的两天反例</h4>
<p>全部为模拟。原始 100 单中，高风险 H 与低风险 L 各 50 单。第 1
天两组都不自然取消；日末在高风险组内随机发走 40
单，低风险不发货。给定组别 X，发走谁与其潜在取消结果独立。第 2
天自然取消概率，高风险为 50%、低风险为
0%。为便于手算，取与该概率相符的一次示例：剩下 10 单高风险中取消 5
单，低风险 50 单中取消 0 单。</p>
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
<th>组别</th>
<th style="text-align: right;">原始单数</th>
<th style="text-align: right;">第 1 天末发货单数</th>
<th style="text-align: right;">第 2 天风险集</th>
<th style="text-align: right;">第 2 天取消数</th>
<th style="text-align: right;">第 2 天组内留存率</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>H</td>
<td style="text-align: right;">50</td>
<td style="text-align: right;">40</td>
<td style="text-align: right;">10</td>
<td style="text-align: right;">5</td>
<td style="text-align: right;">1-5/10=50%</td>
</tr>
<tr class="even">
<td>L</td>
<td style="text-align: right;">50</td>
<td style="text-align: right;">0</td>
<td style="text-align: right;">50</td>
<td style="text-align: right;">0</td>
<td style="text-align: right;">1-0/50=100%</td>
</tr>
</tbody>
</table>
<p><strong>错误合并</strong>：第 2
天总风险集=60，取消=5，合并留存估计=1-5/60≈91.667%。高风险订单被优先移出，剩余人群已经不是原来的
50/50 构成。</p>
<p><strong>不发货目标真值</strong>：50 单高风险预计留下 25 单，50
单低风险留下 50 单，故留存率=(25+50)/100=75%。本例约有 16.667
个百分点的合并估计差异，即使组内删失独立也会出现。</p>
<p><strong>方法一，分层再按原始人群标准化</strong>：</p>
<p><strong>S_target(t)=Σ_x w_x S_x(t)，w_x=N_x/N。</strong></p>
<ul>
<li>x：基线组别，H 或 L，无单位；N_x 是原始组别人数，单。</li>
<li>w_x：原始目标人群组别占比，无单位；不是删失后风险集占比。</li>
<li>S_x(t)：在组内适当独立删失和支持条件下估计的留存概率。</li>
<li>数学来源：对原始人群分层使用全概率公式。本例只有基线组别；时变混杂可能需要纵向标准化，不能简单固定分层解决。</li>
</ul>
<p>代入 w_H=w_L=0.5，S_target(2)=0.5×0.5+0.5×1=0.75。若错误使用第 2 天的
10/60 与 50/60 加权，会再次得到 91.667%。</p>
<p><strong>方法二，逆删失概率加权手算</strong>：高风险订单到第 2
天天初仍被观察的概率 G_H=10/50=0.2；低风险
G_L=1。高风险每个在险订单的权重为 1/0.2=5，低风险权重为 1。</p>
<p>加权风险集=10×5+50×1=100；加权取消数=5×5+0×1=25；加权第 2
天风险=25/100=25%，留存=75%。这里 G
是教学已知的组内留观概率；实际应用必须估计完整的留观概率，防止使用未来信息，并满足支持与正确设定条件。一般时变权重需要累计每一步条件留观概率，不是随意用某一天的原始留存比例代替。</p>
<p><strong>可检验题</strong>：若第 1 天末改为发走 30 单高风险，第 2 天
20 单高风险取消 10 单，其他不变，分别计算合并、分层及加权留存。</p>
<p><strong>答案</strong>：合并=1-10/70≈85.714%；分层仍为
0.5×0.5+0.5×1=75%；G_H=20/50=0.4，权重
2.5，加权风险集=20×2.5+50=100，加权取消=10×2.5=25，留存仍为 75%。</p>
<p>方法依据可核对<a
href="https://pmc.ncbi.nlm.nih.gov/articles/PMC11043789/">Chiu
等关于依赖协变量删失与未经调整 Kaplan–Meier 的原始论文</a>及 <a
href="https://stat.ethz.ch/R-manual/R-devel/library/survival/doc/adjcurve.pdf">R
survival
作者的标准化生存曲线说明</a>。这两者支持估计对象与调整方法的区别；上述
50/50 数值是本课程模拟，不来自论文案例。</p>
<p>原白皮书的 <strong>logit(h_t(X))=α_t+βᵀX</strong>
是离散时间逻辑风险模型，<strong>不是 Cox 模型的同义写法</strong>。这里
logit(p)=ln[p/(1-p)]，α_t 是该天截距，X 是预测时点可知特征向量，β
是相应系数。若讨论连续比例风险的离散分组形式，常见链接是 complementary
log-log，但仍需交代基线风险和分组条件。不要仅凭加入协变量就把模型叫作
Cox。</p>
<h4 id="把-βᵀx-展开成高一能算的加权和">把 βᵀX
展开成高一能算的加权和</h4>
<p>βᵀX
只是一种压缩写法：若有两个特征，<strong>βᵀX=β_1X_1+β_2X_2</strong>。上标
T 表示向量转置，不是时间或幂。</p>
<p>设某一天的基线风险为 10%，因此
α_t=ln[0.1/(1-0.1)]=ln(1/9)≈-2.197225。教学设 X_1 为“已知活动标签”，X_2
为“已知价格带标签”，两者均取 0 或 1，没有单位。假设
β_1=ln2≈0.693147、β_2=ln1.5≈0.405465，系数是教学给定值，不是已估计的商业效应。</p>
<p>对 X_1=X_2=1 的订单： 1. βᵀX=0.693147×1+0.405465×1≈1.098612。 2.
线性分数 η=α_t+βᵀX≈-1.098612，没有单位。 3.
<strong>h=exp(η)/[1+exp(η)]</strong>，来源是把 logit 定义反解。 4.
exp(η)=1/3，所以 h=(1/3)/(1+1/3)=1/4=25%。 5. 若当天有 200
单具有这些特征且都在风险集中，预测取消期望数=200×0.25=50 单。</p>
<p>若只把 X_2 改为 0，则
exp(η)=2/9，h=(2/9)/(1+2/9)=2/11≈18.182%。系数作用在取消的<strong>赔率</strong>
h/(1-h) 上，不能直接把概率 10% 乘 2 再乘 1.5 得到 30%。</p>
<p>条件风险和生存乘积的关系、logit 与其他链接的差别，可核对<a
href="https://link.springer.com/article/10.1186/s12874-022-01679-6">离散时间生存模型的原始方法论文</a>。本课程没有把该论文的实证结果当成供应链效果。</p>
<h3 id="这条-60-天教学曲线如何生成">5.4 这条 60 天教学曲线如何生成</h3>
<p>初始 N=1000 单，假设 1～59
天不发货，且下面的自然取消风险率是教学给定值，不是历史数据拟合值：</p>
<table>
<thead>
<tr class="header">
<th>天数</th>
<th style="text-align: right;">自然取消日条件风险率</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>1</td>
<td style="text-align: right;">18.0%</td>
</tr>
<tr class="even">
<td>2</td>
<td style="text-align: right;">3.7%</td>
</tr>
<tr class="odd">
<td>3</td>
<td style="text-align: right;">3.3%</td>
</tr>
<tr class="even">
<td>4</td>
<td style="text-align: right;">3.0%</td>
</tr>
<tr class="odd">
<td>5</td>
<td style="text-align: right;">2.7%</td>
</tr>
<tr class="even">
<td>6</td>
<td style="text-align: right;">2.3%</td>
</tr>
<tr class="odd">
<td>7</td>
<td style="text-align: right;">2.0%</td>
</tr>
<tr class="even">
<td>8～14</td>
<td style="text-align: right;">每天 1.5%</td>
</tr>
<tr class="odd">
<td>15～30</td>
<td style="text-align: right;">每天 0.9%</td>
</tr>
<tr class="even">
<td>31～45</td>
<td style="text-align: right;">每天 0.5%</td>
</tr>
<tr class="odd">
<td>46～59</td>
<td style="text-align: right;">每天 0.3%</td>
</tr>
<tr class="even">
<td>60 天开始</td>
<td style="text-align: right;">对剩余订单执行规则性强制关闭</td>
</tr>
</tbody>
</table>
<p>定义：</p>
<p><strong>B_0=N；自然取消期望数
E_t=B_(t-1)h_t；B_t=B_(t-1)-E_t（t=1,…,59）。</strong></p>
<p><strong>S_t=B_t/N；自然累计取消率 F_t=1-S_t（这两式仅用于
t=0,…,59）。</strong></p>
<ul>
<li>B_t：不发货设定下第 t 天结束后的预计活跃订单数，单。</li>
<li>E_t：当天预计自然取消数，单。</li>
<li>S_t：自然留存概率，无单位；S_0=1，而不是 1000。</li>
<li>F_t：截至 t 的自然累计取消概率，无单位。</li>
<li>来源：条件期望和人数守恒。预计人数可以有小数，并不代表现实有“半张订单”。</li>
</ul>
<p>第 60 天定义强关数 <strong>G_60=B_59</strong>、规则执行后的活跃数
<strong>B_60=0</strong>。G_60
是不同事件类型，不要解释成买家自然取消意愿突然等于
100%。按照本例时序，强关在第 60 天开始发生，不再模拟该天的自然取消。</p>
<p>前两天手算： 1. 第 1 天：E_1=1000×0.18=180；B_1=820；S_1=0.82。 2. 第
2 天：E_2=820×0.037=30.34；B_2=789.66；S_2=0.78966。 3. 不能把第 2
天算成 1000×0.037=37，因为第 1 天取消的订单不再有资格第二天重复取消。 4.
不能把每天 h_t 相加当作累计率；正确方法是 1-Π(1-h_t)。</p>
<h3 id="全-60-天逐日核对表">5.5 全 60 天逐日核对表</h3>
<p>以下表格只在显示时四舍五入；递推始终使用未四舍五入值。“累计自然取消”不含第
60 天的规则强关。</p>
<table style="width:100%;">
<colgroup>
<col style="width: 14%" />
<col style="width: 14%" />
<col style="width: 14%" />
<col style="width: 14%" />
<col style="width: 14%" />
<col style="width: 14%" />
<col style="width: 14%" />
</colgroup>
<thead>
<tr class="header">
<th style="text-align: right;">天</th>
<th style="text-align: right;">自然日风险率</th>
<th style="text-align: right;">天初预计单数</th>
<th style="text-align: right;">自然取消单数</th>
<th style="text-align: right;">强关单数</th>
<th style="text-align: right;">天末活跃单数</th>
<th style="text-align: right;">累计自然取消</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td style="text-align: right;">1</td>
<td style="text-align: right;">18.00%</td>
<td style="text-align: right;">1000.000</td>
<td style="text-align: right;">180.000</td>
<td style="text-align: right;">0.000</td>
<td style="text-align: right;">820.000</td>
<td style="text-align: right;">18.000%</td>
</tr>
<tr class="even">
<td style="text-align: right;">2</td>
<td style="text-align: right;">3.70%</td>
<td style="text-align: right;">820.000</td>
<td style="text-align: right;">30.340</td>
<td style="text-align: right;">0.000</td>
<td style="text-align: right;">789.660</td>
<td style="text-align: right;">21.034%</td>
</tr>
<tr class="odd">
<td style="text-align: right;">3</td>
<td style="text-align: right;">3.30%</td>
<td style="text-align: right;">789.660</td>
<td style="text-align: right;">26.059</td>
<td style="text-align: right;">0.000</td>
<td style="text-align: right;">763.601</td>
<td style="text-align: right;">23.640%</td>
</tr>
<tr class="even">
<td style="text-align: right;">4</td>
<td style="text-align: right;">3.00%</td>
<td style="text-align: right;">763.601</td>
<td style="text-align: right;">22.908</td>
<td style="text-align: right;">0.000</td>
<td style="text-align: right;">740.693</td>
<td style="text-align: right;">25.931%</td>
</tr>
<tr class="odd">
<td style="text-align: right;">5</td>
<td style="text-align: right;">2.70%</td>
<td style="text-align: right;">740.693</td>
<td style="text-align: right;">19.999</td>
<td style="text-align: right;">0.000</td>
<td style="text-align: right;">720.694</td>
<td style="text-align: right;">27.931%</td>
</tr>
<tr class="even">
<td style="text-align: right;">6</td>
<td style="text-align: right;">2.30%</td>
<td style="text-align: right;">720.694</td>
<td style="text-align: right;">16.576</td>
<td style="text-align: right;">0.000</td>
<td style="text-align: right;">704.118</td>
<td style="text-align: right;">29.588%</td>
</tr>
<tr class="odd">
<td style="text-align: right;">7</td>
<td style="text-align: right;">2.00%</td>
<td style="text-align: right;">704.118</td>
<td style="text-align: right;">14.082</td>
<td style="text-align: right;">0.000</td>
<td style="text-align: right;">690.036</td>
<td style="text-align: right;">30.996%</td>
</tr>
<tr class="even">
<td style="text-align: right;">8</td>
<td style="text-align: right;">1.50%</td>
<td style="text-align: right;">690.036</td>
<td style="text-align: right;">10.351</td>
<td style="text-align: right;">0.000</td>
<td style="text-align: right;">679.686</td>
<td style="text-align: right;">32.031%</td>
</tr>
<tr class="odd">
<td style="text-align: right;">9</td>
<td style="text-align: right;">1.50%</td>
<td style="text-align: right;">679.686</td>
<td style="text-align: right;">10.195</td>
<td style="text-align: right;">0.000</td>
<td style="text-align: right;">669.490</td>
<td style="text-align: right;">33.051%</td>
</tr>
<tr class="even">
<td style="text-align: right;">10</td>
<td style="text-align: right;">1.50%</td>
<td style="text-align: right;">669.490</td>
<td style="text-align: right;">10.042</td>
<td style="text-align: right;">0.000</td>
<td style="text-align: right;">659.448</td>
<td style="text-align: right;">34.055%</td>
</tr>
<tr class="odd">
<td style="text-align: right;">11</td>
<td style="text-align: right;">1.50%</td>
<td style="text-align: right;">659.448</td>
<td style="text-align: right;">9.892</td>
<td style="text-align: right;">0.000</td>
<td style="text-align: right;">649.556</td>
<td style="text-align: right;">35.044%</td>
</tr>
<tr class="even">
<td style="text-align: right;">12</td>
<td style="text-align: right;">1.50%</td>
<td style="text-align: right;">649.556</td>
<td style="text-align: right;">9.743</td>
<td style="text-align: right;">0.000</td>
<td style="text-align: right;">639.813</td>
<td style="text-align: right;">36.019%</td>
</tr>
<tr class="odd">
<td style="text-align: right;">13</td>
<td style="text-align: right;">1.50%</td>
<td style="text-align: right;">639.813</td>
<td style="text-align: right;">9.597</td>
<td style="text-align: right;">0.000</td>
<td style="text-align: right;">630.216</td>
<td style="text-align: right;">36.978%</td>
</tr>
<tr class="even">
<td style="text-align: right;">14</td>
<td style="text-align: right;">1.50%</td>
<td style="text-align: right;">630.216</td>
<td style="text-align: right;">9.453</td>
<td style="text-align: right;">0.000</td>
<td style="text-align: right;">620.762</td>
<td style="text-align: right;">37.924%</td>
</tr>
<tr class="odd">
<td style="text-align: right;">15</td>
<td style="text-align: right;">0.90%</td>
<td style="text-align: right;">620.762</td>
<td style="text-align: right;">5.587</td>
<td style="text-align: right;">0.000</td>
<td style="text-align: right;">615.176</td>
<td style="text-align: right;">38.482%</td>
</tr>
<tr class="even">
<td style="text-align: right;">16</td>
<td style="text-align: right;">0.90%</td>
<td style="text-align: right;">615.176</td>
<td style="text-align: right;">5.537</td>
<td style="text-align: right;">0.000</td>
<td style="text-align: right;">609.639</td>
<td style="text-align: right;">39.036%</td>
</tr>
<tr class="odd">
<td style="text-align: right;">17</td>
<td style="text-align: right;">0.90%</td>
<td style="text-align: right;">609.639</td>
<td style="text-align: right;">5.487</td>
<td style="text-align: right;">0.000</td>
<td style="text-align: right;">604.152</td>
<td style="text-align: right;">39.585%</td>
</tr>
<tr class="even">
<td style="text-align: right;">18</td>
<td style="text-align: right;">0.90%</td>
<td style="text-align: right;">604.152</td>
<td style="text-align: right;">5.437</td>
<td style="text-align: right;">0.000</td>
<td style="text-align: right;">598.715</td>
<td style="text-align: right;">40.129%</td>
</tr>
<tr class="odd">
<td style="text-align: right;">19</td>
<td style="text-align: right;">0.90%</td>
<td style="text-align: right;">598.715</td>
<td style="text-align: right;">5.388</td>
<td style="text-align: right;">0.000</td>
<td style="text-align: right;">593.326</td>
<td style="text-align: right;">40.667%</td>
</tr>
<tr class="even">
<td style="text-align: right;">20</td>
<td style="text-align: right;">0.90%</td>
<td style="text-align: right;">593.326</td>
<td style="text-align: right;">5.340</td>
<td style="text-align: right;">0.000</td>
<td style="text-align: right;">587.987</td>
<td style="text-align: right;">41.201%</td>
</tr>
<tr class="odd">
<td style="text-align: right;">21</td>
<td style="text-align: right;">0.90%</td>
<td style="text-align: right;">587.987</td>
<td style="text-align: right;">5.292</td>
<td style="text-align: right;">0.000</td>
<td style="text-align: right;">582.695</td>
<td style="text-align: right;">41.731%</td>
</tr>
<tr class="even">
<td style="text-align: right;">22</td>
<td style="text-align: right;">0.90%</td>
<td style="text-align: right;">582.695</td>
<td style="text-align: right;">5.244</td>
<td style="text-align: right;">0.000</td>
<td style="text-align: right;">577.450</td>
<td style="text-align: right;">42.255%</td>
</tr>
<tr class="odd">
<td style="text-align: right;">23</td>
<td style="text-align: right;">0.90%</td>
<td style="text-align: right;">577.450</td>
<td style="text-align: right;">5.197</td>
<td style="text-align: right;">0.000</td>
<td style="text-align: right;">572.253</td>
<td style="text-align: right;">42.775%</td>
</tr>
<tr class="even">
<td style="text-align: right;">24</td>
<td style="text-align: right;">0.90%</td>
<td style="text-align: right;">572.253</td>
<td style="text-align: right;">5.150</td>
<td style="text-align: right;">0.000</td>
<td style="text-align: right;">567.103</td>
<td style="text-align: right;">43.290%</td>
</tr>
<tr class="odd">
<td style="text-align: right;">25</td>
<td style="text-align: right;">0.90%</td>
<td style="text-align: right;">567.103</td>
<td style="text-align: right;">5.104</td>
<td style="text-align: right;">0.000</td>
<td style="text-align: right;">561.999</td>
<td style="text-align: right;">43.800%</td>
</tr>
<tr class="even">
<td style="text-align: right;">26</td>
<td style="text-align: right;">0.90%</td>
<td style="text-align: right;">561.999</td>
<td style="text-align: right;">5.058</td>
<td style="text-align: right;">0.000</td>
<td style="text-align: right;">556.941</td>
<td style="text-align: right;">44.306%</td>
</tr>
<tr class="odd">
<td style="text-align: right;">27</td>
<td style="text-align: right;">0.90%</td>
<td style="text-align: right;">556.941</td>
<td style="text-align: right;">5.012</td>
<td style="text-align: right;">0.000</td>
<td style="text-align: right;">551.929</td>
<td style="text-align: right;">44.807%</td>
</tr>
<tr class="even">
<td style="text-align: right;">28</td>
<td style="text-align: right;">0.90%</td>
<td style="text-align: right;">551.929</td>
<td style="text-align: right;">4.967</td>
<td style="text-align: right;">0.000</td>
<td style="text-align: right;">546.961</td>
<td style="text-align: right;">45.304%</td>
</tr>
<tr class="odd">
<td style="text-align: right;">29</td>
<td style="text-align: right;">0.90%</td>
<td style="text-align: right;">546.961</td>
<td style="text-align: right;">4.923</td>
<td style="text-align: right;">0.000</td>
<td style="text-align: right;">542.039</td>
<td style="text-align: right;">45.796%</td>
</tr>
<tr class="even">
<td style="text-align: right;">30</td>
<td style="text-align: right;">0.90%</td>
<td style="text-align: right;">542.039</td>
<td style="text-align: right;">4.878</td>
<td style="text-align: right;">0.000</td>
<td style="text-align: right;">537.160</td>
<td style="text-align: right;">46.284%</td>
</tr>
<tr class="odd">
<td style="text-align: right;">31</td>
<td style="text-align: right;">0.50%</td>
<td style="text-align: right;">537.160</td>
<td style="text-align: right;">2.686</td>
<td style="text-align: right;">0.000</td>
<td style="text-align: right;">534.475</td>
<td style="text-align: right;">46.553%</td>
</tr>
<tr class="even">
<td style="text-align: right;">32</td>
<td style="text-align: right;">0.50%</td>
<td style="text-align: right;">534.475</td>
<td style="text-align: right;">2.672</td>
<td style="text-align: right;">0.000</td>
<td style="text-align: right;">531.802</td>
<td style="text-align: right;">46.820%</td>
</tr>
<tr class="odd">
<td style="text-align: right;">33</td>
<td style="text-align: right;">0.50%</td>
<td style="text-align: right;">531.802</td>
<td style="text-align: right;">2.659</td>
<td style="text-align: right;">0.000</td>
<td style="text-align: right;">529.143</td>
<td style="text-align: right;">47.086%</td>
</tr>
<tr class="even">
<td style="text-align: right;">34</td>
<td style="text-align: right;">0.50%</td>
<td style="text-align: right;">529.143</td>
<td style="text-align: right;">2.646</td>
<td style="text-align: right;">0.000</td>
<td style="text-align: right;">526.497</td>
<td style="text-align: right;">47.350%</td>
</tr>
<tr class="odd">
<td style="text-align: right;">35</td>
<td style="text-align: right;">0.50%</td>
<td style="text-align: right;">526.497</td>
<td style="text-align: right;">2.632</td>
<td style="text-align: right;">0.000</td>
<td style="text-align: right;">523.865</td>
<td style="text-align: right;">47.614%</td>
</tr>
<tr class="even">
<td style="text-align: right;">36</td>
<td style="text-align: right;">0.50%</td>
<td style="text-align: right;">523.865</td>
<td style="text-align: right;">2.619</td>
<td style="text-align: right;">0.000</td>
<td style="text-align: right;">521.246</td>
<td style="text-align: right;">47.875%</td>
</tr>
<tr class="odd">
<td style="text-align: right;">37</td>
<td style="text-align: right;">0.50%</td>
<td style="text-align: right;">521.246</td>
<td style="text-align: right;">2.606</td>
<td style="text-align: right;">0.000</td>
<td style="text-align: right;">518.639</td>
<td style="text-align: right;">48.136%</td>
</tr>
<tr class="even">
<td style="text-align: right;">38</td>
<td style="text-align: right;">0.50%</td>
<td style="text-align: right;">518.639</td>
<td style="text-align: right;">2.593</td>
<td style="text-align: right;">0.000</td>
<td style="text-align: right;">516.046</td>
<td style="text-align: right;">48.395%</td>
</tr>
<tr class="odd">
<td style="text-align: right;">39</td>
<td style="text-align: right;">0.50%</td>
<td style="text-align: right;">516.046</td>
<td style="text-align: right;">2.580</td>
<td style="text-align: right;">0.000</td>
<td style="text-align: right;">513.466</td>
<td style="text-align: right;">48.653%</td>
</tr>
<tr class="even">
<td style="text-align: right;">40</td>
<td style="text-align: right;">0.50%</td>
<td style="text-align: right;">513.466</td>
<td style="text-align: right;">2.567</td>
<td style="text-align: right;">0.000</td>
<td style="text-align: right;">510.899</td>
<td style="text-align: right;">48.910%</td>
</tr>
<tr class="odd">
<td style="text-align: right;">41</td>
<td style="text-align: right;">0.50%</td>
<td style="text-align: right;">510.899</td>
<td style="text-align: right;">2.554</td>
<td style="text-align: right;">0.000</td>
<td style="text-align: right;">508.344</td>
<td style="text-align: right;">49.166%</td>
</tr>
<tr class="even">
<td style="text-align: right;">42</td>
<td style="text-align: right;">0.50%</td>
<td style="text-align: right;">508.344</td>
<td style="text-align: right;">2.542</td>
<td style="text-align: right;">0.000</td>
<td style="text-align: right;">505.802</td>
<td style="text-align: right;">49.420%</td>
</tr>
<tr class="odd">
<td style="text-align: right;">43</td>
<td style="text-align: right;">0.50%</td>
<td style="text-align: right;">505.802</td>
<td style="text-align: right;">2.529</td>
<td style="text-align: right;">0.000</td>
<td style="text-align: right;">503.273</td>
<td style="text-align: right;">49.673%</td>
</tr>
<tr class="even">
<td style="text-align: right;">44</td>
<td style="text-align: right;">0.50%</td>
<td style="text-align: right;">503.273</td>
<td style="text-align: right;">2.516</td>
<td style="text-align: right;">0.000</td>
<td style="text-align: right;">500.757</td>
<td style="text-align: right;">49.924%</td>
</tr>
<tr class="odd">
<td style="text-align: right;">45</td>
<td style="text-align: right;">0.50%</td>
<td style="text-align: right;">500.757</td>
<td style="text-align: right;">2.504</td>
<td style="text-align: right;">0.000</td>
<td style="text-align: right;">498.253</td>
<td style="text-align: right;">50.175%</td>
</tr>
<tr class="even">
<td style="text-align: right;">46</td>
<td style="text-align: right;">0.30%</td>
<td style="text-align: right;">498.253</td>
<td style="text-align: right;">1.495</td>
<td style="text-align: right;">0.000</td>
<td style="text-align: right;">496.758</td>
<td style="text-align: right;">50.324%</td>
</tr>
<tr class="odd">
<td style="text-align: right;">47</td>
<td style="text-align: right;">0.30%</td>
<td style="text-align: right;">496.758</td>
<td style="text-align: right;">1.490</td>
<td style="text-align: right;">0.000</td>
<td style="text-align: right;">495.268</td>
<td style="text-align: right;">50.473%</td>
</tr>
<tr class="even">
<td style="text-align: right;">48</td>
<td style="text-align: right;">0.30%</td>
<td style="text-align: right;">495.268</td>
<td style="text-align: right;">1.486</td>
<td style="text-align: right;">0.000</td>
<td style="text-align: right;">493.782</td>
<td style="text-align: right;">50.622%</td>
</tr>
<tr class="odd">
<td style="text-align: right;">49</td>
<td style="text-align: right;">0.30%</td>
<td style="text-align: right;">493.782</td>
<td style="text-align: right;">1.481</td>
<td style="text-align: right;">0.000</td>
<td style="text-align: right;">492.301</td>
<td style="text-align: right;">50.770%</td>
</tr>
<tr class="even">
<td style="text-align: right;">50</td>
<td style="text-align: right;">0.30%</td>
<td style="text-align: right;">492.301</td>
<td style="text-align: right;">1.477</td>
<td style="text-align: right;">0.000</td>
<td style="text-align: right;">490.824</td>
<td style="text-align: right;">50.918%</td>
</tr>
<tr class="odd">
<td style="text-align: right;">51</td>
<td style="text-align: right;">0.30%</td>
<td style="text-align: right;">490.824</td>
<td style="text-align: right;">1.472</td>
<td style="text-align: right;">0.000</td>
<td style="text-align: right;">489.352</td>
<td style="text-align: right;">51.065%</td>
</tr>
<tr class="even">
<td style="text-align: right;">52</td>
<td style="text-align: right;">0.30%</td>
<td style="text-align: right;">489.352</td>
<td style="text-align: right;">1.468</td>
<td style="text-align: right;">0.000</td>
<td style="text-align: right;">487.884</td>
<td style="text-align: right;">51.212%</td>
</tr>
<tr class="odd">
<td style="text-align: right;">53</td>
<td style="text-align: right;">0.30%</td>
<td style="text-align: right;">487.884</td>
<td style="text-align: right;">1.464</td>
<td style="text-align: right;">0.000</td>
<td style="text-align: right;">486.420</td>
<td style="text-align: right;">51.358%</td>
</tr>
<tr class="even">
<td style="text-align: right;">54</td>
<td style="text-align: right;">0.30%</td>
<td style="text-align: right;">486.420</td>
<td style="text-align: right;">1.459</td>
<td style="text-align: right;">0.000</td>
<td style="text-align: right;">484.961</td>
<td style="text-align: right;">51.504%</td>
</tr>
<tr class="odd">
<td style="text-align: right;">55</td>
<td style="text-align: right;">0.30%</td>
<td style="text-align: right;">484.961</td>
<td style="text-align: right;">1.455</td>
<td style="text-align: right;">0.000</td>
<td style="text-align: right;">483.506</td>
<td style="text-align: right;">51.649%</td>
</tr>
<tr class="even">
<td style="text-align: right;">56</td>
<td style="text-align: right;">0.30%</td>
<td style="text-align: right;">483.506</td>
<td style="text-align: right;">1.451</td>
<td style="text-align: right;">0.000</td>
<td style="text-align: right;">482.055</td>
<td style="text-align: right;">51.794%</td>
</tr>
<tr class="odd">
<td style="text-align: right;">57</td>
<td style="text-align: right;">0.30%</td>
<td style="text-align: right;">482.055</td>
<td style="text-align: right;">1.446</td>
<td style="text-align: right;">0.000</td>
<td style="text-align: right;">480.609</td>
<td style="text-align: right;">51.939%</td>
</tr>
<tr class="even">
<td style="text-align: right;">58</td>
<td style="text-align: right;">0.30%</td>
<td style="text-align: right;">480.609</td>
<td style="text-align: right;">1.442</td>
<td style="text-align: right;">0.000</td>
<td style="text-align: right;">479.167</td>
<td style="text-align: right;">52.083%</td>
</tr>
<tr class="odd">
<td style="text-align: right;">59</td>
<td style="text-align: right;">0.30%</td>
<td style="text-align: right;">479.167</td>
<td style="text-align: right;">1.438</td>
<td style="text-align: right;">0.000</td>
<td style="text-align: right;">477.730</td>
<td style="text-align: right;">52.227%</td>
</tr>
<tr class="even">
<td style="text-align: right;">60</td>
<td style="text-align: right;">不适用</td>
<td style="text-align: right;">477.730</td>
<td style="text-align: right;">0.000</td>
<td style="text-align: right;">477.730</td>
<td style="text-align: right;">0.000</td>
<td style="text-align: right;">52.227%</td>
</tr>
</tbody>
</table>
<p>核对结论： - 第 7 天累计自然取消约 30.996%，留存约 690.036 单。 - 第
59 天累计自然取消约 52.227%，留存约 477.730 单。 - 第 60 天约 477.730
单因规则强关。自然取消期望 522.270 单+强关期望 477.730 单=1000 单。 -
总关闭率在第 60 天达到 100%，不表示自然取消率为
100%。本曲线没有为了贴合原白皮书的未核验百分比而调整参数。</p>
<h3 id="还在等待的订单不能再从零天折扣一次">5.6
还在等待的订单不能再从零天折扣一次</h3>
<p>如果一组订单已经撑过第 a 天，预测它们撑过第 b 天的概率应为：</p>
<p><strong>P(T&gt;b | T&gt;a)=S_b/S_a（b&gt;a，S_a&gt;0）。</strong></p>
<p>其中 T
是自然取消发生日。来源是条件概率定义，且使用相同人群、相同目标机制的生存曲线。若人群构成不同，应重新条件化。</p>
<p>例如有 100 单已撑过第 7 天，预测其到第 14 天的留存：
100×S_14/S_7=100×0.620762454/0.690036125≈89.961 单。</p>
<p>错误算法 100×S_14≈62.076 单，把前 7
天的取消又扣了一遍。该计算仍只代表期望；真实备货还要考虑预测不确定性、交付赔付、取消后可转售性和服务分位数，不能照着均值机械裁剪。</p>
<h3 id="没有可识别性时诚实给出边界">5.7
没有可识别性时，诚实给出边界</h3>
<p>以“第 59 天以前是否自然取消”为结局。假设 N=1000 单中： -
已观察自然取消 C=200 单； - 到第 59 天完整观察、没有自然取消 K=200 单；
- 此前发货而无法看到其不发货潜在结局 M=600 单。</p>
<p>在事件定义一致、观察到的取消和完整未取消结局可用于目标设定的前提下，不附加独立删失等识别假设时：</p>
<p><strong>C/N ≤ 第 59 天自然取消率 ≤ (C+M)/N。</strong></p>
<p>因此边界是 <strong>20%～80%</strong>。下界假设未知的 600
单都不取消；上界假设它们都取消。这是信息不足的范围，不是置信区间，也不是说两个极端同样可能。</p>
<p>如果后半段没有任何在险订单，后半段的曲线来自外推或其他群体借用，不是本群体数据识别出来的。经验贝叶斯平滑可以降低小样本噪声，但不能修复缺乏支持或未观测混杂。</p>
<p>例如全局风险 10%、伪样本量 m=100、本 SKU R=10、C=2：平滑后
p=(2+100×0.10)/(10+100)=12/110≈10.909%。m
的单位可理解为“单”，是先验强度，不是实际新增的订单；10
单自身的原始风险是 20%。若
R=0，平滑结果完全来自先验，应显式标为借用信息。m
应用训练数据与时间外验证选择，不存在普遍最优的 100～500 区间。</p>
<h3 id="小项目与答案">5.8 小项目与答案</h3>
<p><strong>任务 A</strong>：把第 1 天风险率由 18% 改成 20%，其他 1～59
天风险率不变，问第 59 天预计留存如何变化？</p>
<p><strong>答案</strong>：只有第一项从 0.82 变成 0.80，因此
B'_59=B_59×0.80/0.82≈466.078 单，减少约 11.652 单。不是简单减少 20
单，因为原来多留下的 20 单中一部分也会在后面取消。</p>
<p><strong>任务 B</strong>：某商品第 20 天以后 R_t 全为 0，模型仍画到第
59 天，能叫“经历史验证的该商品曲线”吗？</p>
<p><strong>答案</strong>：不能。可以画模型外推或借用先验的曲线，但必须标注无直接支持区段、给出假设与不确定性，并寻找足够长等待期的可比数据。补零、平滑或增加计算量都不能恢复不存在的信息。</p>
<hr />
