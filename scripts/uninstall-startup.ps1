#requires -Version 5.1
<#
.SYNOPSIS
    Removes Septimana from the current user's Windows startup.
.DESCRIPTION
    Deletes the Septimana shortcut from the user's Startup folder. The application
    itself is left untouched; a running instance keeps running until you exit it
    from the tray menu.
#>
[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

$startup = [Environment]::GetFolderPath("Startup")
$shortcut = Join-Path $startup "Septimana.lnk"

if (Test-Path -LiteralPath $shortcut) {
    Remove-Item -LiteralPath $shortcut -Force
    Write-Host "Septimana will no longer start with Windows." -ForegroundColor Green
    Write-Host "  Removed: $shortcut"
}
else {
    Write-Host "Nothing to do - Septimana is not in the Startup folder." -ForegroundColor Yellow
    Write-Host "  Checked: $shortcut"
}
