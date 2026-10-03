"""Isolated archive-only fixtures; frozen legacy metrics remain untouched."""
import hashlib,json,tempfile
from pathlib import Path
from unittest.mock import patch
import cast_ops
for legacy in (True,False):
 with tempfile.TemporaryDirectory(dir=cast_ops.DATA/'reports') as tmp:
  root=Path(tmp);(root/'workflows').mkdir();folder=root/'reports/character-packages';folder.mkdir(parents=True)
  assets=[];stages={};package={'stages':{}}
  for role in ('solo','interactions'):
   path=root/(role+'.png');path.write_bytes(role.encode());sha=hashlib.sha256(path.read_bytes()).hexdigest()
   asset={'id':'asset-'+role,'sha256':sha,'bytes':len(role),'provenance':{'source':'native-imagegen'}};assets.append(asset)
   stages[role]={'assetId':asset['id'],'sha256':sha};package['stages'][role]={'candidates':[dict(stages[role])]}
  (root/'workflows/cast-run.json').write_text(json.dumps({'characters':[{'id':'fixture','status':'produced','stages':stages}]}))
  (folder/'fixture.json').write_text(json.dumps(package))
  frozen=folder/'fixture-generation.json';frozen.write_text(json.dumps({'calls':[{'before':'legacy','after':'legacy','seconds':12}]} if legacy else {'benchmark':'frozen'}));before=frozen.read_bytes()
  class Store:
   def read(self):return {'assets':assets}
   def asset_path(self,identifier):return root/(identifier.removeprefix('asset-')+'.png')
  class Runtime:
   def invoke(self,*args):
    assert args[3]=='/api/storage/enqueue'
    a=next(a for a in assets if a['id']==args[-1]['assetId'])
    return 200,dict(assetId=a['id'],sha256=a['sha256'],bytes=a['bytes'],remoteBackupStatus='verified-download',outboxOwned=True)
  with patch.object(cast_ops,'DATA',root),patch.object(cast_ops,'finish_records',side_effect=AssertionError('No metrics')):
   result=cast_ops.archive_existing(Runtime(),Store(),'fixture');assert result['allRemoteVerified'];assert frozen.read_bytes()==before
   assets[0]['sha256']='0'*64
   try:cast_ops.archive_existing(Runtime(),Store(),'fixture')
   except ValueError:pass
   else:raise AssertionError('Hash mismatch accepted')
print(json.dumps({'passed':6,'legacyAndGenericPairs':True,'creativeRecordsUnchanged':True}))
