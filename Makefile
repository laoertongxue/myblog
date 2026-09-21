HUGO ?= hugo

.PHONY: help serve build check

help:
	@printf 'targets:\n  serve   local preview on http://localhost:1313\n  build   release build with the same flags as CI\n  check   build + assert the invariants this site has regressed on\n'

build:
	hugo --gc --minify

check:
	@./scripts/check.sh

serve:
	$(HUGO) server
