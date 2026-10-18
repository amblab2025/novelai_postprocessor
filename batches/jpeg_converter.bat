@echo off
cd /d %~dp0

call ..\.venv\Scripts\activate
python ..\pythons\jpeg_converter.py %1

pause