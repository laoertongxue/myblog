from pathlib import Path
import subprocess
script=r'''async (page) => {
const report=[];
for (const width of [1440,390,320]) {
 await page.setViewportSize({width,height:1000});
 await page.evaluate(()=>window.scrollTo(0,0));
 await page.screenshot({path:`output/playwright/d12-${width}-top.png`});
 const tables=page.getByRole('region').filter({has:page.getByRole('table')});
 if (await tables.count() !== 4) throw new Error('Expected four metric tables');
 const sizes=[];
 for(let i=0;i<4;i++) {
  await tables.nth(i).scrollIntoViewIfNeeded();
  sizes.push(await tables.nth(i).evaluate(el=>({client:el.clientWidth,scroll:el.scrollWidth,tabindex:el.tabIndex})));
 }
 if(width<700 && !sizes.every(s=>s.scroll>s.client && s.tabindex===0)) throw new Error('Mobile tables must scroll and be keyboard focusable');
 const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth);
 if(overflow) throw new Error('Page overflow');
 await tables.nth(0).scrollIntoViewIfNeeded();
 await page.screenshot({path:`output/playwright/d12-${width}-table.png`});
 for(const img of await page.getByRole('img').all()) {await img.scrollIntoViewIfNeeded(); await img.evaluate(el=>el.decode());}
 const images=await page.getByRole('img').evaluateAll(els=>els.map(e=>({src:e.currentSrc,w:e.naturalWidth,h:e.naturalHeight,loaded:e.complete})));
 if(images.some(i=>!i.loaded||!i.w)) throw new Error('Unloaded image');
 report.push({width,overflow,tables:sizes,images});
}
return report;
}'''
r=subprocess.run(['/Users/laoer/.npm/_npx/31e32ef8478fbf80/node_modules/.bin/playwright-cli','-s=d12-review','run-code',script],text=True,capture_output=True)
Path('docs/d12-review/browser-review.txt').write_text(r.stdout+r.stderr)
print(r.stdout+r.stderr)
raise SystemExit(r.returncode)
