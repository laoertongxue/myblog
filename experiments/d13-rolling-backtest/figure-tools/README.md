# D13 黑白图重绘

Python、Pillow、fontTools及独立TTF/OTF的Noto Sans SC或Noto Sans CJK SC字体。字体不随包分发。

```bash
python -m pip install Pillow fontTools
python practice/run.py
python figure-tools/render_figures.py --font-path /path/to/NotoSansSC.ttf
```

脚本按自身位置查找输入，输出4张灰度图与280/350px预览到images。封面原生900×383，正文按内容排版；无裁切拉伸。图2读negative_control.json；缺货图读stockout_simulation.csv，空白值断线、零值保留。数据曲线点标记、实虚线与文字共同区分，不仅靠灰度。图中文字、字形、边界和重叠检查结果在render-quality-report.json。

使用环境：Python 3.14、Pillow 13.0.0、fontTools 4.68.0；字体文件SHA见报告。其他版本可能产生像素差异，指标计算不依赖绘图库。主图、280px和350px均应人工复核，机器检查不能替代审查。
