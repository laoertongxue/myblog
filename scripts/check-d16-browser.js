async (page, ctx) => {
  const {base,assert}=ctx;
  const route='/blog/fixed-batch-reorder-threshold/';
  const reports=[];
  for(const width of [1440,390,320]){
    await page.setViewportSize({width,height:900});
    const response=await page.goto(base+route);
    assert(response.status()===200,'D16 route unavailable');
    assert(await page.locator('link[rel=canonical]').getAttribute('href')==='https://12lab.cn'+route,'D16 canonical wrong');
    assert((await page.locator('h1').textContent()).includes('固定批量策略'),'D16 title missing');
    assert(!(await page.locator('meta[name=robots]').getAttribute('content')).includes('noindex'),'D16 noindex');
    assert(!(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1)),`D16 ${width}px overflow`);
    const images=page.locator('.prose img');
    assert(await images.count()===4,'D16 requires four figures');
    for(const img of await images.all()){
      await img.scrollIntoViewIfNeeded();await img.evaluate(n=>n.decode());
      const info=await img.evaluate(n=>({width:n.naturalWidth,height:n.naturalHeight,display:n.getBoundingClientRect().width/n.getBoundingClientRect().height,alt:n.alt}));
      assert(info.width>0 && info.alt.length>10,'D16 image missing or alt uninformative');
      assert(Math.abs(info.display-info.width/info.height)<.02,'D16 image distortion');
    }
    const scroll=page.locator('.prose [role=region]');
    assert(await scroll.count()===2,'D16 accessible table wrapper absent');
    for (const region of await scroll.all()) {
    const state=await region.evaluate(n=>{n.scrollLeft=1000;return {focus:n.tabIndex,scroll:n.scrollLeft}});
    assert(state.focus===0,'D16 table not keyboard focusable');
    if(width<=390)assert(state.scroll>0,'D16 wide table cannot scroll');
    }
    reports.push(`${width}px: no overflow, metadata, four figures, accessible table`);
  }
  const links=await page.locator('.prose a[href$=".zip"]').evaluateAll(ns=>ns.map(n=>n.getAttribute('href')));
  assert(links.length===3,'D16 download count');
  for(const link of links){const r=await page.request.get(base+link);const b=await r.body();assert(r.ok()&&b[0]===80&&b[1]===75,'D16 ZIP missing '+link);}
  const cover=await page.request.get(base+route+'images/d16-00_cover.png');
  const bytes=await cover.body();assert(cover.ok()&&bytes.readUInt32BE(16)===900&&bytes.readUInt32BE(20)===383,'D16 cover dimensions');
  // Publishing a new article can move D16 to a later home page.
  const homeEntries=await ctx.walkPagination(page,{path:'/'});
  assert(homeEntries.links.filter(link=>link===route).length===1,'D16 absent or duplicate across home pages');
  await page.goto(base+'/');
  const row=page.locator('.post-row').filter({has:page.locator(`h2 a[href="${route}"]`)});
  for(let current=1;current<homeEntries.pages && await row.count()===0;current++){
    const next=page.locator('.feed-pagination [rel=next]');
    assert(await next.count()===1,'D16 home pagination ended before its row');
    await next.click();
    await page.waitForFunction(expected=>document.querySelector('.feed-pagination [aria-current=page]')?.textContent.trim()===String(expected),current+1);
  }
  assert(await row.count()===1,'D16 listing absent or duplicate');assert(await row.locator('img').count()===1,'D16 has multiple list covers');
  reports.push('three ZIPs, 900×383 cover, one home cover');return reports;
}
