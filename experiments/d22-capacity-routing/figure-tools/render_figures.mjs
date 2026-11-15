#!/usr/bin/env node
/** Original editable SVG layouts; export with an installed Playwright/Chromium. No data files read. */
import fs from 'node:fs';
import crypto from 'node:crypto';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';
const require=createRequire(import.meta.url);
function fail(message){console.error('D22 figure renderer: '+message);process.exit(1);}
if(!process.env.FONT_PATH)fail('请设置 FONT_PATH，指向完整的 Noto Sans SC .ttf 字体文件。');
let font;
try {font=fs.readFileSync(path.resolve(process.env.FONT_PATH)).toString('base64');}
catch {fail('无法读取 FONT_PATH 指定的字体文件，请检查文件与读取权限。');}
let pw;
try {pw=process.env.PLAYWRIGHT_MODULE ? require(path.resolve(process.env.PLAYWRIGHT_MODULE)) : require('playwright');}
catch {fail('无法加载 Playwright。请使用标准 Node 模块安装，或设置 PLAYWRIGHT_MODULE 为已安装模块的绝对路径。');}
const HERE=path.dirname(fileURLToPath(import.meta.url)),ROOT=path.dirname(HERE),REPO=path.resolve(ROOT,'../..');
const OUT=path.join(ROOT,'images'),BUNDLE=path.join(REPO,'content/blog/capacity-constrained-routing/images');
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
let f=new Figure('d22-00_cover',900,383);
f.text(36,50,'D22  /  容量约束车辆路径',28);
f.text(36,137,'车装得下，路线才成立',58,600);
f.parts.push('<rect x="36" y="194" width="828" height="112" fill="none" stroke="black" stroke-width="2"/>');
f.text(62,266,'先验可行  ·  再比距离  ·  不冒称最优',34);
f.text(36,355,'纯配送模拟：从分车到独立验收',30);figs.push(f);
f=new Figure('d22-01_load',700,1410);
f.text(32,72,'累计送出 ≠ 车上剩余',42,600);
f.box(125,230);f.text(56,186,'出仓：装好本车全部货物',35,600);f.text(56,260,'累计送出 0 箱',40);f.text(56,324,'车上剩余 10 箱',40);
f.arrow(375);
f.box(435,230);f.text(56,496,'第一站：交付 2 箱之后',35,600);f.text(56,570,'累计送出 2 箱',40);f.text(56,634,'车上剩余 8 箱',40);
f.arrow(685);
f.box(745,230);f.text(56,806,'最后一站：全部交付之后',35,600);f.text(56,880,'累计送出 10 箱',40);f.text(56,944,'车上剩余 0 箱',40);
f.line(1040);f.text(32,1115,'图中统一使用「服务后」时点。',34,600);f.text(32,1190,'CumulVar 的到站值不能直接',34);f.text(32,1255,'当作该站服务后的累计送出。',34);f.text(32,1355,'仅限纯配送：不取货、不重装。',34);figs.push(f);
f=new Figure('d22-02_counterexample',700,1390);
f.text(32,72,'总容量够，也可能装不下',40,600);
f.box(125,230);f.text(56,188,'3 个配送点，每点 6 箱',38,600);f.text(56,270,'总需求：6 + 6 + 6 = 18 箱',32);f.text(56,326,'每个点不可拆分给多辆车',34);
f.box(410,230);f.text(56,473,'2 辆车，每车容量 10 箱',36,600);f.text(56,555,'总容量：10 + 10 = 20 箱',32);f.text(56,611,'每车只跑一趟，途中不重装',32);
f.box(695,260);f.text(56,758,'但一辆车不能接两个点',36,600);f.text(56,840,'6 + 6 = 12 箱 > 10 箱',34);f.text(56,913,'两辆车最多服务两个点',35);
f.line(1020);f.text(32,1090,'总需求 ≤ 总容量',40,600);f.text(32,1155,'只是必要条件。',36,600);f.text(32,1220,'必须能把每个点分配给车辆，',34);f.text(32,1280,'并满足每辆车自己的容量。',34);f.text(32,1340,'这个反例可用分配逻辑证明不可行。',30);figs.push(f);
f=new Figure('d22-03_checks',700,1530);
f.text(32,72,'先验可行，再比较距离',42,600);
for(const [y,n,t,a,b] of [[125,'01','服务覆盖','每点恰好服务一次','不可漏点、重复或拆单'],[390,'02','闭合路线','从仓出发，最终回仓','最后一段也要计入距离'],[655,'03','逐车容量','分别核对每辆车的箱数','总容量检查不能替代分车'],[920,'04','公平比较','同一矩阵、需求与约束','基线与新路线都必须可行']]){f.box(y,220);f.text(56,y+57,n+'  '+t,39,600);f.text(56,y+128,a,34);f.text(56,y+190,b,32);}
f.line(1200);f.text(32,1280,'可行 ≠ 已证明最优',40,600);f.text(32,1360,'超时无解 ≠ 已证不可行',38,600);f.text(32,1460,'模拟里程差不等于实际经营收益。',32);figs.push(f);
const launch={headless:true};if(process.env.CHROME_PATH)launch.executablePath=process.env.CHROME_PATH;
const browser=await pw.chromium.launch(launch);const page=await browser.newPage({deviceScaleFactor:1});
const report=[];
for(const fig of figs){
 const svg=fig.svg();fs.writeFileSync(path.join(HERE,fig.name+'.svg'),svg+'\n');
 if(inRepo && fig.name==='d22-00_cover')fs.writeFileSync(path.join(REPO,'assets/cover-sources/d22-capacity-routing.svg'),svg+'\n');
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
