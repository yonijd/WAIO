@echo off
chcp 65001 >nul
title Instalador WAIO 3.2
echo ========================================
echo    INSTALADOR WAIO 3.2
echo ========================================
echo.
echo Este instalador copiara WAIO a %%USERPROFILE%%\.waio
echo y registrara el menu contextual.
echo.
pause
echo.
python instalador_waio.py
pause