"""
Command management for the Desktop Commander MCP server.
Handles blocked commands validation and management.
"""

import os
import json
from typing import List, Set
from mcp.server.fastmcp import FastMCP

# Default configuration path
DEFAULT_CONFIG_PATH = os.path.join(os.getcwd(), "config.json")

class CommandManager:
    def __init__(self, config_path: str = DEFAULT_CONFIG_PATH):
        """Initialize the command manager with the given config path."""
        self.config_path = config_path
        self.blocked_commands: Set[str] = set()
        self._load_blocked_commands()
    
    def _load_blocked_commands(self) -> None:
        """Load blocked commands from config file."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, "r") as f:
                    config = json.load(f)
                self.blocked_commands = set(config.get("blockedCommands", []))
            else:
                # Default blocked commands
                self.blocked_commands = {
                    "format", "mount", "umount", "mkfs", "fdisk", "dd",
                    "sudo", "su", "passwd", "adduser", "useradd", "usermod", "groupadd"
                }
                self._save_blocked_commands()
        except Exception as e:
            print(f"Error loading blocked commands: {e}")
            # Default to a safe set if loading fails
            self.blocked_commands = {
                "format", "mount", "umount", "mkfs", "fdisk", "dd",
                "sudo", "su", "passwd", "adduser", "useradd", "usermod", "groupadd"
            }
    
    def _save_blocked_commands(self) -> None:
        """Save blocked commands to config file."""
        try:
            config = {
                "blockedCommands": list(sorted(self.blocked_commands))
            }
            with open(self.config_path, "w") as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            print(f"Error saving blocked commands: {e}")
    
    def validate_command(self, command: str) -> bool:
        """Check if a command is allowed to run."""
        base_command = command.split()[0].lower().strip()
        return base_command not in self.blocked_commands
    
    def block_command(self, command: str) -> bool:
        """Add a command to the blocked list."""
        command = command.lower().strip()
        if command in self.blocked_commands:
            return False
        
        self.blocked_commands.add(command)
        self._save_blocked_commands()
        return True
    
    def unblock_command(self, command: str) -> bool:
        """Remove a command from the blocked list."""
        command = command.lower().strip()
        if command not in self.blocked_commands:
            return False
        
        self.blocked_commands.remove(command)
        self._save_blocked_commands()
        return True
    
    def list_blocked_commands(self) -> List[str]:
        """Return a sorted list of blocked commands."""
        return sorted(list(self.blocked_commands))


def register_command_tools(mcp_server: FastMCP, command_manager: CommandManager = None) -> None:
    """Register command management tools with the MCP server."""
    if command_manager is None:
        command_manager = CommandManager()
    
    @mcp_server.tool()
    def block_command(command: str) -> str:
        """
        Add a command to the blacklist. Once blocked, the command cannot be executed until unblocked.
        """
        success = command_manager.block_command(command)
        if success:
            return f"Command '{command}' is now blocked"
        else:
            return f"Command '{command}' is already blocked"
    
    @mcp_server.tool()
    def unblock_command(command: str) -> str:
        """
        Remove a command from the blacklist. Once unblocked, the command can be executed normally.
        """
        success = command_manager.unblock_command(command)
        if success:
            return f"Command '{command}' is now unblocked"
        else:
            return f"Command '{command}' is not blocked"
    
    @mcp_server.tool()
    def list_blocked_commands() -> str:
        """
        List all currently blocked commands.
        """
        blocked = command_manager.list_blocked_commands()
        if not blocked:
            return "No commands are currently blocked"
        
        return "Blocked commands:\n" + "\n".join(blocked)

# Create default command manager instance
command_manager = CommandManager()