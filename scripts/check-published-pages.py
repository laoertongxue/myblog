#!/usr/bin/env python3
"""Require every published content route, even after intentional content removal."""
import csv
import io
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

output = Path(sys.argv[1] if len(sys.argv) > 1 else '.hugo-check')
listing = subprocess.run(['hugo', 'list', 'published'], check=True, capture_output=True, text=True).stdout
pages = list(csv.DictReader(io.StringIO(listing)))
assert pages, 'Hugo published-content inventory is empty'
required = {Path('index.html'), Path('404.html')}
for page in pages:
    route = unquote(urlsplit(page['permalink']).path).lstrip('/')
    required.add(Path(route) / 'index.html' if route.endswith('/') or not route else Path(route))
missing = sorted(str(path) for path in required if not (output / path).is_file())
assert not missing, f'Published routes missing from build: {missing}'
print(f'ok    all {len(required)} required routes exist ({len(pages)} published content entries plus home/404)')
