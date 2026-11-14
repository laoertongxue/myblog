#!/usr/bin/env python3
"""D21 exact-source archives, independent recomputation and article parity."""
from pathlib import Path
import json, hashlib, importlib.util, subprocess, sys, zipfile, tempfile, struct
from html.parser import HTMLParser
ROOT=Path(__file__).resolve().parents[1]
EXP=ROOT/'experiments/d21-routing-baseline';P=EXP/'practice'
ARTICLE=ROOT/'content/blog/shortest-path-routing-baseline'
def sha(b):return hashlib.sha256(b).hexdigest()
def require(c,m):
    if not c:raise ValueError(m)
class Tables(HTMLParser):
    def __init__(self):super().__init__();self.tables={};self.active=None;self.row=None;self.cell=None
    def handle_starttag(self,t,a):
        if t=='table':
            i=dict(a).get('id');self.active=i if i and i.startswith('d21-') else None
            if self.active:self.tables[self.active]=[]
        elif t=='tr' and self.active:self.row=[]
        elif t=='td' and self.row is not None:self.cell=''
    def handle_data(self,d):
        if self.cell is not None:self.cell+=d
    def handle_endtag(self,t):
        if t=='td' and self.cell is not None:self.row.append(self.cell.strip());self.cell=None
        elif t=='tr' and self.row is not None:
            if self.row:self.tables[self.active].append(self.row)
            self.row=None
        elif t=='table':self.active=None
spec=importlib.util.spec_from_file_location('pkg_d21',ROOT/'scripts/package-d21.py')
pkg=importlib.util.module_from_spec(spec);spec.loader.exec_module(pkg)
# No self-referential manifest: compare the checked-in file to source bytes.
require((P/'MANIFEST.sha256').read_bytes()==pkg.manifest(pkg.tree(P)), 'D21 practice manifest scope or hashes differ')
t=Tables();t.feed((ARTICLE/'index.md').read_text())
r=json.loads((P/'outputs/summary.json').read_text())
require([x['case_id'] for x in r]==['hewei_extension','apparel'],'D21 case inventory')
rows=[]
for x in r:
    a,b=x['routes']
    require(a['initial_load_box']==b['initial_load_box'] and a['capacity_box']==b['capacity_box'],'D21 unequal per-vehicle values require article format update')
    rows.append(['禾味十点扩展' if x['case_id']=='hewei_extension' else '匿名服装十点扩展',str(a['distance_m'])+'米',str(b['distance_m'])+'米',str(x['total_distance_m'])+'米',f"{a['initial_load_box']}箱／{a['capacity_box']}箱"])
require(t.tables.get('d21-baselines')==rows,'D21 article result cells differ')
for kind,items in pkg.expected().items():
    require(items,'D21 empty package '+kind)
    with zipfile.ZipFile(pkg.OUT/f'd21-routing-baseline-{kind}.zip') as z:
        names=z.namelist();require(len(names)==len(set(names)),'D21 duplicate ZIP entries')
        for n in names:pkg.safe(n)
        actual={n:z.read(n) for n in names}
        require(actual==pkg.members(items),'D21 ZIP source parity '+kind)
        require(z.testzip() is None,'D21 ZIP CRC')
        require(b'MANIFEST.sha256' not in actual['MANIFEST.sha256'],'D21 self-referential manifest')
        if kind=='practice':
            with tempfile.TemporaryDirectory(prefix='d21-reader-') as tmp:
                for n,b in actual.items():
                    p=Path(tmp)/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
                subprocess.run([sys.executable,'-B','-m','unittest','-v'],cwd=tmp,check=True)
                subprocess.run([sys.executable,'-B',str(Path(tmp)/'run.py')],cwd=ROOT,check=True)
                require(all((Path(tmp)/n).read_bytes()==b for n,b in actual.items()),'D21 reader rerun changed source/output bytes')
                require(set(pkg.tree(Path(tmp)))==set(items),'D21 reader produced unexpected files')
cover=ARTICLE/'images/d21-00_cover.png'
require(struct.unpack('>II',cover.read_bytes()[16:24])==(900,383),'D21 cover size')
a={p.name:p.read_bytes() for p in (ARTICLE/'images').glob('*.png')}
b={p.name:p.read_bytes() for p in (EXP/'images').glob('*.png')}
require(len(a)==4 and a==b,'D21 exact figure set and copy parity')
print('ok    D21 manifest, article result cells, exact three ZIPs, clean extraction/tests/reproduction, figure parity')
