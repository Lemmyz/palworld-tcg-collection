$ErrorActionPreference = 'Stop'
python -m PyInstaller --noconfirm --clean --windowed --name Palvault --add-data "palvault/assets;palvault/assets" launch.py
if ($LASTEXITCODE -ne 0) { throw 'Build failed.' }
Write-Host 'Build ready: dist/Palvault/Palvault.exe'
