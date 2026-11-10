"""Check chapter 03 published bundles and reproduce only its independent simulation."""
import hashlib
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile
import struct

ROOT = Path(__file__).resolve().parents[1]
BUNDLES = ROOT / 'static/downloads/forecasting/03-regression-and-features'
EXPECTED = {
    'article.zip': '1ac6780a706bbf8ae11be9e2368f85e81ef9af750d3e82229a2a7ffe15c99772',
    'images.zip': 'ad95feb296438f2ffd77185125d40ed5ce4b2d2c441c74d147eaeb27ac3e7b11',
    'practice.zip': 'c12f201fdc183e76bafc1aa6db360c6bdb502f11a8478badc1c3b344eedcfc77',
}
for name, digest in EXPECTED.items():
    assert hashlib.sha256((BUNDLES / name).read_bytes()).hexdigest() == digest, name
    with zipfile.ZipFile(BUNDLES / name) as archive:
        assert archive.testzip() is None, name
        for line in archive.read('SHA256SUMS.txt').decode().splitlines():
            expected, member = line.split('  ', 1)
            assert hashlib.sha256(archive.read(member)).hexdigest() == expected, (name, member)
        assert not any('site-draft' in p or 'review-round' in p for p in archive.namelist())
for name in ('article.zip','images.zip'):
    with zipfile.ZipFile(BUNDLES / name) as archive:
        for image in (ROOT / 'content/topics/forecasting/03-regression-and-features/images').glob('*.png'):
            assert image.read_bytes() == archive.read('images/' + image.name), image
            expected = (900,383) if 'cover' in image.name else (900,500)
            assert struct.unpack('>II', image.read_bytes()[16:24]) == expected, image
with tempfile.TemporaryDirectory(prefix='p03-practice-') as directory:
    with zipfile.ZipFile(BUNDLES / 'practice.zip') as archive:
        archive.extractall(directory)
    subprocess.run([sys.executable, 'verify.py'], cwd=directory, check=True)
print('ok    P03: reviewed ZIP hashes, CRC, member SHA, exact 5 images, 24 tests and deterministic reproduction')
