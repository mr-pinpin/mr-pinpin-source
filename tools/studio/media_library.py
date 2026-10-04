"""Registered panorama images and a fixed, hash-pinned archive allowlist."""
import hashlib
import json,os,re
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


MAX_REGISTRY_BYTES=128*1024
MAX_MEDIA_BYTES=256*1024*1024
MIMES={'.png':'image/png','.jpg':'image/jpeg','.jpeg':'image/jpeg','.webp':'image/webp','.mp4':'video/mp4','.webm':'video/webm'}

def media_entries():
    """Trusted host config only, read lazily; no request may select a root/registry."""
    configured=os.environ.get('PINPIN_MEDIA_CACHE_ROOT')
    root=Path(configured).expanduser().resolve() if configured else ARCHIVE.resolve()
    entries={key:{'path':v[0],'mime':v[1],'sha256':v[2],'legacy':True} for key,v in FILES.items()}
    if configured:
        registry=root/'media-registry.json'
        if registry.is_symlink() or not registry.is_file() or registry.stat().st_size>MAX_REGISTRY_BYTES:
            raise StudioError('Configured media registry unavailable or oversized','media_registry',503)
        raw=registry.read_bytes()
        if len(raw)>MAX_REGISTRY_BYTES:raise StudioError('Media registry grew beyond bound','media_registry',503)
        try:value=json.loads(raw,parse_constant=lambda v:(_ for _ in ()).throw(ValueError(v)))
        except (ValueError,RecursionError):raise StudioError('Invalid media registry','media_registry',503)
        if not isinstance(value,dict) or set(value)!={'schemaVersion','files'} or value['schemaVersion']!=1 or not isinstance(value['files'],dict) or len(value['files'])>128:
            raise StudioError('Invalid media registry bounds','media_registry',503)
        for identifier,row in value['files'].items():
            if not isinstance(identifier,str) or not re.fullmatch('[A-Za-z0-9_.-]{1,160}',identifier) or not isinstance(row,dict) or set(row)-{'path','mime','sha256','bytes','name','reviewStatus','projection','provenance'}:
                raise StudioError('Invalid media entry','media_registry',503)
            relative=row.get('path');mime=row.get('mime');sha=row.get('sha256');size=row.get('bytes')
            if not isinstance(relative,str) or len(relative)>512 or '\\' in relative or Path(relative).is_absolute() or any(part in ('','..','.') for part in relative.split('/')) or ':' in relative:
                raise StudioError('Unsafe media path','media_registry',503)
            if MIMES.get(Path(relative).suffix.lower())!=mime or not isinstance(sha,str) or not re.fullmatch('[a-f0-9]{64}',sha) or type(size)!=int or not 0<size<=MAX_MEDIA_BYTES:
                raise StudioError('Invalid media identity or type','media_registry',503)
            if identifier in FILES and FILES[identifier][2]!=sha:raise StudioError('Legacy media identity cannot change','media_registry',503)
            entries[identifier]=dict(row)
    return root,entries

def media_file(identifier):
    root,entries=media_entries()
    if identifier not in entries:raise StudioError('Media entry not found','not_found',404)
    row=entries[identifier];relative=row['path'];mime=row['mime'];expected=row['sha256']
    path=root
    for part in Path(relative).parts:
        path=path/part
        if path.is_symlink():raise StudioError('Media symlinks are forbidden','media_registry',503)
    path=path.resolve()
    if not path.is_relative_to(root) or not path.is_file():raise StudioError('Registered media unavailable','not_found',404)
    stat=path.stat()
    if stat.st_size>MAX_MEDIA_BYTES or 'bytes' in row and stat.st_size!=row['bytes']:raise StudioError('Media size mismatch','storage_corruption',500)
    signature=(str(path),stat.st_size,stat.st_mtime_ns,stat.st_ctime_ns,expected,mime)
    if _verified.get(identifier)!=signature:
        with path.open('rb') as stream:
            head=stream.read(16);stream.seek(0);hasher=hashlib.sha256();total=0
            for block in iter(lambda:stream.read(1024*1024),b''):
                total+=len(block)
                if total>MAX_MEDIA_BYTES:raise StudioError('Media exceeds bound','storage_corruption',500)
                hasher.update(block)
        actual=hasher.hexdigest()
        signatures={'image/png':head.startswith(b'\x89PNG\r\n\x1a\n'),'image/jpeg':head.startswith(b'\xff\xd8\xff'),'image/webp':head[:4]==b'RIFF' and head[8:12]==b'WEBP','video/mp4':head[4:8]==b'ftyp','video/webm':head.startswith(b'\x1aE\xdf\xa3')}
        after=path.stat()
        if actual!=expected or not signatures.get(mime) or (after.st_size,after.st_mtime_ns,after.st_ctime_ns)!=(stat.st_size,stat.st_mtime_ns,stat.st_ctime_ns):raise StudioError('Media identity/type changed','storage_corruption',500)
        _verified[identifier]=signature
    return path,mime,expected


def import_media(store, identifier):
    from business.media_library import import_media as operation
    return operation(store, identifier)

def media_library(store):
    from business.media_library import media_library as operation
    return operation(store)
