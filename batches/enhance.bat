@echo off
cd /d %~dp0

call ..\.venv\Scripts\activate
python ..\pythons\enhance.py %1

pause