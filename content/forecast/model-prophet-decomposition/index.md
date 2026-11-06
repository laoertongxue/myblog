{
  "title": "讲清分量，不伪造运行",
  "description": "讲清分量，不伪造运行：本章所有数据都为匿名合成教学数据。本地代码不连接生产系统，不改价、不下单、不投放。执行证据分层：三商品回归与 sklearn 梯度提升树确实拟合；随机动态规划确实求解；深度网络、视觉编码器和 Prophet 没有训练或运行。模拟数据上的漂亮",
  "type": "forecast",
  "unit": "model-prophet-decomposition",
  "weight": 69,
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
id="model-prophet-decomposition讲清分量不伪造运行">model-prophet-decomposition：讲清分量，不伪造运行</h2>
<h3 id="模型形式">1. 模型形式</h3>
<p>Prophet常用加性形式为：</p>
<pre class="text"><code>y(t) = g(t) + s(t) + h(t) + ε_t</code></pre>
<p>g(t)为慢变化趋势，s(t)为周期项，h(t)为节假日/事件，ε_t为未解释误差。四项单位均为预测目标单位。若选择乘性季节性，形式与单位解释不同，不能把加性公式原封不动套上。</p>
<p>分段线性趋势可写成：</p>
<pre class="text"><code>g(t) = [k + a(t)ᵀδ]·t + [m + a(t)ᵀγ]
γ_j = −s_jδ_j</code></pre>
<p>k为初始斜率，m为初始截距，s_j为第j个候选变点时刻；a_j(t)在t到达s_j后为1，否则0；δ_j改变斜率，γ_j补偿截距使曲线在变点连续。用稀疏/收缩先验约束过多变点是模型思想的一部分。本教具没有拟合变点，不拿手工折线冒充估计结果。容量约束的logistic趋势是另一种选项，需要有效cap等输入；也未运行。</p>
<p>周期项通常用傅里叶基：</p>
<pre class="text"><code>s(t) = Σ_{n=1}^N [a_n cos(2πnt/P) + b_n sin(2πnt/P)]</code></pre>
<p>P为周期长度，t与P必须同单位；N为谐波数，n为第n阶，a_n/b_n为待拟合系数。N大更灵活，也更容易过拟合。节日项可写h(t)＝Σ_l
κ_l·1{t属于事件l的窗口}，κ_l是该窗口的效果，预测时必须知道窗口，而不是根据销量峰值事后补“节日”。</p>
<h3 id="行算术示例">2. 14行算术示例</h3>
<p>prophet_components.csv给14天明确设定的分量：g(t)＝100＋2t，s(t)＝10sin(2πt/7)，第7天h(t)＝20，其他天0。因为这些系数是手工给定，所以输出是分解算术，不是Prophet预测。</p>
<ul>
<li>第1天：趋势102，周项约7.818315，节日0，总和109.818315。</li>
<li>第7天：趋势114，周项0，节日20，总和134。</li>
<li>第14天：趋势128，周项0，节日0，总和128。</li>
</ul>
<p>14天只能展示两个完整的7天周期，不能据此声称识别年度季节性；也不能仅凭这张表估计可靠的节日效果和预测区间。</p>
<h3 id="与etsarimacrostontsb放在同一比较台">3.
与ETS、ARIMA、Croston/TSB放在同一比较台</h3>
<table>
<colgroup>
<col style="width: 33%" />
<col style="width: 33%" />
<col style="width: 33%" />
</colgroup>
<thead>
<tr class="header">
<th>方法</th>
<th>主要建模对象</th>
<th>本课需避免的误解</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>ETS</td>
<td>随时间递推的水平、趋势、季节状态</td>
<td>不是只能处理完全不变的均值</td>
</tr>
<tr class="even">
<td>ARIMA/SARIMA</td>
<td>差分后序列与误差的滞后依赖</td>
<td>加入差分并不自动解决价格或政策因果变化</td>
</tr>
<tr class="odd">
<td>Prophet</td>
<td>趋势、周期基函数、已知事件等结构分解</td>
<td>不是“自动适用于所有季节”的黑箱；没有足够周期就无法可靠识别</td>
</tr>
<tr class="even">
<td>Croston/TSB</td>
<td>间歇非零需求的大小、间隔或发生概率</td>
<td>不能把每日平滑预测误当每一天都会成交</td>
</tr>
</tbody>
</table>
<p>统一回测接口应接受：已到达的训练表、forecast_origin、horizon、在原点已知的未来协变量，返回[sku,target_date,origin,model,prediction,optional_quantiles]。每个滚动原点只用该时点之前的数据重新fit或按预先固定规则更新；节日、预报、价格版本同样受available_at约束。对所有模型使用相同目标、原点、预测期、样本和指标，调参仅在训练/验证区段。</p>
<p>当前未安装Prophet，因此没有执行Prophet.fit、没有对它报告WAPE或区间覆盖、没有把上面的算术输出与已训练GBDT公平排名。真正加入对照需要安装兼容依赖、验证数据接口和模型收敛，并重新按同一回测协议运行；本课只闭合解释与算术层。</p>
<h3 id="学员验收">4. 学员验收</h3>
<p>能按三分量算出134，解释γ_j为什么保证变点连续，指出周季节、年季节所需数据跨度不同，并区分手工分量、模型拟合、样本外评估与业务效果四层证据。看到库不可用就记录“未运行”，不能把固定公式输出改名为Prophet结果。</p>
<h2 id="统一验收与适用边界">统一验收与适用边界</h2>
<p>运行包测试涵盖公式重算、真实输入读取、时间切块、可得时间、lag/rolling一致、正价/非负计数、场景概率、非预知决策、库存与降价守恒、深度输入形状、未来特征拒绝、零向量、零权重、留出标签隔离和指标重算。verify_reproducibility.py在临时副本内重建，核对10个输入与2个确定性输出逐字节相同，并验证原始文件未被改变。</p>
<p>这些测试验证这个教学实现与输入合同，不证明模型面对真实业务已足够稳健。本包没有真实门店实验，没有部署、权限服务、自动审批、持续监控，也没有运行TFT、DeepAR、视觉编码器或Prophet。尚待更广验证的范围必须继续保留，不因页面出现某个模型名称就自动标成“全部完成”。</p>
