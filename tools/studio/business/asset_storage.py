"""ID-based verified storage over the existing registry and HF archive adapter.

No credentials, catalog, asset deletion, URL changes or kernel overrides.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import time
import tempfile
from datetime import datetime, timezone
from contextlib import contextmanager
import fcntl
import importlib.util
import sys
from model import StudioError, find, valid_id
from store import atomic_json


def stamp():
    return datetime.now(timezone.utc).isoformat()

def replica_repository(store):
    """Configured reusable library; no network or host-read job paths here."""
    cfg=bounded_json(inside(store,'workflows/replica-store.json'))
    if cfg.get('bucket')!='miguelemosreverte/mr-pinpin-archive' or cfg.get('namespace')!='replica-store-v1/book-art':
        raise StudioError('Replica deployment differs from approved artwork namespace')
    library=inside(store,cfg['libraryPath'])/'replica_store'
    if library.is_symlink():raise StudioError('Replica library directory must not be a symlink')
    expected=cfg.get('libraryFiles',{})
    required={'__init__.py','core.py','hf.py','cli.py','__main__.py'}
    if set(expected)!=required:raise StudioError('Replica library needs exact source receipt')
    for name in required:
        path=library/name
        if path.is_symlink() or path.stat().st_size>262144 or hashlib.sha256(path.read_bytes()).hexdigest()!=expected[name]:
            raise StudioError('Replica library source differs from configured receipt')
    root=Path(cfg['root'])
    if not root.is_absolute() or not root.resolve().is_relative_to(store.root.resolve()):raise StudioError('Studio outbox must remain inside its data root')
    namespace='_studio_replica_'+hashlib.sha256(json.dumps(expected,sort_keys=True).encode()).hexdigest()
    module=sys.modules.get(namespace)
    if module is None:
        spec=importlib.util.spec_from_file_location(namespace,library/'__init__.py',submodule_search_locations=[str(library)])
        module=importlib.util.module_from_spec(spec);sys.modules[namespace]=module;spec.loader.exec_module(module)
    return module.Repository(cfg)

def enqueue_replica(store,asset_id):
    state=store.read();asset=find(state['assets'],asset_id,'asset')
    if asset.get('provenance',{}).get('source')!='native-imagegen':raise StudioError('Replica outbox accepts registered generated book images only')
    path=store.asset_path(asset_id,state);identity(path,asset['bytes'],asset['sha256'])
    repository=replica_repository(store)
    result=repository.enqueue(asset_id,path,asset['sha256'],asset['bytes'])
    result.update(outboxOwned=True,remoteBackupStatus='verified-download' if result['status']=='verified' else 'pending')
    atomic_json(inside(store,'reports/storage/'+asset_id+'-replica-outbox.json'),result)
    return result


@contextmanager
def operation(store):
    """Serialize cache admission and job reservations across app processes."""
    path = inside(store, 'reports/storage/operation.lock')
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)


def bounded_json(path, limit=16384):
    with path.open('rb') as stream:
        raw = stream.read(limit + 1)
    if len(raw) > limit:
        raise StudioError('Storage configuration exceeds its read bound')
    return json.loads(raw)


def inside(store, relative):
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute() or '..' in Path(relative).parts:
        raise StudioError('Storage path must be data-relative')
    path = store.root / relative
    if any(p.is_symlink() for p in [path, *path.parents] if p != store.root.parent):
        raise StudioError('Storage symlinks are refused')
    if not path.resolve().is_relative_to(store.root.resolve()):
        raise StudioError('Storage path escapes data')
    return path


def identity(path, size, digest):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd, 'rb') as stream:
        import stat
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_size != size:
            raise StudioError('Asset byte size differs from registry')
        actual = hashlib.file_digest(stream, 'sha256').hexdigest()
    if actual != digest:
        raise StudioError('Asset SHA-256 differs from registry')
    return actual


def policy(store):
    value = bounded_json(inside(store, 'workflows/storage-policy.json'))
    if value.get('schemaVersion') != 1 or value.get('bucket') != 'miguelemosreverte/mr-pinpin-archive':
        raise StudioError('Unsupported storage policy / book bucket')
    for key in ('maxCacheBytes', 'minFreeBytes', 'generationReserveBytes', 'maxAssetBytes'):
        if type(value.get(key)) is not int or value[key] <= 0:
            raise StudioError('Invalid storage budget')
    adapter = Path(value['adapterPath'])
    if adapter.name != 'hf_store.py' or adapter.is_symlink() or hashlib.sha256(adapter.read_bytes()).hexdigest() != value['adapterSha256']:
        raise StudioError('Existing archive adapter changed; refresh verified configuration')
    if not Path(value['pythonPath']).is_file():
        raise StudioError('Archive Python is unavailable')
    inside(store, value['cachePath'])
    return value


def preflight(store, cfg, required, cache_add=0):
    cache = inside(store, cfg['cachePath'])
    used = 0
    if cache.exists():
        for root, dirs, files in os.walk(cache, followlinks=False):
            for name in dirs + files:
                path = Path(root) / name
                if path.is_symlink():
                    raise StudioError('Cache contains a symlink')
            used += sum((Path(root) / name).stat().st_size for name in files)
    jobs = inside(store, 'reports/character-jobs')
    outstanding = 0
    if jobs.exists():
        paths = list(jobs.glob('*.json'))
        if len(paths) > 1000:
            raise StudioError('Job ledger exceeds preflight bound; retain/archive completed records first')
        for path in paths:
            job = bounded_json(path, 262144)
            if job.get('status') == 'prepared':
                outstanding += cfg['generationReserveBytes']
    free = shutil.disk_usage(store.root).free
    # Resolve runtime locations without reading native history or credentials.
    native_home = Path(os.environ.get('CODEX_HOME', str(Path.home() / '.codex'))).expanduser()
    configured = cfg.get('nativeRuntime', {})
    native_paths = [Path(configured.get(key, str(native_home / suffix))).expanduser()
                    for key, suffix in (('generationPath', 'generated_images'), ('historyPath', 'sessions'), ('runtimeTempPath', 'tmp'))]
    native_paths.append(Path(configured.get('systemTempPath', tempfile.gettempdir())).expanduser())
    native_floor = configured.get('minFreeBytes', cfg['minFreeBytes'])
    native_reserve = configured.get('reserveBytes', cfg['generationReserveBytes'])
    if type(native_floor) is not int or type(native_reserve) is not int or min(native_floor, native_reserve) <= 0:
        raise StudioError('Invalid native volume reserves')
    volumes = {}
    for target in [store.root, *native_paths]:
        probe = target
        while not probe.exists() and probe != probe.parent:
            probe = probe.parent
        device = probe.stat().st_dev
        volume = volumes.setdefault(device, {'device': device, 'paths': [], 'freeBytesObserved': shutil.disk_usage(probe).free,
                                             'minimumFreeBytes': 0, 'reservedBytes': 0})
        volume['paths'].append(str(target))
        is_store = target == store.root
        volume['minimumFreeBytes'] = max(volume['minimumFreeBytes'], cfg['minFreeBytes'] if is_store else native_floor)
        # Add store and native reservations once each per device, not per directory.
        role = 'store' if is_store else 'native'
        if role not in volume:
            volume[role] = True
            volume['reservedBytes'] += (required if is_store else native_reserve) + outstanding
    for volume in volumes.values():
        if volume['freeBytesObserved'] - volume['reservedBytes'] < volume['minimumFreeBytes']:
            raise StudioError('Low disk on generation/history/temp or storage volume; dispatch refused')
    if used + cache_add > cfg['maxCacheBytes']:
        raise StudioError('Bounded cache is full; no artwork is evicted automatically')
    if free - required - outstanding < cfg['minFreeBytes']:
        raise StudioError('Low disk: storage/generation reservation refused before dispatch')
    return {'freeBytesObserved': free, 'cacheBytesObserved': used, 'reservedBytes': required,
            'cacheAdmissionBytes': cache_add, 'outstandingJobReservationBytes': outstanding,
            'uniqueVolumes': list(volumes.values()), 'quotaBytes': None}


def asset_entry(store, asset_id, cfg):
    asset = find(store.read()['assets'], valid_id(asset_id), 'asset')
    size, digest = asset.get('bytes'), asset.get('sha256')
    if type(size) is not int or not 0 < size <= cfg['maxAssetBytes'] or not re.fullmatch('[a-f0-9]{64}', digest or ''):
        raise StudioError('Asset identity is invalid or too large')
    path = inside(store, asset['storagePath'])
    if not path.is_relative_to(store.root / 'assets'):
        raise StudioError('Registered artwork must remain under assets')
    entry = {'path': path.name, 'role': 'archive', 'bytes': size, 'sha256': digest,
             'object': 'sha256/' + digest[:2] + '/' + digest + '/' + path.name}
    return asset, path, entry


def receipt_path(store, asset_id, action):
    return inside(store, 'reports/storage/' + asset_id + '-' + action + '.json')


def transfer(store, cfg, entry, action, root, cache, timeout_seconds=180):
    """Only image bytes and the adapter's minimal hash projection leave this app."""
    projection = inside(store, 'reports/storage/projections/' + entry['sha256'] + '.json')
    atomic_json(projection, {'version': 1, 'bucket': cfg['bucket'], 'assets': [entry]})
    argv = [cfg['pythonPath'], '-B', cfg['adapterPath'], action, '--manifest', str(projection),
            '--root', str(root), '--cache', str(cache), '--workers', '1']
    env = dict(os.environ, HF_HUB_DISABLE_PROGRESS_BARS='1', PYTHONDONTWRITEBYTECODE='1')
    began = time.monotonic()
    result = subprocess.run(argv, capture_output=True, text=True, env=env, timeout=timeout_seconds)
    if result.returncode:
        # Never relay SDK stderr, HTTP bodies, URLs or credential-bearing exceptions.
        raise StudioError('Archive transfer failed; authentication/network/quota status is unknown')
    if len(result.stdout) > 65536:
        raise StudioError('Archive receipt exceeds read bound')
    proof = json.loads(result.stdout)
    rows = proof.get('entries', [])
    if proof.get('verified') is not True or proof.get('dry_run') or proof.get('bucket') != cfg['bucket'] or len(rows) != 1:
        raise StudioError('Archive returned incomplete verification')
    if any(rows[0].get(k) != v for k, v in entry.items()) or rows[0].get('verified') is not True:
        raise StudioError('Archive receipt identity differs from registry')
    return {'adapterReceipt': proof, 'transferSeconds': time.monotonic() - began, 'observedUTC': stamp()}


def backup(store, asset_id):
    cfg = policy(store)
    asset, path, entry = asset_entry(store, asset_id, cfg)
    if asset.get('provenance', {}).get('source') != 'native-imagegen':
        raise StudioError('Backup scope is registered generated book images only')
    identity(path, entry['bytes'], entry['sha256'])
    cache = inside(store, cfg['cachePath'])
    cached = cache / entry['object']
    admission = 0 if cached.exists() else entry['bytes']
    budget = preflight(store, cfg, entry['bytes'] * 2, admission)
    try:
        result = transfer(store, cfg, entry, 'push', path.parent, cache)
    except (StudioError, subprocess.TimeoutExpired):
        atomic_json(receipt_path(store, asset_id, 'backup-attempt'), {
            'assetId': asset_id, 'sha256': entry['sha256'], 'bytes': entry['bytes'],
            'remoteBackupStatus': 'unverified', 'observedUTC': stamp(),
            'errorCategory': 'transfer-unavailable', 'quotaBytes': None})
        raise
    if result['adapterReceipt']['entries'][0].get('remote_verified') is not True:
        raise StudioError('Backup requires fresh downloaded hash verification')
    result.update(assetId=asset_id, sha256=entry['sha256'], bytes=entry['bytes'],
                  remoteBackupStatus='verified-download', budget=budget, assetURL=asset['url'])
    atomic_json(receipt_path(store, asset_id, 'backup'), result)
    return result


def resolve(store, asset_id, restore_replica=False, *, allow_remote=True, timeout_seconds=45):
    if not isinstance(allow_remote, bool) or type(timeout_seconds) not in (int, float) or not 0 < timeout_seconds <= 180:
        raise StudioError('Invalid bounded restore options')
    began = time.monotonic()
    cfg = policy(store)
    asset, canonical, entry = asset_entry(store, asset_id, cfg)
    cache = inside(store, cfg['cachePath'])
    if canonical.exists() and not restore_replica:
        identity(canonical, entry['bytes'], entry['sha256'])
        proof_path = receipt_path(store, asset_id, 'backup')
        proof = bounded_json(proof_path, 65536) if proof_path.exists() else {}
        verified = (proof.get('sha256') == entry['sha256'] and proof.get('bytes') == entry['bytes']
                    and proof.get('remoteBackupStatus') == 'verified-download')
        if inside(store,'workflows/replica-store.json').exists():
            shared=replica_repository(store).status(asset_id,entry['sha256'])
            if shared['status']=='verified':
                return {'assetId':asset_id,'sha256':entry['sha256'],'bytes':entry['bytes'],'nativePath':str(canonical),'assetURL':asset['url'],'source':'verified-local','remoteBackupStatus':'verified-download','sharedReceipt':shared['receipt']}
        return {'assetId': asset_id, 'sha256': entry['sha256'], 'bytes': entry['bytes'],
                'nativePath': str(canonical), 'assetURL': asset['url'], 'source': 'verified-local',
                'remoteBackupStatus': 'verified-download' if verified else 'unverified',
                'replicas': [{'kind': 'local', 'verified': True, 'storagePath': asset['storagePath']}] +
                    ([{'kind': 'huggingface', 'bucket': cfg['bucket'], 'object': entry['object'],
                       'verified': True, 'observedUTC': proof['observedUTC']}] if verified else []),
                'backupReceiptPath': str(receipt_path(store, asset_id, 'backup').relative_to(store.root))}
    proof_path = receipt_path(store, asset_id, 'backup')
    proof = bounded_json(proof_path, 65536) if proof_path.exists() else None
    # Shared namespace first; legacy archive remains a fallback. No original eviction.
    if inside(store,'workflows/replica-store.json').exists():
        try:
            repository=replica_repository(store)
            try:owned=repository.resolve(entry['sha256'],entry['bytes'])
            except FileNotFoundError:
                if not allow_remote:raise StudioError('Selected bytes unavailable locally; remote restore disabled')
                environment=os.environ.copy()
                environment['PYTHONPATH']=str(inside(store,repository.config['libraryPath']))
                process=subprocess.run([cfg['pythonPath'],'-B','-m','replica_store','--config',str(inside(store,'workflows/replica-store.json')),'get',entry['sha256'],str(entry['bytes'])],env=environment,capture_output=True,timeout=max(0.001, timeout_seconds - (time.monotonic() - began)))
                if process.returncode or len(process.stdout)>16384:raise StudioError('Shared remote restoration unavailable')
                response=json.loads(process.stdout)
                if response.get('status')!='verified-local':raise StudioError('Shared remote restoration pending')
                owned=repository.resolve(entry['sha256'],entry['bytes'])
            destination=inside(store,cfg['cachePath']+'/shared/'+entry['sha256']) if restore_replica else canonical
            destination.parent.mkdir(parents=True,exist_ok=True)
            preflight(store,cfg,entry['bytes']*2,entry['bytes'])
            fd,name=tempfile.mkstemp(prefix='.shared-restore-',dir=destination.parent)
            os.close(fd)
            try:
                shutil.copyfile(owned,name);identity(Path(name),entry['bytes'],entry['sha256'])
                with open(name,'rb') as stream:os.fsync(stream.fileno())
                try:os.link(name,destination,follow_symlinks=False)
                except FileExistsError:identity(destination,entry['bytes'],entry['sha256'])
            finally:os.unlink(name)
            shared=repository.status(asset_id,entry['sha256'])
            result={'assetId':asset_id,'sha256':entry['sha256'],'bytes':entry['bytes'],'nativePath':str(destination),'assetURL':asset['url'],'source':'shared-verified-bytes','remoteBackupStatus':'verified-download' if shared['status']=='verified' else 'unverified'}
            atomic_json(receipt_path(store,asset_id,'shared-restore'),result)
            return result
        except (ValueError,OSError,StudioError,subprocess.TimeoutExpired):
            if not proof:raise StudioError('Verified shared reference unavailable; retry host get or restore legacy archive')
    if not allow_remote:
        raise StudioError('Selected bytes unavailable locally; remote restore disabled')
    if not proof or proof.get('sha256') != entry['sha256'] or proof.get('bytes') != entry['bytes'] or proof.get('remoteBackupStatus') != 'verified-download':
        raise StudioError('No verified remote-backup receipt for this asset')
    # Replica restoration demonstrates a cold cache without deleting canonical artwork.
    root = cache / 'materialized' if restore_replica else canonical.parent
    if restore_replica:
        cache = cache / 'restoration'
    cached = cache / entry['object']
    admission = (0 if cached.exists() else entry['bytes'])
    if restore_replica and not (root / entry['path']).exists():
        admission += entry['bytes']
    budget = preflight(store, cfg, entry['bytes'] * 2, admission)
    remaining = timeout_seconds - (time.monotonic() - began)
    if remaining <= 0:raise StudioError('Selected restore timed out; retry bounded request')
    result = transfer(store, cfg, entry, 'pull', root, cache, timeout_seconds=remaining)
    destination = root / entry['path']
    identity(destination, entry['bytes'], entry['sha256'])
    result.update(assetId=asset_id, sha256=entry['sha256'], bytes=entry['bytes'], nativePath=str(destination),
                  assetURL=asset['url'], source=result['adapterReceipt']['entries'][0]['status'], budget=budget)
    atomic_json(receipt_path(store, asset_id, 'restore'), result)
    return result


def prepare(store, spec):
    """Validate the actual character job before its native tool is invoked."""
    cfg = policy(store)
    entity = valid_id(spec.get('entityId'), 'character id')
    character = find(store.read()['project']['entities'], entity, 'character')
    if character.get('kind') != 'character':
        raise StudioError('Prepared subject must be a character')
    folder = 'workflows/characters/' + entity + '/'
    dossier = inside(store, folder + 'README.md')
    evidence = inside(store, folder + 'evidence.json')
    if not dossier.is_file() or dossier.stat().st_size > 65536:
        raise StudioError('Prepare a bounded character dossier with source/proposal and age evidence')
    indexed = bounded_json(evidence, 262144)
    if not isinstance(indexed.get('bibliography'), list):
        raise StudioError('Character evidence needs a bibliography, empty only for a disclosed proposal')
    if spec.get('stage') not in ('solo', 'interactions'):
        raise StudioError('Character package requires solo or interactions stage')
    prompt = spec.get('prompt')
    if not isinstance(prompt, str) or not 1 <= len(prompt.encode()) <= 100000:
        raise StudioError('Exact submitted prompt is required')
    if spec.get('promptFile'):
        submitted = inside(store, spec['promptFile']) if not Path(spec['promptFile']).is_absolute() else Path(spec['promptFile'])
        if not submitted.resolve().is_relative_to(store.root.resolve()) or submitted.is_symlink():
            raise StudioError('Prompt file must remain under data without symlinks')
        with submitted.open('rb') as stream:
            submitted_bytes = stream.read(100001)
        if submitted_bytes != prompt.encode():
            raise StudioError('Prompt file must contain the exact prepared prompt under data')
    refs = spec.get('references')
    if not isinstance(refs, list) or not 1 <= len(refs) <= 5 or len({r.get('assetId') for r in refs}) != len(refs):
        raise StudioError('Prepare one to five unique registered inputs before dispatch')
    if any(not isinstance(r.get('role'), str) or not r['role'].strip() for r in refs):
        raise StudioError('Every input requires an identity/counterpart/layout/style role')
    name = spec.get('outputName')
    if not isinstance(name, str) or Path(name).name != name or not name.endswith(('.png', '.webp', '.jpg')):
        raise StudioError('Output requires a plain image filename')
    toolchain = bounded_json(inside(store, 'workflows/toolchain.json'))
    if toolchain.get('imageGeneration', {}).get('tool') != 'image_gen.imagegen':
        raise StudioError('Prepared native image tool is unavailable or changed')
    if spec['stage'] == 'interactions':
        # Resolve requested target bytes before reconciling the actual stage receipt.
        resolve(store, refs[0]['assetId'])
        from .cast_workflow import reconcile_character
        stage = reconcile_character(store, store.read(), {'id': entity}).get('stages', {}).get('solo')
        if not stage or refs[0]['assetId'] != stage['assetId'] or 'primary' not in refs[0]['role'].lower():
            raise StudioError('Interactions must start with the current target solo as PRIMARY identity')
    retry = spec.get('retryOfAttempt')
    if retry is not None:
        if not isinstance(retry, str) or not re.fullmatch('[a-f0-9]{24}', retry):
            raise StudioError('Retry must identify an actual prepared attempt')
        prior = bounded_json(inside(store, 'reports/character-jobs/' + retry + '.json'), 262144)
        if prior.get('entityId') != entity or prior.get('stage') != spec['stage'] or prior.get('status') not in ('registered', 'failed'):
            raise StudioError('Retry lineage must match a real finished/failed subject stage')
        if not isinstance(spec.get('retryReason'), str) or not spec['retryReason'].strip():
            raise StudioError('Retain the actual retry reason')
    budget = preflight(store, cfg, cfg['generationReserveBytes'])
    resolved = []
    for ref in refs:
        value = resolve(store, ref['assetId'])
        if ref.get('sha256') and ref['sha256'] != value['sha256']:
            raise StudioError('Prepared reference hash differs from registry')
        resolved.append(dict(ref, **{k: value[k] for k in ('nativePath', 'sha256', 'bytes')}))
    attempt = hashlib.sha256((entity + spec['stage'] + prompt + stamp()).encode()).hexdigest()[:24]
    receipt = dict(spec, references=resolved, attemptId=attempt, status='prepared', preparedUTC=stamp(),
                   dossierPath=folder + 'README.md', evidencePath=folder + 'evidence.json',
                   dossierSha256=hashlib.sha256(dossier.read_bytes()).hexdigest(),
                   evidenceSha256=hashlib.sha256(evidence.read_bytes()).hexdigest(),
                   budget=budget, tool='image_gen.imagegen', outputRequirements={
                       'nativeBytes': True, 'maxBytes': cfg['maxAssetBytes'], 'registeredCandidate': True,
                       'visualQA': 'Every direction/subject, species, scale, contact and anatomy',
                       'stages': ['solo', 'interactions'], 'approval': 'Unreviewed draft; no publication'})
    atomic_json(inside(store, 'reports/character-jobs/' + attempt + '.json'), receipt)
    return receipt


def outcome(store, body):
    attempt = body.get('attemptId')
    if not isinstance(attempt, str) or not re.fullmatch('[a-f0-9]{24}', attempt):
        raise StudioError('Invalid prepared attempt')
    path = inside(store, 'reports/character-jobs/' + attempt + '.json')
    record = bounded_json(path, 262144)
    if body.get('status') not in ('failed', 'registered', 'cancelled'):
        raise StudioError('Outcome must be failed, registered or cancelled')
    if record['status'] != 'prepared':
        if record.get('outcome') == body:
            return record
        raise StudioError('Attempt outcome already recorded')
    if body['status'] == 'registered':
        resolved = resolve(store, body.get('assetId'))
        asset = find(store.read()['assets'], resolved['assetId'], 'asset')
        provenance = asset.get('provenance', {})
        if provenance.get('prompt') != record['prompt'] or provenance.get('referenceIds') != [r['assetId'] for r in record['references']]:
            raise StudioError('Registered outcome prompt/inputs differ from prepared job')
    record.update(status=body['status'], outcome=body, completedUTC=stamp())
    atomic_json(path, record)
    return record


def registration_preflight(store, body):
    attempt = body.get('attemptId')
    if not isinstance(attempt, str) or not re.fullmatch('[a-f0-9]{24}', attempt):
        raise StudioError('Registration needs a real prepared attempt')
    record = bounded_json(inside(store, 'reports/character-jobs/' + attempt + '.json'), 262144)
    size = body.get('nativeBytes')
    cfg = policy(store)
    if record.get('status') != 'prepared' or type(size) is not int or not 0 < size <= cfg['maxAssetBytes']:
        raise StudioError('Native output size or prepared status is invalid')
    return {'attemptId': attempt, 'budget': preflight(store, cfg, size * 2), 'nativeBytes': size}


def hydrate_selected(store, asset_ids, *, restore=False, byte_budget=33554432, timeout_seconds=45):
    """Metadata-only by default; exact selected-ID restore runs off the UI paint path.

    Internal workflows may choose restore for already authorized generation/reference
    preparation. No extra human permission, approval transition, archive crawl or bulk
    gallery migration. Existing configured replica/archive adapters supply bytes.
    """
    if not isinstance(asset_ids, list) or not 1 <= len(asset_ids) <= 4 or any(not isinstance(identifier, str) for identifier in asset_ids) or len(set(asset_ids)) != len(asset_ids):
        raise StudioError('Select one to four unique registered asset IDs')
    if type(byte_budget) is not int or not 0 < byte_budget <= 67108864:
        raise StudioError('Selected restore byte budget must be at most64MiB')
    if type(timeout_seconds) not in (int, float) or not 0 < timeout_seconds <= 60:
        raise StudioError('Selected restore timeout must be at most60seconds')
    if type(restore) is not bool:raise StudioError('restore must be boolean')
    began=time.monotonic();cfg=policy(store);rows=[]
    for identifier in asset_ids:
        asset,path,entry=asset_entry(store,identifier,cfg)
        rows.append({'assetId':asset['id'],'sha256':entry['sha256'],'bytes':entry['bytes'],
                     'assetURL':asset['url'],'reviewStatus':asset.get('reviewStatus','unknown'),'roles':asset.get('roles',[]),'availability':'local-unverified' if path.exists() else 'missing'})
    missing=sum(row['bytes'] for row in rows if row['availability']=='missing')
    if missing>byte_budget:raise StudioError('Selected missing bytes exceed request budget')
    result={'assets':rows,'missingBytes':missing,'byteBudget':byte_budget,'restoreRequested':restore,
            'networkAllowed':restore,'remoteBackupStatus':'unverified','scope':'exact selected registered IDs only'}
    if restore:
        result['results']=[]
        with operation(store):
            for row in rows:
                remaining=timeout_seconds-(time.monotonic()-began)
                if remaining<=0:
                    result['results'].append({'assetId':row['assetId'],'status':'pending','reason':'request-timeout'});continue
                try:
                    value=resolve(store,row['assetId'],timeout_seconds=remaining)
                    result['results'].append(dict(value,status='ready'))
                except (StudioError,OSError,ValueError,subprocess.TimeoutExpired) as exc:
                    result['results'].append({'assetId':row['assetId'],'status':'pending','errorType':type(exc).__name__})
    result['elapsedMs']=round((time.monotonic()-began)*1000,3)
    return result
