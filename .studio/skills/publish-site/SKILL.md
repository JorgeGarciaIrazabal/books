---
name: publish-site
description: Preview an edition on the Book Studio library site or make an authorized book or audiobook available to readers.
---

# Make an edition available to readers

“Show me how it will look in the library” asks for a preview. “Publish this
edition” or “Make this audiobook available to readers” authorizes the named
edition and format. Confirm which title, version, language, or format only if
the choice is genuinely unclear. Keep unrelated changes out of the release.

1. Follow the [publishing guide](../../../docs/publishing.md) for rights,
   copies, cover, catalog entry, and audio. Preserve the exact reviewed EPUB
   and PDF bytes. Prepare audio with the [read-aloud skill](../read-aloud/SKILL.md).
2. Use `tools/build_catalog.py` to verify the entries, file checks, and links
   and to assemble a preview. Inspect the reader or player and the actual
   download paths. Show the author a preview when requested.
3. For an authorized public release, share the reviewed release files using
   the [workspace sync guide](../../../docs/workspace-sync.md). Verify that the
   public catalog, reader or player, and named downloads are available before
   calling the edition live. Give the author the link and available formats.
