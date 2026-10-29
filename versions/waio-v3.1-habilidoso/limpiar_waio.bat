@echo off
chcp 65001 >nul
title LIMPIAR WAIO - MATAR PROCESOS
echo ============================================================
echo              LIMPIANDO PROCESOS WAIO
echo ============================================================
echo.

echo [1] Matando todos los pythonw.exe...
taskkill /F /IM pythonw.exe 2>nul

echo [2] Matando python.exe (motores)...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq WAIO*" 2>nul

echo [3] Eliminando triggers huérfanos...
cd /d "%USERPROFILE%\.waio" 2>nul
if exist STOP.trigger del STOP.trigger
if exist TRANSCLIP_STOP.trigger del TRANSCLIP_STOP.trigger
if exist ESCUCHA_STOP.trigger del ESCUCHA_STOP.trigger
if exist transclip.lock del transclip.lock
if exist escucha.lock del escucha.lock

echo.
echo LISTO. Procesos limpiados.
echo.
tasklist /FI "IMAGENAME eq pythonw.exe" 2>nul
echo.
pause