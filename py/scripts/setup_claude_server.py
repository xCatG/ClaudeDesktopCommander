#!/usr/bin/env python3
import os
import sys
import json
import platform
import logging
import asyncio
from pathlib import Path


# Determine OS and set appropriate config path
def get_claude_config_path():
    """Get the path to Claude desktop config file based on OS."""
    system = platform.system()
    home_dir = os.path.expanduser("~")
    
    if system == "Windows":
        return os.path.join(os.environ.get("APPDATA", ""), "Claude", "claude_desktop_config.json")
    elif system == "Darwin":  # macOS
        return os.path.join(home_dir, "Library", "Application Support", "Claude", "claude_desktop_config.json")
    else:  # Linux and others
        return os.path.join(home_dir, ".config", "Claude", "claude_desktop_config.json")


# Setup logging
def setup_logging():
    """Set up logging for the setup script."""
    log_file = os.path.join(os.getcwd(), "setup.log")
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return logging.getLogger(__name__)


async def main():
    """Main setup function for Claude desktop integration."""
    logger = setup_logging()
    logger.info("Starting Claude desktop setup")
    
    # Get Claude config path
    claude_config_path = get_claude_config_path()
    logger.info(f"Claude config path: {claude_config_path}")
    
    # Check if config file exists and create default if not
    if not os.path.exists(claude_config_path):
        logger.info(f"Claude config file not found at: {claude_config_path}")
        logger.info("Creating default config file...")
        
        # Create parent directory if it doesn't exist
        os.makedirs(os.path.dirname(claude_config_path), exist_ok=True)
        
        # Create default config based on OS
        system = platform.system()
        if system == "Windows":
            default_config = {
                "serverConfig": {
                    "command": "cmd.exe",
                    "args": ["/c"]
                }
            }
        else:  # macOS/Linux
            default_config = {
                "serverConfig": {
                    "command": "/bin/sh",
                    "args": ["-c"]
                }
            }
        
        # Write default config
        with open(claude_config_path, "w") as f:
            json.dump(default_config, f, indent=2)
            
        logger.info("Default config file created")
    
    try:
        # Read existing config
        with open(claude_config_path, "r") as f:
            config = json.load(f)
        
        # Prepare the server config
        # Check if running from installed package or local directory
        script_path = os.path.abspath(sys.argv[0])
        is_installed = "site-packages" in script_path
        
        if is_installed:
            server_config = {
                "command": sys.executable,
                "args": ["-m", "desktop_commander.main"]
            }
        else:
            # Running from local directory
            server_config = {
                "command": sys.executable,
                "args": [os.path.join(os.getcwd(), "desktop_commander", "main.py")]
            }
        
        # Add or update the MCP server config
        if "mcpServers" not in config:
            config["mcpServers"] = {}
        
        config["mcpServers"]["desktopCommanderPy"] = server_config
        
        # Write the updated config back
        with open(claude_config_path, "w") as f:
            json.dump(config, f, indent=2)
        
        logger.info("Successfully added MCP server to Claude configuration!")
        logger.info(f"Configuration location: {claude_config_path}")
        logger.info(
            "\nTo use the server:\n"
            "1. Restart Claude if it's currently running\n"
            "2. The server will be available in Claude's MCP server list"
        )
        
    except Exception as e:
        logger.error(f"Error updating Claude configuration: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())