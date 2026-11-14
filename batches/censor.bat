@echo off
cd /d %~dp0

call ..\.venv\Scripts\activate
python ..\pythons\censor.py %1

pause