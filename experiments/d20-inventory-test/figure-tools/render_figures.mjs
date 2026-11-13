#!/usr/bin/env node
/** Original editable SVG layouts; export with an installed Playwright/Chromium. No data files read. */
import fs from 'node:fs';
import crypto from 'node:crypto';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';
const require=createRequire(import.meta.url);
function fail(message){console.error('D20 figure renderer: '+message);process.exit(1);}
if(!process.env.FONT_PATH)fail('请设置 FONT_PATH，指向完整的 Noto Sans SC .ttf 字体文件。');
let font;
try {font=fs.readFileSync(path.resolve(process.env.FONT_PATH)).toString('base64');}
catch {fail('无法读取 FONT_PATH 指定的字体文件，请检查文件与读取权限。');}
let pw;
try {pw=process.env.PLAYWRIGHT_MODULE ? require(path.resolve(process.env.PLAYWRIGHT_MODULE)) : require('playwright');}
catch {fail('无法加载 Playwright。请使用标准 Node 模块安装，或设置 PLAYWRIGHT_MODULE 为已安装模块的绝对路径。');}
const HERE=path.dirname(fileURLToPath(import.meta.url)),ROOT=path.dirname(HERE),REPO=path.resolve(ROOT,'../..');
const OUT=path.join(ROOT,'images'),BUNDLE=path.join(REPO,'content/blog/inventory-test-stockout-tradeoff/images');
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
let f=new Figure('d20-00_cover',900,383);
f.text(36,50,'D20  /  冻结后的测试',28);
f.text(36,138,'库存与缺货 / 如何取舍',61,600);
f.parts.push('<rect x="36" y="195" width="828" height="112" fill="none" stroke="black" stroke-width="2"/>');
f.text(62,266,'相同起点  ·  固定规则  ·  如实报告',40);
f.text(36,355,'教学模拟 / 不用测试结果重新挑参数',29);figs.push(f);
f=new Figure('d20-01_boundary',700,1450);
f.text(32,72,'冻结后，各评哪一段？',44,600);
f.box(124,240);f.text(56,184,'预测：第 141—180 天',41,600);f.text(56,252,'固定五日评价窗口',39);f.text(56,316,'完整落在测试块内',39);
f.arrow(384);
f.box(444,310);f.text(56,507,'库存：第 153—180 天',41,600);f.text(56,579,'两策略从相同现存起跑',38);f.text(56,648,'初始在途均为空',38);f.text(56,717,'不热身，不继承验证末态',37);
f.line(819);f.text(32,887,'测试前：参数与规则已冻结',38,600);f.text(32,960,'测试后：报告结果，不重新选参',36);
f.box(1034,285);f.text(56,1098,'不能称为全新盲测',41,600);f.text(56,1172,'历史测试汇总已公开',38);f.text(56,1240,'协议曾修订，须如实披露',37);
f.text(32,1398,'模拟需求 / 无效期的单节点回放',34);figs.push(f);
f=new Figure('d20-02_metrics',700,1530);
f.text(32,72,'四项指标，四种问题',44,600);
for(const [y,n,t,a,b] of [[125,'01','平均现存','日末现存之和 ÷ 测试天数','不含在途，不代表日内平均'],[415,'02','单位满足率','满足需求合计 ÷ 需求合计','总需求为零时记为不适用'],[705,'03','失销量','需求合计 − 满足需求合计','未满足就失销，不转为欠交'],[995,'04','订单次数','只数订货量大于零的事件','到了复核日，也可能不下单']]){f.box(y,245);f.text(56,y+61,n+'  '+t,42,600);f.text(56,y+135,a,35);f.text(56,y+202,b,34);}
f.line(1298);f.text(32,1375,'满足率 ≠ 周期服务水平',41,600);f.text(32,1450,'比较指标，不混淆业务含义。',36);figs.push(f);
f=new Figure('d20-03_tradeoff',700,1450);
f.text(32,72,'怎样读库存与缺货取舍',43,600);
f.box(125,235);f.text(56,188,'先看：是否少缺货',42,600);f.text(56,261,'同一需求、相同初始状态',37);f.text(56,321,'再比较失销量与满足率',37);f.arrow(380);
f.box(440,235);f.text(56,503,'再看：付出什么代价',42,600);f.text(56,576,'平均现存、订单次数',38);f.text(56,636,'期末现存与未到尾单',38);f.arrow(695);
f.box(755,235);f.text(56,818,'最后：限制是否说清',42,600);f.text(56,891,'没有成本，就不称经济最优',35);f.text(56,951,'没有效期，就不推断报废改善',34);
f.line(1055);f.text(32,1126,'禾味：数量用公斤',40);f.text(32,1200,'匿名服装：数量用件',40);f.text(32,1274,'两案分开比较，不相加评分。',36);
f.text(32,1396,'模拟结果不等于真实项目收益。',35);figs.push(f);
// Frozen source copy permits independent chart reproduction outside the repository.
const sourceBytes=fs.readFileSync(path.join(HERE,'data/ledger.csv'));
const expectedLedgerHash='8069dab38b42b1e922dd885068d60ad36e0426ea6d105522b9c7d87999141ca7';
if(crypto.createHash('sha256').update(sourceBytes).digest('hex')!==expectedLedgerHash)fail('曲线源台账哈希改变，请审查来源，不自动更新。');
const sourceMeta=JSON.parse(fs.readFileSync(path.join(HERE,'data/source.json'),'utf8'));
if(sourceMeta.sha256!==expectedLedgerHash)fail('曲线来源记录与固定哈希不一致。');
const sourceLines=sourceBytes.toString('utf8').trimEnd().split(/\r?\n/),headers=sourceLines.shift().split(',');
const curveRows=sourceLines.map(line=>{const vals=line.split(',');if(vals.length!==headers.length)fail('曲线CSV列数错误');return Object.fromEntries(headers.map((k,i)=>[k,vals[i]]));});
if(curveRows.length!==112)fail('曲线CSV必须112行');
f=new Figure('d20-04_inventory-curves',700,1530);
f.text(32,66,'冻结策略的日末库存轨迹',42,600);
f.parts.push('<path d="M36 117H106" stroke="black" stroke-width="4"/><path d="M36 166H106" stroke="#666" stroke-width="4" stroke-dasharray="12 8"/>');
f.text(126,130,'每日固定批量',35);f.text(126,179,'每三天补至目标',35);
const curveReport=[];
for(const [caseName,label,unit,top,maxY,step,initial] of [['hewei','禾味','公斤',330,100,25,78],['apparel','匿名服装','件',930,500,125,316]]){
 const left=104,right=654,height=300;
 f.text(32,top-80,label+' / '+unit,41,600);
 f.text(32,top-30,'日初重置：'+initial+' '+unit+'，空在途',32);
 for(let v=0;v<=maxY;v+=step){const y=top+height-v/maxY*height;f.parts.push(`<path d="M${left} ${y}H${right}" stroke="#ccc" stroke-width="1"/>`);f.text(20,y+11,String(v),30);}
 f.parts.push(`<path d="M${left} ${top}V${top+height}H${right}" fill="none" stroke="black" stroke-width="2"/>`);
 for(const day of [153,162,171,180]){const x=left+(day-153)/27*(right-left);f.parts.push(`<path d="M${x} ${top+height}v8" stroke="black"/>`);f.text(x-25,top+height+48,String(day),29);}
 f.text(260,top+height+100,'模拟日编号',31);
 for(const [policy,color,dash] of [['daily_sQ','black',''],['periodic_RS','#666','12 8']]){
  const rows=curveRows.filter(r=>r.case===caseName&&r.policy===policy);
  if(rows.length!==28||rows.some((r,i)=>Number(r.day)!==153+i||Number(r.opening_oh)<0||Number(r.end_oh)<0||Number(r.end_oh)>maxY))fail('曲线分组或范围错误');
  if(Number(rows[0].opening_oh)!==initial||Number(rows[0].pipeline_before)!==0)fail('曲线初态不符冻结');
  const points=rows.map(r=>[left+(Number(r.day)-153)/27*(right-left),top+height-Number(r.end_oh)/maxY*height]);
  f.parts.push(`<polyline data-case="${caseName}" data-policy="${policy}" points="${points.map(p=>p.join(',')).join(' ')}" fill="none" stroke="${color}" stroke-width="4"${dash?' stroke-dasharray="'+dash+'"':''}/>`);
  curveReport.push({case:caseName,policy,unit,days:rows.map(r=>Number(r.day)),end_oh:rows.map(r=>Number(r.end_oh)),points});
 }
}
f.line(1385);f.text(32,1444,'连线仅连接日末点，不表示日内变化。',33);
f.text(32,1501,'日末均值不等于日内时间加权均值。',33);figs.push(f);
fs.writeFileSync(path.join(HERE,'curve-data-check.json'),JSON.stringify({sourceSha256:expectedLedgerHash,series:curveReport},null,2)+'\n');
const launch={headless:true};if(process.env.CHROME_PATH)launch.executablePath=process.env.CHROME_PATH;
const browser=await pw.chromium.launch(launch);const page=await browser.newPage({deviceScaleFactor:1});
const report=[];
for(const fig of figs){
 const svg=fig.svg();fs.writeFileSync(path.join(HERE,fig.name+'.svg'),svg+'\n');
 if(inRepo && fig.name==='d20-00_cover')fs.writeFileSync(path.join(REPO,'assets/cover-sources/d20-inventory-test.svg'),svg+'\n');
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
await browser.close();fs.writeFileSync(path.join(HERE,'render-quality-report.json'),JSON.stringify(report,null,2)+'\n');console.log('Rendered five SVG designs and PNGs; dimensions, text bounds and overlap checks passed.');
