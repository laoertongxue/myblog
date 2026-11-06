# 预测课堂迁移

线上入口为 `/forecast/`，109 课各有 `/forecast/<stable-id>/` 页面，全部正文由 Hugo 输出，不依赖 JavaScript 抓取。课程与 `/topics/forecasting/` 博客文章分别维护。

## 内容来源

- 原站：<https://shierhuasheng.royal-chub-7016.chatgpt.site>
- 公开版本：3；源提交：`a106275804a20f2598bfd142868a1e68731d5359`
- `data/forecast/course.json` 保存该版本的完整课程数据；`upstream/` 保存编辑用 Markdown 与原构建脚本。
- `static/forecast/` 保存 68 个原始资源；`upstream-manifest.json` 记录课程数据与资源 SHA-256。日常校验不重新执行下载包里的实验或重算测试结果。
- 原站构建需要 Python 3 与 Pandoc；如需重新构建，将本仓库 `static/forecast/` 的内容复制至临时上游源码目录的 `dist/`，再执行该目录内 `build.py`。审查构建差异后才更新课程数据、资源和来源清单，不能为通过校验自动刷新哈希。

## 维护与校验

`python3 scripts/generate-forecast.py` 从课程数据生成 `content/forecast/*/index.md`，保留正文和原始锚点，改写跨课链接与资源路径，并生成每课标题、描述。生成结果入库；`make check` 会检查它与数据源是否一致。

页面沿用博客统一的 head、导航、CSS 管线和站点地图。课程专用交互为 `assets/js/forecast.js`。`make check` 包括课程全文、下载校验值、ID 唯一性、内链/锚点、SEO 及真实浏览器检查；发布清单另加入教程首页、课程、资源中心、搜索索引和下载包探针。

旧 `#unit-*` 和前 82 课的 `#lesson-N` 链接在 `/forecast/` 下兼容，转入各课独立页面。原域名的浏览器 localStorage 不能跨域读取，因此不自动迁移旧站进度；可在旧站导出留存，新站重新勾选。课程进度为自报完成，没有认证或云同步。

原站仍是独立公开副本；本仓库不会更改其托管或权限。新站以自引用 canonical 表示本域首选地址，不声称搜索引擎已收录，也不保证排名。
