@echo off
REM Desktop Commander MCP installation script for Windows

echo Installing Desktop Commander MCP server...

REM Check Python version
for /f "tokens=2" %%I in ('python --version 2^>^&1') do set "PYTHON_VERSION=%%I"
for /f "tokens=1,2 delims=." %%A in ("%PYTHON_VERSION%") do (
    set "PYTHON_MAJOR=%%A"
    set "PYTHON_MINOR=%%B"
)

if %PYTHON_MAJOR% LSS 3 (
    echo Error: Python 3.10 or higher is required.
    echo Your Python version: %PYTHON_VERSION%
    exit /b 1
)

if %PYTHON_MAJOR% EQU 3 (
    if %PYTHON_MINOR% LSS 10 (
        echo Error: Python 3.10 or higher is required.
        echo Your Python version: %PYTHON_VERSION%
        exit /b 1
    )
)

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Install the package in development mode
echo Installing Desktop Commander in development mode...
pip install -e .

REM Run setup script to register with Claude desktop
echo Setting up Claude desktop integration...
python -m desktop_commander.mcp_server setup

echo Installation complete!
echo To use Desktop Commander MCP:
echo 1. Restart Claude if it's currently running
echo 2. The server will be available in Claude's MCP server list as 'desktopCommanderPy'

pause
