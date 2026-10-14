@echo off
chcp 65001 >nul
rem ============================================================
rem  AI Search Diagnostic Tool - SATU KLIK: 2 tunnel publik
rem    Tunnel 1 -> H5 laporan klien (:5173)
rem    Tunnel 2 -> panel admin      (:5174)
rem  Mencetak kedua URL siap pakai (bisa dibuka dari jaringan
rem  apa pun, HP pakai 4G pun bisa).
rem  CATATAN: URL berubah tiap menjalankan skrip ini. Laptop
rem  harus tetap menyala. Segera GANTI password admin default!
rem ============================================================
setlocal EnableDelayedExpansion
set "ROOT=%~dp0"
set "ROOT=%ROOT:~0,-1%"
set "LOGH=%TEMP%\aidiag_tunnel_h5.log"
set "LOGA=%TEMP%\aidiag_tunnel_admin.log"

if not exist "%ROOT%\tools\cloudflared.exe" (
  echo [ERROR] tools\cloudflared.exe tidak ditemukan.
  pause & exit /b 1
)

rem --- pastikan server jalan ---
netstat -ano | findstr ":5173 .*LISTENING" >nul
if errorlevel 1 (
  echo [INFO] Server belum jalan - menjalankan start-demo.bat ...
  start "" "%ROOT%\start-demo.bat"
  timeout /t 12 /nobreak >nul
)

rem --- matikan tunnel lama & backend lama ---
taskkill /F /IM cloudflared.exe >nul 2>&1
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":8000 .*LISTENING"') do taskkill /F /PID %%p >nul 2>&1

echo [1/5] Menjalankan tunnel H5 ...
del /q "%LOGH%" "%LOGA%" >nul 2>&1
start "aidiag-tunnel-h5" /min "%ROOT%\tools\cloudflared.exe" tunnel --url http://localhost:5173 --no-autoupdate > "%LOGH%" 2>&1
echo [2/5] Menjalankan tunnel admin ...
start "aidiag-tunnel-admin" /min "%ROOT%\tools\cloudflared.exe" tunnel --url http://localhost:5174 --no-autoupdate > "%LOGA%" 2>&1

echo [3/5] Menunggu kedua URL publik ...
call :waiturl "%LOGH%" PUBH5
call :waiturl "%LOGA%" PUBADMIN
if not defined PUBH5 ( echo [ERROR] URL H5 tidak muncul. Cek %LOGH% & pause & exit /b 1 )
if not defined PUBADMIN ( echo [ERROR] URL admin tidak muncul. Cek %LOGA% & pause & exit /b 1 )
echo      H5    : %PUBH5%
echo      Admin : %PUBADMIN%

echo [4/5] Restart backend dengan H5_BASE_URL=%PUBH5% ...
start "aidiag-backend" /min cmd /c "set H5_BASE_URL=%PUBH5%&& cd /d "%ROOT%\backend" && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"

echo [5/5] Menunggu backend siap ...
call :waitbackend

echo.
echo ============================================================
echo  BERHASIL. Kedua link berfungsi dari JARINGAN APA PUN:
echo.
echo   LAPORAN H5 (kirim ke klien / WeChat):
echo     %PUBH5%/r/FnWkWQSqtDEp
echo.
echo   PANEL ADMIN (RAHASIA - jangan dibagikan):
echo     %PUBADMIN%
echo     login: admin / admin123  ^<- SEGERA GANTI
echo.
echo  Biarkan semua jendela (2 tunnel/vite/backend) menyala.
echo ============================================================
echo.
pause
exit /b 0

:waiturl
set "%~2="
for /l %%i in (1,1,75) do (
  if not defined %~2 (
    for /f "usebackq delims=" %%u in (`powershell -NoProfile -Command "if (Test-Path '%~1') { Select-String -Path '%~1' -Pattern 'https://[a-z0-9-]+\.trycloudflare\.com' ^| Select-Object -First 1 ^| ForEach-Object { $_.Matches[0].Value } }"`) do set "%~2=%%u"
    if not defined %~2 timeout /t 2 /nobreak >nul
  )
)
exit /b 0

:waitbackend
set "H="
for /l %%i in (1,1,45) do (
  if not defined H (
    for /f "usebackq delims=" %%c in (`powershell -NoProfile -Command "try { (Invoke-WebRequest -Uri 'http://localhost:8000/api/health' -TimeoutSec 2 -UseBasicParsing).StatusCode } catch { '' }"`) do set "H=%%c"
    if not defined H timeout /t 2 /nobreak >nul
  )
)
exit /b 0
