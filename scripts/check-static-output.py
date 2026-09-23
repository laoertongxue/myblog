#!/usr/bin/env python3
"""Catch broken local pictures/links and missing test content in the built site."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote
import sys

output = Path(sys.argv[1] if len(sys.argv) > 1 else '.hugo-check').resolve()
errors = []
images = 0
class Check(HTMLParser):
    def __init__(self, file):
        super().__init__()
        self.file = file
    def handle_starttag(self, tag, attrs):
        global images
        attrs = dict(attrs)
        if 'site-sidebar' in attrs.get('class', '').split():
            errors.append(f'{self.file}: old sidebar remains')
        key = 'src' if tag == 'img' else 'href' if tag == 'a' else None
        if not key or not attrs.get(key):
            return
        url = urlsplit(attrs[key])
        if url.scheme or url.netloc or not url.path:
            return
        path = unquote(url.path)
        target = output / path.lstrip('/') if path.startswith('/') else self.file.parent / path
        if target.is_dir():
            target /= 'index.html'
        if not target.exists():
            errors.append(f'{self.file.relative_to(output)}: missing {attrs[key]}')
        if tag == 'img':
            images += 1
            if 'alt' not in attrs:
                errors.append(f'{self.file}: missing image alt text')

for file in output.rglob('*.html'):
    Check(file).feed(file.read_text())
tests = [p for p in Path('content').rglob('index.md') if 'testContent: true' in p.read_text()]

for file in tests:
    text = file.read_text()
    assert '\nimages:\n' in text and '![' in text, f'{file} must contain preview and body images'

assert not errors, '\n'.join(errors)
print(f'ok    all local image/article links resolve; {len(tests)} test articles and {images} image references')
