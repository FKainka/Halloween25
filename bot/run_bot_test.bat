@echo off
echo ========================================
echo Halloween Bot - Manual Testing
echo ========================================
echo.
echo Starting bot...
echo Use Telegram to test bot features
echo.
echo Test Checklist:
echo [  ] 1. /start command
echo [  ] 2. /help command  
echo [  ] 3. /punkte command (empty)
echo [  ] 4. Upload party photo (no caption)
echo [  ] 5. Send "Team: 480514" (Matrix)
echo [  ] 6. Upload photo with "Film: Matrix"
echo [  ] 7. Upload photo with "Team: 480514" (puzzle)
echo [  ] 8. /punkte command (with points)
echo.
echo Press Ctrl+C to stop bot
echo ========================================
echo.

cd /d "%~dp0"
C:\Projekte\Halloween25\.venv\Scripts\python.exe main.py

pause
