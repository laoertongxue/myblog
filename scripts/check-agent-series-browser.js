// Run with playwright-cli run-code against make check output on port 1316.
async (page) => {
  const base = 'http://127.0.0.1:1316';
  const topic = '/topics/agent-engineering/';
  const chapters = [topic + '01-agent-framework/', topic + '02-harness/'];
  const titles = ['理解 Agent：从核心构成到工程全景', '理解 Harness：从模型回答到 Agent 执行'];
  const report = [];
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  for (const width of [1440, 390, 320]) {
    await page.setViewportSize({width, height: 900});
    await page.goto(base + '/topics/');
    if (await page.locator('.topic-row').count() !== 1) throw Error('Expected one real series');
    await page.locator('.topic-row h2 a').click();
    await page.waitForURL(base + topic);
    const links = await page.locator('.post-row h2 a').evaluateAll(nodes => nodes.map(node => ({href: node.getAttribute('href'), title: node.textContent})));
    if (JSON.stringify(links) !== JSON.stringify(chapters.map((href, i) => ({href, title: titles[i]})))) throw Error('Wrong chapter order');
    for (const [i, chapter] of chapters.entries()) {
      await page.goto(base + chapter);
      if (await page.locator('h1').count() !== 1 || await page.locator('h1').textContent() !== titles[i]) throw Error('Article title duplicated or wrong');
      if (await page.locator('.test-notice, .test-label').count()) throw Error('Test marker remains');
      const pictures = await page.locator('.prose img').evaluateAll(async images => {
        images.forEach(image => image.loading = 'eager');
        await Promise.all(images.map(image => image.decode()));
        return images.map(image => ({src: image.currentSrc, width: image.naturalWidth, height: image.naturalHeight, alt: image.alt}));
      });
      if (pictures.length !== (i === 0 ? 11 : 5) || pictures.some(picture => !picture.width || !picture.height || !picture.alt || !picture.src.startsWith(base + chapter + 'assets/'))) throw Error('Invalid article pictures');
      if (i === 0) {
        const expected = ['00-agent-framework', '01-agent-overview', '02-context-engineering', '03-memory-and-knowledge', '04-tools', '05-coding-agent', '06-interaction', '07-evaluation', '08-post-training', '09-continuous-evolution', '10-multi-agent'];
        const sizes = [[1697, 927], [1698, 926], ...Array.from({length: 9}, () => [1536, 1024])];
        const mapped = await page.locator('.prose').evaluate(element => {
          let chapter = '';
          const result = [];
          for (const node of element.querySelectorAll('h2, img')) {
            if (node.tagName === 'H2') chapter = node.textContent;
            else result.push({chapter, src: node.getAttribute('src'), original: node.closest('a')?.getAttribute('href'), rendered: node.getBoundingClientRect().width});
          }
          return result;
        });
        const expectedChapters = ['', '第一章', '第二章', '第三章', '第四章', '第五章', '第六章', '第七章', '第八章', '第九章', '第十章'];
        if (mapped.length !== 11 || mapped[0].chapter !== '' || mapped.some((image, index) => !image.chapter.startsWith(expectedChapters[index]) || !image.src.includes(expected[index]) || !image.original.endsWith(expected[index] + '.png') || image.rendered > width - 40)) throw Error('Wrong Agent picture placement or size');
        for (const [index, name] of expected.entries()) {
          const original = page.locator('.prose img').nth(index).locator('..');
          await original.click();
          await page.waitForURL(base + chapter + 'assets/' + name + '.png');
          const resolution = await page.locator('img').evaluate(async image => { await image.decode(); return [image.naturalWidth, image.naturalHeight]; });
          if (JSON.stringify(resolution) !== JSON.stringify(sizes[index])) throw Error('Full-resolution PNG unavailable');
          await page.goBack();
          await page.waitForURL(base + chapter);
        }
      }
      if (await page.evaluate(() => document.documentElement.scrollWidth > innerWidth)) throw Error('Horizontal overflow');
      const toc = page.locator('.floating-toc');
      await toc.locator('summary').click();
      const entries = toc.locator('a');
      if (await entries.count() !== (i === 0 ? 10 : 8)) throw Error('Incomplete article TOC');
      const target = entries.last();
      const hash = await target.getAttribute('href');
      await target.click();
      await page.waitForFunction(value => decodeURIComponent(location.hash) === decodeURIComponent(value), hash);
      await page.waitForFunction(() => !document.querySelector('.floating-toc').open);
      await page.waitForFunction(value => document.querySelector('.toc-panel a[aria-current=location]')?.getAttribute('href') === value, hash);
      const pager = page.locator('.article-pager a');
      if (await pager.count() !== 1 || await pager.getAttribute('href') !== chapters[1 - i]) throw Error('Wrong previous/next article');
      await pager.click();
      await page.waitForURL(base + chapters[1 - i]);
      await page.goto(base + chapter);
      const navigation = page.locator('.chapter-navigation');
      await navigation.locator('summary').click();
      const chapterLinks = navigation.locator('nav a');
      if (JSON.stringify(await chapterLinks.evaluateAll(nodes => nodes.map(node => node.getAttribute('href')))) !== JSON.stringify(chapters)) throw Error('Chapter navigation order');
      if (await navigation.locator('[aria-current=page]').getAttribute('href') !== chapter) throw Error('Active chapter not marked');
      await chapterLinks.nth(1 - i).click();
      await page.waitForURL(base + chapters[1 - i]);
      if (i === 1) {
        await page.goto(base + chapter);
        if (await page.locator('.prose table').count() !== 2) throw Error('Concept tables missing');
        for (let reference = 1; reference <= 5; reference++) {
          const link = page.locator(`.prose a[href="#ref-${reference}"]`).first();
          await link.click();
          await page.waitForFunction(id => location.hash === '#' + id && !!document.getElementById(id), `ref-${reference}`);
        }
      }
    }
    for (const query of ['Agent 的构造与实践', ...titles]) {
      await page.goto(base + '/search/?q=' + encodeURIComponent(query));
      await page.waitForFunction(() => !document.querySelector('#search-status').textContent.includes('正在搜索'));
      await page.locator('[data-filter=topics]').click();
      await page.waitForFunction(() => document.querySelectorAll('.search-result').length > 0);
      if (!(await page.locator('.search-result h2 a').allTextContents()).includes(query)) throw Error('Series/article absent in search');
    }
    await page.goto(base + chapters[1]);
    await page.screenshot({path: `output/playwright/agent-harness-${width}.png`, fullPage: true});
    await page.goto(base + topic);
    await page.screenshot({path: `output/playwright/agent-series-${width}.png`, fullPage: true});
    await page.goto(base + chapters[0]);
    await page.screenshot({path: `output/playwright/agent-framework-${width}.png`, fullPage: true});
    report.push(`${width}px: series order, local pictures, TOCs, previous/next, chapter navigation, tables, references and search passed`);
  }
  if (errors.length) throw Error(errors.join('\n'));
  return report;
}
