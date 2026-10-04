"""Worker-only location adapter; cached discovery, bounded hydration, Studio IDs.

No routes, index rebuild, UI paint work, approval mutation, or generation dispatch.
Application owner calls discover(), then prepare() before authorized generation.
"""
import hashlib
import json
from pathlib import Path
import subprocess
import sys


class LocationAdapterError(ValueError):
    pass


def reference_roles(row):
    """Translate semantic roles; contextOnly describes use, not projection."""
    roles = set(row.get('roles', []))
    geometry = bool(roles & {'geometry-underlay', 'underlay'}) or row.get('approval') == 'geometry-underlay'
    projection = bool(roles & {'projection-style-only', 'seamless-panorama'})
    if geometry and projection:
        raise LocationAdapterError('Conflicting geometry/projection reference roles')
    if geometry:
        return ['geometry-underlay']
    if projection:
        return ['seamless-panorama']
    if 'book-style' in roles:
        return ['book-style']
    if row.get('contextOnly'):
        raise LocationAdapterError('Unsupported context reference role; explicit semantic role required')
    return ['location-identity']


class LocationAdapter:
    def __init__(self, source_root, index_path, runner=None, python=None):
        self.root = Path(source_root).absolute()
        self.index = Path(index_path).absolute()
        self.runner = runner or subprocess.run
        self.python = python or sys.executable

    def _request(self, command, location, scope, stop, viewpoint, extra=(), timeout=15):
        if scope not in ('approved', 'all'):
            raise LocationAdapterError('Scope must be approved or all')
        if not isinstance(location, str) or not location or len(location) > 160 or location.startswith('-'):
            raise LocationAdapterError('Invalid location ID')
        argv = [self.python, '-B', str(self.root / 'tools/studio-locations/cli.py'),
                '--root', str(self.root), '--index', str(self.index), command,
                location, '--scope', scope]
        for flag, value in (('--stop', stop), ('--viewpoint', viewpoint)):
            if value is not None:
                if not isinstance(value, str) or not value or value.startswith('-') or len(value) > 160:
                    raise LocationAdapterError('Invalid selector')
                argv.extend((flag, value))
        try:
            result = self.runner(argv + list(extra), capture_output=True, text=True, timeout=timeout)
            if len(result.stdout.encode()) > 256 * 1024:
                raise LocationAdapterError('Location response exceeds bound')
            value = json.loads(result.stdout)
        except (subprocess.TimeoutExpired, OSError, ValueError) as exc:
            raise LocationAdapterError('Location worker failed or returned invalid metadata') from exc
        if result.returncode or not isinstance(value, dict) or value.get('error'):
            raise LocationAdapterError('Location request rejected; inspect catalog or worker receipt')
        return value

    def discover(self, location, scope='approved', stop=None, viewpoint=None):
        """Metadata only. Never index, stat media, restore, or register."""
        return self._request('query', location, scope, stop, viewpoint)

    def prepare(self, store, location, output, cache=None, scope='approved',
                stop=None, viewpoint=None, restore=True, max_bytes=32*1024*1024,
                media='references', entity_id=None,
                supported_roles=('geometry-underlay', 'location-identity', 'seamless-panorama', 'book-style')):
        """Authorized worker workflow. Restore is internal, not a permission gate.

        Imported reviewStatus stays unreviewed. Catalog approval evidence is retained
        as provenance, never converted into a Studio approval or native-imagegen.
        All required files are verified before any asset registration begins.
        """
        if type(max_bytes) is not int or not 0 < max_bytes <= 256*1024*1024:
            raise LocationAdapterError('Invalid byte budget')
        if media not in ('references', 'selected'):
            raise LocationAdapterError('Select references or selected media explicitly')
        out = Path(output).resolve()
        if out == self.root.resolve() or self.root.resolve() in out.parents:
            raise LocationAdapterError('Bundle must be outside source')
        manifest = self.discover(location, scope, stop, viewpoint)
        rows = [r for r in manifest.get('media', []) if r.get('isReference') or r.get('contextOnly')
                or media == 'selected' and r.get('selected')]
        if not rows:
            raise LocationAdapterError('No eligible media; draft stops require explicit scope=all')
        if len(rows) > 64 or sum(r.get('bytes', max_bytes+1) for r in rows) > max_bytes:
            raise LocationAdapterError('Reference selection exceeds budget')
        for row in rows:
            roles = reference_roles(row)
            if any(role not in supported_roles for role in roles):
                raise LocationAdapterError('Downstream does not support reference role: ' + ','.join(roles))
        extra = ['--output', str(out), '--max-bytes', str(max_bytes), '--media', media]
        if restore:
            if cache is None:
                raise LocationAdapterError('Bounded restore requires existing-adapter cache path')
            extra += ['--restore', '--cache', str(cache)]
        receipt = self._request('hydrate', location, scope, stop, viewpoint, extra, 195)
        if receipt.get('missing'):
            raise LocationAdapterError('Required media missing; inspect scoped restore receipt')
        verified = set(receipt.get('verifiedPaths', []))
        staged = []
        for row in rows:
            relative = Path(row['path'])
            if relative.is_absolute() or '..' in relative.parts or '\\' in row['path']:
                raise LocationAdapterError('Unsafe reference path')
            path = (out / 'media' / relative).resolve()
            if out not in path.parents or row['path'] not in verified:
                raise LocationAdapterError('Unverified reference bundle')
            if path.stat().st_size != row['bytes']:
                raise LocationAdapterError('Reference size differs')
            raw = path.read_bytes()
            if len(raw) != row['bytes'] or hashlib.sha256(raw).hexdigest() != row['sha256']:
                raise LocationAdapterError('Reference identity differs')
            # Studio uploads support image formats only; report other exact assets.
            if path.suffix.lower() not in ('.png', '.jpg', '.jpeg', '.webp'):
                continue
            roles = reference_roles(row)
            if any(role not in supported_roles for role in roles):
                raise LocationAdapterError('Downstream does not support reference role: ' + ','.join(roles))
            staged.append((row, raw, roles))
        assets = store.read()['assets']
        bindings = []
        for row, raw, roles in staged:
            existing = next((a for a in assets if a.get('sha256') == row['sha256'] and a.get('bytes') == row['bytes']), None)
            if existing:
                asset = existing
            else:
                provenance = {'source': 'location-catalog-import', 'sourcePath': row['path'],
                              'sourceSha256': row['sha256'], 'role': roles[0],
                              'catalogApprovalEvidence': row.get('approval'),
                              'catalogRoles': row.get('roles', []),
                              'indexProvenance': manifest.get('indexProvenance')}
                asset = store.upload_asset(raw, Path(row['path']).name, provenance, 'unreviewed')[0]
                assets.append(asset)
            binding = {'assetId': asset['id'], 'role': roles[0]}
            if entity_id and roles[0] == 'location-identity':
                binding['entityId'] = entity_id
            if binding not in bindings:
                bindings.append(binding)
        return {'location': manifest.get('location'), 'referenceBindings': bindings,
                'referenceIds': list(dict.fromkeys(b['assetId'] for b in bindings)),
                'references': [{'assetId': b['assetId'], 'role': b['role'],
                                'reviewStatus': next(a for a in assets if a['id'] == b['assetId']).get('reviewStatus', 'unreviewed'),
                                'availability': 'verified-request-bundle'} for b in bindings],
                'hydration': receipt, 'generationDispatched': False,
                'nonImagePaths': [r['path'] for r in rows if Path(r['path']).suffix.lower() not in ('.png','.jpg','.jpeg','.webp')]}
