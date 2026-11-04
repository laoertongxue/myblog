# D11-v2: response to parent-relayed independent round-1 findings

The parent reported no blocking editorial issue and no numerical or future-contamination error. This document records the author's response, not an independent acceptance decision. Round 2 and publication confirmation remain pending.

1. **Outer manifest omitted review support.** The v2 root `CANDIDATE_MANIFEST.sha256` covers every regular ZIP member under `candidate/` and `review-support/`. Freeze verification compares the archive member set with the manifest key set, excluding only the manifest itself, then hashes every member. Missing, surplus, duplicated and mismatched members fail.
2. **CSV blank-line wording.** The model and parser behavior are unchanged. Article, practice README and parser docstring now distinguish empty physical lines (skipped by DictReader) from data records (validated, never silently dropped). A whitespace-only record is rejected. Two added tests confirm empty lines are allowed only when date continuity remains intact, missing dates still fail, and a spaces-only line fails. Total: 27 tests.
3. **14/180-day continuity.** Article and practice README distinguish the initial 2-store/8-SKU/14-day data-and-metrics exercise from D9's expanded 180-day forecasting sequence; D11 uses only the first 140 days.
4. **Provenance strength.** The original D9 archive hash is explicitly an inherited declaration, not independently reverified for D11. Provenance describes the current included data and execution scope and states that historical access cannot be established from current package contents alone.

## Affected checks repeated for v2

- 27 tests pass; numeric `cases` summary is exactly equal to v1. Only result version metadata changes to D11-v2.
- Hugo build, content contracts, routes, static links and SEO checks pass on the disposable source copy.
- D11-specific 1440/390/320 browser checks pass with revised prose and current ZIP sizes. No browser errors, page overflow or split table digits; all 19 image candidates remain grayscale and loaded.
- Three actual HTTP-downloaded reader archives pass CRC and manifests; all 27 practice tests pass on extracted bytes; six generated data files reproduce byte-identically. All 15 PNGs rerender byte-identically. Images and their numerical curves have not changed from v1.
- The unchanged 7 general browser suites passed on v1; they were not needlessly repeated for these prose, documentation and test additions. Their v1 log is retained and named explicitly.

The original repository remains unmodified. No commit, push, production deploy or public sharing change has occurred.
