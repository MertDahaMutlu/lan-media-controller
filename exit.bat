@echo off
cd /d "%~dp0"
:: Kısaca başlattığımız ffplay süreçlerini ve pythonw'yi kapatır
taskkill /IM ffplay.exe /F >nul 2>&1
taskkill /IM pythonw.exe /F >nul 2>&1
exit
