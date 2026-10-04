"""Persistent incremental metadata catalog; no media reads or network."""
import ast
import hashlib
import os
import stat
from datetime import datetime,timezone
import json
from pathlib import Path
import time
from paths import LocationError,atomic_json,digest,metadata_path,relative


def load_json(path,limit=64*1024*1024):
    if path.stat().st_size>limit:raise LocationError('JSON exceeds metadata read bound')
    return json.loads(path.read_text())


def read_index(root,path):
    value=load_json(path)
    if value.get('schemaVersion')!=1 or value.get('root')!=str(root.resolve()):raise LocationError('Index schema/root mismatch')
    return value


def build(root,target,studio_data=None,catalog=None,previous_path=None,progress=None):
    progress=progress or (lambda **values:None)
    progress(phase='catalog-read')
    began=time.perf_counter();config_path=Path(catalog).resolve() if catalog else metadata_path(root,'workflows/locations/catalog.json');config=load_json(config_path,1024*1024)
    if config.get('schemaVersion')!=1:raise LocationError('Unsupported location catalog schema')
    previous=previous_path or target
    progress(phase='previous-cache-read',path=str(previous))
    old_index=read_index(root,previous) if previous.exists() else {};old=old_index.get('documents',{})
    paths={config_path};paths.update(root/relative(n) for n in config.get('metadataFiles',[]))
    extensions=set(config['allowedMetadataExtensions'])|{'.py'}
    # Enumerate only catalog-declared query/recipe dependencies, never whole media trees.
    patterns=set(config['catalogGlobs']+config.get('metadataGlobs',[]))
    for entry in config['entries']:
        patterns.update(entry['documents']);patterns.update(entry.get('recipes',[]))
        if entry.get('approvalEvidence'):patterns.add(entry['approvalEvidence'])
    patterns.update(['docs/storyboard/panorama-workflow/templates/*.txt','tools/panoramas/*.py',
                     'docs/storyboard/production/tractor-stops-20260924/stops/stop-??/selected.json'])
    for pattern in sorted(patterns):
        relative(pattern)
        progress(phase='enumerate-metadata',path=pattern,candidateCount=len(paths))
        if any(c in pattern for c in '*?['):
            paths.update(p for p in root.glob(pattern) if p.suffix in extensions)
        else:
            paths.add(root/pattern)
    docs={};errors=[];changed=reused=0;checked_parents=set()
    queue=sorted(paths);queued=set(paths)
    for p in queue:
        name='workflows/locations/catalog.json' if p==config_path else p.relative_to(root).as_posix()
        try:
            progress(phase='metadata-stat',path=name,changedDocuments=changed,reusedDocuments=reused,candidateCount=len(paths))
            # Validate each distinct metadata directory once; regular files need one lstat.
            if p!=config_path and p.parent not in checked_parents:
                progress(phase='metadata-boundary',path=name)
                metadata_path(root,p.parent.relative_to(root).as_posix())
                checked_parents.add(p.parent)
            st=p.lstat()
            if stat.S_ISLNK(st.st_mode):
                metadata_path(root,name);st=p.stat()
            if not stat.S_ISREG(st.st_mode):raise LocationError('Metadata must be a regular file')
            fp=[st.st_size,st.st_mtime_ns]
            if old.get(name,{}).get('fingerprint')==fp:
                docs[name]=old[name];reused+=1
                if name.endswith('/selected.json') and '/tractor-stops-' in name:
                    base=Path(name.split('/stops/',1)[0])
                    for key in ('stack','exports','anchoredExports','record','prompt','review','sourceLockReview'):
                        value=old[name].get('value',{}).get(key)
                        if isinstance(value,str) and Path(value).suffix in extensions:
                            candidate=root/base/relative(value)
                            if candidate not in queued:queue.append(candidate);queued.add(candidate)
                continue
            if st.st_size>8*1024*1024:raise LocationError('Metadata exceeds 8 MiB bound')
            progress(phase='metadata-read',path=name,changedDocuments=changed,reusedDocuments=reused)
            # Parent boundary and optional file symlink were already validated.
            raw_bytes=p.read_bytes();raw=raw_bytes.decode('utf-8');row={'fingerprint':fp,'sha256':hashlib.sha256(raw_bytes).hexdigest()}
            if p.suffix=='.json':row['value']=json.loads(raw)
            elif name in config.get('metadataFiles',[]) and p.suffix=='.js':row['value']=json.JSONDecoder().raw_decode(raw[raw.index('={')+1:])[0]
            else:row['excerpt']=raw[:600]
            docs[name]=row;changed+=1
            if name.endswith('/selected.json') and '/tractor-stops-' in name:
                base=Path(name.split('/stops/',1)[0])
                for key in ('stack','exports','anchoredExports','record','prompt','review','sourceLockReview'):
                    value=row.get('value',{}).get(key)
                    if isinstance(value,str) and Path(value).suffix in extensions:
                        candidate=root/base/relative(value)
                        if candidate not in queued:queue.append(candidate);queued.add(candidate)
        except (OSError,ValueError) as exc:errors.append({'path':name,'error':str(exc)[:160]})
    progress(phase='derive-catalogs',documentCount=len(docs))
    assets={};catalogs=[];book={}
    for name,row in docs.items():
        value=row.get('value',{})
        if not isinstance(value,dict):continue
        if name.startswith('docs/storyboard/stories/'):
            for scene in value.get('scenes',[]):
                image=scene.get('image')
                if isinstance(image,str) and image.startswith('images/'):
                    book.setdefault('docs/storyboard/'+image,[]).append({'registry':name,'sceneId':scene.get('id')})
        if not (name.startswith('assets/') or name=='tools/assets/production-preservation.json') or not isinstance(value.get('assets'),list):continue
        catalogs.append(name)
        for a in value['assets']:
            if not isinstance(a,dict) or not all(k in a for k in ('path','bytes','sha256')):continue
            try:relative(a['path'])
            except LocationError:continue
            prior=assets.get(a['path'])
            if prior and (prior['sha256'],prior['bytes'])!=(a['sha256'],a['bytes']):
                prior['conflict']=True;errors.append({'path':a['path'],'error':'Catalog identity conflict; restore refused'});continue
            conflict=prior.get('conflict',False) if prior else False
            assets[a['path']]=dict(a,catalog=name,bucket=value.get('bucket'),conflict=conflict)
    allowlist={};allow_path=root/'tools/studio/media_library.py'
    if allow_path.exists():
        for n in ast.parse(allow_path.read_text()).body:
            if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='FILES' for t in n.targets):
                for key,row in ast.literal_eval(n.value).items():allowlist[row[2]]=key
    result={'schemaVersion':1,'root':str(root.resolve()),'indexedAt':datetime.now(timezone.utc).isoformat(),'config':config,'catalogReceipt':{'path':str(config_path),'sha256':docs['workflows/locations/catalog.json']['sha256']},'documents':docs,'assets':assets,'bookRegistry':book,'studioAllowlistBySha256':allowlist,'errors':errors,'catalogs':catalogs,'timing':{'indexSeconds':time.perf_counter()-began,'changedDocuments':changed,'reusedDocuments':reused,'documentCount':len(docs)}}
    data=studio_data or old_index.get('studioBridge',{}).get('dataRoot')
    if data:
        from storage_bridge import identities
        progress(phase='studio-identities',path=str(data))
        result['studioBridge']=identities(root,data)
    progress(phase='candidate-write',path=str(target),documentCount=len(docs))
    atomic_json(target,result)
    progress(phase='complete',documentCount=len(docs),indexSeconds=time.perf_counter()-began)
    return {k:result[k] for k in ('schemaVersion','indexedAt','timing','errors')}
