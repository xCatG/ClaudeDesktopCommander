"""
Filesystem tools for the Desktop Commander MCP Server.
Includes file operations, search, and path utilities.
"""

import os
import re
import shutil
import subprocess
from datetime import datetime
from typing import List

# === Path Utilities ===

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

def get_allowed_directories() -> List[str]:
    """Get the list of allowed directories."""
    return [
        os.getcwd(),         # Current working directory
        os.path.expanduser("~")  # User's home directory
    ]

# === Tool Registration ===

def register_tools(mcp):
    """Register filesystem tools with the MCP server."""
    
    # === Basic File Operations ===
    
    @mcp.tool()
    def list_allowed_directories() -> str:
        """Return the list of directories that this server is allowed to access."""
        allowed_dirs = get_allowed_directories()
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
            shutil.move(valid_source, valid_dest)
            
            return f"Successfully moved {valid_source} to {valid_dest}"
        except Exception as e:
            return f"Error moving file: {str(e)}"

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
            stats = os.stat(valid_path)
            
            # Format dates
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
    
    # === Search and Edit Tools ===
    
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
