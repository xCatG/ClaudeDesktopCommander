#!/usr/bin/env python3
import asyncio
import sys
import os
import signal
import json
from importlib import import_module
from pathlib import Path

from desktop_commander.server import server
from desktop_commander.command_manager import command_manager
from desktop_commander.version import VERSION


def setup_signal_handlers():
    """Set up handlers for graceful shutdown."""
    def handle_exit(signum, frame):
        print(f"Received signal {signum}, shutting down...", file=sys.stderr)
        sys.exit(0)
    
    # Handle SIGINT (Ctrl+C) and SIGTERM
    signal.signal(signal.SIGINT, handle_exit)
    signal.signal(signal.SIGTERM, handle_exit)


async def run_setup():
    """Run the setup script for Claude desktop integration."""
    try:
        # Get the directory of the current script
        current_dir = Path(__file__).parent.parent
        
        # Import and run the setup script
        setup_script = current_dir / "scripts" / "setup_claude_server.py"
        
        if setup_script.exists():
            # Use importlib to import the module dynamically
            module_name = "scripts.setup_claude_server"
            setup_module = import_module(module_name)
            
            # Call the main function if it exists
            if hasattr(setup_module, "main"):
                await setup_module.main()
            else:
                print("Setup script does not have a main function", file=sys.stderr)
        else:
            print(f"Setup script not found at {setup_script}", file=sys.stderr)
    except Exception as e:
        print(f"Error running setup: {str(e)}", file=sys.stderr)
        sys.exit(1)


async def main():
    """Main entry point for the Desktop Commander MCP server."""
    try:
        # Check if first argument is "setup"
        if len(sys.argv) > 1 and sys.argv[1] == "setup":
            await run_setup()
            return
        
        # Set up signal handlers
        setup_signal_handlers()
        
        # Print startup message
        print(f"Desktop Commander MCP Server v{VERSION} starting...", file=sys.stderr)
        
        # Load blocked commands
        await command_manager.load_blocked_commands()
        
        # Run the server
        await server.run()
        
    except Exception as e:
        print(f"Fatal error: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())