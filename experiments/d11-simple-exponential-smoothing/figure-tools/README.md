# D11 黑白图重绘

从包含`figure-tools/`、`practice/`的实验目录运行：

```bash
python -m pip install Pillow fontTools
python practice/run.py
python figure-tools/render_figures.py --font-path /path/to/NotoSansSC.ttf
```

已验证环境：Python 3.14.7，Pillow 13.0.0，fontTools 4.68.0，独立TTF格式的Noto Sans SC。脚本只接受简体中文Noto字族，逐字检查字形。字体不随包分发；可从[Google Fonts的Noto Sans SC页面](https://fonts.google.com/noto/specimen/Noto+Sans+SC)获取。当前接口接受单字体TTF/OTF，不接受TTC集合。换字体版本可能改变PNG字节；报告记录实际字体SHA-256。

脚本从自身路径定位输入输出，不依赖当前工作目录。只读取两份140行开发CSV和本包计算结果，不读取原测试数据；输入哈希必须与D9/D10一致。绘图单独递推SES，并核对每一个验证预测点和水平点与实践CSV一致。

输出位于`images/`：

- `d11-00_cover.png`：900×383，唯一封面。原生按这个尺寸绘制，不裁切旧图。
- `d11-01_alignment.png`：1200×1470，手算的预测/观察/更新时点。
- `d11-02_split.png`：1200×1320，数据和评价边界。
- `d11-03_hewei.png`、`d11-04_apparel.png`：1200×1860，各含28天一步预测与更新后水平。只有上图的预测进入评分；两面板尺度相同，图例共用。

实线=实际；虚线=α0.2；点线=α0.5；点划线=α0.8。曲线均来自对应序列的全部28个验证目标，没有抽点或再次平滑。纵轴为公斤/日或件/日，横轴为日编号。

`images/preview-280`与`preview-350`对应320/390手机页面扣除边距后的实际阅读栏宽。正文图最小文字48px/1200，在280px显示宽度下为11.2px；完整原图提供放大阅读。封面附属文字更小，仅辅助说明。每幅图同时通过灰度像素、字形覆盖、文字边界与文字重叠检查。`render-quality-report.json`记录这些机器检查，`plotted-curves.json`保留曲线数值。

作者查看预览属于排版自检，不等于独立对抗审查。完成候选后仍需两轮独立审查与实际Hugo页面检查。
