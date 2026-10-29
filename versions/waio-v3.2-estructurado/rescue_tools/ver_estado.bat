@echo off
chcp 65001 >nul
title ESTADO WAIO V3

set LOG_DIR=temp\logs
set LOG_FILE=%LOG_DIR%\estado_%date:~6,4%%date:~3,2%%date:~0,2%_%time:~0,2%%time:~3,2%%time:~6,2%.log
set LOG_FILE=%LOG_FILE: =0%

if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

(
echo ============================================================
echo                 ESTADO WAIO V3
echo ============================================================
echo.
echo Fecha: %date% %time%
echo.
echo [DIRECTORIO]
echo   %cd%
echo.

echo [PROCESOS PYTHONW.EXE]
tasklist /FI "IMAGENAME eq pythonw.exe" 2>nul
echo.

echo [LOCK FILES]
if exist waio.lock (echo   WAIO: CORRIENDO) else (echo   WAIO: DETENIDO)
if exist transclip.lock (echo   TRANSCLIP: CORRIENDO) else (echo   TRANSCLIP: DETENIDO)
if exist escucha.lock (echo   ESCUCHA OUTPUT: CORRIENDO) else (echo   ESCUCHA OUTPUT: DETENIDO)
if exist events.lock (echo   EVENT VISOR: CORRIENDO) else (echo   EVENT VISOR: DETENIDO)
echo.

echo [TRIGGER FILES]
if exist STOP.trigger (echo   STOP.trigger: PRESENTE)
if exist TRANSCLIP_STOP.trigger (echo   TRANSCLIP_STOP.trigger: PRESENTE)
if exist ESCUCHA_STOP.trigger (echo   ESCUCHA_STOP.trigger: PRESENTE)
if exist EVENTS_STOP.trigger (echo   EVENTS_STOP.trigger: PRESENTE)
echo.

echo [CONTEO DE PROCESOS]
set count=0
for /f %%a in ('tasklist /FI "IMAGENAME eq pythonw.exe" /NH 2^>nul ^| find /c /v ""') do set count=%%a
echo   pythonw.exe activos: %count%
if %count% gtr 2 echo   [!] Demasiados procesos. Ejecuta limpiar_waio.bat
echo.

echo [CARPETAS Y ARCHIVOS CLAVE]
dir /b 2>nul | findstr /i "waio_escucha waio_visor transclip escucha_output prompt.txt" | sort
echo.

echo ============================================================
) > "%LOG_FILE%" 2>&1

type "%LOG_FILE%"
echo.
echo [LOG] Reporte guardado en: %LOG_FILE%
echo.
pause
