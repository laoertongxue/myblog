#!/usr/bin/env python3
"""Describe every uploaded file and the resources to probe after switching."""
import hashlib
import json
from html.parser import HTMLParser
from pathlib import Path
import sys
from urllib.parse import unquote, urlsplit

NAME = 'release-manifest.json'


class Resources(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.urls = []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if tag in ('script', 'img', 'source') and d.get('src'):
            self.urls.append(d['src'])
        if tag == 'link' and d.get('rel') == 'stylesheet':
            self.urls.append(d['href'])
        if d.get('data-index'):
            self.urls.append(d['data-index'])
        for candidate in d.get('srcset', '').split(','):
            if candidate.strip():
                self.urls.append(candidate.strip().split()[0])


def create(root):
    root = Path(root)
    files = {}
    for file in sorted(root.rglob('*')):
        if file.is_symlink():
            raise ValueError(f'Symlink in build: {file}')
        if file.is_file() and file.relative_to(root).as_posix() != NAME:
            files[file.relative_to(root).as_posix()] = hashlib.sha256(file.read_bytes()).hexdigest()
    selected = ['index.html', 'search/index.html', 'index.xml', 'sitemap.xml', 'robots.txt', '404.html']
    # Prefer a real article over layout-test content, but accept small sites too.
    articles = sorted(p for p in files if p.startswith(('blog/', 'weekly/', 'topics/')) and p.count('/') >= 2 and p.endswith('/index.html') and '/page/' not in p)
    if articles:
        selected.append(next((p for p in articles if 'layout-test' not in p), articles[0]))
    probes = {}
    for name in selected:
        if name not in files:
            raise ValueError(f'Missing required output: {name}')
        probes['/' + name] = {'file': name, 'status': 200}
        if name.endswith('.html'):
            for url in Resources((root / name).read_text()).urls:
                parts = urlsplit(url)
                if parts.scheme or parts.netloc:
                    continue
                path = unquote(parts.path).lstrip('/') if parts.path.startswith('/') else (Path(name).parent / unquote(parts.path)).as_posix()
                if path not in files:
                    raise ValueError(f'Missing probe resource: {path}')
                probes['/' + path] = {'file': path, 'status': 200}
    # Test canonical directory routing, not just direct index.html requests.
    for url, probe in list(probes.items()):
        if url.endswith('/index.html'):
            probes[url[:-10]] = probe
    probes['/__12lab_missing_release_probe__/'] = {'file': '404.html', 'status': 404}
    data = {'version': 1, 'html_count': sum(p.endswith('.html') for p in files), 'files': files, 'probes': probes}
    (root / NAME).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    print(f'Manifest: {len(files)} files, {len(probes)} HTTP probes')
    return data


if __name__ == '__main__':
    create(sys.argv[1])
