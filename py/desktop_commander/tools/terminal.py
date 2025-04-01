"""
Terminal tools for the Desktop Commander MCP Server.
Includes command execution and session management.
"""

import os
import sys
import signal
import asyncio
import subprocess
import time
import fcntl
import select
from datetime import datetime
from typing import Dict, Optional

# Session storage
active_sessions = {}
completed_sessions = {}

def _read_nonblocking(stream) -> str:
    """Read from a stream without blocking."""
    output = ""
    
    # Set non-blocking mode
    fd = stream.fileno()
    fl = fcntl.fcntl(fd, fcntl.F_GETFL)
    fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)
    
    try:
        # Check if there's data available to read
        if select.select([stream], [], [], 0)[0]:
            data = stream.read()
            if data:
                output += data
    except:
        pass
        
    return output

def register_tools(mcp, command_manager):
    """Register terminal command tools with the MCP server."""
    
    @mcp.tool()
    async def execute_command(command: str, timeout_ms: int = 1000) -> str:
        """
        Execute a terminal command with timeout. Command will continue running 
        in background if it doesn't complete within timeout.
        """
        print(f"Executing command: {command}", file=sys.stderr)
        
        # Validate command is allowed
        if not command_manager.validate_command(command):
            return f"Command not allowed: {command}"
        
        # Start the process
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # Ensure process.pid is defined
        if process.pid is None:
            raise ValueError("Failed to get process ID")
        
        # Create session
        session = {
            "pid": process.pid,
            "process": process,
            "last_output": "",
            "is_blocked": False,
            "start_time": datetime.now()
        }
        
        active_sessions[process.pid] = session
        
        # Collect output for the timeout period
        output = ""
        start_time = time.time()
        
        while time.time() - start_time < timeout_ms / 1000:
            # Check if process has completed
            if process.poll() is not None:
                stdout, stderr = process.communicate()
                output += stdout + stderr
                
                # Store in completed sessions
                completed_sessions[process.pid] = {
                    "pid": process.pid,
                    "output": output,
                    "exit_code": process.returncode,
                    "start_time": session["start_time"],
                    "end_time": datetime.now()
                }
                
                # Keep completed sessions manageable
                if len(completed_sessions) > 100:
                    oldest_pid = next(iter(completed_sessions))
                    del completed_sessions[oldest_pid]
                
                # Remove from active sessions
                if process.pid in active_sessions:
                    del active_sessions[process.pid]
                
                return f"Process {process.pid} completed with exit code {process.returncode}.\nOutput:\n{output}"
            
            # Read available output without blocking
            stdout_data = _read_nonblocking(process.stdout)
            stderr_data = _read_nonblocking(process.stderr)
            
            if stdout_data:
                output += stdout_data
                session["last_output"] += stdout_data
                
            if stderr_data:
                output += stderr_data
                session["last_output"] += stderr_data
                
            await asyncio.sleep(0.1)
        
        # Timeout reached, mark as blocked and return current output
        session["is_blocked"] = True
        return f"Command started with PID {process.pid}.\nInitial output (still running):\n{output}"

    @mcp.tool()
    def read_output(pid: int) -> str:
        """
        Read new output from a running terminal session.
        """
        # Check active sessions
        if pid in active_sessions:
            session = active_sessions[pid]
            output = session["last_output"]
            session["last_output"] = ""
            
            if not output:
                return f"No new output from process {pid}"
            
            return f"Output from process {pid}:\n{output}"
        
        # Check completed sessions
        if pid in completed_sessions:
            completed = completed_sessions[pid]
            runtime = (completed["end_time"] - completed["start_time"]).total_seconds()
            
            # After reading from completed session, remove it
            result = (
                f"Process {pid} completed with exit code {completed['exit_code']}\n"
                f"Runtime: {runtime}s\nFinal output:\n{completed['output']}"
            )
            
            del completed_sessions[pid]
            return result
        
        return f"No session found for PID {pid}"

    @mcp.tool()
    def force_terminate(pid: int) -> str:
        """
        Force terminate a running terminal session.
        """
        if pid not in active_sessions:
            return f"No active session found for PID {pid}"
        
        try:
            session = active_sessions[pid]
            process = session["process"]
            
            # First try SIGINT (Ctrl+C)
            process.send_signal(signal.SIGINT)
            
            # Wait a bit for graceful termination
            time.sleep(0.5)
            
            # If still running, force kill
            if process.poll() is None:
                process.kill()
            
            # Store in completed sessions
            completed_sessions[pid] = {
                "pid": pid,
                "output": session["last_output"],
                "exit_code": process.returncode if process.returncode is not None else -9,
                "start_time": session["start_time"],
                "end_time": datetime.now()
            }
            
            # Remove from active sessions
            del active_sessions[pid]
            
            return f"Successfully terminated process {pid}"
        except Exception as e:
            return f"Error terminating process {pid}: {str(e)}"

    @mcp.tool()
    def list_sessions() -> str:
        """
        List all active terminal sessions.
        """
        if not active_sessions:
            return "No active sessions"
        
        now = datetime.now()
        result = []
        
        for pid, session in active_sessions.items():
            runtime = (now - session["start_time"]).total_seconds()
            status = "Blocked" if session["is_blocked"] else "Running"
            result.append(f"PID: {pid}, Status: {status}, Runtime: {round(runtime)}s")
        
        return "\n".join(result)
