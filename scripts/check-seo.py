#!/usr/bin/env python3
"""Validate generated pages, including pagination and discovery outputs, not template text."""
import json
import re
import sys
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit, urljoin
from xml.etree import ElementTree as ET

root = Path(sys.argv[1] if len(sys.argv) > 1 else '.hugo-check')

class Head(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.meta, self.links, self.schemas = {}, {}, []
        self.title, self.in_title = '', False
        self.anchors, self.ids, self.images, self.authors = [], set(), [], []
        self.resources = []
        self.modified_dates = []
        self.json = None
        self.redirect = False
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'title':
            self.in_title = True
        if tag == 'time' and 'date-modified' in attrs.get('class', '').split():
            self.modified_dates.append(attrs.get('datetime'))
        if attrs.get('id'):
            self.ids.add(attrs['id'])
        if tag == 'a' and attrs.get('href'):
            self.anchors.append(attrs['href'])
            if attrs.get('rel') == 'author':
                self.authors.append(attrs['href'])
        if tag == 'img':
            self.images.append(attrs)
        if tag in ('img', 'script') and attrs.get('src'):
            self.resources.append(attrs['src'])
        if tag == 'link' and attrs.get('rel') == 'stylesheet':
            self.resources.append(attrs['href'])
        if tag == 'meta':
            key = attrs.get('name', attrs.get('property', ''))
            self.meta.setdefault(key, []).append(attrs.get('content', ''))
            self.redirect |= attrs.get('http-equiv', '').lower() == 'refresh'
        if tag == 'link':
            self.links.setdefault(attrs.get('rel'), []).append(attrs.get('href'))
        if tag == 'script' and attrs.get('type') == 'application/ld+json':
            self.json = ''

    def handle_data(self, data):
        if self.in_title:
            self.title += data
        if self.json is not None:
            self.json += data

    def handle_endtag(self, tag):
        if tag == 'title':
            self.in_title = False
        if tag == 'script' and self.json is not None:
            self.schemas.append(json.loads(self.json))
            self.json = None


def local_file(url):
    path = unquote(urlsplit(url).path).lstrip('/')
    target = root / path
    return target / 'index.html' if target.is_dir() else target

pages, aliases = {}, {}
for path in root.rglob('*.html'):
    head = Head(path.read_text(encoding='utf-8'))
    if head.redirect:
        assert len(head.links.get('canonical', [])) == 1, (path, 'alias canonical count')
        target = head.links['canonical'][0]
        assert urlsplit(target).netloc == '12lab.cn' and local_file(target).is_file(), (path, 'broken alias', target)
        aliases[path] = target
        continue  # Hugo aliases carry their destination canonical and a refresh.
    for key in ('description', 'robots', 'og:url', 'og:title', 'og:image'):
        assert len(head.meta.get(key, [])) == 1, (path, key, 'missing or duplicated')
        assert head.meta[key][0].strip(), (path, key, 'empty')
    assert len(head.links.get('canonical', [])) == 1, (path, 'canonical count')
    canonical = head.links['canonical'][0]
    assert head.title.strip(), (path, 'empty title')
    assert canonical == head.meta['og:url'][0], (path, 'canonical/og mismatch')
    assert urlsplit(canonical).scheme == 'https', (path, canonical)
    assert urlsplit(canonical).netloc == '12lab.cn', (path, 'canonical host', canonical)
    assert not urlsplit(canonical).query and not urlsplit(canonical).fragment, (path, 'canonical query/fragment', canonical)
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
            assert schema['description'] == head.meta['description'][0]
            author_url = schema['author']['url']
            assert author_url == 'https://12lab.cn/about/' and local_file(author_url).is_file()
            assert any(urljoin(canonical, link) == author_url for link in head.authors), (path, 'author must be visible and linked')
            for field in ('datePublished', 'dateModified'):
                date = datetime.fromisoformat(schema[field])
                assert date.year > 2000 and date.tzinfo is not None, (path, field)
            assert datetime.fromisoformat(schema['dateModified']) >= datetime.fromisoformat(schema['datePublished'])
            if schema['dateModified'] != schema['datePublished']:
                assert head.modified_dates == [schema['dateModified']], (path, 'modified date must be visible and consistent')
    for image in head.images:
        assert image.get('alt', '').strip(), (path, 'content image needs descriptive alt', image.get('src'))
    pages[path.resolve()] = head

assert all(local_file(url).resolve() in pages for url in aliases.values()), 'alias chain or alias loop'

sitemap = ET.parse(root / 'sitemap.xml')
locations = [n.text for n in sitemap.findall('.//{*}loc')]
assert len(set(locations)) == len(locations), 'duplicate sitemap entries'
for url in locations:
    page = pages[local_file(url).resolve()]
    assert 'noindex' not in page.meta['robots'][0], ('noindex page in sitemap', url)
    assert page.links['canonical'] == [url], ('noncanonical sitemap URL', url)
    article = next((schema for schema in page.schemas if schema.get('@type') == 'Article'), None)
    if article:
        node = next(node for node in sitemap.findall('.//{*}url') if node.findtext('{*}loc') == url)
        assert node.findtext('{*}lastmod') == article['dateModified'], ('sitemap/schema modified date mismatch', url)

# Sitemap is a discovery aid, not an index count. This site's contract includes
# each indexable primary page; paginated pages remain discoverable via links.
expected_locations = {head.links['canonical'][0] for path, head in pages.items()
                      if 'noindex' not in head.meta['robots'][0] and not re.search(r'/page/\d+/$', head.links['canonical'][0])}
assert set(locations) == expected_locations, ('sitemap coverage', expected_locations - set(locations))

home = pages[(root / 'index.html').resolve()]
assert home.meta['robots'] == ['index, follow'], 'production homepage must remain indexable'
assert '供应链' in home.meta['description'][0] and 'AI' in home.meta['description'][0], 'homepage needs a content description'
assert home.meta['description'][0] != home.meta['og:site_name'][0]
for route in ('blog', 'topics'):
    assert pages[(root / route / 'index.html').resolve()].meta['robots'] == ['index, follow'], (route, 'public collection accidentally noindexed')

for taxonomy, label in [('tags', '标签'), ('categories', '分类')]:
    for path in (root / taxonomy).glob('*/index.html'):
        head = pages[path.resolve()]
        assert label in head.title and label in head.meta['description'][0], (path, 'taxonomy metadata lacks context')

# Crawl actual HTML links, without JS, and verify every fragment as well as
# reachability from the home page. Normalize encoded Chinese paths on disk.
edges = {}
for path, head in pages.items():
    edges[path] = set()
    for link in head.anchors:
        url = urljoin(head.links['canonical'][0], link)
        parts = urlsplit(url)
        if parts.scheme not in ('https', 'http') or parts.netloc != '12lab.cn':
            continue
        target = local_file(url).resolve()
        if target not in pages:
            continue  # Downloadable resources and Hugo alias targets are checked separately.
        edges[path].add(target)
        if parts.fragment:
            assert unquote(parts.fragment) in pages[target].ids, (path, 'broken fragment', link)
reachable, pending = set(), [(root / 'index.html').resolve()]
while pending:
    path = pending.pop()
    if path in reachable:
        continue
    reachable.add(path)
    pending.extend(edges[path] - reachable)
unreachable = [url for url in locations if local_file(url).resolve() not in reachable]
assert not unreachable, ('indexable pages have no crawlable path from home', unreachable)

feed_count = 0
for path in root.rglob('index.xml'):
    tree = ET.parse(path)
    for item in tree.findall('./channel/item'):
        url = item.findtext('link')
        page = pages[local_file(url).resolve()]
        assert 'noindex' not in page.meta['robots'][0], (path, 'noindex item in RSS', url)
        feed_count += 1
from urllib.robotparser import RobotFileParser
robots = RobotFileParser()
robots.parse((root / 'robots.txt').read_text(encoding='utf-8').splitlines())
assert robots.site_maps() == ['https://12lab.cn/sitemap.xml']
for url in locations + ['https://12lab.cn/search/', home.meta['og:image'][0]]:
    assert robots.can_fetch('Googlebot', url), ('robots blocks crawling', url)
for head in pages.values():
    for resource in head.resources:
        url = urljoin(head.links['canonical'][0], resource)
        if urlsplit(url).netloc == '12lab.cn':
            assert robots.can_fetch('Googlebot', url), ('robots blocks rendering resource', url)
assert 'noindex' in pages[(root / 'search/index.html').resolve()].meta['robots'][0]
print(f'ok    SEO: {len(pages)} pages, self canonicals, crawlable graph/fragments, robots, contextual metadata, visible authors and Article schema; {len(locations)} sitemap URLs and {feed_count} RSS items')
