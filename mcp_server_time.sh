#!/bin/bash
# wrapper.sh

source /home/yenchi/src/ClaudeDesktopCommander/venv/bin/activate

#SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Activate the virtual environment using absolute path
#source "$SCRIPT_DIR/venv/bin/activate"

# Run the MCP server
python -m mcp_server_time --local-timezone=America/Los_Angeles
