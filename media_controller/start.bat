@echo off
echo ====================================
echo Halloween 2025 Media Controller
echo ====================================
echo.

cd /d %~dp0

REM Python pruefen
python --version >nul 2>&1
if errorlevel 1 (
    echo [FEHLER] Python ist nicht installiert!
    echo Bitte installiere Python von https://www.python.org/
    pause
    exit /b 1
)

echo [OK] Python gefunden
echo.

REM Virtual Environment aktivieren (falls vorhanden)
if exist "..\..\.venv\Scripts\activate.bat" (
    echo [INFO] Virtual Environment gefunden, aktiviere...
    call ..\..\.venv\Scripts\activate.bat
    echo.
)

REM Dependencies pruefen
echo Pruefe Dependencies...
python -c "import requests" >nul 2>&1
if errorlevel 1 (
    echo [INFO] Installiere Dependencies...
    pip install -r requirements.txt
    echo.
)

python -c "import yaml" >nul 2>&1
if errorlevel 1 (
    echo [INFO] Installiere PyYAML...
    pip install pyyaml
    echo.
)

echo [OK] Dependencies installiert
echo.

REM Config pruefen
if not exist "config.yaml" (
    echo [FEHLER] config.yaml nicht gefunden!
    echo Bitte erstelle eine config.yaml basierend auf dem Beispiel.
    pause
    exit /b 1
)

echo [OK] Konfiguration gefunden
echo.

REM universen.yaml pruefen
if not exist "..\notes\universen.yaml" (
    echo [WARNUNG] universen.yaml nicht gefunden unter ..\notes\
    echo Film-Spots werden aus config.yaml geladen.
    echo.
)

REM Logs-Verzeichnis erstellen
if not exist "logs" mkdir logs

echo ====================================
echo Starte Media Controller...
echo Druecke Ctrl+C zum Beenden
echo ====================================
echo.

python main.py

pause
