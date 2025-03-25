import subprocess
import asyncio
import time
import signal
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import os

from desktop_commander.types import (
    TerminalSession,
    CommandExecutionResult,
    ActiveSession,
    CompletedSession
)
from desktop_commander.config import DEFAULT_COMMAND_TIMEOUT


class TerminalManager:
    def __init__(self):
        self.sessions: Dict[int, TerminalSession] = {}
        self.completed_sessions: Dict[int, CompletedSession] = {}
        
    async def execute_command(
        self, 
        command: str, 
        timeout_ms: int = DEFAULT_COMMAND_TIMEOUT
    ) -> CommandExecutionResult:
        """Execute a shell command with timeout."""
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
            raise Exception("Failed to get process ID")
            
        # Create session
        session = TerminalSession(
            pid=process.pid,
            process=process,
            last_output="",
            is_blocked=False,
            start_time=datetime.now()
        )
        
        self.sessions[process.pid] = session
        
        # Collect output for the timeout period
        output = ""
        start_time = time.time()
        
        while time.time() - start_time < timeout_ms / 1000:
            # Check if process has completed
            if process.poll() is not None:
                stdout, stderr = process.communicate()
                output += stdout + stderr
                session.last_output += stdout + stderr
                
                # Store completed session
                self.completed_sessions[process.pid] = CompletedSession(
                    pid=process.pid,
                    output=output + session.last_output,
                    exit_code=process.returncode,
                    start_time=session.start_time,
                    end_time=datetime.now()
                )
                
                # Keep only last 100 completed sessions
                if len(self.completed_sessions) > 100:
                    oldest_key = next(iter(self.completed_sessions))
                    del self.completed_sessions[oldest_key]
                    
                # Remove active session
                del self.sessions[process.pid]
                
                return CommandExecutionResult(
                    pid=process.pid,
                    output=output,
                    is_blocked=False
                )
                
            # Read available output without blocking
            stdout_data = self._read_nonblocking(process.stdout)
            stderr_data = self._read_nonblocking(process.stderr)
            
            if stdout_data:
                output += stdout_data
                session.last_output += stdout_data
                
            if stderr_data:
                output += stderr_data
                session.last_output += stderr_data
                
            await asyncio.sleep(0.1)
            
        # Timeout reached, mark as blocked and return current output
        session.is_blocked = True
        return CommandExecutionResult(
            pid=process.pid,
            output=output,
            is_blocked=True
        )

    def _read_nonblocking(self, stream) -> str:
        """Read from a stream without blocking."""
        import fcntl
        import os
        import select
        
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
        
    def get_new_output(self, pid: int) -> Optional[str]:
        """Get new output from a session since last check."""
        # Check active sessions
        if pid in self.sessions:
            session = self.sessions[pid]
            output = session.last_output
            session.last_output = ""
            return output
            
        # Check completed sessions
        if pid in self.completed_sessions:
            completed = self.completed_sessions[pid]
            runtime = (completed.end_time - completed.start_time).total_seconds()
            return (
                f"Process completed with exit code {completed.exit_code}\n"
                f"Runtime: {runtime}s\nFinal output:\n{completed.output}"
            )
            
        return None
        
    def force_terminate(self, pid: int) -> bool:
        """Force terminate a running session."""
        if pid not in self.sessions:
            return False
            
        try:
            session = self.sessions[pid]
            # First try SIGINT (Ctrl+C)
            session.process.send_signal(signal.SIGINT)
            
            # Schedule SIGKILL (force kill) after 1 second if still running
            async def delayed_kill():
                await asyncio.sleep(1)
                if pid in self.sessions:
                    session.process.kill()
                    
            asyncio.create_task(delayed_kill())
            return True
        except Exception:
            return False
            
    def list_active_sessions(self) -> List[ActiveSession]:
        """List all active terminal sessions."""
        now = datetime.now()
        return [
            ActiveSession(
                pid=session.pid,
                is_blocked=session.is_blocked,
                runtime=int((now - session.start_time).total_seconds() * 1000)
            )
            for session in self.sessions.values()
        ]
        
    def list_completed_sessions(self) -> List[CompletedSession]:
        """List completed terminal sessions."""
        return list(self.completed_sessions.values())


# Singleton instance
terminal_manager = TerminalManager()