# D19 黑白配图重绘

四图从原生 SVG 坐标排版重绘，不裁切或拉伸旧图。SVG 为可编辑文字与线框；PNG 直接由 Chromium 渲染 SVG，非另画一套近似图。图中没有读取或展示任何测试数据，脚本也不读取实验数据。

## 重绘

依赖已安装的 Node.js、Playwright 与 Chromium、Noto Sans SC 中文字体。无需 Python 图形依赖。由任意目录运行：

```sh
PLAYWRIGHT_MODULE=/绝对路径/node_modules/playwright \
FONT_PATH=/绝对路径/NotoSansSC.ttf \
node /绝对路径/figure-tools/render_figures.mjs
```

若 Playwright 安装在项目可解析路径中，不需 PLAYWRIGHT_MODULE；显式指定时优先使用该模块。FONT_PATH 必须提供，不查找本机私有路径，也不静默替换为系统字体。缺少变量或文件不可读会输出说明并退出。若使用本机 Chrome，可额外设置 CHROME_PATH 为浏览器可执行文件路径。不自动下载或安装依赖。

脚本输出到 figure-tools 同级 images，并生成本目录四份 SVG 与 render-quality-report.json。在包含 hugo.toml 的本站仓库结构内，额外同步文章 images 和 assets/cover-sources/d19-inventory-validation.svg；独立拷贝本目录时只生成本地图片。

## 图稿

- d19-00_cover.png：900×383，唯一列表封面。
- d19-01_timing.png：700×1510，日内事件顺序、L+1 到货、IP 与期末在途。
- d19-02_fair-comparison.png：700×1380，共同输入与不同复核节奏，不声明收益。
- d19-03_freeze.png：700×1530，训练、验证冻结、D20 预测与库存测试范围。

images/preview-280 与 preview-350 为真实手机宽度 PNG 预览。contact-sheet.png 为本次人工检查用拼图，不由重绘脚本生成，不作为正文配图。

FONT_PATH 应指向完整简体中文 Noto Sans SC 的 .ttf 文件。字体每次运行从该路径读取，以数据 URL 内嵌到新建临时浏览器页面，并等待加载成功后再导出；不依赖旧浏览器页面或系统字体缓存，未把字体复制进仓库。独立打开 SVG 时不会嵌入该字体，应安装同一字体文件，否则查看器可能回退到其他字体，字宽和折行观感不能保证一致。需要像素一致时请以脚本生成的 PNG 为准，并保持字体字节、Playwright/Chromium版本与操作系统一致。脚本会重新创建 SVG，故永久排版变更应修改脚本中的绘制坐标。

## 检查范围

脚本断言实际 PNG 像素、每段文字位于画布内、文字之间无矩形交叠；报告保留浏览器测得的文本框。它不自动保证语义正确或所有线框碰撞。另见 visual-review.md 的人工检查记录。
