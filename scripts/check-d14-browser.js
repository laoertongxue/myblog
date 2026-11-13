async (page, ctx) => {
  const {base,assert}=ctx;
  const route='/blog/forecast-model-selection-boundaries/';
  const reports=[];
  for(const width of [1440,390,320]){
    await page.setViewportSize({width,height:900});
    const response=await page.goto(base+route);
    assert(response.status()===200,'D14 route unavailable');
    assert(await page.locator('link[rel=canonical]').getAttribute('href')==='https://12lab.cn'+route,'D14 canonical wrong');
    assert((await page.locator('h1').textContent()).includes('模型选型边界'),'D14 title missing');
    assert(!(await page.locator('meta[name=robots]').getAttribute('content')).includes('noindex'),'D14 noindex');
    assert(!(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1)),`D14 ${width}px overflow`);
    const images=page.locator('.prose img');
    assert(await images.count()===3,'D14 requires three figures');
    for(const img of await images.all()){
      await img.scrollIntoViewIfNeeded();await img.evaluate(n=>n.decode());
      const info=await img.evaluate(n=>({width:n.naturalWidth,height:n.naturalHeight,display:n.getBoundingClientRect().width/n.getBoundingClientRect().height,alt:n.alt}));
      assert(info.width>0 && info.alt.length>10,'D14 image missing or alt uninformative');
      assert(Math.abs(info.display-info.width/info.height)<.02,'D14 image distortion');
    }
    const scroll=page.locator('.prose [role=region]');
    assert(await scroll.count()===1,'D14 accessible table wrapper absent');
    const state=await scroll.evaluate(n=>{n.scrollLeft=1000;return {focus:n.tabIndex,scroll:n.scrollLeft}});
    assert(state.focus===0,'D14 table not keyboard focusable');
    if(width<=390)assert(state.scroll>0,'D14 wide table cannot scroll');
    reports.push(`${width}px: no overflow, metadata, three figures, accessible table`);
  }
  const links=await page.locator('.prose a[href$=".zip"]').evaluateAll(ns=>ns.map(n=>n.getAttribute('href')));
  assert(links.length===3,'D14 download count');
  for(const link of links){const r=await page.request.get(base+link);const b=await r.body();assert(r.ok()&&b[0]===80&&b[1]===75,'D14 ZIP missing '+link);}
  const cover=await page.request.get(base+route+'images/d14-00_cover.png');
  const bytes=await cover.body();assert(cover.ok()&&bytes.readUInt32BE(16)===900&&bytes.readUInt32BE(20)===383,'D14 cover dimensions');
  // Publishing a new article can move D14 to a later home page.
  const homeEntries=await ctx.walkPagination(page,{path:'/'});
  assert(homeEntries.links.filter(link=>link===route).length===1,'D14 absent or duplicate across home pages');
  await page.goto(base+'/');
  const row=page.locator('.post-row').filter({has:page.locator(`h2 a[href="${route}"]`)});
  for(let current=1;current<homeEntries.pages && await row.count()===0;current++){
    const next=page.locator('.feed-pagination [rel=next]');
    assert(await next.count()===1,'D14 home pagination ended before its row');
    await next.click();
    await page.waitForFunction(expected=>document.querySelector('.feed-pagination [aria-current=page]')?.textContent.trim()===String(expected),current+1);
  }
  assert(await row.count()===1,'D14 listing absent or duplicate');assert(await row.locator('img').count()===1,'D14 has multiple list covers');
  reports.push('three ZIPs, 900×383 cover, one home cover');return reports;
}
