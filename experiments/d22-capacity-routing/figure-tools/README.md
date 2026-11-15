# D22 配图重绘

四张黑白图由原生可编辑 SVG 排版并经 Chromium 导出 PNG。封面 900×383；正文图宽 700，不裁切拉伸。

- `d22-00_cover`：车装得下，路线才成立。
- `d22-01_load`：纯配送的累计送出量与车上剩余量；统一服务后时点。它不是 OR-Tools 到站 CumulVar 的截图。
- `d22-02_counterexample`：3 点各 6 箱、2 车各 10 箱，不拆单、每车一趟且不重装时不可行。
- `d22-03_checks`：覆盖、闭合、逐车容量和公平比较。

以上数字均为教学模拟，不代表实际经营。

## 重绘

安装 Node.js 与 Playwright（本文渲染版本 1.64.0），准备完整 Noto Sans SC TTF 字体。字体文件不包含在包内，可从官方 Google Fonts / Noto 来源取得。以下占位路径须替换为读者本机文件，不需要作者目录。

```bash
npm install playwright@1.64.0
npx playwright install chromium
FONT_PATH=/path/to/NotoSansSC.ttf node figure-tools/render_figures.mjs
```

若安装的 Playwright 不在默认模块搜索路径，额外设置 `PLAYWRIGHT_MODULE=/path/to/node_modules/playwright`。可选 `CHROME_PATH` 指定已安装的 Chromium 系浏览器。

脚本写入 SVG、原尺寸 PNG、350 与 280 像素预览及 `render-quality-report.json`；报告检查字体加载、文字边界和文字框重叠，PNG 尺寸也须匹配。预览仍需人工检查可读性。在博客仓库中运行时会同步文章图片与封面源文件；独立下载包只在包目录内输出。

所有图保持黑白，仅文字抗锯齿含灰度。SVG 不嵌入字体，编辑时须安装兼容字体。PNG 已固化字形。
