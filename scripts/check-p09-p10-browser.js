async (page,ctx) => {
 const {base,assert}=ctx,topic='/topics/forecasting/';
 const routes=['08-hierarchical-reconciliation/','09-intermittent-demand/','10-new-product-cold-start/'];
 for(const width of [1440,390,320]){
  await page.setViewportSize({width,height:900});await page.goto(base+topic);
  const links=await page.locator('.post-row h2 a').evaluateAll(ns=>ns.map(n=>new URL(n.href).pathname));
  assert(links.indexOf(topic+routes[0])<links.indexOf(topic+routes[1])&&links.indexOf(topic+routes[1])<links.indexOf(topic+routes[2]),'topic ordered 8 9 10');
  for(let j=1;j<3;j++){
   const route=topic+routes[j];await page.goto(base+route);
   assert(await page.locator('h1').count()===1,'single title');
   assert(await page.locator('link[rel=canonical]').getAttribute('href')==='https://12lab.cn'+route,'canonical');
   assert(await page.locator('.article-prev a').getAttribute('href')===topic+routes[j-1],'previous');
   if(j===1)assert(await page.locator('.article-next a').getAttribute('href')===topic+routes[j+1],'next');
   else assert(await page.locator('.article-next a').count()===0,'last no next');
   assert(await page.locator('.prose img').count()===4,'four images');
   for(let i=0;i<4;i++){
    const img=page.locator('.prose img').nth(i);await img.scrollIntoViewIfNeeded();await img.evaluate(n=>n.decode());
    assert(await img.evaluate(n=>n.naturalWidth>0&&Math.abs(n.width/n.height-n.naturalWidth/n.naturalHeight)<.02),'loaded complete proportions');
    await page.screenshot({path:`output/playwright/p${j+8}-${width}-image-${i}.png`});
   }
   assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),'no page overflow');
   for(const table of await page.locator('.prose table').all())assert(await table.evaluate(n=>n.parentElement.classList.contains('regression-table-scroll')),'table scroll wrapper');
   const downloads=await page.locator('.prose a[href$=".zip"]').evaluateAll(ns=>ns.map(n=>n.href));assert(downloads.length===3,'three downloads');
   for(const href of downloads){const r=await page.request.get(href);const b=await r.body();assert(r.ok()&&b[0]===80&&b[1]===75,'zip readable');}
   await page.screenshot({path:`output/playwright/p${j+8}-${width}-full.png`,fullPage:true});
   await page.evaluate(()=>scrollTo(0,0));await page.screenshot({path:`output/playwright/p${j+8}-${width}-top.png`});
  }
  await page.goto(base+topic+routes[0]);assert(await page.locator('.article-next a').getAttribute('href')===topic+routes[1],'P08 next P09');
 }
 return ['P09/P10 at 1440, 390, 320: topic order, navigation, four figures each, tables and six downloads'];
}
