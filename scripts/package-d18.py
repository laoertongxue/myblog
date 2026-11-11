#!/usr/bin/env python3
"""Build deterministic D18 downloads; verify ZIP bytes and replay clean practice."""
from pathlib import Path, PurePosixPath
import hashlib
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / 'experiments/d18-safety-stock'
ARTICLE = ROOT / 'content/blog/safety-stock-service-level'
OUT = ROOT / 'static/downloads'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def files(root):
    if not root.is_dir():
        raise ValueError(f'missing directory: {root}')
    return [p for p in sorted(root.rglob('*')) if p.is_file()
            and '__pycache__' not in p.parts and p.suffix != '.pyc'
            and p.name != '.DS_Store']


def tree(root, prefix=''):
    return [(prefix + p.relative_to(root).as_posix(), p.read_bytes()) for p in files(root)]


def manifest_bytes(items):
    return ''.join(f'{sha(data)}  {name}\n' for name, data in sorted(items)).encode('utf-8')


def with_manifest(items):
    if any(name == 'MANIFEST.sha256' for name, _ in items):
        raise ValueError('root manifest must not include itself')
    return items + [('MANIFEST.sha256', manifest_bytes(items))]


def safe_name(name):
    path = PurePosixPath(name)
    if path.is_absolute() or '..' in path.parts or '\\' in name:
        raise ValueError(f'unsafe archive path: {name}')
    if any(part in ('sealed', '__pycache__', '.git', 'node_modules') for part in path.parts):
        raise ValueError(f'forbidden archive path: {name}')
    if path.suffix == '.pyc' or path.name == '.DS_Store':
        raise ValueError(f'cache in archive: {name}')


def verify_archive(path):
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        if len(names) != len(set(names)):
            raise ValueError('duplicate ZIP members')
        for name in names:
            safe_name(name)
        blobs = {name: z.read(name) for name in names}
        if blobs.get('MANIFEST.sha256') != manifest_bytes([(n, b) for n, b in blobs.items() if n != 'MANIFEST.sha256']):
            raise ValueError(f'ZIP manifest differs byte-for-byte: {path}')
        if 'practice/MANIFEST.sha256' in blobs:
            nested = [(n[len('practice/'):], b) for n, b in blobs.items()
                      if n.startswith('practice/') and n != 'practice/MANIFEST.sha256']
            if blobs['practice/MANIFEST.sha256'] != manifest_bytes(nested):
                raise ValueError('embedded practice manifest mismatch')
        return blobs


def archive(name, items):
    path = OUT / name
    with zipfile.ZipFile(path, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for label, data in sorted(items):
            safe_name(label)
            info = zipfile.ZipInfo(label, date_time=(2026, 11, 11, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            z.writestr(info, data)
    verify_archive(path)
    return path


def verify_clean_practice(path):
    original = verify_archive(path)
    with tempfile.TemporaryDirectory(prefix='d18-clean-practice-') as directory:
        root = Path(directory)
        with zipfile.ZipFile(path) as z:
            z.extractall(root)  # All member names were validated above.
        subprocess.run([sys.executable, '-B', '-m', 'unittest', '-v'], cwd=root, check=True)
        subprocess.run([sys.executable, '-B', str(root/'run.py')], cwd=root, check=True)
        for name, data in original.items():
            if (root/name).read_bytes() != data:
                raise ValueError(f'clean replay changed packaged bytes: {name}')
        print('Clean extracted practice: tests pass; rerun output byte-identical.')


def main():
    # Only run once the reviewed article and portable figures are ready.
    if not (ARTICLE/'index.md').is_file() or not (EXP/'figure-tools/render_figures.py').is_file():
        raise ValueError('article/renderer not ready')
    if not list((ARTICLE/'images').glob('*.png')):
        raise ValueError('article figures not ready')
    practice = EXP/'practice'
    items = [(n, b) for n, b in tree(practice) if n != 'MANIFEST.sha256']
    (practice/'MANIFEST.sha256').write_bytes(manifest_bytes(items))
    OUT.mkdir(parents=True, exist_ok=True)
    paths = [archive('d18-safety-stock-practice.zip', tree(practice)),
             archive('d18-safety-stock-article.zip', with_manifest(tree(ARTICLE))),
             archive('d18-safety-stock-images.zip', with_manifest(
                 tree(practice, 'practice/') + tree(EXP/'figure-tools', 'figure-tools/')
                 + tree(EXP/'images', 'images/')))]
    verify_clean_practice(paths[0])
    for path in paths:
        print(sha(path.read_bytes()), path.name, path.stat().st_size)


if __name__ == '__main__':
    main()
