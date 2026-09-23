# AGENTS.md — 12lab.cn

Hugo 静态站（主题以 Go module 方式引入 `github.com/imfing/hextra`，不是 `themes/`），
GitHub Actions 构建后 rsync 到单机 Caddy。

## 改动前必须知道的事

- **`push` 到 `main` 就是上线。** 没有预发环境，`main` 无分支保护，历史上 PR 数为 0。
- 推送前跑 `make check`（构建 + 断言本仓库真实回归项）。`make build` 只构建，不校验。
- CI 的发布门槛是"上传到服务器的 .html 数 **等于** 本次构建数"，不是阈值。故意丢页会让发布在切换
  `current` 前失败——这是预期行为，不是环境坏了。

## 命令

| 目的 | 命令 |
| --- | --- |
| 本地预览 | `make serve`（http://localhost:1313） |
| 与 CI 一致的构建 | `make build` |
| 推送前校验 | `make check` |

`hugo.yaml` 已删除：`hugo.toml` 是唯一配置入口。

## 内容契约

三条内容类型字段不同，用 `hugo new <section>/...` 会按 `archetypes/` 生成对应骨架。

| 栏目 | 路径 | 必需字段 | URL 来源 |
| --- | --- | --- | --- |
| 博客 | `content/blog/<name>/index.md` | `slug`（=目录名）、`date`、`description`、`tags`、`categories` | `/blog/:slug/` |
| 周刊 | `content/weekly/<NNN>/index.md` | `date`、`description`、`tags`、`categories` | `/weekly/:filename/` |
| 专题文章 | `content/topics/<topic>/<NN-name>/index.md` | `date`、`weight`、`description` | 目录名 |
| 单页 | `content/<name>/index.md` | 无 `date` 也可 | 目录名 |

- **博客必须有 `slug`。** `[permalinks] blog = "/blog/:slug/"` 在缺 `slug` 时会回退到**标题**，
  于是中文标题会产生百分号编码的线上地址，之后改一次标题就等于永久断链。
  需要保留旧地址时用 `aliases: ["/blog/<旧路径>/"]`，Hugo 会生成 meta-refresh 重定向页。
- **周刊的目录名同时决定 URL 和页面上显示的 `Vol. NNN`**（`row.html`、`article.html` 读
  `.File.ContentBaseName`）。改名等于换链接又改期号。
- **专题章节顺序与上下篇都由 `weight` 决定**（`chapters.html`、`article.html`）。曾经存在的
  `prev:`/`next:` 字段没有任何模板读取，已删除——不要再加回来。
- `date` 是 `blog`/`weekly`/`topics` 的硬性要求：缺日期会让 Article 结构化数据发布 `0001-01-01`。
  反过来，**未来日期会被 Hugo 主动排除**，到期内容由 `deploy.yml` 的 `schedule` 触发（每天 00:10
  Asia/Shanghai）重建后才会出现，不依赖是否有人 push。

## 导航

真值只有一处：`hugo.toml` 的 `[[menu.main]]` 与 `[[menu.utility]]`，由
`layouts/_partials/lab/site-header.html` 与 `site-footer.html` 消费（`icon` 走 `[menu.*.params]`，取值见
`layouts/_partials/lab/icon.html`）。**不要**在模板里再硬编码一份导航。

## 样式与图片

- 站点的设计系统几乎全部在 `assets/css/custom.css`，采用顶部导航与居中单栏。
  这个文件是被主题的 `css/compiled/main.css` 编译链吸收的，**仓库里没有显式挂接点**——重命名、改后缀或
  新增第二个 CSS 文件，都会静默丢掉全部定制样式。
- 头像走 Hugo 图片管线：`static/images` 里的文件不会被 `[imaging]` 处理，必须放 `assets/images/`，
  由 `layouts/_partials/lab/avatar-src.html` 调 `.Fill` 产出 webp。把图片挪回 `static/` 会让
  `[imaging]` 重新变成空转（`make check` 会拦）。
- 结构化数据与 feed 声明在 `layouts/_partials/custom/head-end.html`。整段 JSON 用一次
  `dict | jsonify | safeJS`；逐字段 `jsonify` 会被 `<script>` 上下文二次转义成 `"\"值\""`。
  Go 的时区版式是 `Z07:00`/`-07:00`，`Z08:00` 会被原样输出成非法日期。

## 服务器侧（仓库改了不等于线上改了）

- `scripts/Caddyfile` **不由 CI 下发**。生效方式是登录服务器执行 `scripts/server-init.sh`
  （`caddy validate` → 安装到 `/etc/caddy/Caddyfile` → `systemctl reload caddy`）。
  缓存与安全头类改动如果没有这一步，线上不会变化。
- 服务器上 `/var/www/12lab.cn/current` 必须是**符号链接**（原子切换依赖它）；若它是普通目录，
  `deploy.yml` 里的一次性迁移分支会先删掉再建链接。
- 发布产物落在 `releases/<时间戳>/`，只保留最近 5 份；健康检查失败时回滚到上一个 release。

## 不要提交

`public/`、`resources/`、`.hugo-check/`、`output/playwright/`、`.playwright-cli/`、`.hugo_build.lock`
（均已在 `.gitignore` 中）。注意 `public/` 常是 `hugo server` 的转储（地址是 localhost），
判断线上状态请以 Actions 产物或线上站点为准，不要用 `public/` 比对。
