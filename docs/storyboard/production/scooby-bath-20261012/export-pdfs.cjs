'use strict';
// Export this new chapter from preserved native masters; never alter older PDFs.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),cp=require('node:child_process');
const {pathToFileURL}=require('node:url');
const out=process.argv[2];if(!out)throw Error('Pass a new external output directory');
const root=path.resolve(__dirname,'../../../..'),destination=path.resolve(out);
if(destination===root || destination.startsWith(root+path.sep)||fs.existsSync(destination))throw Error('New external output directory required');
fs.mkdirSync(destination,{recursive:true});
const storyPath=path.join(root,'docs/storyboard/stories/scooby-bath.json'),story=JSON.parse(fs.readFileSync(storyPath,'utf8'));
const sha=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const python=process.env.PINPIN_PYTHON||'python3';
cp.execFileSync(python,['-c',`from PIL import Image
from pathlib import Path
import sys
source=Path(sys.argv[1]);out=Path(sys.argv[2]);out.mkdir()
for p in source.glob('*.png'):
 if '-v1' in p.stem:continue
 with Image.open(p) as image:image.convert('RGB').save(out/(p.stem+'.jpg'),quality=92,subsampling=0)
`,path.join(__dirname,'native'),path.join(destination,'print-jpeg')]);
const escape=s=>s.replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
(async()=>{
 const browser=await chromium.launch({headless:true});
 const record={schemaVersion:1,sourceStorySha256:sha(storyPath),nativeMasterEncoding:{format:'JPEG print derivative',quality:92,subsampling:0,resize:false,crop:false},pdfs:[]};
 try{
  for(const lang of ['en','ru','es']){
   const page=await browser.newPage();
   const sections=story.scenes.map((scene,index)=>{
    const name=index===0?'title-'+lang:scene.id;
    const src=pathToFileURL(path.join(destination,'print-jpeg',name+'.jpg')).href;
    return `<section class="${index===0?'cover':'spread'}"><div class="frame"><img src="${src}"></div>${index?`<div class="caption">${scene.paragraphs[lang].map(t=>'<p>'+escape(t)+'</p>').join('')}</div>`:''}</section>`;
   }).join('');
   const html=`<!doctype html><html lang="${lang}"><meta charset="utf-8"><title>${escape(story.title[lang])}</title><style>
   @page cover {size:210mm 297mm;margin:0} @page story {size:297mm 210mm;margin:0}
   *{box-sizing:border-box}body{margin:0;color:#283624;background:white;font-family:'DejaVu Serif','Liberation Serif',serif}
   section{break-after:page;overflow:hidden}.cover{page:cover;width:210mm;height:297mm}.cover .frame{width:210mm;height:297mm}
   .spread{page:story;width:297mm;height:210mm}.spread .frame{width:234mm;height:156mm;margin:5mm auto 0}
   .frame img{display:block;width:100%;height:100%;object-fit:contain}.caption{margin:7mm 17mm 0;text-align:center;font-size:18pt;line-height:1.35}.caption p{margin:0}section:last-child{break-after:auto}
   </style>${sections}</html>`;
   const htmlPath=path.join(destination,'scooby-bath-'+lang+'.html');fs.writeFileSync(htmlPath,html);
   await page.goto(pathToFileURL(htmlPath).href);await page.evaluate(async()=>{await document.fonts.ready;await Promise.all([...document.images].map(i=>i.decode()))});
   const pdf=path.join(destination,'scooby-bath-'+lang+'.pdf');await page.pdf({path:pdf,printBackground:true,preferCSSPageSize:true});
   const count=(fs.readFileSync(pdf).toString('latin1').match(/\/Type \/Page[\s>]/g)||[]).length;
   if(count!==17)throw Error('Unexpected page count: '+count);
   record.pdfs.push({language:lang,filename:path.basename(pdf),bytes:fs.statSync(pdf).size,sha256:sha(pdf),pageCount:count});await page.close();
  }
  record.browserVersion=browser.version();fs.writeFileSync(path.join(destination,'export-manifest.json'),JSON.stringify(record,null,2)+'\n');
  console.log(JSON.stringify(record.pdfs));
 }finally{await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1});
