from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, List, Any, Union
import subprocess


@dataclass
class ProcessInfo:
    pid: int
    command: str
    cpu: str
    memory: str


@dataclass
class TerminalSession:
    pid: int
    process: subprocess.Popen
    last_output: str
    is_blocked: bool
    start_time: datetime


@dataclass
class CommandExecutionResult:
    pid: int
    output: str
    is_blocked: bool


@dataclass
class ActiveSession:
    pid: int
    is_blocked: bool
    runtime: int  # in milliseconds


@dataclass
class CompletedSession:
    pid: int
    output: str
    exit_code: Optional[int]
    start_time: datetime
    end_time: datetime


@dataclass
class SearchResult:
    file: str
    line: int
    match: str


@dataclass
class SearchReplaceBlock:
    search: str
    replace: str


@dataclass
class ToolResponse:
    content: List[Dict[str, str]]
    is_error: bool = False