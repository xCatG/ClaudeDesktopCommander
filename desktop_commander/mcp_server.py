#!/usr/bin/env python3
"""
Desktop Commander MCP server using the official Anthropic MCP SDK.
This entry point initializes the MCP server and handles all MCP protocol requirements.
"""

import os
import sys
import asyncio
import traceback
from importlib import import_module
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Try to import the mcp module
try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    print("Error: MCP SDK not found. Please install it with: pip install mcp", file=sys.stderr)
    sys.exit(1)

# Import the server module that contains the FastMCP instance
try:
    from desktop_commander.mcp_implementation import mcp
except ImportError as e:
    print(f"Error importing MCP implementation: {e}", file=sys.stderr)
    traceback.print_exc(file=sys.stderr)
    sys.exit(1)

def main():
    """Main entry point for the MCP server."""
    try:
        print("Desktop Commander MCP Server starting...", file=sys.stderr)
        print(f"Python version: {sys.version}", file=sys.stderr)
        print(f"Current directory: {os.getcwd()}", file=sys.stderr)
        
        # List available tools categories
        print("Available tool categories:", file=sys.stderr)
        print("- Terminal tools: execute_command, read_output, force_terminate, list_sessions", file=sys.stderr)
        print("- Process tools: list_processes, kill_process", file=sys.stderr)
        print("- Filesystem tools: read_file, write_file, list_directory, create_directory, etc.", file=sys.stderr)
        print("- Command management: block_command, unblock_command, list_blocked_commands", file=sys.stderr)
        print("- Project tools: discover_projects, use_project, get_current_project, explore_project", file=sys.stderr)
        print("- Knowledge graph tools: save_project_knowledge, list_knowledge_graphs, get_project_knowledge", file=sys.stderr)
        print("- Memory bridge tools: query_memory_graph, search_memory_nodes, get_memory_entities, sync_memory_to_project_knowledge", file=sys.stderr)

        # Run the MCP server
        # The run() method automatically handles all of the MCP protocol
        # including initialization, capability negotiation, and message handling
        mcp.run()
    except Exception as e:
        print(f"Fatal error: {str(e)}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()