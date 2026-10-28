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
          const available = await row.evaluate(node => node.getBoundingClientRect().width);
          assert(Math.abs(image.rendered[0] - Math.min(available, 540)) <= 1, `${listing} ${route}: single cover must fill its card up to 540px`);
        }
        assert(!await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), `${listing} ${route}: horizontal overflow`);
        await row.screenshot({ path: `output/playwright/thumbnail-fit-${listing === '/' ? 'home' : 'topic'}-${route.split('/').filter(Boolean).pop()}-${width}.png` });
      }
      report.push(`${width}px ${listing}: ${chapters.length} series row(s) show one complete cover each with correct responsive widths and 900:383 frames`);
    }
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
