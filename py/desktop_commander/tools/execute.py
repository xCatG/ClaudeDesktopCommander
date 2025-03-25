from typing import Dict, Any, List
from desktop_commander.terminal_manager import terminal_manager
from desktop_commander.command_manager import command_manager
from desktop_commander.tools.schemas import (
    ExecuteCommandArgs,
    ReadOutputArgs,
    ForceTerminateArgs,
    ListSessionsArgs
)
from desktop_commander.types import ToolResponse


async def execute_command(args: ExecuteCommandArgs) -> ToolResponse:
    """Execute a terminal command."""
    # Validate command is allowed
    if not command_manager.validate_command(args.command):
        raise Exception(f"Command not allowed: {args.command}")
    
    # Execute command
    result = await terminal_manager.execute_command(
        args.command,
        args.timeout_ms if args.timeout_ms is not None else None
    )
    
    message = (
        f"Command started with PID {result.pid}\n"
        f"Initial output:\n{result.output}"
    )
    
    if result.is_blocked:
        message += "\nCommand is still running. Use read_output to get more output."
    
    return ToolResponse(
        content=[{"type": "text", "text": message}]
    )


async def read_output(args: ReadOutputArgs) -> ToolResponse:
    """Read new output from a running terminal session."""
    output = terminal_manager.get_new_output(args.pid)
    
    message = (
        "No session found for PID {args.pid}" if output is None
        else output or "No new output available"
    )
    
    return ToolResponse(
        content=[{"type": "text", "text": message}]
    )


async def force_terminate(args: ForceTerminateArgs) -> ToolResponse:
    """Force terminate a running terminal session."""
    success = terminal_manager.force_terminate(args.pid)
    
    message = (
        f"Successfully initiated termination of session {args.pid}" if success
        else f"No active session found for PID {args.pid}"
    )
    
    return ToolResponse(
        content=[{"type": "text", "text": message}]
    )


async def list_sessions() -> ToolResponse:
    """List all active terminal sessions."""
    sessions = terminal_manager.list_active_sessions()
    
    if not sessions:
        message = "No active sessions"
    else:
        message = "\n".join(
            f"PID: {s.pid}, Blocked: {s.is_blocked}, "
            f"Runtime: {round(s.runtime / 1000)}s"
            for s in sessions
        )
    
    return ToolResponse(
        content=[{"type": "text", "text": message}]
    )