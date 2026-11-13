#!/usr/bin/env python3
"""D20 fixed-policy evidence, article parity and exact downloadable bundles."""
from pathlib import Path
import json, hashlib, importlib.util, subprocess, sys, zipfile, tempfile, struct
from html.parser import HTMLParser
ROOT=Path(__file__).resolve().parents[1];EXP=ROOT/'experiments/d20-inventory-test';P=EXP/'practice';ARTICLE=ROOT/'content/blog/inventory-test-stockout-tradeoff'
EXPECTED_MANIFEST_SHA256='48b5a73da7e8d037e34b033f2060394ed0ce33e346acd3072c7fc81ef8c8c8c4'
def sha(b):return hashlib.sha256(b).hexdigest()
def require(c,m):
    if not c:raise ValueError(m)
class Tables(HTMLParser):
    def __init__(self):super().__init__();self.tables={};self.active=None;self.row=None;self.cell=None
    def handle_starttag(self,t,a):
        if t=='table':
            i=dict(a).get('id');self.active=i if i and i.startswith('d20-') else None
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
spec=importlib.util.spec_from_file_location('pkg_d20',ROOT/'scripts/package-d20.py');pkg=importlib.util.module_from_spec(spec);spec.loader.exec_module(pkg)
require(sha((P/'manifest.json').read_bytes())==EXPECTED_MANIFEST_SHA256,'D20 reviewed manifest drift; investigate, never auto-refresh pin')
m=json.loads((P/'manifest.json').read_text());require(set(m)==set(pkg.tree(P))-{'manifest.json'},'D20 manifest scope')
for n,h in m.items():require(sha((P/n).read_bytes())==h,'D20 file drift '+n)
subprocess.run([sys.executable,'-B','-m','unittest','-v'],cwd=P,check=True)
subprocess.run([sys.executable,'-B',str(P/'run.py')],cwd=ROOT,check=True)
t=Tables();t.feed((ARTICLE/'index.md').read_text());r=json.loads((P/'output/results.json').read_text())
rows=[['禾味／公斤' if x['case']=='hewei' else '服装／件','每日' if x['policy']=='daily_sQ' else '周期',str(x['demand']),str(x['fulfilled']),str(x['lost']),f"{x['mean_end_oh']:.2f}",f"{100*x['fill_rate']:.2f}%",str(x['order_count'])] for x in r]
require(t.tables['d20-results']==rows,'D20 article result cells differ')
f=json.loads((P/'output/forecast_metrics.json').read_text());rows=[['禾味／公斤' if x['case']=='hewei' else '服装／件',str(x['horizon'])+'天',str(x['n']),f"{x['MAE']:.4f}",f"{x['ME']:.4f}"] for x in f]
require(t.tables['d20-forecast']==rows,'D20 forecast cells differ')
for kind,items in pkg.expected().items():
    with zipfile.ZipFile(pkg.OUT/f'd20-inventory-test-{kind}.zip') as z:
        names=z.namelist();require(len(names)==len(set(names)),'D20 duplicate ZIP entries')
        for n in names:pkg.safe(n)
        actual={n:z.read(n) for n in names};require(actual==pkg.members(items),'D20 ZIP source parity '+kind);require(z.testzip() is None,'D20 ZIP CRC')
        if kind=='practice':
            with tempfile.TemporaryDirectory(prefix='d20-reader-') as tmp:
                for n,b in actual.items():
                    p=Path(tmp)/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
                subprocess.run([sys.executable,'-B','-m','unittest','-v'],cwd=tmp,check=True)
                subprocess.run([sys.executable,'-B',str(Path(tmp)/'run.py')],cwd=ROOT,check=True)
                require(all((Path(tmp)/n).read_bytes()==b for n,b in actual.items()),'D20 reader mutated source')
cover=ARTICLE/'images/d20-00_cover.png';require(struct.unpack('>II',cover.read_bytes()[16:24])==(900,383),'D20 cover size')
for p in (ARTICLE/'images').glob('*.png'):require(p.read_bytes()==(EXP/'images'/p.name).read_bytes(),'D20 diagram copy drift')
print('ok    D20 pinned evidence, frozen tests, all article table cells, exact three ZIPs, clean extraction, figure parity')
