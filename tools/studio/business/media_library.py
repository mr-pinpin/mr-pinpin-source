"""Editable catalog presentation and reviewed-image import workflow."""
import hashlib
from model import StudioError
import media_library as archive

NAMES = {'tractor-orbit-scrub-v1': 'Tractor orbit', 'tractor-panorama-v1': 'Tractor clearing',
         'elder-cube-v1': 'Elder’s house', 'lake-cube-v1': 'Forest lake', 'tractor-cube-v1': 'Tractor clearing'}
CATALOG_NAMES = {'reference-kitchen-panorama': 'Kitchen', 'reference-elder-panorama': 'Elder’s house',
                 'reference-forest-panorama': 'Forest lake'}

def import_media(store, identifier):
    path, mime, sha = archive.media_file(identifier)
    if not mime.startswith('image/'):
        raise StudioError('Only archived images can be attached; review video through extracted frames', 'media_kind')
    state = store.read()
    existing = next((a for a in state['assets'] if a['sha256'] == sha), None)
    if existing:
        return existing, state
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != sha:
        raise StudioError('Archived media changed during import', 'storage_corruption', 500)
    return store.upload_asset(raw, NAMES.get(identifier, identifier),
        provenance={'sourcePath': str(path), 'mediaId': identifier, 'archiveSha256': sha},
        review_status='archive-reviewed')


def media_library(store):
    state = store.read()
    items, notes = [], []
    entities = state.get('project', {}).get('entities', [])
    for asset in state.get('assets', []):
        linked = next((e for e in entities if e.get('kind') == 'panorama'
                       and asset['id'] in e.get('referenceIds', [])), None)
        if not linked and 'panorama' not in asset.get('provenance', {}).get('catalogKey', ''):
            continue
        spherical = asset.get('width', 0) == 2 * asset.get('height', -1)
        items.append(dict(id=asset['id'], assetId=asset['id'], entityId=linked['id'] if linked else None,
                          name=CATALOG_NAMES.get(asset.get('provenance', {}).get('catalogKey'), linked.get('name', asset['name']) if linked else asset['name']),
                          kind='panorama', projection='equirectangular' if spherical else 'unknown',
                          url=asset['url'], reviewStatus=asset.get('reviewStatus', 'unknown'),
                          sha256=asset['sha256'], width=asset.get('width'), height=asset.get('height')))
    for identifier in archive.FILES:
        try:
            _, mime, sha = archive.media_file(identifier)
        except StudioError as exc:
            notes.append(identifier + ': ' + exc.message)
            continue
        video = mime.startswith('video/')
        cube = '-cube-' in identifier
        registered = next((a for a in state['assets'] if a['sha256'] == sha), None)
        items.append(dict(id=identifier, assetId=registered['id'] if registered else None, name=NAMES[identifier], initialYawDegrees=108 if identifier.startswith('tractor-') else 0,
                          initialPitchDegrees=-8 if identifier.startswith('tractor-') else 0,
                          kind='orbit-video' if video else 'cubemap' if cube else 'panorama',
                          projection='camera-path' if video else 'cube-atlas-3x2' if cube else 'equirectangular',
                          url='/api/media/files/' + identifier, sha256=sha,
                          reviewStatus='archive-reviewed', durationSeconds=12.041667 if video else None,
                          note='Recorded orbit · drag to explore' if video else
                          'Explore all six views of the clearing.' if cube else
                          'Look around from this illustrated viewpoint.',
                          reviewNotes='One recorded camera path; uneven speed, detail drift and visible loop join.' if video else
                          'Atlas order: front, right, back / left, up, down. Fixed viewpoint, not measured camera translation.'))
    return dict(schemaVersion=1, revision=state['revision'], items=items, notes=notes)
