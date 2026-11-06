"""Compare source, clean build and bytes served from the page's actual ZIP links."""
from pathlib import Path
from html.parser import HTMLParser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from functools import partial
from urllib.request import urlopen, Request
from urllib.parse import urljoin
import hashlib,io,json,threading,zipfile

ROOT=Path(__file__).resolve().parents[2]
class Links(HTMLParser):
    def __init__(self):super().__init__();self.hrefs=[]
    def handle_starttag(self,tag,attrs):
        if tag=='a':
            href=dict(attrs).get('href','')
            if href.startswith('/downloads/d13-') and href.endswith('.zip'):self.hrefs.append(href)

class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self,*args):pass

server=ThreadingHTTPServer(('127.0.0.1',0),partial(QuietHandler,directory=str(ROOT/'.hugo-check')))
thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
base=f'http://127.0.0.1:{server.server_port}'
def fetch(path):
    with urlopen(Request(urljoin(base,path),headers={'Cache-Control':'no-cache'}),timeout=20) as r:
        assert r.status==200
        return r.read()
def sha(data):return hashlib.sha256(data).hexdigest()
try:
    page=fetch('/blog/rolling-backtest-stockout-censoring/')
    parser=Links();parser.feed(page.decode())
    paths=sorted(set(parser.hrefs))
    expected=sorted('/downloads/'+p.name for p in (ROOT/'static/downloads').glob('d13-*.zip'))
    assert paths==expected and len(paths)==3
    report={'page':'/blog/rolling-backtest-stockout-censoring/','page_sha256':sha(page),'downloads':[]}
    for path in paths:
        src=(ROOT/'static'/path.lstrip('/')).read_bytes()
        build=(ROOT/'.hugo-check'/path.lstrip('/')).read_bytes()
        served=fetch(path)
        assert src==build==served, f'source/build/HTTP mismatch: {path}'
        with zipfile.ZipFile(io.BytesIO(served)) as z:
            entries=dict(line.split('  ',1)[::-1] for line in z.read('MANIFEST.sha256').decode().splitlines())
            assert len(z.namelist())==len(set(z.namelist()))
            assert set(entries)==set(z.namelist())-{'MANIFEST.sha256'}
            for name,digest in entries.items():assert sha(z.read(name))==digest
            if path.endswith('-images.zip'):assert 'figure-tools/README.md' in entries
        report['downloads'].append({'href':path,'source_sha256':sha(src),'build_sha256':sha(build),
                                    'http_sha256':sha(served),'bytes':len(served),'manifest':'complete, all members verified'})
    (ROOT/'docs/d13-review/served-download-verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
finally:
    server.shutdown();server.server_close();thread.join()
