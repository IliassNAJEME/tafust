param(
    [switch]$Clean
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

Set-Location $ProjectRoot

if (-not (Test-Path ".\\venv\\Scripts\\python.exe")) {
    throw "Environnement virtuel introuvable. Creez .\\venv puis installez les dependances."
}

$Python = ".\\venv\\Scripts\\python.exe"

if ($Clean) {
    Remove-Item -Recurse -Force .\build, .\dist -ErrorAction SilentlyContinue
}

& $Python -m pip install -r requirements.txt
& $Python -m pip install pyinstaller
& $Python -m PyInstaller --noconfirm --clean .\tafust.spec

Write-Host ""
Write-Host "Build termine. Executable disponible dans: $ProjectRoot\\dist\\Tafust.exe"
