"""Versioned planning, bounded field patches and explicit production dispatch binding."""
import copy
import hashlib
import json
import time
from model import StudioError, valid_id, now

FIELDS = {'action', 'cause', 'effect', 'caption', 'camera', 'beat', 'seconds',
          'castIds', 'dependsOn', 'previewKind', 'imageAssetId'}
MAX_PANELS = 512
PAGE_SIZE = 12

def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()

def current(chapter):
    draft = chapter.get('studioDraft', {})
    return next((v for v in draft.get('versions', []) if v['version'] == draft.get('currentVersion')), None)

def chapter_for(state, identifier):
    identifier = valid_id(identifier)
    return next((c for c in state['project']['chapters'] if c['id'] == identifier), None)

def local_verified(store, state, asset):
    try:
        path = store.asset_path(asset['id'], state)
        size = path.stat().st_size
        if size > 40 * 1024 * 1024 or size != asset.get('bytes', size):
            return False
        h = hashlib.sha256()
        with path.open('rb') as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b''):
                h.update(block)
        return h.hexdigest() == asset.get('sha256')
    except (StudioError, OSError, KeyError, TypeError):
        return False

def entity_reference_role(kind):
    roles = {'character': 'character-identity', 'location': 'location-identity',
             'prop': 'prop-geometry', 'style': 'book-style', 'panorama': 'seamless-panorama'}
    if kind not in roles:
        raise StudioError('Unknown reference entity kind')
    return roles[kind]

def reference_requests(project, scenes, reference_ids=(), requested_bindings=(), entity_id=None):
    """Deterministic inputs shared by plan review and actual job resolution."""
    entities = {e['id']: e for e in project['entities']}
    used = {entity_id} if entity_id else set()
    for scene in scenes:
        used.update(scene.get('castIds', []))
        used.update(scene.get('propIds', []))
        if scene.get('locationId'):
            used.add(scene['locationId'])
    result = []
    for identifier in sorted(used):
        entity = entities.get(identifier)
        if not entity:
            raise StudioError('Unknown reference entity')
        for asset_id in entity.get('referenceIds', []):
            result.append((asset_id, entity_reference_role(entity['kind']), identifier))
    for asset_id in project.get('book', {}).get('styleReferenceIds', []):
        result.append((asset_id, 'book-style', None))
    for scene in scenes:
        if scene.get('imageAssetId'):
            result.append((scene['imageAssetId'], 'current-scene', None))
    result.extend((asset_id, 'reference', None) for asset_id in reference_ids)
    result.extend((b.get('assetId'), b.get('role'), b.get('entityId')) for b in requested_bindings)
    return result

def references(store, state, spec):
    assets = {a['id']: a for a in state['assets']}
    ids = spec.get('referenceIds', [])
    if not isinstance(ids, list) or len(ids) > 32 or len(set(ids)) != len(ids):
        raise StudioError('References must be a bounded unique list')
    scenes = [dict(p, locationId=spec.get('location', {}).get('baseEntityId'))
              for p in spec.get('panels', [])]
    requests = reference_requests(state['project'], scenes, ids)
    permitted = {}
    permitted_entities = {}
    for identifier, role, entity_id in requests:
        if not isinstance(role, str) or not role.strip():
            raise StudioError('Every reference needs a role')
        permitted.setdefault(identifier, set()).add(role)
        if entity_id:
            permitted_entities.setdefault(identifier, set()).add(entity_id)
    if len(permitted) > 256:
        raise StudioError('Effective reference set exceeds bound')
    result = []
    for identifier in sorted(permitted):
        a = assets.get(identifier)
        if not a or not isinstance(a.get('sha256'), str) or len(a['sha256']) != 64:
            raise StudioError('Unknown or unbound reference: ' + str(identifier))
        roles = []
        for e in state['project']['entities']:
            if identifier in e.get('referenceIds', []):
                roles.append(e.get('kind', 'entity') + ':' + e['id'])
        provenance = a.get('provenance', {})
        if isinstance(provenance, dict) and isinstance(provenance.get('role'), str):
            roles.append(provenance['role'][:512])
            # A catalog role is permitted only when that asset is an explicit plan input.
            if identifier in ids and provenance['role'].strip():
                permitted[identifier].add(provenance['role'])
        roles = roles or ['registered-reference:role-unspecified']
        result.append({'assetId': identifier, 'sha256': a['sha256'], 'bytes': a.get('bytes'),
                       'roles': sorted(set(roles)), 'permittedRoles': sorted(permitted[identifier]),
                       'permittedEntityIds': sorted(permitted_entities.get(identifier, set())),
                       'availability': 'verified-local' if local_verified(store, state, a) else 'unresolved-local'})
    return result

def binding_hash(bindings):
    # Availability is cache state; effective identities and permitted roles are semantic.
    return fingerprint([{**{k: b[k] for k in ('assetId', 'sha256', 'bytes', 'roles')},
                         'permittedRoles': b.get('permittedRoles', []),
                         'permittedEntityIds': b.get('permittedEntityIds', [])} for b in bindings])

def resolved_input_preflight(state, approved, resolved):
    """Actual inputs may be a subset, never an added identity/role under old go."""
    permitted = {b['assetId']: b for b in approved['referenceBindings']}
    assets = {a['id']: a for a in state['assets']}
    for actual in resolved:
        reviewed = permitted.get(actual['assetId'])
        asset = assets.get(actual['assetId'], {})
        if (not reviewed or actual.get('sha256') != reviewed['sha256'] or
            asset.get('bytes') != reviewed['bytes'] or
            not set(actual.get('roles', [])) <= set(reviewed.get('permittedRoles', [])) or
            not set(actual.get('entityIds', [])) <= set(reviewed.get('permittedEntityIds', []))):
            raise StudioError('Resolved generation inputs exceed reviewed identities/roles; revise and review the draft')

def validate(state, spec):
    if not isinstance(spec, dict):
        raise StudioError('Draft spec must be an object')
    for key in ('title', 'synopsis'):
        if not isinstance(spec.get(key), str) or not (1 if key == 'title' else 0) <= len(spec[key]) <= 4000:
            raise StudioError('Missing/bounded ' + key)
    if len(json.dumps(spec).encode()) > 1024 * 1024:
        raise StudioError('Draft exceeds 1 MiB bound')
    entities = {e['id']: e for e in state['project']['entities']}
    loc = spec.get('location')
    if not isinstance(loc, dict) or entities.get(loc.get('baseEntityId'), {}).get('kind') != 'location':
        raise StudioError('Location base must be a registered location entity')
    if not isinstance(loc.get('description'), str) or not 0 < len(loc['description']) <= 4000 or type(loc.get('proposed')) != bool:
        raise StudioError('Location requires description and proposed boolean')
    panels = spec.get('panels')
    if not isinstance(panels, list) or not 1 <= len(panels) <= MAX_PANELS:
        raise StudioError('Draft needs 1–512 panels')
    ids = []
    assets = {a['id']: a for a in state['assets']}
    for p in panels:
        if not isinstance(p, dict):
            raise StudioError('Panel must be an object')
        pid = valid_id(p.get('id'))
        dependencies = p.get('dependsOn', [])
        if not isinstance(dependencies, list) or pid in ids or any(d not in ids for d in dependencies):
            raise StudioError('Invalid causal order')
        ids.append(pid)
        for key in ('action', 'cause', 'effect', 'caption', 'camera'):
            if not isinstance(p.get(key), str) or not 0 < len(p[key]) <= 1500:
                raise StudioError('Missing/bounded panel ' + key)
        if p.get('beat') not in ('setup', 'repeat', 'turn', 'payoff') or type(p.get('seconds')) != int or not 1 <= p['seconds'] <= 120:
            raise StudioError('Invalid reading tempo seconds')
        cast = p.get('castIds')
        if not isinstance(cast, list) or not cast or len(cast) > 16 or any(entities.get(c, {}).get('kind') != 'character' for c in cast):
            raise StudioError('Cast must contain registered character entities')
        kind = p.get('previewKind')
        image = p.get('imageAssetId')
        if 'status' in p or 'approved' in p:
            raise StudioError('Planning cannot assert artifact approval/status')
        if kind == 'schematic-placeholder':
            if image is not None:
                raise StudioError('Placeholder cannot claim image art')
        elif kind in ('reused-reference', 'generated'):
            if image not in assets:
                raise StudioError('Visual preview requires a registered image asset')
            if kind == 'generated':
                provenance = assets[image].get('provenance', {})
                if not isinstance(provenance, dict) or not provenance.get('prompt'):
                    raise StudioError('Generated preview requires recorded generation provenance')
        else:
            raise StudioError('Invalid preview kind')

def save_draft(store, body):
    started = time.monotonic()
    if not isinstance(body, dict) or type(body.get('expectedRevision')) != int:
        raise StudioError('expectedRevision is required')
    state = store.read()
    project = state['project']
    identifier = valid_id(body.get('chapterId'))
    chapter = chapter_for(state, identifier)
    history = chapter.get('studioDraft', {}).get('versions', []) if chapter else []
    latest = current(chapter) if chapter else None
    if body.get('baseVersion', 0) != (latest['version'] if latest else 0):
        raise StudioError('Draft version changed; hydrate before revising')
    if latest and body.get('baseSHA256') is not None and body['baseSHA256'] != latest['sha256']:
        raise StudioError('Draft hash changed; hydrate before revising')
    if len(history) >= 100:
        raise StudioError('Draft history bound reached')
    spec = copy.deepcopy(body.get('spec'))
    try:
        if isinstance(spec, dict):
            spec.setdefault('synopsis', '')
        validate(state, spec)
        bindings = references(store, state, spec)
    except (TypeError, KeyError, ValueError) as exc:
        raise StudioError('Malformed draft fields: ' + str(exc)) from None
    if not chapter:
        chapter = {'id': identifier, 'title': {'en': spec['title']}, 'scenes': []}
        project['chapters'].append(chapter)
    request = body.get('request', '')
    if not isinstance(request, str) or len(request) > 16000:
        raise StudioError('Bounded request text required')
    version = {'version': len(history) + 1, 'createdAt': now(), 'reason': str(body.get('reason', 'Draft revision'))[:500],
               'spec': spec, 'sha256': fingerprint({'spec': spec, 'referenceHash': binding_hash(bindings)}),
               'referenceBindings': bindings, 'referenceHash': binding_hash(bindings),
               'inputPrompt': request, 'requestSHA256': fingerprint(request),
               'referenceIds': spec.get('referenceIds', []), 'changedFields': copy.deepcopy(body.get('_changedFields', [])),
               'timing': {'businessPreparationSeconds': time.monotonic() - started,
                          'requestAcceptanceToCompletionSeconds': None},
               'generation': {'calls': 0, 'additionalAPICostUSD': 0, 'fullProductionStarted': False}}
    chapter['studioDraft'] = {'schemaVersion': 2, 'versions': history + [version],
                             'currentVersion': version['version'], 'production': 'awaiting-specific-user-go',
                             'authorizationReceipts': copy.deepcopy(chapter.get('studioDraft', {}).get('authorizationReceipts', []))}
    chapter['synopsis'] = spec['synopsis']
    chapter['script'] = '\n\n'.join(f"{i+1}. {p['action']}\n{p['caption']}" for i, p in enumerate(spec['panels']))
    chapter['scenes'] = [{'id': p['id'], 'title': p['caption'], 'action': p['action'], 'captions': {'en': p['caption']},
                          'castIds': p['castIds'], 'locationId': spec['location']['baseEntityId'],
                          'dependsOn': p.get('dependsOn', []), 'camera': {'description': p['camera']},
                          'tempo': {'weight': 2}, 'stateBefore': p['cause'], 'stateAfter': p['effect']}
                         for p in spec['panels']]
    chapter.pop('studioPlanApproval', None)
    saved = store.save_project(project, body['expectedRevision'])
    return {'chapterId': identifier, 'version': version['version'], 'sha256': version['sha256'],
            'referenceHash': version['referenceHash'], 'revision': saved['revision'],
            'changedFields': version['changedFields'], 'timing': version['timing'],
            'appLink': '/?chapter=' + identifier + '&view=plan', 'productionStarted': False}

def patch_draft(store, body):
    if not isinstance(body, dict) or len(json.dumps(body).encode()) > 32000:
        raise StudioError('Patch must be an object of at most 32 KiB')
    state = store.read()
    chapter = chapter_for(state, body.get('chapterId'))
    v = current(chapter) if chapter else None
    if not v or body.get('baseVersion') != v['version'] or body.get('baseSHA256') != v['sha256']:
        raise StudioError('Patch requires hydrated current version and hash')
    patches = body.get('patches')
    if not isinstance(patches, list) or not 1 <= len(patches) <= 12:
        raise StudioError('Patch needs 1–12 selected panels')
    spec = copy.deepcopy(v['spec'])
    panels = {p['id']: p for p in spec['panels']}
    changes = []
    seen = set()
    for patch in patches:
        if not isinstance(patch, dict) or not isinstance(patch.get('panelId'), str) or patch['panelId'] not in panels or patch['panelId'] in seen:
            raise StudioError('Patch requires unique existing panel IDs')
        fields = patch.get('fields')
        if not isinstance(fields, dict) or not fields or not set(fields) <= FIELDS:
            raise StudioError('Unsupported or empty panel fields')
        seen.add(patch['panelId'])
        panel = panels[patch['panelId']]
        for key, value in fields.items():
            if panel.get(key) != value:
                changes.append({'panelId': patch['panelId'], 'field': key,
                                'before': copy.deepcopy(panel.get(key)), 'after': copy.deepcopy(value)})
                panel[key] = copy.deepcopy(value)
    return save_draft(store, {**body, 'spec': spec, '_changedFields': changes})

def draft_context(chapter, scene_ids=(), page=0, store=None, state=None):
    v = current(chapter)
    if not v:
        return None
    ref_hash = v.get('referenceHash')
    bindings = v.get('referenceBindings', [])
    if store is not None and state is not None:
        spec = copy.deepcopy(v['spec'])
        bindings = references(store, state, spec)
        ref_hash = binding_hash(bindings)
    a = chapter['studioDraft'].get('productionAuthorization', {})
    authorized = bool(a and a.get('version') == v['version'] and a.get('sha256') == v['sha256'] and a.get('referenceHash') == ref_hash and ref_hash)
    panels = v['spec']['panels']
    selected = [p for p in panels if p['id'] in scene_ids][:12] if scene_ids else panels[page * PAGE_SIZE:(page + 1) * PAGE_SIZE]
    selected = [{k: (value[:400] if isinstance(value, str) else value) for k, value in p.items()} for p in selected]
    return {'chapterId': chapter['id'], 'currentVersion': v['version'], 'sha256': v['sha256'],
            'referenceHash': ref_hash, 'referenceBindings': bindings,
            'productionAuthorized': authorized, 'authorizeRoute': '/api/chapter-drafts/authorize-production',
            'panelCount': len(panels), 'pageSize': PAGE_SIZE, 'page': page, 'panels': selected,
            'location': v['spec']['location'], 'production': chapter['studioDraft']['production'],
            'history': [{k: x.get(k) for k in ('version', 'reason', 'sha256')} for x in chapter['studioDraft']['versions'][-10:]],
            'patchRoute': '/api/chapter-drafts/patch'}

def production_binding(store, state, chapter):
    v = current(chapter)
    if not v:
        raise StudioError('Chapter has no managed draft')
    spec = copy.deepcopy(v['spec'])
    bindings = references(store, state, spec)
    ref_hash = binding_hash(bindings)
    if v.get('referenceHash') and v['referenceHash'] != ref_hash:
        raise StudioError('Registered references changed; revise and review the draft before full production')
    return v, bindings, ref_hash

def authorize_production(store, body):
    started = time.monotonic()
    if not isinstance(body, dict) or type(body.get('expectedRevision')) != int:
        raise StudioError('Production authorization requires expectedRevision')
    if any(body.get(k) is not None for k in ('revision', 'projectRevision')) or any(body.get(k) for k in ('readOnly', 'reviewSnapshot')):
        raise StudioError('Historical views cannot authorize production; switch to Live and review current bindings')
    state = store.read()
    if state.get('readOnly'):
        raise StudioError('Historical views cannot authorize production')
    chapter = chapter_for(state, body.get('chapterId'))
    if not chapter:
        raise StudioError('Chapter has no managed draft')
    v, bindings, ref_hash = production_binding(store, state, chapter)
    if type(body.get('version')) != int or body['version'] != v['version'] or body.get('sha256') != v['sha256'] or body.get('referenceHash') != ref_hash:
        raise StudioError('Full production requires reviewed current version/spec/reference binding')
    instruction = body.get('userInstruction')
    if body.get('explicitFullProductionGo') is not True or not isinstance(instruction, str) or not 0 < len(instruction.strip()) <= 4000:
        raise StudioError('Specific explicit user full-production instruction required')
    receipts = chapter['studioDraft'].get('authorizationReceipts', [])
    if len(receipts) >= 100:
        raise StudioError('Authorization receipt bound reached')
    receipt = {'chapterId': chapter['id'], 'version': v['version'], 'sha256': v['sha256'],
               'referenceHash': ref_hash, 'referenceBindings': bindings, 'specSnapshotSHA256': fingerprint(v['spec']),
               'userInstruction': instruction, 'requestSHA256': fingerprint(instruction),
               'recordedAt': now(), 'acceptedRevision': state['revision'],
               'productionScope': 'full-production', 'productionStarted': False}
    receipt['receiptSHA256'] = fingerprint(receipt)
    chapter['studioDraft']['productionAuthorization'] = copy.deepcopy(receipt)
    chapter['studioDraft']['authorizationReceipts'] = receipts + [copy.deepcopy(receipt)]
    saved = store.save_project(state['project'], body['expectedRevision'])
    return {'chapterId': chapter['id'], 'version': v['version'], 'sha256': v['sha256'],
            'referenceHash': ref_hash, 'receipt': receipt, 'revision': saved['revision'],
            'productionStarted': False, 'appLink': '/?chapter=' + chapter['id'] + '&view=plan',
            'timing': {'businessAuthorizationSeconds': time.monotonic() - started,
                       'requestAcceptanceToCompletionSeconds': None}}

def dispatch_preflight(store, state, chapter, request):
    v = current(chapter)
    if not v or request['kind'] == 'story-plan':
        return
    spec = copy.deepcopy(v['spec'])
    bindings = references(store, state, spec)
    scope = request.get('productionScope', 'full-production')
    if scope not in ('rough-preproduction', 'full-production'):
        raise StudioError('Unknown managed chapter production scope')
    if scope == 'full-production':
        a = chapter['studioDraft'].get('productionAuthorization', {})
        if not a or a.get('specSnapshotSHA256') != fingerprint(v['spec']) or any(a.get(k) != v.get(k) for k in ('version', 'sha256')) or a.get('referenceHash') != binding_hash(bindings) or (v.get('referenceHash') and a.get('referenceHash') != v['referenceHash']):
            raise StudioError('Explicit full-production authorization for current spec/references required')
    selected = set(request.get('sceneIds') or [p['id'] for p in v['spec']['panels']])
    for panel in v['spec']['panels']:
        if panel['id'] not in selected:
            continue
        scene = next((s for s in chapter['scenes'] if s['id'] == panel['id']), {})
        if scene.get('action') != panel['action'] or scene.get('castIds') != panel['castIds'] or scene.get('locationId') != v['spec']['location']['baseEntityId'] or scene.get('camera', {}).get('description') != panel['camera'] or scene.get('captions', {}).get('en') != panel['caption']:
            raise StudioError('Managed scene differs from current draft; revise the draft before generation')
    if scope == 'rough-preproduction' and any(b['availability'] != 'verified-local' for b in bindings):
        raise StudioError('Generation preflight: restore and verify unresolved registered references before dispatch')

    if scope == 'full-production':
        return {'version': a['version'], 'sha256': a['sha256'], 'referenceHash': a['referenceHash'],
                'referenceBindings': copy.deepcopy(a['referenceBindings'])}
    return None
