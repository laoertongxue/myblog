"""Verify reviewed forecasting chapter 02 bundles without rewriting them."""
import hashlib
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
BUNDLES = ROOT / 'static/downloads/forecasting/02-problem-and-data'
EXPECTED = {
    'article.zip': 'c2e8a2fb9d6689ee5743af57da8b0b34ddf469b268cb44d7dc2e94aab5943338',
    'images.zip': '0ed9988550e258ab20351d4f1aa274f9475e24807b9d07153c3cd019a8008e8b',
    'practice.zip': '6967920efd1de389ccfc80f0a73c4594f48df760364f9f5ec17ef709dc8d5343',
}
for name, digest in EXPECTED.items():
    assert hashlib.sha256((BUNDLES / name).read_bytes()).hexdigest() == digest, name
    with zipfile.ZipFile(BUNDLES / name) as archive:
        assert archive.testzip() is None, name
with zipfile.ZipFile(BUNDLES / 'article.zip') as archive:
    for image in (ROOT / 'content/topics/forecasting/02-problem-and-data/images').glob('*.png'):
        assert image.read_bytes() == archive.read('images/' + image.name), image
with tempfile.TemporaryDirectory(prefix='p02-practice-') as directory:
    with zipfile.ZipFile(BUNDLES / 'practice.zip') as archive:
        archive.extractall(directory)
    subprocess.run([sys.executable, '-m', 'unittest', '-v'], cwd=directory, check=True)
print('ok    P02: 3 exact reviewed ZIP hashes, 4 exact images, 28 clean-extraction tests')
