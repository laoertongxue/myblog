// Mobile header, navigation dialog and mobile-only content rules.
// Executed by scripts/run-browser-checks.mjs (see its header for the contract).
//   npm run check:browser -- --only mobile-navigation
//
// The mobile menu must offer exactly the same destinations as the desktop
// header, and that expectation is read from the page instead of being written
// out here, so editing hugo.toml cannot silently desynchronise the two.
async (page, ctx) => {
  const { base, assert, pagerSize } = ctx;
  const report = [];
  for (const width of [320, 390, 760]) {
    await page.setViewportSize({ width, height: 844 });
    await page.goto(base);

    // The feed must start immediately below the header (no leftover intro
    // block) and never list more than one page worth of articles.
    const rows = page.locator('.home-feed .post-row');
    assert(await rows.count() > 0, 'home feed is empty');
    assert(await rows.count() <= pagerSize, `home feed lists ${await rows.count()} rows, above pagerSize ${pagerSize}`);
    const firstRowTop = await rows.first().evaluate(node => node.getBoundingClientRect().top);
    const headerBottom = await page.locator('.site-header').evaluate(node => node.getBoundingClientRect().bottom);
    assert(firstRowTop - headerBottom <= 40, `empty block between header and feed: ${Math.round(firstRowTop - headerBottom)}px`);

    await page.goto(base + '/blog/supply-chain-ai-moment/');
    assert(await page.locator('.mobile-site-title').isVisible(), 'mobile site title hidden');
    assert(!await page.locator('.header-primary').isVisible(), 'desktop navigation visible at mobile width');
    assert(!await page.locator('.footer-details').first().isVisible(), 'mobile footer still shows the legal details');

    const toggle = page.locator('.mobile-menu-toggle');
    const dialog = page.locator('#mobile-navigation');
    await toggle.click();
    assert(await dialog.isVisible() && await toggle.getAttribute('aria-expanded') === 'true', 'menu failed to open');
    const desktopLinks = await page.locator('.header-primary a, .header-utility a').evaluateAll(nodes => nodes.map(node => node.getAttribute('href')));
    const dialogLinks = await dialog.locator('a').evaluateAll(nodes => nodes.map(node => node.getAttribute('href')));
    for (const href of desktopLinks) {
      assert(dialogLinks.includes(href), `mobile menu is missing ${href}`);
    }
    await page.keyboard.press('Escape');
    await dialog.waitFor({ state: 'hidden' });
    await page.waitForFunction(() => document.activeElement === document.querySelector('.mobile-menu-toggle'));
    await toggle.click();
    await page.mouse.click(4, 400);
    await dialog.waitFor({ state: 'hidden' });
    await toggle.click();
    await dialog.locator('.mobile-menu-close').click();
    await dialog.waitFor({ state: 'hidden' });
    await toggle.click();
    await page.screenshot({ path: `output/playwright/mobile-menu-${width}.png` });
    await dialog.locator('a').first().click();
    await page.locator('.post-row').first().waitFor();
    assert(!await page.locator('#mobile-navigation').isVisible(), 'menu stayed open after navigating');

    await page.goto(base + '/blog/supply-chain-ai-moment/');
    const stats = await page.locator('.reading-stats').textContent();
    const match = stats.match(/全文共 (\d+) 字，阅读约需 (\d+) 分钟/);
    assert(match, `reading stats missing or reworded: ${JSON.stringify(stats)}`);
    assert(Number(match[1]) > 0 && Number(match[2]) > 0, `reading stats must report real counts: ${stats}`);
    await page.locator('.floating-toc summary').click();
    assert(await page.locator('.toc-panel').isVisible(), 'floating TOC did not open on mobile');

    await toggle.click();
    await page.setViewportSize({ width: 1280, height: 900 });
    await dialog.waitFor({ state: 'hidden' });
    await page.waitForFunction(() => !document.documentElement.classList.contains('navigation-open'));
    assert(await page.locator('.footer-details').first().isVisible(), 'desktop footer details still hidden after resizing up');
    const primary = (await page.locator('.header-primary').innerText()).trim();
    assert(primary.startsWith('← '), `desktop inner pages must link back home, got ${JSON.stringify(primary)}`);
    report.push(`${width}px: menu open/close, Escape, backdrop, focus return, navigation, resize reset, reading stats and TOC passed`);
  }
  return report;
}
