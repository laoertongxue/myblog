async (page,ctx) => {
 const {base,assert}=ctx,topic='/topics/forecasting/',route=topic+'04-probability-and-presale/';
 for(const width of [1440,390,320]){
  await page.setViewportSize({width,height:900});await page.goto(base+topic);
  await page.locator('.topic-intro a[href="'+route+'"]').click();
  assert(new URL(page.url()).pathname===route,'P04 topic link');
  assert(await page.locator('link[rel=canonical]').getAttribute('href')==='https://12lab.cn'+route,'P04 canonical');
  assert(await page.locator('.article-prev a').getAttribute('href')===topic+'03-regression-and-features/','P04 previous');
  assert(await page.locator('.article-next a').count()===0,'P04 no placeholder next');
  assert(await page.locator('.prose img').count()===5,'P04 cover and four figures');
  for(const img of await page.locator('.prose img').all()){
   await img.scrollIntoViewIfNeeded();await img.evaluate(n=>n.decode());
   assert(await img.evaluate(n=>n.naturalWidth>0&&Math.abs(n.width/n.height-n.naturalWidth/n.naturalHeight)<.02),'P04 loaded undistorted image');
  }
  assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),'P04 no page overflow');
  const tables=page.locator('.regression-table-scroll');assert(await tables.count()===7,'P04 all tables wrapped');
  for(const table of await tables.all())assert(await table.evaluate(n=>getComputedStyle(n).overflowX==='auto'),'P04 table scroll');
  for(const i of [0,4,6]){
   await tables.nth(i).scrollIntoViewIfNeeded();
   await page.screenshot({path:`output/playwright/p04-${width}-table-${i}.png`});
  }
  for(let i=0;i<5;i++){
   await page.locator('.prose img').nth(i).scrollIntoViewIfNeeded();
   await page.screenshot({path:`output/playwright/p04-${width}-image-${i}.png`});
  }
  assert((await page.locator('.prose').innerText()).includes('S(14)÷S(7)'),'P04 conditional formula visible');
  await page.evaluate(()=>window.scrollTo(0,0));await page.screenshot({path:`output/playwright/p04-${width}-top.png`});
  await page.screenshot({path:`output/playwright/p04-${width}.png`,fullPage:true});
 }
 const links=await page.locator('.prose a[href$=".zip"]').evaluateAll(ns=>ns.map(n=>n.href));assert(links.length===2,'P04 two archives');
 for(const href of links){const res=await page.request.get(href);const b=await res.body();assert(res.ok()&&b[0]===80&&b[1]===75,'P04 ZIP loads');}
 await page.goto(base+topic+'03-regression-and-features/');assert(await page.locator('.article-next a').getAttribute('href')===route,'P03 points to P04');
 return ['P04 desktop, 390px and 320px: topic/navigation, five images, tables, formula, downloads, screenshots'];
}
