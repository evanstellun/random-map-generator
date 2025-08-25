#!/bin/bash

# Random Map Generator Linux Launcher
# Version 1.0

echo "Random Map Generator v1.0"
echo "============================"
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo "ERROR: Python not detected!"
    echo
    echo "Please install Python 3.6 or higher first"
    echo "Visit: https://www.python.org/downloads/"
    echo
    read -p "Press Enter to exit..."
    exit 1
fi

# Determine Python command
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
fi

echo "Python environment check passed (${PYTHON_CMD})"
echo

# Check dependencies
echo "Checking dependencies..."
if ! $PYTHON_CMD -c "import numpy, matplotlib, scipy, PyQt5" &> /dev/null; then
    echo "Installing dependencies..."
    if ! $PYTHON_CMD -m pip install -r requirements.txt; then
        echo "ERROR: Dependencies installation failed!"
        echo
        echo "Please run manually: ${PYTHON_CMD} -m pip install -r requirements.txt"
        read -p "Press Enter to exit..."
        exit 1
    fi
    echo "Dependencies installation completed"
else
    echo "Dependencies check passed"
fi

echo
echo "Starting Random Map System..."
echo

# Clean old log files and cache
rm -f server.log error.log
rm -rf __pycache__
find . -name "*.pyc" -delete

# Start server (background)
echo "Starting server..."
$PYTHON_CMD ranmap_server.py > server.log 2>&1 &
SERVER_PID=$!

# Wait for server to start
echo "Waiting for server to start..."
sleep 3

# Check if server started successfully
if ! $PYTHON_CMD -c "import socket; s=socket.socket(); s.settimeout(1); s.connect(('localhost', 5000)); s.close()" &> /dev/null; then
    echo "ERROR: Server startup failed!"
    echo
    echo "Please check server.log for details"
    kill $SERVER_PID 2>/dev/null
    read -p "Press Enter to exit..."
    exit 1
fi

echo "Server started successfully (PID: $SERVER_PID)"
echo

# Start GUI
echo "Starting GUI interface..."
$PYTHON_CMD gui_app.py &
GUI_PID=$!

echo
echo "System startup completed!"
echo "Server PID: $SERVER_PID"
echo "GUI PID: $GUI_PID"
echo "Log file: server.log"
echo
echo "Press Ctrl+C to stop all programs or close this window"
echo "(The server and GUI will continue running in background)"

# Wait for user interrupt
trap 'echo "Stopping programs..."; kill $SERVER_PID $GUI_PID 2>/dev/null; exit 0' INT

# Keep the script running
while true; do
    sleep 1
done