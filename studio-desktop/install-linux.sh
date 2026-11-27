#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
APP_BIN_DIR="$HOME/.local/bin"
APP_ICON_DIR="$HOME/.local/share/icons/hicolor/512x512/apps"
APP_DESKTOP_DIR="$HOME/.local/share/applications"

MODE="local"
SKIP_NPM=0

for arg in "$@"; do
  case "$arg" in
    --deb|--appimage|--package) MODE="package" ;;
    --skip-npm) SKIP_NPM=1 ;;
    -h|--help)
      cat <<'EOF'
Book Studio Desktop — Linux Installer

Usage:
  ./install-linux.sh              Install Book Studio in your Applications menu & ~/.local/bin/book-studio
  ./install-linux.sh --package    Build standalone .AppImage and .deb installers in studio-desktop/release/
  ./install-linux.sh --skip-npm   Skip npm install (reuse existing node_modules)
EOF
      exit 0
      ;;
    *)
      echo "Unknown option: $arg" >&2
      exit 1
      ;;
  esac
done

if ! command -v node >/dev/null 2>&1 || ! command -v npm >/dev/null 2>&1; then
  echo "ERROR: Node.js and npm are required to install from source." >&2
  echo "Install Node.js 20+ or download a prebuilt .AppImage / .deb release." >&2
  exit 1
fi

cd "$SCRIPT_DIR"

if [ "$SKIP_NPM" -eq 0 ]; then
  echo "Installing dependencies..."
  npm install
  # npm 11+ may block install scripts until explicitly approved
  if npm install-scripts ls >/dev/null 2>&1; then
    npm install-scripts approve electron esbuild >/dev/null 2>&1 || true
    npm rebuild electron esbuild >/dev/null 2>&1 || true
  fi
fi

# Fallback extraction if Electron's cached zip exists but dist/electron was not populated
if [ ! -x "$SCRIPT_DIR/node_modules/electron/dist/electron" ]; then
  node "$SCRIPT_DIR/node_modules/electron/install.js" || true
fi
if [ ! -x "$SCRIPT_DIR/node_modules/electron/dist/electron" ] && command -v unzip >/dev/null 2>&1; then
  ZIP_PATH="$(node -e 'const {downloadArtifact}=require("@electron/get");downloadArtifact({version:require("./node_modules/electron/package.json").version,artifactName:"electron",platform:process.platform,arch:process.arch}).then(p=>console.log(p)).catch(()=>process.exit(1));' 2>/dev/null || true)"
  if [ -n "$ZIP_PATH" ] && [ -f "$ZIP_PATH" ]; then
    mkdir -p "$SCRIPT_DIR/node_modules/electron/dist"
    unzip -q -o "$ZIP_PATH" -d "$SCRIPT_DIR/node_modules/electron/dist"
    printf "electron" > "$SCRIPT_DIR/node_modules/electron/path.txt"
  fi
fi

echo "Building Book Studio Desktop..."
npm run build

if [ "$MODE" = "package" ]; then
  echo "Building standalone Linux installers (.AppImage and .deb)..."
  npm run dist:linux
  echo ""
  echo "Done! Installers created in: $SCRIPT_DIR/release/"
  ls -lh "$SCRIPT_DIR/release/"
  exit 0
fi

mkdir -p "$APP_BIN_DIR" "$APP_ICON_DIR" "$APP_DESKTOP_DIR"

if [ -f "$SCRIPT_DIR/assets/icon.png" ]; then
  cp "$SCRIPT_DIR/assets/icon.png" "$APP_ICON_DIR/book-studio.png"
fi

cat > "$APP_BIN_DIR/book-studio" <<EOF
#!/usr/bin/env bash
exec "$SCRIPT_DIR/node_modules/.bin/electron" "$SCRIPT_DIR" --library "$REPO_ROOT" "\$@"
EOF
chmod +x "$APP_BIN_DIR/book-studio"

cat > "$APP_DESKTOP_DIR/book-studio.desktop" <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Book Studio
Comment=Writer-first workspace for books, series, and shared worlds
Exec=$APP_BIN_DIR/book-studio %U
Icon=book-studio
Terminal=false
Categories=Office;Utility;
StartupWMClass=Book Studio
EOF

if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database "$APP_DESKTOP_DIR" >/dev/null 2>&1 || true
fi

echo ""
echo "Book Studio Desktop installed!"
echo "  • App Launcher : Search 'Book Studio' in your Linux Applications menu"
echo "  • Command Line : $APP_BIN_DIR/book-studio"
echo "  • Library Root : $REPO_ROOT"

SANDBOX_BIN="$SCRIPT_DIR/node_modules/electron/dist/chrome-sandbox"
if [ -f "$SANDBOX_BIN" ] && [ -f /proc/sys/kernel/apparmor_restrict_unprivileged_userns ]; then
  RESTRICTED="$(cat /proc/sys/kernel/apparmor_restrict_unprivileged_userns 2>/dev/null || echo 0)"
  PERMS="$(stat -c '%u:%a' "$SANDBOX_BIN" 2>/dev/null || echo '')"
  if [ "$RESTRICTED" = "1" ] && [ "$PERMS" != "0:4755" ]; then
    echo ""
    echo "Ubuntu/AppArmor note: to enable Electron's sandbox on this system, either:"
    echo "  1) Run once: sudo chown root:root \"$SANDBOX_BIN\" && sudo chmod 4755 \"$SANDBOX_BIN\""
    echo "  2) Or build & install the .deb package: ./install-linux.sh --package"
  fi
fi
