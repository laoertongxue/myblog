# D17 图稿复现

全部图稿为教学模拟，无真实品牌或经营数据。沿用 D16 的 Pillow/SVG 双输出布局机制，重新设计 D17 日历门槛、目标缺口与事件时间线。

## 运行

依赖 Python 3、Pillow、fontTools，以及含简体中文字形的 Noto Sans CJK SC 字体。当前验证版本见 `portability-check.json`。

```sh
python experiments/d17-periodic-review/figure-tools/render_figures.py \
  --font-path /usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc \
  --font-index 2
```

字体路径显式传入，不硬编码个人目录。TTC 的索引因字体包而异；独立 SC 字体通常为 0。脚本确认字体族与全文字符覆盖，不允许缺字默默输出。字体不随仓库分发。

可把本脚本单独复制到任意目录的 `figure-tools/` 下，在任意工作目录运行。结果写到脚本上一级 `images/`；只有识别到站点仓库时才同步文章 bundle 与封面源。已复制到仓库外运行并验证四张 PNG 的 SHA-256 完全一致。

## 产物

- `d17-00_cover.svg`：原生 900×383；同步到 `assets/cover-sources/d17-periodic-review.svg`。
- `d17-01_calendar.svg`：700×1090，复核日门槛。
- `d17-02_order-up-to.svg`：700×1430，目标缺口、在途与欠交示例。
- `d17-03_timing.svg`：700×1510，事件先后与保护期。
- 原始 PNG 位于同级 `../images/`，同步至 `content/blog/periodic-review-order-up-to/images/`。
- `../images/preview-280/` 与 `../images/preview-350/`：缩图和 contact-sheet。

SVG 保留可编辑文字，编辑或浏览时需安装所选字体。PNG 从同一布局坐标用 Pillow 2 倍超采样后降采样，不依赖系统 SVG 渲染器。

## 检查

每次绘制自动断言：所有字形存在、文字边界在画布内、任意文本框不重叠、RGB 三通道完全一致。正文最小字体 32px / 700px；封面标题 58px。机器记录见 `render-quality-report.json`。边框与文字的视觉关系由人工像素检查补充，不把文本框检查冒称全部图形碰撞检测。

时间口径：日初到货→当日需求→日末判断是否复核。L=2 为两个完整等待日，t 日末订单 t+3 日初到货。第4日只有 q>0 才实际下单，因此第7日到货是条件事件。第2日复核后至第4日订单可售前包含第3–6日需求，R+L=4 是此口径下的保护期起点，不是服务水平承诺，也不是单独计算 S 的充分条件。
