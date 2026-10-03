import os
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from business_runtime import BusinessRuntime
from immutable_bundle import verify_bundle
from model import StudioError
from release import freeze

PACKAGE = """from .helpers import VALUE
API_VERSION = 1
def selected_context(store, body):
    return VALUE, {}, []
def route(store, method, path, query, body):
    return 200, {"value": VALUE}
def self_test():
    return True
"""


class BusinessRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="pinpin-business-test-")
        self.root = Path(self.temp.name)
        self.source = self.root / "business"
        self.source.mkdir()
        self.artifacts = self.root / "runtime"
        self.runtimes = []
        self.write()

    def tearDown(self):
        for runtime in self.runtimes:
            runtime.close()
        for directory, dirs, files in os.walk(self.root):
            Path(directory).chmod(0o755)
            for name in files:
                path = Path(directory) / name
                if not path.is_symlink():
                    path.chmod(0o644)
        self.temp.cleanup()

    def write(self, value="first", package=PACKAGE):
        (self.source / "__init__.py").write_text(package)
        (self.source / "helpers.py").write_text("VALUE = " + repr(value))

    def runtime(self, watch=False):
        runtime = BusinessRuntime(self.source, self.artifacts, watch=watch)
        self.runtimes.append(runtime)
        return runtime

    def test_relative_import_hot_swap_and_immutable_versions(self):
        runtime = self.runtime()
        first = runtime.snapshot()["active"]
        first_namespace = runtime.active.name
        self.assertEqual(runtime.invoke("selected_context", None, {})[0], "first")
        self.write("second")
        runtime.poll(force=True)
        second = runtime.snapshot()["active"]
        self.assertNotEqual(first, second)
        self.assertEqual(runtime.snapshot()["previous"], first)
        self.assertEqual(runtime.invoke("route", None, "GET", "/", {}, {})[1]["value"], "second")
        path = self.artifacts / "business-builds" / first
        self.assertEqual(verify_bundle(path)["hash"], first)
        self.assertEqual((path / "helpers.py").read_text(), "VALUE = 'first'")
        self.assertEqual(path.stat().st_mode & 0o222, 0)
        self.write("third")
        runtime.poll(force=True)
        self.assertNotIn(first_namespace, sys.modules)
        self.assertFalse(any(k.startswith(first_namespace + ".") for k in sys.modules))

    def test_invalid_syntax_import_contract_selftest_preserve_last_good(self):
        runtime = self.runtime()
        first = runtime.snapshot()["active"]
        variants = [
            PACKAGE + "\ndef broken(",
            "from .missing import value\n" + PACKAGE,
            PACKAGE.replace("API_VERSION = 1", "API_VERSION = 2"),
            PACKAGE.replace("def route(store, method, path, query, body):", "def route():"),
            PACKAGE.replace("return True", "raise RuntimeError('selftest failed')"),
            PACKAGE.replace("return True", "return False"),
        ]
        for package in variants:
            with self.subTest(package=package):
                self.write(package=package)
                runtime.poll(force=True)
                self.assertEqual(runtime.snapshot()["active"], first)
                self.assertEqual(runtime.snapshot()["status"], "error")
                self.assertEqual(runtime.invoke("selected_context", None, {})[0], "first")

    def test_mutation_failure_rolls_back_without_replay_or_auto_retry(self):
        runtime = self.runtime()
        first = runtime.snapshot()["active"]
        broken = PACKAGE.replace('return 200, {"value": VALUE}',
                                 'store.append("persisted-once"); raise RuntimeError("after write")')
        self.write("broken", broken)
        runtime.poll(force=True)
        failed = runtime.snapshot()["active"]
        mutations = []
        with self.assertRaises(StudioError) as error:
            runtime.invoke("route", mutations, "POST", "/", {}, {})
        self.assertEqual(error.exception.code, "business_call")
        self.assertEqual(mutations, ["persisted-once"])
        self.assertEqual(runtime.snapshot()["active"], first)
        runtime.poll(force=True)
        self.assertEqual(runtime.snapshot()["active"], first)
        resumed = self.runtime()
        self.assertEqual(resumed.snapshot()["active"], first)
        self.assertEqual(resumed.snapshot()["error"]["hash"], failed)
        self.assertEqual(resumed.invoke("selected_context", None, {})[0], "first")

    def test_expected_api_validation_does_not_roll_back(self):
        package = "from model import StudioError\n" + PACKAGE.replace(
            'return 200, {"value": VALUE}', 'raise StudioError("Bad user input", status=400)')
        self.write(package=package)
        runtime = self.runtime()
        first = runtime.snapshot()["active"]
        with self.assertRaises(StudioError) as error:
            runtime.invoke("route", None, "POST", "/", {}, {})
        self.assertEqual(error.exception.status, 400)
        self.assertEqual(runtime.snapshot()["active"], first)
        self.assertEqual(runtime.snapshot()["status"], "ready")

    def test_output_validator_failure_rolls_back(self):
        runtime = self.runtime()
        first = runtime.snapshot()["active"]
        self.write("invalid-output")
        runtime.poll(force=True)
        def validate(value):
            raise StudioError("Malformed envelope")
        with self.assertRaises(StudioError) as error:
            runtime.invoke("selected_context", None, {}, validate=validate)
        self.assertEqual(error.exception.code, "business_call")
        self.assertEqual(runtime.snapshot()["active"], first)

    def test_inflight_lease_survives_two_swaps_and_late_failure_cannot_revert_new(self):
        package = PACKAGE.replace('return 200, {"value": VALUE}', '''
    store["entered"].set()
    store["release"].wait(5)
    from .helpers import VALUE as late_value
    if body.get("fail"):
        raise RuntimeError("old failure")
    return 200, {"value": late_value}''')
        self.write(package=package)
        runtime = self.runtime()
        original_namespace = runtime.active.name
        entered, release = threading.Event(), threading.Event()
        outcome = []
        def request():
            try:
                outcome.append(runtime.invoke("route", {"entered": entered, "release": release}, "GET", "/", {}, {"fail": True}))
            except StudioError as exc:
                outcome.append(exc.code)
        thread = threading.Thread(target=request)
        thread.start()
        self.assertTrue(entered.wait(2))
        self.write("second")
        runtime.poll(force=True)
        self.write("third")
        runtime.poll(force=True)
        newest = runtime.snapshot()["active"]
        self.assertIn(original_namespace, sys.modules)
        self.assertEqual(runtime.invoke("selected_context", None, {})[0], "third")
        release.set()
        thread.join(3)
        self.assertFalse(thread.is_alive())
        self.assertEqual(outcome, ["business_call"])
        self.assertEqual(runtime.snapshot()["active"], newest)
        self.assertNotIn(original_namespace, sys.modules)

    def test_restart_bad_source_restores_last_good(self):
        runtime = self.runtime()
        first = runtime.snapshot()["active"]
        self.write("second")
        runtime.poll(force=True)
        latest = runtime.snapshot()["active"]
        self.write(package="syntax error :")
        runtime.poll(force=True)
        runtime.close()
        resumed = self.runtime()
        self.assertEqual(resumed.snapshot()["active"], latest)
        self.assertEqual(resumed.snapshot()["previous"], first)
        self.assertEqual(resumed.invoke("selected_context", None, {})[0], "second")

    def test_watcher_and_debounce_same_process(self):
        runtime = self.runtime(watch=True)
        first = runtime.snapshot()["active"]
        self.write("next")
        runtime.poll()
        self.assertEqual(runtime.snapshot()["active"], first)
        deadline = time.monotonic() + 4
        while runtime.snapshot()["active"] == first and time.monotonic() < deadline:
            time.sleep(.05)
        self.assertNotEqual(runtime.snapshot()["active"], first)
        self.assertEqual(runtime.invoke("selected_context", None, {})[0], "next")
        self.assertTrue(runtime.worker.is_alive())

    def test_kernel_identity_excludes_product_and_test_trees(self):
        kernel = self.root / "kernel-source"
        (kernel / "web/workspace-dev").mkdir(parents=True)
        for path in ("business", "tests", "web/tests"):
            (kernel / path).mkdir(parents=True)
        for path in ("server.py", "conversation.py", "web/index.html"):
            (kernel / path).write_text("# stable kernel")
        for path in ("business/product.py", "web/workspace-dev/chat.js", "tests/test_product.py", "web/tests/ui.cjs"):
            (kernel / path).write_text("first")
        first = freeze(kernel, self.artifacts)
        for path in ("business/product.py", "web/workspace-dev/chat.js", "tests/test_product.py", "web/tests/ui.cjs"):
            (kernel / path).write_text("changed independently")
        second = freeze(kernel, self.artifacts)
        self.assertEqual(first["stableRelease"], second["stableRelease"])
        frozen = Path(first["path"])
        self.assertFalse((frozen / "business").exists())
        self.assertFalse((frozen / "web/workspace-dev").exists())
        (kernel / "server.py").write_text("# changed kernel")
        self.assertNotEqual(freeze(kernel, self.artifacts)["stableRelease"], first["stableRelease"])

    def test_system_exit_import_call_and_watcher_recovery(self):
        runtime = self.runtime(watch=True)
        first = runtime.snapshot()["active"]
        self.write(package="raise SystemExit(2)\n" + PACKAGE)
        runtime.poll(force=True)
        self.assertEqual(runtime.snapshot()["active"], first)
        self.assertTrue(runtime.worker.is_alive())
        self.write(package=PACKAGE.replace('return 200, {"value": VALUE}', 'raise SystemExit(3)'))
        runtime.poll(force=True)
        with self.assertRaises(StudioError):
            runtime.invoke("route", None, "GET", "/", {}, {})
        self.assertEqual(runtime.snapshot()["active"], first)
        self.write("recovered")
        deadline = time.monotonic() + 4
        while runtime.snapshot()["active"] == first and time.monotonic() < deadline:
            time.sleep(.05)
        self.assertEqual(runtime.invoke("selected_context", None, {})[0], "recovered")
        self.assertTrue(runtime.worker.is_alive())

    def test_unserializable_route_payload_and_optional_cli_call(self):
        runtime = self.runtime()
        first = runtime.snapshot()["active"]
        self.write(package=PACKAGE.replace('{"value": VALUE}', '{"value": object()}'))
        runtime.poll(force=True)
        with self.assertRaises(StudioError) as error:
            runtime.invoke("route", None, "GET", "/", {}, {})
        self.assertEqual(error.exception.code, "business_call")
        self.assertEqual(runtime.snapshot()["active"], first)
        self.write(package=PACKAGE + "\ndef inbox(store):\n    return {'value': VALUE}\n")
        runtime.poll(force=True)
        self.assertEqual(runtime.invoke("inbox", None), {"value": "first"})

    def test_readonly_consumer_never_builds_or_writes_runtime(self):
        runtime = self.runtime()
        first = runtime.snapshot()["active"]
        self.write("broken-call", PACKAGE.replace('return 200, {"value": VALUE}', 'raise RuntimeError("failure")'))
        runtime.poll(force=True)
        active = runtime.snapshot()["active"]
        def fingerprint():
            return {str(path.relative_to(self.artifacts)): (path.stat().st_mtime_ns, path.read_bytes())
                    for path in self.artifacts.rglob("*") if path.is_file()}
        before = fingerprint()
        self.write("unpublished-source")
        reader = BusinessRuntime(self.source, self.artifacts, read_only=True)
        self.runtimes.append(reader)
        self.assertEqual(reader.snapshot()["active"], active)
        self.assertIsNone(reader.worker)
        reader.poll(force=True)
        self.assertEqual(reader.snapshot()["active"], active)
        with self.assertRaises(StudioError):
            reader.invoke("route", None, "POST", "/", {}, {})
        self.assertEqual(reader.snapshot()["active"], first)
        reader.close()
        self.assertEqual(fingerprint(), before)
        self.assertEqual(runtime.snapshot()["active"], active)

    def test_no_healthy_module_clear_unavailable_and_source_separation(self):
        self.write(package="broken python !")
        runtime = self.runtime()
        with self.assertRaises(StudioError) as error:
            runtime.invoke("selected_context", None, {})
        self.assertEqual(error.exception.code, "business_unavailable")
        with self.assertRaises(ValueError):
            BusinessRuntime(self.source, self.source / "runtime")


if __name__ == "__main__":
    unittest.main()
