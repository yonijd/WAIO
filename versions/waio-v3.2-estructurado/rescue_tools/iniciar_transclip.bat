@echo off
chcp 65001 >nul
title TRANSCLIP V3 - WhatsApp Bridge
echo ========================================
echo    TRANSCLIP V3
echo ========================================
echo.
echo Traductor de comandos simples a WAIO
echo Escucha el portapapeles y traduce:
echo   {"comando": "dir"} -> listar_directorio
echo   {"comando": "mkdir x"} -> crear_carpeta x
echo.
pythonw "%~dp0transclip.py"
