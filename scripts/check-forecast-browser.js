async (page, ctx) => {
  const {base,assert}=ctx;
  // Compare the rendered shared design, including the site's fixed light scheme
  // when the operating system prefers dark. Avoid duplicating CSS values here.
  const design=()=>{
    const result={};
    for(const selector of ['body','.site-header','.site-workspace','.article-heading h1','.prose','.page-footer']){
      const node=document.querySelector(selector),style=getComputedStyle(node);
      result[selector]=Object.fromEntries(['fontFamily','fontSize','lineHeight','color','backgroundColor','colorScheme'].map(key=>[key,style[key]]));
      if(selector==='.site-header'||selector==='.site-workspace'){
        const {x,width}=node.getBoundingClientRect();Object.assign(result[selector],{x,width});
      }
    }
    return result;
  };
  for(const colorScheme of ['light','dark'])for(const width of [1440,390,320]){
    await page.emulateMedia({colorScheme});await page.setViewportSize({width,height:900});
    await page.goto(base+'/topics/forecasting/01-math-bridge/');
    const reference=await page.evaluate(design);
    for(const route of ['/forecast/','/forecast/presale-full/']){
      await page.goto(base+route);
      assert(JSON.stringify(await page.evaluate(design))===JSON.stringify(reference),`shared blog design: ${route}, ${width}px, ${colorScheme}`);
      assert(await page.locator('.site-header').count()===1&&await page.locator('.page-footer').count()===1,'single shared header and footer');
      assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),'shared layout does not overflow');
    }
  }
  await page.emulateMedia({colorScheme:'light'});
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
      assert(await page.locator('#print').evaluate(n=>n.getBoundingClientRect().height<65),`${width}px print label wraps vertically: ${route}`);
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
    {await page.locator('#menu').click();assert(await page.locator('#search').isVisible(),'mobile course menu');assert(await page.locator('#search').evaluate(n=>{const r=n.getBoundingClientRect();return document.elementFromPoint(r.x+r.width/2,r.y+r.height/2)===n;}),'mobile search is not covered by header');await page.screenshot({path:`output/playwright/forecast-${width}-menu.png`});await page.keyboard.press('Escape');assert(!(await page.locator('#side').isVisible()),'escape closes menu');}
    await page.goto(base+'/forecast/legacy-0/');
    await page.screenshot({path:`output/playwright/forecast-${width}-lesson.png`});
  }
  await page.setViewportSize({width:1440,height:900});
  await page.goto(base+'/forecast/#lesson-81');await page.waitForURL('**/forecast/resource-center/');
  await page.goto(base+'/forecast/#unit-core-13');await page.waitForURL('**/forecast/core-13/');
  await page.evaluate(()=>{window.print=()=>{window.__printed=true;};});await page.locator('#print').click();assert(await page.evaluate(()=>window.__printed),'print action');
  await page.locator('#complete').check();await page.reload();assert(await page.locator('#complete').isChecked(),'progress persists');
  await page.locator('#menu').click();
  const download=page.waitForEvent('download');await page.locator('#export').click();assert((await download).suggestedFilename()==='forecast-learning-progress.json','progress export');
  await page.locator('#search').fill('数学桥梁');assert(await page.locator('#nav a[data-unit]:visible').count()>0,'course search');
  await page.locator('#search').fill('definitely-no-course-123');assert(await page.locator('#nav a[data-unit]:visible').count()===0,'search filtering');
  await page.goto(base+'/search/?q=24小时静默&type=forecast');await page.locator('.search-result').first().waitFor();assert(await page.locator('.search-result a[href="/forecast/specialty-gap-presale-plan/"]').count()===1,'blog search finds course');
  const nojs=await page.context().browser().newContext({javaScriptEnabled:false,viewport:{width:390,height:844}});
  const reader=await nojs.newPage();await reader.goto(base+'/forecast/');
  assert(await reader.locator('#cards a').count()===paths.length,'no-JS full course directory');
  await reader.locator('#menu').click();assert(await reader.locator('#nav').isVisible(),'no-JS native course directory');
  await reader.locator('#nav a[data-unit]').first().click();
  assert((await reader.locator('.lesson-content').innerText()).length>100,'no-JS course directory navigation');
  await reader.goto(base+paths[0]);assert((await reader.locator('.lesson-content').innerText()).length>100,'no-JS lesson content');
  await nojs.close();
  return [`${paths.length} lessons at 1440/390/320px, shared blog design in light/dark preferences, images, calculator, hash aliases, local progress/export, search and no-JS reading`];
}
