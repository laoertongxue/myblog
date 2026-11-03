# D10 independent editorial and visual review R1

Reviewed at 2026-11-03 01:39 UTC. Reviewer: independent editorial/visual subagent, not the article or figure author. No author files changed. **Decision: request changes before publication.**

## Candidate and evidence

- Article: `/workspace/shared/d10-work/article.md`, 213 lines; snapshot copied to `/workspace/shared/d10-review-assets/r1/article.md`.
- Inspected all five original PNGs and all five author's 390 px previews by opening the images, not by trusting dimensions or renderer assertions.
- Independently resized originals to 320 px in reviewer-only `/workspace/shared/d10-review-assets/r1-320/` and opened all five at native size. These are QA previews, not changes to the deliverable.
- Independently checked every original pixel has R=G=B. All pass. Cover is exactly 900×383. No missing SC glyphs, overlap or clipping observed in originals.
- This is artifact-level visual review; actual site/theme layout still needs verification after integration.

## Required changes

### R1-EV-01 — P1 — Figure 02 presents previously exposed test data as unopened

**Location:** `images/d10-02_split.png`, right block labeled “未打开 / 第141–180天”; also figure-tools README's “141–180 not opened”. Article L124 correctly discloses that D9 already published test summaries.

**Problem:** The standalone diagram suggests a genuinely untouched holdout even though the same article explicitly says it is not one. Readers may share the figure without its surrounding paragraph. This is a provenance/interpretation issue, not a numerical issue.

**Fix:** Replace “未打开” with wording such as “D10不重读” or “原测试段 / 本篇不重评”; make the D9 previously published status explicit in the figure or a readily readable accompanying note. Preserve the existing L124 disclosure and 112/28/40 boundaries. Do not relabel it as a fresh blind test.

**Recheck:** Open the revised original plus native 320/390 px previews. Search article and all distributed figure/package prose for unopened/unseen claims.

### R1-EV-02 — P1 — Body figures miss actual small-screen readability target

**Location:** `images/d10-01_alignment.png` through `images/d10-04_apparel.png`; clearest failures are 320 px chart axis labels, legends and bottom protocol notes in Figures 03/04, and lower annotations in Figures 01/02.

**Problem:** The desktop minimum of 30–34 px on a 1200 px original becomes approximately 8.0–9.1 px at 320 px and 9.8–11.1 px at 390 px. Actual native-size inspection confirms the smallest annotations require strain/zoom rather than ordinary reading. The 390 px outputs are clean but borderline; no author-produced 320 px gate existed. “No clipping” is not sufficient evidence of readability. On Figure 03 the closely overlapping MA7/MA14 traces also become hard to separate, so the prose must not require reading exact values from this plot.

**Fix:** Redesign rather than only enlarge source dimensions. Increase essential labels/legends/notes to roughly 45–52 px at 1200 px width (12–14 px at 320 px), shorten/wrap notes, reduce x-axis tick density, and stack dense elements where useful. Body plots may be taller. Keep key protocol and simulation disclaimers legible; place any removed explanatory text in a proper caption. Preserve clear dash/dot patterns, grayscale, accurate data and cover geometry. The cover headline is legible at 320; its tiny peripheral labels should not carry unique substantive content.

**Recheck:** Generate both actual 320 and 390 px previews, inspect each at native size, and record the revised hashes. Also check the eventual theme's narrower content width/padding does not further shrink figures beyond that test.

## Non-blocking editorial refinement

### R1-EV-03 — P3 — Alternative text describes content absent from Figure 01

**Location:** article L59.

The alt text says “居中平均会使用未来观测”, but the image depicts trailing smoothing versus next-day alignment plus a step-response example, not an actual centered-window diagram. The statement is true and explained in L55; revise this alt text to describe the visible step-response/lag panel instead, so alternative text faithfully substitutes for the image. This does not affect mathematical correctness.

## Checks that passed

- Body is a full explanatory article, not a checklist: definitions, aligned pandas example, assumptions, window-lag trade-off, seasonality, invalid history, independent tests and concrete PM consequences are developed.
- Both simulated cases are substantive. 禾味 is explicitly fictional (L26), one A-store/SKU01 kg/day series is distinguished from the broader 2-store/8-SKU setting, and apparel is anonymous terminal-order demand rather than factory output (L26, L147).
- No real apparel brand name, real project claim, production connection or revenue claim appears in the reviewed article/figures. No invented replacement 365-day dataset appears.
- D9 data reuse and bytewise hashing, 180 total days, 112/28/40 split and 140 development rows are explicit (L28).
- Fixed-origin future five days repeat a single mean (L36–47); rolling one-day forecasts and five-day forecasts remain distinct (L104–109). Figures 03/04 explicitly describe daily rolling h=1, not a five-day path.
- L113 names the 24 overlapping windows and rejects independence claims. L115–122 distinguishes daily MAE and five-day total MAE, including cancellation.
- L124 honestly discloses D9's prior public test summaries and rejects a new untouched holdout claim. This is why Figure 02 needs alignment, not removal of the caveat.
- Numerical tables and narrative match the independent mathematical review communicated by the parent: 禾味 MA7 daily 5.3214 versus seasonal 1.7857; apparel MA14 five-day total 109.4524 versus seasonal 115.8750, but daily 30.2143 versus 21.1071. No post-hoc universal winner or statistically established superiority is claimed.
- Apparel examples connect activity lag to PM decisions, explain 90/k contribution and the 14-day exit, and explicitly reject real marketing-effect interpretations (L149–168).
- Invalid/short history, real zero versus missing, no automatic event deletion and record versioning are explained (L172–180).

## Primary source verification

Opened the actual live primary pages on 2026-11-03 and inspected the relevant passages:

- [FPP3 chapter 3, §3.3 Moving averages](https://otexts.com/fpp3/decomposition.html#moving-averages): directly contains the centered smoothing definition and trend-cycle discussion. Article L69/L208 correctly distinguishes it from this tutorial's trailing forecast rule.
- [FPP3 chapter 5](https://otexts.com/fpp3/toolbox.html): §5.2 contains seasonal naive; §5.10 contains rolling-origin evaluation and prior-only training information. Article L209 does not falsely attribute the trailing moving-average forecast to §5.2. Optional usability improvement: use direct anchors to the two sections.
- [pandas rolling](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.rolling.html): integer windows, min_periods, right-edge versus centered labels and equal weights support L61–69.
- [pandas shift](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.shift.html): parameter behavior and worked examples support the no-freq next-row alignment described at L69.

No large quotations are present. External references support principles/API semantics; simulated results are appropriately attributed to the downloadable experiment rather than outside business evidence.

## Snapshot hashes

```text
a7f517e39f2cf3800671dc5088c10d3c6ea0f630f4870132d886ef0015397e07  /workspace/shared/d10-work/article.md
d79c18ebd5fa8f64774ce0bdf2427005674b3e546ff36c56cb01f2cc6e8a0223  /workspace/shared/d10-work/images/d10-00_cover.png
417c3fe2672968aa883e503038c483f2bdffc73dc86ae83b5ac337e88ad7f106  /workspace/shared/d10-work/images/d10-01_alignment.png
260cec5775134370b5b1fc8000b6ea30ec6c4fed25ef024830b429e6c92fe5ad  /workspace/shared/d10-work/images/d10-02_split.png
5579e98a2a07a0a8387199cab495204c3b1d0c4fc215c9f38d6c3c2f86c53eba  /workspace/shared/d10-work/images/d10-03_hewei.png
1a624af788a7cc5b28cbe9f978de9a7cf53af2a82fe4412d4b4667e8a546554e  /workspace/shared/d10-work/images/d10-04_apparel.png
a5990adabb51692ec09c9d57a0c8483b6ac446ed9dd0024ec3f7be1e32f2576a  /workspace/shared/d10-work/images/mobile/d10-00_cover.png
8db64bf2b43314481325cb93531cacac2a9e56b72432084f7d88b80cd5a0e668  /workspace/shared/d10-work/images/mobile/d10-01_alignment.png
2aaf8335030db71ef58f9cc76047f743ef1e63407eaa204582fbf31770d18289  /workspace/shared/d10-work/images/mobile/d10-02_split.png
a9894dcbe4cabece114ec32048599754b7397c3fdaef70fdf90534c32151565e  /workspace/shared/d10-work/images/mobile/d10-03_hewei.png
02789a55456e1610fc3e9179b5a52125642b99b042ca8fb29142df316f5786fe  /workspace/shared/d10-work/images/mobile/d10-04_apparel.png
```

R2 must review the changed candidate and reopened PNGs after the two P1 fixes; this R1 does not authorize publication.
