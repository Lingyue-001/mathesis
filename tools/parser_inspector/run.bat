@echo off
setlocal
cd /d "%~dp0"
set PYTHONDONTWRITEBYTECODE=1
set PYTHONUTF8=1

if not exist ".venv\Scripts\python.exe" (
    where py >nul 2>nul
    if errorlevel 1 (
        python -B -m venv .venv
    ) else (
        py -3 -B -m venv .venv
    )
    if errorlevel 1 goto failed
)

".venv\Scripts\python.exe" -B -c "import streamlit; assert streamlit.__version__ == '1.64.0'" >nul 2>nul
if errorlevel 1 (
    ".venv\Scripts\python.exe" -B -m pip install --no-cache-dir -r requirements.txt
    if errorlevel 1 goto failed
)

echo Parser Inspector: http://127.0.0.1:8501
echo Close this window or press Ctrl+C to stop.
if /I not "%~1"=="--no-browser" start "" "http://127.0.0.1:8501"
".venv\Scripts\python.exe" -B -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501 --server.headless true --server.fileWatcherType none --browser.gatherUsageStats false
if errorlevel 1 goto failed
exit /b 0

:failed
echo Startup failed. Python 3.10+ and internet access for first-time installation are required.
pause
exit /b 1
