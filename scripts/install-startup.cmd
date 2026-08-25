@echo off
rem Runs install-startup.ps1 with a one-time, process-only execution-policy bypass.
rem This does not change any system or user settings.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install-startup.ps1"
pause
