// Independent table layout check against a real Hugo build; no production writes.
const fs=require('fs'),path=require('path'),http=require('http'),assert=require('assert');
const {chromium}=require('playwright');
(async()=>{
 const repo=path.resolve(__dirname,'..'),root=path.join(repo,'.hugo-check');
 const mime={'.html':'text/html; charset=utf-8','.css':'text/css','.js':'application/javascript','.png':'image/png','.webp':'image/webp','.svg':'image/svg+xml'};
 const server=http.createServer((req,res)=>{
   const requested=decodeURIComponent(new URL(req.url,'http://localhost').pathname);
   let file=path.resolve(root,'.'+requested);
   if(file!==root&&!file.startsWith(root+path.sep)){res.writeHead(403).end();return;}
   if(fs.existsSync(file)&&fs.statSync(file).isDirectory())file=path.join(file,'index.html');
   if(!fs.existsSync(file)){res.writeHead(404).end();return;}
   res.setHeader('content-type',mime[path.extname(file)]||'application/octet-stream');res.end(fs.readFileSync(file));
 });
 await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
 const browser=await chromium.launch({headless:true});let evidence=[];
 try{
  for(const width of [360,390,1280]){
   const page=await browser.newPage({viewport:{width,height:844}});
   await page.goto(`http://127.0.0.1:${server.address().port}/blog/seasonal-naive-demand-forecast/`,{waitUntil:'networkidle'});
   const result=await page.evaluate(()=>({
    viewport:innerWidth,pageWidth:document.documentElement.scrollWidth,
    tables:[...document.querySelectorAll('.d9-table-scroll')].map(el=>({
      clientWidth:el.clientWidth,scrollWidth:el.scrollWidth,overflow:getComputedStyle(el).overflowX,
      nowrap:getComputedStyle(el.querySelector('table')).whiteSpace,
      rows:[...el.querySelectorAll('tbody tr')].map(tr=>[...tr.cells].map(td=>td.textContent.trim()))
    }))
   }));
   assert(result.pageWidth<=result.viewport+1,JSON.stringify(result));
   assert.equal(result.tables.length,2);
   assert.deepStrictEqual(result.tables[0].rows.map(r=>r[3]),['19','25','19','22','28','38','29']);
   assert.deepStrictEqual(result.tables[1].rows.map(r=>r.slice(1)),[['40','2.1750','36','4.1111'],['40','2.9250','36','5.9167']]);
   for(const table of result.tables){assert.equal(table.overflow,'auto');assert.equal(table.nowrap,'nowrap');}
   if(width<560)assert(result.tables.every(t=>t.scrollWidth>t.clientWidth));
   evidence.push(result);await page.close();
  }
 }finally{await browser.close();await new Promise(resolve=>server.close(resolve));}
 fs.writeFileSync(path.join(__dirname,'d9-review-mobile-tables.json'),JSON.stringify(evidence,null,2)+'\n');
 console.log(JSON.stringify(evidence,null,2));
})().catch(e=>{console.error(e);process.exit(1)});
