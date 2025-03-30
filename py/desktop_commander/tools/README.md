# Desktop Commander Tools

This directory contains the modular tools for the Desktop Commander MCP server.

## Tools Overview

### Terminal Tools (terminal.py)

Command execution and session management:
- `execute_command`: Run terminal commands with timeout
- `read_output`: Get output from long-running commands
- `force_terminate`: Kill a running session
- `list_sessions`: Show active command sessions

### Process Tools (process.py)

Process management:
- `list_processes`: Show all system processes
- `kill_process`: Terminate processes by PID

### Filesystem Tools (filesystem.py)

- Basic operations:
  - `read_file`, `write_file`
  - `list_directory`, `create_directory`
  - `move_file`, `get_file_info`
  - `list_allowed_directories`

- Search and editing:
  - `search_files`: Find files by name
  - `search_code`: Search file contents (uses ripgrep when available)
  - `edit_block`: Apply surgical text replacements

### Memo Tools (memo_tool.py)

- `read_memo`: Read the Claude memory file
- `write_memo`: Replace the memory file content
- `append_memo`: Add content to the memory file

## Implementation Notes

Each tool category is implemented as a separate Python module with a `register_tools` function that registers the tools with the MCP server.
