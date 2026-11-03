# D10 R2 editorial supplement

2026-11-03 01:59 UTC. **PASS within the changed presentation/citation/package scope.** This supplements, rather than replaces, the original R2 image/content review. No candidate files were edited. Actual local-theme browser validation is still required.

## Exact candidate

- Article SHA-256: `35ec4b447988aae680d85fd5ea81ce777cbc746a1b3260871f4871ff1a22a978`
- Integration ZIP SHA-256: `23eaa335ec65779a5192c8516754a5d6171213dfcbf565d6204dba14a5686947`
- Article public ZIP SHA-256: `ffdb1f4a043a7212f39138d94472c251c1d9a94beb7b667f214c97923c37520d`
- Prior full R2 article baseline: `cfcb9ee4eb579cc9f3d99947b60cddc1c15d5bbedac80135a5db34ac7ab797c8`

## Independent checks

I read the complete actual diff from the saved full-R2 baseline, plus `review/mobile-table-delta.json` and `review/mobile-table-closure.md`. I independently parsed and compared the tables instead of relying on the author's 42-cell assertion.

1. **Exactly 42 original header/data cell strings survive, in the same order, across exactly three tables.** Every number, decimal precision, unit and k label is unchanged. No numerical result, formula or comparison claim was changed.
2. **HTML is balanced and structurally sound.** Each real table has `thead` and `tbody`; column headers retain `scope="col"`. All 42 cells enforce `white-space:nowrap`. Each overflow container is bounded to 100% width, explicitly uses horizontal scrolling, has `role="region"`, `tabindex="0"`, and a distinct descriptive `aria-label`. The tables have a 560 px minimum width, so the intended behavior is scrolling rather than shrinking/wrapping decimals. One visible scroll instruction precedes the first table. No script, form, unclosed element or unrelated HTML insertion was found.
3. **References are relocated, not substantively lost.** The D9 article link remains, the source archive link now accompanies the D9 data statement, and existing inline FPP3 moving-average and pandas links remain. The generic final FPP3 chapter-5 link is replaced by more precise inline links to [seasonal naive](https://otexts.com/fpp3/toolbox.html#seasonal-na%C3%AFve-method) and [time-series cross-validation](https://otexts.com/fpp3/toolbox.html#time-series-cross-validation), beside their corresponding claims. Both URLs were opened successfully in this supplement. The source content remains the same primary material verified in R1. No claim now misattributes trailing moving-average prediction to FPP3 §5.2.
4. **Removing the separate reference footer does not remove the core caveats.** The article still distinguishes centered smoothing from trailing prediction, identifies both cases as simulated, rejects real business-effect claims, explains prior D9 test exposure and uses validation-only reporting. The removed footer's document-check date and redundant teaching-design disclaimer are not necessary to understand those retained qualifications.
5. **Frozen asset/package consistency passes.** All five main PNG hashes are unchanged from full R2. Practice and image ZIPs remain byte-identical (`53f2692e…` and `6428e98c…`, respectively). The current integration article/PNGs/three public ZIPs all match their local candidate bytes. The public article ZIP's article exactly matches this supplement's article; its CRC test passes and all 26 root-manifest entries verify.

Evidence and contemporaneous article copy are in `/workspace/shared/d10-review-assets/r2-supplement/independent-delta.json` and `article.md`.

## Still required before publication

The local owner must verify the actual Hugo/theme renders raw HTML, that no overriding stylesheet reintroduces wrapping or page-wide overflow, and that all three tables are usable at 320 and 390 px, including horizontal keyboard/touch scrolling. Check the complete rightmost numeric column after scrolling, visible focus, and the final page width. This source-level supplement does not claim those browser checks have already happened or that deployment occurred.

No further editorial change is requested within this bounded delta.
