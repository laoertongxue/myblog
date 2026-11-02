// Optional authoring tool; baseline reproduction needs Python only.
const {chromium}=require('playwright');
const fs=require('fs');
const path=require('path');
(async()=>{
  const slug='seasonal-naive-demand-forecast';
  const files=[['d9-00_cover',`assets/cover-sources/${slug}.svg`],
    ...['d9-01_split','d9-02_weekdays','d9-03_cases','d9-04_boundaries'].map(n=>[n,`assets/diagram-sources/${slug}/${n}.svg`])];
  const browser=await chromium.launch({headless:true});
  const page=await browser.newPage();
  const target=`content/blog/${slug}/images`;
  fs.mkdirSync(target,{recursive:true});
  let evidence=[];
  for(const [name,file] of files){
    const svg=fs.readFileSync(file,'utf8');
    const result=await page.evaluate(async svg=>{
      const img=new Image(); img.src='data:image/svg+xml;base64,'+btoa(unescape(encodeURIComponent(svg)));
      await img.decode();
      const canvas=document.createElement('canvas');canvas.width=img.width;canvas.height=img.height;
      const ctx=canvas.getContext('2d');ctx.drawImage(img,0,0);
      const pixels=ctx.getImageData(0,0,canvas.width,canvas.height);
      for(let i=0;i<pixels.data.length;i+=4){const gray=Math.round((pixels.data[i]+pixels.data[i+1]+pixels.data[i+2])/3);pixels.data[i]=pixels.data[i+1]=pixels.data[i+2]=gray;}
      ctx.putImageData(pixels,0,0);
      return {width:canvas.width,height:canvas.height,png:canvas.toDataURL('image/png').split(',')[1]};
    },svg);
    fs.writeFileSync(path.join(target,name+'.png'),Buffer.from(result.png,'base64'));
    evidence.push({name,width:result.width,height:result.height,grayscale:true});
  }
  await browser.close();console.log(JSON.stringify(evidence,null,2));
})().catch(e=>{console.error(e);process.exit(1)});
