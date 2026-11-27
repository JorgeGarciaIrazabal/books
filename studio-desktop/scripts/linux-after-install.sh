#!/bin/bash
set -e

if type update-alternatives >/dev/null 2>&1; then
  if [ -L '/usr/bin/book-studio-desktop' ] && [ -e '/usr/bin/book-studio-desktop' ] && [ "$(readlink '/usr/bin/book-studio-desktop')" != '/etc/alternatives/book-studio-desktop' ]; then
    rm -f '/usr/bin/book-studio-desktop'
  fi
  update-alternatives --install '/usr/bin/book-studio-desktop' 'book-studio-desktop' '/opt/Book Studio/book-studio-desktop' 100 || ln -sf '/opt/Book Studio/book-studio-desktop' '/usr/bin/book-studio-desktop'
else
  ln -sf '/opt/Book Studio/book-studio-desktop' '/usr/bin/book-studio-desktop'
fi

# Install an AppArmor profile granting unprivileged userns for Electron's Chromium sandbox
# on Ubuntu 24.04+ / 26.04+ systems where apparmor_restrict_unprivileged_userns=1.
APPARMOR_LOADED=0
if [ -d /etc/apparmor.d ]; then
  cat >/etc/apparmor.d/book-studio-desktop <<'EOF'
abi <abi/4.0>,
include <tunables/global>

profile "book-studio-desktop" "/opt/Book Studio/book-studio-desktop" flags=(unconfined) {
  userns,

  include if exists <local/book-studio-desktop>
}
EOF
  if command -v apparmor_parser >/dev/null 2>&1; then
    if apparmor_parser -r /etc/apparmor.d/book-studio-desktop; then
      APPARMOR_LOADED=1
    fi
  fi
fi

if [ "${APPARMOR_LOADED}" != "1" ] && [ "$(cat /proc/sys/kernel/apparmor_restrict_unprivileged_userns 2>/dev/null || echo 0)" = "1" ]; then
  chmod 4755 '/opt/Book Studio/chrome-sandbox' || true
elif ! { [[ -L /proc/self/ns/user ]] && unshare --user true >/dev/null 2>&1; }; then
  chmod 4755 '/opt/Book Studio/chrome-sandbox' || true
else
  chmod 0755 '/opt/Book Studio/chrome-sandbox' || true
fi

if hash update-mime-database >/dev/null 2>&1; then
  update-mime-database /usr/share/mime || true
fi

if hash update-desktop-database >/dev/null 2>&1; then
  update-desktop-database /usr/share/applications || true
fi
