'use strict';
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),os=require('node:os');
const {buildChapter}=require('./build-chapter.cjs');
const root=path.resolve(__dirname,'../..');
function fixture(t){
 const temp=fs.mkdtempSync(path.join(os.tmpdir(),'pinpin-chapter-test-'));t.after(()=>fs.rmSync(temp,{recursive:true,force:true}));
 const artifact=path.join(temp,'reader');buildChapter({root,story:'scooby-bath',dest:artifact});
 const source=path.join(temp,'source');fs.mkdirSync(source);fs.cpSync(artifact,path.join(source,'docs'),{recursive:true});
 fs.mkdirSync(path.join(source,'assets'));fs.copyFileSync(path.join(root,'assets/manifest.json'),path.join(source,'assets/manifest.json'));
 const deployments=path.join(root,'assets/chapter-deployments.json');if(fs.existsSync(deployments)){fs.copyFileSync(deployments,path.join(source,'assets/chapter-deployments.json'));for(const item of JSON.parse(fs.readFileSync(deployments,'utf8')).chapters){if(item.id!=='scooby-bath')continue;const target=path.join(source,item.storyFile);fs.mkdirSync(path.dirname(target),{recursive:true});fs.copyFileSync(path.join(artifact,'storyboard/stories/scooby-bath.json'),target);}}
 return {source,artifact,temp};
}
test('chapter artifact contains its media and reader without other books or atlas',t=>{
 const {artifact}=fixture(t);const visit=dir=>fs.readdirSync(dir,{withFileTypes:true}).flatMap(x=>x.isDirectory()?visit(path.join(dir,x.name)):[path.relative(artifact,path.join(dir,x.name))]);const files=visit(artifact);
 assert(!files.some(x=>x.includes('atlas/')||x.includes('production/')||x.includes('elder-cycle/')||x.includes('original/')));
 const story=JSON.parse(fs.readFileSync(path.join(artifact,'storyboard/stories/scooby-bath.json'),'utf8'));
 const selectedMedia=new Set(story.scenes.flatMap(scene=>[scene.image,...Object.values(scene.images||{})]));
 for(const file of files.filter(file=>file.startsWith('storyboard/images/published/bath-magic/')))assert(selectedMedia.has(file.slice('storyboard/'.length)),'Unselected older-book media copied');
 for(const scene of story.scenes){const target=path.join(artifact,'storyboard',scene.image);assert(fs.existsSync(target),scene.id);assert.deepEqual(fs.readFileSync(target),fs.readFileSync(path.join(root,'docs/storyboard',scene.image)));}
 assert.match(fs.readFileSync(path.join(artifact,'storyboard/index.html'),'utf8'),/pinpin-chapter/);
 assert.deepEqual(Object.keys(JSON.parse(fs.readFileSync(path.join(artifact,'storyboard/covers.json'),'utf8')).covers),['scooby-bath']);
});
test('changed media is refused rather than silently packaged',t=>{
 const {source}=fixture(t);const story=JSON.parse(fs.readFileSync(path.join(source,'docs/storyboard/stories/scooby-bath.json'),'utf8'));fs.appendFileSync(path.join(source,'docs/storyboard',story.scenes[1].image),'changed');assert.throws(()=>buildChapter({root:source,story:'scooby-bath',check:true}),/identity mismatch/);
});
test('selected media cannot follow a symlink',t=>{
 const {source}=fixture(t);const story=JSON.parse(fs.readFileSync(path.join(source,'docs/storyboard/stories/scooby-bath.json'),'utf8'));const target=path.join(source,'docs/storyboard',story.scenes[1].image);fs.unlinkSync(target);fs.symlinkSync(path.join(root,'docs/storyboard',story.scenes[1].image),target);assert.throws(()=>buildChapter({root:source,story:'scooby-bath',check:true}),/symlink/);
});
test('an existing output is retained and unsafe story identifiers are refused',t=>{
 const {artifact}=fixture(t);assert.throws(()=>buildChapter({root,story:'scooby-bath',dest:artifact}),/already exists/);assert(fs.existsSync(path.join(artifact,'index.html')));assert.throws(()=>buildChapter({root,story:'../scooby-bath',check:true}),/valid --story/);
});
