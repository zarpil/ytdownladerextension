@echo off
:: ══════════════════════════════════════════════════════════════════════════
::  install_host.bat  –  Instala el Native Messaging Host para YT Downloader
::  Delega toda la lógica al script PowerShell install.ps1
:: ══════════════════════════════════════════════════════════════════════════
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0install.ps1"
pause
