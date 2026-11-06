{
  "title": "退货：概率、时滞与可售回流",
  "description": "退货：概率、时滞与可售回流：问题：第8天发100件，第7天发50件；退货率20%、退回良率80%；可售回流时滞2天占40%、3天占60%。第10天预计可售回流多少？",
  "type": "forecast",
  "unit": "returns-full",
  "weight": 62,
  "outputs": [
    "HTML"
  ]
}

<p class="check">完全模拟的可复现实验，不连接生产。<a href="/forecast/forecast-specialty-projects.zip" download>下载四专项完整工程包（20,000/12,000/10,000/2,000实体）</a>。运行前阅读覆盖data/outputs的说明。固定模拟世界的指标不是企业收益。</p><p><a href="/forecast/specialty-start/">运行方法</a> · <a href="/forecast/specialty-time/">时间协议</a> · <a href="/forecast/specialty-data/">字段字典</a></p><h2 id="练习2退回了不等于能卖">练习2：退回了不等于能卖</h2>
<p><strong>问题</strong>：第8天发100件，第7天发50件；退货率20%、退回良率80%；可售回流时滞2天占40%、3天占60%。第10天预计可售回流多少？</p>
<ol type="1">
<li>第8天批次贡献100×0.2×0.8×0.4=6.4件；第7天批次贡献50×0.2×0.8×0.6=4.8件；共11.2件。期望可有小数，实物库存没有0.2件。</li>
<li>从 <code>data/returns/events.csv</code>
挑一条有restocked的实体，写出发货、申请、到仓、质检、上架五个日期。计算发货到可售时滞，不只计算退回运输时间。</li>
<li>在 <code>test_cohort_predictions.csv</code>
核对p_eventual_restock=p_return×conditional_quality_yield。</li>
<li>在 <code>test_cohort_daily_restock.csv</code>
累加预期和实际回流。解释为什么某天误差变小，不代表每一天都变好。</li>
<li>在 <code>state_conditioned_next7_daily.csv</code>
看当前状态预测。为何已经restocked的订单未来不能再加一次？</li>
</ol>
<p><strong>交付</strong>：一条实物事件链、一个日回流复算、分清“预计供应”和“现有可售”的两列。</p>
<p><strong>手算答案</strong>：11.2件；若不可再售食品良率=0，预计可售回流也=0。</p>
<p><strong>验收</strong>：质检前不入可售；单件未来回流总概率≤1；训练窗口未成熟负例留空；食品情景全部0。</p>
<h2>模型实现及未实现范围</h2><h2 id="b.-退货回流">B. 退货回流</h2>
<p><strong>实现</strong>：退货二项概率的品类收缩；退货条件下质检良率；条件于最终可售的发货至可售时滞经验分布；批次卷积；测试批次日回流MAE/WAPE、总量对照；实时状态的历史路径条件匹配；不可再售食品情景0回流；质检后上架才加实物。</p>
<p>形式为
p(退货)×p(可售|退货)×p(时滞=d|最终可售)。最后一项的条件必须写全，不能把所有退回件的时滞与可售件的时滞混用。模型在品类内用完整训练路径，不读当前订单未来结果。</p>
<p>当前状态基线直接筛历史相似路径：没有申请时，未退货历史与“当时仍未申请”的退货历史都进入分母；已经申请但在途时，只保留当时尚未到仓的历史路径。每条路径最多贡献一个将来可售单位，所以7日预测之和不超过1。</p>
<p><strong>关键假设</strong>：本模拟所有退货最晚29日闭环，所以观察30日即可确定负例。下一周状态类比假设同品类历史的剩余路径可用于当前订单。没有证明现实同样成立。</p>
<p><strong>未实现</strong>：跨季节退货尾部、右删失退货生存模型、退货再换货、部分退货、一行多件、质检错误纠正、缺失事件、批次保质期、食品重新上架资格判定、库存销售占用或未来尚未发货批次的回流预测。最后一点表示当前7日回流只来自预测起点前已发出的件。</p>
<h2>实际运行结果与解释</h2><h2 id="退货单件概率与日回流分开看">2. 退货：单件概率与日回流分开看</h2>
<ul>
<li>测试2612个发货行。退货Brier：分组0.144113，总体0.153057。</li>
<li>测试批次日回流MAE：分组1.926件/日，总体1.921件/日，不回流基线5.243件/日。本次分组误差不低于总体。</li>
<li>测试批次预计最终回流387.76件，实际367件；日回流WAPE为36.73%。实际回流总量为0时，WAPE分母为0而无定义，仍可报告MAE。</li>
<li>第180日起下一周按当前状态预测：日MAE
2.163件/日；无历史支持实体数0。这是另一个预测起点和口径，不与上项混比。</li>
</ul>
<p>查看：<code>returns/daily_restock.svg</code>、<code>returns/test_cohort_daily_restock.csv</code>、<code>returns/state_conditioned_next7_daily.csv</code>。</p>
<figure><img loading="lazy" src="/forecast/specialty-outputs/returns/daily_restock.svg" alt="退货：概率、时滞与可售回流：daily_restock.svg，固定种子模拟输出"><figcaption>固定种子20261106的实际程序输出，仅反映教学模拟。daily_restock.svg</figcaption></figure>
