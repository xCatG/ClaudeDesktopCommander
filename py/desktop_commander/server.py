import json
import asyncio
import sys
import os
from typing import Dict, Any, List, Optional, Union, Callable

from desktop_commander.version import VERSION
from desktop_commander.command_manager import command_manager
from desktop_commander.types import ToolResponse

# Import all tool implementations
from desktop_commander.tools.execute import (
    execute_command, 
    read_output, 
    force_terminate, 
    list_sessions
)
from desktop_commander.tools.process import list_processes, kill_process
from desktop_commander.tools.filesystem import (
    read_file,
    read_multiple_files,
    write_file,
    create_directory,
    list_directory,
    move_file,
    search_files,
    get_file_info,
    list_allowed_directories
)
from desktop_commander.tools.edit import parse_edit_block, perform_search_replace
from desktop_commander.tools.search import search_text_in_files
from desktop_commander.tools.schemas import (
    ExecuteCommandArgs,
    ReadOutputArgs,
    ForceTerminateArgs,
    ListSessionsArgs,
    KillProcessArgs,
    BlockCommandArgs,
    UnblockCommandArgs,
    ReadFileArgs,
    ReadMultipleFilesArgs,
    WriteFileArgs,
    CreateDirectoryArgs,
    ListDirectoryArgs,
    MoveFileArgs,
    SearchFilesArgs,
    GetFileInfoArgs,
    SearchCodeArgs,
    EditBlockArgs
)


class MCPServer:
    def __init__(self):
        self.server_info = {
            "name": "desktop-commander-py",
            "version": VERSION
        }
        self.capabilities = {
            "tools": {}
        }
        
        # Set up tools
        self.tools = self._register_tools()
    
    def _register_tools(self) -> Dict[str, Dict[str, Any]]:
        """Register all available tools with their schemas and handlers."""
        return {
            # Terminal tools
            "execute_command": {
                "description": "Execute a terminal command with timeout. Command will continue running in background if it doesn't complete within timeout.",
                "schema": ExecuteCommandArgs,
                "handler": execute_command
            },
            "read_output": {
                "description": "Read new output from a running terminal session.",
                "schema": ReadOutputArgs,
                "handler": read_output
            },
            "force_terminate": {
                "description": "Force terminate a running terminal session.",
                "schema": ForceTerminateArgs,
                "handler": force_terminate
            },
            "list_sessions": {
                "description": "List all active terminal sessions.",
                "schema": ListSessionsArgs,
                "handler": list_sessions
            },
            "list_processes": {
                "description": "List all running processes. Returns process information including PID, command name, CPU usage, and memory usage.",
                "schema": None,
                "handler": list_processes
            },
            "kill_process": {
                "description": "Terminate a running process by PID. Use with caution as this will forcefully terminate the specified process.",
                "schema": KillProcessArgs,
                "handler": kill_process
            },
            "block_command": {
                "description": "Add a command to the blacklist. Once blocked, the command cannot be executed until unblocked.",
                "schema": BlockCommandArgs,
                "handler": self._block_command
            },
            "unblock_command": {
                "description": "Remove a command from the blacklist. Once unblocked, the command can be executed normally.",
                "schema": UnblockCommandArgs,
                "handler": self._unblock_command
            },
            "list_blocked_commands": {
                "description": "List all currently blocked commands.",
                "schema": None,
                "handler": self._list_blocked_commands
            },
            
            # Filesystem tools
            "read_file": {
                "description": "Read the complete contents of a file from the file system. Handles various text encodings and provides detailed error messages if the file cannot be read. Only works within allowed directories.",
                "schema": ReadFileArgs,
                "handler": self._read_file
            },
            "read_multiple_files": {
                "description": "Read the contents of multiple files simultaneously. Each file's content is returned with its path as a reference. Failed reads for individual files won't stop the entire operation. Only works within allowed directories.",
                "schema": ReadMultipleFilesArgs,
                "handler": self._read_multiple_files
            },
            "write_file": {
                "description": "Completely replace file contents. Best for large changes (>20% of file) or when edit_block fails. Use with caution as it will overwrite existing files. Only works within allowed directories.",
                "schema": WriteFileArgs,
                "handler": self._write_file
            },
            "create_directory": {
                "description": "Create a new directory or ensure a directory exists. Can create multiple nested directories in one operation. Only works within allowed directories.",
                "schema": CreateDirectoryArgs,
                "handler": self._create_directory
            },
            "list_directory": {
                "description": "Get a detailed listing of all files and directories in a specified path. Results distinguish between files and directories with [FILE] and [DIR] prefixes. Only works within allowed directories.",
                "schema": ListDirectoryArgs,
                "handler": self._list_directory
            },
            "move_file": {
                "description": "Move or rename files and directories. Can move files between directories and rename them in a single operation. Both source and destination must be within allowed directories.",
                "schema": MoveFileArgs,
                "handler": self._move_file
            },
            "search_files": {
                "description": "Recursively search for files and directories matching a pattern. Searches through all subdirectories from the starting path. Only searches within allowed directories.",
                "schema": SearchFilesArgs,
                "handler": self._search_files
            },
            "search_code": {
                "description": "Search for text/code patterns within file contents using ripgrep. Fast and powerful search similar to VS Code search functionality. Supports regular expressions, file pattern filtering, and context lines. Only searches within allowed directories.",
                "schema": SearchCodeArgs,
                "handler": self._search_code
            },
            "get_file_info": {
                "description": "Retrieve detailed metadata about a file or directory including size, creation time, last modified time, permissions, and type. Only works within allowed directories.",
                "schema": GetFileInfoArgs,
                "handler": self._get_file_info
            },
            "list_allowed_directories": {
                "description": "Returns the list of directories that this server is allowed to access.",
                "schema": None,
                "handler": self._list_allowed_directories
            },
            "edit_block": {
                "description": "Apply surgical text replacements to files. Best for small changes (<20% of file size). Multiple blocks can be used for separate changes. Will verify changes after application. Format: filepath, then <<<<<<< SEARCH, content to find, =======, new content, >>>>>>> REPLACE.",
                "schema": EditBlockArgs,
                "handler": self._edit_block
            }
        }
    
    async def handle_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process an incoming MCP request and return a response."""
        method = request_data.get("method")
        
        if method == "initialize":
            return await self._handle_initialize(request_data)
        elif method == "listTools":
            return await self._handle_list_tools()
        elif method == "callTool":
            return await self._handle_call_tool(request_data)
        else:
            return {
                "error": {
                    "message": f"Unknown method: {method}"
                }
            }
    
    async def _handle_initialize(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle the initialize request from the client."""
        return {
            "jsonrpc": "2.0",
            "id": request_data.get("id"),
            "result": {
                "serverInfo": self.server_info,
                "capabilities": self.capabilities
            }
        }

    async def _handle_list_tools(self) -> Dict[str, Any]:
        """Handle listTools request."""
        tools = []
        
        for name, tool in self.tools.items():
            tool_info = {
                "name": name,
                "description": tool["description"],
                "inputSchema": self._generate_schema(tool["schema"])
            }
            tools.append(tool_info)
        
        return {"tools": tools}
    
    async def _handle_call_tool(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle callTool request."""
        params = request_data.get("params", {})
        tool_name = params.get("name")
        tool_args = params.get("arguments", {})
        
        if tool_name not in self.tools:
            return {
                "error": {
                    "message": f"Unknown tool: {tool_name}"
                }
            }
        
        tool = self.tools[tool_name]
        
        try:
            # Validate arguments if schema exists
            validated_args = None
            if tool["schema"]:
                validated_args = tool["schema"](**tool_args)
            
            # Call the handler
            result = await tool["handler"](validated_args if validated_args else None)
            
            if not isinstance(result, ToolResponse):
                # Wrap simple results
                result = ToolResponse(content=[{"type": "text", "text": str(result)}])
            
            return {
                "result": {
                    "content": result.content,
                    "isError": result.is_error
                }
            }
        except Exception as e:
            return {
                "result": {
                    "content": [{"type": "text", "text": f"Error: {str(e)}"}],
                    "isError": True
                }
            }
    
    def _generate_schema(self, schema_cls) -> Dict[str, Any]:
        """Generate JSON schema from Pydantic model."""
        if schema_cls is None:
            # Empty schema for tools without arguments
            return {
                "type": "object",
                "properties": {},
                "required": []
            }
        
        # Use Pydantic's schema method
        schema = schema_cls.model_json_schema()
        return schema

    # Tool handlers
    async def _block_command(self, args: BlockCommandArgs) -> ToolResponse:
        """Block a command from being executed."""
        result = await command_manager.block_command(args.command)
        return ToolResponse(
            content=[{"type": "text", "text": str(result)}]
        )

    async def _unblock_command(self, args: UnblockCommandArgs) -> ToolResponse:
        """Unblock a command."""
        result = await command_manager.unblock_command(args.command)
        return ToolResponse(
            content=[{"type": "text", "text": str(result)}]
        )

    async def _list_blocked_commands(self, _) -> ToolResponse:
        """List all blocked commands."""
        blocked = command_manager.list_blocked_commands()
        return ToolResponse(
            content=[{"type": "text", "text": "\n".join(blocked)}]
        )

    async def _read_file(self, args: ReadFileArgs) -> ToolResponse:
        """Read a file."""
        content = await read_file(args.path)
        return ToolResponse(
            content=[{"type": "text", "text": content}]
        )

    async def _read_multiple_files(self, args: ReadMultipleFilesArgs) -> ToolResponse:
        """Read multiple files."""
        results = await read_multiple_files(args.paths)
        return ToolResponse(
            content=[{"type": "text", "text": "\n---\n".join(results)}]
        )

    async def _write_file(self, args: WriteFileArgs) -> ToolResponse:
        """Write to a file."""
        await write_file(args.path, args.content)
        return ToolResponse(
            content=[{"type": "text", "text": f"Successfully wrote to {args.path}"}]
        )

    async def _create_directory(self, args: CreateDirectoryArgs) -> ToolResponse:
        """Create a directory."""
        await create_directory(args.path)
        return ToolResponse(
            content=[{"type": "text", "text": f"Successfully created directory {args.path}"}]
        )

    async def _list_directory(self, args: ListDirectoryArgs) -> ToolResponse:
        """List directory contents."""
        entries = await list_directory(args.path)
        return ToolResponse(
            content=[{"type": "text", "text": "\n".join(entries)}]
        )

    async def _move_file(self, args: MoveFileArgs) -> ToolResponse:
        """Move a file or directory."""
        await move_file(args.source, args.destination)
        return ToolResponse(
            content=[{"type": "text", "text": f"Successfully moved {args.source} to {args.destination}"}]
        )

    async def _search_files(self, args: SearchFilesArgs) -> ToolResponse:
        """Search for files."""
        results = await search_files(args.path, args.pattern)
        message = "\n".join(results) if results else "No matches found"
        return ToolResponse(
            content=[{"type": "text", "text": message}]
        )

    async def _search_code(self, args: SearchCodeArgs) -> ToolResponse:
        """Search for code/text in files."""
        results = await search_text_in_files({
            "path": args.path,
            "pattern": args.pattern,
            "file_pattern": args.file_pattern,
            "ignore_case": args.ignore_case,
            "max_results": args.max_results,
            "include_hidden": args.include_hidden,
            "context_lines": args.context_lines
        })
        
        if not results:
            return ToolResponse(
                content=[{"type": "text", "text": "No matches found"}]
            )
        
        # Format the results
        current_file = ""
        formatted_results = ""
        
        for result in results:
            if result.file != current_file:
                formatted_results += f"\n{result.file}:\n"
                current_file = result.file
            
            formatted_results += f"  {result.line}: {result.match}\n"
        
        return ToolResponse(
            content=[{"type": "text", "text": formatted_results.strip()}]
        )

    async def _get_file_info(self, args: GetFileInfoArgs) -> ToolResponse:
        """Get file metadata."""
        info = await get_file_info(args.path)
        message = "\n".join(f"{key}: {value}" for key, value in info.items())
        return ToolResponse(
            content=[{"type": "text", "text": message}]
        )

    async def _list_allowed_directories(self, _) -> ToolResponse:
        """List allowed directories."""
        directories = list_allowed_directories()
        return ToolResponse(
            content=[{"type": "text", "text": f"Allowed directories:\n{chr(10).join(directories)}"}]
        )

    async def _edit_block(self, args: EditBlockArgs) -> ToolResponse:
        """Apply edit block to a file."""
        file_path, search_replace = await parse_edit_block(args.block_content)
        await perform_search_replace(file_path, search_replace)
        return ToolResponse(
            content=[{"type": "text", "text": f"Successfully applied edit to {file_path}"}]
        )

    async def run(self):
        """Run the MCP server, reading from stdin and writing to stdout."""
        print(f"Python Desktop Commander MCP Server v{VERSION} starting...", file=sys.stderr)
        
        # Load blocked commands
        await command_manager.load_blocked_commands()
        
        while True:
            try:
                # Read a line from stdin (protocol requires newline-delimited JSON)
                line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
                
                if not line:
                    # End of input, exit
                    break
                
                # Parse the JSON request
                request = json.loads(line)
                
                # Handle the request
                response = await self.handle_request(request)
                
                # Add id from request if present
                if "id" in request:
                    response["id"] = request["id"]
                
                # Send the response
                print(json.dumps(response), flush=True)
                
            except json.JSONDecodeError:
                # Invalid JSON
                error_response = {
                    "error": {
                        "message": "Invalid JSON request"
                    }
                }
                print(json.dumps(error_response), flush=True)
                
            except Exception as e:
                # Other errors
                error_response = {
                    "error": {
                        "message": f"Server error: {str(e)}"
                    }
                }
                print(json.dumps(error_response), flush=True)


# Server instance
server = MCPServer()