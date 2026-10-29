@echo off
chcp 65001 >nul
title Instalador WAIO
echo ========================================
echo    INSTALADOR WAIO
echo ========================================
echo.
echo Instalando WAIO en el sistema...
echo.
cmd /k python "%~dp0instalador_waio.py"