# 数学桥梁配图重绘

全部为原创教学模拟图；不含真实客户、订单或业务结果。五张图采用白底、黑线和中性灰；唯一封面原生设计为 900 × 383，正文图保持各自尺寸。

在仓库根目录运行（Node.js + package-lock.json 所固定的 Playwright；已安装 Chromium）：

```sh
npm ci
npx playwright install chromium
node experiments/p01-math-bridge/figure-tools/render.cjs
```

脚本写出可编辑 SVG、文章 PNG 与 `render-report.json`。SVG 使用系统简体中文字体栈 PingFang SC / Microsoft YaHei / sans-serif；不同系统的字体回退可能改变字形和图片哈希，重绘后应重新核验文字边界与视觉。脚本检查所有文本边界在画布内，以 Canvas 原尺寸导出 PNG，并把各像素 RGB 通道统一为灰阶。报告记录尺寸、PNG SHA-256 和文字坐标。此脚本未以数据文件驱动画图，数据修改时必须同步修改源图并人工复核。

作者在本次 macOS Chromium 渲染后逐张查看了五张图，无文字裁切与图框溢出。封面 900×383；正文分别为 900×650、900×850、900×820、900×815。读者可点击文章正文图查看原尺寸。
