{
  "title": "把预售与三来源一起优化",
  "description": "把预售与三来源一起优化：本章补上 A07 剩余的一步：在同一个成本目标中，同时决定预售风险要覆盖到什么程度，以及PO采购、STO调拨、WO生产分别做多少。三种来源、BOM材料、产能、库存、每天的到货时间和三种预售情景一起参与求解，不能先把两个单独最优答案拼起来。",
  "type": "forecast",
  "unit": "core-13",
  "weight": 107,
  "outputs": [
    "HTML"
  ]
}

<p class="check">有限联合教学模型：单SKU、三天、三个预售净留存情景，联合PO/STO/WO整数决策。<a href="/forecast/forecast-joint-presale-lab.zip" download>下载联合预售实验</a>。不连接生产，未实现通用多SKU、多工序、随机交期、多阶段APS/MRP/MEIO。</p><h2 id="预售留存与采购-调拨-生产的共同决策">预售留存与采购 调拨
生产的共同决策</h2>
<p>本章补上 A07
剩余的一步：在同一个成本目标中，同时决定预售风险要覆盖到什么程度，以及PO采购、STO调拨、WO生产分别做多少。三种来源、BOM材料、产能、库存、每天的到货时间和三种预售情景一起参与求解，不能先把两个单独最优答案拼起来。</p>
<p>面向已会四则运算、百分数和简单不等式的高中读者。完成本章后，你应能手算最优方案的一条情景、解释为何另一方案更贵，并用程序验证全部有限候选。</p>
<p><strong>全部数据为合成数据；没有真实订单、采购、调拨、生产、营销或外部执行。</strong>
“最优”只指本章明示的一个商品、三天、三种情景、固定到货日、整箱数量的有限模型，不是通用或生产就绪MRP/APS/MEIO求解器。真实销售、食品质量及企业收益均未由此验证。</p>
<h2 id="运行与文件">1 运行与文件</h2>
<p>解压
<code>forecast-joint-presale-lab.zip</code>，进入目录，使用Python
3.10以上版本：</p>
<div class="sourceCode" id="cb1"><pre
class="sourceCode bash"><code class="sourceCode bash"><span id="cb1-1"><a href="#cb1-1" aria-hidden="true" tabindex="-1"></a><span class="ex">python</span> joint_lab.py <span class="at">--self-test</span></span></code></pre></div>
<p>只用Python标准库，无需联网或账号。<code>joint_lab.py</code>是本章入口；<code>base_core.py</code>保留前章的输入规范化、as-of、WMA、BOM等函数，作为依赖，不需要另运行它。新入口直接读取当前
<code>data/</code> 文件，不重新生成输入。</p>
<ul>
<li><code>output/report.json</code>：输入合同、共同最优、硬服务、分开求解对照、九个扰动情景、输入哈希。</li>
<li><code>output/all_candidates.csv</code>：默认模型全部3520个有限可行候选及其成本，按成本排序。</li>
<li><code>output/scenario_calendar.csv</code>：最优方案在三个情景下的九条逐日库存记录。</li>
<li><code>data/joint_sources.csv</code>：三个来源的数量上限、每瓶成本、固定启用费、MOQ、到货日、单位、可得时间。</li>
<li><code>data/joint_config.json</code>：日收货容量、仓容、成本系数、预售交付日及模型范围。</li>
</ul>
<p>改输入前复制一份目录；用
<code>python joint_lab.py --output-dir changed_output</code>计算修改后的方案。基础答案测试是为了确认初始数据，修改数据后不必强求它仍通过。非法选项退出2，不能当作成功。</p>
<h2 id="沿用什么-明确改变什么">2 沿用什么 明确改变什么</h2>
<p>仍为SPU TEA下的柠檬茶SKU T-L，1瓶=1
ea，6瓶为一箱。08:00决策只使用2026-06-15 08:00 UTC以前可得的数据：</p>
<ul>
<li>POS去星期WMA基准130瓶/日，未来三天散客需求117、117、156瓶。</li>
<li>OMS独立渠道30瓶，06-17交付；它不在POS预测中。</li>
<li>WMS当前可售180瓶；另有60瓶确定在途，于06-16开门前到。</li>
<li>远仓84瓶，至少保留24瓶，最多调60瓶。</li>
<li>截至本计划交付的MES制造上限90瓶。</li>
<li>B1每瓶耗糖浆0.2kg、膜0.25m、空瓶1个；可用材料20kg、24m、100个。</li>
<li>新增预售100瓶，低、中、高三情景最后分别留存40、70、90瓶，概率0.2、0.5、0.3，全部06-17交付。</li>
</ul>
<p>本章把三天POS预测暂时当成确定数，只研究预售留存这一项不确定性。因此<strong>共同模型的额外安全库存设为0</strong>，不再把前章28.5788瓶POS误差缓冲重复叠加到同一成本优化中。真实POS也有误差，但本章没有同时为它建情景，不能据此取消实际业务的安全库存政策。若在本模型输入非零
<code>minimum_terminal_reserve</code>，程序明确拒绝，不能默默忽略。</p>
<p>为看清共同选择，本章主实验假设06-17收货能力为300瓶，而前章是210瓶。这是明示的新合成场景参数，不是对真实仓库的批准。我们也实际求解容量仍为210和240的对照，不能只挑宽松场景报告。</p>
<p>默认每日收货容量为0、60、300瓶，仓容为300瓶。现有库存不算当天新收货，但占仓容。所有当日到货都假设开门前可用，所有销售都在当天到货后发生。</p>
<h2 id="为什么要共同求">3 为什么要共同求</h2>
<p>先看新增预售：预期留存为</p>
<p><code>0.2×40 + 0.5×70 + 0.3×90 = 70瓶</code>。</p>
<p>若只考虑缺货每瓶8元、余货每瓶2元，单独为预售选择的对冲量是90瓶。可是备这90瓶也要采购、运输或制造，不能把来源成本当成0。</p>
<p>本章确定基础需求=117+117+156+30=420瓶。现有和确定在途=180+60=240瓶。因此不含新预售的确定性净缺为420−240=180瓶。</p>
<p>分开做法会先取180+90=270瓶，再找最便宜的来源组合。共同做法直接比较所有来源组合在三个留存情景下的全部成本。结果分别是270瓶、687元与252瓶、651元。差36元是在同一套合成输入、同一成本口径下的算法比较，不是实际节约承诺。</p>
<h2 id="所有符号和单位">4 所有符号和单位</h2>
<table>
<thead>
<tr class="header">
<th>符号</th>
<th>意思</th>
<th>单位</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>t</td>
<td>天的编号，0=06-15，1=06-16，2=06-17</td>
<td>无单位</td>
</tr>
<tr class="even">
<td>s</td>
<td>预售情景，低/中/高</td>
<td>无单位</td>
</tr>
<tr class="odd">
<td>π_s</td>
<td>情景发生概率，0.2/0.5/0.3</td>
<td>无单位</td>
</tr>
<tr class="even">
<td>N_s</td>
<td>情景最终预售留存，40/70/90</td>
<td>瓶</td>
</tr>
<tr class="odd">
<td>p、r、w</td>
<td>PO采购量、STO调拨量、WO生产量</td>
<td>瓶</td>
</tr>
<tr class="even">
<td>c</td>
<td>箱规，本例6</td>
<td>瓶/箱</td>
</tr>
<tr class="odd">
<td>Q</td>
<td>三个来源合计p+r+w</td>
<td>瓶</td>
</tr>
<tr class="even">
<td>D_t</td>
<td>当日散客预测117/117/156</td>
<td>瓶</td>
</tr>
<tr class="odd">
<td>F_t</td>
<td>独立已确认订单0/0/30</td>
<td>瓶</td>
</tr>
<tr class="even">
<td>B_t</td>
<td>现有订单到货0/60/0</td>
<td>瓶</td>
</tr>
<tr class="odd">
<td>A_t</td>
<td>现有到货加新计划当日到货</td>
<td>瓶</td>
</tr>
<tr class="even">
<td>I_(t,s)</td>
<td>该情景当天销售后的库存</td>
<td>瓶</td>
</tr>
<tr class="odd">
<td>O_(t,s)</td>
<td>该情景当天到货后、销售前库存</td>
<td>瓶</td>
</tr>
<tr class="even">
<td>U_(t,s)</td>
<td>该情景当天未满足需求，视为流失而非欠交</td>
<td>瓶</td>
</tr>
<tr class="odd">
<td>K_t</td>
<td>当日收货能力0/60/300</td>
<td>瓶/日</td>
</tr>
<tr class="even">
<td>V</td>
<td>仓库最大容纳量300</td>
<td>瓶</td>
</tr>
<tr class="odd">
<td>Cu、Co</td>
<td>每缺一瓶损失8、期末每余一瓶损失2</td>
<td>元/瓶</td>
</tr>
<tr class="even">
<td>C_source</td>
<td>新来源费用，不含初始/既有在途的沉没成本</td>
<td>元</td>
</tr>
<tr class="odd">
<td>J</td>
<td>一个共同方案的期望总成本</td>
<td>元</td>
</tr>
</tbody>
</table>
<p>π读作“派”，在这里只是概率的符号。期望就是把各情景结果乘概率再相加，不等于某一天必然发生的数量。</p>
<h2 id="先写硬约束">5 先写硬约束</h2>
<h3 id="箱规-moq和来源上限">5.1 箱规 MOQ和来源上限</h3>
<p>p、r、w都是非负的6的整数倍。p要么为0，要么至少12瓶；r、w有启用时至少6瓶。</p>
<ul>
<li><code>0 ≤ p ≤ 120</code>。</li>
<li><code>0 ≤ r ≤ 84−24 = 60</code>，不能把远仓保留量调走。</li>
<li><code>0 ≤ w ≤ 90</code>，同时受MES与来源参数上界限制。</li>
</ul>
<p>因此p有0、12、18……120共20种，r有0、6……60共11种，w有0、6……90共16种。总共20×11×16=3520个三元组合。程序实际逐个比较，不是按固定优先级分配后称其最优。</p>
<p>如果某来源的到货日超出这三天，它在本题可选数量只能为0。模型不购买观察窗口以外的未来在途库存，也不给它编造期末残值。修改这种范围需要新的模型，不是把迟到货算成按时到货。</p>
<h3 id="bom与材料">5.2 BOM与材料</h3>
<p><code>0.2w ≤ 20</code>，左边是kg/瓶×瓶=kg。</p>
<p><code>0.25w ≤ 24</code>，左边是m/瓶×瓶=m。</p>
<p><code>1w ≤ 100</code>，左边是个/瓶×瓶=个。</p>
<p>生产90瓶耗18kg、22.5m、90个，均可满足。这些材料在决策时点已可用；没有后续原料采购或替代料。MES上限是本有限任务的制造总量约束，不是逐工序排程。</p>
<h3 id="到货和容量">5.3 到货和容量</h3>
<p>默认三个新来源均在第2天开门前到：</p>
<p><code>A_0=0；A_1=60；A_2=p+r+w</code>。</p>
<p>必须满足
<code>A_t ≤ K_t</code>。例如容量240时，Q=252的方案直接不允许进入候选，不能通过事后多记12瓶仓容来修复。</p>
<p>每天到货后还要检查
<code>O_(t,s) ≤ V</code>。收货能力限制“当天能处理多少”，仓容限制“当时能放多少”，是不同的约束。</p>
<h2 id="在每个情景逐天守恒">6 在每个情景逐天守恒</h2>
<p>期初 <code>I_(-1,s)=180</code>，所有情景相同。每天依次算：</p>
<p><code>O_(t,s) = I_(t−1,s) + A_t</code>。</p>
<p><code>需求_(t,s) = D_t + F_t + N_s×1(t=2)</code>。</p>
<p><code>销售_(t,s) = min(O_(t,s), 需求_(t,s))</code>。</p>
<p><code>U_(t,s) = 需求_(t,s) − 销售_(t,s)</code>。</p>
<p><code>I_(t,s) = O_(t,s) − 销售_(t,s)</code>。</p>
<p>1(t=2)表示“若是第2天取1，否则取0”，所以预售只在其交付日出现。每一天都能反验：到货后库存=当日销售+日末库存。缺货视为当日流失，不会在下一天偷偷再交一次。</p>
<p>前两天还没到预售交付日，所有情景相同：第0天180−117=63；第1天63+60−117=6。若60瓶现有在途改为第2天才到，第1天就有117−63=54瓶缺口。再多订第2天到的货也不能倒流回第1天，因此硬服务模式必定不可行。</p>
<h2 id="把来源成本与情景损失写成同一目标">7
把来源成本与情景损失写成同一目标</h2>
<p>来源成本为：</p>
<p><code>C_source = 3p + 2r + 12×1(r&gt;0) + 1.5w + 20×1(w&gt;0)</code>。</p>
<p>3、2、1.5的单位是元/瓶；12、20是启用一次的固定费用，单位元。PO本例无额外固定费。已有180瓶和既有在途60瓶的成本对所有新方案相同，此处作为沉没成本不再加，不能在一种方案加、另一种不加。</p>
<p>情景s的损失为：</p>
<p><code>L_s = 8×Σ_t U_(t,s) + 2×I_(2,s)</code>。</p>
<p>Σ表示把三天相加。缺货损失按三天累计计算；余货损失只对最后一天仍剩的货计算一次。每天都对同一瓶再收2元，会变成另一种模型。</p>
<p>共同目标：</p>
<p><code>J(p,r,w) = C_source + Σ_s π_s×L_s</code>。</p>
<p>选择满足全部数量、物料、时间和容量约束的同一个(p,r,w)，使J最小。<strong>三个情景必须共用同一个决策。</strong>
08:00不知道最终留存在哪个情景，所以不能“低情景订222，中情景订252，高情景订270”再把它们的成本平均，冒充当天能做的方案。</p>
<p>软服务模式允许U&gt;0，但计入8元/瓶损失；硬服务模式额外要求每个有正概率情景、每一天U=0。两种模式不能混淆，软服务最优不代表保证无缺货。</p>
<h2 id="手算共同最优的全部情景">8 手算共同最优的全部情景</h2>
<p>实际枚举得唯一最优：p=102、r=60、w=90，Q=252瓶。</p>
<p>来源费用：</p>
<ul>
<li>PO：102×3=306元。</li>
<li>STO：60×2+12=132元。</li>
<li>WO：90×1.5+20=155元。</li>
<li>合计306+132+155=593元。</li>
</ul>
<p>第2天销售前库存=前一天剩6+当日新到252=258瓶。当天基础需求156+30=186瓶。</p>
<table>
<thead>
<tr class="header">
<th>预售情景</th>
<th style="text-align: right;">概率</th>
<th style="text-align: right;">当天总需求</th>
<th style="text-align: right;">当天缺货</th>
<th style="text-align: right;">期末余量</th>
<th style="text-align: right;">情景损失</th>
<th style="text-align: right;">加来源费后的总成本</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>低留存40</td>
<td style="text-align: right;">0.2</td>
<td style="text-align: right;">186+40=226</td>
<td style="text-align: right;">0</td>
<td style="text-align: right;">258−226=32</td>
<td style="text-align: right;">32×2=64</td>
<td style="text-align: right;">593+64=657</td>
</tr>
<tr class="even">
<td>中留存70</td>
<td style="text-align: right;">0.5</td>
<td style="text-align: right;">186+70=256</td>
<td style="text-align: right;">0</td>
<td style="text-align: right;">258−256=2</td>
<td style="text-align: right;">2×2=4</td>
<td style="text-align: right;">593+4=597</td>
</tr>
<tr class="odd">
<td>高留存90</td>
<td style="text-align: right;">0.3</td>
<td style="text-align: right;">186+90=276</td>
<td style="text-align: right;">276−258=18</td>
<td style="text-align: right;">0</td>
<td style="text-align: right;">18×8=144</td>
<td style="text-align: right;">593+144=737</td>
</tr>
</tbody>
</table>
<p>期望损失=0.2×64+0.5×4+0.3×144=12.8+2+43.2=58元。</p>
<p>期望总成本J=593+58=651元。也可直接算0.2×657+0.5×597+0.3×737=651，两个算法必须一致。</p>
<p>期望缺货=0.3×18=5.4瓶；期望期末余量=0.2×32+0.5×2=7.4瓶。这些小数是多次同类情景的平均量，不是实际交付“0.4瓶”。</p>
<p>确定性基础净缺180瓶，所以252−180=72瓶是这个方案额外覆盖预售的数量。预售均值仍然70瓶，不能把预测改成72；多出的2瓶与整箱约束有关。</p>
<h2 id="与分开求解及硬服务比较">9 与分开求解及硬服务比较</h2>
<p>单独只最小化预售缺货/余货损失得到90瓶对冲，加基础180，Q=270。配最便宜来源为p120、r60、w90：</p>
<p>来源费用=120×3+60×2+12+90×1.5+20=647元。</p>
<p>期末三个情景余量50、20、0，无缺货。期望损失=0.2×50×2+0.5×20×2=40元；期望总成本=647+40=687元。</p>
<p>相比共同方案，多买18瓶使来源费用多54元，只把期望损失从58降到40，少18元。因此净多花54−18=36元。它没有算错单独的对冲题，只是单独目标遗漏了边际来源成本。</p>
<p>硬服务模式要求每个情景都不缺货，必须Q≥180+90=270；所有来源合计最多270，所以只有p120/r60/w90这一个方案可行，成本687。为“保证这三个指定情景都满足”付出的成本差为36元；不能从三个情景推导现实服务率100%。</p>
<p>完全偷看未来的下界会给低/中/高情景分别选222/252/270，成本507/597/647，概率加权594元。651−594=57元是此模型对完美信息价值的上界诊断，不是允许用未来信息的策略，也不是现实中一定愿意支付的费用。</p>
<h2 id="完整枚举与最优证据">10 完整枚举与最优证据</h2>
<p><code>all_candidates.csv</code>记录每个可行(p,r,w)的来源成本、期望损失和总成本。默认3520个组合全部满足物料/容量条件，没有丢掉中间候选。最便宜的几个方案是：</p>
<table>
<thead>
<tr class="header">
<th style="text-align: right;">PO</th>
<th style="text-align: right;">STO</th>
<th style="text-align: right;">WO</th>
<th style="text-align: right;">合计</th>
<th style="text-align: right;">期望总成本</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td style="text-align: right;">102</td>
<td style="text-align: right;">60</td>
<td style="text-align: right;">90</td>
<td style="text-align: right;">252</td>
<td style="text-align: right;">651</td>
</tr>
<tr class="even">
<td style="text-align: right;">108</td>
<td style="text-align: right;">54</td>
<td style="text-align: right;">90</td>
<td style="text-align: right;">252</td>
<td style="text-align: right;">657</td>
</tr>
<tr class="odd">
<td style="text-align: right;">96</td>
<td style="text-align: right;">60</td>
<td style="text-align: right;">90</td>
<td style="text-align: right;">246</td>
<td style="text-align: right;">659</td>
</tr>
<tr class="even">
<td style="text-align: right;">108</td>
<td style="text-align: right;">60</td>
<td style="text-align: right;">84</td>
<td style="text-align: right;">252</td>
<td style="text-align: right;">660</td>
</tr>
<tr class="odd">
<td style="text-align: right;">114</td>
<td style="text-align: right;">48</td>
<td style="text-align: right;">90</td>
<td style="text-align: right;">252</td>
<td style="text-align: right;">663</td>
</tr>
</tbody>
</table>
<p>可见同样252瓶，也会因来源成本不同而贵；只对总量找最优、忽略来源，仍不完整。独立验收应重写计算并逐行比较3520个成本，而不只是检查第一页恰好出现651。</p>
<p>程序每次输出候选总数、可行数和按原因统计的拒绝数，满足“枚举数=可行数+拒绝数”。某候选可能同时违反多个约束，拒绝统计记录检查到的第一个原因，不是互相独立的所有根因总数。</p>
<h2 id="不可行与参数扰动">11 不可行与参数扰动</h2>
<p>程序实际求解以下变化，默认数据其余不变：</p>
<table>
<colgroup>
<col style="width: 17%" />
<col style="width: 17%" />
<col style="width: 23%" />
<col style="width: 23%" />
<col style="width: 17%" />
</colgroup>
<thead>
<tr class="header">
<th>情景</th>
<th>最优PO/STO/WO</th>
<th style="text-align: right;">总量</th>
<th style="text-align: right;">期望成本</th>
<th>解释</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td>主场景软服务</td>
<td>102/60/90</td>
<td style="text-align: right;">252</td>
<td style="text-align: right;">651</td>
<td>共同最优</td>
</tr>
<tr class="even">
<td>硬服务</td>
<td>120/60/90</td>
<td style="text-align: right;">270</td>
<td style="text-align: right;">687</td>
<td>三个情景都满足</td>
</tr>
<tr class="odd">
<td>收货能力210，软服务</td>
<td>60/60/90</td>
<td style="text-align: right;">210</td>
<td style="text-align: right;">787</td>
<td>容量少，缺货损失高</td>
</tr>
<tr class="even">
<td>收货能力240，软服务</td>
<td>90/60/90</td>
<td style="text-align: right;">240</td>
<td style="text-align: right;">677</td>
<td>接受一定缺货</td>
</tr>
<tr class="odd">
<td>收货能力240，硬服务</td>
<td>不可行</td>
<td style="text-align: right;">无</td>
<td style="text-align: right;">无</td>
<td>最高情景需要270，最多收240</td>
</tr>
<tr class="even">
<td>STO延迟到第3天，软服务</td>
<td>120/0/90</td>
<td style="text-align: right;">210</td>
<td style="text-align: right;">835</td>
<td>迟到调拨不得提前使用</td>
</tr>
<tr class="odd">
<td>STO延迟到第3天，硬服务</td>
<td>不可行</td>
<td style="text-align: right;">无</td>
<td style="text-align: right;">无</td>
<td>只剩PO+WO最多210</td>
</tr>
<tr class="even">
<td>可用膜24m降为10m</td>
<td>120/60/36</td>
<td style="text-align: right;">216</td>
<td style="text-align: right;">838</td>
<td>生产量受膜约束，整箱最多36</td>
</tr>
<tr class="odd">
<td>PO单价3升为5元/瓶</td>
<td>96/60/90</td>
<td style="text-align: right;">246</td>
<td style="text-align: right;">851</td>
<td>共同最优数量也会改变</td>
</tr>
<tr class="even">
<td>现有60瓶在途延迟到第2天，硬服务</td>
<td>不可行</td>
<td style="text-align: right;">无</td>
<td style="text-align: right;">无</td>
<td>第1天已缺54，后来货不能补过去</td>
</tr>
<tr class="odd">
<td>高留存概率变0.7，低/中为0.1/0.2</td>
<td>120/60/90</td>
<td style="text-align: right;">270</td>
<td style="text-align: right;">665</td>
<td>高需求风险更重，最优覆盖更多</td>
</tr>
</tbody>
</table>
<p>不可行时，<code>best</code>为null，状态为
<code>INFEASIBLE_IN_FINITE_GRID</code>，没有“成功下单”或负库存。软服务模式通常仍可找到支付缺货代价的方案，这与硬服务不可行不矛盾。</p>
<p>膜10m的算例：每瓶0.25m，理论最多10÷0.25=40瓶；数量必须为6的倍数，所以最多36。材料够40瓶并不允许开40瓶的工单。</p>
<p>PO变贵的算例：方案96/60/90的来源费用96×5+132+155=767元。三情景期末26、0、0，缺货0、4、24；期望损失0.2×52+0.5×32+0.3×192=84；总计851元。</p>
<h2 id="时点-单位与错误注入">12 时点 单位与错误注入</h2>
<ul>
<li>POS只用cutoff前可得的修订；未来纠正记录不能用于08:00。</li>
<li>MES和WMS按目标日期及cutoff选快照。盘点可售必须和WMS一致；错误SKU不能冒充T-L。</li>
<li>BOM按生产/交付目标日期选生效版本，糖浆必须是质量单位、膜必须是长度单位，且用量严格为正。</li>
<li>预售情景只能使用cutoff前可得版本，概率必须和为1，净留存不能大于毛订单数。</li>
<li>来源条件及共同配置也有known_at。还未知道的容量或成本不能先用。</li>
<li>来源表单位必须为ea，金额口径固定CNY。箱数需要先按主数据换成瓶，不能把一箱当一瓶。</li>
<li>所有资源、成本、概率和数量必须有限、非负。NaN不是“缺失按0处理”，会被拒绝。</li>
<li>现有在途日、预留交付日必须是0至2的整数。Python的−1代表数组末尾，但业务里−1不表示第2天，程序会在索引前拒绝。</li>
</ul>
<p>练习与答案：</p>
<ol type="1">
<li>把 <code>joint_config.json</code>
第2天收货容量从300改240。答案：正常软服务677元、240瓶；硬服务不可行。</li>
<li>把 <code>config.json</code>
的film_m改10。答案：WO≤36，最优120/60/36，总成本838。</li>
<li>把STO到货日改3。答案：STO取0；不能仍用旧的60瓶调拨结果。</li>
<li>把预售高情景概率改0.9而不改另两项。答案：概率和不是1，退出失败，不输出新成功结果。</li>
<li>把资源film_m写为NaN，或把po_cap改−1。答案：非法输入错误，不应包装成业务不可行。</li>
<li>把库存行SKU全部改OTHER。答案：T-L库存合同不完整，应报错，不能继续按180瓶求解。</li>
<li>把现有在途日偏移写−1。答案：非法偏移错误，不能偷偷当第2天。</li>
<li>为什么不为高情景单独发270、低情景单独发222？答案：决策时不知道将来情景，真实可做的三个来源数量必须相同。</li>
</ol>
<h2 id="定量验收与交付范围">13 定量验收与交付范围</h2>
<p>最低验收要求：</p>
<ul>
<li>实际枚举3520个默认候选，唯一最优102/60/90、651元；全表不存在更小成本。</li>
<li>逐情景期末32/2/0，缺货0/0/18；材料18kg、22.5m、90个。</li>
<li>三天逐行守恒；前两天结余63/6；到货容量、仓容及远仓保留均满足。</li>
<li>独立对冲后配来源270瓶、687元；同口径差36，不用不同安全库存政策制造比较优势。</li>
<li>硬服务容量240不可行；迟到STO、材料减少、采购变贵、概率改变能实际改变结果。</li>
<li>修改磁盘输入真实进入计算，输入哈希随相关变化改变；错误输入与业务不可行区分。</li>
<li>所有情景共用同一数量决策；禁止未来信息下界混进可执行答案。</li>
</ul>
<p>本章已经将预售留存情景与三来源成本、物料、产能、逐日库存及到货约束放入同一个有限求解问题，补上旧版“分开求解”的教学缺口。仍未实现多SKU、共享工序、随机交期、多次滚动决策、跨日原料采购、复杂网络MEIO、替代料、真实质量/产权财务、在线执行、实时审批和生产系统容错。它不能被介绍成通用生产求解器。</p>
