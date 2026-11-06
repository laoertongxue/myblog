#!/usr/bin/env python3
"""Check the migration's full HTML lessons, stable anchors and unchanged assets."""
import hashlib
import json
import re
import sys
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from xml.etree import ElementTree as ET

root = Path(sys.argv[1] if len(sys.argv) > 1 else '.hugo-check')
course = json.loads(Path('data/forecast/course.json').read_text())
manifest = json.loads(Path('tutorial/upstream-manifest.json').read_text())
assert hashlib.sha256(Path('data/forecast/course.json').read_bytes()).hexdigest() == manifest['course_sha256']
for name, expected in manifest['resources'].items():
    assert hashlib.sha256((root / 'forecast' / name).read_bytes()).hexdigest() == expected, name
locations = {n.text for n in ET.parse(root / 'sitemap.xml').findall('.//{*}loc')}
titles, descriptions = set(), set()

class Page(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.ids, self.description = [], ''
        self.feed(text)
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'id' in attrs:
            self.ids.append(attrs['id'])
        if tag == 'meta' and attrs.get('name') == 'description':
            self.description = attrs['content']

for lesson in course:
    path = root / 'forecast' / lesson['id'] / 'index.html'
    text = path.read_text()
    page = Page(text)
    url = f'https://12lab.cn/forecast/{lesson["id"]}/'
    assert url in locations, url
    assert 'LearningResource' in text and 'BreadcrumbList' in text, path
    assert len(page.ids) == len(set(page.ids)), f'{path}: duplicate ID'
    body = text.split('class=lesson-content>', 1)[1].split('<div class=check>', 1)[0]
    plain = lambda s: re.sub(r'\s+', '', unescape(re.sub('<[^>]+>', '', s)))
    original = lesson['html'].replace('不修改12lab.cn。', '课程与博客预测专题分别组织，内容与完成范围以各自页面为准。')
    assert plain(original) in plain(body), f'{path}: incomplete lesson'
    assert len(re.findall(r'<h1[ >]', text)) == 1, path
    title = re.search('<title>(.*?)</title>', text).group(1)
    assert title not in titles and page.description not in descriptions, path
    titles.add(title); descriptions.add(page.description)
    assert 'href=#unit-' not in text and 'href="#unit-' not in text, path
print(f'ok    forecast: {len(course)} full HTML lessons, unique metadata/IDs, sitemap/schema, {len(manifest["resources"])} unchanged resources')
