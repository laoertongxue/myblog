# D15 黑白技术图重绘

在任何工作目录运行：

```sh
python /path/to/figure-tools/render_figures.py --font-path /path/to/NotoSansSC.ttf
```

依赖 Pillow、fontTools。字体使用本机已有 Noto Sans SC 或 Noto Sans CJK SC；TTC 可传 `--font-index 2`。脚本校验家族和全部字形，不下载字体、不自动安装依赖。本次使用本机已有 Noto Sans SC 和已有 Pillow 13.0.0 环境。

SVG 和 PNG 使用同一份布局。SVG保留文字可编辑，查看或编辑时需有相同字体。900×383 封面为原生设计；正文分别为700×1240、700×1120、700×940。全部为黑白排版，抗锯齿仅含灰度。

输出：
- `figure-tools/d15-*.svg`：四张可编辑源。
- `images/d15-*.png`：四张原图。
- `images/preview-280/`、`images/preview-350/`：预览与审阅拼图。
- `figure-tools/render-quality-report.json`：字体哈希、环境、尺寸、图片哈希、全部文字框与自动检查结果。

脚本以自身目录定位，独立图包仅需保留 `figure-tools/`，不需要文章、实践CSV或完整仓库。识别到本仓库时，才会同步文章已存在的images目录，以及封面源到assets。打包时将figure-tools和images保留同级即可。

## 数值与时间约定

教学模拟，禾味：初始现货12，初始在途8于第2天日初到货，L=2，目标S=20，需求为[7,9,8,4,5,6,3]。日末订单等待两个完整日后于第3个日初到货，即t日末下单、t+3日初到货。

图2是第1天日末下单前：现货5，在途8，IP13，补7，下单后IP20。图3是第3天：可用4、需求8、履约4、失销4、日末现货0。数值为本例固定教学说明，不由绘图脚本拟合或推导策略优劣。

自动检查：全部文字字形、画布边界、文字两两重叠、RGB通道一致、输出尺寸。自动检查不代替真实视觉检查，检查结论见visual-review.md。独立目录重绘的文件一致性见portability-check.json。

第一轮独立审核修订：图2与图3副标题明确数量单位为公斤。
