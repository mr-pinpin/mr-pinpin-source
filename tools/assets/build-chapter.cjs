#!/usr/bin/env node
'use strict';
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),vm=require('node:vm');
const {parseArgs}=require('node:util');
const {manifestEntries,BUDGET,references}=require('./build-pages.cjs');
const {chapterDeployments}=require('./chapter-deployments.cjs');
const digest=bytes=>crypto.createHash('sha256').update(bytes).digest('hex');
function buildChapter({root=path.resolve(__dirname,'../..'),story,dest,check=false}={}) {
  root=fs.realpathSync(root);
  if(!/^[a-z0-9-]+$/.test(story||''))throw Error('A valid --story is required');
  const manifest=manifestEntries(JSON.parse(fs.readFileSync(path.join(root,'assets/manifest.json'),'utf8')));
  const selected=new Map();
  function source(name,media=false){
    if(!name.startsWith('docs/')||name.split('/').some(p=>!p||p==='.'||p==='..')||name.includes('\\'))throw Error('Unsafe path '+name);
    let current=root;for(const part of name.split('/')){current=path.join(current,part);if(fs.lstatSync(current).isSymbolicLink())throw Error('Source symlink '+name);}
    if(!fs.lstatSync(current).isFile())throw Error('Source is not a regular file '+name);
    const bytes=fs.readFileSync(current),entry=manifest.get(name);
    if(media&&entry?.role!=='production')throw Error('Unselected production media '+name);
    if(entry&&(entry.role!=='production'||entry.bytes!==bytes.length||entry.sha256!==digest(bytes)))throw Error('Asset identity mismatch '+name);
    return bytes;
  }
  function add(name,media=false){const bytes=source(name,media);selected.set(name.slice(5),bytes);return bytes;}
  const deployment=chapterDeployments(root).find(item=>item.id===story);
  const storyPath=deployment?.storyFile||`docs/storyboard/stories/${story}.json`;
  const edition=JSON.parse(source(storyPath).toString());
  selected.set(`storyboard/stories/${story}.json`,Buffer.from(JSON.stringify(edition,null,2)+'\n'));
  const context={window:{},URLSearchParams};vm.runInNewContext(source('docs/storyboard/standalone-stories.js').toString(),context);
  if(edition.id!==story||!context.window.standaloneStories.complete(edition))throw Error('Incomplete or invalid selected story');
  const covers=JSON.parse(source('docs/storyboard/covers.json').toString());
  if(deployment){
    function localize(value){
      if(typeof value==='string'&&value.startsWith(deployment.reader))return value.slice(deployment.reader.length);
      if(Array.isArray(value))return value.map(localize);
      if(value&&typeof value==='object')return Object.fromEntries(Object.entries(value).map(([key,item])=>[key,localize(item)]));
      return value;
    }
    Object.assign(covers,localize(covers));
  }
  covers.covers=Object.fromEntries(Object.entries(covers.covers||{}).filter(([id])=>id===story));
  selected.set('storyboard/covers.json',Buffer.from(JSON.stringify(covers,null,2)+'\n'));
  const pdfs=JSON.parse(source('docs/storyboard/library-pdfs.json').toString());
  pdfs.chapters=pdfs.chapters.filter(x=>x.route?.story===story);
  selected.set('storyboard/library-pdfs.json',Buffer.from(JSON.stringify(pdfs,null,2)+'\n'));
  // Media closure uses the same runtime registry parser as the full-site builder.
  for(const [name,bytes] of [[storyPath,Buffer.from(JSON.stringify(edition))],['docs/storyboard/covers.json',Buffer.from(JSON.stringify(covers))]])
    for(const ref of references(bytes.toString(),name)){
      if(/^(?:[a-z][a-z\d+.-]*:|\/\/|#)/i.test(ref.url))continue;
      const target='docs'+decodeURIComponent(new URL(ref.url,'https://pages.invalid/'+ref.base.slice(5)).pathname);
      add(target,true);
    }
  const runtime=['pdf-route.css','pdf-route.js','library-download.js','reader.css','editorial.css','edition.css','paper.css','print.css','reader-navigation.css','locale.js','chapter-editions.js','standalone-stories.js','title-covers.js','reader.js','icons.js','icons.LICENSE','chapter-hosting.js'];
  for(const name of runtime)add('docs/storyboard/'+name);
  let html=source('docs/storyboard/index.html').toString();
  const description=String(edition.title.en).replaceAll('&','&amp;').replaceAll('"','&quot;').replaceAll('<','&lt;');
  html=html.replace(/(<meta name="description" content=")[^"]*(">)/,(_,before,after)=>before+description+after);
  html=html.replace('<head>',`<head>\n  <meta name="pinpin-chapter" content="${story}">\n  <script src="chapter-hosting.js"></script>`)
    .replaceAll('href="atlas-webgpu.html?lang=ru"','href="https://mr-pinpin.github.io/storyboard/atlas-webgpu.html?lang=ru"');
  selected.set('storyboard/index.html',Buffer.from(html));
  selected.set('storyboard/chapter-deployments.json',Buffer.from('{"schemaVersion":1,"chapters":{}}\n'));
  selected.set('index.html',Buffer.from(`<!doctype html><meta charset="utf-8"><title>Mr. PinPin</title><script>const u=new URL('storyboard/',location.href);u.search=location.search;u.hash=location.hash;location.replace(u.href)</script><a href="storyboard/">Read the chapter</a>`));
  // Preserve the actual deployed notice copies; do not invent broader grants.
  for(const name of fs.readdirSync(path.join(root,'docs/permissions')))add('docs/permissions/'+name);
  if(fs.existsSync(path.join(root,'docs/.nojekyll')))add('docs/.nojekyll');
  const bytes=[...selected.values()].reduce((a,b)=>a+b.length,0);
  if(bytes>=BUDGET)throw Error('Chapter exceeds Pages size budget');
  const result={story,files:selected.size,bytes,budget:BUDGET};
  if(check)return {...result,check:true};
  if(!dest)throw Error('--dest is required');
  const output=path.resolve(root,dest);
  if(output===root||output.startsWith(root+path.sep)||root.startsWith(output+path.sep))throw Error('Destination must be outside source checkout');
  if(fs.existsSync(output))throw Error('Destination already exists');
  let parent=path.dirname(output);while(!fs.existsSync(parent))parent=path.dirname(parent);
  if(fs.realpathSync(parent)!==parent)throw Error('Destination parent contains symlink');
  fs.mkdirSync(path.dirname(output),{recursive:true});
  const staging=fs.mkdtempSync(path.join(path.dirname(output),'.pinpin-chapter-'));
  try{
    for(const [name,content] of selected){const target=path.join(staging,name);fs.mkdirSync(path.dirname(target),{recursive:true});fs.writeFileSync(target,content);if(digest(fs.readFileSync(target))!==digest(content))throw Error('Copied identity mismatch '+name);}
    fs.renameSync(staging,output);
  }catch(error){fs.rmSync(staging,{recursive:true,force:true});throw error;}
  return {...result,dest:output};
}
if(require.main===module){try{const {values}=parseArgs({options:{root:{type:'string'},story:{type:'string'},dest:{type:'string'},check:{type:'boolean'}}});console.log(JSON.stringify(buildChapter(values),null,2));}catch(error){console.error(error.message);process.exitCode=1;}}
module.exports={buildChapter};
