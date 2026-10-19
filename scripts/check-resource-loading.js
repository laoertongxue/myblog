// Real network behaviour at 390px / DPR 1. Executed by
// scripts/run-browser-checks.mjs.
//   npm run check:browser -- --only resource-loading
//
// Request assertions are scoped per phase instead of accumulating over the whole
// run, the search query is taken from the generated index instead of a literal,
// and every picture after the first must stay lazy - the runner additionally
// fails the check on any pageerror or non-aborted requestfailed.
async (page, ctx) => {
  const { base, assert } = ctx;
  const context = await page.context().browser().newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 1 });
  const tab = await context.newPage();
  let requests = [];
  tab.on('request', request => requests.push(request.url()));
  const report = [];

  for (const path of ['/', '/topics/agent-engineering/01-agent-framework/']) {
    requests = [];
    await tab.goto(base + path);
    const selector = path === '/' ? '.list-thumbnails img' : '.prose img';
    await tab.locator(selector).first().evaluate(image => image.decode());
    const images = await tab.locator(selector).evaluateAll(nodes => nodes.map(image => ({
      width: image.getAttribute('width'),
      height: image.getAttribute('height'),
      src: image.currentSrc,
      srcset: image.srcset,
      loading: image.loading,
      priority: image.fetchPriority,
    })));
    assert(images.length > 0, `${path}: no images matched ${selector}`);
    assert(images[0].loading === 'eager' && images[0].priority === 'high', `${path}: the first image is not prioritized`);
    assert(images[0].src, `${path}: the prioritized first image did not select a candidate`);
    assert(images.slice(1).every(image => image.loading === 'lazy'), `${path}: images after the first must stay lazy`);
    assert(images.every(image => image.width && image.height), `${path}: an image is missing its reserved dimensions`);
    for (const image of images) {
      if (!image.srcset || !image.src) continue;
      const chosen = decodeURIComponent(new URL(image.src).pathname);
      const candidates = image.srcset.split(',').map(candidate => candidate.trim().split(/\s+/)[0]);
      assert(candidates.includes(chosen), `${path}: selected candidate ${chosen} is not in its own srcset`);
    }
    assert(!await tab.locator('script[src*="search"]').count(), `${path}: the search script loaded on an ordinary page`);
    assert(!requests.some(url => url.includes('avatar-wangye')), `${path}: the never-visible avatar was downloaded`);
    assert(!requests.some(url => url.includes('search-index')), `${path}: the search index was fetched before searching`);
    report.push(`${path}: ${images.length} picture(s), first eager/high priority, rest lazy, reserved sizes, no hidden avatar, no search code`);
  }

  requests = [];
  const indexHref = await tab.goto(base + '/search/').then(() => tab.locator('.search-page').getAttribute('data-index'));
  assert(!requests.some(url => url.includes('search-index')), 'the index was fetched for an empty search');
  const index = await (await fetch(base + indexHref)).json();
  assert(index.length > 0, 'the search index is empty');
  const query = index[0].title;
  await tab.locator('#search-query').fill(query);
  await tab.locator('.search-form button').click();
  await tab.locator('.search-result').first().waitFor();
  assert(requests.some(url => /search-index\.[a-f0-9]+\.json/.test(url)), 'the versioned search index was never fetched');
  const titles = await tab.locator('.search-result h2 a').allTextContents();
  assert(titles.includes(query), `searching the indexed title ${JSON.stringify(query)} returned nothing`);
  assert(!requests.some(url => url.includes('avatar-wangye')), 'the search page downloaded the hidden avatar');
  report.push(`Search code only on the search page; the fingerprinted index is fetched on demand and finds ${JSON.stringify(query)}`);

  await context.close();
  return report;
}
