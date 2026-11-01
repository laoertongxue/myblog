#!/usr/bin/env python3
"""Prove SEO guards reject bad output, using a disposable copy of the build."""
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

source = Path(sys.argv[1] if len(sys.argv) > 1 else '.hugo-check').resolve()
checker = Path(__file__).with_name('check-seo.py').resolve()
with tempfile.TemporaryDirectory(prefix='12lab-seo-') as temporary:
    output = Path(temporary) / 'public'
    shutil.copytree(source, output)

    def reject(changes, expected):
        originals = {name: (output / name).read_bytes() for name in changes}
        try:
            for name, transform in changes.items():
                path = output / name
                path.write_text(transform(path.read_text(encoding='utf-8')), encoding='utf-8')
            result = subprocess.run([sys.executable, str(checker), str(output)], capture_output=True, text=True)
            assert result.returncode != 0 and expected in result.stderr, (expected, result.stdout, result.stderr)
        finally:
            for name, data in originals.items():
                (output / name).write_bytes(data)

    reject({'index.html': lambda text: text.replace('index, follow', 'noindex, follow')}, 'noindex page in sitemap')
    reject({'index.html': lambda text: text.replace('https://12lab.cn/', 'https://wrong.example/')}, 'canonical host')
    reject({'robots.txt': lambda text: 'User-agent: *\nDisallow: /\nSitemap: https://12lab.cn/sitemap.xml\n'}, 'robots blocks crawling')
    reject({'index.html': lambda text: text.replace('</body>', '<a href="#missing-seo-target">Broken</a></body>')}, 'broken fragment')
    reject({'sitemap.xml': lambda text: re.sub(r'<url>\s*<loc>https://12lab.cn/</loc>.*?</url>', '', text)}, 'sitemap coverage')
    article = next(path for path in (output / 'blog').glob('*/index.html') if 'rel=author' in path.read_text(encoding='utf-8') or 'rel="author"' in path.read_text(encoding='utf-8'))
    reject({article.relative_to(output).as_posix(): lambda text: re.sub(r'rel=(?:"author"|author)', '', text)}, 'author must be visible and linked')
print('ok    SEO fault injection: accidental noindex, wrong canonical host, blocked robots, broken fragments, sitemap omission and invisible author all rejected')
