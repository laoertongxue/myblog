# D12 第二轮候选交接

状态：第一轮独立意见已处理，v2候选等待第二轮独立对抗式审查；两轮通过后才可发布。未提交、未推送、未改原工作区。

源仓库 `/Users/laoer/Documents/12lab.cn`，HEAD `c9ece37ebc1a54066642b3ff329ccc6948687948`，准备前 `git status --short` 为空。候选在工作目录的隔离副本 `d12-candidate/`。复制时排除 `.git`、构建缓存和 `sealed/`；未打开原测试标签或D9下载包。D9日常检查仅验证既有发布结果哈希并复算开发验证段。

## 交付路径

- `content/blog/forecast-error-bias-metrics/`：正文与5图。
- `experiments/d12-forecast-errors/`：实践、输入、全精度结果、图脚本、灰度预览和渲染报告。
- `scripts/package-d12.py`：确定性打包脚本。
- `static/downloads/d12-forecast-errors-{practice,article,images}.zip`：3个读者包。
- `docs/d12-review/`：验证证据，不伪称独立审查报告。

发布检查规则没有变化；`scripts/check.sh`、`AGENTS.md`、D9完整性哈希和原测试产物均未修改。日后迁入原仓库只需上述D12新增路径；不要同步整个隔离副本。

## 实际验证

24项实践测试通过，含手算、全零WAPE、零行保留、误差方向、MAE/RMSE排名反转、异常输入、分组汇总、全部预测的Fraction独立展开核对，以及未来污染与窗口边界。

干净解压运行24项测试，通过；在其他工作目录运行入口，5个结果文件逐字节一致；3个ZIP清单集合完整、逐成员SHA256一致，无重复路径。

`HUGO_CACHEDIR=/tmp/d12-hugo-cache BROWSER_CHECKS=require make check` 通过。Hugo 0.166.0 extended，与CI一致。7项浏览器检查全部通过；D9 20项回归及2条开发验证复算通过，未读取sealed或重评原测试。初次沙箱执行因缓存目录写权限、本机监听限制失败；仅将Hugo缓存定位到/tmp并在允许本机监听的环境重跑，不修改或跳过检查。

五图通过灰度像素、字形覆盖、文字边界和文字重叠检查；作者逐张查看280/350px缩略图。图片重绘使用临时venv：Python 3.14、Pillow 13.0.0、fontTools 4.68.0及本机Noto Sans SC，字体SHA在渲染报告中。

## 已查一手来源

- https://otexts.com/fpp3/toolbox.html#forecast-errors：误差定义、MAE/RMSE、MAPE零值问题。
- https://robjhyndman.com/hyndsight/wape.html：WAPE定义、零分母、非平稳分母限制。

## 独立审查重点

必须对照全量42行表与逐行预测复算。检查文章、脚本、数据和图表共同口径，以及原测试边界。模型参数全量展示为MA3/7/14、SES0.2/0.5/0.8和SNaive7；本篇没有新模型和最终选型。五日输出是额外追溯材料，主表不作五日排名；其窗口重叠。

第一轮处理见round1-resolution.md；第二轮独立复核、迁入原仓库、提交推送、线上核验尚未进行。Space附件保存为当前候选，修改后应明确版本与哈希。

## 页面专项自检

本机静态预览1440、390、320像素宽，4张表可键盘聚焦，手机表格内部横向滚动；页面无横向溢出、5图加载成功。输出 `browser-review.txt` 和 `output/playwright/d12-*.png`。作者查看1440页首与320表格截图，未发现裁切或重叠。Space保存内容及附件已回读；Space自身的渲染预览尚未目视检查。
