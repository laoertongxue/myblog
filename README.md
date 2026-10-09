# 12lab.cn

> 拾贰画生的个人站：博客、周刊与长期维护的专题系统。

线上地址：**https://12lab.cn/**

本站是一个 Hugo 静态站，主题 [Hextra](https://github.com/imfing/hextra) v0.12.3 已经 vendor 进 `themes/hextra/`，由 GitHub Actions 自动构建并 rsync 到单机 Caddy。任何 `push` 到 `main` 的提交都会直接上线；本地构建失败的改动会被部署脚本原子回滚到上一个稳定 release。

## 三类内容

| 栏目 | 路径 | URL 形式 | 必填 front matter |
| --- | --- | --- | --- |
| 博客 | `content/blog/<name>/index.md` | `/blog/<slug>/` | `slug`、`date`、`description`、`tags`、`categories` |
| 周刊 | `content/weekly/<NNN>/index.md` | `/weekly/<NNN>/` | `date`、`description`、`tags`、`categories` |
| 专题 | `content/topics/<topic>/<NN-name>/index.md` | 目录名 | `date`、`weight`、`description` |
| 单页 | `content/<name>/index.md` | 目录名 | 不强制 `date` |

**写一篇新博客的标准流程**：

```bash
hugo new blog/<slug>/              # 按 archetypes/blog.md 生成骨架
# 编辑 content/blog/<slug>/index.md
make check                         # 本地构建 + SEO/图片/分页/内容契约校验
git push                           # 触发 CI，部署到 12lab.cn
```

周刊与专题同理，分别走 `archetypes/weekly.md` / `archetypes/topics.md`。

## 内容契约（必读）

- **博客必须有 `slug`**：`[permalinks] blog = "/blog/:slug/"` 在缺 `slug` 时会回退到标题，中文标题会产生百分号编码、改一次标题即永久断链。需要保留旧地址时用 `aliases: [...]`。
- **周刊目录名同时决定 URL 与页面上 `Vol. NNN` 标签**：`row.html` 与 `article.html` 都从 `.File.ContentBaseName` 取期号。改名等于换链接又改期号。
- **专题章节顺序与上下篇都由 `weight` 决定**：模板不再读取任何 `prev` / `next` 字段。
- **非草稿的 `blog` / `weekly` / `topics` 必须有 `date`**：缺日期会让 Article 结构化数据发布 `0001-01-01`，被 `make check` 直接 FAIL。
- **未来日期会被 Hugo 主动排除**：到期发布依赖 `deploy.yml` 的定时任务（每天 00:10 Asia/Shanghai 重建），不依赖是否有人 push。

## 技术栈

- **Hugo** v0.166.0+extended（Hextra 要求 `min_version = "0.146.0"`）
- **Hextra** v0.12.3，vendor 到 `themes/hextra/`，由 `hugo.toml` 的 `theme = "hextra"` 启用
- **项目级覆盖**位于 `layouts/_partials/lab/*`、`layouts/baseof.html`、`layouts/_partials/head.html`、`assets/css/custom.css`，独立于主题升级，主题切换可分享干净副本
- **GitHub Actions**：build → release-manifest → rsync 到 `43.255.31.74`，部署账户 `deploy12lab` 仅有最小权限
- **Caddy**：基于内容哈希的 immutable 缓存、`nosniff` / `SAMEORIGIN` / `strict-origin-when-cross-origin` 安全头、zstd+gzip

## 本地开发

| 目的 | 命令 |
| --- | --- |
| 本地预览 | `make serve`（http://localhost:1313） |
| 与 CI 一致构建 | `make build` |
| 推送前校验 | `make check` |

`make check` 比 CI 的 build 步骤更严格：除了构建还跑 SEO / 图片链接 / 分页 / 三类文章真实生成 / 发布故障注入测试，详见 `scripts/check.sh` 与 `scripts/check-*.py`。`make build` 只构建不校验——发布前请用 `make check`。

## 部署

- `push` 到 `main` 触发 `.github/workflows/deploy.yml`：Setup Hugo 0.166 → `OUT=public make check` → 生成 SHA-256 清单 → 上传 artifact
- 然后 deploy job：rsync 到 `releases/<UTC时间戳>-<run_id>-<attempt>/`，调用 `scripts/deploy-release.py`
- `deploy-release.py` 会校验 SHA-256、HTML 数等于 CI 报告、做 HTTP 探针；**任一失败原子回滚**到 `previous-release.txt` 指向的 release
- 当前与上一份正常 release 始终保留；服务器最多保留 5 份
- 服务器配置（Caddy 头、缓存规则）由管理员登录执行 `scripts/server-init.sh` 下发，**不在 CI 链路中**——仓库改了不等于线上改了

## 目录结构（高层）

```
archetypes/      # hugo new 骨架（blog / weekly / topics / default）
assets/          # css / js / 头像图（Hugo 图片管线入口）
content/         # 博客 / 周刊 / 专题 / 单页
docs/            # 设计与工程变更日志
layouts/         # 项目级模板，覆盖 themes/hextra 同名文件
scripts/         # 构建检查 / 发布 / 服务器初始化
themes/hextra/   # vendor 的主题（独立可分享）
AGENTS.md        # AI 协作 / 改代码时的工程注意事项
```

## 相关文档

- **改代码前必读**：[`AGENTS.md`](./AGENTS.md) — 列出所有"为什么这么写"的不变量、CI 发布门槛、回滚路径、SSH 凭据策略
- **设计变更日志**：[`docs/`](./docs/) — 单栏改版、列表缩略图、后台链路修复等历史记录
- **主题原文档**：[`themes/hextra/README.md`](./themes/hextra/README.md) — vendored Hextra 主题的官方说明

## 致谢与许可

- 主题：[imfing/hextra](https://github.com/imfing/hextra)（MIT）
- 静态站点生成：[Hugo](https://gohugo.io/)（Apache-2.0）
- 站内原创内容采用 [CC BY-NC-ND 4.0](https://creativecommons.org/licenses/by-nc-nd/4.0/)，详见站内版权页

© 拾贰画生 · [12lab.cn](https://12lab.cn/)
