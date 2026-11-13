#!/usr/bin/env python3
"""Package reviewed D20 sources deterministically; never rewrite frozen evidence."""
from pathlib import Path, PurePosixPath
import hashlib, zipfile
ROOT=Path(__file__).resolve().parents[1]
EXP=ROOT/'experiments/d20-inventory-test'
ARTICLE=ROOT/'content/blog/inventory-test-stockout-tradeoff'
OUT=ROOT/'static/downloads'
def sha(b): return hashlib.sha256(b).hexdigest()
def tree(root,prefix=''):
    return {prefix+p.relative_to(root).as_posix():p.read_bytes() for p in sorted(root.rglob('*'))
            if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc' and p.name!='.DS_Store'}
def safe(n):
    p=PurePosixPath(n)
    assert not p.is_absolute() and '..' not in p.parts and '\\' not in n,n
    assert not any(s in ('sealed','.git','node_modules','__pycache__') for s in p.parts),n
    assert p.suffix!='.pyc',n

def expected():
    return {'practice':tree(EXP/'practice'),'article':tree(ARTICLE),
            'images':dict(tree(EXP/'figure-tools','figure-tools/'),**tree(EXP/'images','images/'))}
def manifest(items): return ''.join(f'{sha(b)}  {n}\n' for n,b in sorted(items.items())).encode()
def members(items): return dict(items,**{'MANIFEST.sha256':manifest(items)})
def archive(kind,items):
    p=OUT/f'd20-inventory-test-{kind}.zip'; OUT.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(p,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for n,b in sorted(members(items).items()):
            safe(n); i=zipfile.ZipInfo(n,(2026,11,13,0,0,0));i.compress_type=zipfile.ZIP_DEFLATED;i.external_attr=0o100644<<16;z.writestr(i,b)
    print(sha(p.read_bytes()),p.name,p.stat().st_size)
if __name__=='__main__':
    for k,items in expected().items(): archive(k,items)
