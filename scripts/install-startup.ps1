#requires -Version 5.1
<#
.SYNOPSIS
    Adds Septimana to the current user's Windows startup.
.DESCRIPTION
    Creates a shortcut to the septimana.exe sitting next to this script, so the
    tray icon appears automatically after sign-in. Re-running the script refreshes
    the existing shortcut. Only the current user is affected; no admin rights are
    needed and nothing outside the Startup folder is modified.
#>
[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

$exe = Join-Path $PSScriptRoot "septimana.exe"
if (-not (Test-Path -LiteralPath $exe)) {
    throw "septimana.exe not found next to this script (looked in '$PSScriptRoot'). Keep both files together."
}
$exe = (Resolve-Path -LiteralPath $exe).Path

$startup = [Environment]::GetFolderPath("Startup")
$shortcut = Join-Path $startup "Septimana.lnk"

$shell = New-Object -ComObject WScript.Shell
try {
    $link = $shell.CreateShortcut($shortcut)
    $link.TargetPath = $exe
    $link.WorkingDirectory = $PSScriptRoot
    $link.Description = "Septimana - week number in the system tray"
    $link.Save()
}
finally {
    [void][Runtime.InteropServices.Marshal]::ReleaseComObject($shell)
}

Write-Host "Septimana will start with Windows." -ForegroundColor Green
Write-Host "  Shortcut: $shortcut"
Write-Host "  Target:   $exe"
Write-Host "Run .\uninstall-startup.ps1 to undo."
Write-Host "Note: the shortcut points at this folder, so moving it later breaks startup."
