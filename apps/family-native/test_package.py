"""The install contract that a working local ELF alone cannot prove."""
import importlib.util
from pathlib import Path
import tarfile
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('family_build', Path(__file__).with_name('build.py'))
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)


class Package(unittest.TestCase):
    def test_only_explicit_native_path_is_executable_and_archives_are_deterministic(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'stage'
            binary = source / 'usr/palm/applications/test.family/family-native'
            binary.parent.mkdir(parents=True)
            binary.write_bytes(b'ELF fixture')
            binary.chmod(0o644)  # Must work even when a transfer lost source execute bits.
            icon = binary.parent / 'icon.png'
            icon.write_bytes(b'image fixture')
            icon.chmod(0o777)  # Source metadata must not make an asset executable.
            relative = binary.relative_to(source).as_posix()
            one, two = root / 'one.tar.gz', root / 'two.tar.gz'
            build.write_archive(one, source, {relative})
            build.write_archive(two, source, {relative})
            self.assertEqual(one.read_bytes(), two.read_bytes())
            with tarfile.open(one) as archive:
                self.assertEqual(archive.getmember(relative).mode, 0o755)
                self.assertEqual(archive.getmember(icon.relative_to(source).as_posix()).mode, 0o644)
                self.assertEqual(archive.extractfile(relative).read(), b'ELF fixture')

    def test_staging_symlinks_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'stage'
            source.mkdir()
            (source / 'link').symlink_to('/etc/passwd')
            with self.assertRaises(ValueError):
                build.write_archive(root / 'bad.tar.gz', source)


if __name__ == '__main__':
    unittest.main()
