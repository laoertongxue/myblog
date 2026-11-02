# D9 发布前LF换行与手机表格补审

审查者：第二轮独立审查子代理 `d9_review2`，2026-11-02。该补审针对冻结文件跨平台字节问题和手机表格布局变化；不代替既有两轮对抗审查。没有修改实验代码、数据、正文、Git属性或主仓库索引，只新增本记录与独立证据脚本。

**结论：本次修复通过。输出统一LF，真实Git暂存和两套换行配置下的检出都保持冻结字节，12项测试及完整重建通过；新旧测试结果数值完全一致。手机表格横向滚动且整页无横向溢出，七值与误差未变。**

## 一 为什么需要修复

旧候选在Windows写出的JSON与CSV含CRLF，冻结回执记录了实际字节。如果Git暂存或Linux检出将其转换为LF，数字虽然相同，SHA-256仍会改变，导致 `finalize`误判候选被修改。这是可复现性缺陷，不能通过忽略哈希失败来处理。

作者的最小修复是：`run.dump()`明确用 `newline='\n'` 写JSON；`csv.DictWriter`明确用 `lineterminator='\n'` 写CSV；`.gitattributes`对 `examples/d9-seasonal-naive/**` 明确 `text eol=lf`；增加 `test_portable_lf_output`，检验JSON不含CR和CSV完整LF字节。种子、LCG递推、星期基础量、服装趋势与活动机制、周期、训练验证测试边界及评价规则没有改变。

## 二 实际Git暂存与检出检查

独立脚本 `docs/d9-review-lf-oracle.py`创建可写临时仓库，复制当前 `.gitattributes`与15个实验文件，执行真实 `git init`、`git config core.autocrlf true`、`git add`。再通过 `git show :<path>`取出每个暂存blob，与源文件逐字节比较：15个全部相同，所有实验文件均不含CR。

随后分别设 `core.autocrlf=true`和`false`，使用真实 `git checkout-index --all --force --prefix=<隔离目录>`导出两套检出文件。两套全部文件均与候选逐字节一致，`git ls-files --eol`没有i/crlf或w/crlf。

每套检出目录均实际执行12项单元测试、原回执下的 `finalize`，再移走隔离目录内旧freeze/test后执行 `prepare → freeze → finalize`。重建后包括代码、README、policy、CSV、手算/验证/测试JSON、freeze回执在内的15个文件，与候选逐字节相同。主仓索引没有受到这次Git测试影响。

最初尝试本地 `git clone --no-hardlinks`未成功，返回 `fatal: Could not read from remote repository`，没有完成clone，也没有使用远程仓库或连接生产服务。之后采取的验证路线是临时仓库真实stage+checkout-index。本补审不声称实际完成了clone，也不声称已经在Linux执行；Linux仍以精确提交的CI结果为准。

## 三 数值与原对抗检查保持一致

读取作者保留的 `E:/12Lab/d9-tools/before-lf/test.json`与当前测试JSON，解析后深度比较：两案例的40条逐日记录、36条五天累计记录及全部误差字段完全相等。旧、新freeze的policy也完全相等。旧新文件SHA不同的原因是输出字节规范发生改变，不是预测值变化。

| 测试案例 | 日MAE | 五天合计MAE |
| --- | ---: | ---: |
| 禾味（公斤） | 2.175 | 4.111111111111111 |
| 服装（件） | 2.925 | 5.916666666666667 |

另重新运行第二轮独立oracle：1392组数学公式与未来非法污染攻击通过；独立生成器逐行核对、完整验证/测试明细、六类冻结文件篡改拒绝及从头重建均通过。更新的 `d9-review-round2-evidence.json`现在对应LF候选，实际单元测试为12项。

## 四 手机表格实际浏览器检查

文章两张表改为显式横向滚动容器与 `white-space:nowrap`。独立脚本 `docs/d9-review-mobile-tables.cjs`为真实 `.hugo-check`构建启动临时静态服务，使用Chromium检查360、390和1280px视口，不写入生产文件。

| 视口宽度 | 页面scrollWidth | 表容器宽度 | 手算表scrollWidth | 测试表scrollWidth |
| ---: | ---: | ---: | ---: | ---: |
| 360 | 360 | 320 | 560 | 720 |
| 390 | 390 | 350 | 560 | 720 |
| 1280 | 1280 | 1024 | 1024 | 1024 |

手机两张表均可在自身容器横向滚动，页面没有横向溢出；桌面自然展开。浏览器读取每个单元格，七值仍为19、25、19、22、28、38、29，测试表仍为40天、36窗及上述四个舍入误差值。

首次沙盒内浏览器导航临时localhost返回 `ERR_NETWORK_ACCESS_DENIED`，页面未打开。申请在沙盒外运行同一只读本地检查后获准，实际检查成功，退出码0。本次没有自动审批拒绝，没有未决或结果不确定的操作。

## 证据与交付边界

- `d9-review-lf.json`：15文件SHA、真实Git命令、两套检出与重建结果、新旧数值比较。
- `d9-review-lf-oracle.py`：对应可重跑独立检查。
- `d9-review-mobile-tables.json`与`.cjs`：三个真实浏览器视口的完整表格和布局证据。
- `d9-review-round2-evidence.json`：重新运行后的原对抗检查证据。

可将本已关闭补审记录装入最终实践包，再重打包并在包外记录最终SHA。此次补审没有执行Git推送、GitHub CI、线上HTTP或Library操作；不把本地检查冒充发布成功。
