"""
Process management tools for the Desktop Commander MCP Server.
"""

import os
import time
import signal
import psutil

def register_tools(mcp):
    """Register process management tools with the MCP server."""
    
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
