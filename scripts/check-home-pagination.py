#!/usr/bin/env python3
"""Build isolated content to check ten-item pages without publishing fixtures."""
import argparse
from html.parser import HTMLParser
from pathlib import Path
import subprocess
import tempfile


class FeedParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_feed = False
        self.in_heading = False
        self.links = []
        self.next = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'section' and 'home-feed' in attrs.get('class', '').split():
            self.in_feed = True
            self.next = attrs.get('data-next') or ''
        if self.in_feed and tag == 'h2':
            self.in_heading = True
        if self.in_heading and tag == 'a':
            self.links.append(attrs['href'])

    def handle_endtag(self, tag):
        if tag == 'h2':
            self.in_heading = False
        if tag == 'section':
            self.in_feed = False


def check(destination=None):
    root = Path(__file__).resolve().parent.parent
    with tempfile.TemporaryDirectory(prefix='12lab-pagination-') as temporary:
        content = Path(temporary) / 'content'
        output = Path(destination).resolve() if destination else Path(temporary) / 'public'
        expected = []
        for i in range(1, 24):
            section = ('blog', 'weekly', 'topics/example')[i % 3]
            name = f'{i:03d}'
            article = content / section / name / 'index.md'
            article.parent.mkdir(parents=True, exist_ok=True)
            article.write_text(f'---\ntitle: "测试文章 {i}"\nslug: "{name}"\ndate: 2020-01-{i:02d}\nweight: {i}\ndescription: "分页测试文章"\n---\n测试正文。\n')
            expected.insert(0, f'/{section}/{name}/')
        for name, metadata in [('future', 'date: 2999-01-01'), ('draft', 'date: 2020-02-01\ndraft: true')]:
            article = content / 'blog' / name / 'index.md'
            article.parent.mkdir(parents=True)
            article.write_text(f'---\ntitle: "不应发布"\nslug: {name}\n{metadata}\n---\n')
        subprocess.run(['hugo', '--gc', '--minify', '--contentDir', str(content), '--destination', str(output)], cwd=root, check=True, capture_output=True)
        combined = []
        for page, count in [(1, 10), (2, 10), (3, 3)]:
            html = output / ('index.html' if page == 1 else f'page/{page}/index.html')
            parser = FeedParser()
            parser.feed(html.read_text())
            assert len(parser.links) == count, (page, parser.links)
            assert parser.links == expected[(page - 1) * 10:page * 10], 'Incorrect chronological order'
            assert parser.next == (f'/page/{page + 1}/' if page < 3 else ''), parser.next
            combined.extend(parser.links)
        assert len(set(combined)) == 23
        print('ok    homepage pagination: 10 + 10 + 3, date order, no duplicates, drafts/future excluded')


if __name__ == '__main__':
    arguments = argparse.ArgumentParser()
    arguments.add_argument('--destination')
    check(arguments.parse_args().destination)
