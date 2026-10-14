@echo off
chcp 65001 >nul
rem Hentikan semua proses AI Search Diagnostic Tool
taskkill /F /IM cloudflared.exe >nul 2>&1
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":8000 .*LISTENING"') do taskkill /F /PID %%p >nul 2>&1
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":5173 .*LISTENING"') do taskkill /F /PID %%p >nul 2>&1
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":5174 .*LISTENING"') do taskkill /F /PID %%p >nul 2>&1
echo Semua server & tunnel dihentikan.
pause
