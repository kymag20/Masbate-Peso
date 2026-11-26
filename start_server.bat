@echo off
title Masbate Provincial PESO Database System
cd /d "%~dp0"
echo ======================================================
echo    PESO MASBATE - Provincial Database System
echo ======================================================
echo.
echo Modern Dashboard : http://127.0.0.1:8000/
echo Django Admin     : http://127.0.0.1:8000/admin/
echo Default Admin    : admin
echo Default Pass     : admin12345
echo.
echo Opening browser...
start http://127.0.0.1:8000/
echo.
echo Server running! Press CTRL+C in this window to stop.
echo.
".\venv\Scripts\python.exe" manage.py runserver 0.0.0.0:8000
pause
