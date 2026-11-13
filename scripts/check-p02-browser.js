async (page, ctx) => {
  const {base,assert}=ctx;
  const topic='/topics/forecasting/', route=topic+'02-problem-and-data/';
  for (const width of [1440,390,320]) {
    await page.setViewportSize({width,height:900});
    await page.goto(base+topic);
    await page.locator('.post-row h2 a[href="'+route+'"]').click();
    assert(new URL(page.url()).pathname===route,'P02 topic entry');
    assert(await page.locator('link[rel=canonical]').getAttribute('href')==='https://12lab.cn'+route,'P02 canonical');
    assert(await page.locator('.article-prev a').getAttribute('href')===topic+'01-math-bridge/','P02 previous chapter');
    const published=(await ctx.walkPagination(page,{path:topic})).links;
    await page.goto(base+route);
    const index=published.indexOf(route);
    assert(index>=0,"current article is a published chapter");
    const next=await page.locator('.article-next a').evaluateAll(ns=>ns.map(n=>n.getAttribute('href')));
    assert(JSON.stringify(next)===JSON.stringify(index+1<published.length?[published[index+1]]:[]),'P02 next matches published chapter order');
    assert(await page.locator('.prose img').count()===4,'P02 four images');
    for(const img of await page.locator('.prose img').all()) {
      await img.scrollIntoViewIfNeeded(); await img.evaluate(n=>n.decode());
      assert(await img.evaluate(n=>n.naturalWidth>0 && Math.abs(n.getBoundingClientRect().width/n.getBoundingClientRect().height-n.naturalWidth/n.naturalHeight)<.02),'P02 complete undistorted image');
    }
    assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),'P02 no page overflow');
    await page.evaluate(()=>window.scrollTo(0,0));
    await page.screenshot({path:`output/playwright/p02-${width}.png`,fullPage:true});
    await page.screenshot({path:`output/playwright/p02-${width}-top.png`});
  }
  const links=await page.locator('.prose a[href$=".zip"]').evaluateAll(ns=>ns.map(n=>n.getAttribute('href')));
  assert(links.length===3,'P02 three download bundles');
  for(const link of links){const r=await page.request.get(base+link), b=await r.body();assert(r.ok()&&b[0]===80&&b[1]===75,'P02 valid ZIP '+link);}
  const cover=await page.request.get(base+route+'images/p02-01_cover.png'), bytes=await cover.body();
  assert(cover.ok()&&bytes.readUInt32BE(16)===900&&bytes.readUInt32BE(20)===383,'P02 exact cover size');
  return ['P02: desktop and mobile topic entry, previous/next, canonical, 4 images, no overflow, 3 ZIPs, exact cover size'];
}
