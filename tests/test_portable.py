import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest

SOURCE = Path(__file__).resolve().parents[1]/'viktor-workflow-portable/source'
spec = importlib.util.spec_from_file_location('verifier', SOURCE/'verify_package.py')
verifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verifier)


class PortableTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)/'package'
        shutil.copytree(SOURCE, self.root)

    def tearDown(self):
        self.tmp.cleanup()

    def accept_hash(self, relative):
        p=self.root/'PACKAGE-MANIFEST.json'
        m=json.loads(p.read_text())
        m['sha256'][relative]=hashlib.sha256((self.root/relative).read_bytes()).hexdigest()
        p.write_text(json.dumps(m))

    def test_original(self):
        self.assertTrue(verifier.verify(self.root)['passed'])

    def test_tampered_file(self):
        (self.root/'README.md').write_text('changed')
        with self.assertRaisesRegex(ValueError, 'Hash mismatch'):
            verifier.verify(self.root)

    def test_unlisted_private_journal(self):
        (self.root/'journal.json').write_text('{}')
        with self.assertRaisesRegex(ValueError, 'Unlisted'):
            verifier.verify(self.root)

    def test_private_marker_even_with_refreshed_hash(self):
        (self.root/'README.md').write_text('owner@private.invalid')
        self.accept_hash('README.md')
        with self.assertRaisesRegex(ValueError, 'Private marker'):
            verifier.verify(self.root)

    def test_missing_license_even_with_changed_manifest(self):
        p=self.root/'PACKAGE-MANIFEST.json';m=json.loads(p.read_text())
        del m['sha256']['LICENSE'];p.write_text(json.dumps(m))
        (self.root/'LICENSE').unlink()
        with self.assertRaisesRegex(ValueError, 'license/provenance'):
            verifier.verify(self.root)

    def test_symlink(self):
        p=self.root/'README.md';p.unlink();p.symlink_to('/etc/hosts')
        with self.assertRaisesRegex(ValueError, 'symlink'):
            verifier.verify(self.root)

    def test_escaping_link_even_with_refreshed_hash(self):
        (self.root/'README.md').write_text('[bad](../private.md)')
        self.accept_hash('README.md')
        with self.assertRaisesRegex(ValueError, 'escaping link'):
            verifier.verify(self.root)


if __name__ == '__main__':
    unittest.main()
