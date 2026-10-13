'use strict';
const fs=require('node:fs'),path=require('node:path');
function chapterDeployments(root){
 const file=path.join(root,'assets/chapter-deployments.json');if(!fs.existsSync(file))return [];
 const stat=fs.lstatSync(file);if(!stat.isFile()||stat.isSymbolicLink())throw Error('Invalid chapter deployment configuration file');
 const data=JSON.parse(fs.readFileSync(file,'utf8'));if(data.schemaVersion!==1||!Array.isArray(data.chapters))throw Error('Invalid chapter deployment configuration');
 const ids=new Set();
 for(const item of data.chapters){
  if(!/^[a-z0-9-]+$/.test(item.id||'')||ids.has(item.id)||
   !new RegExp(`^docs/storyboard/stories/${item.id}-[a-z0-9-]+\\.json$`).test(item.storyFile||'')||
   !new RegExp(`^docs/storyboard/images/published/${item.id}/[a-z0-9-]+$`).test(item.mediaRoot||'')||
   item.reader!==`https://mr-pinpin.github.io/chapter-${item.id}/storyboard/`)throw Error('Unsafe chapter deployment scope');
  ids.add(item.id);
 }
 return data.chapters;
}
module.exports={chapterDeployments};
