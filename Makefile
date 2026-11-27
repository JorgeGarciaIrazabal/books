.PHONY: release-desktop release-desktop-dry-run help

help:
	@echo "Book Studio targets:"
	@echo "  make release-desktop          Bump desktop patch version, test, commit, tag, and push for release"
	@echo "  make release-desktop-dry-run  Preview the next desktop release version and commands (no changes)"
	@echo ""
	@echo "Optional variables: BUMP=patch|minor|major REMOTE=origin SKIP_CHECKS=0|1"

release-desktop:
	@$(MAKE) -C studio-desktop release

release-desktop-dry-run:
	@$(MAKE) -C studio-desktop release-dry-run
