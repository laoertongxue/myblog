async (page, ctx) => {
  const {base,assert}=ctx;
  const topic='/topics/forecasting/', route=topic+'03-regression-and-features/';
  for (const width of [1440,390,320]) {
    await page.setViewportSize({width,height:900});
    await page.goto(base+topic);
    await page.locator('.post-row h2 a[href="'+route+'"]').click();
    assert(new URL(page.url()).pathname===route,'P03 topic entry');
    assert(await page.locator('link[rel=canonical]').getAttribute('href')==='https://12lab.cn'+route,'P03 canonical');
    assert(await page.locator('.article-prev a').getAttribute('href')===topic+'02-problem-and-data/','P03 previous chapter');
    const published=(await ctx.walkPagination(page,{path:topic})).links;
    await page.goto(base+route);
    const index=published.indexOf(route);
    assert(index>=0,"current article is a published chapter");
    const next=await page.locator('.article-next a').evaluateAll(ns=>ns.map(n=>n.getAttribute('href')));
    assert(JSON.stringify(next)===JSON.stringify(index+1<published.length?[published[index+1]]:[]),'P03 next matches published chapter order');
    assert(await page.locator('.prose img').count()===5,'P03 five images');
    for(const img of await page.locator('.prose img').all()) {
      await img.scrollIntoViewIfNeeded(); await img.evaluate(n=>n.decode());
      assert(await img.evaluate(n=>n.naturalWidth>0 && Math.abs(n.getBoundingClientRect().width/n.getBoundingClientRect().height-n.naturalWidth/n.naturalHeight)<.02),'P03 complete undistorted image');
    }
    assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),'P03 no page overflow');
    assert(!(await page.locator('.prose').innerText()).includes('**多特征'),'P03 emphasis renders without literal markers');
    assert(await page.locator('.regression-table-scroll').count()===9,'P03 all nine tables have scroll containers');
    for(const index of [2,7]) {
      const table=page.locator('.regression-table-scroll').nth(index);
      assert(await table.evaluate(n=>getComputedStyle(n).overflowX==='auto'),'P03 table scroll remains inside container');
      if(width<620) assert(await table.evaluate(n=>n.scrollWidth>n.clientWidth),'P03 wide table can scroll on mobile');
      const intact=await table.locator('td').evaluateAll(cells=>cells.every(td=>{
        const walker=document.createTreeWalker(td,NodeFilter.SHOW_TEXT);let node;
        while(node=walker.nextNode()) {const re=/[−-]?\d+(?:\.\d+)?%?/g;let m;while(m=re.exec(node.textContent)){const r=document.createRange();r.setStart(node,m.index);r.setEnd(node,m.index+m[0].length);if(r.getClientRects().length!==1)return false;}}
        return true;
      }));
      assert(intact,'P03 numerical tokens stay on one line');
    }
    await page.evaluate(()=>window.scrollTo(0,0));
    await page.screenshot({path:`output/playwright/p03-${width}.png`,fullPage:true});
    await page.screenshot({path:`output/playwright/p03-${width}-top.png`});
  }
  const links=await page.locator('.prose a[href$=".zip"]').evaluateAll(ns=>ns.map(n=>n.getAttribute('href')));
  assert(links.length===3,'P03 three download bundles');
  for(const link of links){const url=new URL(link,'https://12lab.cn');assert(url.origin==='https://12lab.cn','P03 downloads remain on this site');const r=await page.request.get(base+url.pathname), b=await r.body();assert(r.ok()&&b[0]===80&&b[1]===75,'P03 valid ZIP '+link);}
  const cover=await page.request.get(base+route+'images/p03-01_cover.png'), bytes=await cover.body();
  assert(cover.ok()&&bytes.readUInt32BE(16)===900&&bytes.readUInt32BE(20)===383,'P03 exact cover size');
  return ['P03: desktop and mobile topic entry, previous/next, canonical, 5 images, no overflow, 3 ZIPs, exact cover size'];
}
