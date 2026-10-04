"""Create tiny synthetic delivery fixtures only, no model/provider/artwork calls."""
import argparse,json,runpy,hashlib
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--out',required=True);a=p.parse_args();out=Path(a.out);out.mkdir(parents=True,exist_ok=False)
helpers=runpy.run_path(str(Path(__file__).with_name('test_delivery.py')));raw=helpers['png']();(out/'assets').mkdir();(out/'assets/fixture.png').write_bytes(raw)
assets=[{'id':name,'storagePath':'assets/fixture.png','mime':'image/png','bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'provenance':{'kind':'provided-line-art' if name.startswith('line') else 'synthetic-fixture'}} for name in ('cover','miniature','panel','line1','line2','line3')]
prepare=runpy.run_path(str(Path(__file__).with_name('prepare.py')))['prepare'];spec={'title':{'en':'The leaf — fixture','ru':'Листочек — пример'},'panels':[{'id':'p1','imageAssetId':'panel','captions':{'en':'Hmm…','ru':'Хм…'}}]}
fp=lambda v:hashlib.sha256(json.dumps(v,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
rh=fp([]);record={'chapterId':'fixture','version':1,'spec':spec,'referenceBindings':[],'referenceHash':rh,'sha256':fp({'spec':spec,'referenceHash':rh})};b=json.dumps(record,ensure_ascii=False).encode();file=out/'record.json';file.write_bytes(b)
for lang in ('en','ru'):prepare(file,hashlib.sha256(b).hexdigest(),'fixture',1,assets,out,out/lang,lang,['line1','line2','line3'],'cover',miniature_asset='miniature',require_complete=True,source_version_sha=record['sha256'])
print(json.dumps({'out':str(out),'syntheticFixtureOnly':True,'expectedPages':6}))
