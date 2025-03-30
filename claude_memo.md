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

## TODOs
- Push recent changes to remote repository
- Test MCP integration with latest Claude Desktop app
- Consider documentation updates for new MCP implementation
- Add tool for Claude to modify this memo file (in progress)

## Recent Changes
- Implemented native MCP protocol support using Anthropic SDK
- Refactored setup script to use non-async implementation
- Updated configuration to use new MCP server structure
- Added dedicated MCP implementation files

## Usage Notes
- After setup, restart Claude Desktop app
- Server will be available as 'desktopCommanderPy' in Claude's MCP server list
