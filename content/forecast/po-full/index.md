{
  "title": "PO：部分收货、KM和P90边界",
  "description": "PO：部分收货、KM和P90边界：问题：订购100件，第10天收40件、第15天收30件、第25天收30件。第20天观察，交期是不是15天？",
  "type": "forecast",
  "unit": "po-full",
  "weight": 64,
  "outputs": [
    "HTML"
  ]
}

<p class="check">完全模拟的可复现实验，不连接生产。<a href="/forecast/forecast-specialty-projects.zip" download>下载四专项完整工程包（20,000/12,000/10,000/2,000实体）</a>。运行前阅读覆盖data/outputs的说明。固定模拟世界的指标不是企业收益。</p><p><a href="/forecast/specialty-start/">运行方法</a> · <a href="/forecast/specialty-time/">时间协议</a> · <a href="/forecast/specialty-data/">字段字典</a></p><h2 id="练习4一张po分三次到货">练习4：一张PO分三次到货</h2>
<p><strong>问题</strong>：订购100件，第10天收40件、第15天收30件、第25天收30件。第20天观察，交期是不是15天？</p>
<ol type="1">
<li>第20天已收70、未收30，尚未收齐。完成时长未知，随访20天，右删失=1。第25天才有“收齐时长25天”的标签。</li>
<li>在 <code>po/training_labels_asof179.csv</code>
找一条censored=1。核对订购=已收+未收；complete_age必须为空。</li>
<li>打开
<code>po/test_po_predictions.csv</code>，查看P90留空的行。为何“空”比随便填最大历史天数更诚实？</li>
<li>打开
<code>po/coverage_bounds.csv</code>，把有预测条数/全部条数写出来。覆盖上下界不等于置信区间，也不能只报好看的子集。</li>
<li>对比固定交期、只看完成样本、KM。解释为什么只看已经收齐的PO容易漏掉慢单。</li>
</ol>
<p><strong>交付</strong>：一个部分收货账、至少一个未完成标签说明、一份含分母和上下界的P90报告。</p>
<p><strong>手算答案</strong>：第20天完成时长未知；第25天收齐时长25天，不是首收10天或第二收15天。</p>
<p><strong>验收</strong>：所有日期的订购=已收+未收；未收不为负；右删失不记为交期0；不可估计P90留空；不因模型结果自动改真实PO。</p>
<h2 id="统一提交清单">统一提交清单</h2>
<ol type="1">
<li>命令与Python版本。</li>
<li>固定种子、数据规模、训练/验证/测试日期和标签截止日。</li>
<li>与同样样本基线的对比，包含失败或退步的结果。</li>
<li>一项手算、一项守恒检查、一项未来信息检查。</li>
<li>未实现模型与不能推广的条件。</li>
</ol>
<p>先完成这五项，再考虑更复杂算法。复杂名称不能替代正确的时间和账本。</p>
<h2>模型实现及未实现范围</h2><h2 id="d.-po部分收货与收齐交期">D. PO部分收货与收齐交期</h2>
<p><strong>实现</strong>：10供应商、20物料；部分收货事件与未收齐数量；下单时预测完整收齐日龄；固定P50=21日/P90=35日规则基线；只看已完成PO的经验分位数（作为有偏对照）；总体/供应商Kaplan–Meier；按验证集30天内收齐Brier选择；P50/P90预测、不可估计尾部留空、覆盖率上下界、已完成样本pinball诊断。</p>
<p>同一天先完成事件再行政删失。分位数定义为KM累计收齐概率第一次达到目标的日龄。若曲线未达到90%，不返回最大观察天数冒充P90。</p>
<p><strong>关键假设</strong>：行政观察截止与未来收齐时间在分组条件下可比/独立。模拟创建日期独立于交期，且没有额外时间漂移；现实采购旺季、催单、供应商替换会破坏这种可比性。</p>
<p>覆盖率上下界：已经在预测日以内收齐的肯定覆盖；仍未收齐但已经观察到预测日的肯定不覆盖；观察不足预测日的暂不确定。它们不是置信区间。只对有可估计预测的样本计算，并同步披露分母，不能将其推广到空值PO。</p>
<p><strong>未实现</strong>：参数生存模型、分位数回归、AFT、随机森林、梯度提升、供应商层级贝叶斯模型、物料交互、多状态到货过程预测、缺量取消、延期变更、催单策略、需求与交期相关场景安全库存、端到端补货优化。这里完整实现的是数据、透明基线和评估，不把上述模型列成已交付。</p>
<h2 id="结论怎么写才诚实">结论怎么写才诚实</h2>
<p>可以写：“在固定模拟机制、指定时间分块及所列假设下，方法A的某指标为x，与同样样本上的基线y相比……”</p>
<p>不可以写：“因此真实企业必降库存20%”“P90一定覆盖90%”“训练完校准必定更准”“测试通过就能自动下单”“大量模拟数据证明不存在因果偏差”。</p>
<h2>实际运行结果与解释</h2><h2 id="po不确定的p90就留空">4. PO：不确定的P90就留空</h2>
<ul>
<li>测试335条PO，截止时49条未收齐；训练截止时60条未收齐。</li>
<li>验证集按30天内收齐Brier选择supplier
KM。P50覆盖率52.54%，目标50%。</li>
<li>P90可估计221/335条，不可估计114条，必须披露这个分母。可估计部分的实际覆盖率界为83.26%–93.21%；其中22条观察不足以判定。P90留空原因是训练KM曲线未达到90%收齐概率；没有可估计预测时不报告覆盖率，不用0或最大观察日填补。这个区间不是统计置信区间。</li>
<li>只用已完成训练PO的朴素P90，在全测试集覆盖79.10%，低于目标90%。若训练没有已完成PO，该分位数与覆盖率均不可估计。</li>
<li>没有统一“最好模型”结论：覆盖只对有可估计预测的样本描述；仅已完成样本的pinball有选择偏差风险。</li>
</ul>
<p>查看：<code>po/test_po_predictions.csv</code>、<code>po/coverage_bounds.csv</code>、<code>po/km_survival.svg</code>。</p>
<h2 id="验证记录">验证记录</h2>
<p>运行命令：<code>python run_all.py</code>。测试的实际通过/失败与运行时间以
<code>test_results.txt</code>、<code>run_log.txt</code> 为准。生成清单在
<code>../data/manifest.json</code>。脚本重跑时会重写本页；本页没有把任何未运行模型列成已完成。</p>
<figure><img loading="lazy" src="/forecast/specialty-outputs/po/km_survival.svg" alt="PO：部分收货、KM和P90边界：km_survival.svg，固定种子模拟输出"><figcaption>固定种子20261106的实际程序输出，仅反映教学模拟。km_survival.svg</figcaption></figure><figure><img loading="lazy" src="/forecast/specialty-outputs/po/po_coverage.svg" alt="PO：部分收货、KM和P90边界：po_coverage.svg，固定种子模拟输出"><figcaption>固定种子20261106的实际程序输出，仅反映教学模拟。po_coverage.svg</figcaption></figure>
