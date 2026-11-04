"""Daily regression: immutable published test artifact plus development scoring.

Never reads sealed/ or invokes generate/finalize. Test results are hashed as an
opaque artifact, not parsed or scored. Intentional baseline changes need review.
"""
import hashlib
import json
from pathlib import Path
import run

ROOT = Path(__file__).resolve().parent
# Verified against committed bytes at 6e78881ec5cace564c101ca4dca85cb58254dfae.
FROZEN_RECEIPT_SHA256 = '273f1a5c13363109660030e3df6c618d601759c3db08c0b65ea6ea0c3f469d0e'
PUBLISHED_TEST_SHA256 = 'cb23f87f5c63145f264845836259a7d0c313c6dfe73f58d1ae0bfa69fa4eeb0d'
# Explicit allowlist: never traverse all receipt paths, which include sealed CSVs.
DEVELOPMENT_FILES = (
    'baseline.py', 'generate.py', 'run.py', 'policy.json',
    'data/hewei-development.csv', 'data/apparel-development.csv',
)


def require_digest(path, expected):
    if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
        raise ValueError(f'integrity mismatch: {path.name}; review required, do not auto-refresh hashes')


def check(root=ROOT):
    root = Path(root)
    require_digest(root / 'freeze.json', FROZEN_RECEIPT_SHA256)
    require_digest(root / 'results/test.json', PUBLISHED_TEST_SHA256)
    receipt = json.loads((root / 'freeze.json').read_text(encoding='utf-8'))
    if receipt['policy'] != run.POLICY:
        raise ValueError('frozen policy mismatch')
    for relative in DEVELOPMENT_FILES:
        require_digest(root / relative, receipt['sha256'][relative])
    for case in ('hewei', 'apparel'):
        rows = run.read_csv(root / f'data/{case}-development.csv', 1, 140, {'train', 'validation'})
        actual = run.score(rows, 113, 140)
        expected = json.loads((root / f'results/{case}-validation.json').read_text(encoding='utf-8'))
        if actual != expected:
            raise ValueError(f'{case} development validation regression')
    print('ok    D9: published test artifact and frozen development sources intact; '
          '2 validation regressions passed; no sealed labels read or test scores recomputed')


if __name__ == '__main__':
    check()
