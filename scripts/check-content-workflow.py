#!/usr/bin/env python3
"""Exercise real Hugo authoring and parsed metadata in a disposable site."""
import sys
sys.dont_write_bytecode = True
import importlib.util
from pathlib import Path
import shutil
import subprocess
import tempfile

root = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location('content_check', root / 'scripts/check-content.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
with tempfile.TemporaryDirectory(prefix='12lab-authoring-') as tmp:
    site = Path(tmp)
    (site / "content").mkdir()
    shutil.copytree(root / 'archetypes', site / 'archetypes')
    (site / 'hugo.toml').write_text('baseURL = "https://12lab.cn/"\ntimeZone = "Asia/Shanghai"\n')
    paths = ['blog/example/index.md', 'weekly/999/index.md', 'topics/example/01-start/index.md']
    for path in paths:
        result = subprocess.run(['hugo', 'new', path], cwd=site, capture_output=True, text=True)
        assert result.returncode == 0, result.stderr
        file = site / 'content' / path
        text = file.read_text()
        assert 'draft: true' in text and 'date:' in text
        if path.startswith('blog/'):
            assert "slug: 'example'" in text
        file.write_text(text.replace('draft: true', 'draft: false'))
    module.check(site)  # Includes quoted dates from all three archetypes.
    draft = site / 'content/blog/incomplete/index.md'
    draft.parent.mkdir(parents=True)
    draft.write_text('---\ntitle: "Unfinished"\ndraft: true\n---\n')
    module.check(site)
    draft.write_text('---\ntitle: "Published without date"\nslug: incomplete\ndraft: false\n---\n')
    try:
        module.check(site)
    except ValueError as exc:
        assert 'requires date' in str(exc)
    else:
        raise AssertionError('Missing publication date was accepted')
    draft.write_text('---\ntitle: "Future without slug"\ndate: 2099-01-01\n---\n')
    try:
        module.check(site)
    except ValueError as exc:
        assert 'slug' in str(exc)
    else:
        raise AssertionError('Scheduled blog without slug was accepted')
print('ok    authoring: three archetypes, quoted dates, incomplete drafts, published/scheduled metadata rejection')
