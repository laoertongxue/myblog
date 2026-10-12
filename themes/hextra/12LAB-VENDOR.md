# Vendored Hextra — provenance

This directory is a **vendored copy** of the [Hextra](https://github.com/imfing/hextra)
Hugo theme. Vendoring strips upstream metadata (there is no `VERSION` file, no git
submodule and no Hugo Module record), so this file is the record: without it the
version in `README.md` / `AGENTS.md` cannot be checked against anything in the
repository.

| Field | Value |
| --- | --- |
| Upstream | https://github.com/imfing/hextra |
| Recorded version | v0.12.3 |
| Vendored on | 2026-10-08 (commit `ec76f51`, "build: vendor hextra 到 themes/ 并删除 Hugo Modules 路径") |
| Enabled by | `hugo.toml` → `theme = "hextra"` |
| Minimum Hugo | `min_version = "0.146.0"` (`theme.toml`); CI pins Hugo 0.166.0 |
| License | MIT (`LICENSE` in this directory) |
| Tracked files | 195 |

## Rules

- **Do not make site changes in here.** Project overrides belong in `layouts/`,
  `assets/css/custom.css` and `scripts/`; a file copied into `layouts/` at the same
  path wins over the theme, which is how this site replaces `baseof.html`,
  `head.html` and the list/single templates.
- **Upgrading**: replace this directory with the upstream release, update
  `Recorded version` / `Vendored on` above, then run `make check`. The browser
  checks and `scripts/check-seo.py` are what catch theme-level regressions — the
  site's own templates and CSS no longer depend on Hextra's CSS variables at all,
  only on its `_markup` render hooks, icons/favicons partials and data files.
