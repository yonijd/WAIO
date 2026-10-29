@echo off
chcp 65001 >nul
title Instalador WAIO V3
echo ========================================
echo    INSTALADOR WAIO V3
echo ========================================
echo.
echo Instalando WAIO V3 en el sistema...
echo.
echo Este instalador copiara:
echo   - waio_escucha.py (motor V3)
echo   - waio_visor.py (visor V3)
echo   - transclip.py (puente WhatsApp)
echo   - escucha_output.py (compilador de resultados)
echo   - kill_waio.py (matar motor)
echo.
cmd /k python "%~dp0instalador_waio.py"