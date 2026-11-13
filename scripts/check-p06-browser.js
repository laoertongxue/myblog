async (page,ctx) => {
 const {base,assert}=ctx,topic='/topics/forecasting/',route=topic+'06-source-allocation/';
 for(const width of [1440,390,320]){
  await page.setViewportSize({width,height:900});await page.goto(base+topic);
  await page.locator('.post-row h2 a[href="'+route+'"]').click();
  assert(new URL(page.url()).pathname===route,'P06 topic link');
  assert(await page.locator('link[rel=canonical]').getAttribute('href')==='https://12lab.cn'+route,'P06 canonical');
  assert(await page.locator('.article-prev a').getAttribute('href')===topic+'05-forecast-to-replenishment/','P06 previous');
  assert(await page.locator('.article-next a').count()===0,'P06 has no unpublished next');
  assert(await page.locator('.prose img').count()===5,'P06 cover and four figures');
  for(const img of await page.locator('.prose img').all()){
   await img.scrollIntoViewIfNeeded();await img.evaluate(n=>n.decode());
   assert(await img.evaluate(n=>n.naturalWidth>0&&Math.abs(n.width/n.height-n.naturalWidth/n.naturalHeight)<.02),'P06 loaded undistorted image');
  }
  assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),'P06 no page overflow');
  const tables=page.locator('.regression-table-scroll');assert(await tables.count()===5,'P06 all tables wrapped');
  for(const table of await tables.all())assert(await table.evaluate(n=>getComputedStyle(n).overflowX==='auto'),'P06 table scroll');
  for(const i of [0,2,3]){
   await tables.nth(i).scrollIntoViewIfNeeded();
   await page.screenshot({path:`output/playwright/p06-${width}-table-${i}.png`});
  }
  for(let i=0;i<5;i++){
   await page.locator('.prose img').nth(i).scrollIntoViewIfNeeded();
   await page.screenshot({path:`output/playwright/p06-${width}-image-${i}.png`});
  }
  assert((await page.locator('.prose').innerText()).includes('112元'),'P06 recommendation visible');
  assert(await page.locator('h1').count()===1,'P06 single title');
  assert(!(await page.locator('.prose').innerText()).includes('**'),'P06 emphasis renders without Markdown markers');
  assert(!(await page.locator('.prose').innerText()).includes('](images/'),'P06 image links render without Markdown markers');
  assert(await page.locator('.prose a[href$=".png"] img').count()===4,'P06 original figure links');
  await page.locator('.article-prev').scrollIntoViewIfNeeded(); await page.screenshot({path:`output/playwright/p06-${width}-navigation.png`});
  await page.evaluate(()=>window.scrollTo(0,0));await page.screenshot({path:`output/playwright/p06-${width}-top.png`});
  await page.screenshot({path:`output/playwright/p06-${width}.png`,fullPage:true});
 }
 const links=await page.locator('.prose a[href$=".zip"]').evaluateAll(ns=>ns.map(n=>n.href));assert(links.length===2,'P06 two archives');
 for(const href of links){const res=await page.request.get(href);const b=await res.body();assert(res.ok()&&b[0]===80&&b[1]===75,'P06 ZIP loads');}
 await page.goto(base+topic+'05-forecast-to-replenishment/');assert(await page.locator('.article-next a').getAttribute('href')===route,'P05 points to P06');
 await page.goto(base+'/'); assert(await page.locator('a[href="'+route+'"]').count()>0,'P06 appears on homepage');
 return ['P06 desktop, 390px and 320px: topic/navigation, five images, tables, formula, downloads, screenshots'];
}
