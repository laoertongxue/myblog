# D21 原创图稿与可复现导出

四张黑白原生 SVG 排版图，不依赖截图、模板或外部地图，不读取实验数据。正文图解释建模边界，数值结论以实验输出为准。

## 文件和尺寸

- `d21-00_cover.svg` → 900 × 383 PNG，封面《最短路与配送方案》。
- `d21-01_levels.svg` → 700 × 1430 PNG，最短路、TSP、VRP。
- `d21-02_matrix.svg` → 700 × 1510 PNG，路网、成本矩阵、分车排序与服务口径。
- `d21-03_validation.svg` → 700 × 1530 PNG，可行性与公平比较检查。

所有文字和线框均可在 `render_figures.mjs` 修改，SVG 是导出产物。图片输出到相邻 `images/`，并保留等比例 350 px、280 px 缩略预览。不是用截图裁切封面，也不将正文拉伸成封面比例。

## 独立运行

需要 Node.js、Playwright、Chromium 与 Noto Sans SC 字体。已验证 Playwright 1.64.0。

```sh
npm install playwright@1.64.0
npx playwright install chromium
FONT_PATH="/absolute/path/to/NotoSansSC.ttf" node figure-tools/render_figures.mjs
```

运行目录为包含 `figure-tools/` 的实验目录。字体从 [Google Fonts 的 Noto Sans SC](https://fonts.google.com/noto/specimen/Noto+Sans+SC) 获取，遵循其许可证。字体不随本包附带，避免把本机文件路径或系统字体复制进下载包。

若模块不在正常 Node 搜索路径，可额外设置 `PLAYWRIGHT_MODULE` 为已安装 Playwright 模块目录；若使用已有 Chromium，可设置 `CHROME_PATH`。这些变量必须由运行者填写，不需要原作者电脑。

仅在上两级目录包含 `hugo.toml` 时，脚本额外复制原图到文章 bundle，并保存封面源稿到 `assets/cover-sources/`。独立下载后不会触碰博客仓库。脚本不会调用地图、业务系统或派车接口。

## 验收与重现边界

导出时自动等待字体加载，检查所有文字边界、两两文字重叠、PNG 尺寸；报告为 `render-quality-report.json`。仍需目视检查原图和手机宽度缩略图，不能把边界检查当作视觉验收。

2026-11-14 已检查四张原图和 280 px 缩略图：无裁切、无文字碰撞，正文缩略文字可辨。封面缩略图主标题清晰，小号栏目标签不是正文阅读信息。图文采用黑白灰抗锯齿，不用颜色传达含义。

同一环境重复导出应一致；跨系统、字体版本、浏览器版本可能发生字体栅格化差异，因此不承诺跨环境 PNG 字节相同。SVG 内容、尺寸和文字检查才是可移植验收条件。
