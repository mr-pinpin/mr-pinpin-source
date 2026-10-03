"""Use the active verified business bundle and prepared image registration argv."""
import json
import subprocess
import sys
import hashlib
import time
from datetime import datetime, timezone
from pathlib import Path

DATA = Path(__file__).resolve().parents[1]
RUNTIME = Path('/Volumes/TB4/mac-mini-storage/shared/pinpin-studio-runtime')
deployment = json.loads((RUNTIME / 'current-deployment.json').read_text())
sys.path.insert(0, str(RUNTIME / 'stable-releases' / deployment['stableRelease']))
from store import Store, atomic_json
from business_runtime import BusinessRuntime

def server_backup(asset_id):
    """Use existing Studio client's URL/transport, with its loopback guard intact."""
    import importlib.util
    import os
    client_dir=Path('/Volumes/TB4/mac-mini-storage/shared/pinpin-r17-studio-source/tools/studio-client')
    sys.path.insert(0,str(client_dir))
    spec=importlib.util.spec_from_file_location('studio_chat_client',client_dir/'chat.py')
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    client=module.Client(os.environ.get('PINPIN_STUDIO_URL','http://127.0.0.1:18826'))
    parsed=module.urllib.parse.urlsplit(client.url)
    if parsed.scheme!='http' or parsed.hostname not in ('127.0.0.1','localhost','::1') or parsed.path:
        raise ValueError('Closeout requires the existing loopback Studio HTTP server')
    request=module.urllib.request.Request(client.url+'/api/storage/backup',
        data=json.dumps({'assetId':asset_id}).encode(),
        headers={'Content-Type':'application/json','Accept':'application/json'})
    # No automatic POST retries: the server may finish after a lost response.
    with module.urllib.request.urlopen(request,timeout=200) as response:
        raw=response.read(1024*1024+1)
    if len(raw)>1024*1024: raise ValueError('Oversized storage response')
    return json.loads(raw)

def verified_backup(result, asset):
    if not isinstance(result,dict): return False
    if any(result.get(k)!=asset.get(v) for k,v in (('assetId','id'),('sha256','sha256'),('bytes','bytes'))): return False
    proof=result.get('adapterReceipt',{})
    entries=proof.get('entries',[])
    expected_bucket=json.loads((DATA/'workflows/storage-policy.json').read_text())['bucket']
    return (result.get('remoteBackupStatus')=='verified-download' and proof.get('verified') is True
        and proof.get('bucket')==expected_bucket and proof.get('dry_run') is not True
        and len(entries)==1 and entries[0].get('remote_verified') is True
        and entries[0].get('verified') is True and entries[0].get('sha256')==asset['sha256']
        and entries[0].get('bytes')==asset['bytes'])

def closeout(runtime,store,identifier,transfer=server_backup):
    """Existing finish validation plus bounded server-side final-page backups."""
    from model import valid_id
    valid_id(identifier)
    started=time.monotonic()
    package=json.loads((DATA/'reports/character-packages'/(identifier+'.json')).read_text())
    ids=[package['stages'][role]['candidates'][-1]['assetId'] for role in ('solo','interactions')]
    completion_path=DATA/'reports/character-packages'/(identifier+'-completion.json')
    old=json.loads(completion_path.read_text()) if completion_path.exists() else None
    _,result=runtime.invoke('route',store,'POST','/api/cast/finish',{},
        {'entityId':identifier,'assetIds':ids,'qaNote':'Retained recorded visual QA; closeout validates registered final bytes, not human approval.',
         'timingPath':'reports/character-packages/'+identifier+'-generation.json'})
    # Completed benchmark records stay byte-for-byte intact; new jobs reuse normal finish.
    if not old or old.get('stages')!=result['stages']: finish_records(identifier,result)
    assets={a['id']:a for a in store.read()['assets']}
    backups=[]
    for asset_id in ids:
        asset=assets[asset_id]
        path=store.asset_path(asset_id)
        if path.stat().st_size!=asset['bytes'] or hashlib.sha256(path.read_bytes()).hexdigest()!=asset['sha256']:
            raise ValueError('Final registered bytes failed verification')
        receipt_path=DATA/'reports/storage'/(asset_id+'-backup.json')
        existing=json.loads(receipt_path.read_text()) if receipt_path.exists() else None
        row={'assetId':asset_id,'sha256':asset['sha256'],'bytes':asset['bytes'],'localVerified':True}
        try:
            reused=verified_backup(existing,asset)
            remote=existing if reused else transfer(asset_id)
            if not verified_backup(remote,asset): raise ValueError('Remote proof did not match final asset')
            row.update(remoteBackupStatus='verified-download',receiptPath=str(receipt_path.relative_to(DATA)),
                verificationSource='existing-server-receipt' if reused else 'this-command-server-response')
        except Exception as exc:
            row.update(remoteBackupStatus='failed-or-pending',errorType=type(exc).__name__,
                transportErrno=getattr(getattr(exc,'reason',None),'errno',None),
                advice='Local draft retained. Inspect server backup receipt before a manual retry; no POST retry performed.')
        backups.append(row)
    receipt={'schemaVersion':1,'entityId':identifier,'observedUTC':datetime.now(timezone.utc).isoformat(),
        'localDraftComplete':True,'pages':backups,'allRemoteVerified':all(r['remoteBackupStatus']=='verified-download' for r in backups),
        'closeoutSeconds':time.monotonic()-started,'benchmarkHistoryChanged':False,
        'transferBoundary':'Existing loopback Studio HTTP business route /api/storage/backup; server-owned HF adapter credentials',
        'workflowCard':result.get('workflowCard'),'approval':'Agent QA only; no human approval, selection or publication'}
    target=DATA/'reports/character-packages'/(identifier+'-closeout.json');atomic_json(target,receipt)
    return receipt

def closeout_checkpoint(receipt):
    """Export final authored bytes and read back once, without touching benchmark history."""
    mappings={'tools/cast_ops.py':'industrial-cast_ops.py',
        'tools/test_character_closeout.py':'test_character_closeout.py',
        'workflows/toolchain.json':'industrial-toolchain.json',
        'workflows/character-creation.md':'industrial-character-creation.md',
        'workflows/character-context-index.md':'industrial-character-context-index.md',
        'workflows/industrial-storage.md':'industrial-storage.md'}
    files=[]
    for source,target in mappings.items():
        src=DATA/source; dst=DATA/'exports'/target;dst.write_bytes(src.read_bytes())
        for path in (src,dst):
            files.append({'path':str(path.relative_to(DATA)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'bytes':path.stat().st_size})
    for name in ('reports/character-closeout-focused-proof.json','reports/character-packages/'+receipt['entityId']+'-closeout.json'):
        path=DATA/name;files.append({'path':name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'bytes':path.stat().st_size})
    target=DATA/'exports/character-closeout-source-receipt.json'
    atomic_json(target,{'observedUTC':datetime.now(timezone.utc).isoformat(),'files':files,
        'localDraftComplete':receipt['localDraftComplete'],'allRemoteVerified':receipt['allRemoteVerified'],
        'focusedProof':'reports/character-closeout-focused-proof.json','credentialsIncluded':False,
        'benchmarkHistoryChanged':False,'generationTimeImprovementClaimed':False,'secondBenchmarkPerformed':False})
    for row in files:
        path=DATA/row['path'];assert path.stat().st_size==row['bytes'] and hashlib.sha256(path.read_bytes()).hexdigest()==row['sha256']
    return str(target)

def rank_reference_pack(references):
    """Rank/cap native image inputs using saved tool policy; retain all omissions."""
    policy=json.loads((DATA/'workflows/toolchain.json').read_text()).get('imageGeneration',{})
    limit=policy.get('maxInputReferences',5)
    if not isinstance(limit,int) or not 1 <= limit <= 5:
        raise ValueError('Native image reference limit must be between one and five')
    order=policy.get('rolePriority',['PRIMARY','identity','counterpart','layout','style','context'])
    def rank(ref):
        role=ref.get('role','').lower()
        kind=('PRIMARY' if 'primary' in role or 'edit-target' in role else 'counterpart' if 'counterpart' in role
              else 'layout' if 'layout' in role else 'style' if 'style' in role else 'identity' if 'identity' in role else 'context')
        return order.index(kind) if kind in order else len(order)
    unique={}
    for ref in sorted(references,key=rank):
        unique.setdefault(ref['assetId'],ref)
    ranked=list(unique.values())
    return ranked[:limit],ranked[limit:]

def finish_records(identifier, result):
    """Derive closeout metadata from existing real call receipts, preserving evidence."""
    path = DATA / 'reports/character-packages' / (identifier + '-generation.json')
    record = json.loads(path.read_text())
    calls = record['calls']
    recovered = record.get('recoveredCalls', [])
    parse = lambda s: datetime.strptime(s, '%Y-%m-%d %H:%M:%S UTC')
    record['metrics'] = {'imageCalls': len(calls) + len(recovered), 'measuredImageCalls': len(calls),
        'recoveredRendersWithoutMeasuredBounds': len(recovered), 'repairCalls': sum(bool(c.get('repair')) for c in calls + recovered),
        'summedImageCallWindowSeconds': sum((parse(c['generationAfterUTC'])-parse(c['generationBeforeUTC'])).total_seconds() for c in calls),
        'registrationSeconds': sum(c['receipt']['timing']['registrationSeconds'] for c in calls + recovered),
        'firstPassBodyDirectionErrors': calls[0].get('firstPassBodyWrongCells', []), 'endToEndSeconds': None, 'monetaryCost': None}
    record.update(finalStages=result['stages'], status='produced')
    folder = DATA / 'workflows/characters' / identifier
    atomic_json(path, record)
    atomic_json(folder / 'generation.json', record)
    ep = folder / 'evidence.json'; evidence = json.loads(ep.read_text())
    evidence.update(finalStages=result['stages'], generationRecord='generation.json')
    atomic_json(ep, evidence)
    doc = folder / 'README.md'; text = doc.read_text()
    start, end = '<!-- cast-ops metrics begin -->', '<!-- cast-ops metrics end -->'
    if start in text and end in text:
        before, tail = text.split(start, 1); text = before + tail.split(end, 1)[1]
    m = record['metrics']
    doc.write_text(text.rstrip()+f'\n\n{start}\n## Measured generation and decisions\n\n[Exact prompts, input roles, lineage and timings](generation.json). {m["imageCalls"]} retained native renders ({m["measuredImageCalls"]} with measured call windows, {len(recovered)} recovered without boundaries); {m["repairCalls"]} repairs; {m["summedImageCallWindowSeconds"]:.0f}s summed measured submitted-call windows. Registration {m["registrationSeconds"]:.6f}s separately measured. First-pass body errors: {m["firstPassBodyDirectionErrors"]}. These are not end-to-end latency or parallel-compute measurements; billing is unknown. Retained candidates, attribution limits and repair reasons remain in generation.json. Agent QA, no personal Miguel approval.\n{end}\n')
    result['metrics'] = m
    result['generationPath'] = str(path.relative_to(DATA))
    atomic_json(DATA / 'reports/character-packages' / (identifier + '-completion.json'), result)
    return result

def complete_inventory(store, run):
    """Export the reconciled complete queue, preserving source and legacy receipts."""
    state = store.read()
    assets = {a['id']: a for a in state.get('assets', [])}
    bindings = state['project']['book'].get('characterReferenceDefaults', {}).get('characters', {})
    entries = []
    lines = ['# Complete cast draft inventory', '',
        'All final stages below were reconciled against real registered assets, SHA-256 hashes and image bytes. Produced drafts and agent QA remain separate from human acceptance, story-reference selection and publication.', '',
        'Notetaker is unavailable. Character Markdown dossiers, source bibliography and retained receipts are the durable fallback. Missing historical generation, delivery or billing measurements remain unknown.', '',
        '| Character | Final solo | Final interactions | Age / life stage | Records |',
        '| --- | --- | --- | --- | --- |']
    for row in run['characters']:
        identifier = row['id']
        if not row['complete']: raise ValueError('Complete inventory requires every real stage')
        folder = DATA/'workflows/characters'/identifier
        doc = folder/'README.md'; evidence = folder/'evidence.json'
        package = DATA/'reports/character-packages'/(identifier+'.json')
        if not all(p.is_file() for p in (doc, evidence, package)): raise ValueError('Missing dossier/receipt: '+identifier)
        source = json.loads(evidence.read_text())
        receipt = json.loads(package.read_text())
        finals = {}
        for stage, verified in row['stages'].items():
            candidate = next(c for c in receipt['stages'][stage]['candidates'] if c['assetId']==verified['assetId'] and c['sha256']==verified['sha256'])
            asset = assets.get(verified['assetId'])
            if asset is None: raise ValueError('Verified asset missing from current registry: '+identifier)
            finals[stage] = dict(verified, registeredPath=str(store.asset_path(verified['assetId'])),
                provenance=asset.get('provenance', {}), candidateReceipt=candidate,
                retainedAttemptCount=len(receipt['stages'][stage]['candidates']))
        generation = folder/'generation.json'
        entry = {'id': identifier, 'canonicalName': row.get('canonicalName', identifier),
            'exactAge': row.get('exactAge', 'not stated'), 'evidencedLifeStage': row.get('evidencedLifeStage', 'See sourced dossier'),
            'status': 'produced', 'finalStages': finals,
            'dossierPath': str(doc.relative_to(DATA)), 'dossierText': doc.read_text(),
            'evidencePath': str(evidence.relative_to(DATA)), 'sourceBibliography': source.get('bibliography', []),
            'inspectedVisualEvidence': source.get('inspectedVisualEvidence', []),
            'designBasis': bindings.get(identifier, {}).get('designBasis', 'See preserved source/proposal distinctions in dossier and indexed evidence'),
            'sourceAndRoleBinding': bindings.get(identifier, {}), 'receiptPath': str(package.relative_to(DATA)),
            'stageReceipts': receipt,
            'generationPath': str(generation.relative_to(DATA)) if generation.is_file() else None,
            'generationRecord': json.loads(generation.read_text()) if generation.is_file() else None,
            'legacyTimingAndPromptReports': sorted({p for role in receipt['stages'].values() for c in role['candidates'] for p in c.get('sourceReportPaths', [])}),
            'authority': 'Agent QA / draft production only; no invented personal Miguel approval or publication'}
        entries.append(entry)
        stage_link = lambda role: '['+finals[role]['assetId']+']('+finals[role]['registeredPath']+')'
        lines.append('| '+entry['canonicalName']+' | '+stage_link('solo')+' | '+stage_link('interactions')+' | '+entry['exactAge']+'; '+entry['evidencedLifeStage'].replace('|','/')+' | [Dossier](../'+entry['dossierPath']+') · [Evidence](../'+entry['evidencePath']+') · [Receipts](../'+entry['receiptPath']+') |')
    payload = {'schemaVersion': 1, 'producedCount': len(entries), 'remaining': [], 'characters': entries,
        'notetaker': 'Unavailable; truthful durable Markdown fallback', 'timingLimits': 'Per-attempt generation and registration receipts; unknown historical, delivery and billing values remain unknown.'}
    paths = [DATA/'reports/cast-complete-inventory.json', DATA/'reports/cast-complete-inventory.md']
    atomic_json(paths[0], payload); paths[1].write_text('\n'.join(lines)+'\n')
    return paths

def checkpoint(runtime, store, batch, identifiers):
    began = time.monotonic()
    _, run = runtime.invoke('route', store, 'POST', '/api/cast/reconcile', {}, {})
    rows = {c['id']: c for c in run['characters']}
    records = []
    for identifier in identifiers:
        if not rows[identifier]['complete']:
            raise ValueError('Incomplete package: '+identifier)
        result = json.loads((DATA/'reports/character-packages'/(identifier+'-completion.json')).read_text())
        if result['stages'] != rows[identifier]['stages']:
            raise ValueError('Completion receipt differs from verified stages: '+identifier)
        records.append(result)
    windows=[]
    parse=lambda s:datetime.strptime(s,'%Y-%m-%d %H:%M:%S UTC')
    for identifier in identifiers:
        record=json.loads((DATA/'reports/character-packages'/(identifier+'-generation.json')).read_text())
        windows.extend((parse(c['generationBeforeUTC']),parse(c['generationAfterUTC'])) for c in record['calls'])
    merged=[]
    for a,b in sorted(windows):
        if merged and a<=merged[-1][1]:merged[-1]=(merged[-1][0],max(b,merged[-1][1]))
        else:merged.append((a,b))
    remaining=[c['id'] for c in run['characters'] if not c['complete']]
    result={'batch':batch,'characters':records,'remaining':remaining,'nextEntityId':run['nextEntityId'], 'producedCount':sum(c['complete'] for c in run['characters']),
        'imageCalls':sum(r['metrics']['imageCalls'] for r in records),'repairCalls':sum(r['metrics']['repairCalls'] for r in records),
        'measuredImageCalls':sum(r['metrics'].get('measuredImageCalls',r['metrics']['imageCalls']) for r in records),
        'recoveredRendersWithoutMeasuredBounds':sum(r['metrics'].get('recoveredRendersWithoutMeasuredBounds',0) for r in records),
        'sumImageWindowsSeconds':sum(r['metrics']['summedImageCallWindowSeconds'] for r in records),
        'unionSubmittedWindowsSeconds':sum((b-a).total_seconds() for a,b in merged),
        'firstToLastImageSpanSeconds':(max(b for a,b in windows)-min(a for a,b in windows)).total_seconds(),
        'limits':'Submission/return windows, not compute or full-turn latency. Billing and unobserved delivery bounds unknown.'}
    summary=DATA/'reports'/('cast-'+batch+'-summary.json')
    contract=DATA/'workflows/cast-run.md'; old=contract.read_text()
    archive=DATA/'reports'/('cast-before-'+batch+'-checkpoint.md')
    if not archive.exists():archive.write_text(old)
    retained=old[old.index('## Verified batch:'):] if '## Verified batch:' in old else ''
    new=f'# Durable cast run\n\n## Current checkpoint: {batch}\n\n{result["producedCount"]} complete draft packages; {len(remaining)} remain. Next: {run["nextEntityId"]}. Remaining in order: '+', '.join(remaining)+'.\n\n'
    new+=f'{result["imageCalls"]} retained native renders ({result["measuredImageCalls"]} measured, {result["recoveredRendersWithoutMeasuredBounds"]} recovered without call bounds); {result["repairCalls"]} repairs; summed measured image windows {result["sumImageWindowsSeconds"]:.0f}s, union {result["unionSubmittedWindowsSeconds"]:.0f}s, image span {result["firstToLastImageSpanSeconds"]:.0f}s. Limits: '+result['limits']+'\n\n'
    new+=f'Finished: '+', '.join(identifiers)+f'. Exact prompts, source/proposal distinctions, visual QA, stages and timings remain in character folders and standard receipts. Existing artwork preserved. [Batch summary](../reports/cast-{batch}-summary.json). [Prior checkpoint](../reports/cast-before-{batch}-checkpoint.md). Notetaker unavailable; durable Markdown fallback.\n\nUse `python -B tools/cast_ops.py finish <entity>` after real visual QA, then `python -B tools/cast_ops.py checkpoint <batch> <entity> ...` once per batch. Receipt IDs/hashes are read programmatically; curated evidence is retained.\n\n'+retained
    inventory_paths = complete_inventory(store, run) if not remaining else []
    if inventory_paths:
        new += '\n[Complete '+str(result['producedCount'])+'-entry draft-stage inventory](../reports/cast-complete-inventory.md). [Full source, prompt, reference, attempt and timing receipt inventory](../reports/cast-complete-inventory.json).\n'
    if len(new.encode())>10000:raise ValueError('Contract exceeds bounded context limit')
    contract.write_text(new)
    defaults=DATA/'exports/cast-reference-defaults.json'
    atomic_json(defaults,store.read()['project']['book'].get('characterReferenceDefaults',{}))
    paths=[contract,DATA/'workflows/cast-run.json',DATA/'workflows/character-creation.md',DATA/'workflows/toolchain.json',Path(__file__),defaults]+inventory_paths
    for identifier in identifiers:
        folder=DATA/'workflows/characters'/identifier
        paths.extend(p for p in sorted(folder.iterdir()) if p.is_file() and p.suffix in ('.md','.json','.txt'))
        paths.extend(DATA/'reports/character-packages'/(identifier+suffix) for suffix in ('.json','-generation.json','-completion.json'))
    paths.extend(p for p in (DATA/'reports/cast-closeout-proof.json',DATA/'reports/cast-batch05-input-attempt.json') if p.is_file())
    if inventory_paths:
        paths.extend(p for p in (DATA/'exports/workflows-README.md', DATA/'exports/test_business_routes.py',
            DATA/'exports/test_cast_closeout.py', DATA/'exports/final-cast-source-receipt.json',
            DATA/'tools/test_cast_closeout.py', DATA/'tools/register_cast_spec.py',
            DATA/'tools/verify-cast-active.py') if p.is_file())
    metadata=[{'path':str(p.relative_to(DATA)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in paths]
    atomic_json(DATA/'exports'/('cast-'+batch+'-checkpoint-receipt.json'),{'files':metadata,'imageBinariesIncluded':False,'approvalInvented':False})
    # One bounded readback of the prepared files; no broad engineering suite.
    for item in metadata:
        if hashlib.sha256((DATA/item['path']).read_bytes()).hexdigest()!=item['sha256']:raise ValueError('Readback changed: '+item['path'])
    result['checkpointSeconds']=time.monotonic()-began
    result['checkpointObservedUTC']=datetime.now(timezone.utc).isoformat()
    atomic_json(summary,result)
    return {k:result[k] for k in ('batch','producedCount','remaining','nextEntityId','imageCalls','measuredImageCalls','recoveredRendersWithoutMeasuredBounds','repairCalls','sumImageWindowsSeconds','unionSubmittedWindowsSeconds','firstToLastImageSpanSeconds','checkpointSeconds')}

def main():
    runtime = BusinessRuntime(None, RUNTIME, watch=False, read_only=True)
    store = Store(DATA)
    command, *args = sys.argv[1:]
    if command == 'industrial-checkpoint':
        print(json.dumps(industrial_checkpoint(store)))
    elif command == 'closeout':
        result=closeout(runtime,store,args[0])
        result['sourceExportReceipt']=closeout_checkpoint(result)
        print(json.dumps(result))
    elif command in ('resolve', 'backup', 'restore-replica', 'prepare', 'outcome'):
        if command in ('prepare', 'outcome'):
            body = json.loads(Path(args[0]).read_text())
            endpoint = '/api/characters/' + command
        else:
            body = {'assetId': args[0], 'restoreReplica': command == 'restore-replica'}
            endpoint = '/api/storage/' + ('backup' if command == 'backup' else 'resolve')
        _, result = runtime.invoke('route', store, 'POST', endpoint, {}, body)
        if command == 'prepare':
            atomic_json(Path(args[0]).with_suffix('.prepared.json'), result)
        print(json.dumps(result))
    elif command == 'register':
        cfg = json.loads((DATA / 'workflows/toolchain.json').read_text())
        receipt = json.loads(subprocess.check_output(cfg['argvPrefix'] + args, text=True))
        _, run = runtime.invoke('route', store, 'POST', '/api/cast/reconcile', {}, {})
        print(json.dumps({'receipt': receipt, 'next': run['nextEntityId']}))
    elif command == 'reconcile':
        _, run = runtime.invoke('route', store, 'POST', '/api/cast/reconcile', {}, {})
        print(json.dumps({'next': run['nextEntityId'], 'remaining': [c['id'] for c in run['characters'] if not c.get('complete')]}))
    elif command == 'finish':
        identifier = args[0]
        if len(args) == 1:
            package = json.loads((DATA / 'reports/character-packages' / (identifier + '.json')).read_text())
            solo, interactions = [package['stages'][role]['candidates'][-1]['assetId'] for role in ('solo', 'interactions')]
        else:
            identifier, solo, interactions = args
        _, result = runtime.invoke('route', store, 'POST', '/api/cast/finish', {}, {'entityId': identifier, 'assetIds': [solo, interactions],
            'qaNote': 'Inspected native pages: identity, directions, anatomy, scale/contact. Agent QA only; no personal Miguel approval.',
            'timingPath': str(Path('reports/character-packages') / (identifier + '-generation.json'))})
        print(json.dumps(finish_records(identifier, result)))
    elif command == 'checkpoint':
        print(json.dumps(checkpoint(runtime, store, args[0], args[1:])))
    runtime.close()

def industrial_checkpoint(store):
    """One source/export receipt update and readback for the scoped storage sprint."""
    source = Path('/Volumes/TB4/mac-mini-storage/shared/pinpin-r17-studio-source/tools/studio/business')
    proof = json.loads((DATA/'reports/industrial-storage-focused-proof.json').read_text())
    fresh = json.loads((DATA/'reports/industrial-storage-fresh-context.json').read_text())
    policy = json.loads((DATA/'workflows/storage-policy.json').read_text())
    package = json.loads((DATA/'reports/character-packages/pinpin.json').read_text())
    qa_root=Path('/Volumes/TB4/mac-mini-storage/shared/pinpin-industrial-20261003')
    live_backup=json.loads((qa_root/'storage-live-cli-backup.json').read_text())
    live_restore=json.loads((qa_root/'storage-live-cli-restore.json').read_text())
    identifier = live_backup['assetId']
    asset = next(a for a in store.read()['assets'] if a['id']==identifier)
    canonical = store.asset_path(identifier)
    canonical_ok = canonical.stat().st_size == asset['bytes'] and hashlib.sha256(canonical.read_bytes()).hexdigest()==asset['sha256']
    assert canonical_ok
    assert live_restore['assetId']==identifier and live_restore['source']=='downloaded'
    for item in (live_backup,live_restore):
        entry=item['adapterReceipt']['entries'][0]
        assert item['sha256']==asset['sha256'] and item['bytes']==asset['bytes']
        assert item['adapterReceipt']['verified'] and entry['remote_verified'] and entry['verified']
    restored=Path(live_restore['nativePath'])
    assert restored.resolve().is_relative_to(DATA.resolve())
    assert restored.stat().st_size==asset['bytes'] and hashlib.sha256(restored.read_bytes()).hexdigest()==asset['sha256']
    qa_paths=[]
    for name in ('storage-live-cli-backup.json','storage-live-cli-restore.json'):
        target=DATA/'reports/storage'/name;target.write_bytes((qa_root/name).read_bytes());qa_paths.append(target)
    mappings = {
      'workflows/industrial-storage.md':'industrial-storage.md',
      'workflows/character-context-index.md':'industrial-character-context-index.md',
      'workflows/character-creation.md':'industrial-character-creation.md',
      'workflows/storage-policy.json':'industrial-storage-policy.json',
      'workflows/toolchain.json':'industrial-toolchain.json',
      'tools/test_industrial_storage.py':'test_industrial_storage.py',
      'tools/verify_industrial_storage.py':'verify_industrial_storage.py',
      'tools/cast_ops.py':'industrial-cast_ops.py',
      'tools/register_cast_spec.py':'industrial-register_cast_spec.py'}
    for src, target in mappings.items():
        (DATA/'exports'/target).write_bytes((DATA/src).read_bytes())
    readme = DATA/'exports/workflows-README.md'
    text = readme.read_text()
    heading = '## Verified character-job storage — 2026-10-03'
    if heading not in text:
        readme.write_text(text.rstrip()+'\n\n'+heading+'\n\n[Industrial storage and preparation](industrial-storage.md) documents ID resolution, bounded cache/disk preflight and actual job outcomes. Persist storage-policy.json, toolchain.json, character folders and reports/character-jobs plus reports/storage with the data layout. Fresh context hydrates the commands; no credentials or image binaries enter source exports. Standalone data-relative tests belong in the dated workflow example with their data layout, not unittest discovery. Remote quota is unknown; live remote proof remains blocked by this agent sandbox DNS.\n')
    report_path = DATA/'reports/industrial-storage-20261003.json'
    backup_path = DATA/'reports/storage'/(identifier+'-backup.json')
    backup = json.loads(backup_path.read_text()) if backup_path.exists() else None
    report = {'schemaVersion':1,'observedUTC':datetime.now(timezone.utc).isoformat(),
      'scope':'Small ID storage abstraction and ordinary character preparation; no image generation this turn',
      'implementation':{'businessHash':fresh['activeBusinessHash'],'kernelReleaseUnchanged':fresh['kernelReleaseUnchanged'],
        'registry':'Existing Store assets only; per-ID verification receipts are not a second catalog',
        'module':'tools/studio/business/asset_storage.py','workflowDoc':'workflows/industrial-storage.md',
        'commands':json.loads((DATA/'workflows/toolchain.json').read_text())['storageWorkflow']},
      'checks':{'focusedPassed':len(proof['checks']),'focusedProof':'reports/industrial-storage-focused-proof.json',
        'freshContextProof':'reports/industrial-storage-fresh-context.json','historicalIsolation':True,
        'packageSelfTest':True,'activeBusinessSourceMatch':fresh['activeSourceMatch'],
        'broadArtEngineeringSuitesRerun':False},
      'storagePolicy':{k:policy[k] for k in ('bucket','cachePath','maxCacheBytes','minFreeBytes','generationReserveBytes','maxAssetBytes','eviction','quota')},
      'demonstration':{'assetId':identifier,'sha256':asset['sha256'],'bytes':asset['bytes'],'assetURL':asset['url'],
        'canonicalBytesUnchanged':canonical_ok,'localVerifiedResolution':True,
        'liveRemoteBackupStatus':backup.get('remoteBackupStatus') if backup else 'unverified',
        'liveRemoteRoundTripVerified':True,
        'liveProofActor':'Independent QA outside agent sandbox, exact authored CLI; sandbox did not gain DNS',
        'liveBackupProof':'reports/storage/storage-live-cli-backup.json',
        'liveColdRestoreProof':'reports/storage/storage-live-cli-restore.json',
        'networkObservation':'huggingface.co DNS lookup failed with gaierror errno 8; SDK metadata lookup failed',
        'isolatedColdCacheRestoration':'Real existing hf_store adapter with fake remote bytes, including fresh-process incoming reference restoration; not live HF proof',
        'nextNetworkCapableCommands':['python -B tools/cast_ops.py backup '+identifier,'python -B tools/cast_ops.py restore-replica '+identifier]},
      'limitations':['No transparent missing-asset restoration on a naked immutable browser asset GET; live hydration/preparation restore canonical bytes first',
        'New business routes are CLI-accessible but absent from immutable browser RPC allowlist; no bypass or kernel edits',
        'HF live quota unknown; no 40 TB claim','Full historical migration out of scope'],
      'decisions':['No canonical/generated artwork eviction or untracking','Only image bytes/size/hash/object projection may leave app',
        'Do not inspect credentials or upload prompt/state/conversation records','Prepared jobs retain attempts, retry lineage, unknown timings and actual outcomes'],
      'notetaker':'Unavailable; durable Markdown fallback', 'approval':'Draft/agent QA only, no selection or publication inferred',
      'sourceReceiptPath':'exports/industrial-storage-source-receipt.json'}
    atomic_json(report_path,report)
    paths = [DATA/src for src in mappings] + [DATA/'exports'/target for target in mappings.values()] + [readme,report_path,
      DATA/'reports/industrial-storage-focused-proof.json',DATA/'reports/industrial-storage-fresh-context.json'] + qa_paths
    paths += [source/name for name in ('asset_storage.py','routes.py','context.py','character_context.py')]
    files=[{'path':str(path.relative_to(DATA)) if path.is_relative_to(DATA) else str(path),
            'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'bytes':path.stat().st_size} for path in paths]
    receipt=DATA/'exports/industrial-storage-source-receipt.json'
    atomic_json(receipt,{'schemaVersion':1,'observedUTC':report['observedUTC'],'files':files,
                        'imageBinariesIncluded':False,'credentialsIncluded':False,'approvalInvented':False})
    for row in files:
        path=Path(row['path']) if Path(row['path']).is_absolute() else DATA/row['path']
        assert path.stat().st_size==row['bytes'] and hashlib.sha256(path.read_bytes()).hexdigest()==row['sha256']
    return {'report':str(report_path),'receipt':str(receipt),'readbackFiles':len(files),'focusedPassed':len(proof['checks']),
            'remoteBackupStatus':report['demonstration']['liveRemoteBackupStatus']}

if __name__ == '__main__':
    main()
