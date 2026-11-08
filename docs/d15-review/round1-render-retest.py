from pathlib import Path
import argparse, os, tempfile, zipfile, subprocess
ROOT=Path(__file__).resolve().parents[2]
parser=argparse.ArgumentParser(description='Independently redraw the D15 images ZIP and compare bytes.')
parser.add_argument('--python', default=os.environ.get('D15_RENDER_PYTHON', 'python3'), help='Python with Pillow and fontTools installed')
parser.add_argument('--font', default=os.environ.get('D15_FONT'), help='Noto Sans SC font path (or set D15_FONT)')
args=parser.parse_args()
if not args.font:
    parser.error('--font or D15_FONT is required')
PYTHON=args.python
FONT=str(Path(args.font).expanduser().resolve())
with tempfile.TemporaryDirectory(prefix='d15-independent-figures-') as temp:
    t=Path(temp)
    with zipfile.ZipFile(ROOT/'static/downloads/d15-inventory-position-images.zip') as z:z.extractall(t)
    before={p.relative_to(t):p.read_bytes() for folder in ('images','figure-tools') for p in (t/folder).rglob('*') if p.suffix in ('.png','.svg')}
    subprocess.run([PYTHON,str(t/'figure-tools/render_figures.py'),'--font-path',FONT],cwd='/tmp',check=True)
    for name,blob in before.items():assert (t/name).read_bytes()==blob,name
    assert not (t/'assets').exists() and not (t/'content').exists()
    print('PASS: clean independent ZIP rendering; all',len(before),'PNG/SVG files byte-identical; no repository path generated.')
    code='''from PIL import Image,ImageChops
from pathlib import Path
import sys
root=Path(sys.argv[1])
for p in (root/'images').glob('d15*.png'):
 im=Image.open(p).convert('RGB');r,g,b=im.split();assert ImageChops.difference(r,g).getbbox() is None;assert ImageChops.difference(g,b).getbbox() is None
 if 'cover' in p.name:assert im.size==(900,383)
 print(p.name,im.size,'grayscale PASS')
'''
    subprocess.run([PYTHON,'-c',code,str(t)],check=True)
