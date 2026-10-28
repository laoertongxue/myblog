// Lists show one complete 900x383 cover per article throughout
// Blog/Weekly/topics. Executed by scripts/run-browser-checks.mjs.
//   npm run check:browser -- --only thumbnail-fit
//
// Everything else is derived - the previewed pictures, the original they come
// from and every expected size are read out of the build, following the
// documented bundle convention (`<article>/assets/<name>.png` next to
// index.md), so re-exporting or renaming a picture cannot fail this check.
async (page, ctx) => {
  const { base, assert } = ctx;
  const topic = '/topics/agent-engineering/';
  const report = [];

  await page.setViewportSize({ width: 1440, height: 960 });
  await page.goto(base + topic);
  const chapters = await page.locator('.post-row h2 a').evaluateAll(nodes => nodes.map(node => node.getAttribute('href')));
  assert(chapters.length > 0, `${topic}: no chapters to inspect`);

  for (const width of [1440, 390, 320]) {
    await page.setViewportSize({ width, height: 960 });
    for (const listing of ['/', topic]) {
      await page.goto(base + listing);
      for (const route of chapters) {
        const row = page.locator(`.post-row:has(h2 a[href="${route}"])`);
        const group = row.locator('.list-thumbnails');
        assert(await group.count() === 1, `${listing} ${route}: no thumbnail group`);
        assert(await group.getAttribute('data-fit') === 'contain', `${listing} ${route}: the series must keep complete previews`);
        assert(await group.locator('img').count() === 1, `${listing} ${route}: expected exactly one cover`);
        const images = await group.locator('img').evaluateAll(async nodes => {
          nodes.forEach(node => node.loading = 'eager');
          await Promise.all(nodes.map(node => node.decode()));
          const load = async url => { const image = new Image(); image.src = url; await image.decode(); return { width: image.naturalWidth, height: image.naturalHeight }; };
          return Promise.all(nodes.map(async node => {
            const variants = [];
            for (const candidate of node.srcset.split(',')) {
              const [url, descriptor] = candidate.trim().split(/\s+/);
              variants.push({ url, descriptor: parseInt(descriptor, 10), ...await load(url) });
            }
            const rect = node.getBoundingClientRect();
            return { src: node.currentSrc, original: node.dataset.originalSrc, fit: getComputedStyle(node).objectFit, rendered: [rect.width, rect.height], variants };
          }));
        });
        assert(new Set(images.map(image => image.src)).size === images.length, `${listing} ${route}: duplicate previews`);
        for (const image of images) {
          assert(image.fit === 'contain', `${listing} ${route}: preview ${image.src} is not shown complete`);
          assert(/_hu_[0-9a-f]+\.webp$/.test(new URL(image.src).pathname), `${listing} ${route}: preview is not processed: ${image.src}`);
          const original = new URL(image.original, base).href;
          const originalSize = await page.evaluate(async url => {
            const picture = new Image();
            picture.src = url;
            try { await picture.decode(); } catch { return null; }
            return [picture.naturalWidth, picture.naturalHeight];
          }, original);
          assert(originalSize, `${listing} ${route}: original ${original} is missing`);
          assert(originalSize[0] === 900 && originalSize[1] === 383, `${listing} ${route}: cover source must be 900x383`);
          assert(JSON.stringify(image.variants.map(variant => variant.descriptor)) === JSON.stringify([540, 900]), `${listing} ${route}: cover candidates must be 540px and 900px`);
          const expectedRatio = originalSize[0] / originalSize[1];
          for (const variant of image.variants) {
            assert(variant.width === variant.descriptor, `${listing} ${route}: srcset width ${variant.descriptor} does not match the served ${variant.width}px`);
            assert(Math.abs(variant.height - variant.width / expectedRatio) <= 1, `${listing} ${route}: preview variant ${variant.url} is cropped or distorted`);
          }
          assert(Math.abs(image.rendered[1] - image.rendered[0] * 383 / 900) <= 1, `${listing} ${route}: preview frame must follow 900x383`);
          const available = await group.evaluate(node => {
            const content = node.closest('.row-content');
            if (!content) return 0;
            if (innerWidth > 900) return parseFloat(getComputedStyle(content).gridTemplateColumns);
            return content.getBoundingClientRect().width;
          });
          assert(available > 0 && Math.abs(image.rendered[0] - Math.min(available, 540)) <= 1, `${listing} ${route}: single cover must fill its grid cell up to 540px`);
        }
        assert(!await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), `${listing} ${route}: horizontal overflow`);
        await row.screenshot({ path: `output/playwright/thumbnail-fit-${listing === '/' ? 'home' : 'topic'}-${route.split('/').filter(Boolean).pop()}-${width}.png` });
      }
      report.push(`${width}px ${listing}: ${chapters.length} series row(s) show one complete cover each with correct responsive widths and 900:383 frames`);
    }
  }

  // Term URLs come from the built taxonomy indexes so category/tag names
  // can change without weakening the shared card-layout checks.
  const taxonomyRoutes = [];
  for (const index of ['/tags/', '/categories/']) {
    await page.goto(base + index);
    const first = page.locator('.taxonomy-list a').first();
    if (await first.count()) taxonomyRoutes.push(await first.getAttribute('href'));
  }
  const listingRoutes = [...new Set(['/', '/blog/', '/topics/', topic, ...taxonomyRoutes])];
  for (const width of [1920, 1440, 1024, 768, 390, 320]) {
    await page.setViewportSize({ width, height: 960 });
    let checked = 0;
    for (const listing of listingRoutes) {
      await page.goto(base + listing);
      assert(!await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), `${width}px ${listing}: horizontal overflow`);
      const rows = await page.locator('.post-row').evaluateAll(nodes => nodes.map(row => {
        const rect = node => {
          if (!node) return null;
          const box = node.getBoundingClientRect();
          return { left: box.left, right: box.right, top: box.top, bottom: box.bottom, width: box.width, height: box.height };
        };
        const content = row.querySelector('.row-content');
        const summary = row.querySelector('.row-summary');
        const paragraph = summary?.querySelector('p');
        const paragraphStyle = paragraph && getComputedStyle(paragraph);
        const meta = summary?.querySelector('.row-meta');
        const textRange = document.createRange();
        if (paragraph) textRange.selectNodeContents(paragraph);
        const textBounds = paragraph ? textRange.getBoundingClientRect() : null;
        return {
          href: row.querySelector('h2 a')?.getAttribute('href'),
          dividerRight: row.getBoundingClientRect().right,
          date: rect(row.querySelector('.row-date')),
          title: rect(row.querySelector('.row-body h2')),
          content: rect(content), summary: rect(summary),
          cover: rect(content?.querySelector('.list-thumbnails')),
          coverCount: content?.querySelectorAll('.list-thumbnails img').length || 0,
          description: rect(paragraph),
          paragraph: paragraph ? {
            text: paragraph.textContent.trim(),
            fontSize: parseFloat(paragraphStyle.fontSize), lineHeight: parseFloat(paragraphStyle.lineHeight),
            lineClamp: paragraphStyle.webkitLineClamp, textOverflow: paragraphStyle.textOverflow,
            clipped: paragraph.scrollHeight > paragraph.clientHeight + 1 || paragraph.scrollWidth > paragraph.clientWidth + 1,
            textBottom: textBounds.bottom, textLeft: textBounds.left, textRight: textBounds.right,
          } : null,
          summaryClipped: summary && (summary.scrollHeight > summary.clientHeight + 1 || summary.scrollWidth > summary.clientWidth + 1),
          metaPaddingTop: meta ? parseFloat(getComputedStyle(meta).paddingTop) : 0,
          readMore: rect(summary?.querySelector('.read-more')),
          meta: rect(meta),
          order: content ? [...content.children].map(child => child.className) : [],
        };
      }));
      assert(rows.length > 0, `${width}px ${listing}: no cards to inspect`);
      for (const row of rows) {
        const label = `${width}px ${listing} ${row.href}`;
        assert(row.date && row.title && row.content && row.summary && row.readMore, `${label}: card is missing its date/title/content/summary/read-more structure`);
        assert(row.date.bottom <= row.title.top + 1, `${label}: date must stay above the title`);
        assert(row.title.bottom <= row.content.top + 1, `${label}: title must stay above cover and summary`);
        assert(row.summary.left >= row.content.left - 1 && row.summary.right <= row.content.right + 1, `${label}: summary extends outside its row`);
        assert(Math.abs(row.content.right - row.dividerRight) <= 1 && Math.abs(row.summary.right - row.dividerRight) <= 1, `${label}: content and summary must end at the row divider right edge`);
        assert(!row.summaryClipped, `${label}: summary column clips its contents`);
        if (row.description) {
          assert(row.paragraph.text && row.description.width > 0 && row.description.height > 0, `${label}: rendered summary must be nonempty and visible`);
          assert(!row.paragraph.clipped && !['ellipsis'].includes(row.paragraph.textOverflow) && !Number(row.paragraph.lineClamp), `${label}: summary text must remain complete and unclamped`);
          assert(row.paragraph.textBottom <= row.description.bottom + 1 && row.paragraph.textLeft >= row.description.left - 1 && row.paragraph.textRight <= row.description.right + 1, `${label}: summary glyphs extend outside their paragraph`);
          assert(Math.abs(row.paragraph.lineHeight / row.paragraph.fontSize - 1.7) <= 0.01, `${label}: summary line height must keep the compact reading rhythm`);
          assert(Math.abs(row.description.left - row.summary.left) <= 1 && Math.abs(row.description.width - row.summary.width) <= 1 && Math.abs(row.description.right - row.summary.right) <= 1, `${label}: summary paragraph must fill the right column without an extra width limit`);
          assert(row.description.bottom <= row.readMore.top + 1, `${label}: read-more must follow the complete summary`);
        }
        if (row.meta) {
          assert(row.readMore.bottom + 13 <= row.meta.top + row.metaPaddingTop, `${label}: reading metadata needs a visible gap after read-more`);
          assert(Math.abs(row.meta.bottom - row.summary.bottom) <= 1, `${label}: reading metadata must finish at the bottom of the summary column`);
          if (width <= 900) assert(row.meta.top + row.metaPaddingTop - row.readMore.bottom <= 18, `${label}: stacked summary must not add artificial filler above metadata`);
        }
        if (row.cover) {
          assert(row.coverCount === 1 && row.order.length === 2 && row.order[0] === 'list-thumbnails' && row.order[1] === 'row-summary', `${label}: a card must contain one cover followed by one summary`);
          assert(Math.abs(row.cover.height - row.cover.width * 383 / 900) <= 1, `${label}: cover frame must keep 900:383`);
          const expectedWidth = Math.min(width > 900 ? row.content.width * 0.46 : row.content.width, 540);
          assert(Math.abs(row.cover.width - expectedWidth) <= 1, `${label}: cover width must follow its available grid column`);
          if (width > 900) {
            assert(Math.abs(row.cover.left - row.content.left) <= 1 && row.cover.right < row.summary.left, `${label}: cover must sit left of the summary`);
            assert(Math.abs(row.cover.top - row.summary.top) <= 1 && Math.abs(row.cover.top - row.content.top) <= 1, `${label}: cover and summary must align at the top`);
            assert(Math.abs(row.summary.right - row.content.right) <= 1, `${label}: summary must use the right column`);
            assert(row.summary.height >= row.cover.height - 1, `${label}: desktop summary column must stretch to at least the cover height`);
            assert(Math.abs(row.content.height - Math.max(row.cover.height, row.summary.height)) <= 1, `${label}: side-by-side card has unnecessary vertical space`);
          } else {
            const gap = row.summary.top - row.cover.bottom;
            assert(gap >= 0 && gap <= 24, `${label}: narrow card must stack summary closely below its cover`);
            assert(Math.abs(row.cover.left - row.content.left) <= 1 && Math.abs(row.summary.left - row.content.left) <= 1, `${label}: stacked cover and summary must align with the column`);
            assert(Math.abs(row.summary.width - row.content.width) <= 1, `${label}: stacked summary must use the full column width`);
          }
        } else {
          assert(row.order.length === 1 && row.order[0] === 'row-summary' && Math.abs(row.summary.width - row.content.width) <= 1, `${label}: a coverless card must use the full row`);
        }
        checked++;
      }
    }
    report.push(`${width}px: ${checked} home/blog/topic/taxonomy cards keep date/title above, cover ${width > 900 ? 'left of' : 'above'} summary, full unclamped summaries, bottom-aligned metadata and no overflow`);
  }

  for (const listing of ['/', '/blog/', '/weekly/', '/topics/agent-engineering/']) {
    await page.goto(base + listing);
    assert(await page.locator('.list-thumbnails:not([data-fit=contain])').count() === 0, `${listing}: every preview must keep its complete image`);
    for (const group of await page.locator('.list-thumbnails').all()) {
      assert(await group.locator('img').count() === 1, `${listing}: every article must show only one cover`);
    }
    const images = page.locator('.list-thumbnails img');
    if (await images.count() === 0) continue;
    assert(await images.first().evaluate(node => getComputedStyle(node).objectFit) === 'contain', `${listing}: default thumbnails must scale without cropping`);
    // All candidates must agree with the served image's intrinsic size.
    // Body pictures keep their own proportions; only the selected cover is
    // constrained to 900x383 and shown here.
    const sourceSize = await images.first().evaluate(node => [Number(node.getAttribute('width')), Number(node.getAttribute('height'))]);
    const variants = await images.first().evaluate(async node => {
      const load = async url => { const picture = new Image(); picture.src = url; await picture.decode(); return [picture.naturalWidth, picture.naturalHeight]; };
      const out = [];
      for (const candidate of node.srcset.split(',')) {
        const [url, descriptor] = candidate.trim().split(/\s+/);
        out.push({ descriptor: parseInt(descriptor, 10), size: await load(url) });
      }
      return out;
    });
    for (const variant of variants) {
      assert(variant.size[0] === variant.descriptor, `${listing}: srcset width ${variant.descriptor} does not match the served ${variant.size[0]}px`);
      assert(Math.abs(variant.size[1] - variant.size[0] * sourceSize[1] / sourceSize[0]) <= 1, `${listing}: thumbnail was cropped or distorted: ${variant.size.join('x')}`);
    }
    const frame = await images.first().boundingBox();
    assert(frame.width > 0 && Math.abs(frame.height - frame.width * 383 / 900) <= 1, `${listing}: thumbnail frame must follow 900x383`);
  }
  report.push('Blog/Weekly/topic rows show one 900:383 cover; body-picture dimensions remain independent');
  return report;
}
