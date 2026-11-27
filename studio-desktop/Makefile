BUMP ?= patch
REMOTE ?= origin
DRY_RUN ?= 0
SKIP_CHECKS ?= 0

.PHONY: release release-dry-run help

help:
	@echo "Book Studio Desktop release targets:"
	@echo "  make release          Bump patch version, test, commit, tag desktop-vX.Y.Z, and push"
	@echo "  make release-dry-run  Preview the next version, tag, and git commands without modifying anything"
	@echo ""
	@echo "Options:"
	@echo "  BUMP=patch|minor|major   (default: patch)"
	@echo "  REMOTE=origin            (default: origin)"
	@echo "  SKIP_CHECKS=0|1          (default: 0)"

release:
	@BUMP="$(BUMP)" REMOTE="$(REMOTE)" DRY_RUN="$(DRY_RUN)" SKIP_CHECKS="$(SKIP_CHECKS)" ./scripts/release.sh

release-dry-run:
	@BUMP="$(BUMP)" REMOTE="$(REMOTE)" DRY_RUN=1 SKIP_CHECKS="$(SKIP_CHECKS)" ./scripts/release.sh
