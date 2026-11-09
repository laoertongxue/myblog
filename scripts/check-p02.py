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
    'article.zip': '9ebb737af36354a7088f995ddf1d95646034e60701849f60bb69b0424324f9ee',
    'images.zip': '0ed9988550e258ab20351d4f1aa274f9475e24807b9d07153c3cd019a8008e8b',
    'practice.zip': '9e76dc5f3a897927a378464ee57bda46a232d2854d72d2b76097d14061ba2ff8',
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
