#!/usr/bin/env python3
"""Check the new series and its discovery outputs in the generated site."""
from html.parser import HTMLParser
import json
from pathlib import Path
import sys
from urllib.parse import urlsplit, urljoin
from xml.etree import ElementTree as ET

root = Path(sys.argv[1] if len(sys.argv) > 1 else '.hugo-check')
topic = '/topics/agent-engineering/'
routes = [topic + name + '/' for name in ('01-agent-framework', '02-harness')]

class Page(HTMLParser):
    def __init__(self, route):
        super().__init__()
        self.text = (root / route.lstrip('/') / 'index.html').read_text()
        self.anchors, self.images, self.ids, self.image_chapters = [], [], [], []
        self.chapter = None
        self.tables = 0
        self.feed(self.text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'a': self.anchors.append(attrs.get('href'))
        if attrs.get('id', '').startswith('第') and '章' in attrs['id']:
            self.chapter = attrs['id']
        if tag == 'img':
            self.images.append(attrs)
            self.image_chapters.append(self.chapter)
        if attrs.get('id'): self.ids.append(attrs['id'])
        if tag == 'table': self.tables += 1

overview = Page(topic)
assert overview.anchors.index(routes[0]) < overview.anchors.index(routes[1]), 'Chapter list must follow weight order'

class ThumbnailRows(HTMLParser):
    def __init__(self, route):
        super().__init__()
        self.rows, self.row = [], None
        self.heading = False
        self.feed((root / route.lstrip('/') / 'index.html').read_text())

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'article' and 'post-row' in attrs.get('class', '').split():
            self.row = {'url': None, 'fit': None, 'images': []}
            self.rows.append(self.row)
        if self.row is not None:
            if tag == 'h2': self.heading = True
            if tag == 'a' and self.heading: self.row['url'] = attrs['href']
            if tag == 'div' and 'list-thumbnails' in attrs.get('class', '').split(): self.row['fit'] = attrs.get('data-fit')
            if tag == 'img': self.row['images'].append(attrs)

    def handle_endtag(self, tag):
        if tag == 'h2': self.heading = False
        if tag == 'article': self.row = None

expected_previews = [['00-agent-framework', '01-agent-overview', '02-context-engineering'], ['00-cover', '01-architecture', '02-loop']]
for listing in ('/', topic):
    rows = ThumbnailRows(listing).rows
    for route, names in zip(routes, expected_previews):
        row = next(row for row in rows if row['url'] == route)
        assert row['fit'] == 'contain' and len(row['images']) == 3, 'Both articles must show three complete previews'
        for picture, name in zip(row['images'], names):
            assert name + '_hu_' in picture['src'] and int(picture['width']) > int(picture['height']), 'Preview selection or full aspect ratio changed'
for listing in ('/blog/', '/weekly/'):
    for row in ThumbnailRows(listing).rows:
        assert row['fit'] is None, 'Default Blog/Weekly thumbnail behavior must stay unchanged'
        assert all(picture['width'] == picture['height'] == '520' for picture in row['images'])
print('ok    thumbnail previews: three complete Agent/Harness pictures on home and topic lists; default Blog/Weekly crop retained')
for route in ('/topics/', topic, *routes):
    page = Page(route)
    assert '测试专题' not in page.text and 'test-notice' not in page.text and 'test-label' not in page.text, route
first, second = map(Page, routes)
chapter_ids = [identifier for identifier in first.ids if identifier.startswith('第') and '章' in identifier]
assert len(chapter_ids) == 10 and all('#' + identifier in first.anchors for identifier in chapter_ids), 'All ten book chapters must be in the TOC'
assert len(first.images) == 11, 'All eleven Agent pictures must render once'
assert first.image_chapters == [None] + chapter_ids, 'Agent pictures must match the introduction and all ten chapters'
picture_names = ['00-agent-framework', '01-agent-overview', '02-context-engineering', '03-memory-and-knowledge', '04-tools', '05-coding-agent', '06-interaction', '07-evaluation', '08-post-training', '09-continuous-evolution', '10-multi-agent']
original_sizes = [(1697, 927), (1698, 926)] + [(1536, 1024)] * 9
for picture, name, (width, height) in zip(first.images, picture_names, original_sizes):
    assert picture['src'].startswith(routes[0] + 'assets/' + name), picture
    assert int(picture['width']) == 1440 and abs(int(picture['width']) / int(picture['height']) - width / height) < .003, 'Picture aspect ratio changed'
    assert routes[0] + 'assets/' + name + '.png' in [urljoin(routes[0], link) for link in first.anchors if link], 'Full-resolution source link missing'
    assert (root / (routes[0] + 'assets/' + name + '.png').lstrip('/')).is_file(), 'Original PNG missing from output'
assert len({picture['src'] for picture in first.images}) == 11, 'Do not duplicate pictures across chapters'
assert second.tables == 2, 'Both source concept tables must be retained'
assert len(second.images) == 5, 'All five Harness pictures must render once'
for picture in second.images:
    assert picture['src'].startswith(routes[1] + 'assets/'), picture
    assert int(picture['width']) > 0 and int(picture['height']) > 0, picture
for number in range(1, 6):
    assert f'ref-{number}' in second.ids and f'#ref-{number}' in second.anchors, 'Reference anchor lost'

indices = list(root.glob('search-index.*.json'))
assert len(indices) == 1, 'Expected one fingerprinted search index'
items = json.loads(indices[0].read_text())
assert {topic, *routes} <= {item['url'] for item in items}, 'Series or articles missing from search'
assert not any('/topics/layout-test/' in item['url'] for item in items), 'Removed topic in search'
locations = [element.text for element in ET.parse(root / 'sitemap.xml').findall('.//{*}loc')]
assert {topic, *routes} <= {urlsplit(url).path for url in locations}, 'Series missing from sitemap'
for path in ('index.xml', 'topics/index.xml', 'topics/agent-engineering/index.xml'):
    links = [item.findtext('link') for item in ET.parse(root / path).findall('./channel/item')]
    assert set(routes) <= {urlsplit(link).path for link in links}, f'Articles missing from {path}'
assert not (root / 'topics/layout-test').exists(), 'Removed test topic still generated'
print('ok    Agent series: chapter order, ten-section TOC, eleven unique Agent pictures in correct positions with original-PNG links, five Harness pictures, two tables, reference anchors, search, sitemap and RSS')
