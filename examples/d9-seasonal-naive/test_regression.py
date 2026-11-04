"""Fail-closed regression checks without opening original held-out labels."""
from contextlib import redirect_stdout
import hashlib
import io
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
import check_regression as regression
import run

SOURCE = Path(__file__).resolve().parent


class DailyRegressionTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        names = regression.DEVELOPMENT_FILES + (
            'freeze.json', 'results/test.json',
            'results/hewei-validation.json', 'results/apparel-validation.json',
        )
        for name in names:
            target = self.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(SOURCE / name, target)

    def verify(self):
        with redirect_stdout(io.StringIO()):
            regression.check(self.root)

    def test_passes_without_sealed_and_never_generates_or_finalizes(self):
        self.assertFalse((self.root / 'sealed').exists())
        original_open = Path.open
        original_score = run.score
        calls = []

        def guarded_open(path, *args, **kwargs):
            if 'sealed' in path.parts:
                raise AssertionError('sealed label access')
            return original_open(path, *args, **kwargs)

        def guarded_score(rows, start, end):
            self.assertEqual((len(rows), start, end), (140, 113, 140))
            calls.append((start, end))
            return original_score(rows, start, end)

        with patch.object(Path, 'open', guarded_open), \
             patch.object(run, 'generate', side_effect=AssertionError('full generation forbidden')), \
             patch.object(run, 'finalize', side_effect=AssertionError('test scoring forbidden')), \
             patch.object(run, 'score', guarded_score):
            self.verify()
        self.assertEqual(calls, [(113, 140), (113, 140)])

    def test_published_result_tampering_rejected_before_scoring(self):
        path = self.root / 'results/test.json'
        path.write_bytes(path.read_bytes() + b' ')
        with patch.object(run, 'score', side_effect=AssertionError('must fail before scoring')):
            with self.assertRaisesRegex(ValueError, 'integrity mismatch: test.json'):
                self.verify()

    def test_changed_receipt_rejected(self):
        path = self.root / 'freeze.json'
        path.write_bytes(path.read_bytes() + b' ')
        with self.assertRaisesRegex(ValueError, 'integrity mismatch: freeze.json'):
            self.verify()

    def test_changed_development_and_source_rejected(self):
        for name in ('baseline.py', 'data/hewei-development.csv'):
            path = self.root / name
            original = path.read_bytes()
            path.write_bytes(original + b'\n')
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, 'integrity mismatch'):
                self.verify()
            path.write_bytes(original)

    def test_validation_mismatch_rejected(self):
        path = self.root / 'results/apparel-validation.json'
        payload = json.loads(path.read_text(encoding='utf-8'))
        payload['mae'] += 1
        path.write_text(json.dumps(payload), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'apparel development validation regression'):
            self.verify()

    def test_missing_published_result_rejected(self):
        (self.root / 'results/test.json').unlink()
        with self.assertRaises(FileNotFoundError):
            self.verify()

    def test_checks_do_not_modify_any_input_or_result(self):
        def hashes():
            return {p.relative_to(self.root): hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in self.root.rglob('*') if p.is_file()}
        before = hashes()
        self.verify()
        self.assertEqual(hashes(), before)


if __name__ == '__main__':
    unittest.main()
