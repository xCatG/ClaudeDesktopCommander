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
existing code to replace
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

## Security

Desktop Commander MCP has security features to protect your system:

- Blocked commands list to prevent dangerous operations
- Path validation to restrict file access to allowed directories
- Input validation for all operations

## License

MIT