$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)
if (-not (Test-Path .venv)) { py -3.12 -m venv .venv }
& .venv\Scripts\python.exe -m pip install -r requirements-build.txt
& .venv\Scripts\python.exe -m PyInstaller --noconfirm --clean --name WindowsLocationSimulator `
  --collect-all pymobiledevice3 --collect-all PySide6.QtWebEngineCore `
  --add-data "winloc\map.html;winloc" --add-data "winloc\iphone_bridge.py;winloc" `
  --paths . launcher.py
Write-Host "已生成 dist\WindowsLocationSimulator\WindowsLocationSimulator.exe"
