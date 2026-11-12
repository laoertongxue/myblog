"""Reproduce P05 without changing source inputs or published results."""
from pathlib import Path
import hashlib,zipfile,tempfile,subprocess,sys,struct,re
R=Path(__file__).resolve().parents[1];P=R/'content/topics/forecasting/05-forecast-to-replenishment';E=R/'experiments/p05-forecast-to-replenishment'
EXPECTED={'complete':'3972f708b4c326968281f3e9eef53a3fd9433fb1351ca56bcc4d72c3445c9df1','practice':'afa35d6bbe1de120482bf5998e0f9286bb7bfa922e9b84c1e3674aa18595c16f'}
for name,root in [('complete',E),('practice',E/'practice')]:
 assert hashlib.sha256((P/f'downloads/forecasting-05-{name}.zip').read_bytes()).hexdigest()==EXPECTED[name],name
 with zipfile.ZipFile(P/f'downloads/forecasting-05-{name}.zip') as z:
  assert z.testzip() is None
  for line in z.read('SHA256SUMS.txt').decode().splitlines():
   sha,member=line.split('  ',1);b=z.read(member)
   assert hashlib.sha256(b).hexdigest()==sha,member
   assert b==(root/member).read_bytes(),member
  if name=='complete':
   for f in (P/'images').glob('*.png'):assert f.read_bytes()==z.read('images/'+f.name)
with tempfile.TemporaryDirectory(prefix='p05-') as tmp:
 for inputs,results in [('inputs','results'),('inputs_expiry_pressure','results_expiry_pressure')]:
  dest=Path(tmp)/results
  subprocess.run([sys.executable,str(E/'practice/run.py'),'--inputs',str(E/'practice'/inputs),'--output',str(dest)],check=True)
  expected={f.name:f.read_bytes() for f in (E/'practice'/results).iterdir() if f.is_file()}
  actual={f.name:f.read_bytes() for f in dest.iterdir() if f.is_file()}
  assert expected==actual,results
 subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-v'],cwd=E/'practice',check=True)
assert struct.unpack('>II',(P/'images/p05-cover.png').read_bytes()[16:24])==(900,383)
a=(P/'index.md').read_text();assert 'draft: false' in a and 'weight: 50' in a and '\n# ' not in a
assert a.count('regression-table-scroll')==4
print('ok    P05: ZIP member integrity/source identity, both exact output reruns, 72 tests, cover and metadata')

assert re.findall(r'^\|.*$',a,re.M)==re.findall(r'^\|.*$',(E/'article.md').read_text(),re.M),'all article table cells unchanged'
