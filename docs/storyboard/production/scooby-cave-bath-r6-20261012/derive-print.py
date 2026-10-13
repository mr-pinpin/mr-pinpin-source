"""Native-dimension print codec derivatives, not substitutes for source backups."""
import hashlib,json,sys
from pathlib import Path
from PIL import Image
pack=Path(__file__).resolve().parent;root=pack.parents[3];selected=json.loads(Path(sys.argv[1]).read_text());out=Path(sys.argv[2]);records={'titles':{},'scenes':[]};digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def convert(item):
 source=root/item['source'];assert digest(source)==item['sha256'];name=item['sha256']+'.jpg';target=out/name
 with Image.open(source) as image:
  dimensions=image.size
  if not target.exists():image.convert('RGB').save(target,quality=92,subsampling=0)
 with Image.open(target) as jpeg:assert jpeg.size==dimensions
 assert digest(source)==item['sha256'],'Source changed during derivative'
 return {**item,'jpeg':name,'jpegSha256':digest(target),'dimensions':list(dimensions)}
for lang,item in selected['titles'].items():records['titles'][lang]=convert(item)
for item in selected['scenes']:records['scenes'].append(convert(item))
(out/'inputs.json').write_text(json.dumps(records,indent=2)+'\n');print('Preserved dimensions for',len(records['scenes']),'narrative masters and3titles')
