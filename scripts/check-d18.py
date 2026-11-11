#!/usr/bin/env python3
"""Verify D18 frozen evidence, reader downloads and article tables; never refreeze."""
from pathlib import Path, PurePosixPath
from decimal import Decimal, ROUND_HALF_UP
from html.parser import HTMLParser
import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
import zipfile

ROOT=Path(__file__).resolve().parents[1]
EXP=ROOT/'experiments/d18-safety-stock'
PRACTICE=EXP/'practice'
ARTICLE=ROOT/'content/blog/safety-stock-service-level'
FIXED_CODE_RECEIPT_SHA256='65d82aade740022835bb9dd52e3db29eb31a79e4cdc31dcd0ae366f70b2d6932'


def require(condition,message):
    if not condition:raise ValueError(message)


def sha(data):return hashlib.sha256(data).hexdigest()


def source_tree(root,prefix=''):
    require(root.is_dir(),f'missing directory: {root}')
    return {prefix+p.relative_to(root).as_posix():p.read_bytes()
            for p in sorted(root.rglob('*')) if p.is_file()
            and '__pycache__' not in p.parts and p.suffix!='.pyc' and p.name!='.DS_Store'}


def safe_name(name):
    path=PurePosixPath(name)
    require(not path.is_absolute() and '..' not in path.parts and '\\' not in name,f'unsafe path: {name}')
    require(not any(part in ('sealed','__pycache__','.git','node_modules') for part in path.parts),f'forbidden path: {name}')
    require(path.suffix!='.pyc' and path.name!='.DS_Store',f'cache path: {name}')


def check_manifest(data,blobs):
    entries=[line.split('  ',1) for line in data.decode('utf-8').splitlines()]
    require(all(len(e)==2 for e in entries),'invalid manifest line')
    names=[name for _,name in entries]
    require(len(names)==len(set(names)),'duplicate manifest entries')
    require(set(names)==set(blobs)-{'MANIFEST.sha256'},'incomplete or surplus manifest coverage')
    for expected,name in entries:
        safe_name(name)
        require(sha(blobs[name])==expected,f'manifest hash mismatch: {name}')


def clean_replay(blobs):
    with tempfile.TemporaryDirectory(prefix='d18-reader-') as temp:
        p=Path(temp)
        for name,data in blobs.items():
            safe_name(name)
            path=p/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
        subprocess.run([sys.executable,'-B','-m','unittest','-v'],cwd=p,check=True)
        subprocess.run([sys.executable,'-B',str(p/'run.py')],cwd=ROOT,check=True)
        for name,data in blobs.items():
            require((p/name).read_bytes()==data,f'clean rerun changed {name}')


class ServiceTables(HTMLParser):
    def __init__(self):
        super().__init__();self.tables={};self.active=None;self.row=None;self.cell=None
    def handle_starttag(self,tag,attrs):
        if tag=='table':
            table_id=dict(attrs).get('id')
            if table_id in ('d18-hewei-service','d18-apparel-service'):
                require(table_id not in self.tables,'duplicate service table')
                self.active=table_id;self.tables[table_id]=[]
        elif tag=='tr' and self.active:self.row=[]
        elif tag=='td' and self.row is not None:self.cell=''
    def handle_data(self,data):
        if self.cell is not None:self.cell+=data
    def handle_endtag(self,tag):
        if tag=='td' and self.cell is not None:
            self.row.append(self.cell.strip());self.cell=None
        elif tag=='tr' and self.row is not None:
            if self.row:self.tables[self.active].append(self.row)
            self.row=None
        elif tag=='table':self.active=None


def check_tables():
    parser=ServiceTables();parser.feed((ARTICLE/'index.md').read_text(encoding='utf-8'))
    require(set(parser.tables)=={'d18-hewei-service','d18-apparel-service'},'missing article service tables')
    summary=json.loads((PRACTICE/'results/summary.json').read_text(encoding='utf-8'))
    for case in ('hewei','apparel'):
        expected=[]
        for z in ('0','1','1.645'):
            result=summary['strategies'][f'{case}-z{z}'];m=result['service_complete_cycles']
            cycle_pct=f"{100*m['no_stockout_cycles']//m['complete_cycles']}%"
            fill=(Decimal(str(m['total_served']))/Decimal(str(m['total_demand']))*100).quantize(Decimal('0.01'),rounding=ROUND_HALF_UP)
            expected.append([z,result['calculation']['target_level'],str(m['total_demand']),str(m['total_served']),str(m['total_lost_sales']),cycle_pct,f'{fill}%'])
        require(parser.tables[f'd18-{case}-service']==expected,f'{case}: article table differs cell-by-cell from replay')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--source-only',action='store_true');args=parser.parse_args()
    practice=source_tree(PRACTICE)
    check_manifest(practice['MANIFEST.sha256'],practice)
    require(sha(practice['code_receipt.json'])==FIXED_CODE_RECEIPT_SHA256,'release code receipt changed; explicit review required, do not auto-refresh')
    receipt=json.loads(practice['code_receipt.json'])
    require(set(receipt['files'])=={'run.py','inventory.py','test_safety_stock.py'},'code receipt coverage')
    for name,digest in receipt['files'].items():require(sha(practice[name])==digest,f'released code changed: {name}')
    check_tables()
    if args.source_only:
        clean_replay(practice)
        print('ok    D18 source integrity, clean replay, and both article service tables')
        return
    for kind in ('practice','article','images'):
        path=ROOT/f'static/downloads/d18-safety-stock-{kind}.zip'
        with zipfile.ZipFile(path) as archive:
            names=archive.namelist();require(len(names)==len(set(names)),'duplicate ZIP members')
            for name in names:safe_name(name)
            blobs={name:archive.read(name) for name in names}
        check_manifest(blobs['MANIFEST.sha256'],blobs)
        if kind=='practice':expected=practice
        elif kind=='article':expected=source_tree(ARTICLE)
        else:
            expected={}
            for folder in ('practice','figure-tools','images'):expected.update(source_tree(EXP/folder,folder+'/'))
            nested={name[len('practice/'):]:data for name,data in blobs.items() if name.startswith('practice/')}
            check_manifest(nested['MANIFEST.sha256'],nested)
        require(set(blobs)==set(expected)|{'MANIFEST.sha256'},f'{kind}: ZIP inventory differs from source')
        for name,data in expected.items():require(blobs[name]==data,f'{kind}: stale ZIP member {name}')
        if kind=='practice':clean_replay(blobs)
    print('ok    D18 frozen code, all ZIP manifests/source equality, clean reader tests/replay, article service tables')


if __name__=='__main__':main()
