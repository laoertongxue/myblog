"""Check shipped D9 archives and actually run the practice ZIP, not the source tree."""
from pathlib import Path, PurePosixPath
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import zipfile

REPO=Path(__file__).resolve().parents[1]
evidence=[]
def command(root,*args):
    result=subprocess.run([sys.executable,*args],cwd=root,capture_output=True,text=True,encoding='utf-8')
    assert result.returncode==0,(args,result.stdout,result.stderr)
    return {'args':args,'returncode':result.returncode,'stdout':result.stdout,'stderr':result.stderr}

with tempfile.TemporaryDirectory(prefix='d9-zip-review2-') as tmp:
    for path in sorted((REPO/'static/downloads').glob('d9-seasonal-naive-*.zip')):
        with zipfile.ZipFile(path) as archive:
            assert archive.testzip() is None
            names=archive.namelist()
            assert len(set(names))==len(names)
            for name in names:
                pure=PurePosixPath(name)
                assert not pure.is_absolute() and '..' not in pure.parts and '\\' not in name
            manifest=archive.read('MANIFEST.sha256').decode('utf-8').splitlines()
            listed=[]
            for line in manifest:
                expected,name=line.split('  ',1)
                assert hashlib.sha256(archive.read(name)).hexdigest()==expected
                listed.append(name)
            assert set(listed)==set(names)-{'MANIFEST.sha256'}
            item={'name':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                  'entries':len(names),'crc':'passed','manifest':'all entries passed'}
            if 'practice' in path.name:
                assert 'make_figures.py' not in names
                assert 'review/d9-review-round2.md' in names
                root=Path(tmp)/'practice';root.mkdir()
                archive.extractall(root)
                before=(root/'results/test.json').read_bytes()
                item['commands']=[command(root,'-m','unittest','-v'),command(root,'run.py','finalize')]
                assert (root/'results/test.json').read_bytes()==before
                (root/'freeze.json').unlink();(root/'results/test.json').unlink()
                for args in [('run.py','prepare'),('-m','unittest','-v'),('run.py','freeze'),('run.py','finalize')]:
                    item['commands'].append(command(root,*args))
                assert (root/'results/test.json').read_bytes()==before
                item['actual_zip_rebuild']='passed; original final scores byte identical'
            if 'images' in path.name:
                item['png_matches_current_source']={name:archive.read(name)==(REPO/'content/blog/seasonal-naive-demand-forecast/images'/Path(name).name).read_bytes() for name in names if name.startswith('png/')}
                assert all(item['png_matches_current_source'].values())
            if 'article' in path.name:
                item['article_matches_current_source']={name:archive.read(name)==(REPO/'content/blog/seasonal-naive-demand-forecast'/name).read_bytes() for name in names if name=='index.md' or name.startswith('images/')}
                assert all(item['article_matches_current_source'].values())
            evidence.append(item)
assert len(evidence)==3
(REPO/'docs/d9-review-round2-archives.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps([{k:v for k,v in item.items() if k!='commands'} for item in evidence],ensure_ascii=False,indent=2))
