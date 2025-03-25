import json
import os
from typing import Set, List
from desktop_commander.config import CONFIG_FILE


class CommandManager:
    def __init__(self):
        self.blocked_commands: Set[str] = set()
        
    async def load_blocked_commands(self) -> None:
        """Load blocked commands from config file."""
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, "r") as f:
                    config = json.load(f)
                self.blocked_commands = set(config.get("blockedCommands", []))
            else:
                self.blocked_commands = set()
        except Exception:
            self.blocked_commands = set()
            
    async def save_blocked_commands(self) -> None:
        """Save blocked commands to config file."""
        try:
            config = {
                "blockedCommands": list(self.blocked_commands)
            }
            with open(CONFIG_FILE, "w") as f:
                json.dump(config, f, indent=2)
        except Exception:
            # Handle error if needed
            pass
            
    def validate_command(self, command: str) -> bool:
        """Check if a command is allowed to run."""
        base_command = command.split()[0].lower().strip()
        return base_command not in self.blocked_commands
        
    async def block_command(self, command: str) -> bool:
        """Add a command to the blocked list."""
        command = command.lower().strip()
        if command in self.blocked_commands:
            return False
            
        self.blocked_commands.add(command)
        await self.save_blocked_commands()
        return True
        
    async def unblock_command(self, command: str) -> bool:
        """Remove a command from the blocked list."""
        command = command.lower().strip()
        if command not in self.blocked_commands:
            return False
            
        self.blocked_commands.remove(command)
        await self.save_blocked_commands()
        return True
        
    def list_blocked_commands(self) -> List[str]:
        """Return a sorted list of blocked commands."""
        return sorted(list(self.blocked_commands))


# Singleton instance
command_manager = CommandManager()