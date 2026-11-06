{
  "title": "来源、范围与纠错说明",
  "description": "来源、范围与纠错说明：本教程根据用户上传《供应链预测与计划全景白皮书》重新组织，并结合先前《供应链需求预测实战教程》补充基础。它是可顺序学习的课程，不是博客文章专题；课程与博客预测专题分别组织，内容与完成范围以各自页面为准。原白皮书的未附证据收益数字、行业实际比",
  "type": "forecast",
  "unit": "legacy-18",
  "weight": 19,
  "outputs": [
    "HTML"
  ]
}

<h2 id="来源与教学范围">来源与教学范围</h2>
<p>本教程根据用户上传《供应链预测与计划全景白皮书》重新组织，并结合先前《供应链需求预测实战教程》补充基础。它是可顺序学习的课程，不是博客文章专题；课程与博客预测专题分别组织，内容与完成范围以各自页面为准。原白皮书的未附证据收益数字、行业实际比例与所谓实证评分不作事实沿用。</p>
<h2 id="阅读入口">阅读入口</h2>
<ul>
<li><a href="https://otexts.com/fpp3/">Forecasting: Principles and
Practice
第3版</a>：第5章基础与准确性、第7章回归、第8章指数平滑、第9章ARIMA、第10章动态回归、第11章层级预测、第13章实践边界。</li>
<li><a href="https://otexts.com/fpp3/tscv.html">FPP3
交叉验证</a>：阅读滚动预测起点部分。</li>
<li><a
href="https://scikit-learn.org/stable/modules/calibration.html">scikit-learn
概率校准</a>：阅读校准曲线与Brier评分的含义。</li>
<li><a
href="https://scikit-learn.org/stable/modules/ensemble.html#gradient-boosting">scikit-learn
梯度提升</a>：理解分段树及逐步修正，不必先推导优化算法。</li>
<li><a
href="https://lifelines.readthedocs.io/en/latest/Survival%20Analysis%20intro.html">lifelines
生存分析入门</a>：理解生存函数与删失；不把软件输出当作识别假设已通过。</li>
<li><a
href="https://ocw.mit.edu/courses/1-260j-logistics-systems-fall-2006/pages/lecture-notes/">MIT
OCW Logistics
Systems</a>：选择库存与需求相关讲义，先做本教程简化例题。</li>
<li><a
href="https://developers.google.com/optimization/introduction">OR-Tools
优化介绍</a>：阅读目标、变量、约束的区别。</li>
</ul>
<p>链接为官方或作者资料入口，未编造页码。英文资料可先辅助翻译，再用本教程数字逐步核对。本轮未逐个网页联网验证可用性。</p>
<h2 id="从原稿修正的关键边界">从原稿修正的关键边界</h2>
<ol type="1">
<li>取消概率和留存订单数使用不同符号。现存未取消订单使用条件留存比，不重复乘从下单起的全程留存。</li>
<li>物流发货是竞争事件，也可能与取消风险有关，不能自动据此识别完全不发货的反事实。</li>
<li>离散logit风险回归不是Cox比例风险模型；Croston与TSB的第二个平滑对象不同。</li>
<li>退货回流必须考虑预测日起点之前的历史发货批次；COD库存按实物流记录，不重复净额扣减。</li>
<li>动态定价的销售不能超过库存。需求响应只是预测关联，不自动是价格因果效应。</li>
<li>未核实的收益百分比不作为结论。效期规则需具体法规确认，不由模型擅自延长。</li>
</ol>
<h2 id="数据与验证协议">数据与验证协议</h2>
<p>所有练习数据为模拟。禾味是2店8食材的虚构案例；匿名服装企业不出现真实品牌。14天仅用于手算，预测扩展为180天，按112/28/40切分；5天评价窗口不得跨块。以往已经公开的测试段只作历史演示，不能称为新的盲测；新模型最终比较应另造并封存测试数据。此站的教学计划、验收答案不表示学习者已完成实验。</p>
<p>原型仅离线建议，不自动采购、派车、改价、联系客户或发布文章。进度只存在当前浏览器，勾选代表自报完成，不是服务端认证。</p>
