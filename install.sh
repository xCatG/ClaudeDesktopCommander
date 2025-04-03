#!/bin/bash
# Desktop Commander MCP installation script

set -e  # Exit on error

echo "Installing Desktop Commander MCP server..."

# Check if Python 3.10+ is available
python_version=$(python3 --version 2>&1 | awk '{print $2}')
python_major=$(echo $python_version | cut -d. -f1)
python_minor=$(echo $python_version | cut -d. -f2)

if [ "$python_major" -lt 3 ] || ([ "$python_major" -eq 3 ] && [ "$python_minor" -lt 10 ]); then
    echo "Error: Python 3.10 or higher is required."
    echo "Your Python version: $python_version"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Install the package in development mode
echo "Installing Desktop Commander in development mode..."
pip install -e .

# Run setup script to register with Claude desktop
echo "Setting up Claude desktop integration..."
python -m desktop_commander.mcp_server setup

echo "Installation complete!"
echo "To use Desktop Commander MCP:"
echo "1. Restart Claude if it's currently running"
echo "2. The server will be available in Claude's MCP server list as 'desktopCommanderPy'"
