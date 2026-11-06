// Native SVG artwork and lossless monochrome PNGs. Requires repository Playwright.
const fs=require('fs'),path=require('path'),crypto=require('crypto');
const {chromium}=require('playwright');
const root=path.resolve(__dirname,'../../..');
const out=path.join(root,'content/topics/forecasting/01-math-bridge/images');
const diagram=path.join(root,'assets/diagram-sources/forecasting-math-bridge');
const xml=s=>String(s).replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));
const text=(x,y,s,size=26,weight=400,fill='#111')=>`<text x="${x}" y="${y}" font-size="${size}" font-weight="${weight}" fill="${fill}">${xml(s)}</text>`;
const rect=(x,y,w,h,fill='#fff',stroke='#222')=>`<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="8" fill="${fill}" stroke="${stroke}" stroke-width="2"/>`;
const line=(x,y,xx,yy,dash='')=>`<path d="M${x} ${y} L${xx} ${yy}" fill="none" stroke="#333" stroke-width="3" ${dash?`stroke-dasharray="${dash}"`:''}/>`;
const arrow=(x,y,xx,yy)=>line(x,y,xx,yy)+`<path d="M${xx-10} ${yy-7} L${xx} ${yy} L${xx-10} ${yy+7}" fill="none" stroke="#333" stroke-width="3"/>`;
function svg(w,h,body){return `<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}" font-family="PingFang SC, Microsoft YaHei, sans-serif"><rect width="${w}" height="${h}" fill="#fff"/>${body}</svg>`;}
function heading(title,sub){return text(40,57,title,35,650)+text(40,99,sub,22,400,'#555')+line(40,122,860,122);}
const figs=[];
figs.push(['p01-00_cover',900,383,svg(900,383,
text(44,55,'预测与计划 · 数学桥梁',22,500,'#555')+
text(44,119,'先会算，再读懂预测',44,650)+
text(44,160,'符号 · 均值 · 误差 · 概率',25,400,'#555')+
[[44,'10'],[176,'12'],[308,'14']].map(([x,n])=>rect(x,208,100,68,'#f2f2f2')+text(x+27,253,n,33,600)).join('')+
arrow(425,242,513,242)+rect(537,200,318,86)+text(565,235,'平均值 = 12 kg',30,600)+text(565,265,'三个日需求量的平均',21,400,'#555')+
text(44,342,'禾味 + 匿名服装｜全部为教学模拟',22,400,'#555'))]);
figs.push(['p01-01_time',900,650,svg(900,650,
heading('先标清：站在哪天，预测哪天','模拟日期：11 月 6 日发出对 11 月 11 日的预测')+
rect(40,154,820,106,'#f4f4f4')+text(66,198,'ŷ(T + 5 | T)',38,650)+text(349,193,'帽子：预测值',25,500)+text(349,232,'右侧 T：预测发起时点',25,500)+
line(88,327,800,327)+arrow(720,327,800,327)+
'<circle cx="270" cy="327" r="8" fill="#111"/><circle cx="719" cy="327" r="8" fill="#fff" stroke="#111" stroke-width="3"/>'+
text(160,301,'11 月 6 日日终',25,600)+text(639,301,'11 月 11 日',25,600)+text(220,369,'起点 T',25,600)+text(658,369,'目标 T+5',25,600)+
rect(40,418,397,128)+text(64,457,'可用：截止起点已获得的信息',22,600)+text(64,496,'历史需求、已确认的活动计划',22)+
rect(463,418,397,128,'#f4f4f4')+text(487,457,'不可用：目标日的实际结果',22,600)+text(487,496,'11 月 11 日实际天气、销量',22)+
text(40,599,'y₃ 是第 3 天实际值；不是 y × 3。预测与实际要用相同单位。',23))]);
figs.push(['p01-02_errors',900,850,svg(900,850,
heading('标准差与预测误差，围绕的中心不同','禾味 A 店 · SKU01 鸡腿肉｜三天日需求量，单位 kg')+
rect(40,151,820,215)+text(64,192,'日期',25,600)+text(295,192,'第 1 天',25,600)+text(488,192,'第 2 天',25,600)+text(680,192,'第 3 天',25,600)+
text(64,238,'实际 y',25)+text(320,238,'10',27)+text(514,238,'12',27)+text(706,238,'14',27)+
text(64,284,'预测 ŷ',25)+text(320,284,'11',27)+text(514,284,'11',27)+text(706,284,'13',27)+
text(64,330,'误差 y − ŷ',25)+text(320,330,'−1',27)+text(514,330,'+1',27)+text(706,330,'+1',27)+
rect(40,392,397,256,'#f4f4f4')+text(64,435,'标准差：实际围绕均值',25,600)+text(64,483,'均值 = (10+12+14)÷3 = 12',22)+text(64,526,'偏离均值：−2、0、+2',24)+text(64,568,'总体方差 = (4+0+4)÷3',22)+text(64,610,'总体标准差 ≈ 1.633 kg',24,600)+
rect(463,392,397,256)+text(487,435,'误差：实际减各自预测',25,600)+text(487,483,'绝对误差：1、1、1',24)+text(487,526,'平方误差：1、1、1',24)+text(487,568,'MAE = 3÷3 = 1 kg',24)+text(487,610,'RMSE = √(3÷3) = 1 kg',24,600)+
text(40,702,'这里视作完整总体；样本方差除以 n−1，标准差再开方。',24)+text(40,747,'同一组实际值可以配不同预测，误差会变，实际的标准差不变。',23)+text(40,799,'全部为教学模拟；本图没有训练或比较预测模型。',22,400,'#555'))]);
figs.push(['p01-03_risk',900,820,svg(900,820,
heading('取消概率：先看清这一次的分母','匿名服装 · S01-M 模拟订单批次｜每单一件，取消为整单取消')+
[[40,'100 单','第 1 天开始'],[345,'90 单','第 2 天开始'],[650,'81 单','第 2 天结束']].map(([x,n,l])=>rect(x,164,210,109,'#f4f4f4')+text(x+28,210,n,34,650)+text(x+28,247,l,22)).join('')+
arrow(261,217,332,217)+arrow(566,217,637,217)+
text(65,320,'取消 10 单',25,600)+text(365,320,'取消 9 单',25,600)+text(664,320,'观测留存',25,600)+
rect(40,355,820,118)+text(64,397,'第 1 天：10÷100 = 10%     第 2 天：9÷90 = 10%',25,600)+text(64,443,'9÷100 = 9% 是初始批次占比，不是第 2 天的条件取消率。',23)+
rect(40,505,820,206,'#f4f4f4')+text(64,549,'假设新批次也适用这两个条件概率',27,600)+text(64,595,'两天留存概率 = (1−0.1) × (1−0.1) = 0.81',26)+text(64,641,'新 30 单的期望留存 = 30 × 0.81 = 24.3 单',27,600)+text(64,684,'期望是重复批次的平均；单次实际留存只能是整数。',23)+
text(40,766,'第二个 90% 已以第一天留存为条件；这一步不要求两天独立。',23))]);
figs.push(['p01-04_logit',900,815,svg(900,815,
heading('把概率变成分数，再把分数还原为概率','p 是概率；z 是无单位分数。这里只演示函数，不训练模型。')+
text(40,175,'正向：z = logit(p) = ln[p ÷ (1−p)]',31,600)+
[['p = 0.5','0.5÷0.5 = 1','ln(1) = 0'],['p = 0.8','0.8÷0.2 = 4','ln(4) ≈ 1.386']].map((row,i)=>{let y=211+i*106;return rect(40,y,194,78,'#f4f4f4')+text(62,y+48,row[0],28,600)+arrow(245,y+39,282,y+39)+rect(296,y,260,78)+text(317,y+48,row[1],27)+arrow(567,y+39,604,y+39)+rect(618,y,242,78,'#f4f4f4')+text(636,y+48,row[2],25,600);}).join('')+
text(40,450,'反向：p = 1 ÷ [1 + exp(−z)]',31,600)+rect(40,484,820,149)+text(64,531,'z = 0     →  exp(0) = 1       →  p = 1÷2 = 0.5',26)+text(64,579,'z = ln4  →  exp(−ln4) = ¼  →  p = 1÷1.25 = 0.8',26)+
text(40,684,'ln 是以 e 为底的对数；exp(−z) 就是 e 的 −z 次幂。',24)+text(40,729,'正向必须 0 < p < 1；p 为 0 或 1 时不能直接代入有限公式。',23)+text(40,774,'概率 0.8 = 80%，赔率为 4；赔率 4 不等于概率 400%。',23))]);
(async()=>{
fs.mkdirSync(out,{recursive:true});fs.mkdirSync(diagram,{recursive:true});
const browser=await chromium.launch({headless:true});
const page=await browser.newPage(); const reports=[];
for(const [name,w,h,source] of figs){
 const target=name==='p01-00_cover'?path.join(root,'assets/cover-sources/forecasting-math-bridge.svg'):path.join(diagram,name+'.svg');fs.writeFileSync(target,source+'\n');
 await page.setContent(source);await page.evaluate(()=>document.fonts.ready);
 const bounds=await page.locator('svg').evaluate(el=>Array.from(el.querySelectorAll('text')).map(t=>{const b=t.getBBox();return {text:t.textContent,x:b.x,y:b.y,width:b.width,height:b.height};}));
 const overflow=bounds.filter(b=>b.x<0||b.y<0||b.x+b.width>w||b.y+b.height>h);if(overflow.length)throw new Error(name+' text overflow '+JSON.stringify(overflow));
 const result=await page.evaluate(async source=>{const im=new Image();im.src='data:image/svg+xml;base64,'+btoa(unescape(encodeURIComponent(source)));await im.decode();const c=document.createElement('canvas');c.width=im.width;c.height=im.height;const ctx=c.getContext('2d');ctx.drawImage(im,0,0);const p=ctx.getImageData(0,0,c.width,c.height);let nonGray=0;for(let i=0;i<p.data.length;i+=4){if(p.data[i]!==p.data[i+1]||p.data[i]!==p.data[i+2])nonGray++;const g=Math.round((p.data[i]+p.data[i+1]+p.data[i+2])/3);p.data[i]=p.data[i+1]=p.data[i+2]=g;}ctx.putImageData(p,0,0);return {png:c.toDataURL('image/png').split(',')[1],width:c.width,height:c.height,nonGrayBefore:nonGray};},source);
 const png=Buffer.from(result.png,'base64');fs.writeFileSync(path.join(out,name+'.png'),png);delete result.png;
 reports.push({file:name+'.png',...result,grayscale:true,sha256:crypto.createHash('sha256').update(png).digest('hex'),text_bounds:bounds,overflow:[]});
}
await browser.close();fs.writeFileSync(path.join(__dirname,'render-report.json'),JSON.stringify(reports,null,2)+'\n');console.log(reports.map(({file,width,height,sha256})=>({file,width,height,sha256})));
})().catch(e=>{console.error(e);process.exit(1)});
