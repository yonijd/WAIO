@echo off
chcp 65001 >nul
title Desinstalador WAIO
echo ========================================
echo    DESINSTALADOR WAIO
echo ========================================
echo.
echo Desinstalando WAIO del sistema...
echo.
cmd /k python "%~dp0desinstalador_waio.py"
