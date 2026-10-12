"""Preserve native outputs and create new, native-size WebP reader derivatives."""
import argparse,hashlib,json,shutil
from pathlib import Path
from PIL import Image,__version__ as pillow_version

parser=argparse.ArgumentParser();parser.add_argument('--native',type=Path,required=True);parser.add_argument('--variant',default='');parser.add_argument('--web',action='store_true');args=parser.parse_args()
root=Path(__file__).resolve().parents[4];pack=Path(__file__).resolve().parent
output=root/'docs/storyboard/images/published/scooby-bath'/args.variant;output.mkdir(parents=True,exist_ok=True)
masters=pack/'native';masters.mkdir(exist_ok=True)
records=[]
for name in [*(f'scene-{n:02d}' for n in range(1,17)),'title-en','title-ru','title-es','miniature']:
 source=args.native/(name+'.png');target=output/(name+'.webp')
 expected=(1536,1024) if name.startswith('scene') else (1024,1536)
 with Image.open(source) as image:
  assert image.size==expected,(name,image.size)
  if target.exists():raise RuntimeError('Refusing to overwrite a selected derivative: '+str(target))
  actual=(768,512) if name.startswith('scene') else (512,768)
  derived=image.convert('RGB')
  if args.web:derived=derived.resize(actual,Image.Resampling.LANCZOS)
  else:actual=expected
  quality=76 if args.web else 86
  derived.save(target,format='WEBP',quality=quality,method=6,exact=True)
 copy=masters/source.name
 if copy.exists():
  assert copy.read_bytes()==source.read_bytes(),'Conflicting preserved master'
 else:shutil.copy2(source,copy)
 sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
 records.append({'id':name,'master':str(copy.relative_to(root)),'masterSha256':sha(copy),'masterBytes':copy.stat().st_size,'reader':str(target.relative_to(root)),'readerSha256':sha(target),'readerBytes':target.stat().st_size,'dimensions':list(actual),'nativeDimensions':list(expected),'recipe':{'format':'WebP','quality':quality,'method':6,'resize':bool(args.web),'crop':False,'pillowVersion':pillow_version},'reviewStatus':'agent-selected for user-authorized publication; individual user image review not performed'})
for name in ['scene-15-v1.png','scene-16-v1.png']:
 shutil.copy2(args.native/name,masters/name)
(pack/('media-'+args.variant+'.json' if args.variant else 'media.json')).write_text(json.dumps({'schemaVersion':1,'selected':records,'rejected':['native/scene-15-v1.png','native/scene-16-v1.png'],'rejectionReason':'Historic style-reference geometry drift: extra/background fixtures not in measured camera. Corrected non-destructively before selection.'},indent=2)+'\n')
print('Reader bytes:',sum(r['readerBytes'] for r in records),'native masters preserved:',len(records))
