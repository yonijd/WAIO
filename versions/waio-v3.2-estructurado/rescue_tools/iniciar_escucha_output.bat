@echo off
chcp 65001 >nul
title Escucha Output WAIO V3
echo ========================================
echo    ESCUCHA OUTPUT WAIO V3
echo ========================================
echo.
echo Compila resultados de WAIO en un solo bloque
echo Timeout 5 segundos
echo Formato [N] TX: xxx | Accion X | Comando: xxx
echo.
pythonw %~dp0escucha_output.py
echo Escucha Output iniciado en segundo plano
timeout /t 2 /nobreak >nul
