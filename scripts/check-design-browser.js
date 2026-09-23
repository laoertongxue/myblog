// Run this function with playwright-cli run-code against make check output on port 1316.
async (page) => {
  const base = 'http://127.0.0.1:1316';
  const report = [];
  const failures = [];
  page.on('pageerror', error => failures.push(error.message));
  const routes = ['/', '/blog/', '/weekly/', '/topics/', '/topics/layout-test/', '/blog/layout-test-01/', '/weekly/003/', '/topics/layout-test/01-chapter/', '/about/', '/now/', '/links/', '/archive/', '/search/'];
  for (const width of [1440, 1920, 768, 390, 320]) {
    await page.setViewportSize({width, height:960});
    for (const path of routes) {
      const response = await page.goto(base + path);
      if(response.status() !== 200) throw Error(`${path}: HTTP ${response.status()}`);
      const state = await page.evaluate(async () => {
        const pictures = [...document.images];
        pictures.forEach(image => image.loading = 'eager');
        await Promise.all(pictures.map(image => image.decode().catch(() => {})));
        return {
          overflow:document.documentElement.scrollWidth > innerWidth,
          badImages:pictures.filter(image => !image.naturalWidth).map(image => image.src),
          oldSidebar:!!document.querySelector('.site-sidebar, .list-aside'),
          background:getComputedStyle(document.body).backgroundColor,
          readingAligned:!document.querySelector('.reading-page') || Math.abs(document.querySelector('.reading-page').getBoundingClientRect().left-document.querySelector('.site-workspace').getBoundingClientRect().left)<1
        };
      });
      if(state.overflow || state.oldSidebar || state.badImages.length || !state.readingAligned || state.background !== 'rgb(250, 248, 241)') throw Error(`${width} ${path}: ${JSON.stringify(state)}`);
    }
    report.push(`${width}px: 13 routes, no overflow, all pictures loaded, single column`);
  }
  for (const width of [1440, 390]) {
    await page.setViewportSize({width,height:960});
    await page.goto(base);
    const links = [];
    let pages = 0;
    do {
      pages++;
      const current = await page.locator('.home-feed .row-body h2 a').evaluateAll(nodes=>nodes.map(n=>n.getAttribute('href')));
      if(current.length > 10) throw Error('More than ten articles');
      links.push(...current);
      if(await page.locator('.feed-pagination [aria-current=page]').textContent() !== String(pages)) throw Error('Wrong active page');
      const next = page.locator('.feed-pagination [rel=next]');
      if(!await next.count()) break;
      if(current.length !== 10) throw Error('Incomplete non-final page');
      await next.click();
    } while(pages < 10);
    if(pages !== 5 || links.length !== 43 || new Set(links).size !== 43) throw Error(`Bad pagination: ${pages} / ${links.length}`);
    if(!await page.locator('.feed-pagination [rel=prev]').count()) throw Error('Missing previous arrow');
    await page.locator('.feed-pagination [rel=prev]').click();
    if(!page.url().endsWith('/page/4/')) throw Error('Previous arrow failed');
    await page.goto(base);
    if(await page.locator('.pagination-gap').count() !== 1) throw Error('Missing ellipsis');
    await page.screenshot({path:`output/playwright/single-column-${width}.png`});
    report.push(`${width}px: five numbered pages, 10+10+10+10+3 unique articles, arrows and ellipsis`);
    await page.goto(base+'/blog/layout-test-01/');
    const toc=page.locator('.floating-toc');
    await toc.locator('summary').click();
    const last=toc.locator('a').last();
    const href=await last.getAttribute('href');
    await last.click();
    await page.waitForFunction(hash=>decodeURIComponent(location.hash)===decodeURIComponent(hash), href);
    await page.waitForFunction(()=>!document.querySelector('.floating-toc').open);
    await page.waitForFunction(hash=>document.querySelector('.toc-panel a[aria-current=location]')?.getAttribute('href')===hash, href);
    await toc.locator('summary').click();
    await page.keyboard.press('Escape');
    if(await toc.getAttribute('open') !== null) throw Error('Escape did not close TOC');
    await toc.locator('summary').click();
    await page.locator('.article-heading h1').click();
    if(await toc.getAttribute('open') !== null) throw Error('Outside click did not close TOC');
    await page.screenshot({path:`output/playwright/single-article-${width}.png`});
    report.push(`${width}px: TOC opens, jumps, highlights, closes on Escape and outside click`);
  }
  for(const path of ['/blog/','/weekly/','/topics/layout-test/']) {
    await page.goto(base+path);
    if(await page.locator('.post-row').count()!==10) throw Error(`${path}: first page count`);
    await page.locator('.feed-pagination [rel=next]').click();
    if(await page.locator('.post-row').count()<2) throw Error(`${path}: missing remaining articles`);
  }
  await page.goto(base+'/search/?q=图文测试');
  await page.waitForFunction(()=>document.querySelectorAll('.search-result').length>0);
  await page.locator('[data-filter=weekly]').click();
  await page.waitForFunction(()=>[...document.querySelectorAll('.result-kind')].every(n=>n.textContent==='Weekly'));
  report.push('Blog, Weekly and topic pagination; search and filters work');
  const context = await page.context().browser().newContext({javaScriptEnabled:false,viewport:{width:390,height:844}});
  const fallback=await context.newPage();
  await fallback.goto(base);
  await fallback.locator('.feed-pagination [rel=next]').click();
  if(await fallback.locator('.post-row').count()!==10) throw Error('No-JS pagination failed');
  await context.close();
  if(failures.length) throw Error(failures.join('\n'));
  report.push('Mobile pagination works without JavaScript; no page errors');
  return report;
}
