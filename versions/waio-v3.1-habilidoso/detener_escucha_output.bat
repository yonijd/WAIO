@echo off
chcp 65001 >nul
title Detener Escucha Output
echo ========================================
echo    DETENER ESCUCHA OUTPUT
echo ========================================
echo.
echo Creando ESCUCHA_STOP.trigger...
echo.
echo Si la escucha estaba corriendo, se detendra en <2 segundos.
echo.
cd /d "%USERPROFILE%\.waio"
echo. > ESCUCHA_STOP.trigger
echo Trigger creado.
timeout /t 2 /nobreak >nul