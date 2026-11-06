"""Freeze only D13 deliverables; never package other repository files or test labels."""
from pathlib import Path
import hashlib,json,zipfile
ROOT=Path(__file__).resolve().parents[2]
EXP=ROOT/'experiments/d13-rolling-backtest'
DOC=ROOT/'docs/d13-review'
ARTICLE=ROOT/'content/blog/rolling-backtest-stockout-censoring'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def files(root):
    return [p for p in sorted(root.rglob('*')) if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc' and p.name!='.DS_Store']

# A late repack must invalidate this gate rather than freeze stale served bytes.
served=json.loads((DOC/'served-download-verification.json').read_text())
assert sha(ROOT/'.hugo-check/blog/rolling-backtest-stockout-censoring/index.html')==served['page_sha256']
assert len(served['downloads'])==3
for item in served['downloads']:
    rel=item['href'].lstrip('/')
    assert sha(ROOT/'static'/rel)==sha(ROOT/'.hugo-check'/rel)==item['http_sha256']==item['source_sha256']==item['build_sha256']

payload=files(EXP)+files(ARTICLE)+[ROOT/'scripts/package-d13.py']+sorted((ROOT/'static/downloads').glob('d13-*.zip'))
freeze={'status':'v3: v2 round 2 passed per parent; wording and packaging delta awaiting independent check; not submitted or pushed',
        'version':'D13-v3','source_repo_head':'8fc0bdf14d695ca074736d26357094acf63644fe',
        'files':{str(p.relative_to(ROOT)):sha(p) for p in payload}}
(DOC/'FREEZE.json').write_text(json.dumps(freeze,ensure_ascii=False,indent=2)+'\n')
# Text source allows cloud reviewers to inspect every forecast without unpacking ZIP.
readable=[ARTICLE/'index.md']+[p for p in files(EXP/'practice') if p.suffix in ('.py','.json','.csv','.md')]+[EXP/'figure-tools/render_figures.py',EXP/'figure-tools/README.md',DOC/'README.md',DOC/'v2-v3-payload-diff.json',DOC/'v2-v3-article.patch',DOC/'round1-resolution.md',DOC/'served-download-verification.json',DOC/'FREEZE.json']
chunks=['# D13 v3 完整可读审查材料\n\n包含正文、全部实践源代码、开发CSV、九份结果及冻结清单；配图见审查页附件。\n']
for p in readable:
    chunks.append('\n# 文件 '+str(p.relative_to(ROOT))+'\n\nSHA256 '+sha(p)+'\n\n~~~~text\n'+p.read_text(encoding='utf-8')+'\n~~~~\n')
(DOC/'review-source.md').write_text(''.join(chunks),encoding='utf-8')
assert (DOC/'review-source.md').stat().st_size<1024*1024
bundle_files=sorted(set(payload+files(DOC)))
manifest=''.join(f'{sha(p)}  {p.relative_to(ROOT).as_posix()}\n' for p in bundle_files)
target=ROOT.parent/'d13-review-v3.zip'
with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
    for name,data in [(str(p.relative_to(ROOT)),p.read_bytes()) for p in bundle_files]+[('INTEGRATION_MANIFEST.sha256',manifest.encode())]:
        info=zipfile.ZipInfo(name,date_time=(2026,11,6,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16
        z.writestr(info,data)
with zipfile.ZipFile(target) as z:
    names=z.namelist();assert len(set(names))==len(names)
    for line in z.read('INTEGRATION_MANIFEST.sha256').decode().splitlines():
        digest,name=line.split('  ',1);assert hashlib.sha256(z.read(name)).hexdigest()==digest
receipt={'complete_bundle':str(target),'sha256':sha(target),'size':target.stat().st_size,
         'readable_source':str(DOC/'review-source.md'),'readable_sha256':sha(DOC/'review-source.md'),
         'article_sha256':sha(ARTICLE/'index.md'),'freeze_sha256':sha(DOC/'FREEZE.json'),
         'reader_archives':{p.name:sha(p) for p in sorted((ROOT/'static/downloads').glob('d13-*.zip'))}}
(ROOT.parent/'d13-freeze-receipt-v3.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt,indent=2))
