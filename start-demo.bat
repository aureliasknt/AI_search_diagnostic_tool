@echo off
chcp 65001 >nul
rem ============================================================
rem  AI Search Diagnostic Tool - mode demo Wi-Fi (semua device)
rem  Dobel-klik file ini: mendeteksi IP Wi-Fi, lalu menjalankan
rem  backend + H5 + admin sebagai proses latar.
rem  Link H5 dibagikan lewat WeChat di HP dalam Wi-Fi yang sama.
rem ============================================================
setlocal

set "ROOT=%~dp0"
set "ROOT=%ROOT:~0,-1%"

for /f "usebackq delims=" %%i in (`powershell -NoProfile -Command "(Get-NetIPAddress -AddressFamily IPv4 ^| Where-Object { $_.InterfaceAlias -eq (Get-NetConnectionProfile).InterfaceAlias -and $_.PrefixOrigin -eq 'Dhcp' } ^| Select-Object -First 1).IPAddress"`) do set "LAN_IP=%%i"

if "%LAN_IP%"=="" (
  echo [ERROR] Tidak menemukan IP Wi-Fi. Sambungkan ke Wi-Fi dulu.
  pause
  exit /b 1
)

echo IP Wi-Fi terdeteksi : %LAN_IP%
echo.

rem --- hentikan instance lama (jika ada) ---
for /f "tokens=5" %%p in ('netstat -ano ^| findstr /R ":8000 .*LISTENING"') do taskkill /F /PID %%p >nul 2>&1
for /f "tokens=5" %%p in ('netstat -ano ^| findstr /R ":5173 .*LISTENING"') do taskkill /F /PID %%p >nul 2>&1
for /f "tokens=5" %%p in ('netstat -ano ^| findstr /R ":5174 .*LISTENING"') do taskkill /F /PID %%p >nul 2>&1

rem --- backend (H5_BASE_URL mengikuti IP hari ini) ---
start "aidiag-backend" /min cmd /c "set H5_BASE_URL=http://%LAN_IP%:5173&& cd /d "%ROOT%\backend" && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"

rem --- H5 (laporan klien, dengar di semua interface) ---
start "aidiag-h5" /min cmd /c "cd /d "%ROOT%\frontend-h5" && .\node_modules\.bin\vite --port 5173 --strictPort --host"

rem --- panel admin ---
start "aidiag-admin" /min cmd /c "cd /d "%ROOT%\frontend-admin" && .\node_modules\.bin\vite --port 5174 --strictPort"

echo Menunggu server siap...
timeout /t 8 /nobreak >nul

echo.
echo ============================================================
echo  Selesai. Buka dari HP (WeChat) dalam Wi-Fi yang sama:
echo.
echo    H5 laporan : http://%LAN_IP%:5173/r/FnWkWQSqtDEp
echo    Panel admin: http://localhost:5174   (admin / admin123)
echo.
echo  QR otomatis memakai IP ini: Panel admin -^> 分享
echo ============================================================
echo.
echo Server berjalan di jendela cmd terpisah. Tutup jendela itu untuk mematikan.
pause
