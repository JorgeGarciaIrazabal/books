$StartMenuShortcut = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs\Book Studio.lnk"
$DesktopShortcut = Join-Path ([Environment]::GetFolderPath("Desktop")) "Book Studio.lnk"

foreach ($Path in @($StartMenuShortcut, $DesktopShortcut)) {
  if (Test-Path $Path) {
    Remove-Item $Path -Force
  }
}

Write-Host "Book Studio Desktop shortcuts removed. Your books and files were not touched." -ForegroundColor Green
