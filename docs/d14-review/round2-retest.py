"""Post-fix independent retest. Only development sources, temporary copies."""
from pathlib import Path
import ast, hashlib, json, math, runpy, subprocess, sys, tempfile, zipfile
ROOT=Path(__file__).resolve().parents[2]
P=ROOT/'experiments/d14-model-selection/practice'
sys.dont_write_bytecode=True
# Reuse independent manifest, article-cell and access-trap checks unchanged.
source=(ROOT/'docs/d14-review/round2_attacks.py').read_text().split('# Minimal demonstrations')[0]
ns={'__file__':str(ROOT/'docs/d14-review/round2_attacks.py')}
exec(compile(source,'original-independent-checks','exec'),ns)
baseline,run=ns['baseline'],ns['run']

def rejects(fn, kind=ValueError):
    try: fn()
    except kind: return
    raise AssertionError('malformed input was accepted')

tree=ast.parse((ROOT/'scripts/check-d14.py').read_text())
c={'hashlib':hashlib}
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('digest','check_manifest')],type_ignores=[]),'isolated_checker','exec'),c)
blobs={'a':b'a','b':b'b'}
lines={n:f'{hashlib.sha256(v).hexdigest()}  {n}\n'.encode() for n,v in blobs.items()}
check=c['check_manifest']
check(lines['a']+lines['b'],blobs.__getitem__,list(blobs)+['MANIFEST.sha256'])
for bad in (b'',lines['a'],lines['a']+lines['b']+lines['a'],lines['a']+lines['b']+b'0  surplus\n'):
    rejects(lambda:check(bad,blobs.__getitem__,list(blobs)),AssertionError)
print('PASS: complete manifest accepted; empty, omitted, duplicate and surplus entries rejected')
for case,other in [('apparel','hewei'),('hewei','apparel')]:
    rows=baseline.load_csv(P/'data'/f'{case}-development.csv',run.CASES[case][0])
    for invalid in (other,'unknown'):
        rejects(lambda:run.issue(rows,112,1,invalid,'SNaive7',{'method':'seasonal_naive_7'}))
        rejects(lambda:run.replay(rows,invalid))
print('PASS: both cross-case directions and unknown case rejected in issue and replay')
tiny=math.nextafter(0.,1.)
def ses(values,alpha):return baseline.ses([dict(r,demand=v) for r,v in zip(rows,values)],1,alpha)
rejects(lambda:ses([tiny,tiny],.5))
rejects(lambda:ses([tiny,0],.5))
assert ses([0,0],.5)==[0]
assert ses([tiny,0],0)==[tiny]
assert ses([tiny,0],1)==[0]
assert ses([0,tiny],0)==[0]
assert ses([0,tiny],1)==[tiny]
assert ses([2*tiny,2*tiny],.5)==[2*tiny]
print('PASS: SES original underflow and true-decay underflow reject; zero, endpoints, representable tiny pass')

# Pre-fix numeric behavior is available in the unchanged D13 inherited baseline.
# No historical D14 results copy was retained by this reviewer; this proves
# byte identity to reconstructed pre-hardening behavior, not archival history.
old=ROOT/'experiments/d13-rolling-backtest/practice/baseline.py'
provenance=json.loads((P/'code_provenance.json').read_text())
assert hashlib.sha256(old.read_bytes()).hexdigest()==provenance['files']['baseline.py']['d13_source_sha256']
for name,meta in provenance['files'].items():
    assert hashlib.sha256((P/name).read_bytes()).hexdigest()==meta['d14_sha256']
with tempfile.TemporaryDirectory(prefix='d14-review2-') as temp:
    q=Path(temp)
    with zipfile.ZipFile(ROOT/'static/downloads/d14-model-selection-practice.zip') as z:z.extractall(q)
    (q/'baseline.py').write_bytes(old.read_bytes())
    subprocess.run([sys.executable,'-B',str(q/'run.py')],cwd=q,check=True)
    hashes={}
    for result in sorted((P/'results').iterdir()):
        assert (q/'results'/result.name).read_bytes()==result.read_bytes(),result.name
        hashes[result.name]=hashlib.sha256(result.read_bytes()).hexdigest()
    assert len(hashes)==8
print('PASS: all eight result files byte-identical under original inherited D13 numeric implementation')
print(json.dumps({'result_sha256':hashes},indent=2))
