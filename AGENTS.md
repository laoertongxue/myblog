# AGENTS.md — 12lab.cn

Hugo 静态站（主题已 vendor 进 `themes/hextra/`，来源是 `github.com/imfing/hextra`
v0.12.3，由 `hugo.toml` 的 `theme = "hextra"` 启用），GitHub Actions 构建后
rsync 到单机 Caddy。

## 改动前必须知道的事

- **`push` 到 `main` 就是上线。** 没有预发环境，`main` 无分支保护，历史上 PR 数为 0。
- 本地推送前和 CI 发布前都跑 `make check`（构建 + 断言本仓库真实回归项）。`make build` 只构建，不校验。
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

- **准备发布或定时发布的博客必须有 `slug`。** `[permalinks] blog = "/blog/:slug/"` 在缺 `slug` 时会回退到**标题**，
  于是中文标题会产生百分号编码的线上地址，之后改一次标题就等于永久断链。
  需要保留旧地址时用 `aliases: ["/blog/<旧路径>/"]`，Hugo 会生成 meta-refresh 重定向页。
- **周刊的目录名同时决定 URL 和页面上显示的 `Vol. NNN`**（`row.html`、`article.html` 读
  `.File.ContentBaseName`）。改名等于换链接又改期号。
- **专题章节顺序与上下篇都由 `weight` 决定**（`chapters.html`、`article.html`）。曾经存在的
  `prev:`/`next:` 字段没有任何模板读取，已删除——不要再加回来。
- `date` 是非草稿 `blog`/`weekly`/`topics` 的硬性要求（由 Hugo 解析，支持带引号日期）：缺日期会让 Article 结构化数据发布 `0001-01-01`。
  `draft: true` 的内容允许暂缺必填元数据，但 front matter 本身仍须能被 Hugo 解析。
  反过来，**未来日期会被 Hugo 主动排除**，到期内容由 `deploy.yml` 的 `schedule` 触发（每天 00:10
  Asia/Shanghai）重建后才会出现，不依赖是否有人 push。

## 导航

真值只有一处：`hugo.toml` 的 `[[menu.main]]` 与 `[[menu.utility]]`，由
`layouts/_partials/lab/site-header.html` 与 `site-footer.html` 消费（`icon` 走 `[menu.*.params]`，取值见
`layouts/_partials/lab/icon.html`）。**不要**在模板里再硬编码一份导航。

## 样式与图片

- 站点的设计系统几乎全部在 `assets/css/custom.css`，采用顶部导航与居中单栏。
  由 `layouts/_partials/head.html` 将主题变量、主题 CSS 和此文件合并、压缩并加指纹。
  定制样式仍统一维护在此文件；不要另起未接入编译链的 CSS 文件。
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
- 服务器上 `/var/www/12lab.cn/current` 必须是**符号链接**；发布脚本遇到普通目录会中止，禁止自动删除迁移。
- 发布产物落在 `releases/<UTC时间戳>-<run_id>-<attempt>/`，保留 5 份并保护当前和上一份正常版本。
- `release-manifest.json` 记录全部文件的 SHA-256、HTML 数量及关键 HTTP 探针。远端校验后才切换。
- `scripts/deploy-release.py` 在切换前保存 current 原目标；HTTP、网络或中断异常均恢复该目标，禁止按目录时间猜测回滚版本。
- 发布账户为 `deploy12lab`，仅写站点目录和自己的 home，无 sudo；CI 使用 `DEPLOY_SSH_KEY_DEPLOY12LAB`。
- SSH 指纹固定在 `scripts/deploy-known-hosts`，更新前通过可信管理员连接核验，禁止关闭 StrictHostKeyChecking。
- 初次配置部署账户运行 `scripts/setup-deploy-user.sh <公钥文件>`，管理员负责 Caddy 配置，不给发布账户授权。

## 不要提交

`public/`、`resources/`、`.hugo-check/`、`output/playwright/`、`.playwright-cli/`、`.hugo_build.lock`
（均已在 `.gitignore` 中）。注意 `public/` 常是 `hugo server` 的转储（地址是 localhost），
判断线上状态请以 Actions 产物或线上站点为准，不要用 `public/` 比对。

## SEO 与资源输出

- 页面 head 由本仓库 `layouts/_partials/head.html` 统一输出，避免主题与自定义模板重复 robots、canonical。
- 列表模板与 head 共用 `lab/pager.html`：Hugo 的首次 `.Paginate` 调用决定数据集，不可分别定义。
- `testContent: true` / `noindex: true` 内容不进入 sitemap、RSS；搜索页与纯测试标签页输出 noindex。
- 通用交互放 `assets/js/lab.js`，搜索逻辑仅在搜索页加载 `assets/js/search.js`。搜索索引带内容指纹。
- `make check` 同时验证 SEO、图片链接、分页及内容契约；浏览器交互检查使用 `scripts/check-design-browser.js` 与 `scripts/check-mobile-navigation.js`。

- `make check` 还包含三类文章的真实生成测试和发布故障注入测试；均在临时目录执行，不触及线上 current。
