import hashlib
import importlib.metadata
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SENDER = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SENDER))
import offline_check

class ArtifactChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scratch = SENDER / '.local/test-tmp'
        cls.scratch.mkdir(parents=True, exist_ok=True)

    def fixture(self, root):
        model = root / 'models/tiny.en'
        model.mkdir(parents=True)
        entries = []
        for name in ('config.json', 'model.bin', 'tokenizer.json', 'vocabulary.txt'):
            path = model / name
            path.write_bytes(b'fixture-' + name.encode())
            entries.append({'local_path': path.relative_to(root).as_posix(), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
        (root / 'artifacts.json').write_text(json.dumps({'artifacts': entries}))
        return model

    def test_complete_local_artifacts_accepted(self):
        with tempfile.TemporaryDirectory(dir=self.scratch) as temp:
            root = Path(temp)
            model = self.fixture(root)
            with patch.object(offline_check, 'SENDER', root):
                self.assertEqual(offline_check.verify_model_files(model), model.resolve())

    def test_missing_tokenizer_fails_instead_of_download(self):
        with tempfile.TemporaryDirectory(dir=self.scratch) as temp:
            root = Path(temp)
            model = self.fixture(root)
            (model / 'tokenizer.json').unlink()
            with patch.object(offline_check, 'SENDER', root), self.assertRaisesRegex(ValueError, 'Missing local artifact'):
                offline_check.verify_model_files(model)

    def test_corrupted_weights_fail_before_inference(self):
        with tempfile.TemporaryDirectory(dir=self.scratch) as temp:
            root = Path(temp)
            model = self.fixture(root)
            (model / 'model.bin').write_bytes(b'corrupted')
            with patch.object(offline_check, 'SENDER', root), self.assertRaisesRegex(ValueError, 'hash mismatch'):
                offline_check.verify_model_files(model)

    def test_remote_model_identifier_is_not_accepted(self):
        with self.assertRaisesRegex(ValueError, 'existing sender-local'):
            offline_check.verify_model_files(SENDER / 'not-a-downloaded-model')

    def test_installed_packages_match_prepared_provenance(self):
        metadata = json.loads((SENDER / 'dependencies.json').read_text())
        for package in metadata['packages']:
            with self.subTest(package=package['name']):
                self.assertEqual(importlib.metadata.version(package['name']), package['version'])

if __name__ == '__main__':
    unittest.main()
