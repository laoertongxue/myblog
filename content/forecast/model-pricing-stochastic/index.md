{
  "title": "三期随机动态定价",
  "description": "三期随机动态定价：本章所有数据都为匿名合成教学数据。本地代码不连接生产系统，不改价、不下单、不投放。执行证据分层：三商品回归与 sklearn 梯度提升树确实拟合；随机动态规划确实求解；深度网络、视觉编码器和 Prophet 没有训练或运行。模拟数据上的漂亮",
  "type": "forecast",
  "unit": "model-pricing-stochastic",
  "weight": 66,
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
id="model-pricing-stochastic三期随机动态定价">model-pricing-stochastic：三期随机动态定价</h2>
<h3 id="不是先看到需求再选价格">1. 不是先看到需求再选价格</h3>
<p>生鲜还可卖3小时，现有5件。每期可选10或8元/件，只能降价不能再涨，最后每剩一件要付1元处理费，因此残值s＝−1元/件。第4期到期禁售，只处理剩余库存；没有跨期补货，也没有新鲜度不同的批次混卖。初始价格上限同时约束DP首期动作、固定价与预定价格序列；例如把initial_price_ceiling改为8且保持只降不升后，合法对照只剩8/8/8，不能继续拿10元路径充当可执行对照。</p>
<p>在每期开始时只知道库存和上一期价格，先选价，再看到本期高/低需求。两种需求情景各概率0.5，且在本例中各期独立：</p>
<table>
<thead>
<tr class="header">
<th>期t</th>
<th style="text-align: right;">价格p</th>
<th style="text-align: right;">低需求</th>
<th style="text-align: right;">高需求</th>
<th>低/高概率</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>1</td>
<td style="text-align: right;">10</td>
<td style="text-align: right;">1</td>
<td style="text-align: right;">3</td>
<td>0.5/0.5</td>
</tr>
<tr class="even">
<td>1</td>
<td style="text-align: right;">8</td>
<td style="text-align: right;">2</td>
<td style="text-align: right;">4</td>
<td>0.5/0.5</td>
</tr>
<tr class="odd">
<td>2</td>
<td style="text-align: right;">10</td>
<td style="text-align: right;">1</td>
<td style="text-align: right;">2</td>
<td>0.5/0.5</td>
</tr>
<tr class="even">
<td>2</td>
<td style="text-align: right;">8</td>
<td style="text-align: right;">2</td>
<td style="text-align: right;">4</td>
<td>0.5/0.5</td>
</tr>
<tr class="odd">
<td>3</td>
<td style="text-align: right;">10</td>
<td style="text-align: right;">0</td>
<td style="text-align: right;">1</td>
<td>0.5/0.5</td>
</tr>
<tr class="even">
<td>3</td>
<td style="text-align: right;">8</td>
<td style="text-align: right;">1</td>
<td style="text-align: right;">3</td>
<td>0.5/0.5</td>
</tr>
</tbody>
</table>
<p>低价需求响应更高是设定，非估计结论。库存只限制成交，不应直接把潜在需求改成库存。若一次需求大于库存，丢失需求不向后积压。</p>
<h3 id="每个符号都落在状态上">2. 每个符号都落在状态上</h3>
<pre class="text"><code>S_t = min(I_t, D_t(p_t))
I_{t+1} = I_t − S_t
V_4(I, p_prev) = sI = −I
V_t(I,p_prev) = max_{p∈{8,10}, p≤p_prev}
  Σ_{ω∈{低,高}} π_{t,p,ω}
  [p·min(I,D_{t,p,ω})
    + V_{t+1}(I−min(I,D_{t,p,ω}), p)]</code></pre>
<ul>
<li>t是当前期，I_t是该期开盘库存，单位件；p_t是先选的价格，单位元/件。</li>
<li>D_t(p)是该价格下尚未发生的需求；ω是低/高情景，π为对应概率。</li>
<li>S_t是真正成交件数，不能用D_t直接乘价而无视库存。</li>
<li>V_t是从该期起到期末的最大期望“销售收入＋残值”，单位元。初始货物已经在手，模型没有采购成本决策，因此这里不叫完整净利润。</li>
<li>p_prev记忆上一期价格，保证只降不升。若只把库存放进状态，会忘掉能否重新涨价的限制。</li>
<li>max在期望求和外面，表示未知本期ω时必须选一个价格。把max放入每个情景内部会偷看未来。</li>
</ul>
<h3 id="先算最后一期">3. 先算最后一期</h3>
<p>第3期剩2件、上期价10元：</p>
<ul>
<li>选10元：低情景售0剩2，值0−2＝−2；高情景售1剩1，值10−1＝9；期望0.5×(−2)＋0.5×9＝3.5。</li>
<li>选8元：低情景售1剩1，值8−1＝7；高情景售2剩0，值16；期望0.5×7＋0.5×16＝11.5。</li>
<li>因而V_3(2,10)＝11.5，选8元。不能写“平均需求2，卖2件赚16”，那会忽略低情景的库存尾数。</li>
</ul>
<p>同理，V_3(0,10)＝0，V_3(1,10)＝8，V_3(3,10)＝15。若上一期已降至8，合法动作只剩8，仍按同一递推求值。</p>
<h3 id="再算第二期的两个关键库存">4. 再算第二期的两个关键库存</h3>
<p>第二期有4件、上期10元：</p>
<pre class="text"><code>选10：0.5×[10×1 + V_3(3,10)]
     +0.5×[10×2 + V_3(2,10)]
     =0.5×25 +0.5×31.5 =28.25
选8 ：0.5×[8×2 + V_3(2,8)]
     +0.5×[8×4 + V_3(0,8)]
     =0.5×27.5 +0.5×32 =29.75</code></pre>
<p>因此剩4件时降到8元，V_2(4,10)＝29.75。</p>
<p>第二期有2件、上期10元：</p>
<pre class="text"><code>选10：0.5×[10 + V_3(1,10)] +0.5×[20 + V_3(0,10)]
     =0.5×18 +0.5×20 =19
选8 ：两个情景都售2件，值16</code></pre>
<p>因此剩2件时保持10元，V_2(2,10)＝19。这正是根据已观察到的库存调整价格，而不是事先写死一条折扣曲线。</p>
<h3 id="回到第一期">5. 回到第一期</h3>
<p>初始5件。若先选10元，低需求后剩4件，高需求后剩2件：</p>
<pre class="text"><code>0.5×[10 +29.75] +0.5×[30 +19] =44.375元</code></pre>
<p>若先选8元，以后不能回升，只能继续8元，期望40元。故首期选10元。</p>
<p>程序输出的同一场景协议对照：</p>
<table>
<thead>
<tr class="header">
<th>策略</th>
<th style="text-align: right;">期望收入＋残值</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>固定10元，10/10/10</td>
<td style="text-align: right;">37.625</td>
</tr>
<tr class="even">
<td>固定8元，8/8/8</td>
<td style="text-align: right;">40.000</td>
</tr>
<tr class="odd">
<td>事先写死10/8/8</td>
<td style="text-align: right;">42.875</td>
</tr>
<tr class="even">
<td>事先写死10/10/8</td>
<td style="text-align: right;">43.625</td>
</tr>
<tr class="odd">
<td>观察库存后滚动选价</td>
<td style="text-align: right;">44.375</td>
</tr>
</tbody>
</table>
<p>44.375只是在本题离散状态、两种价格、独立情景和给定约束下最优。相对最佳预定序列增加0.75元，来自第二期可根据第一期已经发生的销售分支选价；不是承诺上线就提高利润。</p>
<p>每条三期低/高路径概率为0.125，共8条，输出保存每期先选价格、再观察情景、成交和库存。独立测试将历史相同的路径合并检查，要求当前动作相同，防止预知未来。</p>
<h3 id="三价格时间与库存响应表">6. 三价格、时间与库存响应表</h3>
<p>price_response.csv另有42行：生鲜3小时×3价×2开盘库存＝18行，服装4周×3价×2开盘库存＝24行。</p>
<p>生鲜价为8/9/10。9元的每个情景需求由8与10的对应低/高需求线性插值；例如第一期为1.5/3.5件，均值2.5件。若库存2件，期望成交是[1.5＋2]/2＝1.75件，而min(2,2.5)＝2是错误的“先平均再截断”。DP本题仍只选择两端价格，不将这张扩展表冒充已求三价格最优。</p>
<p>服装价为60/80/100元，周期t＝1…4周，设定确定性需求D_t(p)＝(32−5t)×(100/p)^1.2；开盘库存20或80件，销量min(I,D)。例如第1周100元需求27件、库存20时成交20件；第4周100元需求12件。它展示季末基础需求下降与价格响应的联合变化，不是从四周数据估出季节曲线。服装到第5周在本表设为禁售，实际业务是否禁售、转仓或清算必须由合法政策决定。</p>
<p>两类业务都必须先确认可售期和最低价。把expiry_period改到3期会被当前三期验证器拒绝，不会悄悄继续销售；改变负残值会重新计算策略。单批次教具不覆盖多批次FEFO与食品安全判定。</p>
<h3 id="学员验收">7. 学员验收</h3>
<p>先手算V_3(2,10)，再算V_2的2件和4件两状态，最后得到44.375。检查八路径概率和为1、库存非负、成交≤库存且≤需求、价格只降不升。将一行概率0.5改成0.6必须失败；将需求改为−1、缺一情景、重复情景也必须失败。初始库存0时价值应为0。剩余处理费增大时，重新求解，不拿旧动作表硬套。</p>
