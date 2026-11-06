{
  "title": "第三章 把箱规 MOQ 仓容和车次写成 MILP",
  "description": "第三章 把箱规 MOQ 仓容和车次写成 MILP：白皮书范围：第一部分第三层。 MILP 是混合整数线性规划：一部分未知数只能取整数或 0/1，目标及约束由加减法和“常数×未知数”组成。它不是一个预测模型，而是拿预测与成本选择可执行方案。",
  "type": "forecast",
  "unit": "milp",
  "weight": 22,
  "outputs": [
    "HTML"
  ]
}

<p class="check">本课使用模拟数据与明确假设。数学推导、枚举和数据核验不等于真实业务模型有效。配套包包含60天教学曲线及约束枚举，不是完整订单训练集。<br><a href="/forecast/planning-math-labs.zip" download>下载数学实验、完整教材与只读验证器</a></p><h2 id="第三章-把箱规-moq-仓容和车次写成-milp">第三章 把箱规 MOQ
仓容和车次写成 MILP</h2>
<p><strong>白皮书范围：第一部分第三层。</strong> MILP
是混合整数线性规划：一部分未知数只能取整数或
0/1，目标及约束由加减法和“常数×未知数”组成。它不是一个预测模型，而是拿预测与成本选择可执行方案。</p>
<p>方法出处：<a
href="https://developers.google.com/optimization/mip/mip_example">Google
OR-Tools
官方混合整数规划示例</a>展示整数变量、线性约束和目标函数。本章箱规、MOQ
和枚举数据另行设计，没有复制其数值。</p>
<h3 id="为什么不能把两个建议数各自向上取整">3.1
为什么不能把两个建议数各自向上取整</h3>
<p>两件商品的净需求分别为 17 件、11 件。A 每箱 6 件，B 每箱 4
件；各自向上取整会订 A=18、B=12。但两者共占 72 L，而仓容只有 64
L，组合起来不可执行。必须一起做决策。</p>
<p>所有输入如下，全部模拟：</p>
<table>
<thead>
<tr class="header">
<th>参数</th>
<th style="text-align: right;">A</th>
<th style="text-align: right;">B</th>
<th>单位与业务来源</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>净需求 r_i</td>
<td style="text-align: right;">17</td>
<td style="text-align: right;">11</td>
<td>件；需求预测扣除可用库存及可靠在途后的缺口</td>
</tr>
<tr class="even">
<td>每箱件数 b_i</td>
<td style="text-align: right;">6</td>
<td style="text-align: right;">4</td>
<td>件/箱；包装主数据</td>
</tr>
<tr class="odd">
<td>最小起订量 M_i</td>
<td style="text-align: right;">12</td>
<td style="text-align: right;">8</td>
<td>件；供应合同条件</td>
</tr>
<tr class="even">
<td>单件库容 v_i</td>
<td style="text-align: right;">2</td>
<td style="text-align: right;">3</td>
<td>L/件；包装尺寸折算</td>
</tr>
<tr class="odd">
<td>单件不足惩罚 π_i</td>
<td style="text-align: right;">8</td>
<td style="text-align: right;">6</td>
<td>元/件；本例人为设定，不等于采购成本</td>
</tr>
<tr class="even">
<td>单件多余惩罚 h_i</td>
<td style="text-align: right;">1</td>
<td style="text-align: right;">1</td>
<td>元/件；本例单期持有/剩余成本设定</td>
</tr>
<tr class="odd">
<td>每次启订成本 f_i</td>
<td style="text-align: right;">3</td>
<td style="text-align: right;">3</td>
<td>元/商品；本例人为设定</td>
</tr>
</tbody>
</table>
<p>另设仓容 W=64 L，单车容量 V=36 L/车，最多 K=2 车，每车固定成本 g=12
元/车。每箱 A 占 6×2=12 L，每箱 B 占 4×3=12 L，故每车恰能放最多 3
箱。本例忽略车厢形状，所有箱体可兼容装载，无重量等其他限制。</p>
<p>这里的目标只包含不足、多余、启订和运输的教学成本，<strong>不是完整利润</strong>。真实采购成本、现金预算、保质期和多期库存需要另加，不能声称本例就是实际总成本最优。</p>
<h3 id="决策变量不是输入参数">3.2 决策变量不是输入参数</h3>
<ul>
<li>n_i：订购箱数，非负整数，单位箱。</li>
<li>q_i=b_i n_i：订购件数，件。</li>
<li>y_i：是否启订；订购为 1，不订为 0，无单位。</li>
<li>u_i：不足件数，非负，件。</li>
<li>e_i：多余件数，非负，件。</li>
<li>k：车次数，非负整数，单位车。</li>
</ul>
<p>最小化目标：</p>
<p><strong>J = 8u_A+6u_B+e_A+e_B+3y_A+3y_B+12k。</strong></p>
<p>J 的单位是元。约束是：</p>
<ol type="1">
<li><strong>q_A=6n_A；q_B=4n_B。</strong> 箱规。</li>
<li><strong>2y_A≤n_A≤5y_A；2y_B≤n_B≤5y_B。</strong> 关闭时 0
箱；启订至少 2 箱，分别满足 MOQ 12、8 件。5
箱是仓容导出的有效上界，不是任意巨大常数。</li>
<li><strong>q_A+u_A-e_A=17；q_B+u_B-e_B=11。</strong> 需求平衡。</li>
<li><strong>2q_A+3q_B≤64。</strong> 仓容，左右单位均为 L。</li>
<li><strong>2q_A+3q_B≤36k；0≤k≤2。</strong> 运力与车数。</li>
<li><strong>n_A,n_B,k
为整数；y_A,y_B∈{0,1}；u_A,u_B,e_A,e_B≥0。</strong></li>
</ol>
<p>为何不必额外规定 u_i 和 e_i
不能同时为正？本例它们的惩罚系数均为正，如果同时为正，可以各减相同数量，平衡式不变，目标成本会下降，所以最优解不会这样做。若以后把系数改成负数或加入其他约束，此结论要重新检查。</p>
<p><strong>一般 MOQ 写法</strong>：当最小起订量是 M_i 件、箱规 b_i
件/箱时，最少箱数是 ⌈M_i/b_i⌉，因此可写 ⌈M_i/b_i⌉y_i≤n_i≤U_i y_i。U_i
是有业务依据的最大箱数。例如 MOQ=10、箱规=6，启订至少 2 箱，即 12
件，并非允许订 10 件。</p>
<h3 id="把全部可行方案列出来验证">3.3 把全部可行方案列出来验证</h3>
<p>本例每箱都是 12 L，仓容允许最多 5 箱。单 SKU 只能取 0 或至少 2
箱。因此只需检查下表 12 种箱数组合。对每组取最低所需车数
k=⌈(n_A+n_B)/3⌉；每多开一车成本增加且没有收益，所以最低车数足够。</p>
<table>
<colgroup>
<col style="width: 9%" />
<col style="width: 9%" />
<col style="width: 9%" />
<col style="width: 9%" />
<col style="width: 9%" />
<col style="width: 9%" />
<col style="width: 9%" />
<col style="width: 9%" />
<col style="width: 9%" />
<col style="width: 9%" />
<col style="width: 9%" />
</colgroup>
<thead>
<tr class="header">
<th style="text-align: right;">A 箱数</th>
<th style="text-align: right;">B 箱数</th>
<th style="text-align: right;">A 件数</th>
<th style="text-align: right;">B 件数</th>
<th style="text-align: right;">占容 L</th>
<th style="text-align: right;">车数</th>
<th style="text-align: right;">A 不足</th>
<th style="text-align: right;">B 不足</th>
<th style="text-align: right;">A 多余</th>
<th style="text-align: right;">B 多余</th>
<th style="text-align: right;">J 元</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td style="text-align: right;">0</td>
<td style="text-align: right;">0</td>
<td style="text-align: right;">0</td>
<td style="text-align: right;">0</td>
<td style="text-align: right;">0</td>
<td style="text-align: right;">0</td>
<td style="text-align: right;">17</td>
<td style="text-align: right;">11</td>
<td style="text-align: right;">0</td>
<td style="text-align: right;">0</td>
<td style="text-align: right;">202</td>
</tr>
<tr class="even">
<td style="text-align: right;">0</td>
<td style="text-align: right;">2</td>
<td style="text-align: right;">0</td>
<td style="text-align: right;">8</td>
<td style="text-align: right;">24</td>
<td style="text-align: right;">1</td>
<td style="text-align: right;">17</td>
<td style="text-align: right;">3</td>
<td style="text-align: right;">0</td>
<td style="text-align: right;">0</td>
<td style="text-align: right;">169</td>
</tr>
<tr class="odd">
<td style="text-align: right;">0</td>
<td style="text-align: right;">3</td>
<td style="text-align: right;">0</td>
<td style="text-align: right;">12</td>
<td style="text-align: right;">36</td>
<td style="text-align: right;">1</td>
<td style="text-align: right;">17</td>
<td style="text-align: right;">0</td>
<td style="text-align: right;">0</td>
<td style="text-align: right;">1</td>
<td style="text-align: right;">152</td>
</tr>
<tr class="even">
<td style="text-align: right;">0</td>
<td style="text-align: right;">4</td>
<td style="text-align: right;">0</td>
<td style="text-align: right;">16</td>
<td style="text-align: right;">48</td>
<td style="text-align: right;">2</td>
<td style="text-align: right;">17</td>
<td style="text-align: right;">0</td>
<td style="text-align: right;">0</td>
<td style="text-align: right;">5</td>
<td style="text-align: right;">168</td>
</tr>
<tr class="odd">
<td style="text-align: right;">0</td>
<td style="text-align: right;">5</td>
<td style="text-align: right;">0</td>
<td style="text-align: right;">20</td>
<td style="text-align: right;">60</td>
<td style="text-align: right;">2</td>
<td style="text-align: right;">17</td>
<td style="text-align: right;">0</td>
<td style="text-align: right;">0</td>
<td style="text-align: right;">9</td>
<td style="text-align: right;">172</td>
</tr>
<tr class="even">
<td style="text-align: right;">2</td>
<td style="text-align: right;">0</td>
<td style="text-align: right;">12</td>
<td style="text-align: right;">0</td>
<td style="text-align: right;">24</td>
<td style="text-align: right;">1</td>
<td style="text-align: right;">5</td>
<td style="text-align: right;">11</td>
<td style="text-align: right;">0</td>
<td style="text-align: right;">0</td>
<td style="text-align: right;">121</td>
</tr>
<tr class="odd">
<td style="text-align: right;">2</td>
<td style="text-align: right;">2</td>
<td style="text-align: right;">12</td>
<td style="text-align: right;">8</td>
<td style="text-align: right;">48</td>
<td style="text-align: right;">2</td>
<td style="text-align: right;">5</td>
<td style="text-align: right;">3</td>
<td style="text-align: right;">0</td>
<td style="text-align: right;">0</td>
<td style="text-align: right;">88</td>
</tr>
<tr class="even">
<td style="text-align: right;">2</td>
<td style="text-align: right;">3</td>
<td style="text-align: right;">12</td>
<td style="text-align: right;">12</td>
<td style="text-align: right;">60</td>
<td style="text-align: right;">2</td>
<td style="text-align: right;">5</td>
<td style="text-align: right;">0</td>
<td style="text-align: right;">0</td>
<td style="text-align: right;">1</td>
<td style="text-align: right;">71</td>
</tr>
<tr class="odd">
<td style="text-align: right;">3</td>
<td style="text-align: right;">0</td>
<td style="text-align: right;">18</td>
<td style="text-align: right;">0</td>
<td style="text-align: right;">36</td>
<td style="text-align: right;">1</td>
<td style="text-align: right;">0</td>
<td style="text-align: right;">11</td>
<td style="text-align: right;">1</td>
<td style="text-align: right;">0</td>
<td style="text-align: right;">82</td>
</tr>
<tr class="even">
<td style="text-align: right;"><strong>3</strong></td>
<td style="text-align: right;"><strong>2</strong></td>
<td style="text-align: right;"><strong>18</strong></td>
<td style="text-align: right;"><strong>8</strong></td>
<td style="text-align: right;"><strong>60</strong></td>
<td style="text-align: right;"><strong>2</strong></td>
<td style="text-align: right;"><strong>0</strong></td>
<td style="text-align: right;"><strong>3</strong></td>
<td style="text-align: right;"><strong>1</strong></td>
<td style="text-align: right;"><strong>0</strong></td>
<td style="text-align: right;"><strong>49</strong></td>
</tr>
<tr class="odd">
<td style="text-align: right;">4</td>
<td style="text-align: right;">0</td>
<td style="text-align: right;">24</td>
<td style="text-align: right;">0</td>
<td style="text-align: right;">48</td>
<td style="text-align: right;">2</td>
<td style="text-align: right;">0</td>
<td style="text-align: right;">11</td>
<td style="text-align: right;">7</td>
<td style="text-align: right;">0</td>
<td style="text-align: right;">100</td>
</tr>
<tr class="even">
<td style="text-align: right;">5</td>
<td style="text-align: right;">0</td>
<td style="text-align: right;">30</td>
<td style="text-align: right;">0</td>
<td style="text-align: right;">60</td>
<td style="text-align: right;">2</td>
<td style="text-align: right;">0</td>
<td style="text-align: right;">11</td>
<td style="text-align: right;">13</td>
<td style="text-align: right;">0</td>
<td style="text-align: right;">106</td>
</tr>
</tbody>
</table>
<p>最优方案逐步验算： 1. 箱规：18/6=3 箱，8/4=2 箱。 2.
MOQ：18≥12，8≥8。 3. 仓容：18×2+8×3=60≤64 L。 4. 车次：5 箱分两车，3
箱和 2 箱，占容 36 L 和 24 L，均不超过 36 L。 5. 缺口：A 没有不足并剩 1
件；B 少 3 件。 6. 成本：0×8+3×6+1×1+0×1+3+3+2×12=49 元。 7. 因为全部 12
个可行组合均已核对，所以这不是“看起来较好”，而是本例全局最优。</p>
<h3 id="满载率不能写错">3.4 满载率不能写错</h3>
<p>本方案总满载率=60/(36×2)=83.33%。若要求每辆车至少装满
2/3，可以把本例箱子分成 3+2 箱，满足要求。</p>
<p>通用模型中，<strong>总容积≥最低满载率×单车容量×车数</strong>通常只约束平均装载，不保证每辆车都达标，也不保证箱体可装下。若各箱体积不同、不能拆箱，需引入每辆车的分配变量并检查车厢形状、重量、温层和危险品兼容等。不能用一个平均率替代装箱可行性。</p>
<h3 id="一个可运行的枚举检查器">3.5 一个可运行的枚举检查器</h3>
<div class="sourceCode" id="cb1"><pre
class="sourceCode python"><code class="sourceCode python"><span id="cb1-1"><a href="#cb1-1" aria-hidden="true" tabindex="-1"></a><span class="im">from</span> math <span class="im">import</span> ceil</span>
<span id="cb1-2"><a href="#cb1-2" aria-hidden="true" tabindex="-1"></a>rows <span class="op">=</span> []</span>
<span id="cb1-3"><a href="#cb1-3" aria-hidden="true" tabindex="-1"></a><span class="cf">for</span> na <span class="kw">in</span> <span class="bu">range</span>(<span class="dv">6</span>):</span>
<span id="cb1-4"><a href="#cb1-4" aria-hidden="true" tabindex="-1"></a>    <span class="cf">for</span> nb <span class="kw">in</span> <span class="bu">range</span>(<span class="dv">6</span>):</span>
<span id="cb1-5"><a href="#cb1-5" aria-hidden="true" tabindex="-1"></a>        <span class="cf">if</span> na <span class="op">==</span> <span class="dv">1</span> <span class="kw">or</span> nb <span class="op">==</span> <span class="dv">1</span>:  <span class="co"># 启订至少两箱</span></span>
<span id="cb1-6"><a href="#cb1-6" aria-hidden="true" tabindex="-1"></a>            <span class="cf">continue</span></span>
<span id="cb1-7"><a href="#cb1-7" aria-hidden="true" tabindex="-1"></a>        qa, qb <span class="op">=</span> <span class="dv">6</span> <span class="op">*</span> na, <span class="dv">4</span> <span class="op">*</span> nb</span>
<span id="cb1-8"><a href="#cb1-8" aria-hidden="true" tabindex="-1"></a>        volume <span class="op">=</span> <span class="dv">2</span> <span class="op">*</span> qa <span class="op">+</span> <span class="dv">3</span> <span class="op">*</span> qb</span>
<span id="cb1-9"><a href="#cb1-9" aria-hidden="true" tabindex="-1"></a>        k <span class="op">=</span> ceil(volume <span class="op">/</span> <span class="dv">36</span>)</span>
<span id="cb1-10"><a href="#cb1-10" aria-hidden="true" tabindex="-1"></a>        <span class="cf">if</span> volume <span class="op">&gt;</span> <span class="dv">64</span> <span class="kw">or</span> k <span class="op">&gt;</span> <span class="dv">2</span>:</span>
<span id="cb1-11"><a href="#cb1-11" aria-hidden="true" tabindex="-1"></a>            <span class="cf">continue</span></span>
<span id="cb1-12"><a href="#cb1-12" aria-hidden="true" tabindex="-1"></a>        ua, ub <span class="op">=</span> <span class="bu">max</span>(<span class="dv">17</span> <span class="op">-</span> qa, <span class="dv">0</span>), <span class="bu">max</span>(<span class="dv">11</span> <span class="op">-</span> qb, <span class="dv">0</span>)</span>
<span id="cb1-13"><a href="#cb1-13" aria-hidden="true" tabindex="-1"></a>        ea, eb <span class="op">=</span> <span class="bu">max</span>(qa <span class="op">-</span> <span class="dv">17</span>, <span class="dv">0</span>), <span class="bu">max</span>(qb <span class="op">-</span> <span class="dv">11</span>, <span class="dv">0</span>)</span>
<span id="cb1-14"><a href="#cb1-14" aria-hidden="true" tabindex="-1"></a>        cost <span class="op">=</span> <span class="dv">8</span><span class="op">*</span>ua <span class="op">+</span> <span class="dv">6</span><span class="op">*</span>ub <span class="op">+</span> ea <span class="op">+</span> eb <span class="op">+</span> <span class="dv">3</span><span class="op">*</span>(na <span class="op">&gt;</span> <span class="dv">0</span>) <span class="op">+</span> <span class="dv">3</span><span class="op">*</span>(nb <span class="op">&gt;</span> <span class="dv">0</span>) <span class="op">+</span> <span class="dv">12</span><span class="op">*</span>k</span>
<span id="cb1-15"><a href="#cb1-15" aria-hidden="true" tabindex="-1"></a>        rows.append((cost, na, nb, k, qa, qb))</span>
<span id="cb1-16"><a href="#cb1-16" aria-hidden="true" tabindex="-1"></a><span class="cf">assert</span> <span class="bu">len</span>(rows) <span class="op">==</span> <span class="dv">12</span></span>
<span id="cb1-17"><a href="#cb1-17" aria-hidden="true" tabindex="-1"></a><span class="cf">assert</span> <span class="bu">min</span>(rows) <span class="op">==</span> (<span class="dv">49</span>, <span class="dv">3</span>, <span class="dv">2</span>, <span class="dv">2</span>, <span class="dv">18</span>, <span class="dv">8</span>)</span>
<span id="cb1-18"><a href="#cb1-18" aria-hidden="true" tabindex="-1"></a><span class="bu">print</span>(<span class="bu">min</span>(rows))</span></code></pre></div>
<h3 id="小项目与答案">3.6 小项目与答案</h3>
<p><strong>任务 A</strong>：只把仓容从 64 L 增至 72
L，其他不变，重新枚举。<strong>答案</strong>：A=18、B=12，6 箱、2
车，占容 72 L，成本=多余 1+1+启订 6+运输 24=32 元。原方案 49 元到 32
元的差额是本模型的 17 元教学改善，不能当作现实节省。</p>
<p><strong>任务 B</strong>：要求完全不缺货，且仓容仍为 64
L。<strong>答案</strong>：不可行。A 至少 18 件、B 至少 12 件，最少占容
72 L&gt;64
L。正确输出是“约束冲突及原因”，不是悄悄突破仓容。可讨论扩仓、分批到货或改变服务承诺，但这些是新决策，不是求解器自动获得的权限。</p>
<hr />
