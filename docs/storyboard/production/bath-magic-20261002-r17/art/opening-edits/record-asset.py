from pathlib import Path
import json,hashlib,struct,sys
b=Path("/Volumes/TB4/mac-mini-storage/shared/pinpin-bath-magic-20261002-r17/art/opening-edits")
def meta(x):return {'path':str(x.relative_to(b)),'sha256':hashlib.sha256(x.read_bytes()).hexdigest(),'bytes':x.stat().st_size}
sid,ver,prior,*refs=sys.argv[1:]
p=b/'native'/f'{sid}-{ver}.png';t=b/'prompts'/f'{sid}-{ver}.txt'
refs=[b/x for x in refs]
out={'schemaVersion':1,'id':sid,'priorR16Number':int(prior),'version':ver,'tool':'builtin image_gen.imagegen','native':meta(p),'prompt':meta(t),'exactPrompt':t.read_text().strip(),'inputs':[meta(r) for r in refs],'toolArguments':{'referenced_image_paths':[str(r) for r in refs],'transparent_background':False},'artistReview':'pending','rootReview':'pending','selected':False,'outputHandling':'Native PNG copied unchanged; no raster edits outside builtin'}
out['native']['width'],out['native']['height']=struct.unpack('>II',p.read_bytes()[16:24])
(b/'records'/f'{sid}-{ver}.json').write_text(json.dumps(out,indent=2)+'\n')
print(sid,ver)
