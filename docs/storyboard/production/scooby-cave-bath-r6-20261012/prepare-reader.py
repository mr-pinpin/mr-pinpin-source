"""Build new R6 runtime metadata/reading codecs only from explicitly reviewed masters."""
import hashlib,json
from pathlib import Path
from PIL import Image
pack=Path(__file__).resolve().parent;root=pack.parents[3]
script=json.loads((pack/'script/story-script.json').read_text())
selection=json.loads((pack/'working-selection.json').read_text())['selected']
records={r['id']:r for r in json.loads((pack/'generation-records.json').read_text())}
titles=json.loads((pack/'reader/title-selection.json').read_text())
output=root/'docs/storyboard/images/published/scooby-bath/r6'
assert not output.exists(),'Use a fresh derivative directory; never overwrite published assets'
digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def reviewed(id):
 record=records[id];assert record['status'] in ['agent-reviewed-working','agent-reviewed-story-candidate'],id
 source=root/record['nativePath'];assert digest(source)==record['nativeSha256'],id
 return source
sources=[]
for scene in script['scenes']:
 n=scene['number']
 if scene.get('reusedApprovedImage'):source=root/'docs/storyboard'/scene['reusedApprovedImage'];kind='approved-book-byte-reuse'
 elif scene.get('reusedEnvironmentNative'):source=pack/scene['reusedEnvironmentNative'];kind='reviewed-environment-POV'
 else:source=reviewed(selection[f'{n:03}']);kind='reviewed-narrative'
 assert source.is_file() and not source.is_symlink()
 with Image.open(source) as image:assert image.size==(1536,1024),(n,image.size)
 sources.append((scene,source,kind))
title_sources={lang:reviewed(id) for lang,id in titles['titles'].items()};miniature=reviewed(titles['miniature'])
for source in [*title_sources.values(),miniature]:
 with Image.open(source) as image:assert image.size==(1024,1536)
output.mkdir(parents=True)
encoding={'format':'WebP','quality':80,'method':6,'narrativeDimensions':[1440,960],'crop':False,'originalsModified':False}
manifest={'schemaVersion':1,'encoding':encoding,'titles':{},'scenes':[],'derivatives':[]}
def derivative(source,destination,size):
 before=digest(source)
 with Image.open(source) as image:
  image=image.convert('RGB')
  if image.size!=size:image=image.resize(size,Image.Resampling.LANCZOS)
  image.save(destination,format='WEBP',quality=80,method=6)
 assert digest(source)==before
 manifest['derivatives'].append({'path':str(destination.relative_to(root)),'bytes':destination.stat().st_size,'sha256':digest(destination),'source':str(source.relative_to(root)),'sourceSha256':before,'width':size[0],'height':size[1]})
base='images/published/scooby-bath/r6/'
localized={'en':'Scooby Gets a Bath','ru':'Скуби купается','es':'Scooby se da un baño'}
covers={lang:base+'title-'+lang+'.webp' for lang in ['en','ru','es']}
for lang,source in title_sources.items():
 derivative(source,output/f'title-{lang}.webp',(1024,1536))
 manifest['titles'][lang]={'source':str(source.relative_to(root)),'sha256':digest(source)}
derivative(miniature,output/'miniature.webp',(1024,1536))
for width in [256,512,1024]:derivative(miniature,output/f'miniature-{width}.webp',(width,width*3//2))
scenes=[{'id':'scooby-bath-title','role':'title','image':covers['en'],'images':covers,'width':1024,'height':1536,'alt':localized,'paragraphs':{lang:[] for lang in localized}}]
for scene,source,kind in sources:
 n=scene['number']
 if kind=='approved-book-byte-reuse':image=scene['reusedApprovedImage'];dimensions=(1536,1024)
 else:
  image=base+f'scene-{n:03}.webp';dimensions=(1440,960)
  derivative(source,output/f'scene-{n:03}.webp',dimensions)
 manifest['scenes'].append({'number':n,'source':str(source.relative_to(root)),'sha256':digest(source),'selectionKind':kind,'readingImage':image})
 scenes.append({'id':f'r6-{n:03}','image':image,'width':dimensions[0],'height':dimensions[1],'alt':{lang:scene['narration'][lang][0] for lang in localized},'paragraphs':scene['narration']})
story={'schemaVersion':1,'id':'scooby-bath','editionVersion':4,'title':localized,'cover':covers,'miniature':base+'miniature.webp','scenes':scenes,'spreads':[{'scenes':[i],'style':'cover' if i==0 else 'elder','paper':'portrait' if i==0 else 'landscape'} for i in range(216)],'sectionNav':[
 {'startScene':1,'title':{'en':'The cool air','ru':'Прохладный воздух','es':'El aire fresco'}},
 {'startScene':53,'title':{'en':'Rooms beneath the roots','ru':'Комнаты под корнями','es':'Salas bajo las raíces'}},
 {'startScene':107,'title':{'en':'Where the water goes','ru':'Куда идёт вода','es':'Adónde va el agua'}},
 {'startScene':160,'title':{'en':'The muddy explorer','ru':'Грязный исследователь','es':'El explorador embarrado'}}]}
(root/'docs/storyboard/stories/scooby-bath-r6.json').write_text(json.dumps(story,ensure_ascii=False,indent=2)+'\n')
(pack/'reader/selected-masters.json').write_text(json.dumps({'schemaVersion':1,'titles':manifest['titles'],'scenes':manifest['scenes']},indent=2)+'\n')
(pack/'reader/production-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
(root/'assets/chapter-deployments.json').write_text(json.dumps({'schemaVersion':1,'chapters':[{'id':'scooby-bath','storyFile':'docs/storyboard/stories/scooby-bath-r6.json','mediaRoot':'docs/storyboard/images/published/scooby-bath/r6','reader':'https://mr-pinpin.github.io/chapter-scooby-bath/storyboard/'}]},indent=2)+'\n')
print('Prepared216pages/3languages;',len(manifest['derivatives']),'reading derivatives;',sum(d['bytes'] for d in manifest['derivatives']),'bytes; native masters untouched')
