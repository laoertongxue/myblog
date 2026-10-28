#!/usr/bin/env python3
"""Regression check for the long-form topic series: expectations are derived from
content/ and from the templates, never hardcoded.

The series is discovered - chapter order and titles come from the front matter
`weight`/`title`, the expected pictures come from each chapter bundle, the
expected rendered size comes from the source picture (read out of the file
header) plus the rule in layouts/_markup/render-image.html, and the table /
reference counts come from the Markdown. Adding a chapter, re-exporting a
picture or renaming a heading therefore cannot fail this check; a lost TOC
entry, a cropped picture, a missing original, a wrong chapter order, a lost
table or a broken reference still can.
"""
from html.parser import HTMLParser
import json
import re
import struct
from pathlib import Path
import sys
from urllib.parse import unquote as url_unquote, urlsplit
from xml.etree import ElementTree as ET

TOPIC_SOURCE = Path('content/topics/agent-engineering')
TOPIC_ROUTE = '/topics/agent-engineering/'
REMOVED_ROUTE = Path('topics/layout-test')
# layouts/_partials/lab/thumbnails.html shows one article cover.
PREVIEW_LIMIT = 1


def unquote(value):
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in '"\'':
        return value[1:-1]
    return value


def front_matter(path):
    """Minimal YAML front matter reader for the scalar fields used here."""
    match = re.match(r'^---\n(.*?)\n---\n', path.read_text(encoding='utf-8'), re.S)
    if not match:
        raise ValueError(f'{path}: no YAML front matter')
    data, key = {}, None
    for line in match.group(1).splitlines():
        if not line.strip():
            continue
        if line.lstrip().startswith('- ') and key:
            data.setdefault(key, []).append(unquote(line.lstrip()[2:]))
            continue
        name, _, value = line.partition(':')
        key = name.strip()
        value = value.strip()
        if not value:
            data[key] = []
        elif value.startswith('['):
            data[key] = [unquote(item) for item in value[1:-1].split(',') if item.strip()]
        else:
            data[key] = unquote(value)
    return data


def image_size(path):
    """Intrinsic size of PNG / JPEG / WebP / SVG without third-party libraries."""
    data = path.read_bytes()
    if data.startswith(b'\x89PNG\r\n\x1a\n'):
        return struct.unpack('>II', data[16:24])
    if data[:2] == b'\xff\xd8':
        index = 2
        while index + 9 < len(data):
            if data[index] != 0xFF:
                index += 1
                continue
            marker = data[index + 1]
            if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):
                height, width = struct.unpack('>HH', data[index + 5:index + 9])
                return width, height
            if marker in (0xD8, 0x01) or 0xD0 <= marker <= 0xD7:
                index += 2
                continue
            index += 2 + struct.unpack('>H', data[index + 2:index + 4])[0]
        raise ValueError(f'{path}: unsupported JPEG layout')
    if data.startswith(b'RIFF') and data[8:12] == b'WEBP':
        chunk = data[12:16]
        if chunk == b'VP8X':
            return int.from_bytes(data[24:27], 'little') + 1, int.from_bytes(data[27:30], 'little') + 1
        if chunk == b'VP8 ':
            return int.from_bytes(data[26:28], 'little') & 0x3FFF, int.from_bytes(data[28:30], 'little') & 0x3FFF
        if chunk == b'VP8L':
            bits = int.from_bytes(data[21:25], 'little')
            return (bits & 0x3FFF) + 1, ((bits >> 14) & 0x3FFF) + 1
        raise ValueError(f'{path}: unsupported WebP variant')
    match = re.search(rb'viewBox=["\']([^"\']+)["\']', data[:2000])
    if match:
        parts = re.split(rb'[,\s]+', match.group(1).strip())
        if len(parts) == 4:
            return int(float(parts[2])), int(float(parts[3]))
    raise ValueError(f'{path}: cannot determine the intrinsic size (add support here if this format is intentional)')


def markdown_table_count(path):
    return len(re.findall(r'^\|[\s|:-]+\|\s*$', path.read_text(encoding='utf-8'), re.M))


def normalized(html):
    """Quote unquoted attribute values so the structural regexes below also work
    on `hugo --minify` output, which writes class=toc-panel / href=/blog/."""
    return re.sub(r'([\w-]+)=(?!["\'])([^\s">]+)', r'\1="\2"', html)


class Body(HTMLParser):
    """Ordered h2/h3 headings, pictures and tables of one rendered article."""

    def __init__(self, path):
        super().__init__()
        source = path.read_text(encoding='utf-8')
        self.text = normalized(source)
        self.in_prose = False
        self.depth = 0
        self.section = None
        self.heading = None
        self.heading_id = None
        self.pictures = []
        self.headings = []
        self.tables = 0
        self.ids = []
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        classes = attributes.get('class', '').split()
        if tag == 'div' and 'prose' in classes:
            self.in_prose = True
            self.depth = 1
            return
        if not self.in_prose:
            return
        if tag == 'div':
            self.depth += 1
        if attributes.get('id'):
            self.ids.append(attributes['id'])
        if tag in ('h2', 'h3'):
            self.heading = tag
            self.heading_id = attributes.get('id')
            self.section = ''
        elif tag == 'img':
            self.pictures.append({
                'section': self.section,
                'src': attributes.get('src'),
                'srcset': attributes.get('srcset', ''),
                'width': attributes.get('width'),
                'height': attributes.get('height'),
                'alt': attributes.get('alt'),
            })
        elif tag == 'table':
            self.tables += 1

    def handle_data(self, data):
        if self.in_prose and self.heading:
            self.section = (self.section or '') + data

    def handle_endtag(self, tag):
        if tag in ('h2', 'h3') and self.heading:
            self.headings.append({'level': int(self.heading[1]), 'text': (self.section or '').strip(), 'id': self.heading_id})
            self.heading = None
        elif self.in_prose and tag == 'div':
            self.depth -= 1
            if self.depth <= 0:
                self.in_prose = False


class Listing(HTMLParser):
    """Rows of a listing page: link, title, preview mode and preview pictures."""

    def __init__(self, path):
        super().__init__()
        self.rows = []
        self.row = None
        self.heading = False
        self.feed(path.read_text(encoding='utf-8'))

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        classes = attributes.get('class', '').split()
        if tag == 'article' and 'post-row' in classes:
            self.row = {'url': None, 'title': None, 'fit': None, 'pictures': []}
            self.rows.append(self.row)
        if self.row is None:
            return
        if tag == 'h2':
            self.heading = True
        elif tag == 'a' and self.heading and self.row['url'] is None:
            self.row['url'] = attributes.get('href')
        elif tag == 'div' and 'list-thumbnails' in classes:
            self.row['fit'] = attributes.get('data-fit')
        elif tag == 'img':
            self.row['pictures'].append({
                'src': attributes.get('src'),
                'srcset': attributes.get('srcset', ''),
                'width': attributes.get('width'),
                'height': attributes.get('height'),
            })

    def handle_data(self, data):
        if self.row is not None and self.heading and self.row['title'] is None:
            self.row['title'] = data.strip()

    def handle_endtag(self, tag):
        if tag == 'h2':
            self.heading = False
        elif tag == 'article':
            self.row = None


def descriptors(picture):
    return {int(candidate.strip().split()[1].rstrip('w')) for candidate in picture['srcset'].split(',') if candidate.strip()}


def check(output='.hugo-check'):
    root = Path(output)
    assert TOPIC_SOURCE.is_dir(), f'{TOPIC_SOURCE} is missing'

    chapters = []
    for directory in sorted(TOPIC_SOURCE.iterdir()):
        source = directory / 'index.md'
        if not source.is_file():
            continue
        markdown = source.read_text(encoding='utf-8')
        meta = front_matter(source)
        bundle = {item.name: item for item in sorted((directory / 'assets').glob('*')) if item.is_file()}
        # Body pictures and their order come from the Markdown; the front matter
        # `images:` list selects the *list previews* only (see docs/列表缩略图.md).
        body = [Path(reference).name for reference in re.findall(r'!\[[^\]]*\]\(([^)\s]+)', markdown)]
        declared = [Path(reference).name for reference in (meta.get('images') or [])]
        cover = [Path(meta['cover']).name] if meta.get('cover') else []
        for name in cover + declared:
            if name not in bundle:
                raise ValueError(f'{source}: preview image {name} is not in the bundle')
        for name in body:
            if name not in bundle:
                raise ValueError(f'{source}: body picture {name} is not in the bundle')
        # No orphan bundle pictures: every file is either shown in the article or
        # declared for the list previews (docs/列表缩略图.md). This is what still
        # catches an accidentally deleted body picture line when previews are
        # declared explicitly.
        for name in bundle:
            if name not in body and name not in declared and name not in cover:
                raise ValueError(f'{source}: {name} is in the bundle but neither rendered nor declared as a preview')
        chapters.append({
            'route': f'{TOPIC_ROUTE}{directory.name}/',
            'title': meta.get('title', ''),
            'weight': int(meta.get('weight', 0)),
            'fit': meta.get('thumbnailFit', ''),
            'pictures': body,
            'previews': cover or declared[:1] or list(bundle)[:1],
            'bundle': bundle,
            'tables': markdown_table_count(source),
        })
    chapters.sort(key=lambda chapter: (chapter['weight'], chapter['route']))
    assert len(chapters) >= 2, 'the series must keep at least two chapters'
    routes = [chapter['route'] for chapter in chapters]

    for chapter in chapters:
        page = root / chapter['route'].lstrip('/') / 'index.html'
        assert page.is_file(), f'{chapter["route"]}: page not generated'
        body = Body(page)
        assert chapter['title'], f'{chapter["route"]}: front matter has no title'
        assert '测试专题' not in body.text and 'test-notice' not in body.text and 'test-label' not in body.text, f'{chapter["route"]}: test markers remain'

        # TOC: one entry per body heading (levels 2-3, as configured in
        # hugo.toml), and every entry must resolve to a real id in the page -
        # the theme puts those ids on its heading-anchor spans, not on the h2.
        toc = re.search(r'<div class="toc-panel">(.*?)</details>', body.text, re.S)
        assert toc, f'{chapter["route"]}: no table of contents rendered'
        toc_hrefs = re.findall(r'href="(#[^"]+)"', toc.group(1))
        anchors = [heading for heading in body.headings if heading['level'] in (2, 3)]
        assert len(toc_hrefs) == len(anchors), f'{chapter["route"]}: TOC lists {len(toc_hrefs)} of {len(anchors)} headings'
        for href in toc_hrefs:
            assert href[1:] in body.ids, f'{chapter["route"]}: TOC entry {href} has no target in the page'

        # Pictures: the bundle pictures, once each, in their own section, shown
        # at min(natural width, 1440) with the responsive candidates that
        # layouts/_markup/render-image.html promises.
        rendered = [picture for picture in body.pictures if picture['src']]
        assert len(rendered) == len(chapter['pictures']), f'{chapter["route"]}: rendered {len(rendered)} of {len(chapter["pictures"])} bundle pictures'
        assert len({picture['src'] for picture in rendered}) == len(rendered), f'{chapter["route"]}: a picture is rendered twice'
        assert rendered, f'{chapter["route"]}: article cover is missing'
        assert image_size(chapter['bundle'][chapter['pictures'][0]]) == (900, 383), f'{chapter["route"]}: first picture must be a 900x383 cover'
        sections = [picture['section'] for picture in rendered[1:]]
        assert len(set(sections)) == len(sections), f'{chapter["route"]}: two body pictures share one section'
        for picture, name in zip(rendered, chapter['pictures']):
            source = chapter['bundle'][name]
            natural_width, natural_height = image_size(source)
            expected_width = min(natural_width, 1440)
            expected_height = round(natural_height * expected_width / natural_width)
            base = name.rsplit('.', 1)[0]
            src = url_unquote(picture['src'])
            assert src.startswith(f'{chapter["route"]}assets/'), f'{chapter["route"]}: {src} is not served from its own bundle'
            assert base in src, f'{chapter["route"]}: expected {name}, page shows {src}'
            assert re.search(rf'{re.escape(base)}_hu_[0-9a-f]+\.webp$', src), f'{chapter["route"]}: {src} is not a fingerprinted WebP derivative of {name}'
            assert picture['alt'], f'{chapter["route"]}: {name} has no alt text'
            assert int(picture['width']) == expected_width, f'{chapter["route"]}: {name} renders {picture["width"]}px wide, expected {expected_width}px from {natural_width}x{natural_height}'
            assert abs(int(picture['height']) - expected_height) <= 1, f'{chapter["route"]}: {name} renders {picture["width"]}x{picture["height"]} for a {natural_width}x{natural_height} source (aspect ratio changed)'
            expected_descriptors = {width for width in (480, 960) if width < expected_width} | {expected_width}
            assert descriptors(picture) == expected_descriptors, f'{chapter["route"]}: {name} srcset is {sorted(descriptors(picture))}, expected {sorted(expected_descriptors)}'
            original = root / chapter['route'].lstrip('/') / 'assets' / name
            assert original.is_file(), f'{chapter["route"]}: original {name} missing from the output'
            assert original.read_bytes() == source.read_bytes(), f'{chapter["route"]}: original {name} was rewritten by the build'

        # Tables and in-page references, counted from the Markdown.
        assert body.tables == chapter['tables'], f'{chapter["route"]}: {body.tables} table(s) rendered, {chapter["tables"]} in the source'
        reference_ids = [identifier for identifier in body.ids if re.fullmatch(r'ref-\d+', identifier)]
        linked = set(re.findall(r'href="#(ref-\d+)"', body.text))
        assert linked == set(reference_ids), f'{chapter["route"]}: references {sorted(linked)} do not match ids {sorted(reference_ids)}'

        # Chapter navigation order and the previous/next pager, from weight order.
        navigation = re.search(r'<section class="chapter-navigation">.*?</section>', body.text, re.S)
        assert navigation, f'{chapter["route"]}: no chapter navigation'
        nav = re.search(r'<nav aria-label="专题章节">(.*?)</nav>', navigation.group(0), re.S)
        assert nav, f'{chapter["route"]}: empty chapter navigation'
        nav_hrefs = re.findall(r'href="([^"]+)"', nav.group(1))
        assert nav_hrefs == routes, f'{chapter["route"]}: chapter navigation is {nav_hrefs}, expected weight order {routes}'
        index = routes.index(chapter['route'])
        neighbours = sorted(routes[i] for i in (index - 1, index + 1) if 0 <= i < len(routes))
        pager = re.search(r'<nav class="article-pager"[^>]*>(.*?)</nav>', body.text, re.S)
        pager_hrefs = sorted(re.findall(r'href="([^"]+)"', pager.group(1))) if pager else []
        assert pager_hrefs == neighbours, f'{chapter["route"]}: pager is {pager_hrefs}, expected {neighbours}'

    # Topic listing: order and titles follow the front matter; every preview
    # preserves its original proportions inside the site's listing frame.
    listing = Listing(root / TOPIC_ROUTE.lstrip('/') / 'index.html')
    assert [row['url'] for row in listing.rows] == routes, f'{TOPIC_ROUTE}: listing order {[row["url"] for row in listing.rows]} does not follow weight order {routes}'
    for row, chapter in zip(listing.rows, chapters):
        assert row['title'] == chapter['title'], f'{chapter["route"]}: listing title {row["title"]!r} differs from front matter'
        assert row['fit'] == 'contain', f'{chapter["route"]}: preview mode must preserve complete pictures'
        previews = min(PREVIEW_LIMIT, len(chapter['previews']))
        assert len(row['pictures']) == previews, f'{chapter["route"]}: {len(row["pictures"])} preview(s), expected {previews}'
        for picture, name in zip(row['pictures'], chapter['previews'][:previews]):
            natural_width, natural_height = image_size(chapter['bundle'][name])
            assert (natural_width, natural_height) == (900, 383), f'{chapter["route"]}: list cover {name} must be 900x383'
            assert name == chapter['pictures'][0], f'{chapter["route"]}: list cover must be the first article picture'
            assert name.rsplit('.', 1)[0] in picture['src'], f'{chapter["route"]}: preview {picture["src"]} is not {name}'
            # The picture keeps the source ratio in its intrinsic attributes
            # and in every built candidate; CSS controls the listing frame.
            reserved = int(picture['width']) / int(picture['height'])
            assert abs(reserved - natural_width / natural_height) <= 0.01, \
                f'{chapter["route"]}: contain preview {name} reserves {picture["width"]}x{picture["height"]} for a {natural_width}x{natural_height} source'
            for candidate in picture['srcset'].split(','):
                if not candidate.strip():
                    continue
                url, descriptor = candidate.strip().split()
                assert descriptor.endswith('w'), f'{chapter["route"]}: preview srcset entry {candidate!r} is not width-described'
                width = int(descriptor.rstrip('w'))
                built = root / urlsplit(url).path.lstrip('/')
                assert built.is_file(), f'{chapter["route"]}: preview candidate {url} is missing from the output'
                variant_width, variant_height = image_size(built)
                assert variant_width == width, f'{chapter["route"]}: preview candidate {url} is {variant_width}px wide but declares {width}w'
                assert abs(variant_height - natural_height * width / natural_width) <= 1, \
                    f'{chapter["route"]}: preview candidate {url} is {variant_width}x{variant_height}, cropped from {natural_width}x{natural_height}'

    for listing_route in ('/blog/', '/weekly/'):
        page = Listing(root / listing_route.lstrip('/') / 'index.html')
        for row in page.rows:
            if not row['pictures']:
                continue
            assert row['fit'] == 'contain', f'{listing_route}: default previews must preserve complete pictures'
            assert len(row['pictures']) == PREVIEW_LIMIT, f'{listing_route}: each article must show one cover'
            for picture in row['pictures']:
                if not picture['srcset']:
                    continue  # SVG previews keep their original vector source.
                source = root / urlsplit(picture['src']).path.lstrip('/')
                intrinsic = image_size(source)
                assert (int(picture['width']), int(picture['height'])) == intrinsic, \
                    f'{listing_route}: thumbnail dimensions do not match the served image'

    # Discovery outputs.
    indices = list(root.glob('search-index.*.json'))
    assert len(indices) == 1, 'expected exactly one fingerprinted search index'
    urls = {item['url'] for item in json.loads(indices[0].read_text())}
    assert {TOPIC_ROUTE, *routes} <= urls, 'series or articles missing from the search index'
    assert not any(str(REMOVED_ROUTE) in url for url in urls), 'removed test topic still in the search index'
    locations = {urlsplit(element.text).path for element in ET.parse(root / 'sitemap.xml').findall('.//{*}loc')}
    assert {TOPIC_ROUTE, *routes} <= locations, 'series or articles missing from the sitemap'
    for feed in ('index.xml', 'topics/index.xml', 'topics/agent-engineering/index.xml'):
        path = root / feed
        assert path.is_file(), f'{feed}: missing'
        links = {urlsplit(item.findtext('link')).path for item in ET.parse(path).findall('./channel/item')}
        assert set(routes) <= links, f'{feed}: articles missing'
    assert not (root / REMOVED_ROUTE).exists(), 'removed test topic is still generated'

    counts = ', '.join(f'{len(chapter["pictures"])} pictures' for chapter in chapters)
    print(f'ok    series: {len(chapters)} chapters in weight order ({counts}); sizes, TOC, tables, references, previews, search, sitemap and RSS all derived from content and templates')


if __name__ == '__main__':
    try:
        check(sys.argv[1] if len(sys.argv) > 1 else '.hugo-check')
    except (AssertionError, ValueError) as exc:
        sys.exit(f'FAIL  {exc}')
