# D16 黑白中文技术图

在任意工作目录执行（路径替换为本机实际位置）：

```sh
python /path/to/figure-tools/render_figures.py --font-path /path/to/NotoSansSC.ttf
```

依赖 Python、Pillow、fontTools；本次验证版本为 Python 3.12、Pillow 13.0.0、fontTools 4.68.0。字体使用本机已有 Noto Sans SC（`NotoSansSC.ttf`），也支持 Noto Sans CJK SC；TTC 可通过 `--font-index` 指定。脚本校验字体家族与全部字符字形，不下载字体、不自动安装依赖。本次依赖安装于隔离虚拟环境，没有全局安装。字体哈希与精确运行版本见 render-quality-report.json。其他机器可在自己的隔离虚拟环境安装 `Pillow==13.0.0 fonttools==4.68.0`。

SVG、PNG 使用同一布局；SVG 保留可编辑文字，查看时需装相同字体。PNG 不依赖客户端字体。封面原生排版为900×383；正文依次为700×1120、700×1290、700×1440，所有正文文字至少32px，纯黑白，抗锯齿仅含灰度。

输出：
- `figure-tools/d16-*.svg`：四张 SVG 源。
- `images/d16-*.png`：四张原图。
- `images/preview-280/`、`images/preview-350/`：各图预览和拼图。
- `figure-tools/render-quality-report.json`：字体、环境、尺寸、全部文字框、图片哈希与自动检查。

独立图包只需保留 figure-tools 目录；脚本以自身路径定位，重绘无需仓库、文章、CSV或模拟运行器。重绘输出 images 为同级目录。识别出仓库时，才同步到文章已存在的 images 目录及 assets/cover-sources/d16-fixed-batch.svg。

## 内容约定

全部为教学模拟。每日只在日末复核一次，IP > r 订0；IP = r 或 IP < r 均只订一个固定批量Q，不循环追单，不是连续复核。图2单位公斤，IP3、r10、Q6，当天只下单6，订后IP9仍≤10，本次检查结束；新单增加在途，不增加现货。图3每日顺序为日初到货→当日需求→日末检查与下单，L2代表等待两个完整日，t日末下单、t+3日初到货。失销不转为欠交，所以这里IP为日末现货与有效在途之和。

自动检查：全部文字字形、画布bounds、文字两两重叠、RGB通道一致、输出尺寸。自动检查不替代实际视觉核验，见visual-review.md；独立目录重绘一致性见portability-check.json。
