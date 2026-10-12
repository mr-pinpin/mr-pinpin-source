"""Measure new-story reading variants externally; preserve native originals."""
import argparse,hashlib,json
from pathlib import Path
from PIL import Image,__version__
p=argparse.ArgumentParser();p.add_argument('--out',required=True,type=Path);p.add_argument('--primary-quality',type=int,default=55);p.add_argument('--fallback-width',type=int,default=576);p.add_argument('--fallback-quality',type=int,default=55);p.add_argument('inputs',nargs='+',type=Path);a=p.parse_args();pack=Path(__file__).resolve().parent;root=pack.parents[3]
assert not a.out.exists(),'Choose a fresh external output';a.out.mkdir(parents=True)
rows=[]
for f in a.inputs:
 before=hashlib.sha256(f.read_bytes()).hexdigest()
 with Image.open(f) as native:
  assert native.size==(1536,1024),(f,native.size)
  for fmt,width,height,q,kw in [('AVIF',960,640,a.primary_quality,{'speed':4}),('WEBP',a.fallback_width,round(a.fallback_width*2/3),a.fallback_quality,{'method':6})]:
   target=a.out/(f.stem+'.'+fmt.lower());native.convert('RGB').resize((width,height),Image.Resampling.LANCZOS).save(target,format=fmt,quality=q,**kw)
   rows.append({'native':str(f),'nativeSha256':before,'variant':target.name,'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'bytes':target.stat().st_size,'dimensions':[width,height],'recipe':{'format':fmt,'quality':q,**kw,'resize':'Lanczos, no crop','pillowVersion':__version__},'status':'codec feasibility study; visual review required, not selected production'})
 assert hashlib.sha256(f.read_bytes()).hexdigest()==before,'Native changed'
(a.out/'results.json').write_text(json.dumps(rows,indent=2)+'\n')
avg=sum(r['bytes'] for r in rows)/len(a.inputs)
print(json.dumps({'samples':len(a.inputs),'averageTwoFormatBytes':round(avg),'estimate214NewStoryImages':round(avg*214),'note':'One approved duck scene reused; covers/text/budget still need actual final build.'}))
