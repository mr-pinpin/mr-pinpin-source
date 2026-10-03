import json
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.request import Request, urlopen
from urllib.error import HTTPError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from store import Store
from server import StudioServer


class BusinessRouteTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='pinpin-business-routes-')
        self.root = Path(self.temp.name)
        self.source = self.root / 'business'
        shutil.copytree(Path(__file__).resolve().parents[1] / 'business', self.source,
                        ignore=shutil.ignore_patterns('__pycache__'))
        self.store = Store(self.root / 'data')
        state = self.store.read()
        state['project']['chapters'] = [dict(id='test', title={'en':'Test'}, script='', scenes=[])]
        self.store.save_project(state['project'], state['revision'])
        self.server = StudioServer(('127.0.0.1', 0), self.store,
                                  business_source=self.source, runtime_dir=self.root / 'runtime')
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = 'http://127.0.0.1:' + str(self.server.server_port)

    def tearDown(self):
        self.server.shutdown(); self.server.server_close(); self.thread.join()
        self.temp.cleanup()

    def request(self, path, body=None):
        request = Request(self.base + path, data=None if body is None else json.dumps(body).encode(),
                          headers={'Content-Type':'application/json'})
        with urlopen(request) as response:
            return response.status, json.load(response)

    def wait(self, predicate):
        end = time.monotonic() + 8
        while time.monotonic() < end:
            if predicate(): return
            time.sleep(.05)
        self.fail('Business watcher did not reach expected state')

    def test_real_product_routes_and_validation(self):
        initial = self.request('/api/runtime')[1]['business']['active']
        for path in ('/api/plan?chapterId=test','/api/jobs','/api/inbox','/api/insights','/api/media'):
            self.assertEqual(self.request(path)[0], 200)
        status, job = self.request('/api/jobs', dict(kind='orbit-video', instruction='Prepare reviewed handoff'))
        self.assertEqual(status, 201)
        self.assertEqual(job['job']['kind'], 'orbit-video')
        self.assertEqual(self.request('/api/insights')[1]['totalJobs'], 1)
        self.request('/api/plan/approve', dict(chapterId='test', expectedRevision=self.store.read()['revision']))
        self.assertTrue(self.request('/api/plan?chapterId=test')[1]['approved'])
        with self.assertRaises(HTTPError) as invalid:
            self.request('/api/jobs', dict(kind='bad-kind'))
        self.assertEqual(invalid.exception.code, 400); invalid.exception.close()
        self.assertEqual(self.request('/api/runtime')[1]['business']['active'], initial)

    def test_same_server_watches_product_edit_and_bad_candidate(self):
        runtime = self.server.business_runtime
        original = runtime.snapshot()['active']
        insights = self.source / 'insights.py'
        insights.write_text(insights.read_text().replace('schemaVersion=1,', 'schemaVersion=17,'))
        self.wait(lambda: runtime.snapshot()['active'] != original)
        healthy = runtime.snapshot()['active']
        self.assertEqual(self.request('/api/insights')[1]['schemaVersion'], 17)
        self.assertIs(self.server.business_runtime, runtime)
        self.assertTrue(self.thread.is_alive())
        insights.write_text('def broken(:\n')
        self.wait(lambda: runtime.snapshot()['status'] == 'error')
        self.assertEqual(self.request('/api/insights')[1]['schemaVersion'], 17)
        self.assertEqual(runtime.snapshot()['active'], healthy)
        self.assertEqual(self.request('/api/conversation')[0], 200)

    def test_unserializable_route_rolls_back_without_breaking_transport(self):
        runtime = self.server.business_runtime
        original = runtime.snapshot()['active']
        routes = self.source / 'routes.py'
        routes.write_text(routes.read_text().replace('return 200, insights(store)',
                                                   'return 200, {"bad": object()}'))
        self.wait(lambda: runtime.snapshot()['active'] != original)
        with self.assertRaises(HTTPError) as error:
            self.request('/api/insights')
        self.assertEqual(error.exception.code, 503); error.exception.close()
        self.assertEqual(runtime.snapshot()['active'], original)
        self.assertEqual(self.request('/api/insights')[1]['schemaVersion'], 1)
        self.assertEqual(self.request('/api/conversation')[0], 200)

    def test_cli_reads_active_bundle_without_runtime_writes(self):
        runtime = self.root / 'runtime'
        def files():
            return {str(p.relative_to(runtime)): p.read_bytes() for p in runtime.rglob('*') if p.is_file()}
        before = files()
        cli = Path(__file__).resolve().parents[1] / 'cli.py'
        result = subprocess.run([sys.executable, str(cli), '--data-dir', str(self.store.root),
                                 '--business-source', str(self.source), '--runtime-dir', str(runtime),
                                 'inbox'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIsInstance(json.loads(result.stdout), dict)
        self.assertEqual(files(), before)

    def test_frozen_kernel_requires_explicit_business_source(self):
        with patch('server.stable_release', return_value='a' * 64):
            with self.assertRaisesRegex(ValueError, 'business-source'):
                StudioServer(('127.0.0.1', 0), self.store)


if __name__ == '__main__':
    unittest.main()
