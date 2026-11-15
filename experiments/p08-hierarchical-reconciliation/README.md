# 供应链预测与计划 · 第8篇完整实验包

先双击图文阅读版HTML；正文图片已内嵌，不依赖网络。文章源稿使用images相对路径，需与images文件夹一起保留。

## 复现
进入practice，Python 3.10+：
```
python run.py
python -m unittest -v
```
输入、输出、字典说明和模拟边界见practice/README.md。数据运算仅用标准库；现有PNG/SVG无需额外工具。

可选重画图：安装matplotlib并准备Noto Sans CJK字体，运行`python figure-tools/make_figures.py`；可用CJK_FONT_PATH指定字体。图片为设计性手算示意，不是实验准确率曲线。

## 范围
全部数据与场景为教学模拟。服装与禾味不是实际经营成绩。固定权重协调，不含MinT、概率协调、预测训练、真实审批或自动采购。

文章经历至少两轮独立对抗审查，首轮失败项与修复后的第二轮报告一并保留。本版本为经作者授权发布到12lab.cn的配套资料。审查记录反映发布前各轮状态。

MANIFEST.sha256用于核验包内文件；不包含其自身。浏览器截图为私有QA材料，不装入本包。
