{
  "title": "三商品全式与混杂识别",
  "description": "三商品全式与混杂识别：本章所有数据都为匿名合成教学数据。本地代码不连接生产系统，不改价、不下单、不投放。执行证据分层：三商品回归与 sklearn 梯度提升树确实拟合；随机动态规划确实求解；深度网络、视觉编码器和 Prophet 没有训练或运行。模拟数据上的漂亮",
  "type": "forecast",
  "unit": "model-causal-three",
  "weight": 65,
  "outputs": [
    "HTML"
  ]
}

<p class="check">模拟教学与独立审查范围内的实际代码。<a href="/forecast/forecast-model-labs.zip" download>下载模型实验 r3</a>。Prophet、TFT、DeepAR和视觉编码器未运行；不得把分解算术或张量校验称为深度训练。</p><details><summary>共同运行方法与能力边界</summary><h2
id="模型补课从价格混杂到真正跑过的树">模型补课：从价格混杂到真正跑过的树</h2>
<blockquote>
<p>本章所有数据都为匿名合成教学数据。本地代码不连接生产系统，不改价、不下单、不投放。执行证据分层：三商品回归与
sklearn 梯度提升树确实拟合；随机动态规划确实求解；深度网络、视觉编码器和
Prophet 没有训练或运行。模拟数据上的漂亮数字不能证明实际业务收益。</p>
</blockquote>
<h2 id="课程与运行入口">课程与运行入口</h2>
<table>
<colgroup>
<col style="width: 20%" />
<col style="width: 20%" />
<col style="width: 20%" />
<col style="width: 20%" />
<col style="width: 20%" />
</colgroup>
<thead>
<tr class="header">
<th>课 ID</th>
<th>要回答的问题</th>
<th>关联白皮书项</th>
<th>输入</th>
<th>本轮证据</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>model-causal-three</td>
<td>三商品价格如何共同影响需求，为什么降价数据会估出反号？</td>
<td>E01–E03</td>
<td>three_products.csv、elasticity_truth.json</td>
<td>1,008行输入、三种拟合、价格情景、补货缺口、毛利与非法输入检查</td>
</tr>
<tr class="even">
<td>model-pricing-stochastic</td>
<td>需求未发生时，三期怎样选价？</td>
<td>M01、M03、M04；保留M02确定性基础</td>
<td>pricing_scenarios.csv、pricing_config.json、price_response.csv</td>
<td>Bellman全部状态、八路径、固定价和预定序列对照</td>
</tr>
<tr class="odd">
<td>model-tree-trained</td>
<td>规则、线性、树用同样时间协议究竟表现如何？</td>
<td>A05、G08</td>
<td>tree_features.csv</td>
<td>实际训练、验证选参、独立测试、逐行预测、按SKU与特征消融</td>
</tr>
<tr class="even">
<td>model-deep-inputs</td>
<td>深度模型究竟吃哪些张量，图像向量怎样参加新品类比？</td>
<td>A06、C07</td>
<td>deep_inputs.json、image_vectors.csv、trend_history.csv</td>
<td>输入形状、时点、模拟路径分位数、8款向量类比、聚类、整款留出</td>
</tr>
<tr class="odd">
<td>model-prophet-decomposition</td>
<td>Prophet中的趋势、季节、事件是什么？</td>
<td>A04</td>
<td>prophet_components.csv</td>
<td>分量算术和统一回测接口；Prophet库本身未运行</td>
</tr>
</tbody>
</table>
<p>下载运行包 forecast-model-labs.zip，解压后在目录内执行：</p>
<div class="sourceCode" id="cb1"><pre
class="sourceCode bash"><code class="sourceCode bash"><span id="cb1-1"><a href="#cb1-1" aria-hidden="true" tabindex="-1"></a><span class="ex">python</span> run_models.py</span>
<span id="cb1-2"><a href="#cb1-2" aria-hidden="true" tabindex="-1"></a><span class="ex">python</span> tests/test_labs.py</span>
<span id="cb1-3"><a href="#cb1-3" aria-hidden="true" tabindex="-1"></a><span class="ex">python</span> verify_reproducibility.py</span></code></pre></div>
<p>无需访问在线业务系统。输入文件已经附上；generate_data.py
仅用于重建合成夹具，会覆盖本包 data 中的同名文件。完整数值输出在
outputs/results.json，逐行测试预测在
outputs/tree_test_predictions.csv。测试与运行依赖固定版本见
requirements.txt；若环境未安装，需要先安装
numpy、scipy、scikit-learn。不可用库不是静默跳过：本次环境没有
Prophet、torch、LightGBM 或 XGBoost，运行包没有声称使用这些库训练。</p>
</details><h2
id="model-causal-three三商品全式与混杂识别">model-causal-three：三商品全式与混杂识别</h2>
<h3 id="业务问题与单位">1. 业务问题与单位</h3>
<p>同一品类三个商品A、B、C，基准日需求分别100、80、60件，基准售价分别10、12、8元/件。A提价可能把客人推给B，也可能使搭配购买的C减少。预测对象是潜在需求均值，不是已经被库存上限截掉的销量。当前小实验没有缺货删失，observed_sales等于latent_demand；若把stockout改成1，验证器拒绝直接拿这份销量估弹性。</p>
<p>每行一SKU一天；每个设计168天，共2×168×3＝1,008行。文件中的随机版
randomized
在每个8天区组内把三商品价格的高低组合全部覆盖，并用固定随机种子打乱顺序；隐藏需求冲击在区组内相同。它是有意平衡的外生价格教学试验，不是真实门店A/B实验。confounded版把A价与隐藏需求冲击关联，代表运营人员看到旺季信号后抬价。</p>
<p>先写含相对竞价的一般式：</p>
<pre class="text"><code>ln(Q_i / Q_i0)
 = α_i + β_ii ln(P_i / P_i0)
   + Σ_{j≠i} β_ij ln[(P_j / R) / (P_j0 / R0)]
   + γ_iᵀX + ε_i</code></pre>
<p>逐符号解释：</p>
<ul>
<li>i是被预测的商品，j是其他商品。矩阵的行是需求商品，列是被改变价格的商品，不能转置着解读。</li>
<li>Q_i是该期需求均值，Q_i0是可比基准需求，均为件。P_i、P_i0为当前和基准售价，均为元/件。比值无量纲，才可取自然对数ln。</li>
<li>R是外部品类参考价，R0为它的基准值。本题固定R＝R0＝10元/件，所以相对竞价项化成ln(P_j/P_j0)。外部参考价必须在预测时点已可得。</li>
<li>α_i是基准修正；β_ii为自价系数，β_ij为交叉系数。γ_iᵀX是每项控制变量与其系数相乘再相加，例如γ_promo×已公布促销标记。</li>
<li>ε_i是没被模型解释的变化，不可以假装它一定与价格独立。</li>
<li>弹性是局部比例导数，不是“涨价1元”的绝对销量变化。β_ij＝0.35表示其他条件固定时，j价小幅增加1%，i需求约增加0.35%。大改价必须回到指数式。</li>
</ul>
<p>本题结构系数表：</p>
<table>
<thead>
<tr class="header">
<th>需求商品＼价格商品</th>
<th style="text-align: right;">A价</th>
<th style="text-align: right;">B价</th>
<th style="text-align: right;">C价</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>A需求</td>
<td style="text-align: right;">−1.40</td>
<td style="text-align: right;">+0.35</td>
<td style="text-align: right;">−0.15</td>
</tr>
<tr class="even">
<td>B需求</td>
<td style="text-align: right;">+0.40</td>
<td style="text-align: right;">−1.20</td>
<td style="text-align: right;">−0.10</td>
</tr>
<tr class="odd">
<td>C需求</td>
<td style="text-align: right;">−0.20</td>
<td style="text-align: right;">−0.15</td>
<td style="text-align: right;">−0.90</td>
</tr>
</tbody>
</table>
<p>A与B的正交叉项在这个模拟设定中代表替代；A/B与C的负项代表互补。品类总需求不守恒：价格可以让顾客离开整个品类，也可以带来新顾客。</p>
<h3 id="为什么类别均价会改变导数">2. 为什么类别均价会改变导数</h3>
<p>若R并不是固定外部基准，而是R＝Σ_k w_kP_k，w固定且和为1，则：</p>
<pre class="text"><code>a_k = ∂ln R / ∂ln P_k = w_k P_k / R
∂ln Q_i / ∂ln P_k
 = β_ii·1{k=i} + Σ_{j≠i} β_ij·(1{j=k} − a_k)</code></pre>
<p>1{条件}在条件成立时为1，否则为0。因为调整P_k同时改变共同分母R，所以β_ik通常不再单独等于纯交叉弹性。若权重也随销量变化，还要加入权重变化的导数。本实验固定外部R，避免把这个联动藏起来。</p>
<h3 id="一次联合价格情景逐项代入">3. 一次联合价格情景，逐项代入</h3>
<p>现在A从10变10.8，B保持12，C从8降到7.36。促销与隐藏冲击保持基准值0。对数变化：</p>
<pre class="text"><code>x_A = ln(10.8/10) = 0.0769610411
x_B = ln(12/12) = 0
x_C = ln(7.36/8) = −0.0833816089</code></pre>
<p>A的每一项：−1.4×0.0769610411＋0.35×0−0.15×(−0.0833816089)＝−0.0952382162。因此Q_A＝100×exp(−0.0952382162)＝90.915633件。</p>
<p>B：0.4×0.0769610411−1.2×0−0.1×(−0.0833816089)＝0.0391225773，所以Q_B＝80×exp(0.0391225773)＝83.191836件。</p>
<p>C：−0.2×0.0769610411−0.15×0−0.9×(−0.0833816089)＝0.0596512398，所以Q_C＝60×exp(0.0596512398)＝63.687977件。</p>
<p>品类需求由240变为237.795446件，不能强行把三项缩放回240。程序使用随机版训练得到的价格系数和单独给定的基准需求做这次相对变化预测；并非用混杂版斜率改价。由于这个理想平衡模拟的价格系数恢复近乎精确，手算与程序相符。</p>
<p>若当前可售库存为[80,60,50]，无补货销量分别是min(Q,I)＝[80,60,50]。按一件取整的建议缺口为：</p>
<pre class="text"><code>G_i = max(0, ceil(Q_i) − I_i)
G = [11,24,14] 件</code></pre>
<p>ceil向上取整。若单位成本为[6,7,4]元，无补货情景销售毛利为(10.8−6)×80＋(12−7)×60＋(7.36−4)×50＝852元；假设建议补货全部及时到货且需求实现，则销售毛利为1,066.345820元。这是售价减单位销售成本的毛利，未计尾货、运费、整箱、MOQ、采购现金流和报废，不是净利润，也不是批准采购。</p>
<h3 id="真实拟合与反号">4. 真实拟合与反号</h3>
<p>数据生成机制是：</p>
<pre class="text"><code>ln(Q_i / Q_i0) = Σ_j β_ij x_j + 0.12·promo + 0.4·z</code></pre>
<p>z是隐藏需求冲击，只存在于模拟真值。随机版价格高低组合与z在训练区组内正交。混杂版则令A的对数相对价x_A＝0.12z＋0.03s_A，其中s_A为−1/+1的价格扰动。旺需求时价格也高，于是省略z后把旺需求错误归因于提价。</p>
<p>训练仅使用day
0–111；day112–139留作验证，day140–167留作测试。此次“价格识别”验收只检查训练设计下能否恢复已知真值，不把留出时间块的存在当作已经完成真实因果验证。代码没有用这些留出标签选价格系数，也没有报告未经执行的样本外因果效果。</p>
<p>最小二乘不是手填答案。对每SKU构造设计矩阵的一行：[1,x_A,x_B,x_C,promo]，目标是一行ln(Q_i/Q_i0)，调用np.linalg.lstsq实际求解，使各行预测残差平方和最小。训练矩阵满秩才允许求解。输出系数顺序为[截距,A价,B价,C价,promo]。</p>
<p>实际输出：</p>
<ul>
<li>随机版A自价系数约−1.400000，与真值一致；整个价格系数矩阵最大误差小于10⁻⁸。</li>
<li>混杂版忽略z时，A自价系数约+1.154101。不是“顾客更喜欢贵价”的证据。</li>
<li>仅教学诊断的oracle再加入z后，A自价系数回到−1.400000。真实业务中z通常拿不到；不能把该隐藏列塞进线上特征来宣布解决混杂。</li>
<li>随机版只随机化价格，不随机化promo。由于promo与隐藏冲击在这批训练区组里有关，拟合的promo系数约0.368，而生成真值为0.12。价格试验恢复成功不表示控制变量的所有系数也可解释为因果。</li>
</ul>
<p>该数据无额外测量噪声，价格组合又特意平衡，近乎精确的恢复是教学验算优势，不是对真实数据精度的保证。现实还需识别缺货删失、同时促销、曝光差异、季节、反向因果、溢出、价格共同变化与实验单位干扰。仅多放一些控制列不能自动保证没有遗漏混杂。</p>
<h3 id="学员验收">5. 学员验收</h3>
<ol type="1">
<li>不运行模型，先把A的三个项逐项算完，再对照90.915633。</li>
<li>检查“行需求、列价格”，独立解释β_BA与β_AB为何不是同一个数字。</li>
<li>把price_A改成0、stockout改成1、price_available_at改到预测后：程序必须拒绝，不自动把0补成1。</li>
<li>改成超出训练支持的价格20元：情景函数必须报外推错误。落在价格范围内也不是因果可用的充分条件。</li>
<li>说明ln(Q)不接受零需求；log1p改变模型与弹性含义。遇到真实零需求应选适当的计数/零膨胀模型或分开建模，不偷偷删零。</li>
<li>能说出混杂版反号、oracle限制，以及缺口不是订单。</li>
</ol>
