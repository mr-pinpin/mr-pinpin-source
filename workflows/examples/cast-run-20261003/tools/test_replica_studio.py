"""Isolated Studio outbox contract; no networking or live artwork writes."""
import importlib.util,io,json,sys,tempfile,shutil
from pathlib import Path
from unittest.mock import patch
import cast_ops
from store import Store
from PIL import Image
DATA=cast_ops.DATA
BUSINESS=Path('/Volumes/TB4/mac-mini-storage/shared/pinpin-r17-studio-source/tools/studio/business')
spec=importlib.util.spec_from_file_location('replica_fixture_business',BUSINESS/'__init__.py',submodule_search_locations=[str(BUSINESS)])
b=importlib.util.module_from_spec(spec);sys.modules[spec.name]=b;spec.loader.exec_module(b)
with tempfile.TemporaryDirectory(dir=DATA/'reports') as tmp:
 root=Path(tmp);store=Store(root);(root/'workflows').mkdir()
 shutil.copytree(DATA/'exports/packages/replica_store/src',root/'library')
 cfg=json.loads((DATA/'workflows/replica-store.json').read_text());cfg.update(root=str(root/'outbox'),libraryPath='library')
 (root/'workflows/replica-store.json').write_text(json.dumps(cfg))
 shutil.copyfile(DATA/'workflows/storage-policy.json',root/'workflows/storage-policy.json')
 raw=io.BytesIO();Image.new('RGB',(4,4),'blue').save(raw,format='PNG')
 asset,_=store.upload_asset(raw.getvalue(),'test.png',{'source':'native-imagegen','prompt':'PRIVATE fixture only','referenceIds':[]})
 _,result=b.route(store,'POST','/api/storage/enqueue',{}, {'assetId':asset['id']})
 assert result['outboxOwned'] and result['remoteBackupStatus']=='pending'
 owned=root/'outbox/objects'/asset['sha256'];assert owned.read_bytes()==raw.getvalue()
 jobs=list((root/'outbox/jobs').glob('*.json'));assert len(jobs)==1
 assert 'PRIVATE' not in jobs[0].read_text() and str(root) not in jobs[0].read_text()
 assert b.route(store,'POST','/api/storage/enqueue',{}, {'assetId':asset['id']})[1]['sha256']==asset['sha256']
 folder=root/'reports/character-packages';folder.mkdir(parents=True)
 stages={role:{'assetId':asset['id'],'sha256':asset['sha256']} for role in ('solo','interactions')}
 (folder/'subject.json').write_text(json.dumps({'stages':{role:{'candidates':[{'assetId':asset['id']}]} for role in stages}}))
 frozen=json.dumps({'stages':stages,'benchmark':'frozen'}).encode();(folder/'subject-completion.json').write_bytes(frozen)
 class Runtime:
  def invoke(self,kind,store,method,path,query,body):
   if path=='/api/cast/finish':return 200,{'stages':stages}
   return b.route(store,method,path,query,body)
 with patch.object(cast_ops,'DATA',root):
  receipt=cast_ops.closeout(Runtime(),store,'subject',lambda _:(_ for _ in ()).throw(AssertionError('HTTP forbidden')))
 assert receipt['localDraftComplete'] and all(p['outboxOwned'] for p in receipt['pages'])
 assert not receipt['allRemoteVerified'] and (folder/'subject-completion.json').read_bytes()==frozen
 # Cold canonical fixture restored from owned bytes without host/network access.
 canonical=store.asset_path(asset['id']);canonical.unlink()
 with patch.object(b.asset_storage.subprocess,'run',side_effect=AssertionError('Owned restoration must not need network')):
  restored=b.asset_storage.resolve(store,asset['id'])
 assert Path(restored['nativePath']).read_bytes()==raw.getvalue()
 assert restored['source']=='shared-verified-bytes'
 assert b.self_test()
print(json.dumps({'passed':10,'networkCalls':0,'liveArtworkChanged':False,'businessSelfTest':True}))
