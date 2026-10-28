#!/usr/bin/env python3
"""Build isolated content to check ten-item pages without publishing fixtures."""
import argparse
import json
from html.parser import HTMLParser
from pathlib import Path
import subprocess
import shutil
import struct
import tempfile
import zlib


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


class TopicParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_article = self.in_heading = False
        self.links = []
        self.next = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'article' and 'post-row' in attrs.get('class', '').split():
            self.in_article = True
        if self.in_article and tag == 'h2':
            self.in_heading = True
        if self.in_heading and tag == 'a':
            self.links.append(attrs['href'])
        if tag == 'a' and attrs.get('rel') == 'next':
            self.next = attrs['href']

    def handle_endtag(self, tag):
        if tag == 'h2': self.in_heading = False
        if tag == 'article': self.in_article = False


class ContainParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.contain = False
        self.images = []
        self.all_images = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'div' and 'list-thumbnails' in attrs.get('class', '').split():
            self.contain = attrs.get('data-fit') == 'contain'
        if tag == 'img':
            self.all_images.append(attrs)
            if self.contain:
                self.images.append(attrs)

    def handle_endtag(self, tag):
        if tag == 'div': self.contain = False



class SummaryParser(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.rows, self.meta, self.schemas = {}, {}, []
        self.row = self.json = None
        self.heading = self.summary = self.paragraph = False
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'meta':
            self.meta[attrs.get('name', attrs.get('property', ''))] = attrs.get('content', '')
        if tag == 'script' and attrs.get('type') == 'application/ld+json':
            self.json = ''
        if tag == 'article' and 'post-row' in attrs.get('class', '').split():
            self.row = {'href': None, 'summary': ''}
        if self.row is not None:
            if tag == 'h2': self.heading = True
            if self.heading and tag == 'a': self.row['href'] = attrs.get('href')
            if tag == 'div' and 'row-summary' in attrs.get('class', '').split(): self.summary = True
            if self.summary and tag == 'p': self.paragraph = True

    def handle_data(self, data):
        if self.json is not None: self.json += data
        if self.row is not None and self.paragraph: self.row['summary'] += data

    def handle_endtag(self, tag):
        if tag == 'script' and self.json is not None:
            self.schemas.append(json.loads(self.json))
            self.json = None
        if tag == 'h2': self.heading = False
        if tag == 'p': self.paragraph = False
        if tag == 'article' and self.row is not None:
            self.rows[self.row['href']] = self.row['summary'].strip()
            self.row = None
            self.summary = False


def check(destination=None):
    root = Path(__file__).resolve().parent.parent
    with tempfile.TemporaryDirectory(prefix='12lab-pagination-') as temporary:
        content = Path(temporary) / 'content'
        output = Path(destination).resolve() if destination else Path(temporary) / 'public'
        expected = []
        long_summary = ('这段列表摘要说明文章覆盖的业务问题、案例边界和阅读收益，让读者先判断内容是否适合自己。'
                        '正文会逐步梳理数据口径、展示计算过程，并用可复核的示例解释常见错误。'
                        '摘要独立于搜索引擎描述保存，不能因为页面宽度变化而被省略、截断或替换；'
                        '不同栏目共用同一套列表模板，短摘要和没有填写摘要的旧文章也应保持正常展示。')
        short_summary = '短摘要仍应完整显示。'
        for section, title in [('topics', '测试专题'), ('topics/example', '章节分页测试')]:
            directory = content / section
            directory.mkdir(parents=True, exist_ok=True)
            (directory / '_index.md').write_text(f'---\ntitle: "{title}"\ndescription: "仅用于临时分页验收"\n---\n')
        for i in range(1, 44):
            section = ('blog', 'weekly', 'topics/example')[i % 3]
            name = f'{i:03d}'
            article = content / section / name / 'index.md'
            article.parent.mkdir(parents=True, exist_ok=True)
            article.write_text(f'---\ntitle: "测试文章 {i}"\nslug: "{name}"\ndate: 2020-{((i-1)//28)+1:02d}-{((i-1)%28)+1:02d}\nweight: {i}\ndescription: "分页测试文章"\n---\n测试正文。\n')
            if i == 42:
                article.write_text(article.read_text().replace('description:', f'summary: >-\n  {long_summary}\ndescription:'))
            elif i == 41:
                article.write_text(article.read_text().replace('description:', f'summary: "{short_summary}"\ndescription:'))
            if i in (41, 42, 43):
                for image in range(1, 5):
                    shutil.copy(root / 'assets/images/avatar-wangye.png', article.parent / f'photo-{image}.png')
                # Each selection route gets a real cover; the other images stay
                # portrait sources so a single-preview cap cannot hide cropping.
                def chunk(name, data):
                    return struct.pack('>I', len(data)) + name + data + struct.pack('>I', zlib.crc32(name + data))
                banner = b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', 900, 383, 8, 2, 0, 0, 0))
                banner += chunk(b'IDAT', zlib.compress((b'\0' + b'\x65\x7d\x96' * 900) * 383)) + chunk(b'IEND', b'')
                selected = {41: 2, 42: 3, 43: 1}[i]
                (article.parent / f'photo-{selected}.png').write_bytes(banner)
                if i == 42:
                    article.write_text(article.read_text().replace('weight:', 'images: ["photo-3.png", "photo-1.png"]\nweight:'))
                if i == 41:
                    article.write_text(article.read_text().replace('weight:', 'thumbnailFit: contain\ncover: "photo-2.png"\nimages: ["photo-3.png"]\nweight:'))
                with article.open('a') as fixture:
                    fixture.write('\n![正文竖图](photo-4.png)\n')
            expected.insert(0, f'/{section}/{name}/')
        for name, metadata in [('future', 'date: 2999-01-01'), ('draft', 'date: 2020-02-01\ndraft: true')]:
            article = content / 'blog' / name / 'index.md'
            article.parent.mkdir(parents=True)
            article.write_text(f'---\ntitle: "不应发布"\nslug: {name}\n{metadata}\n---\n')
        subprocess.run(['hugo', '--gc', '--minify', '--contentDir', str(content), '--destination', str(output)], cwd=root, check=True, capture_output=True)
        first_page = (output / 'index.html').read_text()
        assert first_page.count('class=list-thumbnails') + first_page.count('class="list-thumbnails"') == 3
        assert '--thumbnail-count' not in first_page, 'A single cover must not retain the multi-image layout variable'
        summaries = SummaryParser(first_page)
        assert summaries.rows['/blog/042/'] == long_summary, 'The list must render the complete explicit summary, not the SEO description'
        assert summaries.rows['/topics/example/041/'] == short_summary, 'Short explicit summaries must remain valid'
        assert summaries.rows['/weekly/043/'] == '分页测试文章', 'Missing summaries must fall back to description, not an automatic body excerpt'
        for route in ['/blog/042/', '/topics/example/041/', '/weekly/043/']:
            detail_head = SummaryParser((output / route.lstrip('/') / 'index.html').read_text())
            for field in ['description', 'og:description', 'twitter:description']:
                assert detail_head.meta[field] == '分页测试文章', f'{route}: {field} must retain the independent SEO description'
            schema = next(item for item in detail_head.schemas if item.get('@type') == 'Article')
            assert schema['description'] == '分页测试文章', f'{route}: Article schema must retain the independent SEO description'
        print('ok    summaries: complete explicit text, short-summary support, description fallback and independent SEO metadata')
        contained = ContainParser()
        contained.feed(first_page)
        assert len(contained.images) == 3, 'Each of the three selection routes must show exactly one cover'
        expected_covers = ['/weekly/043/photo-1_', '/blog/042/photo-3_', '/topics/example/041/photo-2_']
        for picture, expected_cover in zip(contained.images, expected_covers):
            assert expected_cover in picture['src'], f'Cover priority selected {picture["src"]}, expected {expected_cover}'
            assert (int(picture['width']), int(picture['height'])) == (540, 230), '900x383 cover must produce a 540x230 preview'
            widths = [int(candidate.strip().split()[1][:-1]) for candidate in picture['srcset'].split(',')]
            assert widths == [540, 900], 'A single cover must retain medium and original-width candidates'
        print('ok    thumbnails: cover over images, first explicit image, bundle discovery; exactly one cover per row')
        print('ok    900x383 covers: 540x230 previews, 540/900 responsive widths')
        assert 'pagination-gap' in first_page, 'Long pagination should collapse middle pages'
        assert 'home-feed.min.' not in first_page, 'Mobile must use the same numbered pagination'
        cover_detail = (output / 'topics/example/041/index.html').read_text()
        assert '/topics/example/041/photo-2_hu_' in cover_detail, 'Bundle cover must resolve inside its article'
        detail = ContainParser()
        detail.feed(cover_detail)
        portrait = next(picture for picture in detail.all_images if '/photo-4_hu_' in picture['src'])
        natural_width, natural_height = struct.unpack('>II', (root / 'assets/images/avatar-wangye.png').read_bytes()[16:24])
        assert natural_height > natural_width, 'The body-picture fixture must remain portrait'
        assert abs(int(portrait['height']) - int(portrait['width']) * natural_height / natural_width) <= 1, 'A portrait body image must retain its natural proportions'
        print('ok    body images: portrait source keeps its independent original proportions')
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
        chapters = [f'/topics/example/{i:03d}/' for i in range(1, 44) if i % 3 == 2]
        combined = []
        for page, count in [(1, 10), (2, 4)]:
            html = output / ('topics/example/index.html' if page == 1 else f'topics/example/page/{page}/index.html')
            parser = TopicParser()
            parser.feed(html.read_text())
            assert len(parser.links) == count, (page, parser.links)
            assert parser.links == chapters[(page - 1) * 10:page * 10], 'Incorrect topic weight order'
            assert parser.next == ('/topics/example/page/2/' if page == 1 else None), parser.next
            combined.extend(parser.links)
        assert len(set(combined)) == 14
        print('ok    topic pagination fixture: 10 + 4 chapters, weight order, no duplicates')


if __name__ == '__main__':
    arguments = argparse.ArgumentParser()
    arguments.add_argument('--destination')
    check(arguments.parse_args().destination)
