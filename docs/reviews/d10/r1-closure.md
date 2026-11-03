# D10 author response to independent round 1

This is an author repair log, not an independent approval.

- **R1 CSV P2** — `baseline.load_csv` now uses `csv.DictReader(strict=True)` and translates `csv.Error` to `ValueError('malformed CSV syntax: ...')`. A regression checks the exact unclosed `"train` field reported by the reviewer, plus malformed closing text and header quoting. The 25-test suite passes. Numerical outputs are unchanged.
- **R1-EV-01 P1** — Figure 02 now says 'D10不评分' for days 141–180 and explicitly states that D9 already published original test summaries. The article's previously exposed-data caveat is retained. Author reopened the revised 320 px figure and confirmed the disclosure is readable; independent R2 must recheck.
- **R1-EV-02 P1** — All four body figures were redesigned with essential labels at least 46 px at 1200 px width (12.27 px at 320 px), shortened/wrapped notes and taller layouts. Figure author opened all ten native 320/390 px previews; article author reopened all four revised 320 px body previews. No overlap/clipping observed and key information is readable. This is a layout change, not pixel upscaling; independent R2 must recheck. Figure and source hashes are frozen in figure-tools/FIGURE_MANIFEST.sha256.
- **R1-EV-03 P3** — Article image-01 alt text now describes the actual date-alignment and synthetic step/lag illustration; it no longer says the image draws a centered window.

Additional delivery changes: article `draft: false` is the final publication candidate only; no publishing action has occurred. Three final download links are present. Figure script now defaults to adjacent `practice/data`, verifies original development hashes, supports `--data-dir`, and does not require bundling the raw D9 archive. Optional presence of that archive permits a hash check only. Public deliverables never include the original test labels.
