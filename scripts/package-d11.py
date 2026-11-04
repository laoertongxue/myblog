#!/usr/bin/env python3
"""Build deterministic D11 reader downloads from reviewed repository files."""
from pathlib import Path
import hashlib, zipfile
ROOT=Path(__file__).resolve().parents[1]
EXP=ROOT/'experiments/d11-simple-exponential-smoothing'
ARTICLE=ROOT/'content/blog/simple-exponential-smoothing-demand-forecast'
OUT=ROOT/'static/downloads';OUT.mkdir(parents=True,exist_ok=True)

def files(root):
    return [p for p in sorted(root.rglob('*')) if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc' and p.name!='.DS_Store']

def manifest(root):
    entries=[f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(root).as_posix()}' for p in files(root) if p.name!='MANIFEST.sha256']
    (root/'MANIFEST.sha256').write_text('\n'.join(entries)+'\n',encoding='utf-8',newline='\n')

def archive(name,items):
    with zipfile.ZipFile(OUT/name,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for label,data in sorted(items):
            info=zipfile.ZipInfo(label,date_time=(2026,11,4,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16
            z.writestr(info,data)

def tree(root,prefix=''):
    return [(prefix+p.relative_to(root).as_posix(),p.read_bytes()) for p in files(root)]

def with_manifest(items):
    return items+[('MANIFEST.sha256',(''.join(f'{hashlib.sha256(data).hexdigest()}  {name}\n' for name,data in sorted(items))).encode())]

manifest(EXP/'practice')
archive('d11-simple-exponential-smoothing-practice.zip',tree(EXP/'practice'))
archive('d11-simple-exponential-smoothing-article.zip',with_manifest(tree(ARTICLE)))
archive('d11-simple-exponential-smoothing-images.zip',with_manifest(tree(EXP/'practice','practice/')+tree(EXP/'figure-tools','figure-tools/')+tree(EXP/'images','images/')))
for p in sorted(OUT.glob('d11-*.zip')):
    print(hashlib.sha256(p.read_bytes()).hexdigest(),p.name,p.stat().st_size)
