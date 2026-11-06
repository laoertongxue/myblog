#!/usr/bin/env python3
"""Generate crawlable Hugo lessons from the preserved published course payload."""
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
course = json.loads((ROOT / 'data/forecast/course.json').read_text())
ids = {lesson['id'] for lesson in course}
assert len(ids) == len(course)
check = '--check' in sys.argv

def rewrite(match):
    attribute, value = match.groups()
    if value.startswith('#unit-'):
        key = value[6:]
        assert key in ids, value
        value = f'/forecast/{key}/'
    elif not value.startswith(('#', '/', 'http:', 'https:', 'mailto:', 'data:')):
        assert '..' not in value.split('/'), value
        value = '/forecast/' + value
    return f'{attribute}="{value}"'

for i, lesson in enumerate(course):
    assert re.fullmatch('[a-z][a-z0-9-]+', lesson['id'])
    body = re.sub(r'(href|src)="([^"]+)"', rewrite, lesson['html'])
    body = body.replace('不修改12lab.cn。', '课程与博客预测专题分别组织，内容与完成范围以各自页面为准。')
    # Each page has one descriptive H1; retain all original heading anchors.
    body = re.sub(r'<(/?)h1(?=[\s>])', r'<\1h2', body)
    paragraphs = re.findall(r'<p(?:\s[^>]*)?>(.*?)</p>', body, re.S)
    text = next((re.sub(r'\s+', ' ', html.unescape(re.sub('<[^>]+>', '', p))).strip()
                 for p in paragraphs if len(re.sub('<[^>]+>', '', p)) > 30 and 'download' not in p), '')
    description = f"{lesson['title']}：{text[:120]}" if text else f"预测课堂的{lesson['group']}模块：{lesson['title']}。通过教学模拟、逐步讲解和练习理解方法及适用边界。"
    metadata = dict(title=lesson['title'], description=description, type='forecast', unit=lesson['id'], weight=i+1, outputs=['HTML'])
    result = json.dumps(metadata, ensure_ascii=False, indent=2) + '\n\n' + body.rstrip() + '\n'
    path = ROOT / 'content/forecast' / lesson['id'] / 'index.md'
    if check:
        assert path.read_text() == result, f'{path}: run python3 scripts/generate-forecast.py'
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(result)
print(f'ok    forecast: {len(course)} generated lessons match published source')
