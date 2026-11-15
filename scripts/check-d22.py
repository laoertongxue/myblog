#!/usr/bin/env python3
"""D22 clean-reader tests, exact source archives and article results."""
from pathlib import Path
import importlib.util,json,subprocess,sys,tempfile,zipfile,struct
R=Path(__file__).resolve().parents[1];P=R/'experiments/d22-capacity-routing/practice';A=R/'content/blog/capacity-constrained-routing'
def require(v,m):
    if not v:raise ValueError(m)
spec=importlib.util.spec_from_file_location('pkg',R/'scripts/package-d22.py');pkg=importlib.util.module_from_spec(spec);spec.loader.exec_module(pkg)
for kind,items in pkg.expected().items():
    with zipfile.ZipFile(pkg.OUT/f'd22-capacity-routing-{kind}.zip') as z:
        require(len(z.namelist())==len(set(z.namelist())),'duplicate ZIP members')
        for n in z.namelist():pkg.safe(n)
        actual={n:z.read(n) for n in z.namelist()}
        require(actual==pkg.members(items),'D22 archive source mismatch '+kind)
        require(z.testzip() is None,'D22 CRC')
        if kind=='practice':
            with tempfile.TemporaryDirectory(prefix='d22-reader-') as td:
                for n,b in actual.items():
                    p=Path(td)/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
                subprocess.run([sys.executable,'-B','-m','unittest','-v'],cwd=td,check=True)
                subprocess.run([sys.executable,'-B',str(Path(td)/'run.py')],cwd=R,check=True)
                require(all((Path(td)/n).read_bytes()==b for n,b in actual.items()),'D22 reader changed evidence')
# Reuse established table parser only, without running D21 module side effects.
from html.parser import HTMLParser
class Table(HTMLParser):
    def __init__(self):super().__init__();self.active=False;self.rows=[];self.row=None;self.cell=None
    def handle_starttag(self,t,a):
        if t=='table':self.active=dict(a).get('id')=='d22-results'
        if t=='tr' and self.active:self.row=[]
        if t=='td' and self.row is not None:self.cell=''
    def handle_data(self,d):
        if self.cell is not None:self.cell+=d
    def handle_endtag(self,t):
        if t=='td' and self.cell is not None:self.row.append(self.cell.strip());self.cell=None
        if t=='tr' and self.row is not None:
            if self.row:self.rows.append(self.row)
            self.row=None
        if t=='table':self.active=False
p=Table();p.feed((A/'index.md').read_text());rows=[]
for x in json.loads((P/'outputs/comparison.json').read_text()):
    r=x['solver']['routes'];require(all(a['initial_load_box']==10 and a['capacity_box']==12 for a in r),'D22 table capacity changed')
    rows.append(['禾味十点扩展' if x['case_id']=='hewei_extension' else '匿名服装十点扩展',str(x['baseline']['total_distance_m'])+'米',str(x['solver']['total_distance_m'])+'米',str(x['difference_m'])+'米','10箱／12箱'])
require(p.rows==rows,'D22 article result parity')
require(struct.unpack('>II',(A/'images/d22-00_cover.png').read_bytes()[16:24])==(900,383),'D22 cover')
imgs=lambda p:{x.name:x.read_bytes() for x in p.glob('*.png')}
require(imgs(A/'images')==imgs(R/'experiments/d22-capacity-routing/images') and len(imgs(A/'images'))==4,'D22 figures')
print('ok    D22 exact archives, clean-reader tests/replay, result table and figures')
