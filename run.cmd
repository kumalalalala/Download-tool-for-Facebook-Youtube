@echo off
set ROOT=%~dp0

set PYTHONHOME=%ROOT%main\python\python-3.10.2.amd64
set PATH=%PYTHONHOME%;%PATH%

cd /d %ROOT%
python main/python/main.py

pause
