{
  "title": "从一条直线到类别特征",
  "description": "从一条直线到类别特征：设x为“预测发出时已确认的次日套餐预订份数”，y为“次日鸡腿肉净耗用量kg”。先使用：",
  "type": "forecast",
  "unit": "legacy-4",
  "weight": 5,
  "outputs": [
    "HTML"
  ]
}

<h2 id="第5章-从一个特征开始理解线性回归">第5章
从一个特征开始理解线性回归</h2>
<h3 id="把一条直线看作一条计算规则">5.1 把一条直线看作一条计算规则</h3>
<p>设x为“预测发出时已确认的次日套餐预订份数”，y为“次日鸡腿肉净耗用量kg”。先使用：</p>
<p>ŷ=a+b×x。</p>
<p>a是截距，b是斜率。b的单位是kg/份：在这条拟合规则中，预订增加1份，预测耗用增加b
kg。它不是自动等同于配方BOM，更不是增加1份预订必然造成的因果效果。</p>
<p>下面4个观测是单独构造的回归手算数据，不是前面14天数据的另几列：</p>
<table>
<thead>
<tr class="header">
<th>观测</th>
<th style="text-align: right;">已确认预订x 份</th>
<th style="text-align: right;">实际净耗用y kg</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>A</td>
<td style="text-align: right;">100</td>
<td style="text-align: right;">20</td>
</tr>
<tr class="even">
<td>B</td>
<td style="text-align: right;">120</td>
<td style="text-align: right;">23</td>
</tr>
<tr class="odd">
<td>C</td>
<td style="text-align: right;">140</td>
<td style="text-align: right;">27</td>
</tr>
<tr class="even">
<td>D</td>
<td style="text-align: right;">160</td>
<td style="text-align: right;">30</td>
</tr>
</tbody>
</table>
<p>模型训练要做的事是：找到一组a、b，使这4个点与直线之间的偏差尽量小。普通最小二乘使用“偏差平方和最小”作为目标，参见<a
href="https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LinearRegression.html">scikit-learn
LinearRegression文档</a>。</p>
<h3 id="先算两个平均数">5.2 先算两个平均数</h3>
<p>x的平均数为(100+120+140+160)÷4=130份。</p>
<p>y的平均数为(20+23+27+30)÷4=25kg。</p>
<p>把每个观测减去平均值，再做下表：</p>
<table>
<thead>
<tr class="header">
<th style="text-align: right;">x</th>
<th style="text-align: right;">y</th>
<th style="text-align: right;">x−130</th>
<th style="text-align: right;">y−25</th>
<th style="text-align: right;">两项相乘</th>
<th style="text-align: right;">(x−130)²</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td style="text-align: right;">100</td>
<td style="text-align: right;">20</td>
<td style="text-align: right;">−30</td>
<td style="text-align: right;">−5</td>
<td style="text-align: right;">150</td>
<td style="text-align: right;">900</td>
</tr>
<tr class="even">
<td style="text-align: right;">120</td>
<td style="text-align: right;">23</td>
<td style="text-align: right;">−10</td>
<td style="text-align: right;">−2</td>
<td style="text-align: right;">20</td>
<td style="text-align: right;">100</td>
</tr>
<tr class="odd">
<td style="text-align: right;">140</td>
<td style="text-align: right;">27</td>
<td style="text-align: right;">10</td>
<td style="text-align: right;">2</td>
<td style="text-align: right;">20</td>
<td style="text-align: right;">100</td>
</tr>
<tr class="even">
<td style="text-align: right;">160</td>
<td style="text-align: right;">30</td>
<td style="text-align: right;">30</td>
<td style="text-align: right;">5</td>
<td style="text-align: right;">150</td>
<td style="text-align: right;">900</td>
</tr>
<tr class="odd">
<td style="text-align: right;">合计</td>
<td style="text-align: right;"></td>
<td style="text-align: right;"></td>
<td style="text-align: right;"></td>
<td style="text-align: right;">340</td>
<td style="text-align: right;">2000</td>
</tr>
</tbody>
</table>
<p>一元线性回归的斜率可以这样求：</p>
<p>b=Σ[(x−x均值)×(y−y均值)]÷Σ(x−x均值)²=340÷2000=0.17。</p>
<p>Σ遍历这4个观测。分子单位是份×kg，分母是份²，相除得到kg/份；截距a的单位为kg。这个闭式解适用于带截距的一元普通最小二乘，前提是x不全相同。若4个x都等于130，则分母为0，斜率不能由这些数据唯一确定，不应强行输出0。最小二乘的几何目标本身不要求先假设正态分布；若要进行置信区间或显著性推断，还需额外统计条件。</p>
<p>分子表示两者偏离各自平均值时是否倾向于同向变化；分母用于按x自身变化的尺度进行换算。此刻不需要记住推导，只需知道它把一组点的共同变化压缩成一个斜率。</p>
<p>然后算截距：a=y均值−b×x均值=25−0.17×130=2.9。</p>
<p>因此模型为：ŷ=2.9+0.17x。</p>
<h3 id="检查拟合结果">5.3 检查拟合结果</h3>
<table>
<thead>
<tr class="header">
<th style="text-align: right;">x</th>
<th style="text-align: right;">实际y</th>
<th style="text-align: right;">拟合ŷ</th>
<th style="text-align: right;">实际−拟合</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td style="text-align: right;">100</td>
<td style="text-align: right;">20</td>
<td style="text-align: right;">19.9</td>
<td style="text-align: right;">0.1</td>
</tr>
<tr class="even">
<td style="text-align: right;">120</td>
<td style="text-align: right;">23</td>
<td style="text-align: right;">23.3</td>
<td style="text-align: right;">−0.3</td>
</tr>
<tr class="odd">
<td style="text-align: right;">140</td>
<td style="text-align: right;">27</td>
<td style="text-align: right;">26.7</td>
<td style="text-align: right;">0.3</td>
</tr>
<tr class="even">
<td style="text-align: right;">160</td>
<td style="text-align: right;">30</td>
<td style="text-align: right;">30.1</td>
<td style="text-align: right;">−0.1</td>
</tr>
</tbody>
</table>
<p>平方误差和=0.1²+0.3²+0.3²+0.1²=0.2。训练MAE为0.2kg。</p>
<p>这里使用参与训练的4个点来检查拟合，误差叫训练残差。它不等同于提前预测未来的误差。这个样本故意接近直线，而且只有4个点，不能拿0.2kg当作上线后精度。</p>
<h3 id="真正生成一个预测">5.4 真正生成一个预测</h3>
<p>若截单时已确认次日预订150份：</p>
<p>ŷ=2.9+0.17×150=28.4kg。</p>
<p>这个150在预测时已经知道，因此可以使用。若150其实是第二天最终完成的订单总数，就不允许这样直接用。你需要先预测订单数，或者换成预测时可见的预订信息，并在回测时完整模拟同样过程。</p>
<p>这里150位于训练范围100至160之间，属于插值。若拿它预测800份预订，则是远距离外推。厨房产能、团餐结构、菜品配比和供应约束都可能变化，不能因为公式还能算出138.9kg，就认为这个数可靠。</p>
<p>截距2.9是直线的位置，不应机械解释为“没有预订也一定耗用2.9kg”。样本并没有观察到接近0份的情况，截距的业务意义需要额外证据。</p>
<h3 id="用电子表格复现">5.5 用电子表格复现</h3>
<p>假设A2:A5放x，B2:B5放y：</p>
<ul>
<li>斜率：<code>=SLOPE(B2:B5,A2:A5)，应得到0.17。</code></li>
<li>截距：<code>=INTERCEPT(B2:B5,A2:A5)，应得到2.9。</code></li>
<li>预测150份：<code>=FORECAST.LINEAR(150,B2:B5,A2:A5)，应得到28.4。</code></li>
</ul>
<p>图表中使用散点图，而不是把A、B、C、D当作等距类别的折线图。横轴是预订份数，纵轴是kg，坐标单位应写出来。</p>
<h3 id="不用r²替代预测验收">5.6 不用R²替代预测验收</h3>
<p>R²描述模型对这批数据波动的拟合程度。4个点几乎排成直线，训练R²自然很高，但这不说明未来预测可靠。增加特征通常能让训练拟合更好，却可能损害未来效果。</p>
<p>同样，“预订与耗用正相关”可以支持预测候选特征，但不能直接推出改变预订策略的收益。预测关系和因果干预需要不同证据。<a
href="https://otexts.com/fpp3/regression.html">Forecasting Principles
and Practice 第7章</a>专门讨论了R²的局限与相关、因果的区别。</p>
<p><strong>本章练习。</strong>
用刚才的模型预测130份预订的耗用量；再说明为什么不能承诺“每增加100份预订，采购一定增加17kg”。</p>
<p><strong>参考答案。</strong>
预测为25kg。17kg只是模型给出的条件关联增量，不等于已识别的因果效果；采购还受库存、交期、可替代食材与包装规格影响。</p>
<h2 id="第6章-从多个数值到不同类型的特征">第6章
从多个数值到不同类型的特征</h2>
<h3 id="多元回归只是把一条规则拆成多项">6.1
多元回归只是把一条规则拆成多项</h3>
<p>真实业务不只受预订影响。加入周末、促销、门店后，可以写成：</p>
<p>ŷ=b0+b1×预订份数+b2×周末标记+b3×促销标记+b4×门店B标记。</p>
<p>ŷ单位kg；b0为截距，单位kg；b1单位kg/份；三个标记均无单位，因此b2、b3、b4单位都为kg。下标0至4只是参数编号，不是时间或乘方。把各特征乘对应系数后，所有项都转成kg才能相加。</p>
<p>周末、促销与门店B标记都是0或1。为了只练习“模型怎样使用多个输入”，先人为设定一组系数：</p>
<p>ŷ=8+0.08×预订份数+2×周末标记+3×促销标记+4×门店B标记。</p>
<p><strong>这些系数是教学假设，不是对14天数据或180天数据训练得到的结果。</strong>
真正训练时，应由历史训练样本共同估计所有系数，再进行时间回测。</p>
<p>如果门店B明天是周末、有促销、已确认150份预订，则：</p>
<p>ŷ=8+0.08×150+2+3+4=29kg。</p>
<p>若所有其他条件不变，仅换成门店A，门店B标记由1变为0，预测降到25kg。这是模型内部的条件比较，不是证明把A店改名为B店就能增加4kg需求。</p>
<h3 id="为什么不能把门店随意编码成1-2-3">6.2 为什么不能把门店随意编码成1
2 3</h3>
<p>如果门店A=1、B=2、C=3，再直接乘一个系数，模型就会把B与A的差异视为和C与B相同，还暗含门店之间有顺序和距离。这一般不是门店类别的真实含义。</p>
<p>对于带截距的普通线性回归，常见做法是选一个参考类别，其余类别各建一个0/1列。例如三种渠道：</p>
<table>
<thead>
<tr class="header">
<th>渠道</th>
<th style="text-align: right;">外卖标记</th>
<th style="text-align: right;">团餐标记</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>堂食 参考组</td>
<td style="text-align: right;">0</td>
<td style="text-align: right;">0</td>
</tr>
<tr class="even">
<td>外卖</td>
<td style="text-align: right;">1</td>
<td style="text-align: right;">0</td>
</tr>
<tr class="odd">
<td>团餐</td>
<td style="text-align: right;">0</td>
<td style="text-align: right;">1</td>
</tr>
</tbody>
</table>
<p>若同时放截距、堂食、外卖、团餐三个标记，它们会满足“堂食+外卖+团餐=1”，产生完全线性依赖。软件可能给出某种数值解，但系数不能按唯一可识别的类别差异随意解释。参考组编码是一个清楚的处理办法。独热编码的工具行为见<a
href="https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.OneHotEncoder.html">scikit-learn
OneHotEncoder文档</a>。</p>
<p>类别数量很多时，独热列也会变多。新品、新店或新渠道还可能在预测时第一次出现。训练前就应确定未知类别的处理规则，不能到上线才发现系统拒绝预测。树模型或原生类别模型的编码要求也各不相同，不能把一套编码方式当作所有算法的通用规定。</p>
<h3 id="不同类别对促销反应不同需要交互项">6.3
“不同类别对促销反应不同”需要交互项</h3>
<p>刚才的规则让A店和B店的促销增量都等于3kg。如果希望表达“B店促销可能更强”，可以加入：</p>
<p>交互项=促销标记×门店B标记。</p>
<p>再假定它的教学系数为1.5，则：</p>
<p>ŷ=原公式+1.5×促销标记×门店B标记。</p>
<p>门店B有促销时，新预测为30.5kg；A店有促销时仍加3kg；B店无促销时交互项为0。</p>
<p>交互项回答的是“某个因素的预测关系是否因另一个因素而不同”。服装中可对应“折扣×品类”“气温×外套品类”“渠道×价格”。如果数据里所有促销都恰好发生在周末，你很难可靠分开周末与促销各自的关系，需要更多不同组合的数据。</p>
<h3 id="周几-价格-尺码不能采用同一种处理">6.4 周几 价格
尺码不能采用同一种处理</h3>
<table>
<colgroup>
<col style="width: 33%" />
<col style="width: 33%" />
<col style="width: 33%" />
</colgroup>
<thead>
<tr class="header">
<th>信息</th>
<th>一种入门处理</th>
<th>需要警惕的事</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>价格</td>
<td>数值特征</td>
<td>历史价格可能由清库存策略决定，系数不自动是价格弹性</td>
</tr>
<tr class="even">
<td>促销</td>
<td>0/1、类型类别、折扣深度</td>
<td>只用预测时已确认的活动版本</td>
</tr>
<tr class="odd">
<td>星期</td>
<td>类别标记</td>
<td>周日与周一相邻，但数字7与1相差6，不宜任意当直线关系</td>
</tr>
<tr class="even">
<td>门店或渠道</td>
<td>类别编码</td>
<td>编号本身没有大小和等距意义</td>
</tr>
<tr class="odd">
<td>尺码</td>
<td>结合品类定义的类别或有序信息</td>
<td>S到M与M到L未必代表同样的需求变化</td>
</tr>
<tr class="even">
<td>温度</td>
<td>数值，可进一步加非线性关系</td>
<td>未来实际温度不可用，应使用当时预报或情景</td>
</tr>
<tr class="odd">
<td>节假日</td>
<td>已知日历、节前节后距离</td>
<td>调休和移动节日不等于普通星期模式</td>
</tr>
<tr class="even">
<td>商品上市天数</td>
<td>数值或生命周期阶段</td>
<td>不能使用预测时尚未知的最终退市日期</td>
</tr>
</tbody>
</table>
<p>“线性”也不意味着只能画直线。如果把x²作为额外特征，ŷ=a+b1x+b2x²仍对系数保持线性，但对x呈曲线。模型变灵活后，也更容易在样本边界外给出不合理结果。</p>
<h3 id="多加一个特征之前先问四个问题">6.5
多加一个特征之前先问四个问题</h3>
<ol type="1">
<li>预测发出时能拿到它吗？</li>
<li>历史能重建当时版本吗？</li>
<li>样本是否覆盖它的不同取值和组合？</li>
<li>加入后是否改善相同时间回测，并值得增加数据依赖？</li>
</ol>
<p>例如天气特征带来0.1个百分点WAPE改善，却需要一个经常延迟的外部接口，它未必值得引入第一版。反过来，促销计划若显著降低关键大促的短缺风险，即使平均指标改善不大，也可能有业务价值，需要单独分组验证。</p>
<h3 id="正则化是给过于灵活的系数加约束">6.6
正则化是给过于灵活的系数加约束</h3>
<p>特征变多以后，模型可能用很大的正负系数互相抵消，把历史噪声拟合得很好。Ridge在拟合误差之外惩罚系数平方，Lasso惩罚系数绝对值，后者可能把部分系数压到0。</p>
<p>入门时先理解作用，不急着手推优化算法：模型需要在“解释历史”与“保持规则稳定”之间折中。惩罚强度是需要验证的设置。若特征量纲相差很大，通常要按训练集统计量进行缩放，使惩罚更可比；验证与测试只能沿用训练阶段学到的缩放规则。</p>
<p>正则化不能修复数据穿越，也不能从4个样本里制造充足证据。应先建立低特征数、可解释的基线，再比较它是否真的带来改进。</p>
<p><strong>本章练习。</strong>
匿名服装企业有品类、颜色、门店、上市天数、折扣率和明日实际销量。哪些可以用于预测明日销量？</p>
<p><strong>参考答案。</strong>
前五类信息在预测时可知且历史版本可重建时可以作为候选；“明日实际销量”本身是目标，不能作为输入。计划折扣可以使用，事后实际折扣若当时未确定则不能直接使用。</p>
<h2 id="本阶段项目与验收">本阶段项目与验收</h2>
<h3
id="阶段4从一条直线到多特征与类别3课">阶段4：从一条直线到多特征与类别（3课）</h3>
<p><strong>必修/扩展边界：</strong>必修只使用本节完整三行(x,y)=(20,10),(25,15),(30,20)，x单位℃、y单位kg，按手算公式得到斜率1、截距−10，预测27℃为17kg。类别练习另设门店B哑变量=1时加5kg，则B在27℃预测22kg，A为17kg。温度/促销/尺码的大样本特征尚未提供，正式回归训练为选修，不作必修验收。</p>
<p>课程：①斜率截距与最小平方；②数值、0/1类别、交互项；③相关不等于因果，拟合不等于外推能力。</p>
<p>选修扩展项目P04“温度、促销、门店一起解释需求”：手算x=[20,25,30]、y=[10,15,20]得到y=x−10；再用180天禾味数据建立温度、星期、计划促销、门店类别模型；服装加入价格、品类、尺码。未来温度使用原点可获得天气预报/情景，不用事后真实温度。</p>
<p>扩展交付：coefficients.csv、feature_availability.md、按门店残差图、回归解释卡。</p>
<p>扩展验收（完成必修不要求实现此部分）：手算斜率1、截距−10正确；保留截距时K类别仅K−1哑变量；未见类别有处理规则；常数x触发“无法估计斜率”而非除0；模型是否改善如实报告，不设必胜门槛。</p>
