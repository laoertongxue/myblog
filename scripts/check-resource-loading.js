// Use playwright-cli run-code against the production build served on port 1316.
async (page) => {
  const context = await page.context().browser().newContext({viewport:{width:390,height:844},deviceScaleFactor:1});
  const tab = await context.newPage();
  const requests = [];
  tab.on('request', request => requests.push(request.url()));
  const result = [];
  for (const path of ['/', '/blog/layout-test-01/']) {
    await tab.goto('http://127.0.0.1:1316'+path);
    const selector = path === '/' ? '.list-thumbnails img' : '.prose img';
    await tab.locator(selector).first().evaluate(image => image.decode());
    const images = await tab.locator(selector).evaluateAll(nodes => nodes.map(image => ({
      width:image.getAttribute('width'),height:image.getAttribute('height'),src:image.currentSrc,
      srcset:image.srcset,loading:image.loading,priority:image.fetchPriority
    })));
    if(images[0].loading !== 'eager' || images[0].priority !== 'high') throw Error('First image priority');
    if(images.some(image => !image.width || !image.height)) throw Error('Missing reserved image dimensions');
    if(images.some(image => image.srcset && !image.srcset.includes(image.src.replace('http://127.0.0.1:1316','')))) throw Error('Selected image not in srcset');
    if(await tab.locator('script[src*="search"]').count()) throw Error('Search script loaded on ordinary page');
    result.push({path,firstImage:images[0]});
  }
  if(requests.some(url => url.includes('avatar-wangye'))) throw Error('Hidden mobile avatar was downloaded');
  if(requests.some(url => url.includes('search-index'))) throw Error('Search index loaded before search');
  await tab.goto('http://127.0.0.1:1316/search/');
  if(requests.some(url => url.includes('search-index'))) throw Error('Index downloaded for empty search');
  await tab.locator('#search-query').fill('图文测试');
  await tab.locator('.search-form button').click();
  await tab.locator('.search-result').first().waitFor();
  if(!requests.some(url=>/search-index\.[a-f0-9]+\.json/.test(url))) throw Error('Missing versioned search index');
  result.push('Search code only on search page; versioned index fetched on demand');
  await context.close();
  return result;
}
