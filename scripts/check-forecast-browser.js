async (page, ctx) => {
  const {base,assert}=ctx;
  await page.goto(base+'/forecast/');
  const paths=await page.locator('#cards a').evaluateAll(nodes=>nodes.map(n=>n.getAttribute('href')));
  assert(paths.length>0,'course directory is empty');
  await page.locator('#numbers').fill('10,12,14');await page.locator('#calc').click();
  assert((await page.locator('#result').textContent()).includes('12.60'),'weighted average');
  await page.locator('#numbers').fill('-1,2,3');await page.locator('#calc').click();
  assert((await page.locator('#result').textContent()).includes('非负数'),'invalid number feedback');
  let visited=0;
  for(const route of paths){
    await page.goto(base+route);
    assert(await page.locator('.lesson-content').innerText().then(t=>t.length>100),'actual lesson '+route);
    assert(await page.locator('h1:visible').count()===1,'one visible title '+route);
    for(const width of [1440,390,320]){
      await page.setViewportSize({width,height:900});
      assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),`${width}px overflow: ${route}`);
    }
    if(++visited%20===0)console.log(`      forecast: ${visited}/${paths.length} lessons checked`);
    for(const img of await page.locator('.lesson-content img').all()){
      await img.scrollIntoViewIfNeeded();
      await img.evaluate(n=>n.decode());
      assert(await img.evaluate(n=>Math.abs(n.width/n.height-n.naturalWidth/n.naturalHeight)<.02),'image aspect ratio');
    }
  }
  for(const width of [1440,390,320]){
    await page.setViewportSize({width,height:900});
    await page.goto(base+'/forecast/');
    await page.screenshot({path:`output/playwright/forecast-${width}-home.png`});
    if(width<680){await page.locator('#menu').click();assert(await page.locator('#search').isVisible(),'mobile course menu');assert(await page.locator('#search').evaluate(n=>{const r=n.getBoundingClientRect();return document.elementFromPoint(r.x+r.width/2,r.y+r.height/2)===n;}),'mobile search is not covered by header');await page.screenshot({path:`output/playwright/forecast-${width}-menu.png`});await page.keyboard.press('Escape');assert(!(await page.locator('#side').isVisible()),'escape closes menu');}
    await page.goto(base+'/forecast/legacy-0/');
    await page.screenshot({path:`output/playwright/forecast-${width}-lesson.png`});
  }
  await page.setViewportSize({width:1440,height:900});
  await page.goto(base+'/forecast/#lesson-81');await page.waitForURL('**/forecast/resource-center/');
  await page.goto(base+'/forecast/#unit-core-13');await page.waitForURL('**/forecast/core-13/');
  await page.evaluate(()=>{window.print=()=>{window.__printed=true;};});await page.locator('#print').click();assert(await page.evaluate(()=>window.__printed),'print action');
  await page.locator('#complete').check();await page.reload();assert(await page.locator('#complete').isChecked(),'progress persists');
  const download=page.waitForEvent('download');await page.locator('#export').click();assert((await download).suggestedFilename()==='forecast-learning-progress.json','progress export');
  await page.locator('#search').fill('数学桥梁');assert(await page.locator('#nav a[data-unit]:visible').count()>0,'course search');
  await page.locator('#search').fill('definitely-no-course-123');assert(await page.locator('#nav a[data-unit]:visible').count()===0,'search filtering');
  await page.goto(base+'/search/?q=24小时静默&type=forecast');await page.locator('.search-result').first().waitFor();assert(await page.locator('.search-result a[href="/forecast/specialty-gap-presale-plan/"]').count()===1,'blog search finds course');
  const nojs=await page.context().browser().newContext({javaScriptEnabled:false,viewport:{width:390,height:844}});
  const reader=await nojs.newPage();await reader.goto(base+'/forecast/');
  assert(await reader.locator('#cards a').count()===paths.length,'no-JS full course directory');
  await reader.goto(base+paths[0]);assert((await reader.locator('.lesson-content').innerText()).length>100,'no-JS lesson content');
  await nojs.close();
  return [`${paths.length} lessons at 1440/390/320px, images, calculator, hash aliases, local progress/export, search and no-JS reading`];
}
