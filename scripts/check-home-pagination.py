#!/usr/bin/env python3
"""Build isolated content to check ten-item pages without publishing fixtures."""
import argparse
from html.parser import HTMLParser
from pathlib import Path
import subprocess
import shutil
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
            self.next = ''
        if tag == 'a' and attrs.get('rel') == 'next':
            self.next = attrs['href']
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
        for i in range(1, 44):
            section = ('blog', 'weekly', 'topics/example')[i % 3]
            name = f'{i:03d}'
            article = content / section / name / 'index.md'
            article.parent.mkdir(parents=True, exist_ok=True)
            article.write_text(f'---\ntitle: "测试文章 {i}"\nslug: "{name}"\ndate: 2020-{((i-1)//28)+1:02d}-{((i-1)%28)+1:02d}\nweight: {i}\ndescription: "分页测试文章"\n---\n测试正文。\n')
            if i in (41, 42, 43):
                for image in range(1, 5):
                    shutil.copy(root / 'assets/images/avatar-wangye.png', article.parent / f'photo-{image}.png')
                if i == 42:
                    article.write_text(article.read_text().replace('weight:', 'images: ["photo-3.png", "photo-1.png"]\nweight:'))
                if i == 41:
                    article.write_text(article.read_text().replace('weight:', 'cover: "photo-2.png"\nweight:'))
            expected.insert(0, f'/{section}/{name}/')
        for name, metadata in [('future', 'date: 2999-01-01'), ('draft', 'date: 2020-02-01\ndraft: true')]:
            article = content / 'blog' / name / 'index.md'
            article.parent.mkdir(parents=True)
            article.write_text(f'---\ntitle: "不应发布"\nslug: {name}\n{metadata}\n---\n')
        subprocess.run(['hugo', '--gc', '--minify', '--contentDir', str(content), '--destination', str(output)], cwd=root, check=True, capture_output=True)
        first_page = (output / 'index.html').read_text()
        assert first_page.count('class=list-thumbnails') + first_page.count('class="list-thumbnails"') == 3
        for count in (1, 2, 3):
            assert f'--thumbnail-count:{count}' in first_page
        assert 'photo-4_' not in first_page, 'Preview should be limited to three images'
        assert 'photo-3_' in first_page and '.webp' in first_page
        print('ok    thumbnails: explicit images, cover fallback, bundle discovery, three-image limit')
        assert 'pagination-gap' in first_page, 'Long pagination should collapse middle pages'
        assert 'home-feed.min.' not in first_page, 'Mobile must use the same numbered pagination'
        cover_detail = (output / 'topics/example/041/index.html').read_text()
        assert '/topics/example/041/photo-2_hu_' in cover_detail, 'Bundle cover must resolve inside its article'
        combined = []
        for page, count in [(1, 10), (2, 10), (3, 10), (4, 10), (5, 3)]:
            html = output / ('index.html' if page == 1 else f'page/{page}/index.html')
            parser = FeedParser()
            parser.feed(html.read_text())
            assert len(parser.links) == count, (page, parser.links)
            assert parser.links == expected[(page - 1) * 10:page * 10], 'Incorrect chronological order'
            assert parser.next == (f'/page/{page + 1}/' if page < 5 else ''), parser.next
            combined.extend(parser.links)
        assert len(set(combined)) == 43
        print('ok    homepage pagination: 10 + 10 + 10 + 10 + 3, date order, no duplicates, drafts/future excluded')


if __name__ == '__main__':
    arguments = argparse.ArgumentParser()
    arguments.add_argument('--destination')
    check(arguments.parse_args().destination)
