#!/usr/bin/env python3
"""Deterministic, allowlisted math bridge reader downloads."""
from pathlib import Path
import hashlib, zipfile
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'static/downloads'
EXP=ROOT/'experiments/p01-math-bridge'
ARTICLE=ROOT/'content/topics/forecasting/01-math-bridge'
def tree(root,prefix=''):
    return [(prefix+p.relative_to(root).as_posix(),p.read_bytes()) for p in sorted(root.rglob('*')) if p.is_file() and '__pycache__' not in p.parts and p.suffix not in ('.pyc',) and p.name!='.DS_Store']
def archive(label,items):
    items.append(('MANIFEST.sha256',''.join(f'{hashlib.sha256(data).hexdigest()}  {name}\n' for name,data in sorted(items)).encode()))
    with zipfile.ZipFile(OUT/f'p01-math-bridge-{label}.zip','w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for name,data in sorted(items):
            info=zipfile.ZipInfo(name,(2026,11,6,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16
            z.writestr(info,data)
archive('practice',tree(EXP/'practice'))
archive('article',tree(ARTICLE))
archive('images',tree(ARTICLE/'images','content/topics/forecasting/01-math-bridge/images/')+tree(EXP/'figure-tools','experiments/p01-math-bridge/figure-tools/')+tree(ROOT/'assets/diagram-sources/forecasting-math-bridge','assets/diagram-sources/forecasting-math-bridge/')+[('assets/cover-sources/forecasting-math-bridge.svg',(ROOT/'assets/cover-sources/forecasting-math-bridge.svg').read_bytes()),('package.json',(ROOT/'package.json').read_bytes()),('package-lock.json',(ROOT/'package-lock.json').read_bytes())])
for p in sorted(OUT.glob('p01-*.zip')):print(hashlib.sha256(p.read_bytes()).hexdigest(),p.name)
