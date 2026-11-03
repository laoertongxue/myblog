# D10 independent editorial and visual review R2

Reviewed at 2026-11-03 01:47 UTC. **PASS for the frozen article, image assets and package-integrity scope below.** No outstanding editorial/visual publication blockers found in this scope. This is not a claim that the website is deployed, its Hugo build passes, or the actual theme has been browser-verified.

## Frozen scope

- `article.md`: `cfcb9ee4eb579cc9f3d99947b60cddc1c15d5bbedac80135a5db34ac7ab797c8`
- `d10-integration.zip`: `8fc53c283bba0c8287c61c043fbaa3263df5700f0dd2daf13aca9845230f0ff0`
- `d10-moving-average-article.zip`: `f0e7c3c58ee5fdf11cb51058c156f0fbb9760a4592a315549808f95982a57e17`
- `d10-moving-average-images.zip`: `6428e98c7f7d08bada7436a54803b2b72f1793e8e967a9fe049524f282a53856`
- `d10-moving-average-practice.zip`: `53f2692e0f934d7717ceb2d02b3433a53e1f7eeca04c661445f530adf9b4c949`

I independently read all 215 article lines and reopened all five originals, all five 320 px previews, and all five 390 px previews, at native preview size. I did not rely on the author's render report to decide visual readability. I did not edit any frozen candidate file or upload/deploy anything.

## R1 closure

### R1-EV-01 — CLOSED

Figure 02 now says “D9已公开原测试汇总；D10不再评分” and labels days 141–180 “D10不评分”. This is readable at 320 and 390 px. It agrees with article L124's explicit prior-publication caveat. The diagram no longer calls the original test segment unopened or a new blind test. The 112/28/40 boundaries, 28 daily targets and 24 overlapping five-day windows remain correct.

### R1-EV-02 — CLOSED

The body figures were actually redesigned taller, not merely exported with more pixels. Essential labels, legends, date ticks and protocol notes are clearly larger and readable at native 320/390 px. The mechanism figure's long text is shortened; split annotations are stacked; chart notes are split across lines. No clipping, overlap or missing Chinese glyphs observed in any of the 15 opened images. The charts remain legible in solid/dashed/dotted/dash-dot styles without relying on color. Naturally near-coincident MA7/MA14 paths in the 禾味 chart cannot show precise numerical differences at phone width, but the article tables provide the exact values and the prose does not require extracting those differences from pixels.

The cover remains exactly 900×383. Its headline/mechanism is legible at both widths; small peripheral cover labels are supplementary rather than the only location of essential protocol information. Independent all-pixel checks confirm R=G=B for every original and both preview sets.

### R1-EV-03 — CLOSED

Article L59 now describes the visible alignment and synthetic step-response panels, not an unshown centered-window panel. The centered-window limitation remains correctly explained in L55/L69.

## Editorial and unit checks

- Article L122 and result table headers L130/L157 now consistently use kg/day or pieces/day for daily MAE and kg or pieces for the five-day cumulative metric. Chart y-axes use kg/day and pieces/day. Per-day example quantities stated as “公斤” or “件” refer to a specific day's amount; this is not a conflicting metric definition.
- Fixed-origin h=1…5 is a constant mean; no recursive feedback or within-horizon observation updating is implied (L36–47). Figure captions and plot notes explicitly distinguish rolling h=1 charts from fixed-origin five-step forecasts.
- L106–113 uses 28 daily targets and 24 fully-contained overlapping five-day windows, and denies independence of overlapping windows. L115–122 uses the absolute error of totals, not a sum/mean of daily absolute errors masquerading as cumulative error.
- Both simulated cases remain substantial: fictional 禾味 A/SKU01, stable weekly pattern, hand calculation and concrete PM implications; anonymous apparel terminal orders, known simulated 90-piece activity increment, post-event window lag, five-day versus daily ranking conflict and decision relevance.
- No real apparel brand, actual business-outcome claim, production-system connection or replacement 365-day dataset occurs in the article or displayed figures.
- D9 reuse, original 180 days and 112/28/40 division, first 140 development rows and original byte hashes remain explicit. Prior-public test exposure is not concealed. No post-hoc universal winning method is declared.
- The two key comparisons remain unchanged: 禾味 MA7 daily 5.3214 versus seasonal 1.7857; apparel MA14 five-day total 109.4524 versus seasonal 115.8750, but daily 30.2143 versus 21.1071. Numerical reproduction is additionally the separate mathematical reviewer’s gate, not replaced by this editorial check.
- Invalid history, missing versus zero demand, insufficient history, event information available at origin and limitations are still explained rather than reduced to a checklist.

## Links and exact package-content checks

- All five relative figure links resolve to integration members under the article bundle. The article bytes and all five original PNG bytes exactly match their integration members.
- All three D10 download links map to existing integration `static/downloads/` members. Their bytes exactly match the separately reviewed public ZIPs.
- Public article ZIP's `article.md` exactly matches the frozen candidate. Every original and mobile PNG in both public article/image ZIPs exactly matches the files visually inspected here.
- All four ZIP CRC tests pass. Public manifests independently verified: image package root 25/25 and figure manifest 21/21; article root 26/26 and figure manifest 21/21; practice archive manifest 18/18 and practice manifest 17/17.
- R1 live verification of all four unchanged primary-reference URLs is still applicable: [FPP3 §3.3](https://otexts.com/fpp3/decomposition.html#moving-averages), [FPP3 chapter 5 §5.2 and §5.10](https://otexts.com/fpp3/toolbox.html), [pandas rolling](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.rolling.html), and [pandas shift](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.shift.html). Their scope remains accurately described; §5.2 is not falsely presented as teaching trailing moving-average forecasts.
- Existing D9 URLs agree with the downloaded source HTML's canonical `https://12lab.cn/blog/seasonal-naive-demand-forecast/` and the known D9 source archive. A fresh web-tool open of the D9 page and archive was inaccessible in this session, so I cannot certify their current HTTP status; that is not evidence of a 404. Existing-site/D10-download HTTP checks remain part of the integration/deployment gate.

## Honest R1 audit timing note

R1's complete article read and initial hash at 01:38 UTC were of `b5150127206bb532d91cbf391aaf0ff8737e28c34294d78c7bce7d19b379a47c`. Author fixes landed before my 01:40 filesystem copy: the retained `r1/article.md` and R1 report hash block therefore show `a7f517e39f2cf3800671dc5088c10d3c6ea0f630f4870132d886ef0015397e07`, already containing the alt/unit fixes. R1 findings describe the initial read, not an atomic frozen initial capture. This limitation is retained; the original copied snapshot and report have not been silently rewritten.

For comparison only, a **later reconstruction** from the exact recorded alt/unit edits, `/workspace/shared/d10-review-assets/r1/article-reconstructed-later-from-recorded-diff.md`, independently matches the originally observed b515… hash. It is not represented as an original contemporaneous filesystem capture. R2 above checks the actual frozen final bytes directly and closes the findings independently.

## Evidence files and final image hashes

Machine-readable evidence: `/workspace/shared/d10-review-assets/r2/integrity.json` and `archive-manifests.json`. Frozen article copy: `/workspace/shared/d10-review-assets/r2/article.md`.

```text
d79c18ebd5fa8f64774ce0bdf2427005674b3e546ff36c56cb01f2cc6e8a0223  images/d10-00_cover.png
c6d6e218a2abeead1a80ef5e8b9b05834fb5f1e4b6bfa98e723006bd412e4deb  images/d10-01_alignment.png
f3a4cf9ff5b1078ad907495a85798f3d743ed54721f07b640cf23702982d2d0a  images/d10-02_split.png
23f4d636e39c439a502fc95bfea148ad291d71c383d323109951390138bc3406  images/d10-03_hewei.png
cc3e1d780288f4232ceb3883ff942b2ea73c513e596b149848b7504efcc5f074  images/d10-04_apparel.png
a5990adabb51692ec09c9d57a0c8483b6ac446ed9dd0024ec3f7be1e32f2576a  images/mobile/d10-00_cover.png
93a6557dd66acf3804410207704379232400341a3fc4a48abfed20cba72b5306  images/mobile/d10-01_alignment.png
0b196a4486a0327e1edbfc5a0a4b2ab25827b01c35041842a278801a640cc365  images/mobile/d10-02_split.png
6e5c39f038504f7812d962720a9213feb8e7b0f4ff396726f8a13f2ac61ea707  images/mobile/d10-03_hewei.png
631a2ca4f9620a794450d4655e6cbccfedfbd2f0d42d1a21b6d08e94fdbe6ab6  images/mobile/d10-04_apparel.png
e20a1a3e571d136fd39f5ebe3dbf7fc4213f634d4d1254fd523e74e67825654c  images/mobile-320/d10-00_cover.png
5e1020f5a804808529e376dd4f90affb5d31e510c92285019b63d92af4154ac8  images/mobile-320/d10-01_alignment.png
7ea16c44fc364459cad7177e3de0481a84f06892d1e99cffe7edfc8d6d14bde3  images/mobile-320/d10-02_split.png
3c2d5e865af7b4a12f2c6570d18847e375300e5e9146674fba704396366779b5  images/mobile-320/d10-03_hewei.png
592e6eb89081295dba4c90edea0a39badedd302b9f59cea3e28c08518c90e650  images/mobile-320/d10-04_apparel.png
```

## Remaining integration gate

Run the authorized repository build and inspect the actual site/theme at 320/390 px, including padding-scaled figure widths, tables, code blocks, cover handling, links and downloads. This artifact PASS does not skip that gate or authorize publication outside the parent's user-granted scope. Any material change to this frozen article/PNG content invalidates the corresponding hash-scoped part of this PASS and needs rechecking.
