#!/usr/bin/env python3
"""Validate generated pages, including pagination and discovery outputs, not template text."""
import json
import sys
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
from xml.etree import ElementTree as ET

root = Path(sys.argv[1] if len(sys.argv) > 1 else '.hugo-check')

class Head(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.meta, self.links, self.schemas = {}, {}, []
        self.json = None
        self.redirect = False
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'meta':
            key = attrs.get('name', attrs.get('property', ''))
            self.meta.setdefault(key, []).append(attrs.get('content', ''))
            self.redirect |= attrs.get('http-equiv', '').lower() == 'refresh'
        if tag == 'link':
            self.links.setdefault(attrs.get('rel'), []).append(attrs.get('href'))
        if tag == 'script' and attrs.get('type') == 'application/ld+json':
            self.json = ''

    def handle_data(self, data):
        if self.json is not None:
            self.json += data

    def handle_endtag(self, tag):
        if tag == 'script' and self.json is not None:
            self.schemas.append(json.loads(self.json))
            self.json = None


def local_file(url):
    path = unquote(urlsplit(url).path).lstrip('/')
    target = root / path
    return target / 'index.html' if target.is_dir() else target

pages = {}
for path in root.rglob('*.html'):
    head = Head(path.read_text())
    if head.redirect:
        continue  # Hugo aliases carry their destination canonical and a refresh.
    for key in ('description', 'robots', 'og:url', 'og:title', 'og:image'):
        assert len(head.meta.get(key, [])) == 1, (path, key, 'missing or duplicated')
        assert head.meta[key][0].strip(), (path, key, 'empty')
    assert len(head.links.get('canonical', [])) == 1, (path, 'canonical count')
    canonical = head.links['canonical'][0]
    assert canonical == head.meta['og:url'][0], (path, 'canonical/og mismatch')
    assert urlsplit(canonical).scheme == 'https', (path, canonical)
    if path.name != '404.html':
        assert local_file(canonical).resolve() == path.resolve(), (path, 'non-self canonical', canonical)
    image = head.meta['og:image'][0]
    assert local_file(image).is_file(), (path, 'broken social image', image)
    if path.name == '404.html':
        assert 'noindex' in head.meta['robots'][0], '404 must not be indexed'
    for schema in head.schemas:
        if schema.get('@type') == 'Article':
            assert schema['mainEntityOfPage']['@id'] == canonical
            assert schema['image'] == image
            assert isinstance(schema['wordCount'], int) and schema['wordCount'] > 0
            for field in ('datePublished', 'dateModified'):
                assert datetime.fromisoformat(schema[field]).year > 2000, (path, field)
    pages[path.resolve()] = head

sitemap = ET.parse(root / 'sitemap.xml')
locations = [n.text for n in sitemap.findall('.//{*}loc')]
assert len(set(locations)) == len(locations), 'duplicate sitemap entries'
for url in locations:
    page = pages[local_file(url).resolve()]
    assert 'noindex' not in page.meta['robots'][0], ('noindex page in sitemap', url)

feed_count = 0
for path in root.rglob('index.xml'):
    tree = ET.parse(path)
    for item in tree.findall('./channel/item'):
        url = item.findtext('link')
        page = pages[local_file(url).resolve()]
        assert 'noindex' not in page.meta['robots'][0], (path, 'noindex item in RSS', url)
        feed_count += 1
assert 'Sitemap: https://12lab.cn/sitemap.xml' in (root / 'robots.txt').read_text()
assert 'noindex' in pages[(root / 'search/index.html').resolve()].meta['robots'][0]
print(f'ok    SEO: {len(pages)} pages, self canonicals, single robots, social images, Article schema; {len(locations)} sitemap URLs and {feed_count} RSS items')
