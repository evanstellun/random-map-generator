@echo off
title Random Map Generator
color 0A

:: Set window title and colors
echo.
echo  Random Map Generator v1.0
echo.

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not detected!
    echo.
    echo Please install Python 3.6 or higher first
    echo Download: https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

echo Python environment check passed
echo.

:: Check dependencies
echo Checking dependencies...
python -c "import numpy, matplotlib, scipy, PyQt5" >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing dependencies...
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo ERROR: Dependencies installation failed!
        echo.
        echo Please run manually: pip install -r requirements.txt
        pause
        exit /b 1
    )
    echo Dependencies installation completed
) else (
    echo Dependencies check passed
)

echo.
echo Starting Random Map System...
echo.

:: clean old log files and cache
if exist server.log del server.log
if exist error.log del error.log
if exist __pycache__ rmdir /s /q __pycache__
if exist *.pyc del /q *.pyc

:: Start server (background)
start "" /b python ranmap_server.py > server.log 2>^&1

:: Wait for server to start
echo Waiting for server to start...
timeout /t 3 /nobreak > nul

:: Check if server started successfully
python -c "import socket; s=socket.socket(); s.settimeout(1); s.connect(('localhost', 5000)); s.close()" >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Server startup failed!
    echo.
    echo Please check server.log for details
    pause
    exit /b 1
)

echo Server started successfully
echo.

:: Start GUI
echo Starting GUI interface...
start "" /b python gui_app.py

echo.
echo System startup completed!
echo Log file: server.log
echo.
echo Press any key to close this window (does not affect running programs)
pause > nul