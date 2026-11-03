# D10 frozen candidate integration

Slug: `moving-average-demand-forecast`. Article date: `2026-11-03T09:00:00+08:00`.

- Overlay these repository-relative files only after both independent review rounds pass.
- `content/blog/moving-average-demand-forecast/index.md` intentionally uses final `draft: false`; copying is not authorization to push before final gates.
- The first body image and only frontmatter image are `images/d10-00_cover.png` (900 x 383).
- `static/downloads/` contains the three article-linked archives.
- `experiments/d10-moving-average/` preserves standard-library practice and figure-authoring source. Figure re-rendering requires Pillow, fontTools, and Noto Sans CJK SC; use that directory's figure-tools README. Its default data path is the adjacent practice/data directory.
- No raw D9 ZIP, last-40-day labels, source reference tree, caches, or unrelated changes are included.
- Add final independent R2 records here after the frozen package is reviewed. Do not modify reviewed source or PNGs silently; any material change requires rechecking its hash and affected gate.
- Native Hugo extended must match the current deploy workflow. Run required build/browser gates and inspect 320/390 px actual theme rendering before authorized main push.
- No cover SVG exists; the cover is rendered from the reproducible Python diagram source, so no SVG belongs in the article bundle.

This file is a packaging note, not a statement that reviews or deployment have passed.
