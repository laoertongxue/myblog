// Adversarial boundary checks: hostile content, navigation state, contrast and
// image priority. Executed by scripts/run-browser-checks.mjs.
//   npm run check:browser -- --only adversarial-ui
//
// The aria-current expectations are derived: on every page exactly one nav item
// may be marked, it must point at an ancestor of the current URL, and it is
// `page` only when the href is the URL itself.
async (page, ctx) => {
  const { base, assert } = ctx;
  const report = [];
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto(base);
  const headline = page.locator('.row-body h2 a').first();
  assert(await headline.count() > 0, 'home feed has no headline to stress');
  await headline.evaluate(node => { node.textContent = 'A'.repeat(90); });
  assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), 'long title causes horizontal overflow');

  await page.goto(base + '/search/');
  await page.locator('#search-query').fill('Z'.repeat(180));
  await page.locator('.search-form button').click();
  await page.waitForFunction(() => document.querySelector('#search-status').textContent.includes('没有找到'));
  assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), 'long search query causes horizontal overflow');
  report.push('Unbroken 90-character title and 180-character query wrap without overflow');

  await page.goto(base);
  const toggle = page.locator('.mobile-menu-toggle');
  const dialog = page.locator('#mobile-navigation');
  await toggle.click();
  const bounds = await dialog.boundingBox();
  await page.mouse.click(bounds.x + 8, bounds.y + 60);
  assert(await dialog.isVisible(), 'click inside the dialog padding closed the menu');
  await page.mouse.click(4, 400);
  await dialog.waitFor({ state: 'hidden' });
  await toggle.click();
  await page.keyboard.press('Escape');
  await dialog.waitFor({ state: 'hidden' });
  report.push('Menu ignores clicks inside its own padding; backdrop and Escape still close it');

  for (const route of ['/blog/supply-chain-ai-moment/', '/weekly/002/', '/topics/agent-engineering/01-agent-framework/', '/blog/', '/about/', '/now/', '/links/']) {
    await page.goto(base + route);
    for (const selector of ['.site-header', '#mobile-navigation']) {
      const marked = page.locator(`${selector} [aria-current]`);
      assert(await marked.count() === 1, `${route} ${selector}: expected exactly one aria-current, found ${await marked.count()}`);
      const href = await marked.getAttribute('href');
      const state = await marked.getAttribute('aria-current');
      assert(route.startsWith(href), `${route} ${selector}: ${href} is not an ancestor of the page`);
      assert(state === (route === href ? 'page' : 'location'), `${route} ${selector}: expected ${route === href ? 'page' : 'location'}, got ${state}`);
    }
  }
  report.push('Every page marks exactly one ancestor nav item, with page/location used correctly');

  await page.goto(base);
  const contrast = await page.evaluate(() => {
    const tokens = getComputedStyle(document.documentElement);
    const relative = value => {
      const match = String(value).match(/rgba?\(([^)]+)\)/);
      if (!match) return null;
      const [r, g, b] = match[1].split(',').map(Number);
      const channel = c => { const v = c / 255; return v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4; };
      return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b);
    };
    const sample = document.querySelector('.row-date') ?? document.querySelector('.row-meta');
    const foreground = relative(getComputedStyle(sample).color);
    const background = relative(getComputedStyle(document.body).backgroundColor);
    return {
      paper: tokens.getPropertyValue('--lab-paper').trim(),
      muted: tokens.getPropertyValue('--lab-muted').trim(),
      text: sample.textContent.trim().slice(0, 24),
      ratio: (Math.max(foreground, background) + 0.05) / (Math.min(foreground, background) + 0.05),
    };
  });
  assert(contrast.paper && contrast.muted, 'design tokens --lab-paper / --lab-muted must stay defined');
  assert(contrast.ratio >= 4.5, `muted text ${JSON.stringify(contrast.text)} contrast is ${contrast.ratio.toFixed(2)}:1`);
  report.push(`Muted list text renders at ${contrast.ratio.toFixed(2)}:1 against the real page background`);

  // Thumbnail priority is derived from the listing itself: exactly one group's
  // first picture may be eager/high, everything else stays lazy. Listings whose
  // posts have no images legitimately render 0 preview groups, so the
  // expectation is "one prioritized picture per listing that shows previews".
  for (const route of ['/', '/weekly/', '/blog/', '/topics/', '/topics/agent-engineering/']) {
    await page.goto(base + route);
    assert(await page.locator('.post-row').count() > 0, `${route}: listing is empty`);
    const groups = await page.locator('.post-row .list-thumbnails').count();
    const total = await page.locator('.list-thumbnails img').count();
    const prioritized = await page.locator('.list-thumbnails img[fetchpriority="high"]').count();
    const eager = await page.locator('.list-thumbnails img[loading="eager"]').count();
    assert(prioritized === (groups ? 1 : 0), `${route}: ${prioritized} prioritized thumbnail(s) across ${groups} preview group(s)`);
    assert(eager === prioritized, `${route}: eager thumbnails (${eager}) do not match prioritized ones (${prioritized})`);
    assert(await page.locator('.list-thumbnails img[loading="lazy"]').count() === total - prioritized, `${route}: every thumbnail after the first must stay lazy`);
    if (route === '/' || route === '/topics/agent-engineering/') assert(groups > 0, `${route}: previews disappeared from a listing that shows them`);
    for (let i = 0; i < groups; i++) {
      assert(await page.locator('.list-thumbnails').nth(i).locator('img').count() <= 3, `${route}: a preview group shows more than three pictures`);
    }
  }
  report.push('Exactly the first preview of each listing is prioritized, never more than three per row, the rest lazy');
  return report;
}
