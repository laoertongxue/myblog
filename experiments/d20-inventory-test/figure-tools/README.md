# D20 黑白配图与独立重绘

五幅原创 SVG，使用纯黑、白排版。仅封面为900×383；正文按自身比例保留。前四图只说明概念。第五图使用已经生成的D20测试台账副本，只绘日末现存；不运行策略，不读取封存路径。

## 重绘

使用 Node.js 22、Playwright 1.64.0 及其 Chromium。将 figure-tools 和 images 两目录放在同一父目录，进入 figure-tools。安装依赖：

```sh
npm install --no-save playwright@1.64.0
npx playwright install chromium
FONT_PATH=/你的字体目录/NotoSansSC.ttf node render_figures.mjs
```

FONT_PATH 必须指向完整 Noto Sans SC TTF；本包不分发字体。已有模块可通过 PLAYWRIGHT_MODULE 显式传入 Playwright 模块绝对路径；可选 CHROME_PATH 指定 Chromium。脚本不含作者机器固定目录。使用不同字体、浏览器版本或操作系统，可能产生像素差异；须重做视觉检查。

脚本将字体字节嵌入内存页面等待加载后截图，SVG源不嵌入字体，单独打开SVG须安装同一字体。输出原尺寸PNG、350及280像素预览，并检查文本边界与重叠。当所在目录结构属于博客仓库时，会同时复制PNG至文章bundle，并保存封面SVG至 assets/cover-sources；离开仓库时仅重绘本包。

## 内容

- 00_cover：库存与缺货取舍，900×383。
- 01_boundary：预测141—180、库存153—180，冻结后报告，历史接触与修订披露。
- 02_metrics：平均现存、单位满足率、失销、订单次数。
- 03_tradeoff：缺货与占用、尾单、成本及效期局限、两案单位不混合。

- 04_inventory-curves：两案例的实证日末现存曲线，黑实线为每日策略、灰虚线为每三天策略；两面板单位分开。

曲线所需 data/ledger.csv 为原台账逐字节副本，来源与SHA记录在 data/source.json，渲染脚本固定校验该哈希，不自动更新。独立重绘须一并保留data目录。curve-data-check.json列出112个点；curve-independent-check.json记录从SVG反算并核对每个点的独立检查。

render-quality-report.json 保存实际尺寸及逐文本边界检查；visual-review.md 保存目视记录。
