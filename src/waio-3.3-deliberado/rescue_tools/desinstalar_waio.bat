@echo off
chcp 65001 >nul
title Desinstalador WAIO 3.3
cd /d "%~dp0"
echo ========================================
echo    DESINSTALADOR WAIO 3.3
echo ========================================
echo.
echo Esto eliminara:
echo   - Carpeta .waio (con opcion de preservar trash/ y logs/)
echo   - Menu contextual 06_WAIO
echo.
echo ADVERTENCIA: La desinstalacion es irreversible.
echo.
pause
echo.
python "%~dp0desinstalador_waio.py"
pause