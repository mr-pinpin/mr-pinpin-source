"""Small request hydration: verified local bytes, shared IDs, then existing archive."""
import re
import shutil
import subprocess
import sys
import time
from paths import LocationError,atomic_json,digest,external_path,media_path,relative


def hydrate(root,manifest,output,max_bytes,selection='references',restore=False,cache=None):
    began=time.perf_counter();out=external_path(root,output);bridge=manifest.pop('_hydrationBridge',None)
    if out.exists() and any(out.iterdir()):raise LocationError('Request bundle must be new or empty')
    if type(max_bytes) is not int or not 0<max_bytes<=256*1024*1024:raise LocationError('Byte budget must be 1..256 MiB')
    rows=[r for r in manifest['media'] if selection=='all' or r.get('isReference') or r.get('contextOnly') or selection=='selected' and r.get('selected')]
    if len(rows)>64:raise LocationError('Request exceeds 64-file bound; narrow query')
    if any(type(r.get('bytes')) is not int or r['bytes']<0 or not re.fullmatch('[a-f0-9]{64}',r.get('sha256','')) for r in rows):raise LocationError('Hydration needs exact bytes and SHA-256')
    total=sum(r['bytes'] for r in rows)
    if total>max_bytes:raise LocationError('Request exceeds explicit byte budget')
    if any(r.get('identityConflict') or r.get('conflict') for r in rows):raise LocationError('Conflicting identities cannot hydrate')
    cache_path=external_path(root,cache) if cache else None
    if restore and not cache_path:raise LocationError('Cold restore requires explicit external cache')
    out.parent.mkdir(parents=True,exist_ok=True)
    if shutil.disk_usage(out.parent).free<total*2+64*1024*1024:raise LocationError('Insufficient bounded bundle disk reserve')
    sources={};missing=[]
    for row in rows:
        p=media_path(root,row['path'])
        source=p if p.is_file() else None
        if source is None and bridge:
            from storage_bridge import resolve
            source=resolve(root,bridge,row,cold=False)
        if source:
            if source.stat().st_size!=row['bytes'] or digest(source)!=row['sha256']:raise LocationError('Local media identity differs: '+row['path'])
            sources[row['path']]=source
        else:missing.append(row)
    if restore and any(not r['restorable'] and not r.get('sharedReplica',{}).get('registeredStudioIds') for r in missing):
        raise LocationError('Missing media has no exact legacy object or existing shared ID')
    out.mkdir(parents=True,exist_ok=True);copied=[];shared=[];network=False
    def copy_verified(row,source):
        target=out/'media'/relative(row['path']);external_path(root,target);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
        if target.stat().st_size!=row['bytes'] or digest(target)!=row['sha256']:raise LocationError('Hydrated output identity differs')
        copied.append(row['path'])
    for row in rows:
        if row['path'] in sources:copy_verified(row,sources[row['path']])
    if restore and bridge:
        from storage_bridge import resolve
        for row in missing:
            if row.get('sharedReplica',{}).get('registeredStudioIds'):
                network=True
                remaining=180-(time.perf_counter()-began)
                if remaining<=0:raise LocationError('Cold request budget exhausted')
                try:
                    source=resolve(root,bridge,row,cold=True,timeout=remaining)
                except subprocess.TimeoutExpired:source=None
                if source:copy_verified(row,source);shared.append(row['path'])
    missing=[r for r in missing if r['path'] not in copied]
    legacy=[r for r in missing if r['restorable']]
    projection={'version':1,'bucket':'miguelemosreverte/mr-pinpin-archive','assets':[{k:r[k] for k in ('path','role','bytes','sha256','object')} for r in legacy]}
    atomic_json(out/'restore-manifest.json',projection)
    adapter=root/'tools/assets/hf_store.py'
    info={'requested':restore,'adapterPath':'tools/assets/hf_store.py','adapterSha256':digest(adapter),
          'missingBytes':sum(r['bytes'] for r in missing),'networkInvoked':network,'sharedReplicaRestoredPaths':shared}
    atomic_json(out/'request-manifest.json',manifest)
    if restore and missing:
        if len(legacy)!=len(missing):raise LocationError('Shared ID unavailable and no legacy fallback object')
        cache_path.mkdir(parents=True,exist_ok=True)
        argv=[sys.executable,'-B',str(adapter),'pull','--manifest',str(out/'restore-manifest.json'),'--root',str(out/'media'),'--cache',str(cache_path),'--profile','all','--workers','1','--receipt',str(out/'adapter-receipt.json')]
        info['networkInvoked']=True
        try:
            result=subprocess.run(argv,capture_output=True,text=True,timeout=max(1,180-(time.perf_counter()-began)))
            if result.returncode:raise LocationError('Existing archive adapter failed; private output omitted')
            for row in missing:
                p=out/'media'/relative(row['path'])
                if not p.is_file() or p.stat().st_size!=row['bytes'] or digest(p)!=row['sha256']:raise LocationError('Restored media identity differs')
                copied.append(row['path'])
        except subprocess.TimeoutExpired:raise LocationError('Cold restore exceeded 180s; bounded bundle retained')
    report={'schemaVersion':1,'request':manifest['request'],'selectedBytes':total,'budgetBytes':max_bytes,'verifiedPaths':copied,
            'missing':[{'path':r['path'],'sha256':r['sha256'],'restorable':r['restorable']} for r in missing if r['path'] not in copied],
            'restore':info,'timing':{'hydrateSeconds':time.perf_counter()-began},'provenance':manifest['indexProvenance']}
    atomic_json(out/'hydration-receipt.json',report);return report
