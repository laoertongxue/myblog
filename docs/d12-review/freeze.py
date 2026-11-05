from pathlib import Path
import hashlib,json,zipfile
ROOT=Path(__file__).resolve().parents[2]
paths=['content/blog/forecast-error-bias-metrics','experiments/d12-forecast-errors','scripts/package-d12.py','docs/d12-review']
files=[]
for name in paths:
 p=ROOT/name
 files.extend([p] if p.is_file() else [f for f in p.rglob('*') if f.is_file() and '__pycache__' not in f.parts and f.suffix!='.pyc' and f.name!='FREEZE.json'])
files.extend((ROOT/'static/downloads').glob('d12-*.zip'))
files.extend((ROOT/'output/playwright').glob('d12-*.png'))
manifest={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)}
freeze={'version':'D12-v2-round2','base_commit':'c9ece37ebc1a54066642b3ff329ccc6948687948','independent_review_status':'round1 findings addressed; pending independent round2','files':manifest}
(ROOT/'docs/d12-review/FREEZE.json').write_text(json.dumps(freeze,ensure_ascii=False,indent=2)+'\n')
files.append(ROOT/'docs/d12-review/FREEZE.json')
out=ROOT.parent/'d12-round2-review.zip'
with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for p in sorted(files):
  info=zipfile.ZipInfo(p.relative_to(ROOT).as_posix(),date_time=(2026,11,5,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16
  z.writestr(info,p.read_bytes())
print(json.dumps({'file':str(out),'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'bytes':out.stat().st_size,'files':len(files)}))
