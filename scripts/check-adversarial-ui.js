// Run with playwright-cli run-code against the production build on port 1316.
async (page) => {
  const base = 'http://127.0.0.1:1316';
  const assert = (condition, message) => { if (!condition) throw Error(message); };
  const report = [];
  await page.setViewportSize({width:390,height:844});
  await page.goto(base);
  await page.locator('.row-body h2 a').first().evaluate(node => { node.textContent = 'A'.repeat(90); });
  assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), 'Long title causes horizontal overflow');
  await page.goto(base + '/search/');
  await page.locator('#search-query').fill('Z'.repeat(180));
  await page.locator('.search-form button').click();
  await page.waitForFunction(() => document.querySelector('#search-status').textContent.includes('没有找到'));
  assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), 'Long search causes horizontal overflow');
  report.push('Long title and search query wrap without overflow');
  await page.goto(base);
  const toggle = page.locator('.mobile-menu-toggle');
  const dialog = page.locator('#mobile-navigation');
  await toggle.click();
  const bounds = await dialog.boundingBox();
  await page.mouse.click(bounds.x + 8, bounds.y + 60);
  assert(await dialog.isVisible(), 'Dialog padding must not close menu');
  await page.mouse.click(4, 400);
  await dialog.waitFor({state:'hidden'});
  await toggle.click();
  await page.keyboard.press('Escape');
  await dialog.waitFor({state:'hidden'});
  report.push('Menu ignores inside padding clicks; backdrop and Escape still close');
  for (const [route, target, state] of [
    ['/blog/layout-test-01/', '/blog/', 'location'],
    ['/weekly/003/', '/weekly/', 'location'],
    ['/topics/layout-test/01-chapter/', '/topics/', 'location'],
    ['/blog/', '/blog/', 'page'],
    ['/about/', '/about/', 'page'],
    ['/now/', '/now/', 'page'],
    ['/links/', '/links/', 'page']
  ]) {
    await page.goto(base + route);
    for (const selector of ['.site-header', '#mobile-navigation']) {
      assert(await page.locator(`${selector} a[href="${target}"]`).getAttribute('aria-current') === state, `Navigation state missing: ${route}`);
      assert(await page.locator(`${selector} [aria-current]`).count() === 1, `Multiple navigation states: ${route}`);
    }
  }
  const contrast = await page.evaluate(() => {
    const style = getComputedStyle(document.documentElement);
    const luminance = hex => {
      const values = hex.trim().slice(1).match(/../g).map(value => parseInt(value,16)/255).map(value => value <= .04045 ? value/12.92 : ((value+.055)/1.055)**2.4);
      return values.reduce((total,value,index) => total + value * [.2126,.7152,.0722][index],0);
    };
    return (luminance(style.getPropertyValue('--lab-paper'))+.05)/(luminance(style.getPropertyValue('--lab-muted'))+.05);
  });
  assert(contrast >= 4.5, `Muted text contrast too low: ${contrast}`);
  report.push(`Desktop/mobile navigation states correct; muted text contrast ${contrast.toFixed(2)}:1`);
  for (const route of ['/', '/weekly/', '/blog/', '/topics/']) {
    await page.goto(base + route);
    const images = page.locator('.list-thumbnails img');
    if (await images.count()) {
      assert(await images.first().getAttribute('fetchpriority') === 'high', `First thumbnail not prioritized: ${route}`);
      assert(await images.first().getAttribute('loading') === 'eager', `First thumbnail is lazy: ${route}`);
      assert(await page.locator('.list-thumbnails img[fetchpriority="high"]').count() === 1, `Too many high priority thumbnails: ${route}`);
    }
  }
  report.push('Only the first actual thumbnail receives high priority across listings');
  await page.goto(base);
  return report;
}
