"""Registered panorama images and a fixed, hash-pinned archive allowlist."""
import hashlib
from pathlib import Path
from model import StudioError

ARCHIVE = Path('/Volumes/TB4/mac-mini-storage/shared')
FILES = {
    'tractor-orbit-scrub-v1': ('pinpin-tractor-orbit-20260924/orbit-scrub-v1.mp4', 'video/mp4', '5c30e3ee490785285db00041d0b7a90fcc0e1c10e38535ac6aea6521b326a9de'),
    'tractor-panorama-v1': ('pinpin-story-worlds-20260924/tractor/panorama-assembled-v1.png', 'image/png', '84dbfe633a8f3c9282f9dd23406324c983c85ae19a9a488178b2b7976cae35fe'),
    'elder-cube-v1': ('pinpin-story-worlds-20260924/elder/cube-atlas-v1.png', 'image/png', 'd0bb1cf96ed3ffc7a75c11948bd41b43149b9ce230d3bf619673a7c48d9edd92'),
    'lake-cube-v1': ('pinpin-story-worlds-20260924/lake/cube-atlas-v1.png', 'image/png', 'bc4939765c6b62ee10464d766d28f72da9d52cdd5f541f229e45ed9d7ae48107'),
    'tractor-cube-v1': ('pinpin-story-worlds-20260924/tractor/cube-atlas-v1.png', 'image/png', '727ae23d08afe13eaabfb3ed4490ffc1428d6ff997efe892c860c21cf08d7d44'),
}
NAMES = {'tractor-orbit-scrub-v1': 'Tractor orbit', 'tractor-panorama-v1': 'Tractor clearing',
         'elder-cube-v1': 'Elder’s house', 'lake-cube-v1': 'Forest lake', 'tractor-cube-v1': 'Tractor clearing'}
CATALOG_NAMES = {'reference-kitchen-panorama': 'Kitchen', 'reference-elder-panorama': 'Elder’s house',
                 'reference-forest-panorama': 'Forest lake'}
_verified = {}


def media_file(identifier):
    if identifier not in FILES:
        raise StudioError('Media entry not found', 'not_found', 404)
    relative, mime, expected = FILES[identifier]
    path = (ARCHIVE / relative).resolve()
    if not path.is_relative_to(ARCHIVE.resolve()) or not path.is_file():
        raise StudioError('Archived media is unavailable', 'not_found', 404)
    stat = path.stat()
    signature = (str(path), stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns)
    if _verified.get(identifier) != signature:
        with path.open('rb') as stream:
            hasher = hashlib.sha256()
            for block in iter(lambda: stream.read(1024 * 1024), b''):
                hasher.update(block)
            actual = hasher.hexdigest()
        if actual != expected:
            raise StudioError('Archived media checksum mismatch', 'storage_corruption', 500)
        _verified[identifier] = signature
    return path, mime, expected


def import_media(store, identifier):
    path, mime, sha = media_file(identifier)
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
    for identifier in FILES:
        try:
            _, mime, sha = media_file(identifier)
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
