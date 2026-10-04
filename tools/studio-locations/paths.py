"""Bounded, traversal-safe paths for metadata, media and request outputs."""
import hashlib
import json
import os
from pathlib import Path


class LocationError(ValueError):
    pass


def relative(value):
    if not isinstance(value,str) or not value or '\\' in value or '\x00' in value:
        raise LocationError('Invalid relative path')
    p=Path(value)
    if p.is_absolute() or '..' in p.parts or value.startswith('~'):
        raise LocationError('Path must remain repository-relative')
    return p


def metadata_path(root,value):
    p=root/relative(value)
    if not p.resolve().is_relative_to(root.resolve()):raise LocationError('Metadata escapes source')
    return p


def media_path(root,value):
    p=root/relative(value);resolved=p.resolve()
    if not (resolved.is_relative_to(root.resolve()) or resolved.is_relative_to(Path('/Volumes/TB4/mac-mini-storage/shared'))):
        raise LocationError('Media link escapes source/TB4 shared storage')
    return p


def external_path(root,value):
    p=Path(value).expanduser().absolute()
    if p.resolve().is_relative_to(root.resolve()):raise LocationError('Output/cache must be external')
    if any(x.is_symlink() for x in [p,*p.parents]):raise LocationError('Output/cache symlinks refused')
    return p


def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


def atomic_json(path,value):
    path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_name(path.name+'.tmp-'+str(os.getpid()))
    try:
        with tmp.open('x') as stream:json.dump(value,stream,indent=2,ensure_ascii=False);stream.write('\n')
        os.replace(tmp,path)
    finally:tmp.unlink(missing_ok=True)
