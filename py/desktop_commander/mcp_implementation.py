"""
Desktop Commander MCP implementation using the official Anthropic MCP SDK.
This file contains the FastMCP instance with all tools and resources registered.
"""

import os
import sys
import signal
import asyncio
import subprocess
import time
from datetime import datetime
import json
from typing import Optional, List, Dict, Any
import psutil
import fcntl
import select

from mcp.server.fastmcp import FastMCP, Context

# Import command manager
from desktop_commander.mcp_command_manager import command_manager, register_command_tools
# Import memo tool functions
from desktop_commander.tools.memo_tool import get_tool_functions as get_memo_tool_functions

# Define our MCP server
mcp = FastMCP("Desktop Commander")

# Register command management tools
register_command_tools(mcp, command_manager)

# Register memo tool functions
memo_functions = get_memo_tool_functions()
for name, tool_def in memo_functions.items():
    mcp.tool(name=name, description=tool_def["description"])(tool_def["function"])

# Store active sessions
active_sessions = {}
# Store completed sessions (last 100)
completed_sessions = {}

# === Terminal Tools ===

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

@mcp.tool()
def list_processes() -> str:
    """
    List all running processes. Returns process information including PID, command name, 
    CPU usage, and memory usage.
    """
    processes = []
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cpu_percent', 'memory_percent']):
        try:
            # Get process info
            pinfo = proc.info
            command = " ".join(pinfo['cmdline']) if pinfo['cmdline'] else pinfo['name']
            
            processes.append(
                f"PID: {pinfo['pid']}, Command: {command}, "
                f"CPU: {pinfo['cpu_percent']:.1f}%, Memory: {pinfo['memory_percent']:.1f}%"
            )
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    
    if not processes:
        return "No processes found"
    
    return "\n".join(processes)

@mcp.tool()
def kill_process(pid: int) -> str:
    """
    Terminate a running process by PID. Use with caution as this will 
    forcefully terminate the specified process.
    """
    try:
        process = psutil.Process(pid)
        process.terminate()
        
        # Give process a chance to terminate gracefully
        time.sleep(0.5)
        
        # If process still exists, force kill
        if psutil.pid_exists(pid):
            process.kill()
            
        return f"Successfully terminated process {pid}"
    except psutil.NoSuchProcess:
        return f"No process found with PID {pid}"
    except Exception as e:
        return f"Failed to kill process {pid}: {str(e)}"

# === Filesystem Tools ===

# @mcp.resource("allowed_directories://list")
# def get_allowed_directories() -> str:
#     """Return the list of directories that this server is allowed to access."""
#     allowed_dirs = [
#         os.getcwd(),  # Current working directory
#         os.path.expanduser("~")  # User's home directory
#     ]
#     return f"Allowed directories:\n" + "\n".join(allowed_dirs)
@mcp.tool()
def list_allowed_directories() -> str:
    """Return the list of directories that this server is allowed to access."""
    allowed_dirs = [
        os.getcwd(),  # Current working directory
        os.path.expanduser("~")  # User's home directory
    ]
    return f"Allowed directories:\n" + "\n".join(allowed_dirs)

@mcp.tool()
async def read_file(path: str) -> str:
    """
    Read the complete contents of a file from the file system. 
    Only works within allowed directories.
    """
    try:
        # Validate path
        valid_path = _validate_path(path)
        
        with open(valid_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        return content
    except Exception as e:
        return f"Error reading file: {str(e)}"

@mcp.tool()
async def write_file(path: str, content: str) -> str:
    """
    Completely replace file contents. Best for large changes or when edit_block fails.
    Only works within allowed directories.
    """
    try:
        # Validate path
        valid_path = _validate_path(path)
        
        with open(valid_path, "w", encoding="utf-8") as f:
            f.write(content)
            
        return f"Successfully wrote to {valid_path}"
    except Exception as e:
        return f"Error writing file: {str(e)}"

@mcp.tool()
async def edit_block(block_content: str) -> str:
    """
    Apply surgical text replacements to files. Format: 
    filepath
    <<<<<<< SEARCH
    content to find
    =======
    new content
    >>>>>>> REPLACE
    """
    try:
        # Parse the edit block
        lines = block_content.split('\n')
        
        # First line should be the file path
        file_path = lines[0].strip()
        
        # Find the markers
        search_start = -1
        divider = -1
        replace_end = -1
        
        for i, line in enumerate(lines):
            if line.strip() == '<<<<<<< SEARCH':
                search_start = i
            elif line.strip() == '=======':
                divider = i
            elif line.strip() == '>>>>>>> REPLACE':
                replace_end = i
        
        if search_start == -1 or divider == -1 or replace_end == -1:
            return 'Invalid edit block format - missing markers'
        
        # Extract search and replace content
        search = '\n'.join(lines[search_start + 1:divider])
        replace = '\n'.join(lines[divider + 1:replace_end])
        
        # Validate file path
        valid_path = _validate_path(file_path)
        
        # Read the file
        with open(valid_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Find first occurrence
        search_index = content.find(search)
        if search_index == -1:
            return f"Search content not found in {file_path}"
        
        # Replace content
        new_content = (
            content[:search_index] + 
            replace + 
            content[search_index + len(search):]
        )
        
        # Write the file
        with open(valid_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        
        return f"Successfully applied edit to {file_path}"
    except Exception as e:
        return f"Error applying edit: {str(e)}"

@mcp.tool()
async def list_directory(path: str) -> str:
    """
    Get a detailed listing of all files and directories in a specified path.
    Only works within allowed directories.
    """
    try:
        # Validate path
        valid_path = _validate_path(path)
        
        entries = []
        for entry in os.listdir(valid_path):
            full_path = os.path.join(valid_path, entry)
            entry_type = "[DIR]" if os.path.isdir(full_path) else "[FILE]"
            entries.append(f"{entry_type} {entry}")
        
        if not entries:
            return f"Directory {valid_path} is empty"
        
        return "\n".join(entries)
    except Exception as e:
        return f"Error listing directory: {str(e)}"

@mcp.tool()
async def create_directory(path: str) -> str:
    """
    Create a new directory or ensure a directory exists.
    Can create multiple nested directories in one operation.
    Only works within allowed directories.
    """
    try:
        # Validate path
        valid_path = _validate_path(path)
        
        os.makedirs(valid_path, exist_ok=True)
        return f"Successfully created directory {valid_path}"
    except Exception as e:
        return f"Error creating directory: {str(e)}"

@mcp.tool()
async def move_file(source: str, destination: str) -> str:
    """
    Move or rename files and directories. Both source and destination
    must be within allowed directories.
    """
    try:
        # Validate paths
        valid_source = _validate_path(source)
        valid_dest = _validate_path(destination)
        
        # Perform move operation
        import shutil
        shutil.move(valid_source, valid_dest)
        
        return f"Successfully moved {valid_source} to {valid_dest}"
    except Exception as e:
        return f"Error moving file: {str(e)}"

@mcp.tool()
async def search_files(path: str, pattern: str) -> str:
    """
    Search for files matching a pattern within a directory.
    Only searches within allowed directories.
    """
    try:
        # Validate path
        valid_path = _validate_path(path)
        
        results = []
        pattern_lower = pattern.lower()
        
        for root, dirs, files in os.walk(valid_path):
            # Skip hidden directories
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            
            for name in files:
                if pattern_lower in name.lower():
                    file_path = os.path.join(root, name)
                    results.append(file_path)
        
        if not results:
            return f"No files matching '{pattern}' found in {valid_path}"
        
        return "\n".join(results)
    except Exception as e:
        return f"Error searching files: {str(e)}"

@mcp.tool()
async def search_code(path: str, pattern: str, file_pattern: str = None, 
                      ignore_case: bool = True, max_results: int = 1000) -> str:
    """
    Search for text patterns within file contents using ripgrep or fallback method.
    Only searches within allowed directories.
    """
    try:
        # Validate path
        valid_path = _validate_path(path)
        
        # Try to use ripgrep if available
        import shutil
        import re
        import subprocess
        
        rg_path = shutil.which("rg")
        
        if rg_path:
            # Build ripgrep command
            args = [
                rg_path,
                "--line-number",  # Include line numbers
            ]
            
            if ignore_case:
                args.append("-i")
            
            if max_results:
                args.extend(["-m", str(max_results)])
            
            if file_pattern:
                args.extend(["-g", file_pattern])
            
            # Add pattern and path
            args.extend([pattern, valid_path])
            
            # Run command
            try:
                process = subprocess.run(args, capture_output=True, text=True)
                
                if process.returncode in (0, 1):  # 0: matches found, 1: no matches
                    if not process.stdout:
                        return f"No matches found for '{pattern}' in {valid_path}"
                    
                    return process.stdout
                else:
                    # Fall back to Python implementation on error
                    raise Exception(f"ripgrep error: {process.stderr}")
            except Exception:
                # Fall back to Python implementation
                pass
        
        # Fallback: Python-based search
        results = []
        count = 0
        
        # Prepare regex pattern
        if ignore_case:
            pattern_re = re.compile(pattern, re.IGNORECASE)
        else:
            pattern_re = re.compile(pattern)
        
        # Prepare file pattern
        file_matcher = None
        if file_pattern:
            import fnmatch
            file_matcher = lambda f: fnmatch.fnmatch(f, file_pattern)
        
        for root, dirs, files in os.walk(valid_path):
            # Skip hidden directories
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            
            for name in files:
                if file_matcher and not file_matcher(name):
                    continue
                
                try:
                    file_path = os.path.join(root, name)
                    
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        for i, line in enumerate(f, 1):
                            if pattern_re.search(line):
                                results.append(f"{file_path}:{i}: {line.strip()}")
                                count += 1
                                
                                if count >= max_results:
                                    break
                    
                    if count >= max_results:
                        break
                except (UnicodeDecodeError, PermissionError, FileNotFoundError):
                    # Skip files that can't be read
                    continue
            
            if count >= max_results:
                break
        
        if not results:
            return f"No matches found for '{pattern}' in {valid_path}"
        
        return "\n".join(results)
    except Exception as e:
        return f"Error searching code: {str(e)}"

@mcp.tool()
async def get_file_info(path: str) -> str:
    """
    Retrieve detailed metadata about a file or directory.
    Only works within allowed directories.
    """
    try:
        # Validate path
        valid_path = _validate_path(path)
        
        # Get file/directory stats
        import stat
        stats = os.stat(valid_path)
        
        # Format dates
        from datetime import datetime
        created = datetime.fromtimestamp(stats.st_ctime).strftime('%Y-%m-%d %H:%M:%S')
        modified = datetime.fromtimestamp(stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
        accessed = datetime.fromtimestamp(stats.st_atime).strftime('%Y-%m-%d %H:%M:%S')
        
        # Format size
        size_bytes = stats.st_size
        if size_bytes >= 1024 * 1024 * 1024:
            size_str = f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"
        elif size_bytes >= 1024 * 1024:
            size_str = f"{size_bytes / (1024 * 1024):.2f} MB"
        elif size_bytes >= 1024:
            size_str = f"{size_bytes / 1024:.2f} KB"
        else:
            size_str = f"{size_bytes} bytes"
        
        # Get permissions
        permissions = oct(stats.st_mode)[-3:]
        
        # Determine file type
        file_type = "Directory" if os.path.isdir(valid_path) else "File"
        if os.path.islink(valid_path):
            file_type = "Symbolic Link"
        elif os.path.ismount(valid_path):
            file_type = "Mount Point"
        
        # Format output
        info = [
            f"Path: {valid_path}",
            f"Type: {file_type}",
            f"Size: {size_str} ({stats.st_size} bytes)",
            f"Created: {created}",
            f"Modified: {modified}",
            f"Accessed: {accessed}",
            f"Permissions: {permissions}"
        ]
        
        return "\n".join(info)
    except Exception as e:
        return f"Error getting file info: {str(e)}"

# === Helper Functions ===

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

def _validate_path(requested_path: str) -> str:
    """
    Validate that a path is within allowed directories.
    Returns the absolute path if valid, raises Exception if not.
    """
    allowed_directories = [
        os.getcwd(),         # Current working directory
        os.path.expanduser("~")  # User's home directory
    ]
    
    # Expand ~ to user's home directory
    if requested_path.startswith("~/") or requested_path == "~":
        expanded_path = os.path.join(os.path.expanduser("~"), 
                                     requested_path[1:] if requested_path != "~" else "")
    else:
        expanded_path = requested_path
    
    # Get absolute path
    absolute = (
        os.path.abspath(expanded_path) if os.path.isabs(expanded_path) 
        else os.path.abspath(os.path.join(os.getcwd(), expanded_path))
    )
    
    # Normalize paths for comparison
    def normalize_path(p):
        return os.path.normpath(p).lower()
    
    normalized_requested = normalize_path(absolute)
    
    # Check if path is within allowed directories
    is_allowed = any(
        normalized_requested.startswith(normalize_path(dir)) 
        for dir in allowed_directories
    )
    
    if not is_allowed:
        raise Exception(f"Access denied - path outside allowed directories: {absolute}")
    
    # Check symlinks
    if os.path.exists(absolute) and os.path.islink(absolute):
        real_path = os.path.realpath(absolute)
        normalized_real = normalize_path(real_path)
        
        is_real_allowed = any(
            normalized_real.startswith(normalize_path(dir))
            for dir in allowed_directories
        )
        
        if not is_real_allowed:
            raise Exception("Access denied - symlink target outside allowed directories")
    
    return absolute