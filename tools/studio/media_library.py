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
    from business.media_library import import_media as operation
    return operation(store, identifier)

def media_library(store):
    from business.media_library import media_library as operation
    return operation(store)
