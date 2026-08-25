#requires -Version 5.1
$ErrorActionPreference = "Stop"
Push-Location $PSScriptRoot
try {
    # Prefer the project venv so the script works without activating it first.
    $python = if (Test-Path .\.venv\Scripts\python.exe) { ".\.venv\Scripts\python.exe" } else { "python" }

    # OneDrive can transiently lock files under build\, which makes PyInstaller's
    # own --clean step fail with WinError 5. Remove it ourselves first so a stale
    # lock never blocks the build.
    if (Test-Path .\build) {
        Remove-Item .\build -Recurse -Force -ErrorAction SilentlyContinue
    }

    & $python -m PyInstaller --noconfirm septimana.spec
    if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed with exit code $LASTEXITCODE" }

    # dist\ is the shippable bundle, so the startup helpers ride along with the exe.
    Copy-Item .\scripts\install-startup.ps1, .\scripts\uninstall-startup.ps1, `
        .\scripts\install-startup.cmd, .\scripts\uninstall-startup.cmd .\dist\ -Force

    Write-Host "Built dist\ (septimana.exe + startup scripts)" -ForegroundColor Green
    Get-ChildItem .\dist | Select-Object Name, Length | Format-Table | Out-String | Write-Host
}
finally {
    Pop-Location
}
