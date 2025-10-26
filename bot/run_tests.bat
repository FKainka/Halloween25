@echo off
cd /d "%~dp0"
echo Running pytest tests...
C:\Projekte\Halloween25\.venv\Scripts\python.exe -m pytest tests/ -v --tb=short
pause
