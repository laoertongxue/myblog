#!/usr/bin/env node
/** Original editable SVG layouts; export with an installed Playwright/Chromium. No data files read. */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';
const require=createRequire(import.meta.url);
function fail(message){console.error('D19 figure renderer: '+message);process.exit(1);}
if(!process.env.FONT_PATH)fail('请设置 FONT_PATH，指向完整的 Noto Sans SC .ttf 字体文件。');
let font;
try {font=fs.readFileSync(path.resolve(process.env.FONT_PATH)).toString('base64');}
catch {fail('无法读取 FONT_PATH 指定的字体文件，请检查文件与读取权限。');}
let pw;
try {pw=process.env.PLAYWRIGHT_MODULE ? require(path.resolve(process.env.PLAYWRIGHT_MODULE)) : require('playwright');}
catch {fail('无法加载 Playwright。请使用标准 Node 模块安装，或设置 PLAYWRIGHT_MODULE 为已安装模块的绝对路径。');}
const HERE=path.dirname(fileURLToPath(import.meta.url)),ROOT=path.dirname(HERE),REPO=path.resolve(ROOT,'../..');
const OUT=path.join(ROOT,'images'),BUNDLE=path.join(REPO,'content/blog/inventory-validation-policy-freeze/images');
fs.mkdirSync(OUT,{recursive:true});
const inRepo=fs.existsSync(path.join(REPO,'hugo.toml'));
if(inRepo)fs.mkdirSync(BUNDLE,{recursive:true});
const esc=s=>s.replaceAll('&','&amp;').replaceAll('<','&lt;');
class Figure {
 constructor(name,w,h){this.name=name;this.w=w;this.h=h;this.parts=[];}
 text(x,y,s,size=36,weight=400){this.parts.push(`<text x="${x}" y="${y}" font-size="${size}" font-weight="${weight}">${esc(s)}</text>`);}
 box(y,h){this.parts.push(`<rect x="32" y="${y}" width="636" height="${h}" fill="none" stroke="black" stroke-width="2"/>`);}
 line(y){this.parts.push(`<path d="M32 ${y}H668" stroke="black" stroke-width="2"/>`);}
 arrow(y){this.parts.push(`<path d="M350 ${y}v32m-10-10 10 10 10-10" fill="none" stroke="black" stroke-width="3"/>`);}
 svg(){return `<svg xmlns="http://www.w3.org/2000/svg" width="${this.w}" height="${this.h}" viewBox="0 0 ${this.w} ${this.h}"><rect width="100%" height="100%" fill="white"/><g fill="black" font-family="Noto Sans SC, Noto Sans CJK SC, sans-serif">${this.parts.join('')}</g></svg>`;}
}
const figs=[];
let f=new Figure('d19-00_cover',900,383);
f.text(36,48,'D19  /  验证回放与冻结',28);
f.text(36,138,'同一需求 / 两种补货',64,600);
f.parts.push('<rect x="36" y="199" width="390" height="108" fill="none" stroke="black" stroke-width="2"/><rect x="474" y="199" width="390" height="108" fill="none" stroke="black" stroke-width="2"/>');
f.text(60,266,'(s, Q) 每天复核',40);f.text(498,266,'(R, S) 定期复核',40);
f.text(36,357,'教学模拟 · 先比较验证，再冻结规则',29);figs.push(f);
f=new Figure('d19-01_timing',700,1510);
f.text(32,72,'先对齐一天的事件顺序',44,600);
for(const [y,num,title,sub] of [[128,'01','日初：到货入库','只收今天到期的订单'],[363,'02','日内：按需求履约','不足即失销，不留欠交'],[598,'03','日末：复核并下单','按策略判断是否补货']]){f.box(y,180);f.text(56,y+58,`${num}  ${title}`,40);f.text(56,y+130,sub,38);if(y<598)f.arrow(y+194);}
f.text(32,857,'t 日末下单',42,600);f.text(32,924,'t + L + 1 日初到货',42);
f.box(974,120);f.text(56,1051,'L = 2 → t + 3 日初到',42);
f.line(1153);f.text(32,1223,'库存位置 IP = 现货 + 在途',39);
f.text(32,1305,'期末尚未到货的尾单',39);f.text(32,1368,'保留在途，不删除、不提前收。',36);
f.text(32,1450,'教学模拟 · 无欠交模型',36);figs.push(f);
f=new Figure('d19-02_fair-comparison',700,1380);
f.text(32,72,'公平比较，先固定共同输入',42,600);
f.box(132,346);f.text(56,195,'同一条原始需求',42);f.text(56,272,'同初始现货与在途',40);f.text(56,349,'同外生原始需求预测',40);f.text(56,425,'不拿策略销量替换需求',38);
f.arrow(496);
f.box(554,210);f.text(56,618,'(s, Q)  每天复核',44,600);f.text(56,694,'达到触发条件，订固定 Q',38);
f.box(814,210);f.text(56,878,'(R, S)  每 3 天复核',42,600);f.text(56,954,'仅复核日决定是否补到 S',38);
f.line(1090);f.text(32,1162,'比较范围：开发验证回放',40);f.text(32,1243,'可比较失销、库存与订货。',38);f.text(32,1321,'模拟结果 ≠ 真实经营收益',38);figs.push(f);
f=new Figure('d19-03_freeze',700,1530);
f.text(32,72,'分块比较，冻结后再测试',44,600);
f.box(130,180);f.text(56,194,'第 1—112 天',46,600);f.text(56,264,'训练：建立模型与候选',38);f.arrow(326);
f.box(386,230);f.text(56,450,'第 113—140 天',44,600);f.text(56,522,'验证：比较候选策略',40);f.text(56,579,'随后冻结规则与参数',38);f.arrow(632);
f.box(692,310);f.text(56,758,'D20：第 141—180 天',40,600);f.text(56,830,'预测测试范围',40);f.text(56,906,'库存只评最后 28 天',39);f.text(56,968,'即第 153—180 天',40);
f.line(1068);f.text(32,1140,'固定五日窗口不跨块',42,600);f.text(32,1214,'136—140：在验证块内',38);f.text(32,1286,'137—141：跨块，不纳入',38);
f.box(1350,120);f.text(56,1427,'今天不读取测试数据',44,600);figs.push(f);
const launch={headless:true};if(process.env.CHROME_PATH)launch.executablePath=process.env.CHROME_PATH;
const browser=await pw.chromium.launch(launch);const page=await browser.newPage({deviceScaleFactor:1});
const report=[];
for(const fig of figs){
 const svg=fig.svg();fs.writeFileSync(path.join(HERE,fig.name+'.svg'),svg+'\n');
 if(inRepo && fig.name==='d19-00_cover')fs.writeFileSync(path.join(REPO,'assets/cover-sources/d19-inventory-validation.svg'),svg+'\n');
 await page.setViewportSize({width:fig.w,height:fig.h});
 await page.setContent(`<style>@font-face{font-family:'Noto Sans SC';src:url(data:font/ttf;base64,${font})}html,body{margin:0;background:white}svg{display:block}</style>${svg}`);
 await page.evaluate(async()=>{await document.fonts.load('36px "Noto Sans SC"');await document.fonts.ready;if(!document.fonts.check('36px "Noto Sans SC"'))throw Error('FONT_PATH 字体加载失败');});
 const bounds=await page.locator('text').evaluateAll(ts=>ts.map(t=>{const b=t.getBBox();return {text:t.textContent,x:b.x,y:b.y,w:b.width,h:b.height}}));
 for(const b of bounds)if(b.x<0||b.y<0||b.x+b.w>fig.w||b.y+b.h>fig.h)throw Error('Text outside: '+JSON.stringify(b));
 for(let i=0;i<bounds.length;i++)for(let j=i+1;j<bounds.length;j++){const a=bounds[i],b=bounds[j];if(Math.min(a.x+a.w,b.x+b.w)>Math.max(a.x,b.x)&&Math.min(a.y+a.h,b.y+b.h)>Math.max(a.y,b.y))throw Error('Text overlap');}
 for(const width of [fig.w,350,280]){const h=Math.round(fig.h*width/fig.w);await page.setViewportSize({width,height:h});await page.locator('svg').evaluate((e,w)=>{e.style.width=w+'px';e.style.height='auto';},width);const dir=width===fig.w?OUT:path.join(OUT,`preview-${width}`);fs.mkdirSync(dir,{recursive:true});const p=path.join(dir,fig.name+'.png');await page.screenshot({path:p});const buf=fs.readFileSync(p);if(buf.readUInt32BE(16)!==width||buf.readUInt32BE(20)!==h)throw Error('PNG dimensions');}
 if(inRepo)fs.copyFileSync(path.join(OUT,fig.name+'.png'),path.join(BUNDLE,fig.name+'.png'));
 report.push({name:fig.name,width:fig.w,height:fig.h,textBoundsPassed:true,textOverlap:false,textBoxes:bounds});
}
await browser.close();fs.writeFileSync(path.join(HERE,'render-quality-report.json'),JSON.stringify(report,null,2)+'\n');console.log('Rendered four SVG designs and PNGs; dimensions, text bounds and overlap checks passed.');
