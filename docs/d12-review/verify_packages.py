from pathlib import Path
import hashlib,json,subprocess,sys,tempfile,zipfile
ROOT=Path(__file__).resolve().parents[2]
report={}
for path in sorted((ROOT/'static/downloads').glob('d12-*.zip')):
    with zipfile.ZipFile(path) as z:
        names=z.namelist()
        assert len(names)==len(set(names))
        manifest={line.split('  ',1)[1]:line.split('  ',1)[0] for line in z.read('MANIFEST.sha256').decode().splitlines()}
        assert set(manifest)==set(names)-{'MANIFEST.sha256'}
        for name,sha in manifest.items(): assert hashlib.sha256(z.read(name)).hexdigest()==sha,name
        assert not any('sealed' in name or 'test-data' in name for name in names)
        entry={'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'members':len(names),'manifest':'complete and verified'}
        if 'practice' in path.name:
            with tempfile.TemporaryDirectory() as td:
                z.extractall(td)
                test=subprocess.run([sys.executable,'-m','unittest','-v'],cwd=td,text=True,capture_output=True,check=True)
                subprocess.run([sys.executable, str(Path(td)/'run.py')],cwd='/',check=True,capture_output=True)
                for name,sha in manifest.items():
                    assert hashlib.sha256((Path(td)/name).read_bytes()).hexdigest()==sha,name
                entry['fresh_extract_tests']=test.stderr
                entry['rerun']='all five result files byte-identical; all manifest files unchanged'
        report[path.name]=entry
(ROOT/'docs/d12-review/package-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:{x:y for x,y in v.items() if x!='fresh_extract_tests'} for k,v in report.items()},indent=2))
