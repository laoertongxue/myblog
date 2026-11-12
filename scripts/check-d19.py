#!/usr/bin/env python3
"""Read-only D19 regression: pinned evidence, full CSV/table parity and reader ZIPs."""
from pathlib import Path
from html.parser import HTMLParser
import json, csv, hashlib, zipfile, tempfile, subprocess, sys, importlib.util, struct
ROOT=Path(__file__).resolve().parents[1]
EXP=ROOT/'experiments/d19-inventory-validation'; P=EXP/'practice'
ARTICLE=ROOT/'content/blog/inventory-validation-policy-freeze'
EXPECTED_MANIFEST_SHA256='32b11271604ef2042d38903114d089ba626022018a1ae55e4a0a2ebe3d20b2c6'
def sha(b):return hashlib.sha256(b).hexdigest()
def require(ok,msg):
    if not ok:raise ValueError(msg)
class Tables(HTMLParser):
    def __init__(self):super().__init__();self.tables={};self.active=None;self.row=None;self.cell=None
    def handle_starttag(self,tag,attrs):
        if tag=='table':
            i=dict(attrs).get('id'); self.active=i if i and i.startswith('d19-') else None
            if self.active:self.tables[self.active]=[]
        elif tag=='tr' and self.active:self.row=[]
        elif tag=='td' and self.row is not None:self.cell=''
    def handle_data(self,data):
        if self.cell is not None:self.cell+=data
    def handle_endtag(self,tag):
        if tag=='td' and self.cell is not None:self.row.append(self.cell.strip());self.cell=None
        elif tag=='tr' and self.row is not None:
            if self.row:self.tables[self.active].append(self.row)
            self.row=None
        elif tag=='table':self.active=None
spec=importlib.util.spec_from_file_location('package_d19',ROOT/'scripts/package-d19.py');pkg=importlib.util.module_from_spec(spec);spec.loader.exec_module(pkg)
require(sha((P/'manifest.json').read_bytes())==EXPECTED_MANIFEST_SHA256,'D19 reviewed manifest changed; inspect rather than refresh pin')
manifest=json.loads((P/'manifest.json').read_text())
require(set(manifest)==set(pkg.tree(P))-{'manifest.json'},'D19 manifest must cover every source/output file')
for n,h in manifest.items():require(sha((P/n).read_bytes())==h,'D19 manifest mismatch '+n)
subprocess.run([sys.executable,'-B','-m','unittest','-v'],cwd=P,check=True)
subprocess.run([sys.executable,'-B',str(P/'run.py')],cwd=ROOT,check=True)
t=Tables();t.feed((ARTICLE/'index.md').read_text())
results=json.loads((P/'output/results.json').read_text())
for case in ('hewei','apparel'):
    rows=[]
    for r in results:
        if r['case']!=case:continue
        a=r['parameters'];pol='日 / Q'+str(a['Q']) if a['policy']=='daily_sQ' else '周 / R3'
        rows.append([pol,str(a['z']),str(r['lost']),f"{r['mean_end_oh']:.2f}",str(r['order_count']),str(r['end_oh']),str(r['end_pipeline'])])
    require(t.tables['d19-'+case]==rows,'D19 article parameter table differs '+case)
manual=json.loads((P/'output/manual_seven_days.json').read_text())[0]['ledger']
fields=['day','opening_oh','arrivals','demand','fulfilled','lost','end_oh','ordered','pipeline_after']
require(t.tables['d19-manual']==[[str(r[f]) for f in fields] for r in manual],'D19 manual table differs')
for kind,items in pkg.expected().items():
    with zipfile.ZipFile(pkg.OUT/f'd19-inventory-validation-{kind}.zip') as z:
        names=z.namelist(); require(len(names)==len(set(names)),'duplicate ZIP names')
        for n in names:pkg.safe(n)
        actual={n:z.read(n) for n in names}
        require(actual==pkg.members(items),'D19 ZIP differs from current source '+kind)
        require(z.testzip() is None,'D19 corrupt ZIP')
        if kind=='practice':
            with tempfile.TemporaryDirectory(prefix='d19-reader-') as tmp:
                for n,b in actual.items():
                    p=Path(tmp)/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
                subprocess.run([sys.executable,'-B','-m','unittest','-v'],cwd=tmp,check=True)
                subprocess.run([sys.executable,'-B',str(Path(tmp)/'run.py')],cwd=ROOT,check=True)
                require(all((Path(tmp)/n).read_bytes()==b for n,b in actual.items()),'reader run mutated files')
cover=ARTICLE/'images/d19-00_cover.png'
require(struct.unpack('>II',cover.read_bytes()[16:24])==(900,383),'cover dimensions')
for p in (ARTICLE/'images').glob('*.png'):require(p.read_bytes()==(EXP/'images'/p.name).read_bytes(),'diagram copy differs')
print('ok    D19: pinned manifest, full replay, all article table cells, exact reader ZIPs, clean extraction, four diagram copies')
