{
  "title": "输入张量、概率路径与匿名视觉向量",
  "description": "输入张量、概率路径与匿名视觉向量：本章所有数据都为匿名合成教学数据。本地代码不连接生产系统，不改价、不下单、不投放。执行证据分层：三商品回归与 sklearn 梯度提升树确实拟合；随机动态规划确实求解；深度网络、视觉编码器和 Prophet 没有训练或运行。模拟数据上的漂亮",
  "type": "forecast",
  "unit": "model-deep-inputs",
  "weight": 68,
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
id="model-deep-inputs输入张量概率路径与匿名视觉向量">model-deep-inputs：输入张量、概率路径与匿名视觉向量</h2>
<h3 id="先把吃什么数据讲清楚">1. 先把“吃什么数据”讲清楚</h3>
<p>B＝2条商品序列；L＝4个历史步；H＝3个未来步。每条序列只用训练集算缩放因子，分别为10和20，不能用未来标签均值缩放。输入必须恰好是两个有限正数；NaN、无穷、零、负值或仅给一条尺度均拒绝，不能依赖数组广播悄悄通过。</p>
<table>
<colgroup>
<col style="width: 25%" />
<col style="width: 25%" />
<col style="width: 25%" />
<col style="width: 25%" />
</colgroup>
<thead>
<tr class="header">
<th>数据块</th>
<th>形状</th>
<th>逐轴含义</th>
<th>示例</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>静态static</td>
<td>[2,2]</td>
<td>商品×静态字段</td>
<td>[category_code,base_price]，第一行[0,10]</td>
</tr>
<tr class="even">
<td>历史history</td>
<td>[2,4,3]</td>
<td>商品×历史步×通道</td>
<td>[销量/训练尺度,已发生促销,缩放温度]</td>
</tr>
<tr class="odd">
<td>未来已知future_known</td>
<td>[2,3,3]</td>
<td>商品×预测步×通道</td>
<td>[已公告促销,已发布天气预报,步长/3]</td>
</tr>
<tr class="even">
<td>模拟路径samples</td>
<td>[2,5,3]</td>
<td>商品×抽样路径×预测步</td>
<td>人工设定5条路径，不是模型输出</td>
</tr>
</tbody>
</table>
<p>类别编号0/1是类别标签，不表示商品1比商品0“大一倍”。真实网络应走类别embedding或one-hot路径；本包只检查输入，不把它当连续类别训练。连续价格、温度与销量应各用训练得到的尺度。实际多序列模型还要有有效长度、缺失掩码和padding掩码，不能把补零当真实零销量。</p>
<p>第一条序列的4行历史是：</p>
<pre class="text"><code>[0.8,0,0.2]
[0.9,0,0.3]
[1.0,1,0.1]
[1.2,1,0.2]</code></pre>
<p>第1通道乘回训练尺度10后，是8、9、10、12件。它最后一步为已发生12件，不能把未来第一天的真实需求填进这里。</p>
<p>预测原点为2025-01-10
18:00；未来块的预报发布于当天12:00，合法。未来天气“最终实测值”、下周实际库存、最终促销销量不是未来已知变量。把future_available_at改到原点以后，验收失败。</p>
<h3 id="tft与deepar各把这些块放在哪里">2.
TFT与DeepAR各把这些块放在哪里</h3>
<p>TFT是一类多步预测架构，可区分静态协变量、历史观测协变量和未来已知协变量，并用变量选择、门控、序列编码和注意力等结构组合。常见实现输出各期若干条件分位数。注意力权重或变量权重不是自动成立的因果解释。</p>
<p>DeepAR是一类自回归概率模型，把历史目标、动态协变量与静态商品信息输入循环网络，输出下一步分布的参数，再抽样滚动形成未来路径。连续值可用相应连续分布，计数需选适当计数分布；不能仅因为叫DeepAR就宣称一定输出负二项。训练时真实历史目标可以逐步喂入；多步预测时未知未来目标要用预测分布滚动，不能继续喂真实未来。</p>
<p>符号化写法：</p>
<pre class="text"><code>h_t = RNN(h_{t−1}, [scaled_y_{t−1}, dynamic_x_t, static_embedding])
θ_t = output_head(h_t)
y_t^(s) ~ p(y | θ_t)</code></pre>
<p>h_t为隐藏状态，方括号表示拼接；θ_t为概率分布参数；s表示第几条模拟路径。此式描述数据流，不是本包已经执行过的训练。当前没有torch，未训练TFT/DeepAR，也不拿人工样本冒充它们的预测。</p>
<h3 id="条模拟路径怎样变成p50p90">3. 5条模拟路径怎样变成P50/P90</h3>
<p>第一商品第一天的5个样本为[8,9,10,11,12]件；第二天[7,8,9,10,11]，第三天[6,7,8,9,10]。程序按numpy.quantile的method="higher"计算：</p>
<ul>
<li>第一商品P50＝[10,9,8]；P90＝[12,11,10]。</li>
<li>第二商品P50＝[20,19,18]；P90＝[24,23,22]。</li>
</ul>
<p>“H​​igher”取相邻排序位置中较高的观测样本。5条路径非常少，P90在这里落到最大样本，并不证明90%覆盖已校准。逐期P90之和一般也不等于总需求P90；要算累计需求分位数，应先在同一条路径内加总，再对路径总量取分位数。这批路径人为同向，碰巧相等也不能推广。</p>
<h3 id="款匿名向量的完整类比">4. 8款匿名向量的完整类比</h3>
<p>这些二维向量是人工设定的匿名模拟嵌入，不来自真实图片，更不是已训练视觉模型。8款整款划分：V1–V6为历史训练款，V7–V8为新款留出。向量在2025-01-09可用；历史款结果在1月10可用；留出款真实销量到1月20才可得，不参加相似款权重或趋势估计。</p>
<table>
<thead>
<tr class="header">
<th>商品</th>
<th>分组</th>
<th>类别</th>
<th>向量(v1,v2)</th>
<th style="text-align: right;">可比曝光</th>
<th style="text-align: right;">销量</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>V1</td>
<td>train</td>
<td>shirts</td>
<td>(1,0)</td>
<td style="text-align: right;">1000</td>
<td style="text-align: right;">100</td>
</tr>
<tr class="even">
<td>V2</td>
<td>train</td>
<td>shirts</td>
<td>(0.8,0.2)</td>
<td style="text-align: right;">1000</td>
<td style="text-align: right;">120</td>
</tr>
<tr class="odd">
<td>V3</td>
<td>train</td>
<td>shirts</td>
<td>(0,1)</td>
<td style="text-align: right;">1000</td>
<td style="text-align: right;">80</td>
</tr>
<tr class="even">
<td>V4</td>
<td>train</td>
<td>shoes</td>
<td>(−1,0)</td>
<td style="text-align: right;">1000</td>
<td style="text-align: right;">70</td>
</tr>
<tr class="odd">
<td>V5</td>
<td>train</td>
<td>shoes</td>
<td>(−0.8,0.2)</td>
<td style="text-align: right;">1000</td>
<td style="text-align: right;">90</td>
</tr>
<tr class="even">
<td>V6</td>
<td>train</td>
<td>shoes</td>
<td>(0,−1)</td>
<td style="text-align: right;">1000</td>
<td style="text-align: right;">60</td>
</tr>
<tr class="odd">
<td>V7</td>
<td>holdout</td>
<td>shirts</td>
<td>(0.9,0.1)</td>
<td style="text-align: right;">1000</td>
<td style="text-align: right;">118，仅事后评价</td>
</tr>
<tr class="even">
<td>V8</td>
<td>holdout</td>
<td>shoes</td>
<td>(−0.9,0.1)</td>
<td style="text-align: right;">1000</td>
<td style="text-align: right;">87，仅事后评价</td>
</tr>
</tbody>
</table>
<p>余弦相似度与权重：</p>
<pre class="text"><code>cos(u,v) = (u1v1 + u2v2) / [sqrt(u1²+u2²)·sqrt(v1²+v2²)]
w_j = max(cos(u,v_j),0) / Σ_{k∈选中邻居} max(cos(u,v_k),0)
r = Σ_j w_j·(销量_j / 曝光_j)
新品预测 = 计划曝光 × r × 趋势系数</code></pre>
<p>先筛相同类别，取相似度为正的前2个历史款。cos是方向相似，不受向量整体倍数影响；欧氏距离则受尺度影响，所以不能把未经归一化的两种距离混着用。零向量模长为0，余弦未定义，程序明确拒绝。</p>
<p>对V7=(0.9,0.1)：模长sqrt(0.82)；V1模长1，点积0.9，所以cos(V7,V1)＝0.993883735。V2模长sqrt(0.68)，点积0.74，得到cos(V7,V2)＝0.990992430。两款归一化权重分别0.500728334和0.499271666。</p>
<p>基准转化率r＝0.500728334×0.1＋0.499271666×0.12＝0.109985433。两个已发生可比期间，曝光均6000，销量从500到550，因此趋势系数＝(550/6000)/(500/6000)＝1.1。两期都早于预测原点，不用留出款销售来倒算趋势。</p>
<p>V7预测＝1000×0.109985433×1.1＝120.983977件，事后实际118。V8同理得到87.983977件，事后实际87。这只是2款留出的教学误差，不足以证明视觉类比稳定有效。</p>
<p>若没有同类正相似邻居，代码回退到历史6款总销量/总曝光，再乘既定趋势；输出fallback=true。此回退把多个类别合并，只是透明保底，真实业务可选择人工复核而非自动首单。若向量、曝光分布、价格或上市渠道不具有可比性，应拒绝类比，不能只因cos高就认定需求相同。</p>
<p>另做一项真正执行的聚类实验：把6款历史向量先除以各自模长，再用sklearn
KMeans拟合K＝2个簇，n_init＝10、random_state＝20261106、algorithm＝lloyd。代码在fit与predict内部用threadpoolctl固定单线程，调用者无需设置环境变量。目标为Σ_j
||v̂<em>j−μ</em>{z_j}||²，v̂_j为归一化向量，z_j为簇编号，μ为簇中心。算法交替“把点分给最近中心”与“用簇内点的均值更新中心”，新款只分配到已经拟合的中心，不参与重训。</p>
<p>例如V2归一化为(0.970142500,0.242535625)。实际拟合中心为(0.656714167,−0.252488125)与(−0.656714167,0.414178542)，历史款V1–V6的簇编号依次[0,0,1,1,1,0]，留出V7/V8分到[0,1]；簇内平方距离和inertia＝2.706476666。聚类编号本身没有大小含义，换种初始化编号可能互换。由于这份教具左右对称，也存在不同分组却具有相同最优损失的解；并行求和的末位浮点差曾令固定种子仍在两解间切换。此处内部固定单线程以消除该环境下的复现不稳定，保留严格的训练中心一致测试，未将对称差异当作留出样本可以进入训练的理由。逐字节复现限定在本包固定依赖与受测运行环境，不承诺跨所有库版本和硬件。</p>
<p>聚类没有完美恢复商品类别：V3衬衫被分到主要鞋类所在簇，V6鞋被分到主要衬衫所在簇。这说明几何相似不等于业务可替代或需求可比。上述销量类比仍使用已知类别过滤和最近邻，没有悄悄切换为簇均值。K＝2是教学预设，没有完成簇数选择或稳定性研究。训练的是这些合成向量上的小型聚类，不是视觉编码器。</p>
<h3 id="学员验收">5. 学员验收</h3>
<p>能读出[2,4,3]不是“2天×4商品×3值”；手算V7两权重与120.983977。修改V8留出销量为9000时，预测应完全不变；改向量可得时间到未来则必须拒绝。零向量拒绝，无正权重触发回退，趋势分母0拒绝。P50≤P90只检验分位顺序，不等于概率校准。</p>
