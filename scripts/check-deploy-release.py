#!/usr/bin/env python3
"""Failure injection against the actual deployment implementation, never a live server."""
import hashlib
import sys
sys.dont_write_bytecode = True
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import subprocess
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError


def load(name):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


release = load('deploy-release')
manifest_module = load('release-manifest')


class DeploymentTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.site = Path(self.tmp.name).resolve()
        self.previous = self.site / 'releases/20261001-000000'
        self.previous.mkdir(parents=True)
        (self.previous / 'index.html').write_text('GOOD OLD RELEASE')
        (self.site / 'current').symlink_to('releases/' + self.previous.name)
        # A newer failed upload must never be selected for rollback.
        (self.site / 'releases/20261006-000000').mkdir()
        self.id = '20261007-000000-123-1'
        self.new = self.site / 'releases' / self.id
        self.new.mkdir()
        files = {
            'index.html': '<script src="/app.js"></script><link rel="stylesheet" href="/site.css"><img src="/one.webp" srcset="/two.webp 640w">',
            'app.js': 'console.log(1)', 'site.css': 'body{}', 'one.webp': 'image1', 'two.webp': 'image2',
            'search/index.html': '<div data-index="/search-index.json"></div>',
            'search-index.json': '[]', 'index.xml': '<rss/>', 'sitemap.xml': '<urlset/>',
            'robots.txt': 'User-agent: *', '404.html': 'NOT FOUND',
            'blog/real/index.html': 'REAL ARTICLE'
        }
        for name, text in files.items():
            p = self.new / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text)
        self.manifest = manifest_module.create(self.new)
        self.count = self.manifest['html_count']

    def deploy(self, health=lambda *args: None):
        release.deploy(self.site, self.id, self.count, 'https://example.invalid', health)

    def assert_previous(self):
        self.assertEqual((self.site / 'current').resolve(), self.previous)

    def test_static_validator_rejects_missing_dependencies(self):
        checker = Path(__file__).with_name('check-static-output.py').resolve()
        for name in ('site.css', 'app.js', 'one.webp', 'two.webp', 'search-index.json'):
            file = self.new / name
            original = file.read_bytes()
            file.unlink()
            result = subprocess.run([sys.executable, str(checker), str(self.new)], cwd=self.site, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn(name, result.stderr)
            file.write_bytes(original)

    def test_success_and_probe_inventory(self):
        for url in ['/', '/blog/real/', '/app.js', '/site.css', '/two.webp', '/search-index.json', '/__12lab_missing_release_probe__/']:
            self.assertIn(url, self.manifest['probes'])
        self.deploy()
        self.assertEqual((self.site / 'current').resolve(), self.new)

    def test_corrupted_resource_stops_before_switch(self):
        (self.new / 'site.css').write_text('CORRUPT')
        with self.assertRaisesRegex(ValueError, 'Checksum'):
            self.deploy()
        self.assert_previous()

    def test_missing_file_stops_before_switch(self):
        (self.new / 'app.js').unlink()
        with self.assertRaisesRegex(ValueError, 'inventory'):
            self.deploy()
        self.assert_previous()

    def test_html_count_stops_before_switch(self):
        with self.assertRaisesRegex(ValueError, 'HTML count'):
            release.deploy(self.site, self.id, 999, '', lambda *a: None)
        self.assert_previous()

    def test_network_failure_retries_and_restores_exact_previous(self):
        def health(base, rid, data):
            release.probe_site(base, rid, data, attempts=3, delay=0)
        with patch.object(release, 'urlopen', side_effect=URLError('connection refused')) as request:
            with self.assertRaises(RuntimeError):
                self.deploy(health)
            self.assertEqual(request.call_count, 3)
            self.assertEqual(request.call_args.kwargs['timeout'], 8)
        self.assert_previous()

    def test_body_mismatch_restores_previous(self):
        response = io.BytesIO(b'WRONG VERSION')
        response.status = 200
        with patch.object(release, 'urlopen', return_value=response):
            with self.assertRaises(RuntimeError):
                self.deploy(lambda b, r, m: release.probe_site(b, r, m, attempts=1))
        self.assert_previous()

    def test_http_500_restores_previous(self):
        with patch.object(release, 'urlopen', side_effect=HTTPError('https://example.invalid', 500, 'failed', {}, io.BytesIO(b'bad'))):
            with self.assertRaises(RuntimeError):
                self.deploy(lambda b, r, m: release.probe_site(b, r, m, attempts=1))
        self.assert_previous()

    def test_expected_404_is_verified(self):
        data = {'files': {'404.html': hashlib.sha256(b'NOT FOUND').hexdigest()}, 'probes': {'/missing/': {'status': 404, 'file': '404.html'}}}
        with patch.object(release, 'urlopen', side_effect=HTTPError('https://example.invalid', 404, 'missing', {}, io.BytesIO(b'NOT FOUND'))):
            release.probe_site('https://example.invalid', self.id, data, attempts=1)

    def test_signal_restores_previous(self):
        with self.assertRaises(InterruptedError):
            self.deploy(lambda *a: release.interrupted(15, None))
        self.assert_previous()

    def test_regular_current_is_not_deleted(self):
        (self.site / 'current').unlink()
        (self.site / 'current').mkdir()
        with self.assertRaisesRegex(ValueError, 'symlink'):
            self.deploy()
        self.assertTrue((self.site / 'current').is_dir())


if __name__ == '__main__':
    unittest.main()
