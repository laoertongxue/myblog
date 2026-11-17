"""Verify reviewed P09/P10 simulation artifacts in isolated directories."""
from pathlib import Path
import hashlib,zipfile,tempfile,subprocess,sys,struct,shutil
R=Path(__file__).resolve().parents[1]
for n,slug in [('09','intermittent-demand'),('10','new-product-cold-start')]:
 E=R/f'experiments/p{n}-{slug}';P=R/f'content/topics/forecasting/{n}-{slug}'
 assert struct.unpack('>II',(P/'images/01-cover.png').read_bytes()[16:24])==(900,383)
 a=(P/'index.md').read_text();assert f'weight: {int(n)*10}' in a and 'monochromeImages: true' in a
 with tempfile.TemporaryDirectory() as tmp:
  d=Path(tmp)/'practice';shutil.copytree(E/'practice',d)
  subprocess.run([sys.executable,'run.py'],cwd=d,check=True)
  subprocess.run([sys.executable,'-m','unittest','-v'],cwd=d,check=True)
  for f in (E/'practice').rglob('*'):
   if f.is_file() and f.suffix in ['.json','.csv']:assert f.read_bytes()==(d/f.relative_to(E/'practice')).read_bytes(),f
 for kind in ['practice','article','images']:
  with zipfile.ZipFile(R/f'static/downloads/p{n}-{slug}-{kind}.zip') as z:
   assert z.testzip() is None
   for name in z.namelist():
    if name.endswith('/') or name.startswith('__MACOSX/'):continue
    rel=Path(name);cand=E/rel
    if kind=='practice' and cand.is_file():assert z.read(name)==cand.read_bytes(),name
    if name.endswith('.png'):
     pic=P/'images'/rel.name;assert z.read(name)==pic.read_bytes(),name
print('ok P09/P10: 38 tests, deterministic outputs, archives and cover metadata')
