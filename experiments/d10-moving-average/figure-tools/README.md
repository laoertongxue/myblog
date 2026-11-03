# D10 figures — reproducible authoring assets

From the unpacked package root (the directory containing `figure-tools/`, `practice/`, and `images/`):

```bash
python figure-tools/render_figures.py
```

The default inputs are `practice/data/hewei-development.csv` and `practice/data/apparel-development.csv`. To use another folder containing the exact same two development files:

```bash
python figure-tools/render_figures.py --data-dir ./path/to/development-data
```

The script resolves output locations from its own file location, so it can also be called by an absolute path from another working directory. It creates missing image directories. The package needs only the two unchanged development CSVs: **do not bundle the original D9 ZIP or any sealed/test labels**.

Dependencies: Python 3.9+, Pillow, fontTools, and a locally installed **Simplified-Chinese Noto sans font**. No font is bundled. The default is `/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc`, collection face **2**, `Noto Sans CJK SC`. For macOS or another font location:

```bash
python figure-tools/render_figures.py --font-path /path/to/NotoSansCJK-Regular.ttc --font-face 2
# For a standalone SC OTF/TTF rather than a TTC collection:
python figure-tools/render_figures.py --font-path /path/to/NotoSansCJKsc-Regular.otf --font-face 0
```

The script rejects a non-SC family; it accepts `Noto Sans CJK SC` / `Noto Sans SC` and checks coverage of every rendered character. Do not select the JP/KR/TC/HK face. Reproduction with another font version may change PNG bytes even when the layout/data remain correct. No image-generation model is used.

## Deliverables

| File | Geometry | Content |
|---|---:|---|
| `images/d10-00_cover.png` | 900×383 | Mechanism schematic: known recent history yields one mean repeated for five future targets at a fixed origin. |
| `images/d10-01_alignment.png` | 1200×1680 | History 10/20/30, trailing smoothing at day 3 versus forecast aligned to day 4; toy step-response illustration. |
| `images/d10-02_split.png` | 1200×1620 | Train 1–112; validation 113–140; 141–180 not scored by D10; D9 had already published its original test summary. 28 daily targets and 24 overlapping, fully contained five-day windows. |
| `images/d10-03_hewei.png` | 1200×1370 | Fictional Hewei A/SKU01 simulated demand (kg/day), validation days 113–140, actual and daily rolling one-step MA3/7/14. |
| `images/d10-04_apparel.png` | 1200×1370 | Anonymous apparel simulated terminal-order demand (pieces/day), same validation protocol. |

`images/mobile/` contains 390 px-wide previews; `images/mobile-320/` contains 320 px-wide previews of all five images. `render-quality-report.json` records exact geometry, bounding boxes, font/glyph checks, every-pixel RGB equality, hashes, the source boundary, and matching against the independently generated practice predictions. `plotted-curves.json` preserves all 28 plotted daily actuals and predictions per case. `mobile-review.json` records authoring visual inspection, not an adversarial review. The report includes that review only while every preview hash still matches it.

## Data provenance and boundary

The renderer reads only the configured `hewei-development.csv` and `apparel-development.csv` (140 rows each), defaulting to `practice/data/`. Both file hashes must exactly match the fixed original development hashes below. It never reads `sealed/` or `results/test.json`. The original archive is **not required**. If `source/d9-seasonal-naive-practice.zip` happens to exist, its bytes are hashed without extracting or reading any sealed member, and a mismatched archive is rejected. If absent, the report records `archive_not_bundled_declared_hash_only` and leaves the verified hash null, rather than implying a fresh archive verification. The fixed declared source archive SHA-256 is `0063b6ddae7459eff9dc7779c0a0a6c9ecef8d0bd48320c653eae1c072ce1c31`.

- Hewei CSV SHA-256: `292072a63439529f22a73d41b83516928ae5a5b474b907b33d42e74962c23407`
- Apparel CSV SHA-256: `56badd2fc37decd72b2f55a980acb7add2594b96c7b8d269f6aaae59ee7d47e5`

Charts independently calculate `mean(y[d-k:d])` for the next target day `d+1`, using one-based human dates and only previously known observations. The displayed targets are days 113–140, origins 112–139. Every plotted MA point and actual is checked against `practice/results/daily_predictions.csv` if that file exists (168 MA rows). The result charts do **not** plot five-day forecasts or totals. Styles: actual black solid, MA3 dashed, MA7 dotted, MA14 dash-dot. No data smoothing, point sampling, normalized units, or empirical business benefit is asserted.

The step illustration uses a toy level of 10 followed by 30, with prehistory equal to 10. MA3 and MA7 there are rolling one-step forecasts; its only purpose is to explain the response mechanism, not choose a window or claim validation superiority. Both demand cases are teaching simulations, not observations from real businesses. The apparel promotion is an artificial simulation input, not a measured marketing effect.

## QA

All drawing starts on a grayscale (`L`) canvas at 2×, is antialiased with LANCZOS, and is converted to RGB. Thus all exported PNG pixels have exactly equal R, G, and B values. The script verifies equality across every pixel, verifies SC glyph coverage for every rendered character, checks text bounds and text-to-text overlap, and asserts the cover/body dimensions. All essential body text is at least 46 px at 1200 px source width (12.27 px at 320 px display width). Only non-essential kicker labels and the not-to-scale note are smaller. The cover is the exact requested size, unchanged, and has smaller subsidiary labels. All ten 320/390 px previews were visually inspected for clipping, overlap, and legible line-style separation. These are authoring checks, not adversarial review approval.

No upload, push, publication, or old-repository modification is performed by these tools.

## Portable-package verification and freeze

`portability-check.json` records a clean-directory run with only the renderer and the two development CSVs, without `source/` or the original ZIP. The default path, explicit data/font arguments, and rejection of a changed CSV were tested. All 15 exported PNGs (five full-size plus both preview widths) were byte-identical in that clean run. `FIGURE_MANIFEST.sha256` freezes the renderer, this README, reports, plotted values, and all PNGs. The R1 layout is frozen for independent R2 review; this statement does not claim R2 approval.
