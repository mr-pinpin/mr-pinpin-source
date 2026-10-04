"""Read existing Studio identities and use its configured replica library; never enqueue."""
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from paths import LocationError, digest, external_path, relative


def inside(data, value):
    p = data / relative(value)
    if any(x.is_symlink() for x in [p,*p.parents]):
        raise LocationError('Studio storage symlinks are refused')
    if not p.resolve().is_relative_to(data.resolve()):
        raise LocationError('Studio storage path escapes data root')
    return p


def bounded(path, maximum=16384):
    if path.stat().st_size>maximum:
        raise LocationError('Studio metadata exceeds read bound')
    return json.loads(path.read_text())


def identities(root, data):
    data = external_path(root,data)
    config_path = inside(data,'workflows/replica-store.json')
    if not config_path.exists():
        return None
    cfg = bounded(config_path)
    if cfg.get('bucket')!='miguelemosreverte/mr-pinpin-archive' or cfg.get('namespace')!='replica-store-v1/book-art':
        raise LocationError('Replica namespace differs from existing approved book-art store')
    replica_root = Path(cfg['root'])
    if not replica_root.is_absolute() or not replica_root.resolve().is_relative_to(data):
        raise LocationError('Replica root must remain inside Studio data')
    inside(data,str(replica_root.relative_to(data)))
    registry = bounded(inside(data,'state.json'),16*1024*1024)
    assets = {}
    for a in registry.get('assets',[]):
        if re.fullmatch('[a-f0-9]{64}',a.get('sha256','')) and type(a.get('bytes')) is int:
            assets.setdefault(a['sha256'],[]).append({'assetId':a['id'],'bytes':a['bytes'],
                'storagePath':a['storagePath'],'reviewStatus':a.get('reviewStatus','unknown')})
    return {'dataRoot':str(data),'configSha256':digest(config_path),'assetsBySha256':assets,
            'replicaRoot':str(replica_root),'namespace':cfg['namespace']}


def annotate(root, row, bridge, probe=False):
    if not bridge or not row.get('sha256'):
        return
    sha = row['sha256']
    matches = [a for a in bridge['assetsBySha256'].get(sha,[]) if a['bytes']==row.get('bytes')]
    row['sharedReplica'] = {'sha256Id':sha,'namespace':bridge['namespace'],
        'registeredStudioIds':[a['assetId'] for a in matches],
        'localOwnedPresent':None,'registeredLocalPresent':None}
    if not probe:
        return
    owned = inside(Path(bridge['dataRoot']),str(Path(bridge['replicaRoot']).relative_to(bridge['dataRoot']))+'/objects/'+sha)
    local = next((inside(Path(bridge['dataRoot']),a['storagePath']) for a in matches
                  if inside(Path(bridge['dataRoot']),a['storagePath']).is_file()),None)
    row['sharedReplica']['localOwnedPresent'] = owned.is_file()
    row['sharedReplica']['registeredLocalPresent'] = bool(local)
    if local or owned.is_file():
        row['availability'] = 'studio-local-unverified'


def repository(root, bridge):
    data = Path(bridge['dataRoot'])
    config_path = inside(data,'workflows/replica-store.json')
    if digest(config_path)!=bridge['configSha256']:
        raise LocationError('Replica configuration changed; rebuild location index')
    cfg = bounded(config_path)
    library = inside(data,cfg['libraryPath'])/'replica_store'
    expected = cfg.get('libraryFiles',{})
    if set(expected)!={'__init__.py','core.py','hf.py','cli.py','__main__.py'}:
        raise LocationError('Existing replica library source receipt is incomplete')
    for name,sha in expected.items():
        p = inside(data,str((library/name).relative_to(data)))
        if digest(p)!=sha:
            raise LocationError('Replica library source differs from current configured receipt')
    namespace = '_location_existing_replica_'+digest(config_path)[:16]
    spec = importlib.util.spec_from_file_location(namespace,library/'__init__.py',submodule_search_locations=[str(library)])
    module = importlib.util.module_from_spec(spec)
    sys.modules[namespace] = module
    spec.loader.exec_module(module)
    return module.Repository(cfg),cfg,data


def resolve(root, bridge, row, cold=False, timeout=180):
    """Use exact existing IDs; cold work is allowed only by hydrate --restore."""
    repo,cfg,data = repository(root,bridge)
    sha,size = row['sha256'],row['bytes']
    # Registered local source first; no new provenance or backup state is minted.
    for a in bridge['assetsBySha256'].get(sha,[]):
        if relative(a['storagePath']).parts[0]!='assets':
            raise LocationError('Registered shared artwork must remain under assets')
        p = inside(data,a['storagePath'])
        if a['bytes']==size and p.is_file():
            if p.stat().st_size!=size or digest(p)!=sha:
                raise LocationError('Registered Studio media identity changed')
            return p
    try:
        return repo.resolve(sha,size)
    except FileNotFoundError:
        if not cold:
            return None
    policy = bounded(inside(data,'workflows/storage-policy.json'))
    python = Path(policy['pythonPath'])
    if not python.is_file():
        raise LocationError('Configured host archive Python is unavailable')
    env = dict(os.environ,PYTHONPATH=str(inside(data,cfg['libraryPath'])),PYTHONDONTWRITEBYTECODE='1')
    result = subprocess.run([str(python),'-B','-m','replica_store','--config',str(inside(data,'workflows/replica-store.json')),
                             'get',sha,str(size)],capture_output=True,timeout=timeout,env=env)
    if result.returncode or len(result.stdout)>16384:
        return None
    response = json.loads(result.stdout)
    if response.get('status')!='verified-local':
        return None
    return repo.resolve(sha,size)
