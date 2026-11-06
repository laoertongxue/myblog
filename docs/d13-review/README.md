# D13 v3 文字修正与打包差异交接

状态：主审线程已通知v2第二轮数学、下载包及图文审查通过。v3仅将“把第121天之后的标签改大”改为“从第121天起把标签改大”，同步文章包，等待这处文字及打包差异的独立复核。未提交、未推送，未迁入原仓库。

原仓库 /Users/laoer/Documents/12lab.cn，HEAD 8fc0bdf14d695ca074736d26357094acf63644fe，制作前后git status均为空。隔离副本为 /Users/laoer/Documents/Codex/2026-11-06/task/d13-candidate。复制排除.git、sealed、缓存与构建目录；未打开原测试标签或D9下载包。完整检查沿用D11审查通过的规则，只对D9既有测试结果做固定哈希完整性校验、复算前140天中的验证段。

## 集成范围

仅新增 content/blog/rolling-backtest-stockout-censoring/、experiments/d13-rolling-backtest/、scripts/package-d13.py、static/downloads/d13-rolling-backtest-{practice,article,images}.zip、docs/d13-review/。不应同步整个副本，不应修改原仓库其他变更。AGENTS.md、scripts/check.sh、D9回归脚本及CI逐字节不变，证据见unchanged-release-checks.json。

第一轮处理见round1-resolution.md。v1、v2冻结包保持原字节；v3单独命名。发布载荷相比v2仅正文和文章ZIP变化，40个其他载荷文件完全一致。文章ZIP内部仅index.md和MANIFEST.sha256变化，见v2-v3-payload-diff.json及v2-v3-article.patch。实践代码、开发CSV、九份结果、图表和两个其他读者ZIP不变，运行编号仍为D13-v2-development-replay。v3是文稿包版本，不是一次新实验。

## 实际检查

22项实践测试通过；Fraction独立算术展开核对2072条预测、28行指标。728条总量含392个一步和336个固定五日窗口；336组未来攻击每组3种，外加完整回放未来扰动、最后4个一步起点、已观测值应能更新的正对照。7个候选全展示，原测试不重评。

3个ZIP无重复成员、清单集合完整、每成员SHA256匹配。干净解压22项测试通过，从另一个工作目录运行入口，九份结果全部逐字节一致。见package-verification.json及verify_packages.py。最终打包后重新清洁构建；从实际文章href通过HTTP获取三个下载包，与源ZIP及构建ZIP逐字节一致，且图包含重绘README，见served-download-verification.json。

Hugo 0.166.0 extended，和CI版本一致。HUGO_CACHEDIR=/tmp/d13-hugo-cache BROWSER_CHECKS=require make check完整通过，含7项浏览器检查、20项D9测试、2条开发回归。首轮沙箱因127.0.0.1监听EPERM中止，未弱化检查，在允许本机监听环境重跑成功。见make-check.txt。

D13专项浏览器检查1440/390/320px通过：页面无横向溢出，2表可键盘聚焦、手机内部滚动，4图均完整加载。截图保存在output/playwright（不入版本库）；浏览器报告在browser-review.txt。作者查看1440页首、320表格，以及四图280px预览。现有全站悬浮目录按钮仍可能在窄屏某个滚动位置遮住局部正文，本篇不修改主题。

四图纯灰度，封面原生900×383；正文按内容独立尺寸。重绘使用Python3.14、Pillow13.0.0、fontTools4.68.0及Noto Sans SC，字体与输入哈希、边界和文字不重叠检查见render-quality-report.json。封面和所有配图由Python排版源码重绘，不通过旧图裁切或拉伸生成。

## 审查必须攻击的边界

1. 预测函数在检查数值前切历史前缀；离线完整性验证和事后评分不能变成拟合或插补。
2. 五日窗口同一起点一次发布，不准用后续一步修订拼接；输出起点、日期、步长、参数与单位逐条可核对。
3. 先选参数再在同段报分会有选择偏差。本篇明确反复查看的教学开发回放，冻结在全部回放之后，不回灌历史，也不称新盲测或独立泛化证据。
4. 缺货另造14天一月反例，未改主数据。闭店目标未定义，缺测销量空白，真零与缺货零分离；模拟真值不可称现实已恢复。服装是五倍单位演示，不是独立实证。
5. 28个一步目标、24个重叠五日窗口；窗口WAPE分母重复覆盖，不同单位不合并；误差符号为实际减预测。

已访问一手来源 https://otexts.com/fpp3/tscv.html ，跳转第5章并核验5.10滚动起点段落。正文按该稳定链接引用，不依赖未核验锚点。

## 私人材料

Space 已核验 shares=[]，继承来源完整且为空，仅所有者。v1审查页 https://chatgpt.com/space/page_6aed32583ebc8191bc5c9ee6133c64d9 作为历史冻结记录保留；v2审查页为 https://chatgpt.com/space/page_6aed372e52ec819195467d3d1f7cfff3 。v3另建文字与打包差异审查页。附件将包含完整候选ZIP、可读文本整包、正文、4图和冻结回执。Space自身渲染预览未目视检查，保存及附件回读另行核验；本机文章渲染已检查。
