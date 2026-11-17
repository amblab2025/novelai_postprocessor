@echo off
cd /d %~dp0

call ..\.venv\Scripts\activate
python ..\pythons\enhance.py %1 v4.5

pause