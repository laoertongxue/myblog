#!/usr/bin/env bash
# Repo-owned pre-push check. Mirrors the CI build (deploy.yml) and asserts the
# invariants this site has actually regressed on. Run with: make check
#
# Builds into .hugo-check/ rather than public/ so an existing local public/
# (often a `hugo server` dump) is never clobbered.
#
# The last step runs the real browser checks in scripts/check-*.js through
# scripts/run-browser-checks.mjs. BROWSER_CHECKS=auto (default) runs them when
# playwright is installed and prints an explicit skip otherwise,
# BROWSER_CHECKS=require (CI) fails instead of skipping, BROWSER_CHECKS=0 skips.
set -euo pipefail

cd "$(dirname "$0")/.."
OUT=${OUT:-.hugo-check}
# Validate published routes against Hugo's current inventory, so intentional
# topic cleanup never requires weakening an arbitrary total-page floor.

fail() { printf 'FAIL  %s\n' "$1" >&2; exit 1; }
ok()   { printf 'ok    %s\n' "$1"; }

printf '==> hugo --gc --minify (same flags as CI)\n'
# Only disposable build destinations inside this repository may be cleared.
case "$OUT" in .hugo-check|public) ;; *) fail "unsupported build output: $OUT" ;; esac
[ ! -L "$OUT" ] || fail "build output must not be a symlink"
rm -rf "$OUT"
hugo --gc --minify --destination "$OUT" >/dev/null

[ -d "$OUT" ] && [ -n "$(ls -A "$OUT")" ] || fail "build output $OUT/ is empty"

PAGES=$(find "$OUT" -name '*.html' | wc -l | tr -d ' ')
ok "built $PAGES pages"
python3 scripts/check-published-pages.py "$OUT"

python3 scripts/check-content.py

if grep -rq '0001-01-01' "$OUT"; then
  fail "a page publishes a 0001-01-01 date - a dated content type is missing front matter date"
fi
ok "no year-1 dates"

if grep -rq 'Z0[0-9]:[0-9][0-9]' "$OUT"; then
  fail "invalid Go time layout found (Z08:00 is not a layout token; use -07:00)"
fi
ok "date layout tokens valid"

if grep -rq 'http://localhost' "$OUT"; then
  fail "output contains localhost - baseURL was not applied to this build"
fi
ok "no localhost URLs"

# Go's html/template writes this literal when an action sits in a position it
# cannot escape - in practice `{{ with partial ... }}attr="{{ . }}"{{ end }}`
# in attribute-name position, which fires on every empty partial result and
# replaced the whole aria-current attribute on non-current nav links.
if grep -rqi 'zgotmplz' "$OUT"; then
  fail "template escaping placeholder (zgotmplz) leaked into the output - bind the partial result to a variable before using it in an attribute"
fi
ok "no template escaping placeholders"

# R7: the avatar must go through the image pipeline. If it drifts back to
# static/, [imaging] silently stops doing anything.
IMAGES=$(find "$OUT/images" -name '*_hu_*' 2>/dev/null | wc -l | tr -d ' ')
[ "$IMAGES" -ge 1 ] || fail "no processed images in output - [imaging] pipeline is inert"
ok "$IMAGES processed image(s) emitted"

python3 scripts/check-home-pagination.py
python3 scripts/check-static-output.py "$OUT"
python3 scripts/check-seo.py "$OUT"
python3 scripts/check-agent-series.py "$OUT"

python3 scripts/check-content-workflow.py
python3 scripts/check-deploy-release.py

# Real browser checks against the build that was just produced. They are never
# silently skipped: with BROWSER_CHECKS=require (CI) a missing playwright is a
# failure, and the "auto" default always prints which of the two happened.
case "${BROWSER_CHECKS:-auto}" in
  0|off|false)
    printf 'skip  browser checks (BROWSER_CHECKS=%s)\n' "${BROWSER_CHECKS}"
    ;;
  *)
    if node -e "require.resolve('playwright')" >/dev/null 2>&1; then
      node scripts/run-browser-checks.mjs --dir "$OUT"
    elif [ "${BROWSER_CHECKS}" = "require" ]; then
      fail "BROWSER_CHECKS=require but playwright is not installed - run: npm ci && npx playwright install chromium"
    else
      printf 'skip  browser checks: playwright not installed (npm ci && npx playwright install chromium)\n'
    fi
    ;;
esac

printf '\nAll checks passed.\n'
