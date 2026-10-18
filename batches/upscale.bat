@echo off
cd /d %~dp0

call ..\.venv\Scripts\activate
python ..\pythons\upscale.py %1

pause