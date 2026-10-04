"""Resolve exact inventory with explicit evidence; approval never follows a hash."""
import fnmatch
import re
import time
from pathlib import Path
from paths import LocationError, media_path, relative

MEDIA = {'.png','.webp','.jpeg','.jpg','.mp4','.webm','.glb','.blend'}
SHA = re.compile(r'^[a-f0-9]{64}$')


def resolve_entry(index, request):
    if not isinstance(request, str) or len(request) > 160:
        raise LocationError('Query must be a compact location ID or alias')
    request = request.strip().lower()
    if '..' in request or '\\' in request:
        raise LocationError('Unsafe query')
    matches = [e for e in index['config']['entries'] if request in [e['id'], *e.get('aliases',[])]]
    if len(matches) != 1:
        raise LocationError('Unknown or ambiguous location; use list to choose an exact ID')
    return dict(matches[0])


def reference_path(value, source, assets):
    """Map historical absolute paths by content identity, never read arbitrary hosts."""
    path = value.get('src') or value.get('asset') or value.get('sourcePath') or value.get('sourceRepoPath') or value.get('path') or value.get('file')
    if not isinstance(path, str):
        return None
    if '/docs/' in path and Path(path).is_absolute():
        path = 'docs/' + path.split('/docs/',1)[1]
    if path.startswith('storyboard/'):
        path = 'docs/' + path
    if path.startswith('docs/'):
        return str(relative(path))
    if not Path(path).is_absolute():
        try:
            # Provenance paths may use ../ relative to their record; normalize then bound.
            p = Path(source).parent / path
            import posixpath
            candidate = posixpath.normpath(str(p))
            relative(candidate)
            if candidate in assets:
                return candidate
        except LocationError:
            pass
    sha = value.get('sha256')
    candidates = [n for n,a in assets.items() if a['sha256']==sha]
    if candidates:
        basename = Path(path).name
        named = [n for n in candidates if Path(n).name == basename]
        return sorted(named or candidates)[0]
    return None


def extract_media(value, source, index, output, context='source'):
    if isinstance(value, list):
        for v in value:
            extract_media(v, source, index, output, context)
    elif isinstance(value, dict):
        p = reference_path(value, source, index['assets'])
        if p and Path(p).suffix.lower() in MEDIA:
            row = output.setdefault(p, {'path': p, 'roles': [], 'provenance': []})
            role = value.get('role') or context
            roles = value.get('roles') or [role]
            row['roles'] = sorted(set(row['roles'] + roles))
            row['provenance'].append(source)
            for k in ('sha256','bytes'):
                if k in value:
                    if k in row and row[k] != value[k]:
                        row['identityConflict'] = True
                    row[k] = value[k]
            row['notes'] = value.get('notes', row.get('notes',''))
        for k,v in value.items():
            if isinstance(v,str) and k in ('asset','cube','assembled','front','rear','up','down','detail','base') and Path(v).suffix.lower() in MEDIA:
                extract_media({'path':v,'role':'selected-'+k}, source, index, output, k)
            if k in ('prompt','command','originalOutput','originalToolOutput','outputPath'):
                continue
            extract_media(v, source, index, output, k)


def query(index, root, request, scope='approved', stop=None, viewpoint=None, probe_media=False):
    began = time.perf_counter()
    entry = resolve_entry(index, request)
    viewpoint = viewpoint or entry.get('aliasViewpoints',{}).get(request.strip().lower())
    docs = index['documents']
    patterns = list(entry['documents'])
    if stop is not None:
        if entry['id'] != 'tractor/orbit' or not re.fullmatch(r'stop-(?:0[0-9]|1[0-9]|2[0-3])', stop):
            raise LocationError('Stop must be stop-00..stop-23 for tractor/orbit')
        patterns += ['docs/storyboard/production/tractor-stops-20260924/stops/'+stop+'/*.json',
                     'docs/storyboard/production/tractor-stops-20260924/stops/'+stop+'/*.txt',
                     'docs/storyboard/production/tractor-stops-20260924/stops/'+stop+'/*.md']
    selected = sorted(n for n in docs if any(Path(n).match(p) for p in patterns))
    media = {}
    cameras = []
    records = []
    stop_record = None
    selected_paths = set()
    for name in selected:
        raw = docs[name].get('value')
        record={'path':name,'sha256':docs[name]['sha256']}
        if isinstance(raw,dict):
            for key in ('status','selectionStatus','cameraIntent'):
                if key in raw:record[key]=raw[key]
        records.append(record)
        if raw is None:
            continue
        value = raw
        if name.endswith('/references.json'):
            value = {'references': [r for r in raw['references'] if r['id'] in entry.get('referenceIds',[])]}
        selected_runtime = False
        if name == 'docs/house-image-tour-config.js':
            selected_runtime = True
            value = raw.get(entry.get('room'),{})
            entry['initialView'] = value.get('initialView')
            entry['connections'] = [{'from':entry['room'], **d} for d in value.get('doors',[])]
        if name == 'docs/house-variants.config.js':
            selected_runtime = True
            config = raw.get(entry.get('room'),{})
            value = config.get('after',{})
            entry['initialView'] = config.get('initialView')
        if name == 'docs/story-worlds.config.js':
            selected_runtime = True
            value = raw.get(entry.get('room'),{})
            entry['initialView'] = value.get('initialView')
        if name.endswith('/input-config.json'):
            value = raw.get('rooms',{}).get(entry.get('room'),{})
        if name.endswith('/cameras.json'):
            cameras = [c for c in raw['presets'] if not entry.get('room') or c['room']==entry.get('room')]
            if viewpoint:
                cameras = [c for c in cameras if c['id']==viewpoint]
                if not cameras:
                    raise LocationError('Unknown camera preset for this room')
            entry['cubemapPosition'] = raw['cubemapPositions'].get(entry.get('room')) if entry.get('room') else raw['cubemapPositions']
            entry['cameraValidation'] = raw['validation']
        if entry['id']=='tractor/orbit' and isinstance(raw,dict) and isinstance(raw.get('stops'),list):
            value = dict(raw, stops=[s for s in raw['stops'] if s.get('id')==stop]) if stop else {k:v for k,v in raw.items() if k!='stops'}
        if entry['id']=='tractor/orbit' and name.endswith('/source-display-manifest.json'):
            value = {'frames':[f for f in raw.get('frames',[]) if f.get('id')==stop]}
        if entry['id']=='tractor/orbit' and name.endswith('/frames-manifest.json'):
            value = dict(raw, stops=[s for s in raw['stops'] if s['id']==stop]) if stop else {'video': raw['video']}
            entry['stopCount'] = len(raw['stops'])
            entry['stopInventory'] = [{k:s[k] for k in ('id','frameIndex','timestampSeconds','visualSector')} for s in raw['stops']]
        if stop and name.endswith('/selected.json'):
            stop_record = raw
        extract_media(value, name, index, media)
        if selected_runtime or name.endswith('/selected-stack.json'):
            chosen = {}
            extract_media(value,name,index,chosen)
            selected_paths.update(chosen)
            entry['selectedStack'] = {k:value[k] for k in ('asset','repairs','details','inputs') if k in value}
    if viewpoint and not cameras:
        raise LocationError('Viewpoint presets apply to measured house entries only')
    # Selected stop string references have identities in scoped catalogs.
    if stop_record:
        base = 'docs/storyboard/production/tractor-stops-20260924/'
        for k in ('panorama','forward','anchoredPanorama','anchoredCube'):
            p = stop_record.get(k)
            if p:
                relative(base+p)
                media.setdefault(base+p, {'path':base+p,'roles':[k],'provenance':[base+'stops/'+stop+'/selected.json']})
                selected_paths.add(base+p)
        entry['selectedStop'] = {k:stop_record[k] for k in ('id','status','camera','sourceCamera','authoredGuideCamera','sourceLockStatus','sourceAnchor') if k in stop_record}
    if entry.get('projectionReference'):
        ref = entry['projectionReference']
        media[ref['path']] = dict(ref, provenance=[ref['evidence']], contextOnly=True)
    references = []
    excluded = []
    for p,row in sorted(media.items()):
        asset = index['assets'].get(p)
        if asset:
            if row.get('sha256') and row['sha256'] != asset['sha256']:
                row['identityConflict'] = True
            for k in ('sha256','bytes','object','role','bucket','catalog','conflict'):
                if k in asset: row[k] = asset[k]
        row['provenance'] = sorted(set(row['provenance']))
        approved_book = any('Actual approved' in row.get('notes','') for _ in [0])
        # Published book inputs establish reference provenance, not approval of their derivatives.
        published = bool(index.get('bookRegistry',{}).get(p))
        if published:
            row['bookRegistryEvidence'] = index['bookRegistry'][p]
        row['approval'] = ('approved-book-reference' if approved_book else 'published-book-reference') if approved_book or published else entry['approval']
        row['approvalEvidence'] = (row['provenance'][0] if approved_book else index['bookRegistry'][p][0]['registry']) if approved_book or published else entry['approvalEvidence']
        row['isReference'] = approved_book or published or row.get('contextOnly',False)
        row['selected'] = p in selected_paths
        if 'geometry-underlay' in row['roles']:
            row['contextOnly'] = True
            row['isReference'] = True
        if row.get('contextOnly'):
            row['approval'] = 'projection-style-reference' if 'projection-style-only' in row['roles'] else 'geometry-underlay'
            row['approvalEvidence'] = row.get('evidence',row['provenance'][0])
        row['usableForChapter'] = approved_book or published
        row['availability'] = 'not-probed'
        if probe_media:
            try:
                local = media_path(root,p)
                row['availability'] = 'local-unverified' if local.is_file() else 'missing'
            except LocationError:
                row['availability'] = 'unsafe-source-link'
        from storage_bridge import annotate
        annotate(root,row,index.get('studioBridge'),probe=probe_media)
        row['studioAllowlisted'] = row['sha256'] in index.get('studioAllowlistBySha256',{}) if row.get('sha256') else False
        if row['studioAllowlisted']:
            row['studioMediaId'] = index['studioAllowlistBySha256'][row['sha256']]
        row['restorable'] = bool(asset and asset.get('object') and not asset.get('conflict') and not row.get('identityConflict'))
        if not (row['isReference'] or row['selected'] or entry['kind']=='measured-geometry' or (entry['id']=='tractor/orbit' and '/tractor-orbit-' in p and stop is None)):
            continue
        if scope=='approved' and not row['usableForChapter'] and not row.get('contextOnly'):
            excluded.append({k:row[k] for k in ('path','sha256','bytes','approval','approvalEvidence','availability','selected') if k in row})
        else:
            references.append(row)
    return {'schemaVersion':1, 'request':{'location':entry['id'],'scope':scope,'stop':stop,'viewpoint':viewpoint},
            'location':entry, 'cameras':cameras, 'media':references,
            'excludedMedia':excluded, 'records':records,
            'recipes':[{'path':p,'sha256':docs.get(p,{}).get('sha256')} for p in entry['recipes']],
            'studioBridge':{k:v for k,v in index.get('studioBridge',{}).items() if k!='assetsBySha256'} if index.get('studioBridge') else None,
            'indexProvenance':{'indexedAt':index['indexedAt'],'sourceRoot':index['root']},
            'warnings':['Default availability is not-probed: query never opens or stats media. Optional probe and hydrate report missing bytes; hydrate verifies SHA-256.',
                        'Approved chapter references, visual-direction approval, reviewed experiments and publication are distinct.'],
            'timing':{'querySeconds':time.perf_counter()-began}}
