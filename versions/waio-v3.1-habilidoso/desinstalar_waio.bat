@echo off
chcp 65001 >nul
title Desinstalador WAIO V3
echo ========================================
echo    DESINSTALADOR WAIO V3
echo ========================================
echo.
echo Desinstalando WAIO V3 del sistema...
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
cmd /k python "%~dp0desinstalador_waio.py"