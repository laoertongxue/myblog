import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';
const require=createRequire(import.meta.url);
const {marked}=await import(require.resolve('marked'));
const {chromium}=require('playwright');
const root=path.resolve(path.dirname(new URL(import.meta.url).pathname),'..'), dir=root;
let md=fs.readFileSync(path.join(dir,'article.md'),'utf8').replace(/^---\n[\s\S]*?\n---\n/,'');
let html=marked.parse(md), heads=[], i=0;
html=html.replace(/<h2>(.*?)<\/h2>/g,(_,t)=>{const id='s'+(++i);heads.push({id,t});return `<h2 id="${id}">${t}</h2>`});
html=html.replace(/(src|href)="(images\/[^"]+)"/g,(_,attr,file)=>`${attr}="data:image/png;base64,${fs.readFileSync(path.join(dir,file)).toString('base64')}"`);
html=html.replace(/<table>/g,'<div class="table-wrap" tabindex="0" role="region" aria-label="可横向滚动的数据表"><table>').replace(/<\/table>/g,'</table></div>');
const css=`*{box-sizing:border-box}body{margin:0;color:#1a1a1a;background:#fcfbf8;font-family:"Noto Serif CJK SC","Songti SC",serif;font-size:18px;line-height:1.95}main{max-width:950px;margin:65px auto 90px;padding:0 28px}h1{font-family:"Noto Sans CJK SC",sans-serif;font-size:37px;line-height:1.5;font-weight:700;margin:0 0 27px}h2{font-family:"Noto Sans CJK SC",sans-serif;font-size:26px;line-height:1.55;margin:54px 0 22px;scroll-margin-top:24px}p{margin:0 0 22px}strong{font-family:"Noto Sans CJK SC",sans-serif;font-weight:700}a{color:inherit;text-underline-offset:4px;text-decoration-thickness:1px;overflow-wrap:anywhere}img{display:block;max-width:100%;height:auto;margin:28px auto 12px}table{border-collapse:collapse;width:100%;font-family:"Noto Sans CJK SC",sans-serif;font-size:15px;line-height:1.7;margin:12px 0 24px}th,td{border:1px solid #d0d0d0;padding:10px 13px;vertical-align:middle}th{background:#eeeeeb;text-align:left}td{font-variant-numeric:tabular-nums}td:not(:first-child),th:not(:first-child){white-space:nowrap}.table-wrap{overflow-x:auto}ul,ol{padding-left:1.5em;margin:16px 0 26px}li{margin-bottom:11px}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#efefeb;padding:18px;line-height:1.65;font-size:15px}code{font-family:monospace}nav{font-family:"Noto Sans CJK SC",sans-serif;font-size:14px;margin:24px 0 36px;padding:18px 0;border-top:1px solid #ccc;border-bottom:1px solid #ccc}nav a{display:inline-block;margin:4px 16px 4px 0}header{font-family:"Noto Sans CJK SC",sans-serif;font-size:12px;color:#666;margin-bottom:25px;letter-spacing:1px}@media(max-width:680px){body{font-size:17px}main{margin:28px auto;padding:0 20px}h1{font-size:29px}h2{font-size:23px}th,td{min-width:85px;padding:9px}nav a{display:block}}@media print{body{background:white}main{margin:0;max-width:none}h2{break-after:avoid}table,img{break-inside:avoid}a{text-decoration:none}nav{display:none}}`;
const nav='<nav aria-label="文章目录">'+heads.map(h=>`<a href="#${h.id}">${h.t}</a>`).join('')+'</nav>';
html=html.replace(/(<h1>[\s\S]*?<\/h1>)/,'$1'+nav);
const page='<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>第05篇 预测之后，究竟该订多少</title><style>'+css+'</style></head><body><main><header>供应链预测与计划 · 第05篇 · 离线阅读版 · 教学模拟</header>'+html+'</main></body></html>';
const dest=path.join(dir,'第05篇_预测之后究竟该订多少.html');fs.writeFileSync(dest,page);
if(process.argv.includes('--no-qa')) {console.log(dest);process.exit(0);}
const browser=await chromium.launch({executablePath:'/usr/bin/chromium',headless:true,args:['--no-sandbox']});
const tab=await browser.newPage({viewport:{width:1180,height:1000},deviceScaleFactor:1});
await tab.goto('file://'+dest);await tab.evaluate(()=>document.fonts.ready);
fs.mkdirSync(path.join(root,'qa'),{recursive:true});
const results={};
for (const [name,width,height] of [['desktop',1180,1000],['mobile',390,844]]) {
 await tab.setViewportSize({width,height});await tab.evaluate(()=>scrollTo(0,0));
 await tab.screenshot({path:path.join(root,`qa/${name}-top.png`)});
 for (let h of [4,6,7,9]) {await tab.locator('#s'+h).scrollIntoViewIfNeeded();await tab.screenshot({path:path.join(root,`qa/${name}-s${h}.png`)});}
 results[name]=await tab.evaluate(()=>({images:[...document.images].map(x=>({ok:x.complete&&x.naturalWidth>0,w:x.naturalWidth,h:x.naturalHeight,alt:x.alt})),overflow:document.documentElement.scrollWidth>innerWidth,brokenFragments:[...document.querySelectorAll('a[href^="#"]')].filter(x=>!document.querySelector(x.getAttribute('href'))).length,headings:document.querySelectorAll('h2').length,tables:document.querySelectorAll('table').length,textLength:document.body.innerText.length}));
}
await browser.close();fs.writeFileSync(path.join(root,'qa/html-checks.json'),JSON.stringify(results,null,2));console.log(JSON.stringify(results,null,2));
if(Object.values(results).some(r=>r.overflow||r.brokenFragments||r.images.some(x=>!x.ok)))process.exit(1);
