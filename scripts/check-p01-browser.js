async (page, ctx) => {
  const {base,assert}=ctx;
  const topic='/topics/forecasting/';
  const article=topic+'01-math-bridge/';
  const published=(await ctx.walkPagination(page,{path:topic})).links;
  for (const width of [1440,390,320]) {
    await page.setViewportSize({width,height:900});
    await page.goto(base+'/topics/');
    await page.locator('h2 a[href="'+topic+'"]').click();
    assert(new URL(page.url()).pathname===topic,'topic list opens forecasting');
    assert(await page.locator('.topic-intro > p').count()===1,'topic has one introductory paragraph');
    assert(await page.locator('.topic-intro').evaluate(el=>el.children.length===1),'no duplicate guide, table or planned sections');
    assert(await page.locator('.topic-intro').evaluate(el=>el.nextElementSibling?.classList.contains('post-row')),'article list follows introduction immediately');
    assert(JSON.stringify(await page.locator('.post-row h2 a').evaluateAll(ns=>ns.map(n=>n.getAttribute('href'))))===JSON.stringify(published.slice(0,ctx.pagerSize)),'topic lists published articles in order');
    assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'topic has no horizontal overflow');
    await page.screenshot({path:`output/playwright/forecast-topic-simple-${width}.png`,fullPage:true});

    await page.locator('.post-row h2 a[href="'+article+'"]').click();
    assert(new URL(page.url()).pathname===article,'topic opens first article');
    const index=published.indexOf(article);
    assert(index>=0,'math bridge is a published chapter');
    const previous=await page.locator('.article-prev a').evaluateAll(nodes=>nodes.map(n=>n.getAttribute('href')));
    const next=await page.locator('.article-next a').evaluateAll(nodes=>nodes.map(n=>n.getAttribute('href')));
    assert(JSON.stringify(previous)===JSON.stringify(index>0?[published[index-1]]:[]),'previous matches published chapter order');
    assert(JSON.stringify(next)===JSON.stringify(index+1<published.length?[published[index+1]]:[]),'next matches published chapter order');
    await page.locator('.chapter-navigation summary').click();
    const chapters=page.locator('nav[aria-label="专题章节"] a');
    assert(JSON.stringify(await chapters.evaluateAll(nodes=>nodes.map(n=>n.getAttribute('href'))))===JSON.stringify(published),'navigation mirrors published chapters in order');
    assert(await page.locator('nav[aria-label="专题章节"] a[href="'+article+'"]').getAttribute('aria-current')==='page','current chapter marked');
    assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'no page overflow');
    const errorTable=page.locator('.math-bridge-error-table');
    assert(await errorTable.locator('table').count()===1,'error table renders inside its scroll region');
    assert(await errorTable.locator('th').evaluateAll(nodes=>nodes.every(n=>n.getBoundingClientRect().height<120)),'error table headers remain readable');
    if(width<760)assert(await errorTable.evaluate(el=>el.scrollWidth>el.clientWidth),'wide calculation table scrolls on phones');
    for (const img of await page.locator('.prose img').all()) {
      await img.scrollIntoViewIfNeeded(); await img.evaluate(el=>el.decode());
      assert(await img.evaluate(el=>el.naturalWidth>0),'body image loads');
    }
    await page.evaluate(()=>window.scrollTo(0,0));
    await page.screenshot({path:`output/playwright/p01-${width}-article.png`,fullPage:true});
    await page.screenshot({path:`output/playwright/p01-${width}-article-top.png`});
    await page.locator('.chapter-navigation h2 a').click();
    assert(new URL(page.url()).pathname===topic,'article returns to topic home');
    await page.screenshot({path:`output/playwright/p01-${width}-topic.png`,fullPage:true});
    const expected=['seasonal-naive-demand-forecast','moving-average-demand-forecast','simple-exponential-smoothing-demand-forecast','forecast-error-bias-metrics','rolling-backtest-stockout-censoring'];
    for (const slug of expected) {
      const url='/blog/'+slug+'/';
      assert((await page.request.get(base+url)).status()===200,'original route '+slug);
    }
    await page.goto(base+article);
    for(const kind of ['practice','article','images'])assert((await page.request.get(base+'/downloads/p01-math-bridge-'+kind+'.zip')).status()===200,'download '+kind);
  }
  return ['1440px, 390px and 320px: complete forecasting topic chain, published chapter, original routes, images and downloads passed'];
}
