# Claude Desktop Commander - Memory File

## Project Overview
- Desktop Commander MCP allows Claude to execute terminal commands and manage files
- Two implementations: TypeScript (original) and Python 
- Recently added native MCP protocol support using Anthropic SDK
- Currently on `python` branch with recent commits not pushed to origin

## Implementation Details
- Python implementation in `/py` directory
- TypeScript implementation in `/ts` directory
- Both expose similar functionality but with language-specific implementations
- Recent changes focus on native MCP support vs previous approach

## Key Features
- Terminal command execution with timeout and background support
- Process management (list, kill)
- Session management for long-running commands
- Full filesystem operations (read/write, directory management)
- Code editing with search/replace functionality
- File search capabilities
- Claude memo functionality for persistent memory

## TODOs
- Push recent changes to remote repository
- Test MCP integration with latest Claude Desktop app
- Consider documentation updates for new MCP implementation

## Recent Changes
- Implemented native MCP protocol support using Anthropic SDK
- Refactored setup script to use non-async implementation
- Updated configuration to use new MCP server structure
- Added dedicated MCP implementation files
- Added Claude memo tools for cross-conversation memory

## Usage Notes
- After setup, restart Claude Desktop app
- Server will be available as 'desktopCommanderPy' in Claude's MCP server list
- Use read_memo, write_memo, and append_memo tools to maintain context


## Memory Test
- Successfully verified memo tools on March 29, 2025
- All three functions (read, write, append) are working properly
- This entry was added using the append_memo tool


## WSL Support - March 29, 2025
- Added documentation for running under Windows Subsystem for Linux (WSL)
- Added example configuration for claude_desktop_config.json
- Noted limitations around setup script and path handling for WSL
- Future improvement ideas: more generic path handling, setup script enhancements for WSL
