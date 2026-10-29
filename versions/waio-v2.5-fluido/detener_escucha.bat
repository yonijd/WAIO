@echo off
title DETENER TRADUCTOR
echo Cerrando traductor WAIO...
taskkill /F /FI "WINDOWTITLE eq TRADUCTOR WAIO*"
echo.
echo Si ves "NINGUN proceso", ya estaba cerrado.
timeout /t 2 /nobreak >nul
