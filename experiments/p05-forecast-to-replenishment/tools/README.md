# 可选的图文重建

数值实验仅需Python标准库，见 ../practice/README.md。此目录的工具用于重新绘制配图或生成独立HTML，不是运行练习所必需。

- make_figures.py：需要matplotlib和可显示中文的Noto Sans CJK字体，原制作环境字体路径为 /usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc。脚本读取practice/inputs，重建原文五对PNG/SVG；它是本篇原始算例的插图模板，不是任意修改数据后的自动报告，核心输入改变时会拒绝重建。
- render_article.mjs：需要Node.js、marked、playwright。只生成HTML可传 --no-qa；浏览器检查另需可运行的Chromium，默认路径 /usr/bin/chromium。缺少浏览器权限时不要把生成HTML当作视觉验收完成。

本目录脚本已调整为以本完整包根目录为输入输出位置。可在完整包根目录运行：

```sh
python3 tools/make_figures.py
node tools/render_article.mjs --no-qa
```

以上工具会重建包内图片与HTML，修改之前请复制完整包。原文章的复核不代表读者修改后的新版本也已经通过复核。
