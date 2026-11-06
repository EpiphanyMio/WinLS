$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)
if (-not (Test-Path .venv)) { py -3.12 -m venv .venv }
& .venv\Scripts\python.exe -m pip install -r requirements-build.txt
# PyInstaller resolves Qt's icuuc.dll dependency from PATH. Keep unrelated ICU
# builds (for example, a Poppler runtime) from being bundled ahead of Windows' ICU.
$systemIcuDirectory = Join-Path $env:SystemRoot "System32"
$filteredPath = foreach ($entry in ($env:PATH -split ';')) {
  if (-not $entry.Trim()) { continue }
  $resolvedEntry = [System.IO.Path]::GetFullPath($entry.Trim('"'))
  $isSystemIcu = $resolvedEntry.TrimEnd('\') -ieq $systemIcuDirectory.TrimEnd('\')
  if (-not $isSystemIcu -and (Test-Path (Join-Path $resolvedEntry 'icuuc.dll') -PathType Leaf)) { continue }
  $entry
}
$env:PATH = $filteredPath -join ';'
& .venv\Scripts\python.exe -m PyInstaller --noconfirm --clean --name WindowsLocationSimulator `
  --runtime-hook scripts\pyi_rth_qt_dll.py `
  --collect-all pymobiledevice3 --collect-all pytun_pmd3 --collect-all PySide6.QtWebEngineCore `
  --add-data "winloc\map.html;winloc" --add-data "winloc\qwebchannel.js;winloc" `
  --add-data "winloc\vendor;winloc\vendor" --add-data "winloc\iphone_bridge.py;winloc" `
  --paths . launcher.py
Write-Host "已生成 dist\WindowsLocationSimulator\WindowsLocationSimulator.exe"
