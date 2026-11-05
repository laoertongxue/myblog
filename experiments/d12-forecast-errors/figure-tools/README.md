# D12 黑白图重绘

Python、Pillow、fontTools和独立TTF/OTF的 Noto Sans SC 或 Noto Sans CJK SC 字体。字体不随包分发；可从 Google Fonts 的 Noto Sans SC 页面获取。

```bash
python -m pip install Pillow fontTools
python practice/run.py
python figure-tools/render_figures.py --font-path /path/to/NotoSansSC.ttf
```

脚本按自身位置寻找文件。五张图输出于 `images/`；封面原生900×383，其余按内容排版，不裁切。同步输出280/350px宽预览、字体哈希和文字边界、重叠、灰度检查报告。正文图最小字号48/1200，280px宽时为11.2px；原图链接作为补充。

手算图为固定教学示例；禾味偏差图与服装指标图读取 `practice/results/metrics.csv` 的完整精度值。图三比较MAE和RMSE，同一指标面板采用相同尺度。机器检查不代替人眼检查和独立审查。
