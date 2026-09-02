#requires -Version 5.1
[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
Push-Location $PSScriptRoot
try {
    $python = if (Test-Path .\.venv\Scripts\python.exe) { ".\.venv\Scripts\python.exe" } else { "python" }
    $version = (& $python -c "from septimana import __version__; print(__version__)").Trim()

    if ($version -notmatch '^\d+\.\d+$') {
        throw "Version '$version' must use the x.y format. Update septimana\__init__.py."
    }

    & .\build.ps1
    if ($LASTEXITCODE -ne 0) { throw "Build failed with exit code $LASTEXITCODE" }

    New-Item -ItemType Directory -Path .\release -Force | Out-Null
    $archive = ".\release\septimana-$version-windows.zip"
    Compress-Archive -Path .\dist\* -DestinationPath $archive -Force

    Write-Host "Release archive: $archive" -ForegroundColor Green
}
finally {
    Pop-Location
}
