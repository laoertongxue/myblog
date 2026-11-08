async (page, ctx) => {
  const {base,assert}=ctx;
  const route='/blog/inventory-position-event-timing/';
  const reports=[];
  for(const width of [1440,390,320]){
    await page.setViewportSize({width,height:900});
    const response=await page.goto(base+route);
    assert(response.status()===200,'D15 route unavailable');
    assert(await page.locator('link[rel=canonical]').getAttribute('href')==='https://12lab.cn'+route,'D15 canonical wrong');
    assert((await page.locator('h1').textContent()).includes('库存位置与到货时序'),'D15 title missing');
    assert(!(await page.locator('meta[name=robots]').getAttribute('content')).includes('noindex'),'D15 noindex');
    assert(!(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1)),`D15 ${width}px overflow`);
    const images=page.locator('.prose img');
    assert(await images.count()===4,'D15 requires four figures');
    for(const img of await images.all()){
      await img.scrollIntoViewIfNeeded();await img.evaluate(n=>n.decode());
      const info=await img.evaluate(n=>({width:n.naturalWidth,height:n.naturalHeight,display:n.getBoundingClientRect().width/n.getBoundingClientRect().height,alt:n.alt}));
      assert(info.width>0 && info.alt.length>10,'D15 image missing or alt uninformative');
      assert(Math.abs(info.display-info.width/info.height)<.02,'D15 image distortion');
    }
    const scroll=page.locator('.prose [role=region]');
    assert(await scroll.count()===1,'D15 accessible table wrapper absent');
    const state=await scroll.evaluate(n=>{n.scrollLeft=1000;return {focus:n.tabIndex,scroll:n.scrollLeft}});
    assert(state.focus===0,'D15 table not keyboard focusable');
    if(width<=390)assert(state.scroll>0,'D15 wide table cannot scroll');
    reports.push(`${width}px: no overflow, metadata, four figures, accessible table`);
  }
  const links=await page.locator('.prose a[href$=".zip"]').evaluateAll(ns=>ns.map(n=>n.getAttribute('href')));
  assert(links.length===3,'D15 download count');
  for(const link of links){const r=await page.request.get(base+link);const b=await r.body();assert(r.ok()&&b[0]===80&&b[1]===75,'D15 ZIP missing '+link);}
  const cover=await page.request.get(base+route+'images/d15-00_cover.png');
  const bytes=await cover.body();assert(cover.ok()&&bytes.readUInt32BE(16)===900&&bytes.readUInt32BE(20)===383,'D15 cover dimensions');
  await page.goto(base+'/');
  const row=page.locator('.post-row').filter({has:page.locator(`h2 a[href="${route}"]`)});
  assert(await row.count()===1,'D15 home listing absent or duplicate');assert(await row.locator('img').count()===1,'D15 has multiple list covers');
  reports.push('three ZIPs, 900×383 cover, one home cover');return reports;
}
