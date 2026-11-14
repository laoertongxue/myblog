#!/usr/bin/env node
/** Original editable SVG layouts; export with an installed Playwright/Chromium. No data files read. */
import fs from 'node:fs';
import crypto from 'node:crypto';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';
const require=createRequire(import.meta.url);
function fail(message){console.error('D21 figure renderer: '+message);process.exit(1);}
if(!process.env.FONT_PATH)fail('请设置 FONT_PATH，指向完整的 Noto Sans SC .ttf 字体文件。');
let font;
try {font=fs.readFileSync(path.resolve(process.env.FONT_PATH)).toString('base64');}
catch {fail('无法读取 FONT_PATH 指定的字体文件，请检查文件与读取权限。');}
let pw;
try {pw=process.env.PLAYWRIGHT_MODULE ? require(path.resolve(process.env.PLAYWRIGHT_MODULE)) : require('playwright');}
catch {fail('无法加载 Playwright。请使用标准 Node 模块安装，或设置 PLAYWRIGHT_MODULE 为已安装模块的绝对路径。');}
const HERE=path.dirname(fileURLToPath(import.meta.url)),ROOT=path.dirname(HERE),REPO=path.resolve(ROOT,'../..');
const OUT=path.join(ROOT,'images'),BUNDLE=path.join(REPO,'content/blog/shortest-path-routing-baseline/images');
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
let f=new Figure('d21-00_cover',900,383);
f.text(36,50,'D21  /  配送建模起步',28);
f.text(36,137,'最短路与配送方案',65,600);
f.parts.push('<rect x="36" y="194" width="828" height="112" fill="none" stroke="black" stroke-width="2"/>');
f.text(62,266,'走哪条路  ·  怎么排点  ·  谁来送',40);
f.text(36,355,'先建可行基线，再谈优化',30);figs.push(f);
f=new Figure('d21-01_levels',700,1430);
f.text(32,72,'三类问题，三层决定',44,600);
f.box(125,260);f.text(56,188,'01  两点最短路',42,600);f.text(56,263,'A 到 B，沿哪条路走？',38);f.text(56,333,'输入：路网与每段成本',36);
f.arrow(405);
f.box(465,260);f.text(56,528,'02  单车 TSP',42,600);f.text(56,603,'一辆车，先后访问哪些点？',35);f.text(56,673,'所有点访问后返回起点',36);
f.arrow(745);
f.box(805,260);f.text(56,868,'03  多车 VRP',42,600);f.text(56,943,'哪个点分给哪辆车？',38);f.text(56,1013,'还要决定各车访问顺序',36);
f.line(1127);f.text(32,1205,'容量、时间窗等约束',40,600);f.text(32,1280,'需要另行建模与检查。',37);f.text(32,1373,'会找最短路，不等于会排配送。',34);figs.push(f);
f=new Figure('d21-02_matrix',700,1510);
f.text(32,72,'矩阵连接路网与配送',43,600);
f.box(125,235);f.text(56,188,'路网：点与边',42,600);f.text(56,261,'道路连接哪些位置？',38);f.text(56,321,'每段成本是什么单位？',36);f.arrow(380);
f.box(440,235);f.text(56,503,'矩阵：两点间成本',41,600);f.text(56,576,'第 i 行、第 j 列',38);f.text(56,636,'表示从 i 到 j 的成本',36);f.arrow(695);
f.box(755,235);f.text(56,818,'路线：分车与排序',41,600);f.text(56,891,'共同决定分配与访问顺序',34);f.text(56,951,'逐段相加，包含最后回仓',35);
f.line(1055);f.text(32,1126,'经过某点 ≠ 已完成服务',40,600);f.text(32,1200,'到达、卸货和签收需有约定。',35);
f.text(32,1290,'距离、时间、箱数分开记录。',35);f.text(32,1380,'本篇矩阵为固定教学模拟。',35);f.text(32,1460,'不调用真实地图，不实际派车。',34);figs.push(f);
f=new Figure('d21-03_validation',700,1530);
f.text(32,72,'可行基线，先过这四关',42,600);
for(const [y,n,t,a,b] of [[125,'01','服务覆盖','每个配送点恰好服务一次','不能漏点，也不能重复'],[415,'02','路线闭合','从仓出发，最终回到仓','距离要包括回仓这一段'],[705,'03','载荷合法','逐车核对箱数与容量','总容量够，不代表分车正确'],[995,'04','比较公平','使用相同数据、目标与约束','不可行基线不能用于宣称降本']]){f.box(y,245);f.text(56,y+61,n+'  '+t,42,600);f.text(56,y+135,a,35);f.text(56,y+202,b,33);}
f.line(1298);f.text(32,1375,'可行 ≠ 已证明最优',42,600);f.text(32,1450,'教学结果不等于实际经营收益。',34);figs.push(f);
const launch={headless:true};if(process.env.CHROME_PATH)launch.executablePath=process.env.CHROME_PATH;
const browser=await pw.chromium.launch(launch);const page=await browser.newPage({deviceScaleFactor:1});
const report=[];
for(const fig of figs){
 const svg=fig.svg();fs.writeFileSync(path.join(HERE,fig.name+'.svg'),svg+'\n');
 if(inRepo && fig.name==='d21-00_cover')fs.writeFileSync(path.join(REPO,'assets/cover-sources/d21-routing-baseline.svg'),svg+'\n');
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
