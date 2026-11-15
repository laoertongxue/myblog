async (page,ctx) => {
 const {base,assert}=ctx,topic='/topics/forecasting/',route=topic+'08-hierarchical-reconciliation/';
 for(const width of [1440,390,320]){
  await page.setViewportSize({width,height:900});await page.goto(base+topic);
  const chapterLinks=await page.locator('.post-row h2 a').evaluateAll(ns=>ns.map(n=>new URL(n.href).pathname));
  const expectedNext=chapterLinks[chapterLinks.indexOf(route)+1];
  await page.locator('.post-row h2 a[href="'+route+'"]').click();
  assert(new URL(page.url()).pathname===route,'P08 topic link');
  assert(await page.locator('link[rel=canonical]').getAttribute('href')==='https://12lab.cn'+route,'P08 canonical');
  assert(await page.locator('.article-prev a').getAttribute('href')===topic+'07-lead-time-uncertainty/','P08 previous');
  if(expectedNext) assert(await page.locator('.article-next a').getAttribute('href')===expectedNext,'P08 next matches published topic order');
  else assert(await page.locator('.article-next a').count()===0,'P08 no next beyond published topic order');
  assert(await page.locator('.prose img').count()===5,'P08 cover and four figures');
  for(const img of await page.locator('.prose img').all()){
   await img.scrollIntoViewIfNeeded();await img.evaluate(n=>n.decode());
   assert(await img.evaluate(n=>n.naturalWidth>0&&Math.abs(n.width/n.height-n.naturalWidth/n.naturalHeight)<.02),'P08 loaded undistorted image');
  }
  assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),'P08 no page overflow');
  const tables=page.locator('.regression-table-scroll');assert(await tables.count()===1,'P08 all tables wrapped');
  for(const table of await tables.all())assert(await table.evaluate(n=>getComputedStyle(n).overflowX==='auto'),'P08 table scroll');
  for(const i of [0]){
   await tables.nth(i).scrollIntoViewIfNeeded();
   await page.screenshot({path:`output/playwright/p08-${width}-table-${i}.png`});
  }
  for(let i=0;i<5;i++){
   await page.locator('.prose img').nth(i).scrollIntoViewIfNeeded();
   await page.screenshot({path:`output/playwright/p08-${width}-image-${i}.png`});
  }
  assert((await page.locator('.prose').innerText()).includes('104'),'P08 recommendation visible');
  assert(await page.locator('h1').count()===1,'P08 single title');
  assert(!(await page.locator('.prose').innerText()).includes('**'),'P08 emphasis renders without Markdown markers');
  assert(!(await page.locator('.prose').innerText()).includes('](images/'),'P08 image links render without Markdown markers');

  await page.locator('.article-prev').scrollIntoViewIfNeeded(); await page.screenshot({path:`output/playwright/p08-${width}-navigation.png`});
  await page.evaluate(()=>window.scrollTo(0,0));await page.screenshot({path:`output/playwright/p08-${width}-top.png`});
  await page.screenshot({path:`output/playwright/p08-${width}.png`,fullPage:true});
 }
 const links=await page.locator('.prose a[href$=".zip"]').evaluateAll(ns=>ns.map(n=>n.href));assert(links.length===3,'P08 three archives');
 for(const href of links){const res=await page.request.get(href);const b=await res.body();assert(res.ok()&&b[0]===80&&b[1]===75,'P08 ZIP loads');}
 await page.goto(base+topic+'07-lead-time-uncertainty/');assert(await page.locator('.article-next a').getAttribute('href')===route,'P07 points to P08');
 await page.goto(base+'/'); assert(await page.locator('a[href="'+route+'"]').count()>0,'P08 appears on homepage');
 return ['P08 desktop, 390px and 320px: topic/navigation, five images, tables, formula, downloads, screenshots'];
}
