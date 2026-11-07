# D14 黑白配图重绘

从仓库根目录运行（输入输出定位基于脚本，可从其他工作目录通过脚本绝对路径执行）：

```bash
python -m pip install Pillow fontTools
python experiments/d14-model-selection/figure-tools/render_figures.py \
  --font-path /usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc \
  --font-index 2
```

字体必须为 Noto Sans SC / Noto Sans CJK SC，字体不随包分发。`--font-path` 支持本机绝对或相对路径，独立 TTF/OTF 使用默认索引0；上述已安装 TTC 的简体中文索引为2。脚本校验字体家族及每个文字的字形，不自动联网安装。Pillow/fontTools 可由 PyPI 安装。

封面在900×383画布原生设计，生成可编辑源 `figure-tools/d14-00_cover.svg`，仓库中额外同步为 `assets/cover-sources/d14-model-selection.svg`，无旧图裁切、补边、拉伸。SVG与PNG由同一文字/线框布局产生；SVG保留文字，编辑或导出时须安装上述字体。其余两图为700×1090、700×1530；可编辑SVG在本目录。

输出到 `experiments/d14-model-selection/images/`，仅在识别到本仓库且文章目标目录存在时，将三张原图同步至文章的 `images/`。280px、350px预览和横向审阅拼图保留在实验images下，不复制到文章bundle。主图数字直接读取本D14实验的 `practice/results/metrics.csv`（D13同协议回放结果）；按匿名服装、任务跨度与指标寻找既有候选中的最小者，并断言方法身份，不拟合新模型。

三个指标分面独立，不建立共同数值轴，不跨任务或指标比较大小。只展示模拟数据；SARIMA、Croston类、树模型均明确为未实现、未评分的候选路线。

`render-quality-report.json` 记录环境版本、字体/输入SHA-256、图片尺寸与SHA-256、文字框、灰度检查。每次重绘自动检查缺字、画布越界、文字两两重叠和RGB通道一致性。自动检查不能替代视觉检查：重绘后必须真实查看三张原尺寸图、350px和280px预览，确认线框、文字、脚注无碰撞且可读。本次人工复核结论见 `visual-review.md`。

## 独立压缩包

解压后保持 `figure-tools/`、`practice/results/metrics.csv` 为同级目录结构，运行：

```bash
python /path/to/unpacked/figure-tools/render_figures.py --font-path /path/to/NotoSansSC.ttf
```

无需D13目录或完整Hugo仓库。三张SVG始终写入包内 `figure-tools/`，PNG及预览写入包内 `images/`。脚本不会为独立包创建仓库assets或content目录。
