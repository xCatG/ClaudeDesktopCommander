import os
import signal
import psutil
from typing import List, Dict
import asyncio

from desktop_commander.types import ProcessInfo, ToolResponse
from desktop_commander.tools.schemas import KillProcessArgs


async def list_processes() -> ToolResponse:
    """List all running processes."""
    processes = []
    
    async with asyncio.to_thread():
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cpu_percent', 'memory_percent']):
            try:
                # Get process info
                pinfo = proc.info
                command = " ".join(pinfo['cmdline']) if pinfo['cmdline'] else pinfo['name']
                
                processes.append(ProcessInfo(
                    pid=pinfo['pid'],
                    command=command,
                    cpu=f"{pinfo['cpu_percent']:.1f}%",
                    memory=f"{pinfo['memory_percent']:.1f}%"
                ))
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
    
    # Format output
    message = "\n".join(
        f"PID: {p.pid}, Command: {p.command}, CPU: {p.cpu}, Memory: {p.memory}"
        for p in processes
    )
    
    return ToolResponse(
        content=[{"type": "text", "text": message}]
    )


async def kill_process(args: KillProcessArgs) -> ToolResponse:
    """Terminate a running process by PID."""
    try:
        async with asyncio.to_thread():
            os.kill(args.pid, signal.SIGTERM)
            
            # Give process a chance to terminate gracefully
            await asyncio.sleep(0.5)
            
            # If process still exists, force kill
            try:
                os.kill(args.pid, 0)  # Check if process exists
                os.kill(args.pid, signal.SIGKILL)
            except OSError:
                pass  # Process already terminated
                
        return ToolResponse(
            content=[{"type": "text", "text": f"Successfully terminated process {args.pid}"}]
        )
    except Exception as e:
        raise Exception(f"Failed to kill process: {str(e)}")