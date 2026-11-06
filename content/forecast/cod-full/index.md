{
  "title": "COD：真实拟合、校准与两本账",
  "description": "COD：真实拟合、校准与两本账：问题：四个预测为0.8、0.2、0.6、0.4，实际为1、0、0、1。平均平方误差是多少？",
  "type": "forecast",
  "unit": "cod-full",
  "weight": 63,
  "outputs": [
    "HTML"
  ]
}

<p class="check">完全模拟的可复现实验，不连接生产。<a href="/forecast/forecast-specialty-projects.zip" download>下载四专项完整工程包（20,000/12,000/10,000/2,000实体）</a>。运行前阅读覆盖data/outputs的说明。固定模拟世界的指标不是企业收益。</p><p><a href="/forecast/specialty-start/">运行方法</a> · <a href="/forecast/specialty-time/">时间协议</a> · <a href="/forecast/specialty-data/">字段字典</a></p><h2 id="练习3概率与实物两本账">练习3：概率与实物两本账</h2>
<p><strong>问题</strong>：四个预测为0.8、0.2、0.6、0.4，实际为1、0、0、1。平均平方误差是多少？</p>
<ol type="1">
<li>分别算0.04、0.04、0.36、0.36，相加除以4=0.2。Brier越小越好，但必须与同一批样本上的基线比较。</li>
<li>打开
<code>cod/test_calibration.csv</code>。先看每组n，再比较平均预测和实际拒收率。空组不能说“0%拒收”。</li>
<li>打开
<code>validation_threshold_costs.csv</code>，找模拟成本最低行。核对
<code>model_selection.json</code>
的阈值完全相同。不要用测试拒收结果改这个阈值。</li>
<li>打开
<code>probability_ledger.csv</code>，比较原始概率、校准概率、实际结果。写清本次校准是否改善，而不是预设它必须改善。</li>
<li>另做实物手算：初始100件，发100件后库存0；20件拒收，退回质检18件合格、2件报损，现有可售18件。发货当天不能只扣“预计能签收的80件”。</li>
</ol>
<p><strong>交付</strong>：Brier手算、带组样本量的校准解释、验证阈值和工作量、实物库存核对。</p>
<p><strong>手算答案</strong>：Brier=0.2，前两条子集=0.04；实物最终18件，报损2件。</p>
<p><strong>验收</strong>：概率在0–1；未完结包裹不是拒收0；实际出库按全部件数扣减；不声称假设复核60%有效就是因果证据。</p>
<p><strong>可选扩展</strong>：在模型的成本函数里更改复核成本后，先写下新假设，再从头运行，把它作为另一个实验，不要挑测试效果最好的成本设定。若加入复核容量，需要重新设计决策问题，本包没有实现容量优化。</p>
<h2>模型实现及未实现范围</h2><h2 id="c.-cod拒收与概率校准">C. COD拒收与概率校准</h2>
<p><strong>实现</strong>：训练均值概率基线；批量梯度下降拟合带L2的逻辑回归（截距不正则化）；距离/件数/计划时长缩放；路线0/1编码；独立验证子块的截距校准；另一个验证子块的阈值成本选择；冻结后测试Brier/对数损失/10组校准；实际库存账与预期销售账分离。</p>
<p>逻辑回归设置：500次完整梯度迭代，学习率0.15，L2=0.01。实现没有外部库的优化器、收敛诊断与特征标准差缩放；它是教学基线，不声称达到全局数值最优。校准只加一个logit截距，不是同时估计斜率和截距的完整Platt缩放，也不是isotonic校准。</p>
<p><strong>关键假设</strong>：成本是假想的反事实收益计算。每包2元复核、每件拒收损失25元、复核减少60%拒收损失，均为教学设定。没有真实复核试验能证明60%。模型输出只是建议，不会取消任何包裹。</p>
<p><strong>未实现</strong>：完整Platt/isotonic、交叉拟合、置信区间、AUC/PR-AUC专项评估、极端类别不平衡处理、群体公平性审计、人工复核容量约束、因果干预评估、个人信用评分、自动取消、动态上线阈值。模拟测试期有风险漂移，验证集校准可能变坏。</p>
<p><strong>成本选择限制</strong>：所有验证候选看同一验证标签，存在有限样本选择误差；最终测试只报告一次。选到“全部复核”不等于模型创造了价值，应与全复核基线比较。单位成本或容量约束改变时，应重新定义实验，而不是按测试结果事后调成本。</p>
<h2>实际运行结果与解释</h2><h2 id="cod校准后也可能变差">3. COD：校准后也可能变差</h2>
<ul>
<li>测试2194包裹，实际拒收率18.64%。</li>
<li>Brier：训练均值基线0.153947；未校准逻辑回归0.149606；验证集截距校准后0.152524。本次校准后未改善，保留结果，不按测试答案反选模型。</li>
<li>验证集冻结复核阈值为0.00。本次选到0，即全部建议复核。工作量为测试样本的100%。</li>
<li>假想成本：按冻结阈值15568.00元，不复核27950.00元，全复核15568.00元。冻结策略与全复核相同，不能把差额宣称成模型增量价值。</li>
<li>成本假设：每包复核2元、每件拒收损失25元、复核可减少真实拒收损失的60%。未模拟复核容量或人工效果实验，数字不是已实现节省。</li>
</ul>
<p>查看：<code>cod/calibration.svg</code>、<code>cod/test_calibration.csv</code>、<code>cod/validation_threshold_costs.csv</code>，以及三张单独的库存/在途/预期销售图。</p>
<figure><img loading="lazy" src="/forecast/specialty-outputs/cod/calibration.svg" alt="COD：真实拟合、校准与两本账：calibration.svg，固定种子模拟输出"><figcaption>固定种子20261106的实际程序输出，仅反映教学模拟。calibration.svg</figcaption></figure><figure><img loading="lazy" src="/forecast/specialty-outputs/cod/threshold_cost.svg" alt="COD：真实拟合、校准与两本账：threshold_cost.svg，固定种子模拟输出"><figcaption>固定种子20261106的实际程序输出，仅反映教学模拟。threshold_cost.svg</figcaption></figure>
