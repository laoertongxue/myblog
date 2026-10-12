// Run with playwright-cli run-code against make check output on port 1316.
async (page) => {
  const base = 'http://127.0.0.1:1316';
  const topic = '/topics/agent-engineering/';
  const articles = [
    {route: topic + '01-agent-framework/', images: ['00-agent-framework', '01-agent-overview', '02-context-engineering'], sizes: [[1697,927],[1698,926],[1536,1024]], body: 11},
    {route: topic + '02-harness/', images: ['00-cover', '01-architecture', '02-loop'], sizes: [[1586,992],[1600,1000],[1600,1000]], body: 5}
  ];
  const report = [];
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  for (const width of [1440,390,320]) {
    await page.setViewportSize({width, height:960});
    for (const listing of ['/',topic]) {
      await page.goto(base + listing);
      for (const article of articles) {
        const row = page.locator(`.post-row:has(h2 a[href="${article.route}"])`);
        const group = row.locator('.list-thumbnails');
        if (await group.getAttribute('data-fit') !== 'contain' || await group.locator('img').count() !== 3) throw Error('Three complete preview configuration missing');
        const images = await group.locator('img').evaluateAll(async nodes => {
          nodes.forEach(node => node.loading = 'eager');
          await Promise.all(nodes.map(node => node.decode()));
          const load = async url => { const image = new Image(); image.src = url; await image.decode(); return {width:image.naturalWidth,height:image.naturalHeight}; };
          return Promise.all(nodes.map(async node => {
            const variants = [];
            for (const candidate of node.srcset.split(',')) {
              const [url, descriptor] = candidate.trim().split(/\s+/);
              variants.push({url, descriptor:parseInt(descriptor), ...await load(url)});
            }
            const rect = node.getBoundingClientRect();
            return {src:node.currentSrc, fit:getComputedStyle(node).objectFit, rendered:[rect.width,rect.height], variants};
          }));
        });
        for (const [index,image] of images.entries()) {
          if (image.fit !== 'contain' || !image.src.includes(article.images[index] + '_hu_')) throw Error('Preview mode or selection wrong');
          const [sourceWidth,sourceHeight] = article.sizes[index];
          for (const variant of image.variants) {
            if (variant.width !== variant.descriptor || Math.abs(variant.height - variant.width * sourceHeight / sourceWidth) > 1) throw Error('Cropped or distorted thumbnail, or incorrect srcset width');
          }
          if (Math.abs(image.rendered[0] - image.rendered[1]) > 1) throw Error('Existing square frame changed');
        }
        if (await page.evaluate(() => document.documentElement.scrollWidth > innerWidth)) throw Error('Horizontal overflow');
        await row.screenshot({path:`output/playwright/thumbnail-fit-${listing==='/'?'home':'topic'}-${article.body===11?'agent':'harness'}-${width}.png`});
        await group.locator('a').last().click();
        await page.waitForURL(base + article.route);
        if (await page.locator('.prose img').count() !== article.body) throw Error('Body pictures changed');
        await page.goBack();
        await page.waitForURL(base + listing);
      }
      report.push(`${width}px ${listing}: both articles show 3 complete source-proportion previews, correct responsive widths, no overflow, links and body counts unchanged`);
    }
  }
  for (const listing of ['/blog/','/weekly/']) {
    await page.goto(base + listing);
    if (await page.locator('.list-thumbnails[data-fit=contain]').count()) throw Error('Default Blog/Weekly presentation changed');
    const image = page.locator('.list-thumbnails img').first();
    if (await image.evaluate(node => getComputedStyle(node).objectFit) !== 'cover') throw Error('Default crop behavior changed');
  }
  if (errors.length) throw Error(errors.join('\n'));
  report.push('Default Blog/Weekly crop behavior retained; no browser errors');
  return report;
}
