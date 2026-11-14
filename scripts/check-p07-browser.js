async (page,ctx) => {
 const {base,assert}=ctx,topic='/topics/forecasting/',route=topic+'07-lead-time-uncertainty/';
 for(const width of [1440,390,320]){
  await page.setViewportSize({width,height:900});await page.goto(base+topic);
  const chapterLinks=await page.locator('.post-row h2 a').evaluateAll(ns=>ns.map(n=>new URL(n.href).pathname));
  const expectedNext=chapterLinks[chapterLinks.indexOf(route)+1];
  await page.locator('.post-row h2 a[href="'+route+'"]').click();
  assert(new URL(page.url()).pathname===route,'P07 topic link');
  assert(await page.locator('link[rel=canonical]').getAttribute('href')==='https://12lab.cn'+route,'P07 canonical');
  assert(await page.locator('.article-prev a').getAttribute('href')===topic+'06-source-allocation/','P07 previous');
  if(expectedNext) assert(await page.locator('.article-next a').getAttribute('href')===expectedNext,'P07 next matches published topic order');
  else assert(await page.locator('.article-next a').count()===0,'P07 no next beyond published topic order');
  assert(await page.locator('.prose img').count()===4,'P07 cover and three figures');
  for(const img of await page.locator('.prose img').all()){
   await img.scrollIntoViewIfNeeded();await img.evaluate(n=>n.decode());
   assert(await img.evaluate(n=>n.naturalWidth>0&&Math.abs(n.width/n.height-n.naturalWidth/n.naturalHeight)<.02),'P07 loaded undistorted image');
  }
  assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),'P07 no page overflow');
  const tables=page.locator('.regression-table-scroll');assert(await tables.count()===3,'P07 all tables wrapped');
  for(const table of await tables.all())assert(await table.evaluate(n=>getComputedStyle(n).overflowX==='auto'),'P07 table scroll');
  for(const i of [0,1,2]){
   await tables.nth(i).scrollIntoViewIfNeeded();
   await page.screenshot({path:`output/playwright/p07-${width}-table-${i}.png`});
  }
  for(let i=0;i<4;i++){
   await page.locator('.prose img').nth(i).scrollIntoViewIfNeeded();
   await page.screenshot({path:`output/playwright/p07-${width}-image-${i}.png`});
  }
  assert((await page.locator('.prose').innerText()).includes('116'),'P07 recommendation visible');
  assert(await page.locator('h1').count()===1,'P07 single title');
  assert(!(await page.locator('.prose').innerText()).includes('**'),'P07 emphasis renders without Markdown markers');
  assert(!(await page.locator('.prose').innerText()).includes('](images/'),'P07 image links render without Markdown markers');

  await page.locator('.article-prev').scrollIntoViewIfNeeded(); await page.screenshot({path:`output/playwright/p07-${width}-navigation.png`});
  await page.evaluate(()=>window.scrollTo(0,0));await page.screenshot({path:`output/playwright/p07-${width}-top.png`});
  await page.screenshot({path:`output/playwright/p07-${width}.png`,fullPage:true});
 }
 const links=await page.locator('.prose a[href$=".zip"]').evaluateAll(ns=>ns.map(n=>n.href));assert(links.length===2,'P07 two archives');
 for(const href of links){const res=await page.request.get(href);const b=await res.body();assert(res.ok()&&b[0]===80&&b[1]===75,'P07 ZIP loads');}
 await page.goto(base+topic+'06-source-allocation/');assert(await page.locator('.article-next a').getAttribute('href')===route,'P06 points to P07');
 await page.goto(base+'/'); assert(await page.locator('a[href="'+route+'"]').count()>0,'P07 appears on homepage');
 return ['P07 desktop, 390px and 320px: topic/navigation, four images, tables, formula, downloads, screenshots'];
}
