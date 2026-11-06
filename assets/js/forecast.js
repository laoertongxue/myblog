/* Progressive enhancement: all lessons and navigation remain readable without JS. */
'use strict';
const legacyNumericIds=["legacy-0", "legacy-1", "legacy-2", "legacy-3", "legacy-4", "legacy-5", "legacy-6", "legacy-7", "legacy-8", "legacy-9", "legacy-10", "legacy-11", "legacy-12", "legacy-13", "legacy-14", "legacy-15", "legacy-16", "legacy-17", "legacy-18", "abc-xyz", "sop-fva", "milp", "deviance-residual", "presale-60days", "cross-price", "multiechelon", "markdown-dp", "fresh-01", "fresh-02", "fresh-03", "fresh-04", "fresh-05", "apparel-01", "apparel-02", "apparel-03", "apparel-04", "apparel-05", "fmcg-01", "fmcg-02", "fmcg-03", "fmcg-04", "fmcg-05", "restaurant-01", "restaurant-02", "restaurant-03", "restaurant-04", "restaurant-05", "manufacturing-01", "manufacturing-02", "manufacturing-03", "manufacturing-04", "manufacturing-05", "pharma-01", "pharma-02", "pharma-03", "pharma-04", "pharma-05", "specialty-start", "specialty-time", "specialty-data", "presale-full", "returns-full", "cod-full", "po-full", "model-causal-three", "model-pricing-stochastic", "model-tree-trained", "model-deep-inputs", "model-prophet-decomposition", "planning-pr01", "planning-pr02", "planning-pr03", "planning-pr04", "planning-pr05", "planning-pr06", "fresh-hourly-unobserved", "temperature-shelf-life", "apparel-bayesian-lifecycle", "vmi-asof-conservation", "collab-first-second-allocation", "whitepaper-trace", "resource-center"];
const el=id=>document.getElementById(id);
const current=el('main').dataset.unit;
const anchors=[...el('nav').querySelectorAll('[data-unit]')];
const known=new Set(anchors.map(a=>a.dataset.unit));
function legacyRoute(){
 const stable=location.hash.match(/^#unit-([a-z0-9-]+)$/);
 const numeric=location.hash.match(/^#lesson-(\d+)$/);
 const id=stable?stable[1]:numeric?legacyNumericIds[Number(numeric[1])]:null;
 if(id&&known.has(id))location.replace('/forecast/'+id+'/');
 else if(location.hash==='#home')location.replace('/forecast/');
}
legacyRoute();window.addEventListener('hashchange',legacyRoute);
let done={},storageWarning=false;
try{
 const stored=JSON.parse(localStorage.getItem('forecast-course-progress')||'{}');
 if(stored&&typeof stored==='object'&&!Array.isArray(stored))for(const [key,value] of Object.entries(stored)){
  const id=/^\d+$/.test(key)&&Number(key)<19?legacyNumericIds[Number(key)]:key;
  if(known.has(id)&&value===true)done[id]=true;
 }
}catch(e){storageWarning=true;}
function progress(){
 const n=Object.keys(done).filter(id=>done[id]).length;
 el('count').textContent=n+' / '+known.size;el('progress').max=known.size;el('progress').value=n;
 for(const a of anchors){a.classList.toggle('completed',!!done[a.dataset.unit]);}
}
if(storageWarning)el('storage-status').textContent='当前浏览器无法读取保存进度，请使用导出功能保留记录。';
if(el('complete')){
 el('complete').checked=!!done[current];
 el('complete').onchange=e=>{
  done[current]=e.target.checked;
  try{localStorage.setItem('forecast-course-progress',JSON.stringify(done));el('storage-status').textContent='进度已保存到本机浏览器。';}
  catch(e){el('storage-status').textContent='当前浏览器无法保存进度。本次勾选只在当前页面有效，请使用“导出学习记录”保留。';}
  progress();
 };
 el('print').onclick=()=>window.print();
}
progress();
let lessons=[];
function filter(){
 const query=el('search').value.toLowerCase(),group=el('scope').value;
 for(const a of anchors){const lesson=lessons.find(m=>m.id===a.dataset.unit);
  a.hidden=!!((group&&lesson&&lesson.group!==group)||!(lesson?lesson.title+lesson.html:a.textContent).toLowerCase().includes(query));
 }
}
el('search').oninput=filter;el('scope').onchange=filter;
fetch(el('main').dataset.index).then(r=>{if(!r.ok)throw new Error();return r.json();}).then(data=>{lessons=data;filter();}).catch(()=>{
 el('storage-status').textContent='全文搜索暂不可用，仍可按课程标题查找并阅读全部课程。';el('scope').disabled=true;
});
el('export').onclick=()=>{
 const blob=new Blob([JSON.stringify({exportedAt:new Date().toISOString(),progress:anchors.map(a=>({id:a.dataset.unit,title:a.dataset.title,selfReportedComplete:!!done[a.dataset.unit]}))},null,2)],{type:'application/json'});
 const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='forecast-learning-progress.json';a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000);
};
function closeMenu(){el('side').classList.remove('open');el('menu').setAttribute('aria-expanded','false');}
el('menu').onclick=()=>{el('side').style.setProperty('--course-menu-top',document.querySelector('.forecast-app>header').getBoundingClientRect().bottom+'px');const open=el('side').classList.toggle('open');el('menu').setAttribute('aria-expanded',String(open));if(open)el('search').focus();};
document.addEventListener('keydown',e=>{if(e.key==='Escape'&&el('side').classList.contains('open')){closeMenu();el('menu').focus();}});
window.addEventListener('resize',()=>{if(window.innerWidth>680)closeMenu();});
function calc(){const nums=el('numbers').value.split(/[,，]/).map(v=>v.trim()).filter(Boolean).map(Number);if(nums.length!==3||nums.some(x=>!Number.isFinite(x)||x<0||x>1e9)){el('result').textContent='请输入3个0至10亿之间的非负数，例如10,12,14。';return}const sum=nums.reduce((a,b)=>a+b,0),w=[.2,.3,.5];const weighted=nums.reduce((a,b,i)=>a+b*w[i],0);el('result').textContent=`① 先相加\n${nums.join(' + ')} = ${sum.toFixed(2)} kg\n\n② 再除以天数\n${sum.toFixed(2)} ÷ 3 = ${(sum/3).toFixed(2)} kg\n\n③ 按权重计算\n${nums.map((n,i)=>`${w[i]} × ${n}`).join(' + ')}\n= ${weighted.toFixed(2)} kg\n\n这里是预测示范，不是订货量。`}

if(el('calc')){el('calc').onclick=calc;calc();}
