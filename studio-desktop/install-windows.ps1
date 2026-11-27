param(
  [switch]$BuildInstaller,
  [switch]$SkipNpm
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = (Resolve-Path (Join-Path $ScriptDir "..")).Path

if (-not (Get-Command node -ErrorAction SilentlyContinue) -or -not (Get-Command npm -ErrorAction SilentlyContinue)) {
  Write-Host "ERROR: Node.js and npm are required. Install Node.js LTS from https://nodejs.org or use a prebuilt .exe installer." -ForegroundColor Red
  exit 1
}

Push-Location $ScriptDir
try {
  if (-not $SkipNpm) {
    Write-Host "Installing dependencies..." -ForegroundColor Cyan
    npm install
    try {
      npm install-scripts approve electron esbuild | Out-Null
      npm rebuild electron esbuild | Out-Null
    } catch {
      # Older npm versions already run postinstall automatically
    }
  }

  $ElectronExe = Join-Path $ScriptDir "node_modules\electron\dist\electron.exe"
  if (-not (Test-Path $ElectronExe)) {
    node (Join-Path $ScriptDir "node_modules\electron\install.js")
  }

  Write-Host "Building Book Studio Desktop..." -ForegroundColor Cyan
  npm run build

  if ($BuildInstaller) {
    Write-Host "Packaging Windows installer (.exe)..." -ForegroundColor Cyan
    npm run dist:win
    $ReleaseDir = Join-Path $ScriptDir "release"
    Write-Host "Done! Windows installer saved to: $ReleaseDir" -ForegroundColor Green
    Start-Process explorer.exe $ReleaseDir
    exit 0
  }

  $WshShell = New-Object -ComObject WScript.Shell
  $StartMenuDir = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs"
  $DesktopDir = [Environment]::GetFolderPath("Desktop")
  $IconPath = Join-Path $ScriptDir "assets\icon.ico"

  $Targets = @(
    (Join-Path $StartMenuDir "Book Studio.lnk"),
    (Join-Path $DesktopDir "Book Studio.lnk")
  )

  foreach ($ShortcutPath in $Targets) {
    $Shortcut = $WshShell.CreateShortcut($ShortcutPath)
    $Shortcut.TargetPath = $ElectronExe
    $Shortcut.Arguments = "`"$ScriptDir`" --library `"$RepoRoot`""
    $Shortcut.WorkingDirectory = $ScriptDir
    if (Test-Path $IconPath) {
      $Shortcut.IconLocation = $IconPath
    }
    $Shortcut.Description = "Book Studio — Writer-first book workspace"
    $Shortcut.Save()
  }

  Write-Host ""
  Write-Host "Book Studio Desktop installed!" -ForegroundColor Green
  Write-Host "  * Start Menu : Book Studio"
  Write-Host "  * Desktop    : Book Studio"
  Write-Host "  * Library    : $RepoRoot"
} finally {
  Pop-Location
}
