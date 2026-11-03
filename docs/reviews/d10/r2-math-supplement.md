# D10 R2 数学/归档补充审查：移动端表格修复

**PASS（限定增量审查）。无新增 P1/P2。此前 R2 数学、代码、数据结论对本版仍有效。**

审查时间：2026-11-03 01:58 UTC。仅检验实际更新 integration ZIP 及其嵌套下载包、原 R2 冻结版本差异；未修改候选或部署。

## 新版身份（实际读取计算）

- integration ZIP：`23eaa335ec65779a5192c8516754a5d6171213dfcbf565d6204dba14a5686947`
- 文章：`35ec4b447988aae680d85fd5ea81ce777cbc746a1b3260871f4871ff1a22a978`
- 内嵌文章下载 ZIP：`ffdb1f4a043a7212f39138d94472c251c1d9a94beb7b667f214c97923c37520d`
- 内嵌实践 ZIP（不变）：`53f2692e0f934d7717ceb2d02b3433a53e1f7eeca04c661445f530adf9b4c949`
- 内嵌图片 ZIP（不变）：`6428e98c7f7d08bada7436a54803b2b72f1793e8e967a9fe049524f282a53856`
- 更新外部 candidate manifest：`c60a78d554e9e8b2300f6770a3c6a182bf9c65d6ad2f3f3d4ccb4f72d467376f`

## 独立检查结果

1. 从原 R2 Markdown 提取三个表格的全部单元格，从新版实际文章用 HTMLParser 提取 th/td 内容，按原顺序逐一比较：**42/42 字符串完全一致**。包括表头、单位、方法标签、手算和全部16项评分；并非仅采信作者 delta.json。
2. 新版文章 ZIP 中 `article.md` 与 integration 正式文章逐字节相同。
3. 实际嵌套实践与图片 ZIP 摘要和原 R2 完全相同；integration 内整个 experiments 目录（包括预测代码、数据、结果、制图脚本及元数据）和5张文章PNG逐字节未变。因此无需重复先前25项测试及独立数值计算。
4. 实际 integration manifest、三个嵌套下载ZIP内各 manifest，以及更新外部 CANDIDATE_MANIFEST 的所有条目摘要逐项验证通过。
5. 对比整个 integration：仅文章、integration manifest、文章下载ZIP改变，新增mobile-table-closure.md及mobile-table-delta.json。不存在未声明的实验代码、数据或图片变化。
6. 人工检查文章差异：三表转为HTML横向滚动/nowrap，列头使用scope，容器具region、tabindex和aria-label；移除末尾独立参考模块并保留正文对应来源链接。数值解释、边界、测试集已公开的限制与教学模拟声明未被实质改变。

## 结论边界

本补充确认内容与包完整性，不代替浏览器中键盘操作、320/390px实际滚动及无障碍体验测试；由对应主题/视觉门禁确认。未扩大原R2审查范围，不声称部署已发生。新的冻结文章和ZIP身份以上述摘要为准；本报告存于候选之外。
