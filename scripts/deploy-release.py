#!/usr/bin/env python3
"""Verify, atomically switch and probe a release; restore the exact previous link on failure."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import time
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


def verify(release, expected_pages):
    manifest = json.loads((release / 'release-manifest.json').read_text())
    if manifest.get('version') != 1:
        raise ValueError('Unsupported manifest version')
    actual = set()
    for p in release.rglob('*'):
        if p.is_symlink():
            raise ValueError(f'Symlink in release: {p}')
        if p.is_file() and p.relative_to(release).as_posix() != 'release-manifest.json':
            actual.add(p.relative_to(release).as_posix())
    if actual != set(manifest['files']):
        raise ValueError('Uploaded file inventory differs from manifest')
    for name, expected in manifest['files'].items():
        if hashlib.sha256((release / name).read_bytes()).hexdigest() != expected:
            raise ValueError(f'Checksum mismatch: {name}')
    count = sum(p.endswith('.html') for p in actual)
    if count != expected_pages:
        raise ValueError(f'HTML count mismatch: {count} != {expected_pages}')
    if not manifest.get('probes'):
        raise ValueError('No health probes')
    return manifest


def atomic_link(site, target):
    temporary = site / 'current.new'
    temporary.unlink(missing_ok=True)
    temporary.symlink_to(target)
    os.replace(temporary, site / 'current')


def probe_site(base_url, release_id, manifest, attempts=3, timeout=8, delay=2):
    last_error = None
    for attempt in range(attempts):
        try:
            for path, probe in manifest['probes'].items():
                url = base_url.rstrip('/') + quote(path, safe='/') + '?release=' + release_id
                request = Request(url, headers={'Cache-Control': 'no-cache', 'Accept-Encoding': 'identity'})
                try:
                    response = urlopen(request, timeout=timeout)
                except HTTPError as exc:
                    response = exc  # An expected 404 still has a body to validate.
                with response:
                    body = response.read()
                    if response.status != probe['status']:
                        raise ValueError(f'{path}: HTTP {response.status}, expected {probe["status"]}')
                    if hashlib.sha256(body).hexdigest() != manifest['files'][probe['file']]:
                        raise ValueError(f'{path}: served bytes differ from release')
            return
        except (OSError, URLError, ValueError) as exc:
            last_error = exc
            print(f'Health attempt {attempt + 1}/{attempts}: {exc}', flush=True)
            if attempt + 1 < attempts:
                time.sleep(delay)
    raise RuntimeError(f'Health checks failed: {last_error}')


def deploy(site, release_id, expected_pages, base_url, health=probe_site):
    site = Path(site).resolve()
    if not re.fullmatch(r'[0-9]{8}-[0-9]{6}-[0-9]+-[0-9]+', release_id):
        raise ValueError('Invalid release ID')
    release = site / 'releases' / release_id
    if release.is_symlink() or not release.is_dir():
        raise ValueError('Release must be a real directory')
    manifest = verify(release, expected_pages)
    current = site / 'current'
    if not current.is_symlink():
        raise ValueError('current must be an existing healthy symlink; refusing destructive migration')
    previous = os.readlink(current)
    previous_path = current.resolve(strict=True)
    if previous_path.parent != (site / 'releases').resolve() or not previous_path.is_dir():
        raise ValueError('Previous release is outside releases directory')
    if previous_path == release:
        raise ValueError('Refusing to redeploy current release')
    # Persist exact target before switching; never infer it from directory mtime.
    (site / 'previous-release.txt').write_text(previous + '\n')
    try:
        atomic_link(site, f'releases/{release_id}')
        health(base_url, release_id, manifest)
    except BaseException:
        atomic_link(site, previous)
        if current.resolve(strict=True) != previous_path:
            raise RuntimeError('Rollback verification failed')
        print(f'ROLLED BACK to {previous}', flush=True)
        raise
    (site / 'last-successful-release.txt').write_text(release_id + '\n')
    # Keep five releases including both current and its known-good predecessor.
    directories = sorted((p for p in (site / 'releases').iterdir() if p.is_dir() and not p.is_symlink() and re.fullmatch(r'[0-9]{8}-[0-9]{6}(?:-[0-9]+-[0-9]+)?', p.name)), key=lambda p: p.name, reverse=True)
    keep = {release, previous_path}
    for directory in directories:
        if len(keep) < 5:
            keep.add(directory)
    for directory in directories:
        if directory not in keep:
            try:
                shutil.rmtree(directory)
            except OSError as exc:
                print(f'WARNING: could not remove old release {directory.name}: {exc}', flush=True)
    print(f'Deployed {release_id}: {len(manifest["files"])} checksums and {len(manifest["probes"])} HTTP probes passed', flush=True)


def interrupted(signum, frame):
    raise InterruptedError(f'Received signal {signum}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--site-dir', required=True)
    parser.add_argument('--release', required=True)
    parser.add_argument('--expected-pages', type=int, required=True)
    parser.add_argument('--base-url', default='https://12lab.cn')
    args = parser.parse_args()
    signal.signal(signal.SIGTERM, interrupted)
    deploy(args.site_dir, args.release, args.expected_pages, args.base_url)
