import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace

spec = importlib.util.spec_from_file_location('location_adapter', Path(__file__).parents[1] / 'locations.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class Store:
    def __init__(self, assets=()):
        self.assets = list(assets)
        self.uploads = []
    def read(self):
        return {'assets': list(self.assets)}
    def upload_asset(self, raw, name, provenance, review):
        self.uploads.append((provenance, review))
        asset = {'id': 'asset-' + hashlib.sha256(raw).hexdigest()[:24],
                 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw), 'reviewStatus': review}
        self.assets.append(asset)
        return asset, {}


class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name)
        self.out = self.home / 'bundle'
        self.rows = []
        for name, raw, context in [('room.png', b'room', False), ('projection.png', b'projection', True)]:
            path = self.out / 'media' / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
            self.rows.append({'path': name, 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest(),
                              'isReference': not context, 'contextOnly': context,
                              'approval': 'projection-style-reference' if context else 'published-book-reference',
                              'roles': ['projection-style-only'] if context else ['book-reference']})
        self.calls = []
        self.missing = []
        def run(argv, **kwargs):
            self.calls.append((argv, kwargs))
            value = {'media': self.rows, 'location': {'id': 'house/common'}, 'indexProvenance': {'hash': 'fixture'}} if 'query' in argv else {'missing': self.missing, 'verifiedPaths': [r['path'] for r in self.rows]}
            return SimpleNamespace(returncode=0, stdout=json.dumps(value))
        self.adapter = module.LocationAdapter(self.home / 'source', self.home / 'index.json', run)
    def prepare(self, store=None, **kwargs):
        return self.adapter.prepare(store or Store(), 'house/common', self.out, restore=False, **kwargs)
    def test_metadata_only(self):
        self.adapter.discover('tractor/orbit', scope='all', stop='stop-07')
        argv = self.calls[0][0]
        self.assertIn('query', argv)
        for prohibited in ('index', '--probe-media', '--restore'):
            self.assertNotIn(prohibited, argv)
        self.assertIn('all', argv)
    def test_roles_and_honest_review(self):
        store = Store()
        result = self.prepare(store, entity_id='entity-room')
        self.assertEqual([b['role'] for b in result['referenceBindings']], ['location-identity', 'seamless-panorama'])
        self.assertNotIn('entityId', result['referenceBindings'][1])
        self.assertTrue(all(r['reviewStatus'] == 'unreviewed' for r in result['references']))
        self.assertTrue(all(p['source'] == 'location-catalog-import' and review == 'unreviewed' for p, review in store.uploads))
        self.assertFalse(result['generationDispatched'])
    def test_actual_house_geometry_underlay_shape(self):
        row = self.rows[0]
        row.update(path='merged-semantic-plan.png', roles=['geometry-underlay', 'underlay'],
                   contextOnly=True, approval='geometry-underlay')
        (self.out/'media/room.png').rename(self.out/'media/merged-semantic-plan.png')
        result = self.prepare(entity_id='entity-room')
        self.assertEqual(result['referenceBindings'][0]['role'], 'geometry-underlay')
        self.assertNotIn('entityId', result['referenceBindings'][0])
        self.assertEqual(result['referenceBindings'][1]['role'], 'seamless-panorama')
    def test_unsupported_geometry_fails_before_registration(self):
        self.rows[0].update(roles=['geometry-underlay','underlay'], contextOnly=True)
        store=Store()
        with self.assertRaisesRegex(module.LocationAdapterError, 'Downstream'):
            self.prepare(store, supported_roles=('location-identity','seamless-panorama'))
        self.assertEqual(store.uploads, [])
        self.assertEqual(len(self.calls), 1)  # No hydration before semantic rejection.
    def test_unclassified_context_fails_instead_of_relabeling(self):
        self.rows[1]['roles']=['unknown-context']
        with self.assertRaisesRegex(module.LocationAdapterError, 'Unsupported context'):
            self.prepare()
    def test_conflicting_projection_geometry_rejected(self):
        self.rows[1]['roles']=['geometry-underlay','projection-style-only']
        with self.assertRaisesRegex(module.LocationAdapterError, 'Conflicting'):
            self.prepare()
    def test_reuse_registered_ids_without_changing_review(self):
        row = self.rows[0]
        store = Store([{'id': 'existing', 'sha256': row['sha256'], 'bytes': row['bytes'], 'reviewStatus': 'approved'}])
        result = self.prepare(store)
        self.assertEqual(result['referenceIds'][0], 'existing')
        self.assertEqual(len(store.uploads), 1)
        self.assertEqual(result['references'][0]['reviewStatus'], 'approved')
    def test_missing_no_registration(self):
        self.missing = [{'path': 'room.png'}]
        store = Store()
        with self.assertRaises(module.LocationAdapterError): self.prepare(store)
        self.assertEqual(store.uploads, [])
    def test_corruption_preflights_all_before_registration(self):
        (self.out / 'media/projection.png').write_bytes(b'bad')
        store = Store()
        with self.assertRaises(module.LocationAdapterError): self.prepare(store)
        self.assertEqual(store.uploads, [])
    def test_budget(self):
        with self.assertRaises(module.LocationAdapterError): self.prepare(max_bytes=1)
    def test_unsafe_path(self):
        self.rows[0]['path'] = '../outside.png'
        with self.assertRaises(module.LocationAdapterError): self.prepare()
    def test_restore_internal_explicit_budget(self):
        self.adapter.prepare(Store(), 'house/common', self.out, cache=self.home/'cache')
        self.assertIn('--restore', self.calls[1][0])
        self.assertEqual(self.calls[1][1]['timeout'], 195)
    def test_empty_approved_stop_not_fabricated(self):
        self.rows = []
        with self.assertRaisesRegex(module.LocationAdapterError, 'scope=all'): self.prepare()
    def test_unknown_worker_and_selector_rejected(self):
        self.adapter.runner = lambda *a, **k: SimpleNamespace(returncode=2, stdout='{"error": {}}')
        with self.assertRaises(module.LocationAdapterError): self.adapter.discover('unknown')
        with self.assertRaises(module.LocationAdapterError): self.adapter.discover('--restore')

if __name__ == '__main__': unittest.main()
