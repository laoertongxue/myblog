async (page) => {
  const base='http://127.0.0.1:1316';
  const report=[];
  for(const width of [320,390,760]) {
    await page.setViewportSize({width,height:844});
    await page.goto(base);
    if(await page.locator('.home-intro').isVisible()) throw Error('Mobile home intro remains visible');
    const firstRowTop = await page.locator('.home-feed .post-row').first().evaluate(node=>node.getBoundingClientRect().top);
    const headerBottom = await page.locator('.site-header').evaluate(node=>node.getBoundingClientRect().bottom);
    if(firstRowTop-headerBottom > 40) throw Error('Empty intro space remains');
    await page.goto(base+'/blog/layout-test-01/');
    if(!await page.locator('.mobile-site-title').isVisible() || await page.locator('.header-primary').isVisible()) throw Error('Mobile header');
    if(await page.locator('.footer-details').first().isVisible()) throw Error('Mobile footer details visible');
    const toggle=page.locator('.mobile-menu-toggle');
    const dialog=page.locator('#mobile-navigation');
    await toggle.click();
    if(!await dialog.isVisible() || await toggle.getAttribute('aria-expanded')!=='true') throw Error('Open failed');
    if(!await dialog.locator('a[href="/weekly/"]').isVisible()) throw Error('Missing menu items');
    await page.keyboard.press('Escape');
    await dialog.waitFor({state:'hidden'});
    await page.waitForFunction(()=>document.activeElement===document.querySelector('.mobile-menu-toggle'));
    await toggle.click();
    await page.mouse.click(4,400);
    await dialog.waitFor({state:'hidden'});
    await toggle.click();
    await dialog.locator('.mobile-menu-close').click();
    await dialog.waitFor({state:'hidden'});
    await toggle.click();
    await page.screenshot({path:`output/playwright/mobile-menu-${width}.png`});
    await dialog.locator('a[href="/weekly/"]').click();
    await page.waitForURL('**/weekly/');
    await page.locator('.post-row').first().waitFor();
    if(await page.locator('#mobile-navigation').isVisible()) throw Error('Menu remains open after navigation');
    await page.goto(base+'/blog/layout-test-01/');
    const stats=await page.locator('.reading-stats').textContent();
    if(!/全文共 \d+ 字，阅读约需 \d+ 分钟/.test(stats)) throw Error(stats);
    await page.locator('.floating-toc summary').click();
    if(!await page.locator('.toc-panel').isVisible()) throw Error('TOC regression');
    await toggle.click();
    await page.setViewportSize({width:1280,height:900});
    await dialog.waitFor({state:'hidden'});
    await page.waitForFunction(()=>!document.documentElement.classList.contains('navigation-open'));
    if(!await page.locator('.footer-details').first().isVisible()) throw Error('Desktop footer hidden');
    if(!await page.locator('.header-primary').innerText().then(s=>s.startsWith('← 拾贰画生'))) throw Error('Missing return home label');
    report.push(`${width}px: menu open/close, Escape, backdrop, focus return, navigation, resize reset, metadata and TOC passed`);
  }
  return report;
}
