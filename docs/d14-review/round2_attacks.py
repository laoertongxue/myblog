"""Read-only independent D14 adversarial probes; no sealed/test source access."""
from pathlib import Path
import ast, csv, hashlib, math, re, sys, zipfile
ROOT=Path(__file__).resolve().parents[2]
P=ROOT/'experiments/d14-model-selection/practice'
sys.dont_write_bytecode=True
sys.path.insert(0,str(P))
import baseline, run

# Check actual manifest coverage independently, including nested practice.
for kind in ('practice','article','images'):
    with zipfile.ZipFile(ROOT/f'static/downloads/d14-model-selection-{kind}.zip') as z:
        blobs={n:z.read(n) for n in z.namelist()}
        for prefix in ('','practice/') if kind=='images' else ('',):
            manifest=prefix+'MANIFEST.sha256'
            listed={n:sha for sha,n in (s.split('  ',1) for s in blobs[manifest].decode().splitlines())}
            expected={n[len(prefix):]:v for n,v in blobs.items() if n.startswith(prefix) and n!=manifest}
            assert set(listed)==set(expected),(kind,prefix,'coverage')
            assert all(hashlib.sha256(expected[n]).hexdigest()==sha for n,sha in listed.items())
print('PASS: actual archive manifests cover all members, including nested practice')

# Independently compare all displayed table cells with output metrics.
scores=list(csv.DictReader((P/'results/metrics.csv').open()))
md=(ROOT/'content/blog/forecast-model-selection-boundaries/index.md').read_text()
for s in scores:
    if s['case']=='hewei' and s['task_horizon']=='1':
        other=next(t for t in scores if t['case']=='hewei' and t['method']==s['method'] and t['task_horizon']=='5')
        assert f"| {s['method']} | {float(s['mae']):.4f} | {float(other['mae']):.4f} |" in md
    if s['case']=='apparel' and s['task_horizon']=='1':
        other=next(t for t in scores if t['case']=='apparel' and t['method']==s['method'] and t['task_horizon']=='5')
        assert f"<tr><td>{s['method']}</td><td>{float(s['mae']):.4f}</td><td>{float(s['rmse']):.4f}</td><td>{float(other['mae']):.4f}</td></tr>" in md
print('PASS: all 35 displayed numeric table cells match exact four-decimal rounding')

class GuardedRows(list):
    def __getitem__(self,key):
        if isinstance(key,slice):
            assert key.stop is not None and key.stop<=self.limit,'future slice'
        else: assert 0<=key<self.limit,'future index'
        return super().__getitem__(key)
for case,meta in run.CASES.items():
    rows=baseline.load_csv(P/'data'/f'{case}-development.csv',meta[0])
    guarded=GuardedRows(rows)
    for h in (1,5):
        for origin in range(112,141-h):
            guarded.limit=origin
            for label,args in run.METHODS:
                assert run.issue(guarded,origin,h,case,label,args)==run.issue(rows[:origin],origin,h,case,label,args)
print('PASS: access-trapped future boundary for all 728 method/case/origin/task vintages')

# Minimal demonstrations of optional hardening gaps, without changing artifacts.
tree=ast.parse((ROOT/'scripts/check-d14.py').read_text())
ns={'hashlib':hashlib}
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('digest','check_manifest')],type_ignores=[]),'isolated_checker','exec'),ns)
ns['check_manifest'](b'',lambda n: (_ for _ in ()).throw(AssertionError('unexpected read')))
print('P3 hardening: empty manifest accepted by check_manifest (actual manifests complete)')
rows=baseline.load_csv(P/'data/apparel-development.csv',run.CASES['apparel'][0])
r=run.issue(rows,112,1,'hewei','SNaive7',{'method':'seasonal_naive_7'})[0]
assert r['series']==run.CASES['hewei'][0] and r['unit']=='kg/day'
print('P3 hardening: direct issue accepts apparel rows with hewei case, labels them kg/day')
tiny=math.nextafter(0.,1.)
small=[dict(r,demand=tiny) for r in rows[:2]]
assert baseline.ses(small,1,.5)==[0.]
print('P3 numeric scope: SES of two equal min-subnormals returns zero (exact result is min-subnormal)')
