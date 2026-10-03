import copy
import hashlib
import io
import json
import threading
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from PIL import Image
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from insights import insights
import media_library as media
from model import StudioError
from store import Store
from jobs import create_job
from server import StudioServer


class StaticStore:
    def __init__(self, state): self.state = state
    def read(self): return copy.deepcopy(self.state)


class InsightMediaTests(unittest.TestCase):
    def test_no_inferred_retries_or_provider_timing(self):
        jobs = [dict(id='one', kind='illustration', status='failed', sceneIds=['scene'],
                     claimedAt='2026-10-02T10:00:00+00:00', updatedAt='2026-10-02T12:00:00+00:00'),
                dict(id='two', kind='illustration', status='completed', sceneIds=['scene'],
                     claimedAt='2026-10-02T10:01:00+00:00', completedAt='2026-10-02T10:02:00+00:00'),
                dict(id='three', kind='illustration', status='queued', retryOf='one', sceneIds=['scene'])]
        state = dict(revision=4, jobs=jobs, events=[dict(type='job.failed', jobId='one', createdAt='2026-10-02T10:00:30+00:00')])
        result = insights(StaticStore(state))
        self.assertEqual(result['explicitRetries'], 1)
        self.assertEqual(result['observedDurations']['medianSeconds'], 45)
        self.assertEqual(result['hotspots'][0]['failures'], 1)
        self.assertEqual(result['hotspots'][0]['retries'], 1)
        self.assertEqual(result['totalJobs'], 3)

    def test_unknown_timing_is_not_zero(self):
        result = insights(StaticStore(dict(revision=0, jobs=[dict(id='old', status='completed')], events=[])))
        self.assertIsNone(result['observedDurations']['medianSeconds'])
        self.assertEqual(result['observedDurations']['terminalJobsWithoutTiming'], 1)

    def test_explicit_registration_excluded_from_timing(self):
        job=dict(id='imported', status='completed', instruction='Register already-generated R24 candidate',
                 claimedAt='2026-10-02T10:00:00+00:00', completedAt='2026-10-02T10:00:00.02+00:00')
        result=insights(StaticStore(dict(revision=0,jobs=[job],events=[])))
        self.assertIsNone(result['observedDurations']['medianSeconds'])
        self.assertEqual(result['observedDurations']['excludedHistoricalRegistrations'], 1)
        self.assertEqual(result['totalJobs'], 1)

    def test_allowlist_integrity_and_traversal(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); (root/'clip.mp4').write_bytes(b'known clip')
            entries = {'clip': ('clip.mp4', 'video/mp4', hashlib.sha256(b'known clip').hexdigest())}
            with patch.object(media, 'ARCHIVE', root), patch.object(media, 'FILES', entries), patch.object(media, '_verified', {}):
                self.assertEqual(media.media_file('clip')[1], 'video/mp4')
                for value in ('../clip.mp4', '/etc/passwd', '%2e%2e/clip.mp4'):
                    with self.assertRaises(StudioError): media.media_file(value)
                (root/'clip.mp4').write_bytes(b'changed clip')
                with self.assertRaises(StudioError) as error: media.media_file('clip')
                self.assertEqual(error.exception.code, 'storage_corruption')

    def test_symlink_escape_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); (root/'archive').mkdir(); (root/'outside').write_bytes(b'x')
            (root/'archive'/'clip').symlink_to(root/'outside')
            with patch.object(media, 'ARCHIVE', root/'archive'), patch.object(media, 'FILES', {'clip': ('clip','video/mp4',hashlib.sha256(b'x').hexdigest())}):
                with self.assertRaises(StudioError): media.media_file('clip')

    def test_unknown_projection_not_mislabeled(self):
        state=dict(revision=0,project={'entities':[dict(id='place',kind='panorama',referenceIds=['a'])]},
                   assets=[dict(id='a', name='Cross atlas', url='/api/assets/a', width=300, height=200, sha256='x')])
        with patch.object(media, 'FILES', {}):
            self.assertEqual(media.media_library(StaticStore(state))['items'][0]['projection'], 'unknown')

    def test_fixed_media_import_http_and_idempotence(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); archive=root/'archive'; archive.mkdir()
            raw=io.BytesIO(); Image.new('RGB',(16,8),'red').save(raw,'PNG')
            image=raw.getvalue(); (archive/'sphere.png').write_bytes(image)
            (archive/'clip.mp4').write_bytes(b'video')
            entries={'sphere':('sphere.png','image/png',hashlib.sha256(image).hexdigest()),
                     'clip':('clip.mp4','video/mp4',hashlib.sha256(b'video').hexdigest())}
            store=Store(root/'data')
            with patch.object(media,'ARCHIVE',archive), patch.object(media,'FILES',entries), patch.object(media,'_verified',{}):
                server=StudioServer(('127.0.0.1',0),store)
                thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
                try:
                    url='http://127.0.0.1:'+str(server.server_port)+'/api/media/import'
                    def post(identifier):
                        request=Request(url,data=json.dumps({'id':identifier}).encode(),headers={'Content-Type':'application/json'})
                        with urlopen(request) as response:return json.load(response)
                    first=post('sphere');second=post('sphere')
                    self.assertEqual(first['asset']['id'],second['asset']['id'])
                    self.assertEqual(first['revision'],second['revision'])
                    self.assertEqual(store.asset_path(first['asset']['id']).read_bytes(),image)
                    for identifier, expected in [('clip',400),('../outside',400),('unknown',404)]:
                        with self.assertRaises(HTTPError) as error:post(identifier)
                        self.assertEqual(error.exception.code,expected)
                        error.exception.close()
                finally:
                    server.shutdown();server.server_close();thread.join()

    def test_orbit_handoff_and_retry_lineage(self):
        with tempfile.TemporaryDirectory() as temp:
            store=Store(temp)
            first=create_job(store, dict(kind='orbit-video',instruction='Inspect the tractor'))[0]
            self.assertIn('does not execute a paid video call', first['prompt'])
            retry=create_job(store, dict(kind='orbit-video', instruction='Repair the loop', retryOf=first['id']))[0]
            self.assertEqual(retry['retryOf'], first['id'])
            changed=create_job(store, dict(kind='edit',instruction='Revise source image',retryOf=first['id']))[0]
            self.assertEqual(changed['retryOf'], first['id'])
            with self.assertRaises(StudioError):
                create_job(store, dict(kind='orbit-video',instruction='Missing parent',retryOf='missing'))


if __name__ == '__main__': unittest.main()
