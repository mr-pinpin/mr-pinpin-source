"""Focused data-relative tests; no live transfers or artwork changes."""
import copy
import hashlib
import json
import tempfile
import sys
from pathlib import Path
from unittest.mock import patch
import cast_ops

checks=[]
def check(name,condition):
    assert condition,name
    checks.append(name)

with tempfile.TemporaryDirectory(dir=cast_ops.DATA/'reports') as tmp:
    root=Path(tmp); folder=root/'reports/character-packages';folder.mkdir(parents=True)
    (root/'reports/storage').mkdir()
    (root/'workflows').mkdir()
    (root/'workflows/storage-policy.json').write_text(json.dumps({'bucket':'approved-test-bucket'}))
    assets=[];stages={}
    for role in ('solo','interactions'):
        path=root/(role+'.png');path.write_bytes(role.encode())
        asset={'id':'asset-'+role,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'bytes':path.stat().st_size}
        assets.append(asset);stages[role]={'assetId':asset['id'],'sha256':asset['sha256']}
    package={'stages':{r:{'candidates':[{'assetId':stages[r]['assetId']}]} for r in stages}}
    (folder/'test-character.json').write_text(json.dumps(package))
    frozen=json.dumps({'stages':stages,'frozenBenchmark':'unchanged'}).encode()
    completion=folder/'test-character-completion.json';completion.write_bytes(frozen)
    class Store:
        def read(self): return {'assets':assets}
        def asset_path(self,identifier): return root/(identifier.removeprefix('asset-')+'.png')
    class Runtime:
        def invoke(self,*args):
            check('Existing finish receives exact final IDs',args[-1]['assetIds']==[a['id'] for a in assets])
            return 200,{'stages':stages,'workflowCard':{'type':'WorkflowCard','assetIds':[a['id'] for a in assets],'actions':[]}}
    def proof(identifier):
        a=next(a for a in assets if a['id']==identifier)
        return {'assetId':identifier,'sha256':a['sha256'],'bytes':a['bytes'],'remoteBackupStatus':'verified-download',
            'adapterReceipt':{'bucket':'approved-test-bucket','verified':True,'entries':[{'sha256':a['sha256'],'bytes':a['bytes'],'remote_verified':True,'verified':True}]}}
    with patch.object(cast_ops,'DATA',root):
        calls=[]
        result=cast_ops.closeout(Runtime(),Store(),'test-character',lambda identifier:(calls.append(identifier),proof(identifier))[1])
        check('Both finals transferred once',calls==[a['id'] for a in assets])
        check('Matched download proofs accepted',result['allRemoteVerified'])
        check('Frozen completion bytes preserved',completion.read_bytes()==frozen)
        bad=proof(assets[0]['id']);bad['adapterReceipt']['entries'][0]['sha256']='wrong'
        check('Mismatched remote identity rejected',not cast_ops.verified_backup(bad,assets[0]))
        def fail(identifier): raise TimeoutError()
        result=cast_ops.closeout(Runtime(),Store(),'test-character',fail)
        check('Timeout keeps usable local package',result['localDraftComplete'] and not result['allRemoteVerified'])
        check('Both outcomes explicitly pending or failed',all(p['remoteBackupStatus']=='failed-or-pending' for p in result['pages']))
        for a in assets:
            (root/'reports/storage'/(a['id']+'-backup.json')).write_text(json.dumps(proof(a['id'])))
        result=cast_ops.closeout(Runtime(),Store(),'test-character',fail)
        check('Verified existing receipts reused without transfer',result['allRemoteVerified'])
        # Exercise the CLI dispatch, not just closeout(). Fixture has no exports,
        # helper source files or engineering focused-test proof.
        with patch.object(cast_ops,'Store',return_value=Store()),patch.object(cast_ops,'BusinessRuntime') as factory,patch.object(sys,'argv',['cast_ops.py','closeout','test-character']),patch.object(cast_ops,'closeout_checkpoint',side_effect=AssertionError('Engineering work in ordinary closeout')):
            factory.return_value=Runtime();factory.return_value.close=lambda:None
            cast_ops.main()
        check('Ordinary CLI works without engineering files',not (root/'exports').exists() and not (root/'reports/character-closeout-focused-proof.json').exists())
        with patch.object(cast_ops,'Store',return_value=Store()),patch.object(cast_ops,'BusinessRuntime') as factory,patch.object(sys,'argv',['cast_ops.py','closeout-dev-checkpoint','test-character']),patch.object(cast_ops,'closeout_checkpoint',return_value='fixture-export-receipt') as checkpoint:
            factory.return_value=Runtime();factory.return_value.close=lambda:None
            cast_ops.main()
            check('Developer checkpoint explicitly dispatches export verification',checkpoint.call_count==1)
        Store().asset_path(assets[0]['id']).write_bytes(b'corrupt')
        try: cast_ops.closeout(Runtime(),Store(),'test-character',fail)
        except ValueError: checks.append('Corrupt local final refused')
        else: raise AssertionError('Corrupt local final accepted')
cast_ops.atomic_json(cast_ops.DATA/'reports/character-closeout-focused-proof.json',{'checks':checks,'passed':len(checks),'liveRemoteProof':False})
print(json.dumps({'passed':len(checks)}))
