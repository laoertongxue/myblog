"""P08 reproducibility and shipped-archive contract; no production actions."""
from pathlib import Path
import hashlib,zipfile,tempfile,subprocess,sys,struct
R=Path(__file__).resolve().parents[1];P=R/'content/topics/forecasting/08-hierarchical-reconciliation';E=R/'experiments/p08-hierarchical-reconciliation'
for name,root in [('complete',E),('practice',E/'practice')]:
 with zipfile.ZipFile(P/f'downloads/forecasting-08-{name}.zip') as z:
  assert z.testzip() is None
  manifest=z.read('MANIFEST.sha256').decode().splitlines()
  expected=set()
  for line in manifest:
   sha,member=line.split('  ',1);expected.add(member);b=z.read(member)
   assert hashlib.sha256(b).hexdigest()==sha,member
   assert b==(root/member).read_bytes(),member
  assert set(z.namelist())==expected|{'MANIFEST.sha256'}
with tempfile.TemporaryDirectory(prefix='p08-') as tmp:
 dest=Path(tmp)/'outputs'
 subprocess.run([sys.executable,str(E/'practice/run.py'),'--out',str(dest)],check=True)
 for f in (E/'practice/outputs').iterdir():
  if f.is_file():assert f.read_bytes()==(dest/f.name).read_bytes(),f.name
 subprocess.run([sys.executable,'-m','unittest','discover','-s',str(E/'practice'),'-v'],check=True)
assert struct.unpack('>II',(P/'images/00-cover.png').read_bytes()[16:24])==(900,383)
a=(P/'index.md').read_text();assert 'draft: false' in a and 'weight: 80' in a and '\n# ' not in a
assert a.count('regression-table-scroll')==1
with zipfile.ZipFile(P/'downloads/forecasting-08-reader.zip') as z:reader=z.read('第08篇_层级预测协调_图文阅读版.html').decode()
assert 'noindex, follow' in reader and 'rel="canonical"' in reader
print('ok P08: archive checksums, byte-identical rerun, 28 tests, cover and SEO')
