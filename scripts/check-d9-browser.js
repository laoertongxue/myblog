async (page, ctx) => {
  const {base,assert}=ctx;
  const route='/blog/seasonal-naive-demand-forecast/';
  const report=[];
  const imageURLs=new Set();
  for(const width of [1440,390,320]){
    await page.setViewportSize({width,height:900});
    const response=await page.goto(base+route);
    assert(response.status()===200,'D9 route unavailable');
    const metadata=await page.evaluate(()=>({
      title:document.title,canonical:document.querySelector('link[rel=canonical]')?.href,
      h1:document.querySelector('h1')?.textContent,
      robots:document.querySelector('meta[name=robots]')?.content,
      author:document.querySelector('.article-meta [rel=author]')?.textContent,
      date:document.querySelector('.article-meta time')?.getAttribute('datetime'),
      overflow:document.documentElement.scrollWidth>innerWidth+1,
      tables:[...document.querySelectorAll('.prose table')].map(t=>({right:t.getBoundingClientRect().right,scroll:t.scrollWidth,client:t.clientWidth})),
    }));
    assert(!metadata.overflow,`${width}: D9 page overflow`);
    const tables=await page.locator('.d9-table-scroll').evaluateAll(nodes=>nodes.map(n=>{
      const before=n.scrollLeft;n.scrollLeft=1000;
      const moved=n.scrollLeft;n.scrollLeft=before;
      return {scroll:n.scrollWidth,client:n.clientWidth,moved,focus:n.tabIndex};
    }));
    assert(tables.length===2 && tables.every(t=>t.focus===0),'D9 accessible table wrappers missing');
    if(width<=390) assert(tables.every(t=>t.scroll>t.client && t.moved>0),`${width}: D9 table cannot scroll`);
    assert(metadata.canonical==='https://12lab.cn'+route,'canonical mismatch');
    assert(metadata.author && metadata.date.startsWith('2026-11-02'),'article author/date missing');
    assert(!metadata.robots?.includes('noindex'),'D9 accidentally noindex');
    const images=page.locator('.prose img');
    assert(await images.count()===5,'D9 requires one cover plus four explanatory figures');
    for(const img of await images.all()){
      await img.scrollIntoViewIfNeeded();
      await img.evaluate(async n=>{await n.decode()});
      const data=await img.evaluate(n=>({alt:n.alt,src:n.currentSrc,original:n.dataset.originalSrc,
        width:n.naturalWidth,height:n.naturalHeight,display:n.getBoundingClientRect().width/n.getBoundingClientRect().height,
        sources:[...n.parentElement.querySelectorAll('source')].flatMap(s=>s.srcset.split(',').map(v=>v.trim().split(' ')[0])),
        srcset:n.srcset.split(',').filter(Boolean).map(v=>v.trim().split(' ')[0])}));
      assert(data.alt.length>10,'missing descriptive D9 alt');
      assert(Math.abs(data.display-data.width/data.height)<.02,'D9 body image cropped/distorted');
      for(const url of [data.src,data.original,...data.srcset,...data.sources].filter(Boolean)) imageURLs.add(new URL(url,base).href);
    }
    const pager=await page.locator('.article-pager').evaluate(n=>({
      prev:n.querySelector('.article-prev')?.getBoundingClientRect().x,
      next:n.querySelector('.article-next')?.getBoundingClientRect().x,
      href:n.querySelector('.article-prev a')?.getAttribute('href'),
    }));
    assert(pager.prev<pager.next && pager.href==='/blog/supply-chain-metrics-evidence-package/',`${width}: previous/next placement changed`);
    report.push(`${width}px: metadata, five images, tables, pager, no overflow`);
  }
  // Older articles move to later home pages as new posts are published.
  // Validate uniqueness across the real pager, then inspect the actual row.
  const homeEntries=await ctx.walkPagination(page,{path:'/'});
  assert(homeEntries.links.filter(link=>link===route).length===1,'D9 absent/duplicated across home pages');
  await page.goto(base+'/');
  const homeRow=page.locator('.post-row').filter({has:page.locator(`h2 a[href="${route}"]`)});
  for(let current=1;current<homeEntries.pages && await homeRow.count()===0;current++){
    const next=page.locator('.feed-pagination [rel=next]');
    assert(await next.count()===1,'D9 home pagination ended before its row');
    await next.click();
    await page.waitForFunction(expected=>document.querySelector('.feed-pagination [aria-current=page]')?.textContent.trim()===String(expected),current+1);
  }
  assert(await homeRow.count()===1,'D9 row missing from its home pagination');
  assert(await homeRow.locator('img').count()===1,'D9 home has extra covers');
  const cover=homeRow.locator('img');
  for(const url of await cover.evaluate(n=>[n.src,n.dataset.originalSrc,...n.srcset.split(',').map(v=>v.trim().split(' ')[0])])){
    imageURLs.add(new URL(url,base).href);
  }
  // Fetch and decode original PNGs plus every responsive candidate actually emitted.
  const colors=await page.evaluate(async urls=>{
    const rows=[];
    for(const url of urls){
      const response=await fetch(url);
      if(!response.ok) throw new Error('image fetch failed '+url);
      const bitmap=await createImageBitmap(await response.blob());
      const canvas=document.createElement('canvas');canvas.width=bitmap.width;canvas.height=bitmap.height;
      const context=canvas.getContext('2d');context.drawImage(bitmap,0,0);
      const pixels=context.getImageData(0,0,canvas.width,canvas.height).data;
      let colored=0;
      for(let i=0;i<pixels.length;i+=4) if(pixels[i]!==pixels[i+1]||pixels[i+1]!==pixels[i+2]) colored++;
      rows.push({url,width:bitmap.width,height:bitmap.height,colored});
    }
    return rows;
  },[...imageURLs]);
  assert(colors.every(r=>r.colored===0),'D9 original/derived image has non-grayscale pixels');
  assert(colors.some(r=>r.url.endsWith('d9-00_cover.png') && r.width===900 && r.height===383),'D9 cover pixel size mismatch');
  await page.goto(base+route);
  const downloads=await page.locator('.prose a[href$=".zip"]').evaluateAll(a=>a.map(n=>n.getAttribute('href')));
  assert(downloads.length===3,'D9 download links missing');
  for(const url of downloads){
    const response=await page.request.get(base+url);
    const bytes=await response.body();
    assert(response.ok() && bytes[0]===80 && bytes[1]===75,`ZIP invalid ${url}`);
  }
  await page.goto(base+'/categories/');
  const category=page.locator('a').filter({hasText:'供应链'}).first();
  assert(await category.count()===1,'supply-chain category missing');
  const categoryRoute=await category.getAttribute('href');
  const entries=await ctx.walkPagination(page,{path:categoryRoute});
  assert(entries.links ? entries.links.includes(route) : entries.includes(route),'D9 missing from supply-chain category');
  report.push(`${colors.length} original/responsive image candidates: R=G=B; 3 ZIPs; unique home pagination row/category navigation`);
  return report;
}
