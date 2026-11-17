from pathlib import Path
import zipfile,hashlib
root=Path(__file__).parent;out=root/'delivery';out.mkdir(exist_ok=True)
for label,src in [('practice',root/'practice'),('article',root/'article'),('images',root/'article')]:
 files=[p for p in src.rglob('*') if p.is_file() and '__pycache__' not in p.parts and (label!='images' or p.suffix=='.png')]
 with zipfile.ZipFile(out/f'd23-time-windows-{label}.zip','w',zipfile.ZIP_DEFLATED) as z:
  for p in files:z.write(p,p.relative_to(src))
print('\n'.join(f'{p.name}: {hashlib.sha256(p.read_bytes()).hexdigest()}' for p in out.glob('*.zip')))
