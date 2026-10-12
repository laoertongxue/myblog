// The Agent/Harness series end to end. Executed by
// scripts/run-browser-checks.mjs.
//   npm run check:browser -- --only agent-series
//
// The series is discovered from the built pages (topic index -> chapter list ->
// article body) instead of from tables of file names and pixel sizes: adding a
// chapter or re-exporting a picture must not break this check, while a broken
// TOC, a cropped picture, a missing original PNG, a lost table or a wrong
// previous/next link still must.
async (page, ctx) => {
  const { base, assert } = ctx;
  const topic = '/topics/agent-engineering/';
  const report = [];

  const feedLinks = async feedPath => {
    const xml = await (await fetch(base + feedPath)).text();
    return [...xml.matchAll(/<item>[\s\S]*?<link>([^<]+)<\/link>/g)].map(match => new URL(match[1]).pathname);
  };

  for (const width of [1440, 390, 320]) {
    await page.setViewportSize({ width, height: 900 });

    await page.goto(base + '/topics/');
    const seriesRows = await page.locator('.topic-row').evaluateAll(nodes => nodes.map(node => ({
      href: node.querySelector('h2 a').getAttribute('href'),
      title: node.querySelector('h2 a').textContent,
      label: node.querySelector('.row-date')?.textContent ?? '',
      text: node.textContent,
    })));
    const series = seriesRows.find(row => row.href === topic);
    assert(series, `${topic} is missing from the topics index`);
    assert(!/测试/.test(series.label) && !/测试/.test(series.text), 'the series is labelled as test content');

    await page.goto(base + topic);
    const chapters = await page.locator('.post-row h2 a').evaluateAll(nodes => nodes.map(node => ({ href: node.getAttribute('href'), title: node.textContent })));
    assert(chapters.length >= 2, `series must keep at least two chapters, found ${chapters.length}`);
    assert(new Set(chapters.map(chapter => chapter.href)).size === chapters.length, 'duplicate chapter links');
    assert(JSON.stringify([...await feedLinks(topic + 'index.xml')].sort()) === JSON.stringify(chapters.map(chapter => chapter.href).sort()), 'series feed does not mirror the chapter list');
    assert(!await page.locator('.test-notice, .test-label').count(), 'test markers leaked into the series');

    for (const [index, chapter] of chapters.entries()) {
      await page.goto(base + chapter.href);
      assert(await page.locator('h1').count() === 1, `${chapter.href}: expected exactly one h1`);
      assert((await page.locator('h1').textContent()).trim() === chapter.title.trim(), `${chapter.href}: h1 does not match the chapter list title`);
      assert(!await page.locator('.test-notice, .test-label').count(), `${chapter.href}: test markers remain`);
      assert(!await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), `${chapter.href}: horizontal overflow at ${width}px`);

      // Every body picture keeps its reserved box, its own bundle path, its
      // original PNG link, and the aspect ratio of that original.
      const pictures = await page.locator('.prose img').evaluateAll(async images => {
        images.forEach(image => image.loading = 'eager');
        await Promise.all(images.map(image => image.decode()));
        return images.map(image => ({
          src: image.currentSrc,
          width: Number(image.getAttribute('width')),
          height: Number(image.getAttribute('height')),
          alt: image.alt,
          rendered: image.getBoundingClientRect().width,
          original: image.closest('a')?.href ?? null,
        }));
      });
      assert(pictures.length > 0, `${chapter.href}: no body pictures`);
      assert(new Set(pictures.map(picture => picture.src)).size === pictures.length, `${chapter.href}: a picture is rendered twice`);
      // The original is derived from the bundle convention
      // (<article>/assets/<name>.png next to index.md), not from a wrapper link:
      // only some chapters link the full-resolution file.
      const originalOf = picture => chapter.href + 'assets/' + decodeURIComponent(new URL(picture.src).pathname.split('/').pop()).replace(/_hu_[0-9a-f]+\.webp$/, '.png');
      for (const picture of pictures) {
        assert(picture.src.startsWith(base + chapter.href + 'assets/'), `${chapter.href}: picture outside its bundle: ${picture.src}`);
        assert(picture.width > 0 && picture.height > 0 && picture.alt, `${chapter.href}: picture without reserved size or alt: ${picture.src}`);
        assert(picture.rendered <= width - 40, `${chapter.href}: picture wider than its column: ${Math.round(picture.rendered)}px`);
        if (picture.original) {
          assert(decodeURIComponent(new URL(picture.original, base).pathname) === originalOf(picture), `${chapter.href}: original link ${picture.original} does not match the rendered picture`);
        }
      }
      const originals = await page.evaluate(async pictures => {
        const sizes = [];
        for (const picture of pictures) {
          const image = new Image();
          image.src = picture.original;
          try { await image.decode(); } catch { image.width = 0; }
          sizes.push([image.naturalWidth, image.naturalHeight]);
        }
        return sizes;
      }, pictures.map(picture => ({ original: originalOf(picture) })));
      for (const [i, picture] of pictures.entries()) {
        const [originalWidth, originalHeight] = originals[i];
        assert(originalWidth > 0 && originalHeight > 0, `${chapter.href}: original PNG missing: ${originalOf(picture)}`);
        const rendered = picture.width / picture.height;
        assert(Math.abs(rendered - originalWidth / originalHeight) < 0.01, `${chapter.href}: cropped or distorted picture ${picture.src}`);
        assert(originalWidth >= picture.width, `${chapter.href}: original PNG is not the full resolution of ${picture.src}`);
      }

      const toc = page.locator('.floating-toc');
      await toc.locator('summary').click();
      const headings = await page.locator('.prose h2, .prose h3').count();
      assert(await toc.locator('a').count() === headings, `${chapter.href}: TOC lists ${await toc.locator('a').count()} of ${headings} headings`);
      const last = toc.locator('a').last();
      const hash = await last.getAttribute('href');
      assert(await page.evaluate(value => !!document.getElementById(decodeURIComponent(value.slice(1))), hash), `${chapter.href}: TOC entry ${hash} points at nothing`);
      await last.click();
      await page.waitForFunction(value => decodeURIComponent(location.hash) === decodeURIComponent(value), hash);
      await page.waitForFunction(() => !document.querySelector('.floating-toc').open);
      await page.waitForFunction(value => document.querySelector('.toc-panel a[aria-current=location]')?.getAttribute('href') === value, hash);

      const neighbours = [chapters[index - 1], chapters[index + 1]].filter(Boolean);
      const pager = page.locator('.article-pager a');
      assert(await pager.count() === neighbours.length, `${chapter.href}: expected ${neighbours.length} previous/next link(s)`);
      const pagerLinks = await pager.evaluateAll(nodes => nodes.map(node => node.getAttribute('href')));
      for (const neighbour of neighbours) assert(pagerLinks.includes(neighbour.href), `${chapter.href}: missing ${neighbour.href} in the article pager`);

      const navigation = page.locator('.chapter-navigation');
      await navigation.locator('summary').click();
      const chapterLinks = await navigation.locator('nav a').evaluateAll(nodes => nodes.map(node => node.getAttribute('href')));
      assert(JSON.stringify(chapterLinks) === JSON.stringify(chapters.map(chapter => chapter.href)), `${chapter.href}: chapter navigation order changed`);
      assert(await navigation.locator('[aria-current=page]').getAttribute('href') === chapter.href, `${chapter.href}: active chapter not marked`);

      // Internal references (ref-N) and tables are content features of the
      // series: assert every reference resolves, without counting them.
      const references = await page.locator('.prose [id^=ref-]').evaluateAll(nodes => nodes.map(node => node.id));
      for (const id of references) {
        const link = page.locator(`.prose a[href="#${id}"]`).first();
        assert(await link.count() > 0, `${chapter.href}: reference #${id} has no link`);
        await link.click();
        await page.waitForFunction(value => location.hash === '#' + value && !!document.getElementById(value), id);
      }
      const tables = page.locator('.prose table');
      for (let i = 0; i < await tables.count(); i++) {
        assert(await tables.nth(i).locator('thead th').count() > 0, `${chapter.href}: table ${i + 1} lost its header row`);
      }
      report.push(`${width}px ${chapter.href}: ${pictures.length} pictures, ${headings} TOC entries, ${references.length} references, ${await tables.count()} table(s)`);
    }

    for (const query of [series.title, ...chapters.map(chapter => chapter.title)]) {
      await page.goto(base + '/search/?q=' + encodeURIComponent(query));
      await page.waitForFunction(() => !document.querySelector('#search-status').textContent.includes('正在搜索'));
      await page.locator('[data-filter=topics]').click();
      await page.waitForFunction(() => document.querySelectorAll('.search-result').length > 0);
      const titles = await page.locator('.search-result h2 a').allTextContents();
      assert(titles.includes(query), `search does not find ${JSON.stringify(query)}`);
    }
    report.push(`${width}px: series and every chapter are searchable under the topics filter`);

    await page.goto(base + topic);
    await page.screenshot({ path: `output/playwright/agent-series-${width}.png`, fullPage: true });
    await page.goto(base + chapters[0].href);
    await page.screenshot({ path: `output/playwright/agent-framework-${width}.png`, fullPage: true });
  }
  return report;
}
