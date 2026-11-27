# Book Studio Desktop

A writer-first desktop application for **Linux** and **Windows**, encapsulated inside `studio-desktop/`.

It works directly on top of your Book Studio library folder—saving clean `.md` manuscripts, keeping local draft versions, anchoring margin notes on both prose and world rules, running automatic cloud backups, and wrapping reading-copy builds and optional Fish Audio Drama 3 narration without requiring writers to touch raw code files.

---

## Install & Start on Linux

Run the one-step installer from this folder:

```bash
cd studio-desktop
./install-linux.sh
```

This builds the app, registers **Book Studio** in your Linux Applications menu (with icon), and installs `~/.local/bin/book-studio` so you can launch it from anywhere or pin it to your dock.

- **Build standalone `.AppImage` / `.deb` packages:**
  ```bash
  ./install-linux.sh --package
  ```
- **Uninstall shortcuts:**
  ```bash
  ./uninstall-linux.sh
  ```

---

## Install & Start on Windows

1. Open the `studio-desktop` folder in File Explorer and **double-click `Install-Book-Studio.bat`** (or run `.\install-windows.ps1` in PowerShell).
2. Launch **Book Studio** from your **Start Menu** or **Desktop shortcut**.

- **Build a standalone Windows Setup `.exe` installer:**
  ```powershell
  powershell -ExecutionPolicy Bypass -File .\install-windows.ps1 -BuildInstaller
  ```
- **Uninstall shortcuts:**
  ```powershell
  powershell -ExecutionPolicy Bypass -File .\Uninstall-Book-Studio.ps1
  ```

---

## Standalone Installers (GitHub Actions)

To build downloadable `.AppImage`, `.deb`, and Windows `.exe` installers without building locally, use **Build Book Studio Desktop installers** (`.github/workflows/desktop-installers.yml`):

- **One-command release for writers (recommended):**
  From the repository root (or inside `studio-desktop/` with `make release`), run:
  ```bash
  make release-desktop
  ```
  This automatically bumps the patch version (`package.json` + `package-lock.json`), runs `npm run typecheck && npm test`, commits the bump, creates a `desktop-vX.Y.Z` tag, and pushes to `origin` so GitHub Actions builds and publishes `.AppImage`, `.deb`, and Windows `.exe` installers to a permanent GitHub Release (no GitHub login needed for public repos, and no 90-day Actions artifact expiration).
  - Preview first without making changes: `make release-desktop-dry-run`
  - Bump minor or major instead of patch: `make release-desktop BUMP=minor` (or `BUMP=major`)
- **Manual release or temporary test builds (GitHub Actions UI):**
  Trigger **Build Book Studio Desktop installers** manually from the GitHub Actions tab. Enter a `release_tag` (such as `desktop-v0.1.0`) to publish a GitHub Release, or leave `release_tag` blank to build temporary Actions artifacts without creating a Release.

---

## Development & Tests

```bash
npm run typecheck
npm test
npm run dev:linux   # Hot-reload development on Linux
npm run dev:win     # Hot-reload development on Windows
```
