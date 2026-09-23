#!/usr/bin/env bash
# Repo-owned pre-push check. Mirrors the CI build (deploy.yml) and asserts the
# invariants this site has actually regressed on. Run with: make check
#
# Builds into .hugo-check/ rather than public/ so an existing local public/
# (often a `hugo server` dump) is never clobbered.
set -euo pipefail

cd "$(dirname "$0")/.."
OUT=${OUT:-.hugo-check}
# Floor on generated .html files, not on Hugo's "Pages" metric (55 Pages = 34
# HTML + 21 XML/RSS + 1 JSON here). Only meant to catch catastrophic loss.
MIN_PAGES=${MIN_PAGES:-30}

fail() { printf 'FAIL  %s\n' "$1" >&2; exit 1; }
ok()   { printf 'ok    %s\n' "$1"; }

printf '==> hugo --gc --minify (same flags as CI)\n'
rm -rf "$OUT"
hugo --gc --minify --destination "$OUT" >/dev/null

[ -d "$OUT" ] && [ -n "$(ls -A "$OUT")" ] || fail "build output $OUT/ is empty"

PAGES=$(find "$OUT" -name '*.html' | wc -l | tr -d ' ')
[ "$PAGES" -ge "$MIN_PAGES" ] || fail "only $PAGES pages built (floor $MIN_PAGES)"
ok "built $PAGES pages"

# R2: every blog post must pin its slug. [permalinks] blog = "/blog/:slug/"
# falls back to the title, so an unslugged post gets a title-derived URL and a
# later title edit silently breaks the published link.
missing=""
for dir in content/blog/*/; do
  [ -f "$dir/index.md" ] || continue
  name=$(basename "$dir")
  grep -Eq "^slug: *\"?'?${name}\"?'?$" "$dir/index.md" || missing="$missing $name"
done
[ -z "$missing" ] || fail "blog posts without a matching slug:$missing"
ok "every blog post pins its slug"

# R4: an Article schema built from a page with no `date` publishes year 1, and
# head-end.html now drops the schema instead - a silent SEO loss. Assert the
# date on the content side, where the real invariant lives.
nodate=""
for f in $(find content/blog content/weekly content/topics -name 'index.md' ! -name '_index.md' 2>/dev/null | sort); do
  grep -Eq '^date: *[0-9]{4}-[0-9]{2}-[0-9]{2}' "$f" || nodate="$nodate $f"
done
[ -z "$nodate" ] || fail "article pages without a valid date:$nodate"
ok "every article page declares a date"

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

# R7: the avatar must go through the image pipeline. If it drifts back to
# static/, [imaging] silently stops doing anything.
IMAGES=$(find "$OUT/images" -name '*_hu_*' 2>/dev/null | wc -l | tr -d ' ')
[ "$IMAGES" -ge 1 ] || fail "no processed images in output - [imaging] pipeline is inert"
ok "$IMAGES processed image(s) emitted"

python3 scripts/check-home-pagination.py
python3 scripts/check-static-output.py "$OUT"

printf '\nAll checks passed.\n'
