// Single-column layout and pagination sweep over the built site.
//
// This file is a closure, not a program: it is loaded and executed by
// scripts/run-browser-checks.mjs, which serves the build, hands over `page` and
// `ctx`, and fails the run on any pageerror / non-aborted requestfailed. Run it
// with:  npm run check:browser -- --only design
//
// Everything it asserts is derived from the build or from hugo.toml
// (ctx.pagerSize, ctx.rssCount) rather than from hardcoded counts, so growing
// the content does not turn this check red.
async (page, ctx) => {
  const { base, assert, pagerSize, walkPagination, rssCount } = ctx;
  const report = [];
  const { readFile, readdir } = await import('node:fs/promises');
  const checkedSources = new Map();
  const checkedCandidates = new Map();
  const checkOriginal = async (image, label) => {
    assert(image.originalSrc, `${label}: image is missing its original source: ${image.src}`);
    const url = new URL(image.originalSrc, base);
    let source = checkedSources.get(url.href);
    if (!source) {
      const response = await page.request.get(url.href);
      assert(response.ok(), `${label}: original source returned HTTP ${response.status()}: ${url.href}`);
      const size = await page.evaluate(async value => {
        const picture = new Image();
        picture.src = value;
        try { await picture.decode(); } catch { return null; }
        return [picture.naturalWidth, picture.naturalHeight];
      }, url.href);
      assert(size && size[0] > 0 && size[1] > 0, `${label}: original source failed to decode: ${url.href}`);
      source = { width: size[0], height: size[1] };
      checkedSources.set(url.href, source);
    }
    if (image.cover || image.listing) {
      assert(source.width === 900 && source.height === 383, `${label}: cover source must be 900x383, got ${source.width}x${source.height}: ${url.href}`);
    }
    if (image.originalWidth || image.originalHeight) {
      assert(image.originalWidth === source.width && image.originalHeight === source.height, `${label}: original size metadata disagrees with decoded source: ${url.href}`);
    }
    if (image.intrinsicWidth > 0) assert(Math.abs(image.intrinsicHeight - image.intrinsicWidth * source.height / source.width) <= 1, `${label}: processed image changed its original proportions: ${image.src}`);
    // srcset images expose density-corrected natural sizes. Decode the chosen
    // file without srcset so rounding is checked against its encoded pixels.
    const candidateUrl = new URL(image.currentSrc || image.src, base).href;
    let candidate = checkedCandidates.get(candidateUrl);
    if (!candidate) {
      candidate = await page.evaluate(async value => {
        const picture = new Image();
        picture.src = value;
        try { await picture.decode(); } catch { return null; }
        return [picture.naturalWidth, picture.naturalHeight];
      }, candidateUrl);
      assert(candidate && candidate[0] > 0 && candidate[1] > 0, `${label}: selected candidate failed to decode: ${candidateUrl}`);
      checkedCandidates.set(candidateUrl, candidate);
    }
    assert(Math.abs(candidate[1] - candidate[0] * source.height / source.width) <= 1, `${label}: selected candidate changed the source proportions: ${candidateUrl}`);

  };
  // Check covers on every built page; other body pictures keep their own
  // dimensions and are checked only for successful, proportional rendering.
  await page.goto(base);
  const checkBuiltSources = async directory => {
    for (const entry of await readdir(directory, { withFileTypes: true })) {
      const file = `${directory}/${entry.name}`;
      if (entry.isDirectory()) {
        await checkBuiltSources(file);
      } else if (entry.name.endsWith('.html')) {
        const pictures = await page.evaluate(html => {
          const doc = new DOMParser().parseFromString(html, 'text/html');
          return [...doc.querySelectorAll('img[data-original-src]')].map(image => ({
            src: image.getAttribute('src'),
            listing: !!image.closest('.list-thumbnails'),
            cover: image.matches('.article-cover') || (!doc.querySelector('.article-cover') && image === doc.querySelector('.reading-page .prose img')),
            originalSrc: image.dataset.originalSrc,
            originalWidth: Number(image.dataset.originalWidth),
            originalHeight: Number(image.dataset.originalHeight),
            intrinsicWidth: Number(image.getAttribute('width')),
            intrinsicHeight: Number(image.getAttribute('height')),
          }));
        }, await readFile(file, 'utf8'));
        for (const image of pictures) await checkOriginal(image, file);
      }
    }
  };
  await checkBuiltSources(ctx.dir);
  const checkPager = async (label, expected = null) => {
    const pager = page.locator('.article-pager');
    if (!await pager.count()) {
      if (expected) assert(!expected.previous && !expected.next, `${label}: article pager is missing`);
      return;
    }
    assert(await pager.count() === 1, `${label}: duplicate article pagers`);
    const slots = await pager.evaluate(node => [...node.children].map(slot => {
      const rect = slot.getBoundingClientRect();
      return {
        className: slot.className, left: rect.left, right: rect.right,
        top: rect.top, width: rect.width, align: getComputedStyle(slot).textAlign,
        links: [...slot.querySelectorAll('a')].map(link => link.getAttribute('href')),
      };
    }));
    assert(slots.length === 2 && slots[0].className === 'article-prev' && slots[1].className === 'article-next', `${label}: previous/next must keep two ordered slots, including empty edges`);
    const [previous, next] = slots;
    assert(previous.width > 0 && next.width > 0 && Math.abs(previous.width - next.width) <= 1, `${label}: pager columns must keep equal space`);
    assert(Math.abs(previous.top - next.top) <= 1 && previous.right <= next.left, `${label}: pager must remain in one left/right row`);
    assert(['left', 'start'].includes(previous.align) && ['right', 'end'].includes(next.align), `${label}: pager text must align to previous-left and next-right`);
    assert(previous.links.length <= 1 && next.links.length <= 1, `${label}: a pager slot contains multiple article links`);
    if (expected) {
      assert(JSON.stringify(previous.links) === JSON.stringify(expected.previous ? [expected.previous] : []), `${label}: previous link moved out of the left slot`);
      assert(JSON.stringify(next.links) === JSON.stringify(expected.next ? [expected.next] : []), `${label}: next link moved out of the right slot`);
    }
  };
  const routes = ['/', '/blog/', '/weekly/', '/topics/', '/topics/agent-engineering/', '/topics/agent-engineering/01-agent-framework/', '/topics/agent-engineering/02-harness/', '/about/', '/now/', '/links/', '/archive/', '/search/', '/copyright/', '/tags/', '/categories/', '/404.html'];
  const articleRoutes = ['/topics/agent-engineering/01-agent-framework/', '/topics/agent-engineering/02-harness/'];

  for (const width of [1440, 1920, 768, 390, 320]) {
    await page.setViewportSize({ width, height: 960 });
    for (const path of routes) {
      const response = await page.goto(base + path);
      assert(response.status() === 200, `${path}: HTTP ${response.status()}`);
      const state = await page.evaluate(async () => {
        const pictures = [...document.images];
        pictures.forEach(image => image.loading = 'eager');
        await Promise.all(pictures.map(image => image.decode().catch(() => {})));
        // Resolve the design token through a probe element so the assertion
        // follows --lab-paper instead of repeating its hex value.
        const probe = document.createElement('span');
        probe.style.color = getComputedStyle(document.documentElement).getPropertyValue('--lab-paper').trim();
        document.body.append(probe);
        const paper = getComputedStyle(probe).color;
        probe.remove();
        const reading = document.querySelector('.reading-page');
        const workspace = document.querySelector('.site-workspace');
        const main = document.querySelector('main');
        return {
          overflow: document.documentElement.scrollWidth > innerWidth,
          badImages: pictures.filter(image => !image.naturalWidth).map(image => image.src),
          imageFrames: [...document.querySelectorAll('.list-thumbnails img, .article-cover, .prose img')].map(image => {
            const rect = image.getBoundingClientRect();
            return {
              src: image.src, currentSrc: image.currentSrc, width: rect.width, height: rect.height,
              listing: !!image.closest('.list-thumbnails'),
              cover: image.matches('.article-cover') || (!document.querySelector('.article-cover') && image === document.querySelector('.reading-page .prose img')),
              columnWidth: (image.closest('.prose') || image.closest('article'))?.getBoundingClientRect().width || 0,
              intrinsicWidth: Number(image.getAttribute('width')) || image.naturalWidth,
              intrinsicHeight: Number(image.getAttribute('height')) || image.naturalHeight,
              originalSrc: image.dataset.originalSrc,
              originalWidth: Number(image.dataset.originalWidth),
              originalHeight: Number(image.dataset.originalHeight),
              fit: getComputedStyle(image).objectFit,
            };
          }),
          mainCount: document.querySelectorAll('main').length,
          // A single-column layout means one <main> and its footer inside the
          // workspace; a reintroduced sidebar would add a third child or squeeze
          // the column.
          workspaceChildren: [...workspace.children].map(node => node.tagName),
          mainWidthRatio: main.getBoundingClientRect().width / workspace.getBoundingClientRect().width,
          paper,
          background: getComputedStyle(document.body).backgroundColor,
          hasReading: !!reading,
          readingAligned: !reading || Math.abs(reading.getBoundingClientRect().left - workspace.getBoundingClientRect().left) < 1,
        };
      });
      assert(!state.overflow, `${width} ${path}: horizontal overflow`);
      assert(!state.badImages.length, `${width} ${path}: images failed to decode: ${state.badImages.join(', ')}`);
      for (const image of state.imageFrames) {
        const ratio = image.listing ? 383 / 900 : image.intrinsicHeight / image.intrinsicWidth;
        const expected = image.listing ? '900x383 list frame' : 'intrinsic article image ratio';
        assert(image.width > 0 && Math.abs(image.height - image.width * ratio) <= 1, `${width} ${path}: expected ${expected}, got ${image.width}x${image.height}: ${image.src}`);
        assert(image.fit === 'contain', `${width} ${path}: image must scale without cropping or distortion: ${image.src}`);
        if (!image.listing) assert(Math.abs(image.width - image.columnWidth) <= 1, `${width} ${path}: article image must fill its reading column: ${image.src}`);
        await checkOriginal(image, `${width} ${path}`);
      }
      assert(state.mainCount === 1, `${width} ${path}: expected exactly one <main>, found ${state.mainCount}`);
      assert(JSON.stringify(state.workspaceChildren) === JSON.stringify(['MAIN', 'FOOTER']), `${width} ${path}: single-column workspace contains ${state.workspaceChildren.join(' + ')}`);
      assert(state.mainWidthRatio >= 0.99, `${width} ${path}: the main column only spans ${(state.mainWidthRatio * 100).toFixed(1)}% of the workspace`);
      assert(state.background === state.paper, `${width} ${path}: body background ${state.background} does not follow the --lab-paper token (${state.paper})`);
      assert(state.readingAligned, `${width} ${path}: reading column is not aligned with the workspace`);
      assert(state.hasReading === articleRoutes.includes(path), `${width} ${path}: .reading-page presence does not match the template`);
      if (state.hasReading) await checkPager(`${width} ${path}`);
    }
    report.push(`${width}px: ${routes.length} routes, no overflow, every picture decoded, single column, design tokens applied`);
  }

  for (const width of [1440, 390]) {
    await page.setViewportSize({ width, height: 960 });
    const home = await walkPagination(page, { path: '/', rowSelector: '.home-feed .post-row' });
    if (home.pages > 1) {
      assert(await page.locator('.feed-pagination [rel=prev]').count() > 0, 'last home page has no previous arrow');
      await page.locator('.feed-pagination [rel=prev]').click();
      await page.waitForFunction(expected => document.querySelector('.feed-pagination [aria-current=page]')?.textContent.trim() === String(expected), home.pages - 1);
      await page.goto(base);
    }
    await page.screenshot({ path: `output/playwright/single-column-${width}.png` });
    if (home.pages > 3) assert(await page.locator('.pagination-gap').count() > 0, 'collapsed middle pages show no ellipsis');
    report.push(`${width}px: ${home.pages} numbered home page(s), ${home.links.length} unique articles, ${pagerSize} per page`);

    for (const listing of ['/blog/', '/weekly/', '/topics/agent-engineering/']) {
      const walked = await walkPagination(page, { path: listing });
      if (listing === '/topics/agent-engineering/') assert(walked.links.length > 0, `${listing}: no articles listed`);
    }
    report.push(`Blog, Weekly and topic listings paginate at ${pagerSize} with unique articles`);

    await page.goto(base + '/topics/agent-engineering/');
    const chapters = await rssCount('/topics/agent-engineering/index.xml');
    const rows = await page.locator('.post-row').count();
    assert(rows === Math.min(chapters, pagerSize), `topic list shows ${rows} rows but its feed advertises ${chapters} chapters`);
    assert((await page.locator('.feed-pagination').count() > 0) === (chapters > pagerSize), 'topic pagination does not follow the chapter count');
    report.push(`Topic list and its feed agree on ${chapters} chapter(s)`);
  }

  // Discover every published blog article through pagination, then inspect all
  // its inline images. Lead pictures are covers; optional original links
  // supplement full-width body pictures without constraining their dimensions.
  const blogs = await walkPagination(page, { path: '/blog/' });
  const blogImageReports = [];
  for (const width of [1440, 390, 320]) {
    await page.setViewportSize({ width, height: 960 });
    let pictureCount = 0;
    let sourceCount = 0;
    for (const [index, path] of blogs.links.entries()) {
      const response = await page.goto(base + path);
      assert(response.status() === 200, `${path}: HTTP ${response.status()}`);
      const state = await page.evaluate(async () => {
        const pictures = [...document.images];
        pictures.forEach(image => image.loading = 'eager');
        await Promise.all(pictures.map(image => image.decode().catch(() => {})));
        return {
          overflow: document.documentElement.scrollWidth > innerWidth,
          badImages: pictures.filter(image => !image.naturalWidth).map(image => image.src),
          images: [...document.querySelectorAll('.article-cover, .prose img')].map(image => {
            const rect = image.getBoundingClientRect();
            return {
              src: image.src, currentSrc: image.currentSrc, width: rect.width, height: rect.height,
              left: rect.left, right: rect.right,
              cover: image.matches('.article-cover') || (!document.querySelector('.article-cover') && image === document.querySelector('.reading-page .prose img')),
              columnWidth: (image.closest('.prose') || image.closest('article')).getBoundingClientRect().width,
              intrinsicWidth: Number(image.getAttribute('width')) || image.naturalWidth,
              intrinsicHeight: Number(image.getAttribute('height')) || image.naturalHeight,
              naturalWidth: image.naturalWidth, naturalHeight: image.naturalHeight,
              originalSrc: image.dataset.originalSrc,
              originalWidth: Number(image.dataset.originalWidth),
              originalHeight: Number(image.dataset.originalHeight),
              fit: getComputedStyle(image).objectFit,
              original: image.closest('a')?.href || null,
            };
          }),
        };
      });
      assert(!state.overflow, `${width} ${path}: horizontal overflow`);
      assert(!state.badImages.length, `${width} ${path}: images failed to decode: ${state.badImages.join(', ')}`);
      await checkPager(`${width} ${path}`, { previous: blogs.links[index + 1], next: blogs.links[index - 1] });
      for (const image of state.images) {
        const ratio = image.intrinsicHeight / image.intrinsicWidth;
        assert(image.width > 0 && image.height > 0 && Math.abs(image.height - image.width * ratio) <= 1, `${width} ${path}: inline image lost its intrinsic ratio: ${image.src}`);
        assert(image.fit === 'contain', `${width} ${path}: inline image must remain complete: ${image.src}`);
        assert(Math.abs(image.width - image.columnWidth) <= 1, `${width} ${path}: article image must fill its reading column: ${image.src}`);
        assert(image.left >= -1 && image.right <= width + 1, `${width} ${path}: inline image extends beyond the viewport: ${image.src}`);
        await checkOriginal(image, `${width} ${path}`);
        if (image.original) {
          const original = new URL(image.original);
          assert(original.href === new URL(image.originalSrc, base).href && !/_hu_[0-9a-f]+\./.test(original.pathname), `${width} ${path}: figure link must preserve its unprocessed source: ${image.original}`);
          sourceCount++;
        }
        pictureCount++;
      }
    }
    blogImageReports.push(`${width}px: ${blogs.links.length} blog article(s), ${pictureCount} inline image(s) preserve intrinsic proportions, ${sourceCount} source link(s), no overflow`);
  }

  await page.setViewportSize({ width: 1440, height: 960 });
  await page.goto(base + '/topics/agent-engineering/01-agent-framework/');
  const toc = page.locator('.floating-toc');
  await toc.locator('summary').click();
  const last = toc.locator('a').last();
  const href = await last.getAttribute('href');
  assert(await page.evaluate(value => !!document.getElementById(decodeURIComponent(value.slice(1))), href), `TOC entry ${href} points at nothing`);
  await last.click();
  await page.waitForFunction(hash => decodeURIComponent(location.hash) === decodeURIComponent(hash), href);
  await page.waitForFunction(() => !document.querySelector('.floating-toc').open);
  await page.waitForFunction(hash => document.querySelector('.toc-panel a[aria-current=location]')?.getAttribute('href') === hash, href);
  await toc.locator('summary').click();
  await page.keyboard.press('Escape');
  assert(await toc.getAttribute('open') === null, 'Escape did not close the TOC');
  await toc.locator('summary').click();
  await page.locator('.article-heading h1').click();
  assert(await toc.getAttribute('open') === null, 'Outside click did not close the TOC');
  await page.screenshot({ path: 'output/playwright/single-article-1440.png' });
  report.push('TOC opens, jumps, highlights, and closes on Escape and outside click');

  // Search a title that the generated index really contains, then narrow it to
  // its section: no hardcoded query string or section assumption.
  const indexHref = await page.goto(base + '/search/').then(() => page.locator('.search-page').getAttribute('data-index'));
  const index = await (await fetch(base + indexHref)).json();
  const sample = index[0];
  const labels = { blog: '博客', weekly: 'Weekly', topics: '专题' };
  assert(sample, 'search index carries no item to search for');
  await page.goto(`${base}/search/?q=${encodeURIComponent(sample.title)}`);
  await page.waitForFunction(() => document.querySelectorAll('.search-result').length > 0);
  await page.locator(`[data-filter=${sample.section}]`).click();
  await page.waitForFunction(expected => [...document.querySelectorAll('.result-kind')].every(node => node.textContent === expected), labels[sample.section]);
  report.push(`Search and the ${sample.section} filter work for the indexed title ${JSON.stringify(sample.title)}`);

  const noJsContext = await page.context().browser().newContext({ javaScriptEnabled: false, viewport: { width: 390, height: 844 } });
  const fallback = await noJsContext.newPage();
  await fallback.goto(base);
  if (await fallback.locator('.feed-pagination [rel=next]').count()) {
    await fallback.locator('.feed-pagination [rel=next]').click();
    const rows = await fallback.locator('.post-row').count();
    assert(rows === pagerSize, `without JavaScript the next page shows ${rows} of ${pagerSize} articles`);
  }
  await noJsContext.close();
  report.push('Numbered pagination works without JavaScript');

  // content/about/index.md is the only page that turns the intro block on, and
  // that block is the only place the avatar is rendered at all. Assert the
  // whole chain, so the flag and the template cannot drift apart unnoticed.
  await page.goto(base + '/about/');
  const intro = page.locator('.about-intro');
  assert(await intro.count() === 1, 'aboutIntro is set on /about/ but no intro block was rendered');
  const avatar = intro.locator('img');
  assert(await avatar.count() === 1, 'the about intro rendered without the avatar');
  const avatarSrc = await avatar.getAttribute('src');
  assert(/_hu_[0-9a-f]+\./.test(avatarSrc), `the avatar bypasses the image pipeline: ${avatarSrc}`);
  assert(await avatar.evaluate(node => node.complete && node.naturalWidth > 0), `the avatar did not load: ${avatarSrc}`);
  assert(await avatar.getAttribute('width') === '120' && await avatar.getAttribute('height') === '120', 'the avatar must reserve its rendered square');
  report.push('About intro renders the pipelined avatar through aboutIntro');
  report.push(`${blogImageReports.join('; ')}; ${checkedSources.size} distinct original source(s) decoded with preserved proportions; every cover is 900x383`);
  return report;
}
