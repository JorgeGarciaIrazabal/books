#!/usr/bin/env bash
set -euo pipefail

rm -f "$HOME/.local/bin/book-studio"
rm -f "$HOME/.local/share/applications/book-studio.desktop"
rm -f "$HOME/.local/share/icons/hicolor/512x512/apps/book-studio.png"

if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database "$HOME/.local/share/applications" >/dev/null 2>&1 || true
fi

echo "Book Studio Desktop shortcuts removed. Your books and files were not touched."
