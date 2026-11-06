{
  "title": "实际训练的全局梯度提升树",
  "description": "实际训练的全局梯度提升树：本章所有数据都为匿名合成教学数据。本地代码不连接生产系统，不改价、不下单、不投放。执行证据分层：三商品回归与 sklearn 梯度提升树确实拟合；随机动态规划确实求解；深度网络、视觉编码器和 Prophet 没有训练或运行。模拟数据上的漂亮",
  "type": "forecast",
  "unit": "model-tree-trained",
  "weight": 67,
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
id="model-tree-trained实际训练的全局梯度提升树">model-tree-trained：实际训练的全局梯度提升树</h2>
<h3 id="这次真正做了什么">1. 这次真正做了什么</h3>
<p>运行包使用scikit-learn的GradientBoostingRegressor训练全局回归模型，三个SKU共同参与。它是实际梯度提升树，不是四行手工分裂，也不是运行LightGBM/XGBoost/CatBoost的替代声称。没有这些库也能学懂相同的提升思想；各库性能、类别编码与工程实现不能混为一谈。</p>
<p>数据生成420天×3SKU。前14天用于历史暖启动，交付特征day14–419，共1,218行。目标是已定义营业日内的需求件数。每个营业日17:00结束，销量17:30已入账，18:00预测次日；促销、天气预报与已知交期均在当日12:00发布。这里的“天气”是昨日已经发布的预报快照，不是次日实测。</p>
<h3 id="每一列为什么合法">2. 每一列为什么合法</h3>
<table>
<thead>
<tr class="header">
<th>列</th>
<th>定义</th>
<th>预测时是否已知</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>sku_A/B/C</td>
<td>三个SKU的one-hot列，每行一列1其余0</td>
<td>静态已知</td>
</tr>
<tr class="even">
<td>lag1</td>
<td>上一个营业日已发生需求</td>
<td>昨日17:30可得</td>
</tr>
<tr class="odd">
<td>lag7</td>
<td>七个营业日前同一天需求</td>
<td>已发生</td>
</tr>
<tr class="even">
<td>rolling7</td>
<td>t−7到t−1的需求均值</td>
<td>排除当天目标t</td>
</tr>
<tr class="odd">
<td>sin7</td>
<td>sin(2πt/7)的周内位置</td>
<td>日历已知</td>
</tr>
<tr class="even">
<td>cos30</td>
<td>cos(2πt/30)的模拟周期位置</td>
<td>日历已知；不是声称自然月总是30天</td>
</tr>
<tr class="odd">
<td>promo</td>
<td>次日已公告促销0/1</td>
<td>昨日12:00</td>
</tr>
<tr class="even">
<td>weather_forecast</td>
<td>次日温度预报</td>
<td>昨日12:00的固定版本</td>
</tr>
<tr class="odd">
<td>supplier_lead_known</td>
<td>预测前已知的交期报价</td>
<td>昨日12:00</td>
</tr>
<tr class="even">
<td>target_demand</td>
<td>次日真正发生的需求</td>
<td>特征禁用，只作标签</td>
</tr>
</tbody>
</table>
<p>所有派生列都必须按SKU分别排序再shift，不能让B商品的历史接在A后面。程序检查主键、日期连续、day从2024-01-01起的目标日期映射、预测原点恰为目标前一日18:00，再把available_at解析为时间而非只比较字符串；同时检查lag1、lag7、rolling7与已交付前序目标是否一致；数据最前面少于7日的暖启动值来自合成生成器，完整重建验证另覆盖这段历史，不声称CSV自己包含全部暖启动原始销量。</p>
<p>lead字段在模拟生成机制中有一个−2件的已知条件效应，用来演示“已公布较长等待时间可能影响顾客下单”。这是人为条件关系，不是供应商交期必然导致自然需求下降的业务定律，更不能从本例提炼真实因果。</p>
<h3 id="时间切块与回测目标">3. 时间切块与回测目标</h3>
<ul>
<li>训练：day14–251，共714行；所有缩放器、线性系数、树只在这里拟合。</li>
<li>验证：day252–335，共252行；只用于树深度2或3的选择。</li>
<li>测试：day336–419，共252行；不改参数，不反复挑最好测试成绩，不把标签回灌训练。</li>
<li>模型训练后冻结；每天向前走一步，允许使用昨天已实际发生的销量更新lag，再预测明天。</li>
</ul>
<p>这是滚动一日预测，不是在day335一次预测接下来84天。测试期中的历史值可能来自前几天已经发生的测试目标，因其在该次预测原点已可得而合法；若改为固定原点多日预测，必须递推预测lag或改成多步模型，不能继续使用未来真实销量。</p>
<h3 id="从线性到树逐符号看更新">4. 从线性到树，逐符号看更新</h3>
<p>线性Ridge解的是：</p>
<pre class="text"><code>min_{b,w} Σ_train (y_n − b − Σ_j w_j z_nj)^2 + λΣ_j w_j²</code></pre>
<p>n为样本，j为特征，z为只按训练集均值与标准差缩放后的特征，b为截距，w_j为权重，λ＝1。截距通常不惩罚；本包使用sklearn的标准行为。标准化器从训练数据学习，不能先在全数据上fit。</p>
<p>平方损失梯度提升的教学更新为：</p>
<pre class="text"><code>F_0(x) = 训练标签均值
r_nm = y_n − F_{m−1}(x_n)
h_m = 用训练特征拟合残差r_m的一棵浅树
F_m(x) = F_{m−1}(x) + η·h_m(x)</code></pre>
<p>m是第几棵树，η是学习率；本例η＝0.05、共120棵。每轮专门修正前一轮剩下的误差，并不是把120棵树互不相关地训练再平均。max_depth限制单棵树层数，min_samples_leaf＝12防止叶子只记少数点。固定random_state＝20261106。</p>
<p>一个叶子手算：四个训练残差[−2,−1,3,4]，若只用一个常数叶子，平方误差最小的输出是均值1；这四点的SSE为9＋4＋4＋9＝26。若某合法特征阈值把前两点和后两点分开，叶子输出分别−1.5和3.5，两叶总SSE＝0.25＋0.25＋0.25＋0.25＝1。损失下降25。若某样本当前预测20、落入输出3.5的叶子，本轮更新为20＋0.05×3.5＝20.175。此手算解释原理，不冒充运行模型某棵树的真实节点。</p>
<h3 id="同一协议相同测试行">5. 同一协议、相同测试行</h3>
<p>模型的输入按顺序扩展：历史＋日历＋SKU；再加促销；再加天气预报；再加已知交期。每个版本单独训练；每版树都仅用验证WAPE从深度2/3中选一个。主表完整版本固定，不在测试集上从所有消融中倒选冠军。</p>
<p>实际测试结果如下，WAPE＝Σ|A−F|/ΣA，Bias＝Σ(F−A)/ΣA；这里WAPE和常用WMAPE是同一个定义。</p>
<table>
<thead>
<tr class="header">
<th>模型/特征</th>
<th style="text-align: right;">测试WAPE</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>同星期lag7基线</td>
<td style="text-align: right;">24.2517%</td>
</tr>
<tr class="even">
<td>Ridge历史＋日历</td>
<td style="text-align: right;">10.4244%</td>
</tr>
<tr class="odd">
<td>GBDT历史＋日历</td>
<td style="text-align: right;">9.0195%</td>
</tr>
<tr class="even">
<td>Ridge＋促销</td>
<td style="text-align: right;">7.3469%</td>
</tr>
<tr class="odd">
<td>GBDT＋促销</td>
<td style="text-align: right;">6.6643%</td>
</tr>
<tr class="even">
<td>Ridge＋促销＋天气</td>
<td style="text-align: right;">6.3339%</td>
</tr>
<tr class="odd">
<td>GBDT＋促销＋天气</td>
<td style="text-align: right;">5.4068%</td>
</tr>
<tr class="even">
<td>Ridge完整</td>
<td style="text-align: right;">6.0408%</td>
</tr>
<tr class="odd">
<td>GBDT完整</td>
<td style="text-align: right;">5.3833%</td>
</tr>
</tbody>
</table>
<p>完整GBDT深度3在验证集WAPE为4.8268%，深度2为5.7768%，因此选3。测试结果只在选择之后计算。完整GBDT测试Bias＝+0.2389%，小正值表示总体略高估；正负误差可能互相抵消，Bias接近0不代表逐行误差小。</p>
<p>分SKU不能只看总体：</p>
<table>
<thead>
<tr class="header">
<th>测试商品</th>
<th style="text-align: right;">lag7 WAPE</th>
<th style="text-align: right;">完整Ridge WAPE</th>
<th style="text-align: right;">完整GBDT WAPE</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>A</td>
<td style="text-align: right;">26.4924%</td>
<td style="text-align: right;">8.7228%</td>
<td style="text-align: right;">7.9671%</td>
</tr>
<tr class="even">
<td>B</td>
<td style="text-align: right;">23.7257%</td>
<td style="text-align: right;">5.6190%</td>
<td style="text-align: right;">5.7000%</td>
</tr>
<tr class="odd">
<td>C</td>
<td style="text-align: right;">23.4375%</td>
<td style="text-align: right;">4.9068%</td>
<td style="text-align: right;">3.7368%</td>
</tr>
</tbody>
</table>
<p>B商品树略差于线性，不能因为总体更好就声称所有商品都应该升级。只有3条合成序列，尚不能证明规模化泛化，时间相关误差也不能当成252个完全独立实验样本。</p>
<h3 id="同政策成本避免精度替代业务">6. 同政策成本，避免精度替代业务</h3>
<p>本教具每行是独立单日备货，没有跨日库存：备货Q＝ceil(max(F,0))；缺1件罚2元，多1件罚1元。成本为2max(A−Q,0)＋max(Q−A,0)。所有模型使用完全相同目标、成本和政策，不为某个模型特制规则。</p>
<p>测试252行合计：lag7为3,541元，完整Ridge为797元，完整GBDT为718元。B商品分别是1,152、240、259元，树仍略差。它只是同协议下的静态模拟成本，不含资金、MOQ、补货交期、跨日库存或实际利润。模型低WAPE不保证每个决策目标更好，正式库存政策必须单独验证。</p>
<h3 id="三种常见树库与本包边界">7. 三种常见树库，与本包边界</h3>
<ul>
<li>XGBoost、LightGBM、CatBoost都属于提升树家族，能学习非线性与特征交互。名称不保证优于线性基线。</li>
<li>XGBoost常用正则化目标与多种建树策略；现代版本支持类别特征，但输入类型、启用方式、序列化和版本必须匹配。</li>
<li>LightGBM常用直方图与叶优先生长，支持按规则编码的类别列；小数据要限制叶数/最小叶样本，不能把任意编号当连续大小。</li>
<li>CatBoost强调类别处理与有序统计以减少目标编码泄漏；不意味着可以把未来目标提前给它。</li>
<li>本包实际使用sklearn经典GBDT，SKU采用明确one-hot。没有运行前三个库，不报告它们速度、精度或重要性。</li>
</ul>
<h3 id="学员验收">8. 学员验收</h3>
<p>运行后应看到8份训练记录：4个Ridge和4个GBDT特征版本；每个GBDT版本实际拟合2个候选深度，共8次树拟合，加4次线性拟合。逐SKU、逐日预测保存252行，能重新算出主表和成本。将未来天气发布时间改到2099、rolling7偷偷加上当天目标、把测试行标成训练、复制主键，均须失败。</p>
<p>当外部特征缺失，不能默认以0代替。可回退到仅历史＋日历的独立已验证模型；若历史也不完整，标记不可预测并进入人工数据检查。本包不包含在线自动回退服务，只有独立历史模型供比较，不能声称已部署完整监控。</p>
