#!/usr/bin/env python3
"""Verify D17 reader deliverables without rewriting any tracked evidence."""
from pathlib import Path
import hashlib, json, subprocess, sys, tempfile, zipfile
ROOT=Path(__file__).resolve().parents[1]
EXP=ROOT/'experiments/d17-periodic-review'
ARTICLE=ROOT/'content/blog/periodic-review-order-up-to'
def digest(data):return hashlib.sha256(data).hexdigest()
def check_manifest(data, get, members):
    entries=[line.split('  ',1) for line in data.decode('utf-8').splitlines()]
    names=[name for _,name in entries]
    assert len(names)==len(set(names)), 'duplicate manifest entries'
    assert set(names)==set(members)-{'MANIFEST.sha256'}, 'incomplete or surplus manifest coverage'
    for expected,name in entries:
        assert digest(get(name))==expected, f'hash mismatch: {name}'
practice_files=[p.relative_to(EXP/'practice').as_posix() for p in (EXP/'practice').rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc']
check_manifest((EXP/'practice/MANIFEST.sha256').read_bytes(), lambda n:(EXP/'practice'/n).read_bytes(),practice_files)
for kind in ('practice','article','images'):
    path=ROOT/f'static/downloads/d17-periodic-review-{kind}.zip'
    with zipfile.ZipFile(path) as z:
        names=z.namelist()
        assert len(names)==len(set(names)), 'duplicate ZIP entries'
        assert all(not n.startswith('/') and '..' not in Path(n).parts for n in names), 'unsafe ZIP paths'
        assert not any('__pycache__' in n or n.endswith('.pyc') or '/sealed/' in '/'+n for n in names), 'unwanted ZIP contents'
        check_manifest(z.read('MANIFEST.sha256'),z.read,names)
        if kind=='practice':
            expected={p.relative_to(EXP/'practice').as_posix():p.read_bytes() for p in (EXP/'practice').rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc'}
        elif kind=='article':
            expected={p.relative_to(ARTICLE).as_posix():p.read_bytes() for p in ARTICLE.rglob('*') if p.is_file()}
        else:
            expected={f'{folder}/'+p.relative_to(EXP/folder).as_posix():p.read_bytes() for folder in ('practice','figure-tools','images') for p in (EXP/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc'}
        assert set(names)==set(expected)|{'MANIFEST.sha256'}, f'{kind}: archive inventory drift'
        for name,data in expected.items():assert z.read(name)==data, f'{kind}: stale {name}'
        if kind=='practice':
            with tempfile.TemporaryDirectory(prefix='d17-reader-') as temp:
                z.extractall(temp)
                subprocess.run([sys.executable,'-m','unittest','-v'],cwd=temp,check=True)
                subprocess.run([sys.executable,str(Path(temp)/'run.py')],cwd=ROOT,check=True)
                for name,data in expected.items():assert (Path(temp)/name).read_bytes()==data, f'rerun drift: {name}'
print('ok    D17 archive manifests, source equality, clean reader tests and deterministic replay')

# Article ledgers must agree cell-by-cell with the frozen replay, including
# the no-order calendar gate. This checks prose tables, not merely totals.
import csv
from html.parser import HTMLParser
class ArticleTables(HTMLParser):
    def __init__(self):
        super().__init__(); self.tables=[]; self.row=None; self.cell=None; self.table=None
    def handle_starttag(self,tag,attrs):
        if tag=='table': self.table=[]
        elif tag=='tr' and self.table is not None:self.row=[]
        elif tag=='td' and self.row is not None:self.cell=''
    def handle_data(self,data):
        if self.cell is not None:self.cell+=data
    def handle_endtag(self,tag):
        if tag=='td' and self.cell is not None:self.row.append(self.cell.strip());self.cell=None
        elif tag=='tr' and self.row is not None:
            if self.row:self.table.append(self.row)
            self.row=None
        elif tag=='table' and self.table is not None:self.tables.append(self.table);self.table=None
parser=ArticleTables();parser.feed((ARTICLE/'index.md').read_text())
assert len(parser.tables)==2,'D17 must have two Hewei ledgers'
for table,key in zip(parser.tables,('hewei-r2','hewei-r3')):
    rows=list(csv.DictReader((EXP/f'practice/results/{key}-ledger.csv').open()))
    expected=[]
    for row in rows:
        q=row['order_quantity']
        expected.append([row[k] for k in ('day','arrivals','demand','served','lost_sales','closing_on_hand','on_order_before_order','ip_before_order')]
          + ['是' if row['is_review_day']=='True' else '否',q,str(int(row['day'])+3) if q!='0' else '无'])
    assert table==expected,f'D17 article table differs from frozen {key} replay'
print('ok    D17 both article ledgers match all frozen row values and review gates')
