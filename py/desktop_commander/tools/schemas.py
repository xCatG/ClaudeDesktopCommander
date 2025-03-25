from typing import List, Optional
from pydantic import BaseModel, Field


# Terminal tools schemas
class ExecuteCommandArgs(BaseModel):
    command: str
    timeout_ms: Optional[int] = None


class ReadOutputArgs(BaseModel):
    pid: int


class ForceTerminateArgs(BaseModel):
    pid: int


class ListSessionsArgs(BaseModel):
    pass


class KillProcessArgs(BaseModel):
    pid: int


class BlockCommandArgs(BaseModel):
    command: str


class UnblockCommandArgs(BaseModel):
    command: str


# Filesystem tools schemas
class ReadFileArgs(BaseModel):
    path: str


class ReadMultipleFilesArgs(BaseModel):
    paths: List[str]


class WriteFileArgs(BaseModel):
    path: str
    content: str


class CreateDirectoryArgs(BaseModel):
    path: str


class ListDirectoryArgs(BaseModel):
    path: str


class MoveFileArgs(BaseModel):
    source: str
    destination: str


class SearchFilesArgs(BaseModel):
    path: str
    pattern: str


class GetFileInfoArgs(BaseModel):
    path: str


# Search tools schema
class SearchCodeArgs(BaseModel):
    path: str
    pattern: str
    file_pattern: Optional[str] = None
    ignore_case: Optional[bool] = True
    max_results: Optional[int] = 1000
    include_hidden: Optional[bool] = False
    context_lines: Optional[int] = 0


# Edit tools schemas
class EditBlockArgs(BaseModel):
    block_content: str