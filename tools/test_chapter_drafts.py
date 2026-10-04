"""Isolated portable regression suite; no live project fixtures or artwork calls.

Run with --studio-dir <source/tools/studio> --kernel-dir <stable release>.
"""
import argparse
import base64
import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('--studio-dir', required=True)
parser.add_argument('--kernel-dir', required=True)
parser.add_argument('--scratch-dir', required=True)
args, remaining = parser.parse_known_args()
sys.path.insert(0, args.kernel_dir)
sys.path.insert(0, args.studio_dir)
from store import Store
from model import StudioError
from business.chapter_drafts import save_draft, patch_draft, current, draft_context, authorize_production
from business.jobs import create_job
from business import self_test, selected_context
from review_state import state_at_revision

class DraftTests(unittest.TestCase):
    def setUp(self):
        Path(args.scratch_dir).mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=args.scratch_dir)
        self.addCleanup(self.temp.cleanup)
        self.store = Store(self.temp.name)
        state = self.store.read(); project = state['project']
        project['entities'] = [{'id': 'hero', 'kind': 'character', 'name': 'Hero', 'referenceIds': []},
                               {'id': 'forest', 'kind': 'location', 'name': 'Forest', 'referenceIds': []}]
        self.store.save_project(project, state['revision'])
        self.body = {'chapterId': 'pilot', 'baseVersion': 0, 'request': 'Original request',
                     'spec': {'title': 'Pilot', 'synopsis': 'A leaf returns.', 'referenceIds': [],
                              'location': {'baseEntityId': 'forest', 'proposed': True, 'description': 'Sheltered clearing'},
                              'panels': [{'id': 'p' + str(i), 'action': 'Watch leaf', 'cause': 'Leaf moves',
                                          'effect': 'Leaf settles', 'caption': 'Hmm…', 'camera': 'Close-up',
                                          'beat': 'repeat', 'seconds': 5, 'castIds': ['hero'],
                                          'dependsOn': [], 'previewKind': 'schematic-placeholder'} for i in range(10)]}}
    def save(self):
        self.body['expectedRevision'] = self.store.read()['revision']
        return save_draft(self.store, self.body)
    def chapter(self):
        return self.store.read()['project']['chapters'][-1]
    def patch(self, fields=None):
        v = current(self.chapter())
        return {'chapterId': 'pilot', 'baseVersion': v['version'], 'baseSHA256': v['sha256'],
                'expectedRevision': self.store.read()['revision'], 'request': 'Quiet pause',
                'patches': [{'panelId': 'p7', 'fields': fields or {'caption': 'Quiet', 'seconds': 6}}]}
    def authorization(self):
        v = current(self.chapter())
        return {'chapterId': 'pilot', 'version': v['version'], 'sha256': v['sha256'],
                'referenceHash': v['referenceHash'], 'expectedRevision': self.store.read()['revision'],
                'explicitFullProductionGo': True, 'userInstruction': 'Go: full production for this reviewed version.'}
    def job(self, **extra):
        return create_job(self.store, {'kind': 'illustration', 'chapterId': 'pilot', 'sceneIds': ['p7'],
                                       'instruction': 'Fixture only; never executed', **extra})
    def asset(self, prompt=None):
        import struct, zlib
        def chunk(kind, data):
            return struct.pack('!I', len(data)) + kind + data + struct.pack('!I', zlib.crc32(kind + data))
        raw = b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('!IIBBBBB', 1, 1, 8, 2, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(b'\0\0\0\0')) + chunk(b'IEND', b'')
        provenance = {'role': 'book-style'}
        if prompt: provenance['prompt'] = prompt
        asset, _ = self.store.upload_asset(raw, 'fixture', provenance)
        return asset
    def test_patch_exact_and_stale(self):
        self.save(); old = copy.deepcopy(self.chapter()); body = self.patch(); result = patch_draft(self.store, body)
        v = current(self.chapter())
        self.assertEqual(self.chapter()['studioDraft']['versions'][0], old['studioDraft']['versions'][0])
        for i, p in enumerate(v['spec']['panels']):
            if i != 7: self.assertEqual(p, old['studioDraft']['versions'][0]['spec']['panels'][i])
        self.assertEqual({c['field'] for c in result['changedFields']}, {'caption', 'seconds'})
        self.assertIsNone(result['timing']['requestAcceptanceToCompletionSeconds'])
        self.assertTrue(result['appLink'].startswith('/?chapter='))
        with self.assertRaises(StudioError): patch_draft(self.store, body)
    def test_long_chapter_pages(self):
        p = self.body['spec']['panels'][0]
        self.body['spec']['panels'] = [dict(copy.deepcopy(p), id='p' + str(i)) for i in range(215)]
        self.save(); context = draft_context(self.chapter(), page=17)
        self.assertEqual(context['panelCount'], 215); self.assertEqual(len(context['panels']), 11)
        self.assertEqual(self.chapter()['scenes'][0]['tempo'], {'weight': 2})
        self.assertEqual(current(self.chapter())['spec']['panels'][0]['seconds'], 5)
    def test_role_and_required_errors(self):
        for transform in (lambda s:s['location'].update(baseEntityId='hero'),
                          lambda s:s['panels'][0].update(castIds=['forest']),
                          lambda s:s.pop('title'), lambda s:s['location'].pop('description'),
                          lambda s:s['panels'][0].update(seconds=True),
                          lambda s:s['panels'][0].update(dependsOn=[{}]),
                          lambda s:s['panels'][0].update(imageAssetId='missing'),
                          lambda s:s['panels'][0].update(previewKind='generated'),
                          lambda s:s['panels'][0].update(status='user-approved')):
            body = copy.deepcopy(self.body); transform(body['spec']); body['expectedRevision'] = self.store.read()['revision']
            with self.assertRaises(StudioError): save_draft(self.store, body)
        self.assertEqual(self.store.read()['jobs'], [])
    def test_revision_required(self):
        with self.assertRaises(StudioError): save_draft(self.store, self.body)
        self.body['expectedRevision'] = 0
        with self.assertRaises(StudioError): save_draft(self.store, self.body)
    def test_reference_bindings_and_missing_bytes(self):
        asset = self.asset(); self.body['spec']['referenceIds'] = [asset['id']]
        self.store.asset_path(asset['id']).unlink(); self.save()
        binding = current(self.chapter())['referenceBindings'][0]
        self.assertEqual(binding['sha256'], asset['sha256']); self.assertIn('book-style', binding['roles'])
        self.assertEqual(binding['availability'], 'unresolved-local')
        with self.assertRaises(StudioError): self.job(productionScope='rough-preproduction')
        self.assertEqual(self.store.read()['jobs'], [])
    def test_production_gate_revision_and_rough(self):
        self.save()
        with self.assertRaises(StudioError): self.job()
        with self.assertRaises(StudioError): self.job(approved=True, draftVersion=0)
        self.job(productionScope='rough-preproduction')
        authorize_production(self.store, self.authorization()); self.job()
        patch_draft(self.store, self.patch())
        with self.assertRaises(StudioError): self.job()
        self.assertEqual(len(self.store.read()['jobs']), 2)
    def test_reference_change_invalidates_authorization(self):
        asset = self.asset(); self.body['spec']['referenceIds'] = [asset['id']]; self.save()
        authorize_production(self.store, self.authorization())
        self.store.mutate(lambda st:st['assets'][0].update(sha256='a'*64))
        with self.assertRaises(StudioError): self.job()
    def test_registered_visual_preview(self):
        asset = self.asset(prompt='Actual fixture provenance')
        self.body['spec']['panels'][0].update(previewKind='generated', imageAssetId=asset['id'])
        self.save(); self.assertEqual(current(self.chapter())['referenceBindings'][0]['assetId'], asset['id'])
    def test_provenance_separate_from_semantics(self):
        first = self.save(); self.body.update(baseVersion=1, request='Different wording')
        second = self.save(); versions = self.chapter()['studioDraft']['versions']
        self.assertEqual(first['sha256'], second['sha256']); self.assertNotEqual(versions[0]['requestSHA256'], versions[1]['requestSHA256'])
    def test_historical_context_no_mutation(self):
        first = self.save(); old = state_at_revision(self.store, first['revision'])
        patch_draft(self.store, self.patch()); self.assertEqual(current(old['project']['chapters'][-1])['version'], 1)
        before = self.store.read(); text, scope, inputs = selected_context(self.store, {'chapterId': 'pilot', 'text': 'Revise panel 7'})
        self.assertIn('patchRoute', json.dumps(inputs)); self.assertEqual(before, self.store.read()); self.assertTrue(self_test())

    def test_go_route_receipt_persists_without_job(self):
        from business.routes import route
        self.save()
        body = self.authorization()
        status, result = route(self.store, 'POST', '/api/chapter-drafts/authorize-production', {}, body)
        self.assertEqual(status, 200)
        reopened = Store(self.temp.name)
        chapter = reopened.read()['project']['chapters'][-1]
        receipt = result['receipt']
        self.assertEqual(chapter['studioDraft']['productionAuthorization'], receipt)
        self.assertEqual(chapter['studioDraft']['authorizationReceipts'], [receipt])
        self.assertEqual(reopened.read()['jobs'], [])
        self.assertFalse(result['productionStarted'])
        self.assertIsNone(result['timing']['requestAcceptanceToCompletionSeconds'])
        self.assertEqual(receipt['userInstruction'], body['userInstruction'])

    def test_go_rejects_stale_and_historical_without_mutation(self):
        from business.routes import route
        self.save()
        for fields in ({'version': 0}, {'sha256': '0'*64}, {'referenceHash': '0'*64},
                       {'readOnly': True}, {'reviewSnapshot': True}, {'revision': 1},
                       {'explicitFullProductionGo': False}, {'expectedRevision': 0}):
            body = dict(self.authorization(), **fields)
            before = self.store.read()
            with self.assertRaises(StudioError):
                route(self.store, 'POST', '/api/chapter-drafts/authorize-production', {}, body)
            self.assertEqual(self.store.read(), before)

    def test_go_edit_preserves_receipt_requires_fresh_go(self):
        self.save()
        receipt = authorize_production(self.store, self.authorization())['receipt']
        patch_draft(self.store, self.patch())
        chapter = self.chapter()
        self.assertNotIn('productionAuthorization', chapter['studioDraft'])
        self.assertEqual(chapter['studioDraft']['authorizationReceipts'], [receipt])
        with self.assertRaises(StudioError): self.job()
        authorize_production(self.store, self.authorization())
        self.job()

    def test_legacy_go_hydration_preserves_frozen_version(self):
        from business.routes import route
        self.save()
        def legacy(st):
            v = current(st['project']['chapters'][-1])
            v.pop('referenceHash'); v.pop('referenceBindings')
        self.store.mutate(legacy)
        before = copy.deepcopy(current(self.chapter()))
        _, context = route(self.store, 'GET', '/api/chapter-drafts', {'chapterId':['pilot']}, None)
        body = self.authorization() if 'referenceHash' in before else {
            'chapterId':'pilot', 'version':before['version'], 'sha256':before['sha256'],
            'referenceHash':context['draft']['referenceHash'], 'expectedRevision':context['revision'],
            'explicitFullProductionGo':True, 'userInstruction':'Explicit full production go for this legacy reviewed version.'}
        authorize_production(self.store, body)
        self.assertEqual(current(self.chapter()), before)
        self.job()

    def test_go_reference_role_change_requires_new_review(self):
        asset = self.asset()
        self.body['spec']['referenceIds'] = [asset['id']]
        self.save()
        body = self.authorization()
        self.store.mutate(lambda st:st['assets'][0]['provenance'].update(role='changed-role'))
        body['expectedRevision'] = self.store.read()['revision']
        with self.assertRaises(StudioError): authorize_production(self.store, body)


if __name__ == '__main__':
    unittest.main(argv=[sys.argv[0], *remaining])
