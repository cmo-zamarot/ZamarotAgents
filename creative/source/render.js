const { chromium } = require('playwright');
const path=require('path'); const fs=require('fs');
(async()=>{
  const [,,mode,out,fps]=process.argv;
  const b=await chromium.launch(); const p=await b.newPage({viewport:{width:1080,height:1440},deviceScaleFactor:1});
  p.on('console',m=>console.log('console:',m.text())); p.on('pageerror',e=>console.log('ERR',e.message));
  await p.goto('file://'+path.resolve(__dirname,'build/index.html')); await p.evaluate(()=>document.fonts.ready);
  await p.waitForTimeout(500);
  fs.mkdirSync(out,{recursive:true});
  if(mode==='stills'){
    const ts=process.argv.slice(4).map(Number);
    for(const t of ts){ await p.evaluate(t=>seek(t),t); await p.screenshot({path:`${out}/t${t.toFixed(1)}.jpg`,type:'jpeg',quality:85}); }
  } else {
    const F=+fps, dur=await p.evaluate(()=>DUR), n=Math.round(dur*F);
    for(let i=0;i<n;i++){ await p.evaluate(t=>seek(t),i/F); await p.screenshot({path:`${out}/f${String(i).padStart(5,'0')}.png`}); if(i%150==0) console.log(i,'/',n); }
  }
  await b.close();
})();
