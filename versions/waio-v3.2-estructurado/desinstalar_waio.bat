@echo off
chcp 65001 >nul
title Desinstalador WAIO 3.2
echo ========================================
echo    DESINSTALADOR WAIO 3.2
echo ========================================
echo.
echo Esto eliminara:
echo   - Carpeta .waio (todos los archivos)
echo   - Menu contextual (todas las entradas)
echo.
echo ADVERTENCIA: Los logs y archivos de configuracion
echo se eliminaran permanentemente.
echo.
pause
echo.
python "%~dp0desinstalador_waio.py"
pause
