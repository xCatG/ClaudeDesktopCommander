# Desktop Commander MCP

[![npm downloads](https://img.shields.io/npm/dw/@wonderwhy-er/desktop-commander)](https://www.npmjs.com/package/@wonderwhy-er/desktop-commander)
[![smithery badge](https://smithery.ai/badge/@wonderwhy-er/desktop-commander)](https://smithery.ai/server/@wonderwhy-er/desktop-commander)
[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-support-yellow.svg)](https://www.buymeacoffee.com/wonderwhyer)

[![Discord](https://img.shields.io/badge/Join%20Discord-5865F2?style=for-the-badge&logo=discord&logoColor=white)](https://discord.gg/kQ27sNnZr7)

Short version. Two key things. Terminal commands and diff based file editing.

![Desktop Commander MCP](logo.png)

<a href="https://glama.ai/mcp/servers/zempur9oh4">
  <img width="380" height="200" src="https://glama.ai/mcp/servers/zempur9oh4/badge" alt="Claude Desktop Commander MCP server" />
</a>

## Table of Contents
- [Features](#features)
- [Implementations](#implementations)
- [Installation](#installation)
- [Usage](#usage)
- [Handling Long-Running Commands](#handling-long-running-commands)
- [Docker Support](#docker-support)
- [Work in Progress and TODOs](#work-in-progress-and-todos)
- [Media links](#media)
- [Testimonials](#testimonials)
- [Contributing](#contributing)
- [License](#license)

This is a server that allows Claude desktop app to execute long-running terminal commands on your computer and manage processes through Model Context Protocol (MCP) + Built on top of [MCP Filesystem Server](https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem) to provide additional search and replace file editing capabilities.

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
  - vscode-ripgrep based recursive code or text search in folders

## Implementations

This repository contains two implementations of the Desktop Commander MCP:

1. **TypeScript Implementation** (Original) - Located in the `/ts` directory
2. **Python Implementation** - Located in the `/py` directory

Choose the implementation that best fits your environment and preferences. Both provide the same core functionality.

## Installation

First, ensure you've downloaded and installed the [Claude Desktop app](https://claude.ai/download).

### TypeScript Implementation

#### Option 1: Installing via Smithery

To install Desktop Commander for Claude Desktop automatically via [Smithery](https://smithery.ai/server/@wonderwhy-er/desktop-commander):

```bash
npx -y @smithery/cli install @wonderwhy-er/desktop-commander --client claude
```

#### Option 2: Install through npx
Just run this in terminal
```
npx @wonderwhy-er/desktop-commander setup
```
Restart Claude if running

#### Option 3: Add to claude_desktop_config by hand
Add this entry to your claude_desktop_config.json (on Mac, found at ~/Library/Application\ Support/Claude/claude_desktop_config.json):
```json
{
  "mcpServers": {
    "desktop-commander": {
      "command": "npx",
      "args": [
        "-y",
        "@wonderwhy-er/desktop-commander"
      ]
    }
  }
}
```
Restart Claude if running

#### Option 4: Checkout locally
1. Clone and build:
```bash
git clone https://github.com/wonderwhy-er/ClaudeComputerCommander.git
cd ClaudeComputerCommander/ts
npm run setup
```
Restart Claude if running

### Python Implementation

#### Option 1: Install using pip
```bash
cd ClaudeComputerCommander/py
pip install -e .
python -m desktop_commander.main setup
```
Restart Claude if running

#### Option 2: Run directly from source
```bash
cd ClaudeComputerCommander/py
pip install -r requirements.txt
python -m desktop_commander.main setup
```
Restart Claude if running

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
- `code_search`: Recursive ripgrep based text and code search

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

Example:
```
src/main.js
<<<<<<< SEARCH
console.log("old message");
=======
console.log("new message");
>>>>>>> REPLACE
```

## Handling Long-Running Commands

For commands that may take a while:

1. `execute_command` returns after timeout with initial output
2. Command continues in background
3. Use `read_output` with PID to get new output
4. Use `force_terminate` to stop if needed

## Docker Support

Both implementations can be run in Docker containers.

### TypeScript Docker Support

The TypeScript implementation includes a Dockerfile in the `/ts` directory:

```bash
cd ts
docker build -t desktop-commander-ts .
docker run -it --rm desktop-commander-ts
```

### Python Docker Support

To run the Python implementation in Docker:

```bash
cd py
docker build -t desktop-commander-py .
docker run -it --rm desktop-commander-py
```

## Model Context Protocol Integration

This project extends the MCP Filesystem Server to enable:
- Local server support in Claude Desktop
- Full system command execution
- Process management
- File operations
- Code editing with search/replace blocks

Created as part of exploring Claude MCPs: https://youtube.com/live/TlbjFDbl5Us

## DONE
- **25-03-2025 Better code search** ([in progress](https://github.com/wonderwhy-er/ClaudeDesktopCommander/pull/17)) - Enhanced code exploration with context-aware results
- **Added Python implementation** - Alternative implementation for Python environments

## Work in Progress and TODOs

The following features are currently being developed or planned:

- **Better configurations** ([in progress](https://github.com/wonderwhy-er/ClaudeDesktopCommander/pull/16)) - Improved settings for allowed paths, commands and shell environment
- **Windows environment fixes** ([in progress](https://github.com/wonderwhy-er/ClaudeDesktopCommander/pull/13)) - Resolving issues specific to Windows platforms
- **Linux improvements** ([in progress](https://github.com/wonderwhy-er/ClaudeDesktopCommander/pull/12)) - Enhancing compatibility with various Linux distributions
- **Support for WSL** - Windows Subsystem for Linux integration
- **Support for SSH** - Remote server command execution
- **Installation troubleshooting guide** - Comprehensive help for setup issues

## Media
Learn more about this project through these resources:

### Article
[Claude with MCPs replaced Cursor & Windsurf. How did that happen?](https://wonderwhy-er.medium.com/claude-with-mcps-replaced-cursor-windsurf-how-did-that-happen-c1d1e2795e96) - A detailed exploration of how Claude with Model Context Protocol capabilities is changing developer workflows.

### Video
[Claude Desktop Commander Video Tutorial](https://www.youtube.com/watch?v=ly3bed99Dy8) - Watch how to set up and use the Commander effectively.

### Community
Join our [Discord server](https://discord.gg/7cbccwRp) to get help, share feedback, and connect with other users.

## Testimonials

[![It's a life saver! I paid Claude + Cursor currently which I always feel it's kind of duplicated. This solves the problem ultimately. I am so happy. Thanks so much. Plus today Claude has added the web search support. With this MCP + Internet search, it writes the code with the latest updates. It's so good when Cursor doesn't work sometimes or all the fast requests are used.](testemonials/img.png) https://www.youtube.com/watch?v=ly3bed99Dy8&lc=UgyyBt6_ShdDX_rIOad4AaABAg
](https://www.youtube.com/watch?v=ly3bed99Dy8&lc=UgyyBt6_ShdDX_rIOad4AaABAg
)

[Additional testimonials...]

## Contributing

If you find this project useful, please consider giving it a ⭐ star on GitHub! This helps others discover the project and encourages further development.

We welcome contributions from the community! Whether you've found a bug, have a feature request, or want to contribute code, here's how you can help:

- **Found a bug?** Open an issue at [GitHub Issues](https://github.com/wonderwhy-er/ClaudeComputerCommander/issues)
- **Have a feature idea?** Submit a feature request in the issues section
- **Want to contribute code?** Fork the repository, create a branch, and submit a pull request
- **Questions or discussions?** Start a discussion in the GitHub Discussions tab

All contributions, big or small, are greatly appreciated!

If you find this tool valuable for your workflow, please consider [supporting the project](https://www.buymeacoffee.com/wonderwhyer).

## License

MIT