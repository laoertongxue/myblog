HUGO ?= hugo
OUT_DIR ?= .hugo-check

.PHONY: help serve build check check-browser browser-deps

help:
	@printf 'targets:\n  serve         local preview on http://localhost:1313\n  build         release build with the same flags as CI\n  check         build + assert every invariant this site has regressed on\n                (browser checks included when playwright is installed)\n  check-browser only the browser checks, against $(OUT_DIR)\n  browser-deps  install the browser check dependencies (npm + chromium)\n'

build:
	hugo --gc --minify

check:
	@./scripts/check.sh

check-browser:
	node scripts/run-browser-checks.mjs --dir $(OUT_DIR)

browser-deps:
	npm ci
	npx playwright install chromium

serve:
	$(HUGO) server
