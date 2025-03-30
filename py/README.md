# Desktop Commander MCP - Python Version

A Python port of the Desktop Commander MCP server that allows Claude desktop app to execute terminal commands on your computer and manage processes through Model Context Protocol (MCP).

## Features

- Execute terminal commands with output streaming
- Command timeout and background execution support
- Process management (list and kill processes)
- Session management for long-running commands
- Full filesystem operations:
  - Read/write files
  - Create/list directories
  - Move files/directories
  - Search files
  - Get file metadata
  - Code editing capabilities:
  - Surgical text replacements for small changes
  - Full file rewrites for major changes
  - Multiple file support
  - Pattern-based replacements
  - Text searching in files

## Installation

### Prerequisites

- Python 3.10 or higher
- [Claude Desktop App](https://claude.ai/download)

### Option 1: Install from PyPI

```bash
pip install desktop-commander-py
desktop-commander-py-setup
```

### Option 2: Install from Source

```bash
git clone https://github.com/yourusername/desktop-commander-py.git
cd desktop-commander-py
pip install -e .
python -m desktop_commander.main setup
```

## Usage

The server provides these tool categories:

### Terminal Tools
- `execute_command`: Run commands with configurable timeout
- `read_output`: Get output from long-running commands
- `force_terminate`: Stop running command sessions
- `list_sessions`: View active command sessions
- `list_processes`: View system processes
- `kill_process`: Terminate processes by PID
- `block_command`/`unblock_command`: Manage command blacklist

### Filesystem Tools
- `read_file`/`write_file`: File operations
- `create_directory`/`list_directory`: Directory management  
- `move_file`: Move/rename files
- `search_files`: Pattern-based file search
- `get_file_info`: File metadata
- `code_search`: Text and code search

### Edit Tools
- `edit_block`: Apply surgical text replacements (best for changes <20% of file size)
- `write_file`: Complete file rewrites (best for large changes >20% or when edit_block fails)

Search/Replace Block Format:
```
filepath.ext
<<<<<<< SEARCH
new code to insert
>>>>>>> REPLACE
```

## Security Features

- Blocked commands list prevents dangerous operations
- Path validation restricts file access to allowed directories
- Symlink security to prevent path traversal attacks

## Handling Long-Running Commands

For commands that may take a while:

1. `execute_command` returns after timeout with initial output
2. Command continues in background
3. Use `read_output` with PID to get new output
4. Use `force_terminate` to stop if needed

## Implementation Details

This Python implementation uses the official Anthropic MCP Python SDK which:

- Handles JSON-RPC 2.0 communication
- Manages client-server lifecycle
- Negotiates capabilities
- Provides a clean interface for tool registration

## WSL Support

When running under Windows Subsystem for Linux (WSL):

- Use the `wsl` command in the Claude Desktop config
- Be aware of path differences between Windows and Linux
- The memo file is stored at the project root

## Troubleshooting

- **Connection Issues**: Ensure Claude desktop is properly configured and restarted after installation
- **Permission Errors**: Check that scripts have executable permissions
- **Path Access Errors**: Only paths within allowed directories can be accessed
- **Blocked Commands**: Some dangerous commands are blocked by default for security

## License

MIT
=======
new code to insert
>>>>>>> REPLACE
```

## Handling Long-Running Commands

For commands that may take a while:

1. `execute_command` returns after timeout with initial output
2. Command continues in background
3. Use `read_output` with PID to get new output
4. Use `force_terminate` to stop if needed

## Windows Subsystem for Linux (WSL) Support

If you want to run the Desktop Commander MCP server under WSL and make it available to Claude Desktop on Windows, you can add the following configuration to your `claude_desktop_config.json` file:

```json
"desktopCommanderPyWSL": {
  "command": "wsl",
  "args": [
    "-e", "bash", "-c", "cd /home/<username>/src/ClaudeDesktopCommander/py && source venv/bin/activate && python -m desktop_commander.mcp_server"
  ]
}
```

Replace `<username>` with your actual WSL username.

### Notes on WSL Setup:

- The setup script cannot directly modify the Windows configuration file from WSL since it runs in the Linux environment
- You'll need to manually add the entry to your Claude Desktop configuration file located at:
  - Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- Make sure the path to your project directory in WSL is correctly specified in the command
- The server needs to be started from the correct directory with the virtual environment activated

Future improvements:
- More generic path handling for WSL configuration
- Potential setup script enhancements to help with WSL configuration

## Security

Desktop Commander MCP has security features to protect your system:

- Blocked commands list to prevent dangerous operations
- Path validation to restrict file access to allowed directories
- Input validation for all operations

## License

MIT