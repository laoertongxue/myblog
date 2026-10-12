// List thumbnails: "contain" previews for the series, default square crop for
// Blog/Weekly. Executed by scripts/run-browser-checks.mjs.
//   npm run check:browser -- --only thumbnail-fit
//
// Content expectation kept here: the series declares `thumbnailFit: contain`.
// Everything else is derived - the previewed pictures, the original they come
// from and every expected size are read out of the build, following the
// documented bundle convention (`<article>/assets/<name>.png` next to
// index.md), so re-exporting or renaming a picture cannot fail this check.
async (page, ctx) => {
  const { base, assert } = ctx;
  const topic = '/topics/agent-engineering/';
  const report = [];

  const originalOf = (route, src) => {
    const file = decodeURIComponent(new URL(src).pathname.split('/').pop());
    return route + 'assets/' + file.replace(/_hu_[0-9a-f]+\.webp$/, '.png');
  };

  await page.setViewportSize({ width: 1440, height: 960 });
  await page.goto(base + topic);
  const chapters = await page.locator('.post-row h2 a').evaluateAll(nodes => nodes.map(node => node.getAttribute('href')));
  assert(chapters.length > 0, `${topic}: no chapters to inspect`);
  const bodyCounts = {};
  for (const route of chapters) {
    await page.goto(base + route);
    bodyCounts[route] = await page.locator('.prose img').count();
  }

  for (const width of [1440, 390, 320]) {
    await page.setViewportSize({ width, height: 960 });
    for (const listing of ['/', topic]) {
      await page.goto(base + listing);
      for (const route of chapters) {
        const row = page.locator(`.post-row:has(h2 a[href="${route}"])`);
        const group = row.locator('.list-thumbnails');
        assert(await group.count() === 1, `${listing} ${route}: no thumbnail group`);
        assert(await group.getAttribute('data-fit') === 'contain', `${listing} ${route}: the series must keep complete previews (thumbnailFit: contain)`);
        const expected = Math.min(3, bodyCounts[route]);
        assert(await group.locator('img').count() === expected, `${listing} ${route}: expected ${expected} preview(s)`);
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
            return { src: node.currentSrc, fit: getComputedStyle(node).objectFit, rendered: [rect.width, rect.height], variants };
          }));
        });
        assert(new Set(images.map(image => image.src)).size === images.length, `${listing} ${route}: duplicate previews`);
        for (const image of images) {
          assert(image.fit === 'contain', `${listing} ${route}: preview ${image.src} is not shown complete`);
          assert(/_hu_[0-9a-f]+\.webp$/.test(new URL(image.src).pathname), `${listing} ${route}: preview is not processed: ${image.src}`);
          const original = originalOf(route, image.src);
          const originalSize = await page.evaluate(async url => {
            const picture = new Image();
            picture.src = url;
            try { await picture.decode(); } catch { return null; }
            return [picture.naturalWidth, picture.naturalHeight];
          }, original);
          assert(originalSize, `${listing} ${route}: original ${original} is missing`);
          const expectedRatio = originalSize[0] / originalSize[1];
          for (const variant of image.variants) {
            assert(variant.width === variant.descriptor, `${listing} ${route}: srcset width ${variant.descriptor} does not match the served ${variant.width}px`);
            assert(Math.abs(variant.height - variant.width / expectedRatio) <= 1, `${listing} ${route}: preview variant ${variant.url} is cropped or distorted`);
          }
          assert(Math.abs(image.rendered[0] - image.rendered[1]) <= 1, `${listing} ${route}: the square preview frame changed`);
        }
        assert(!await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), `${listing} ${route}: horizontal overflow`);
        await row.screenshot({ path: `output/playwright/thumbnail-fit-${listing === '/' ? 'home' : 'topic'}-${route.split('/').filter(Boolean).pop()}-${width}.png` });
      }
      report.push(`${width}px ${listing}: ${chapters.length} series row(s) show complete source-proportion previews with correct widths and square frames`);
    }
  }

  for (const listing of ['/blog/', '/weekly/']) {
    await page.goto(base + listing);
    assert(await page.locator('.list-thumbnails[data-fit=contain]').count() === 0, `${listing}: default crop mode must stay unchanged`);
    const images = page.locator('.list-thumbnails img');
    assert(await images.count() > 0, `${listing}: no thumbnails to inspect`);
    assert(await images.first().evaluate(node => getComputedStyle(node).objectFit) === 'cover', `${listing}: default thumbnails are no longer cropped to cover`);
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
      assert(variant.size[0] === variant.size[1], `${listing}: default thumbnails must stay square, got ${variant.size.join('x')}`);
    }
    const reserved = await images.first().evaluate(node => [Number(node.getAttribute('width')), Number(node.getAttribute('height'))]);
    assert(reserved[0] === reserved[1] && reserved[0] > 0, `${listing}: default thumbnail box must stay square, got ${reserved.join('x')}`);
  }
  report.push('Default Blog/Weekly square crop retained');
  return report;
}
