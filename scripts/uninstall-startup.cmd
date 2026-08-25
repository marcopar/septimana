@echo off
rem Runs uninstall-startup.ps1 with a one-time, process-only execution-policy bypass.
rem This does not change any system or user settings.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0uninstall-startup.ps1"
pause
