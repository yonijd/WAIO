@echo off
chcp 65001 >nul
title Instalador WAIO 3.3
echo ========================================
echo    INSTALADOR WAIO 3.3
echo ========================================
echo.
echo Este instalador copiara WAIO a %USERPROFILE%\.waio
echo y registrara el menu contextual.
echo.
pause
echo.
cd /d "%~dp0"
python "%~dp0instalador_waio.py"
pause