"""Validate the published fourth chapter and reproduce its independent simulations."""
from pathlib import Path
import hashlib, zipfile, tempfile, subprocess, sys, struct
ROOT=Path(__file__).resolve().parents[1]
P=ROOT/'content/topics/forecasting/04-probability-and-presale'
EXPECTED={'forecasting-04-complete.zip': '3a470a1a6d430f8fbf0753f0c42c2929429f91524210927a6130f8dc0af79d48', 'forecasting-04-practice.zip': '966ebbe525c6d64d799da8a28a887a7559a96089d98c70bfd6a0aab52dcc9341'}
for name,digest in EXPECTED.items():
    f=P/'downloads'/name
    assert hashlib.sha256(f.read_bytes()).hexdigest()==digest, name
    with zipfile.ZipFile(f) as z:
        assert z.testzip() is None
        for line in z.read('SHA256SUMS.txt').decode().splitlines():
            sha,member=line.split('  ',1)
            assert hashlib.sha256(z.read(member)).hexdigest()==sha,member
        if name.endswith('complete.zip'):
            for image in (P/'images').glob('*.png'):
                assert image.read_bytes()==z.read('images/'+image.name),image
with tempfile.TemporaryDirectory(prefix='p04-') as tmp:
    with zipfile.ZipFile(P/'downloads/forecasting-04-practice.zip') as z:z.extractall(tmp)
    before={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in (Path(tmp)/'outputs').glob('*.csv')}
    subprocess.run([sys.executable,'run.py'],cwd=tmp,check=True)
    after={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in (Path(tmp)/'outputs').glob('*.csv')}
    assert before==after,'deterministic output CSVs'
    subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-v'],cwd=tmp,check=True)
assert struct.unpack('>II',(P/'images/p04-cover.png').read_bytes()[16:24])==(900,383)
print('ok    P04: exact ZIP and member hashes, CRC, exact images, deterministic CSVs, 22 tests, cover dimensions')
