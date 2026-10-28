# AGENTS.md — 12lab.cn

Hugo 静态站（无外部主题依赖，全部模板与样式收归仓库内 `layouts/` 与 `assets/`），GitHub Actions 构建后
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
| 推送前校验 | `make check`（已含浏览器检查，装好依赖时） |
| 只跑浏览器检查 | `npm run check:browser -- [--only design] [--dir public]` |
| 首次准备浏览器检查 | `npm ci && npx playwright install chromium` |

`hugo.yaml` 已删除：`hugo.toml` 是唯一配置入口。
`BROWSER_CHECKS=0 make check` 可临时跳过浏览器检查；`BROWSER_CHECKS=require` 让缺少
playwright 变成失败（CI 用的就是它，见下）。

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


- `summary` 是可选的手写列表摘要，通常以约 120–180 字为目标，准确概括业务问题、案例或方法与阅读收益，
  不为凑长度添加空话。列表优先读取 `.Params.summary`，为空时回退 `.Description`；不要使用 Hugo
  自动生成、可能过长的 `.Summary`。`description` 继续保持简短，服务 SEO、文章导语、搜索与订阅描述，
  不因列表需要更完整的摘要而扩写。`archetypes/blog.md`、`topics.md`、`weekly.md` 提供空 `summary`，
  但它不是发布必填字段，不增加强制长度或元数据门槛。

## 导航

真值只有一处：`hugo.toml` 的 `[[menu.main]]` 与 `[[menu.utility]]`，由
`layouts/_partials/lab/site-header.html` 与 `site-footer.html` 消费。模板只读两个字段：
`[menu.*.params] placement`（`leading` = 顶栏左侧、`quick` = 顶栏右侧、留空只进移动端浮层）
和 `weight`（顺序，也决定移动端浮层顺序）。**不要**在模板里再硬编码一份导航，也不要在菜单里
加模板不读的字段：曾经配置的 `params.icon` 没有任何模板渲染，已删除；
`layouts/_partials/lab/icon.html` 只服务模板里写死的三个图标（`menu`/`search`/`toc`）。
页脚只从 `[[menu.utility]]` 取 `identifier = "archive"` 与 `"copyright"` 两项。

## 样式与图片

- **每篇文章只有一张列表封面，且仅封面要求 900 × 383px**，精确比例为 `900:383`（约 2.35:1）。
  交付前核对封面 PNG 文件的实际像素，不用提示词、留白补边、拉伸或裁切旧图代替重新设计。
  封面优先从可编辑 SVG 原生排版后导出；本次源文件保存在 `assets/cover-sources/`，不放入文章
  bundle，避免自动发现时把设计源当成额外配图。封面应简明，中文标题和示意图在缩略图中仍清楚。
  每篇 front matter 的 `images` 只指定这一张封面，正文首图也使用同一文件；列表不展示其他正文图。
  首页、博客、Weekly、专题及标签/分类列表共用紧凑条目：日期和标题在上，下方 `.row-content`
  内封面在左，摘要、继续阅读、阅读时长与栏目组成 `.row-summary` 在右，两列顶部对齐。
  大于 900px 时封面列宽为内容区宽度的 46% 与 540px 中的较小值，列间距 32px；
  不超过 900px 时改为封面在上、信息在下，封面仍最多 540px，手机占满可用栏宽。
  没有封面的条目只展示全宽信息。标题保留在 `.row-body h2`，不放进图文两列，条目间距保持紧凑。
  `.row-summary` 为随网格行自然伸展的纵向 flex 区，不设置固定高度或最小高度；摘要宽度最多 `38em`、
  行高 `1.7`，继续阅读上距 `16px` 且靠左。其 `.row-meta` 用 `margin-top:auto`、上内距 `14px`
  放在文字区底部；堆叠布局按内容自然增高，不补空白。宽屏通常以 3–4 行摘要为目标，窄屏允许更多行，
  不截断、不钳制行数，也不通过固定高度对齐。
  Hugo `.Fit` 使用 `540x230`、`900x383` 两档边界，CSS `object-fit: contain` 保留完整画面。
  **其他正文配图按原始尺寸与比例保留，没有统一像素尺寸要求。** 不使用历史例外清单或哈希白名单
  限制正文图尺寸；正文默认按原比例占满阅读栏宽、自动高度，不裁切、不拉伸、不套用封面宽幅框。
  文字密集的技术图可用 `[![图片说明](images/diagram.png)](images/diagram.png)` 提供原图入口，
  不重复包裹已有链接；放大阅读仅为补充，不能代替合理排版与正文可读性。
  浏览器检查分别校验单封面的实际 `900x383` 尺寸，以及正文图的原比例、完整加载与无溢出。
  上下篇导航在桌面和手机上均为左右两列：上一篇在左、下一篇在右，缺项保留空格，不挤到另一侧。
  已有 `thumbnailFit` 字段不再决定显示方式；头像和导航图标继续使用各自尺寸。
  详见 `docs/列表缩略图.md` 与 `docs/2026-10-28-图片规格核查.md`。
- 站点的设计系统全部在 `assets/css/custom.css`，采用顶部导航与居中单栏。
  由 `layouts/_partials/head.html` 将 `assets/css/chroma.css`（Hugo Chroma 语法高亮）和此文件合并、压缩并加指纹（已彻底移除外部 `themes/hextra` 依赖）。
  定制样式仍统一维护在此文件；不要另起未接入编译链的 CSS 文件。
- 头像走 Hugo 图片管线：`static/images` 里的文件不会被 `[imaging]` 处理，必须放 `assets/images/`，
  由 `layouts/_partials/lab/avatar-src.html` 调 `.Fill` 产出 webp。把图片挪回 `static/` 会让
  `[imaging]` 重新变成空转（`make check` 会拦）。
- 头像在页面上只有一个渲染点：`layouts/single.html` 的 `.about-intro` 区块，由页面 front matter
  `aboutIntro: true` 打开（当前只有 `content/about/index.md`）。删掉这个标记等于删掉全站唯一
  显示头像的地方，浏览器检查会失败。head 里的社交图另走 `params.avatar`（`layouts/_partials/head.html`）。
- **属性名位置不能直接写 `{{ with partial ... }}`。** `{{ with partial "lab/nav-current.html" ... }}aria-current="{{ . }}"{{ end }}`
  写在 `<a href="…"` 之后时，Go 的 html/template 会在 partial 返回空串（即"非当前栏目"，
  绝大多数链接）时输出字面量 `ZgotmplZ`，把整个属性顶掉——线上曾出现 1208 处。
  正确写法是先把结果存进变量再 `with`；`scripts/check.sh` 现在会 grep `zgotmplz` 拦截。
- 结构化数据与 feed 声明在 `layouts/_partials/custom/head-end.html`。整段 JSON 用一次
  `dict | jsonify | safeJS`；逐字段 `jsonify` 会被 `<script>` 上下文二次转义成 `"\"值\""`。
  Go 的时区版式是 `Z07:00`/`-07:00`，`Z08:00` 会被原样输出成非法日期。

## 服务器侧（仓库改了不等于线上改了）

- `scripts/Caddyfile` **不由 CI 下发**：服务器上只有构建产物，没有仓库，所以
  `scripts/server-init.sh` 必须先和 `scripts/Caddyfile` 一起传到服务器（同一目录，脚本按
  `$(dirname "$0")/Caddyfile` 找配置），再由管理员执行。缓存与安全头类改动如果没有这一步，
  线上不会变化。
  ```bash
  # 本地：两个文件一起传
  scp scripts/server-init.sh scripts/Caddyfile <管理员>@43.255.31.74:/root/
  # 服务器（root）：校验 → 备份 → 安装 → reload → 健康检查，任一步失败自动装回备份
  cd /root && bash server-init.sh
  # 无 systemd 时改用 caddy 自带 reload
  # install -m 644 /root/Caddyfile /etc/caddy/Caddyfile && caddy reload --config /etc/caddy/Caddyfile
  ```
  生效后在本地核对 `curl -sSI https://12lab.cn/ | grep -iE "strict-transport|content-security"`。
- 安全头里除 `nosniff` / `SAMEORIGIN` / `Referrer-Policy` 外还有 HSTS（不带
  `includeSubDomains`/`preload`，180 天，避免不可逆地牵连子域）与 CSP。
  **CSP 不是只在服务器上生效的字符串**：`scripts/run-browser-checks.mjs` 会从 Caddyfile 读出
  `Content-Security-Policy` 并加在本地静态服务上，所以每个浏览器检查都在真实策略下运行；
  被 CSP 拦掉的脚本/样式/图片会以 `requestfailed ... csp` 或控制台报错让 `make check` 失败。
  改 CSP 时必须同时保证 `make check` 仍然通过（脚本全部是指纹化外部文件，故 `script-src 'self'`；
  缩略图数量用的是行内 style 属性，故 `style-src` 需要 `'unsafe-inline'`；`docs/列表缩略图.md`
  允许外链 HTTPS 图片，故 `img-src` 含 `https:`）。行内 `application/ld+json` 数据块不受 `script-src` 约束。
- 服务器上 `/var/www/12lab.cn/current` 必须是**符号链接**；发布脚本遇到普通目录会中止，禁止自动删除迁移。
- 发布产物落在 `releases/<UTC时间戳>-<run_id>-<attempt>/`，保留 5 份并保护当前和上一份正常版本。
- `release-manifest.json` 记录全部文件的 SHA-256、HTML 数量及关键 HTTP 探针。远端校验后才切换。
- `scripts/deploy-release.py` 在切换前保存 current 原目标；HTTP、网络或中断异常均恢复该目标，禁止按目录时间猜测回滚版本。
- 发布账户为 `deploy12lab`，仅写站点目录和自己的 home，无 sudo；CI 使用 `DEPLOY_SSH_KEY_DEPLOY12LAB`。
- SSH 指纹固定在 `scripts/deploy-known-hosts`，更新前通过可信管理员连接核验，禁止关闭 StrictHostKeyChecking。
- 初次配置部署账户运行 `scripts/setup-deploy-user.sh <公钥文件>`，管理员负责 Caddy 配置，不给发布账户授权。

## 不要提交

`public/`、`resources/`、`.hugo-check/`、`output/playwright/`、`.playwright-cli/`、`.hugo_build.lock`
、`node_modules/`、`.npm-cache/`、`.playwright-browsers/`
（均已在 `.gitignore` 中）。`package.json` 与 `package-lock.json` **要提交**：它们声明浏览器检查
唯一的依赖（playwright）。注意 `public/` 常是 `hugo server` 的转储（地址是 localhost），
判断线上状态请以 Actions 产物或线上站点为准，不要用 `public/` 比对。

## SEO 与资源输出

- 页面 head 由本仓库 `layouts/_partials/head.html` 统一输出，避免主题与自定义模板重复 robots、canonical。
- 列表模板与 head 共用 `lab/pager.html`：Hugo 的首次 `.Paginate` 调用决定数据集，不可分别定义。
- `testContent: true` / `noindex: true` 内容不进入 sitemap、RSS；搜索页与纯测试标签页输出 noindex。
- 通用交互放 `assets/js/lab.js`，搜索逻辑仅在搜索页加载 `assets/js/search.js`。搜索索引带内容指纹。
- `make check` 顺序：Hugo 构建 → 路由/内容契约/日期与转义 placeholders 的 grep → SEO、图片链接、
  分页夹具、专题系列 → 三类文章真实生成与发布故障注入（临时目录）→ **浏览器检查**。
- 浏览器检查是 `scripts/check-*.js` 里的 `async (page, ctx) => {}` **闭包**，本身不是程序
  （`node scripts/check-design-browser.js` 会静默退出 0）。统一由 `scripts/run-browser-checks.mjs`
  提供静态服务（默认 1316 端口，行为对齐 Caddy，含真实 404）并逐个执行，`ctx` 提供
  `base`/`assert`/`pagerSize`（读 `hugo.toml`）/`walkPagination`/`rssCount`。
  断言应尽量从构建产物推导（页数、章节数、图片原始比例），不要写死"10 篇""11 张图"这类计数。
- CI 在构建前 `npm ci && npx playwright install --with-deps chromium --only-shell`，并以
  `BROWSER_CHECKS=require` 跑同一份 `make check`，因此浏览器检查不会被静默跳过。
