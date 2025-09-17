:: extraenter.bat
@echo off
:: Copies run_server.bat to current user's Startup folder so server auto-starts on login
set SRC=%~dp0run_server.bat
set DST=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\run_server.bat
copy /Y "%SRC%" "%DST%" >nul
exit
