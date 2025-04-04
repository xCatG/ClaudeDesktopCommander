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
- `edit_block`: Apply a single surgical text replacement to a file
- `edit_file`: Apply multiple text replacements to a file in one operation
- `write_file`: Complete file rewrites with smart handling of different file types

#### Enhanced JSON Handling
The `write_file` tool automatically:
- Detects and formats JSON content (regardless of file extension)
- Validates JSON syntax and provides helpful error messages
- Creates parent directories automatically
- Preserves non-ASCII characters in JSON files

#### JSON File Operations

The project includes specialized tools for JSON files:

1. **Create/overwrite JSON with `save_json`:**
```python
# Complete JSON replacement, properly formatted
save_json(
    "config.json", 
    '{"name": "Test Configuration", "version": "1.0.0", "debug": false}'
)

# Triple-quoted strings work great for complex JSON
save_json("config.json", """
{
  "name": "Test Configuration",
  "version": "1.0.0",
  "settings": {
    "debug": false,
    "maxRetries": 3
  }
}
""")
```

2. **Update specific JSON properties with `edit_json`:**
```python
# Only modifies the specified keys, keeps the rest unchanged
edit_json(
    "config.json", 
    '{"version": "1.1.0", "settings.debug": true}'
)

# Supports dot notation for nested properties
edit_json("config.json", """
{
  "version": "2.0.0",
  "settings.maxRetries": 5,
  "settings.timeout": 60000,
  "features": ["export", "sharing", "reporting"]
}
""")
```

3. **Using the general `write_file` tool:**
```python
# When using write_file, JSON must be a properly formatted string
write_file(
    "config.json", 
    '{"name": "Test Configuration", "version": "1.0.0", "debug": false}'
)
```

Both `save_json` and `edit_json` automatically:
- Add the `.json` extension if not included in the path
- Create parent directories if they don't exist
- Format JSON with proper indentation
- Support project-relative paths with the `proj:` prefix

#### File Editing Options
1. **Single Edit** with `edit_block`:
```python
edit_block(
    file="config.json",
    search='"version": "1.0.0"',
    replace='"version": "1.1.0"',
    dry_run=False  # Set to True to preview changes
)
```

2. **Multiple Edits** with `edit_file`:
```python
edit_file(
    file="config.json",
    edits=[
        {"oldText": '"version": "1.0.0"', "newText": '"version": "1.1.0"'},
        {"oldText": '"debug": false', "newText": '"debug": true'}
    ]
)
```

## Security Features

- Blocked commands list prevents dangerous operations
- Directory whitelist controls which paths can be accessed (configured in config.json)
- Path validation ensures file access is limited to whitelisted directories
- Cross-platform path handling for both Windows and Linux/macOS
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

## Directory Whitelist Configuration

The Desktop Commander restricts file access to directories specified in the `dir_whitelist` in `config.json`:

```json
{
  "dir_whitelist": [
    "",                // Empty string means home directory itself
    "src",             // ~/src directory (relative to home)
    "work/src",        // ~/work/src directory
    "/tmp",            // Absolute path (Linux/Unix)
    "C:/tmp",          // Windows path with forward slashes
    "C:\\Users\\Public", // Windows path with backslashes
    "D:\\my_av"        // Another Windows path with backslashes
  ]
}
```

The whitelist supports:
- **Relative paths**: Relative to the user's home directory (e.g., "src", "documents/projects")
- **Absolute paths**: Full paths that start with "/" (Unix/Linux) or drive letters (Windows)
- **Home directory**: An empty string ("") allows access to the home directory itself
- **Windows paths**: Supports both forward slashes ("C:/Users") and backslashes ("C:\\Users")
- **Cross-platform paths**: Works on both Windows and Linux/macOS regardless of where you run it

If a path is not within any of the whitelisted directories, the operation will be blocked with an "Access denied" error.

## Troubleshooting

- **Connection Issues**: Ensure Claude desktop is properly configured and restarted after installation
- **Permission Errors**: Check that scripts have executable permissions
- **Path Access Errors**: Only paths within whitelisted directories can be accessed
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