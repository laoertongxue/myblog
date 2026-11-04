# D11-v2 candidate — author verification, not independent review

Status: revised after parent-relayed independent round-1 findings; pending round 2. Do not publish without parent confirmation.

Original repository: `/Users/laoer/Documents/12lab.cn`, main at `6e78881ec5cace564c101ca4dca85cb58254dfae` (D10). Working tree was clean before and after preparation. Remote main was checked read-only and matches; GitHub API reports push access. D10 live URL returned HTTP 200. No original-repository file was changed, staged, committed or pushed.

The candidate is an additive overlay at the requested slug `simple-exponential-smoothing-demand-forecast`. Date is `2026-11-04T09:00:00+08:00`, draft false for eventual publication; this does not authorize deployment. The site is Hugo 0.166.0 extended, same as CI. Node 26.8.2, npm 11.19.1, Python 3.14.7, Playwright 1.64.0 and installed Chromium are available.

## Completed author checks

- 27 practice unit tests pass, including hand expectations, invalid CSV quoting, missing dates, future contamination, first initialization, endpoints and independent expanded geometric-weight Fraction arithmetic for all validation forecasts and metrics.
- Only two unchanged development CSVs were used. All 28 single-day targets and 24 contained five-day windows per case/method are retained. The current package contains no original last-40-day labels; the current experiment entrypoint reads development CSVs and scores validation only. Package contents cannot prove historical file access. The original D9 ZIP hash remains an inherited declaration, not a fresh independent verification.
- Five monochrome figures, exact 900×383 cover. Text bounds/overlap, Simplified Chinese glyphs, every-pixel grayscale and all plotted predictions/levels versus practice outputs pass. Source and reports accompany the candidate. Original PNGs and 280/350 px previews were inspected; actual-theme phone figures and tables also checked.
- Independent disposable copy of current tracked source plus candidate built successfully with `hugo --gc --minify` and a task-local cache. Parsed content, 28 required route checks, local image/article links and SEO checks pass.
- All 7 existing browser suites passed on v1 under the repository's CSP-aware static server. For v2, affected build/content/SEO and D11-specific browser checks were repeated; the unchanged general suites were not repeated.
- D11-specific actual Hugo preview passes at 1440/390/320 widths: no horizontal document overflow, 19 original/responsive image candidates fully loaded and grayscale, no browser errors, exactly one listing cover, D10 previous navigation, 2 accessible horizontal-scroll tables with no split numbers. All three download URLs returned ZIP content. No separate end reference module.
- Actual HTTP-downloaded practice ZIP passes CRC/manifests and all 27 tests. All 6 data result files reproduce byte-for-byte. Downloaded article/figures match candidate bytes. Downloaded figure ZIP rerenders all 15 original/phone PNGs byte-for-byte with the recorded local font.

The full `make check` is not reported as passed: initial disposable-copy invocation encountered executable-bit loss while copying; targeted build/content/link/SEO and browser checks then ran successfully. We deliberately did not invoke the legacy D9 `run.py finalize` step, which re-evaluates the already exposed original test block. Publication-stage requirements and that existing regression step remain for the parent to reconcile; no D11 test-block evaluation should be added.

## Packaging / integration

- `content/blog/.../` contains article and five PNGs. The first image and sole frontmatter cover are the same PNG. Body images retain intrinsic aspect ratios and link to original files.
- `experiments/d11-simple-exponential-smoothing/` preserves standard-library practice, data, results, renderer, previews and provenance. Figure source is Python, following D10; no SVG is claimed.
- `scripts/package-d11.py` reproduces the three deterministic reader ZIPs. It excludes Python caches and adds manifests. It does not upload or publish.
- `static/downloads/` holds the three final reader archives.
- Review-support logs, scripts and selected screenshots accompany the external frozen review bundle; they need not be committed to the blog.

The review bundle root manifest covers every regular member under both candidate/ and review-support/, excluding only the manifest itself. An archive-vs-manifest set-equality and byte-hash check is required before upload. Any revision requires a new candidate hash, fresh affected verification and review of the changed material. This file is author evidence, not a claim of either adversarial review passing.
