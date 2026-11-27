#!/bin/bash
set -e

if [ "${1:-}" = "remove" ] || [ "${1:-}" = "purge" ]; then
  if [ -f /etc/apparmor.d/book-studio-desktop ]; then
    if command -v apparmor_parser >/dev/null 2>&1; then
      apparmor_parser -R /etc/apparmor.d/book-studio-desktop || true
    fi
    rm -f /etc/apparmor.d/book-studio-desktop
  fi
fi

if hash update-mime-database >/dev/null 2>&1; then
  update-mime-database /usr/share/mime || true
fi

if hash update-desktop-database >/dev/null 2>&1; then
  update-desktop-database /usr/share/applications || true
fi
