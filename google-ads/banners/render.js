const { chromium } = require('playwright');
(async()=>{const b=await chromium.launch();
const sizes=[[300,250],[336,280],[300,600],[728,90],[320,100],[320,50]];
const projs=(process.argv[2]||'hadera').split(',');
for(const P of projs) for(const [w,h] of sizes){const p=await b.newPage({viewport:{width:w,height:h},deviceScaleFactor:1});
 for(let f=0;f<4;f++){await p.goto(`file://${process.cwd()}/banner.html?w=${w}&h=${h}&f=${f}&p=${P}`);await p.evaluate(()=>document.fonts.ready);await p.waitForTimeout(250);await p.screenshot({path:`frames/${P}_${w}x${h}_${f}.png`});}
 await p.close();}
// logos
const L=await b.newPage({viewport:{width:1200,height:1200}});
for(const [bg,logo,n] of [['#f0eedf','logo-navy.svg','logo_navy-on-bone'],['#222944','logo-white.svg','logo_white-on-navy']]){
 await L.setContent(`<body style="margin:0;width:1200px;height:1200px;background:${bg};display:flex;align-items:center;justify-content:center"><img src="file://${process.cwd()}/img/${logo}" style="height:78%"></body>`);await L.waitForTimeout(300);await L.screenshot({path:`out/responsive/${n}_1200x1200.png`});}
await b.close()})();
