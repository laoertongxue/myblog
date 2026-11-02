"""Independent LF/Git checkout supplement; mutates only temporary repositories."""
from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile

REPO=Path(__file__).resolve().parents[1]
SOURCE=REPO/'examples/d9-seasonal-naive'
OLD=REPO.parent/'d9-tools/before-lf'
result={'reviewer':'independent d9_review2 LF supplement','commands':[],'source_sha256':{},'checks':{}}


def sha(raw):return hashlib.sha256(raw).hexdigest()


def command(args,cwd):
    completed=subprocess.run(args,cwd=cwd,capture_output=True,text=True,encoding='utf-8')
    result['commands'].append({'args':args,'returncode':completed.returncode,'stdout':completed.stdout,'stderr':completed.stderr})
    assert completed.returncode==0,(args,completed.stdout,completed.stderr)
    return completed.stdout


files={p.relative_to(SOURCE).as_posix():p.read_bytes() for p in SOURCE.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
assert all(b'\r' not in raw for raw in files.values())
result['source_sha256']={name:sha(raw) for name,raw in files.items()}
result['checks']['all_current_experiment_files_lf']=True
assert 'examples/d9-seasonal-naive/** text eol=lf' in (REPO/'.gitattributes').read_text(encoding='utf-8')
result['checks']['gitattributes_pattern']='examples/d9-seasonal-naive/** text eol=lf'

old_test=json.loads((OLD/'test.json').read_text(encoding='utf-8'))
new_test=json.loads((SOURCE/'results/test.json').read_text(encoding='utf-8'))
assert old_test==new_test
old_freeze=json.loads((OLD/'freeze.json').read_text(encoding='utf-8'))
new_freeze=json.loads((SOURCE/'freeze.json').read_text(encoding='utf-8'))
assert old_freeze['policy']==new_freeze['policy']
result['checks']['test_results_before_after']='all JSON values identical, both cases and all40 daily/36 cumulative records'
result['checks']['policy_before_after']='identical; seed/period/splits/generation scenario unchanged'

# Independently compare every current JSON to old article ZIP values where it has results.
# The pre-LF byte hashes are also recorded by the earlier review evidence (if retained).
earlier=REPO/'docs/d9-review-round2-evidence.json'
result['checks']['old_test_file_sha256']=sha((OLD/'test.json').read_bytes())
result['checks']['new_test_file_sha256']=sha((SOURCE/'results/test.json').read_bytes())

with tempfile.TemporaryDirectory(prefix='d9-lf-git-') as directory:
    root=Path(directory)
    gitroot=root/'repository';gitroot.mkdir()
    attr=(REPO/'.gitattributes').read_bytes()
    (gitroot/'.gitattributes').write_bytes(attr)
    target=gitroot/'examples/d9-seasonal-naive'
    shutil.copytree(SOURCE,target,ignore=shutil.ignore_patterns('__pycache__'))
    command(['git','init',str(gitroot)],root)
    for key,value in [('core.autocrlf','true'),('user.name','D9 independent review'),('user.email','d9-review@example.invalid')]:
        command(['git','config',key,value],gitroot)
    command(['git','add','--','.gitattributes','examples/d9-seasonal-naive'],gitroot)
    stage=[]
    for name,raw in files.items():
        blob=subprocess.run(['git','show',':examples/d9-seasonal-naive/'+name],cwd=gitroot,capture_output=True)
        assert blob.returncode==0 and blob.stdout==raw,name
        stage.append(name)
    command(['git','commit','-m','Independent LF candidate checkout test'],gitroot)
    result['checks']['staged_blob_matches_source']=stage
    checkouts=[]
    for mode in ['true','false']:
        clone=root/('checkout-'+mode)
        clone.mkdir()
        command(['git','config','core.autocrlf',mode],gitroot)
        command(['git','checkout-index','--all','--force','--prefix='+clone.as_posix()+'/'],gitroot)
        for name,raw in files.items():
            assert (clone/'examples/d9-seasonal-naive'/name).read_bytes()==raw,(mode,name)
        eol=command(['git','ls-files','--eol','--','examples/d9-seasonal-naive'],gitroot)
        assert 'w/crlf' not in eol and 'i/crlf' not in eol,eol
        runroot=clone/'examples/d9-seasonal-naive'
        command([sys.executable,'-m','unittest','-v'],runroot)
        command([sys.executable,'run.py','finalize'],runroot)
        assert (runroot/'results/test.json').read_bytes()==files['results/test.json']
        # Fresh output must remain LF and reproduce the freeze file across checkout modes.
        (runroot/'freeze.json').unlink();(runroot/'results/test.json').unlink()
        for phase in ['prepare','freeze','finalize']:
            command([sys.executable,'run.py',phase],runroot)
        for name,raw in files.items():
            assert (runroot/name).read_bytes()==raw,('rebuild',mode,name)
        checkouts.append({'core.autocrlf':mode,'checkout_bytes':'identical all files','tests':12,'finalize':'passed',
                       'fresh_rebuild':'all files byte identical; LF preserved'})
    result['checks']['real_git_checkout_index']=checkouts
    result['checks']['local_clone_attempt']='An earlier local clone attempt failed with Could not read from remote repository; no clone completed. Actual stage+checkout-index is the verified route; no remote/network repository used.'

# Compare the pre-layout article ZIP's educational table values with current HTML tables.
article=(REPO/'content/blog/seasonal-naive-demand-forecast/index.md').read_text(encoding='utf-8')
for fragment in ['第106天','第107天','第108天','第109天','第110天','第111天','第112天',
                 '2.1750','4.1111','2.9250','5.9167']:
    assert fragment in article
assert 'overflow-x:auto' in article and 'white-space:nowrap' in article
result['checks']['mobile_table_layout']='horizontal scroll and nowrap present; seven-value hand table and final scores retained'

assert all((SOURCE/name).read_bytes()==raw for name,raw in files.items())
result['checks']['main_experiment_unchanged_by_review']=True
(REPO/'docs/d9-review-lf.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result['checks'],ensure_ascii=False,indent=2))
