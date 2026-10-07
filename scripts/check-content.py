#!/usr/bin/env python3
"""Validate Hugo-parsed metadata, supporting YAML/TOML/JSON and quoted dates."""
import csv
import io
from pathlib import Path
import subprocess
import sys


def check(source=None):
    command = ['hugo', 'list', 'all']
    if source:
        command += ['--source', str(source)]
    result = subprocess.run(command, text=True, capture_output=True, check=True)
    errors = []
    count = drafts = 0
    for row in csv.DictReader(io.StringIO(result.stdout)):
        if row['kind'] != 'page' or row['section'] not in {'blog', 'weekly', 'topics'}:
            continue
        if row['draft'] == 'true':
            drafts += 1
            continue  # Incomplete draft metadata must not block other publications.
        count += 1
        path = Path(row['path'])
        if not row['date'] or row['date'].startswith('0001-'):
            errors.append(f'{path}: published/scheduled article requires date')
        expected = path.parent.name if path.stem == 'index' else path.stem
        if row['section'] == 'blog' and row['slug'] != expected:
            errors.append(f'{path}: slug must equal {expected!r}')
    if errors:
        raise ValueError('\n'.join(errors))
    print(f'ok    parsed content: {count} published/scheduled articles; {drafts} drafts excluded from required-field checks')


if __name__ == '__main__':
    try:
        check(sys.argv[1] if len(sys.argv) > 1 else None)
    except (ValueError, subprocess.CalledProcessError) as exc:
        sys.exit(f'FAIL  {exc}\n{getattr(exc, "stderr", "")}')
