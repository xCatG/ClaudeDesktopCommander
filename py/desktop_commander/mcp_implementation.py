"""
Desktop Commander MCP implementation using the official Anthropic MCP SDK.
This file contains the FastMCP instance with all tools and resources registered.
Uses a simplified, modular structure with one file per tool category.
"""

import os
import sys
from mcp.server.fastmcp import FastMCP, Context

# Import command manager
from desktop_commander.mcp_command_manager import command_manager, register_command_tools

# Import tool modules - each module registers its tools via register_tools function
from desktop_commander.tools.terminal import register_tools as register_terminal_tools
from desktop_commander.tools.process import register_tools as register_process_tools
from desktop_commander.tools.filesystem import register_tools as register_filesystem_tools
from desktop_commander.tools.memo import register_tools as register_memo_tools
from desktop_commander.tools.project import register_tools as register_project_tools

# Define our MCP server
mcp = FastMCP("Desktop Commander")

# Register command management tools
register_command_tools(mcp, command_manager)

# Register all modular tools
register_terminal_tools(mcp, command_manager)
register_process_tools(mcp)
register_filesystem_tools(mcp)
register_memo_tools(mcp)
register_project_tools(mcp)

# Print initialization message
print(f"Desktop Commander MCP Server initialized", file=sys.stderr)
