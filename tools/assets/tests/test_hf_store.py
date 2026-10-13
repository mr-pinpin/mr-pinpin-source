"""Offline storage contract tests; no credentials or network are needed."""
import contextlib
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import patch

MODULE = Path(__file__).resolve().parents[1] / "hf_store.py"
spec = importlib.util.spec_from_file_location("hf_store", MODULE)
store = importlib.util.module_from_spec(spec)
spec.loader.exec_module(store)


class FakeAPI:
    def __init__(self):
        self.objects = {}
        self.uploads = []
        self.downloads = []
        self.corrupt_download = False
        self.fail_upload = False
        self.batches = []

    def get_bucket_file_metadata(self, bucket, key):
        from huggingface_hub.errors import EntryNotFoundError
        if key not in self.objects:
            raise EntryNotFoundError("Missing fixture")
        fingerprint = hashlib.sha512(self.objects[key]).hexdigest()
        return SimpleNamespace(size=len(self.objects[key]), xet_file_data=SimpleNamespace(file_hash=fingerprint))

    def get_bucket_paths_info(self, bucket, paths):
        return [SimpleNamespace(type="file", path=key, size=len(self.objects[key]),
                                xet_hash=hashlib.sha512(self.objects[key]).hexdigest())
                for key in paths if key in self.objects]

    def batch_bucket_files(self, bucket, *, add):
        if self.fail_upload:
            raise RuntimeError("sensitive-provider-response-must-not-escape")
        self.batches.append(len(add))
        for source, key in add:
            self.objects[key] = Path(source).read_bytes()
            self.uploads.append(key)

    def download_bucket_files(self, bucket, files, *, raise_on_missing_files):
        assert raise_on_missing_files is True
        for key, target in files:
            if key not in self.objects:
                raise RuntimeError("sensitive-provider-response-must-not-escape")
            self.downloads.append(key)
            data = self.objects[key]
            if self.corrupt_download:
                data = bytes([data[0] ^ 1]) + data[1:]
            Path(target).write_bytes(data)


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.root, self.cache = self.base / "repo", self.base / "cache"
        self.root.mkdir()
        self.bucket = "miguelemosreverte/mr-pinpin-archive"
        self.data = b"PinPin offline content\n"
        self.entry = self.asset("docs/old/reference.png", self.data)
        self.api = FakeAPI()

    def asset(self, path, data, role="archive"):
        digest = hashlib.sha256(data).hexdigest()
        return {"path": path, "role": role, "bytes": len(data), "sha256": digest,
                "object": store.content_key(digest, Path(path).name)}

    def source(self, entry=None, data=None):
        entry = entry or self.entry
        path = self.root / entry["path"]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(self.data if data is None else data)
        return path

    def call(self, name, entries=None, **kwargs):
        return getattr(store, name)(entries or [self.entry], self.root, self.bucket,
                                    self.cache, api=self.api, **kwargs)

    def manifest(self, entries=None):
        path = self.base / "manifest.json"
        path.write_text(json.dumps({"version": 1, "bucket": self.bucket, "assets": entries or [self.entry]}))
        return path

    def test_round_trip_receipt_and_resume(self):
        original = self.source()
        receipt = self.call("upload_entries")
        self.assertTrue(receipt["verified"])
        self.assertTrue(receipt["entries"][0]["remote_verified"])
        self.assertEqual(self.api.downloads, [self.entry["object"]])
        self.assertEqual(original.read_bytes(), self.data)
        self.call("upload_entries")
        self.assertEqual(len(self.api.uploads), 1)
        self.assertEqual(len(self.api.downloads), 2)
        restored = self.base / "restored"
        restored.mkdir()
        result = store.materialize_entries([self.entry], restored, self.bucket, self.cache, api=self.api)
        self.assertEqual(result["entries"][0]["status"], "cache-restored")
        self.assertEqual((restored / self.entry["path"]).read_bytes(), self.data)
        self.assertEqual(len(self.api.downloads), 2)

    def test_push_preflights_every_source_before_upload(self):
        self.source()
        second = self.asset("docs/old/other.png", b"expected")
        self.source(second, b"wrong")
        with self.assertRaises(store.StorageError):
            self.call("upload_entries", [self.entry, second])
        self.assertEqual(self.api.uploads, [])

    def test_dry_run_has_no_remote_or_cache_writes(self):
        self.source()
        result = self.call("upload_entries", dry_run=True)
        self.assertFalse(result["verified"])
        self.assertFalse(result["entries"][0]["verified"])
        self.assertEqual(self.api.uploads + self.api.downloads, [])
        self.assertFalse(self.cache.exists())

    def test_fresh_remote_verify_ignores_valid_cache(self):
        self.source()
        self.call("upload_entries")
        self.api.objects[self.entry["object"]] = b"X" * len(self.data)
        with self.assertRaises(store.StorageError):
            self.call("verify_entries")
        self.assertEqual(len(self.api.downloads), 2)

    def test_existing_remote_conflict_is_not_overwritten(self):
        self.source()
        for data in [b"different-size", b"X" * len(self.data)]:
            with self.subTest(size=len(data)):
                self.api.objects[self.entry["object"]] = data
                with self.assertRaises(store.StorageError):
                    self.call("upload_entries")
                self.assertEqual(self.api.uploads, [])
                self.assertEqual(self.api.objects[self.entry["object"]], data)

    def test_redirect_head_length_does_not_override_stored_object_identity(self):
        self.source()
        self.api.objects[self.entry["object"]] = self.data
        with patch.object(self.api, "get_bucket_file_metadata", return_value=SimpleNamespace(size=1173)) as head:
            receipt = self.call("upload_entries")
        head.assert_not_called()
        self.assertTrue(receipt["entries"][0]["remote_verified"])
        self.assertEqual(self.api.downloads, [self.entry["object"]])
        self.api.corrupt_download = True
        with self.assertRaises(store.StorageError):
            self.call("verify_entries")

    def test_path_metadata_must_identify_exactly_one_file_with_xet_identity(self):
        valid = SimpleNamespace(type="file", path=self.entry["object"], size=len(self.data), xet_hash="identity")
        for records in [[valid, valid],
                        [SimpleNamespace(**{**vars(valid), "path": "another/object"})],
                        [SimpleNamespace(**{**vars(valid), "type": "directory"})],
                        [SimpleNamespace(**{**vars(valid), "xet_hash": None})]]:
            with self.subTest(records=records), patch.object(self.api, "get_bucket_paths_info", return_value=records):
                with self.assertRaises(store.StorageError):
                    self.call("verify_entries")
        self.assertEqual(self.api.downloads, [])

    def test_corrupt_download_never_appears_at_destination(self):
        self.api.objects[self.entry["object"]] = self.data
        self.api.corrupt_download = True
        with self.assertRaises(store.StorageError):
            self.call("materialize_entries")
        self.assertFalse((self.root / self.entry["path"]).exists())
        self.assertFalse((self.cache / self.entry["object"]).exists())
        self.assertEqual(list(self.base.rglob("*.part")), [])

    def test_missing_remote_cannot_publish_empty_asset(self):
        empty = self.asset("docs/empty.txt", b"")
        with self.assertRaises(store.StorageError):
            self.call("materialize_entries", [empty])
        self.assertFalse((self.root / empty["path"]).exists())

    def test_pull_downloads_and_then_skips_identical_destination(self):
        self.api.objects[self.entry["object"]] = self.data
        self.call("materialize_entries")
        self.call("materialize_entries")
        self.assertEqual(len(self.api.downloads), 1)
        self.assertEqual((self.root / self.entry["path"]).read_bytes(), self.data)

    def test_modified_local_file_is_preserved(self):
        original = self.source(data=b"local edit")
        with self.assertRaises(store.StorageError):
            self.call("materialize_entries")
        self.assertEqual(original.read_bytes(), b"local edit")
        self.assertEqual(self.api.downloads, [])

    def test_corrupt_cache_is_preserved_and_rejected(self):
        cached = self.cache / self.entry["object"]
        cached.parent.mkdir(parents=True)
        cached.write_bytes(b"corrupt cached content")
        with self.assertRaises(store.StorageError):
            self.call("materialize_entries")
        self.assertEqual(cached.read_bytes(), b"corrupt cached content")
        self.assertEqual(self.api.downloads, [])

    def test_invalid_paths_and_objects_are_rejected(self):
        for path in ["../escape", "/escape", "docs/../escape", "C:/escape", "docs\\escape", "docs//escape", "./escape", "docs/./escape", "docs/\x00escape", "docs/\x7fescape"]:
            with self.subTest(path=path), self.assertRaises(store.StorageError):
                store.validate_entries([{**self.entry, "path": path}])
        for fields in [{"object": "../escape"}, {"sha256": "0" * 64}, {"bytes": True}, {"role": []}]:
            with self.subTest(fields=fields), self.assertRaises(store.StorageError):
                store.validate_entries([{**self.entry, **fields}])
        with self.assertRaises(store.StorageError):
            store.validate_entries([self.entry, self.entry])

    def test_overlapping_manifest_paths_and_invalid_buckets_fail_before_writes(self):
        child = self.asset(self.entry["path"] + "/child.png", b"child")
        with self.assertRaisesRegex(store.StorageError, "overlap"):
            self.call("materialize_entries", [self.entry, child])
        for bucket in [None, "../bucket", "owner/../bucket", "owner/bucket/path", "owner/bucket?x", "owner/bucket\n", "owner/buck\u00e9t"]:
            with self.subTest(bucket=bucket), self.assertRaises(store.StorageError):
                store.validate_bucket(bucket)
        self.assertEqual(self.api.uploads + self.api.downloads, [])
        self.assertEqual(list(self.root.iterdir()), [])

    def test_source_and_destination_symlinks_rejected(self):
        outside = self.base / "outside"
        outside.mkdir()
        (outside / "reference.png").write_bytes(self.data)
        (self.root / "docs").symlink_to(outside, target_is_directory=True)
        for operation in ["upload_entries", "materialize_entries"]:
            with self.subTest(operation=operation), self.assertRaises(store.StorageError):
                self.call(operation)
        self.assertEqual(list(outside.iterdir()), [outside / "reference.png"])

    def test_final_dangling_symlink_and_cache_symlink_rejected(self):
        target = self.root / self.entry["path"]
        target.parent.mkdir(parents=True)
        target.symlink_to(self.base / "missing")
        with self.assertRaises(store.StorageError):
            self.call("materialize_entries")
        with self.assertRaises(store.StorageError):
            self.call("upload_entries")
        target.unlink()  # Test fixture cleanup only; the adapter never removes assets.
        self.cache.mkdir()
        (self.cache / "sha256").symlink_to(self.base / "missing-cache")
        with self.assertRaises(store.StorageError):
            self.call("materialize_entries")

    def test_explicit_push_source_symlink_opt_in(self):
        outside = self.base / "external-source"
        outside.write_bytes(self.data)
        source = self.root / self.entry["path"]
        source.parent.mkdir(parents=True)
        source.symlink_to(outside)
        with self.assertRaises(store.StorageError):
            self.call("upload_entries")
        receipt = self.call("upload_entries", allow_source_symlinks=True)
        self.assertTrue(receipt["verified"])
        self.assertTrue(source.is_symlink())
        self.assertEqual(outside.read_bytes(), self.data)
        with self.assertRaises(store.StorageError):
            self.call("materialize_entries")
        outside.write_bytes(b"modified")
        with self.assertRaises(store.StorageError):
            self.call("upload_entries", allow_source_symlinks=True)

    def test_receipt_resume_binds_bucket_path_hash_and_remote_identity(self):
        self.source()
        receipt = self.call("upload_entries")
        resumed = self.call("upload_entries", resume_receipt=receipt)
        self.assertEqual(resumed["entries"][0]["status"], "receipt-resumed")
        self.assertEqual(len(self.api.downloads), 1)
        for invalid in [{**receipt, "bucket": "other/bucket"},
                        {**receipt, "version": True}, {**receipt, "version": None},
                        {**receipt, "action": "pull"}, {**receipt, "action": None},
                        {**receipt, "dry_run": True}, {**receipt, "dry_run": None},
                        {**receipt, "entries": [{**receipt["entries"][0], "remote_verified": None}]},
                        {**receipt, "entries": [{**receipt["entries"][0], "object": "other/object"}]},
                        {**receipt, "entries": [{**receipt["entries"][0], "path": "other/path"}]},
                        {**receipt, "entries": [{**receipt["entries"][0], "sha256": "0" * 64}]}]:
            previous = len(self.api.downloads)
            self.call("upload_entries", resume_receipt=invalid)
            self.assertEqual(len(self.api.downloads), previous + 1)
        self.api.objects[self.entry["object"]] = b"X" * len(self.data)
        with self.assertRaises(store.StorageError):
            self.call("upload_entries", resume_receipt=receipt)
        self.assertEqual(len(self.api.uploads), 1)

    def test_batch_upload_and_bounded_parallel_verification(self):
        entries = [self.asset(f"docs/{i}.bin", str(i).encode()) for i in range(4)]
        for i, entry in enumerate(entries):
            self.source(entry, str(i).encode())
        barrier = threading.Barrier(4)
        download = self.api.download_bucket_files

        def synchronized_download(*args, **kwargs):
            barrier.wait(timeout=5)
            return download(*args, **kwargs)

        with patch.object(self.api, "download_bucket_files", side_effect=synchronized_download):
            receipt = self.call("upload_entries", entries, workers=4)
        self.assertEqual(self.api.batches, [4])
        self.assertEqual([e["path"] for e in receipt["entries"]], [e["path"] for e in entries])
        self.assertTrue(receipt["verified"])

    def test_private_quota_error_is_actionable_without_provider_details(self):
        self.source()
        error = RuntimeError("Private bucket storage quota exceeded: sensitive-provider-response")
        error.response = SimpleNamespace(status_code=403)
        with patch.object(self.api, "batch_bucket_files", side_effect=error):
            with self.assertRaisesRegex(store.StorageError, "private bucket storage quota exceeded") as caught:
                self.call("upload_entries")
        self.assertIn("HTTP 403", str(caught.exception))
        self.assertNotIn("sensitive-provider-response", str(caught.exception))

    def test_cache_must_be_external(self):
        with self.assertRaises(store.StorageError):
            store.cache_root(self.root, self.root / ".cache")
        with patch.dict(os.environ, {"PINPIN_ASSET_CACHE": str(self.cache)}):
            self.assertEqual(store.cache_root(self.root, None), self.cache.resolve())

    def test_atomic_placement_preserves_concurrent_file(self):
        target = self.source(data=b"concurrent edit")
        temporary = self.base / "prepared"
        temporary.write_bytes(self.data)
        with self.assertRaises(store.StorageError):
            store.atomic_place(temporary, target, self.entry["bytes"], self.entry["sha256"])
        self.assertEqual(target.read_bytes(), b"concurrent edit")

    def test_production_never_transfers(self):
        production = {**self.entry, "role": "production"}
        self.source(production)
        for operation in ["upload_entries", "materialize_entries", "verify_entries"]:
            self.call(operation, [production])
        self.assertEqual(self.api.uploads + self.api.downloads, [])
        self.assertEqual(store.load_manifest(self.manifest([production]))[1], [])
        self.assertEqual(store.load_manifest(self.manifest([production]), "all")[1], [production])

    def test_cli_receipt_only_after_full_remote_verification(self):
        self.source()
        manifest, receipt = self.manifest(), self.base / "receipt.json"
        arguments = ["push", "--manifest", str(manifest), "--root", str(self.root),
                     "--cache", str(self.cache), "--profile", "archive", "--receipt", str(receipt)]
        output = io.StringIO()
        with patch.object(store, "_client", return_value=self.api), contextlib.redirect_stdout(output):
            self.assertEqual(store.main(arguments + ["--dry-run"]), 0)
            self.assertFalse(receipt.exists())
            self.assertEqual(store.main(arguments), 0)
        proof = json.loads(receipt.read_text())
        self.assertEqual(proof["bucket"], self.bucket)
        self.assertTrue(proof["entries"][0]["verified"])
        self.assertEqual(proof["entries"][0]["sha256"], self.entry["sha256"])
        self.assertTrue(proof["entries"][0]["remote_verified"])

    def test_push_symlink_option_cannot_enable_pull_destination_writes(self):
        outside = self.base / "outside"
        outside.mkdir()
        (self.root / "docs").symlink_to(outside, target_is_directory=True)
        args = ["pull", "--manifest", str(self.manifest()), "--root", str(self.root),
                "--cache", str(self.cache), "--allow-source-symlinks"]
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as caught:
            store.main(args)
        self.assertEqual(caught.exception.code, 2)
        self.assertEqual(list(outside.iterdir()), [])

    def test_failed_upload_or_remote_verify_cannot_write_receipt(self):
        self.source()
        receipt = self.base / "receipt.json"
        args = ["push", "--manifest", str(self.manifest()), "--root", str(self.root),
                "--cache", str(self.cache), "--receipt", str(receipt)]
        self.api.fail_upload = True
        errors = io.StringIO()
        with patch.object(store, "_client", return_value=self.api), contextlib.redirect_stderr(errors):
            self.assertEqual(store.main(args), 1)
        self.assertNotIn("sensitive-provider-response", errors.getvalue())
        self.assertFalse(receipt.exists())
        self.api.fail_upload, self.api.corrupt_download = False, True
        with patch.object(store, "_client", return_value=self.api), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(store.main(args), 1)
        self.assertFalse(receipt.exists())

    def test_sync_cli_uses_real_adapter_receipts_and_preserves_files_on_failure(self):
        for outcome in ("success", "corrupt", "upload-failed"):
            with self.subTest(outcome=outcome):
                base = self.base / outcome
                root, cache = base / "repo", base / "cache"
                root.mkdir(parents=True)
                docs = root / "docs"
                docs.mkdir()
                (docs / "archive.png").write_bytes(self.data)
                (docs / "production.webp").write_bytes(b"production")
                outside = base / "managed-source"
                outside.mkdir()
                (outside / "frame.png").write_bytes(b"frame")
                (docs / "renders").symlink_to(outside, target_is_directory=True)
                (root / ".gitignore").write_text("# user rules\n.env\n")
                (root / "assets").mkdir()
                policy = {"version": 1, "bucket": self.bucket, "roots": ["docs"],
                          "extensions": [".png", ".webp"], "production": ["docs/production.webp"],
                          "archive": ["docs/archive.png", "docs/renders/frame.png"],
                          "managedSymlinks": ["docs/renders"]}
                (root / "assets/policy.json").write_text(json.dumps(policy))
                driver = base / "offline-python"
                driver.write_text(
                    f"#!{sys.executable}\nimport sys\n"
                    f"sys.path.insert(0, {str(Path(__file__).resolve().parent)!r})\n"
                    "from test_hf_store import store, FakeAPI\napi = FakeAPI()\n"
                    f"api.corrupt_download = {outcome == 'corrupt'!r}\n"
                    f"api.fail_upload = {outcome == 'upload-failed'!r}\n"
                    "store._client = lambda unused: api\n"
                    "raise SystemExit(store.main(sys.argv[2:]))\n")
                driver.chmod(0o700)
                env = {**os.environ, "PINPIN_PYTHON": str(driver), "HF_HUB_OFFLINE": "1",
                       "PYTHONDONTWRITEBYTECODE": "1", "GIT_CONFIG_NOSYSTEM": "1",
                       "GIT_CONFIG_GLOBAL": os.devnull, "GIT_TEMPLATE_DIR": ""}

                def git(*args):
                    return subprocess.check_output(["git", "-C", str(root), *args], env=env)

                git("init", "-q")
                git("add", "--", "docs", ".gitignore")
                index_before = (root / ".git/index").read_bytes()
                ignore_before = (root / ".gitignore").read_bytes()
                result = subprocess.run(
                    ["node", str(MODULE.parent / "sync.cjs"), "--root", str(root), "--cache", str(cache)],
                    env=env, capture_output=True, text=True, timeout=30)
                receipts = list(cache.glob("sync-receipt-*.json"))
                if outcome == "success":
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertEqual(len(receipts), 1)
                    receipt = json.loads(receipts[0].read_text())
                    self.assertEqual(receipt["action"], "push")
                    self.assertTrue(receipt["verified"])
                    self.assertEqual(len(receipt["entries"]), 2)
                    self.assertTrue(all(e["remote_verified"] for e in receipt["entries"]))
                    self.assertEqual(git("ls-files", "--", "docs").decode().splitlines(), ["docs/production.webp"])
                    self.assertIn("/docs/renders\n", (root / ".gitignore").read_text())
                else:
                    self.assertNotEqual(result.returncode, 0)
                    self.assertEqual(receipts, [])
                    self.assertEqual((root / ".git/index").read_bytes(), index_before)
                    self.assertEqual((root / ".gitignore").read_bytes(), ignore_before)
                self.assertEqual((docs / "archive.png").read_bytes(), self.data)
                self.assertEqual((docs / "production.webp").read_bytes(), b"production")
                self.assertEqual((outside / "frame.png").read_bytes(), b"frame")
                self.assertTrue((docs / "renders").is_symlink())
    def test_explicit_public_http_readback_verifies_anonymous_bytes(self):
        self.source()
        with patch.object(store, "urlopen", return_value=io.BytesIO(self.data)) as request:
            receipt = self.call("upload_entries", public_http_readback=True)
        self.assertTrue(receipt["verified"])
        self.assertTrue(receipt["entries"][0]["remote_verified"])
        self.assertEqual(self.api.downloads, [])
        url = request.call_args.args[0]
        self.assertEqual(url, "https://huggingface.co/buckets/" + self.bucket + "/resolve/" + self.entry["object"])
        self.assertEqual(request.call_args.kwargs, {"timeout": 60})
        self.assertEqual((self.root / self.entry["path"]).read_bytes(), self.data)

    def test_public_readback_rejects_corruption_and_oversized_response(self):
        self.source()
        for payload in [bytes([self.data[0] ^ 1]) + self.data[1:], self.data + b"extra"]:
            with self.subTest(payload=payload), patch.object(store, "urlopen", return_value=io.BytesIO(payload)):
                with self.assertRaises(store.StorageError):
                    self.call("upload_entries", public_http_readback=True)
        self.assertEqual((self.root / self.entry["path"]).read_bytes(), self.data)

    def test_public_readback_is_not_enabled_for_arbitrary_buckets(self):
        self.source()
        with patch.object(store, "urlopen") as request:
            with self.assertRaisesRegex(store.StorageError, "restricted"):
                store.upload_entries([self.entry], self.root, "another/private", self.cache,
                                     api=self.api, public_http_readback=True)
        request.assert_not_called()
        self.assertEqual(self.api.uploads, [])

if __name__ == "__main__":
    unittest.main()
