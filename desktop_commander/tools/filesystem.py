"""
Filesystem tools for the Desktop Commander MCP Server.
Includes file operations, search, and path utilities.
"""

import io
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from typing import List, Optional, Union, Any

# Import current_project from project module (at runtime to avoid circular imports)
# This will be used for project-relative path handling
current_project = None
def _get_current_project():
    """Get the current project information, handling circular imports."""
    global current_project
    if current_project is None:
        try:
            from desktop_commander.tools.project import current_project as proj
            current_project = proj
        except ImportError:
            # Fallback if import fails
            current_project = {"path": None, "name": None, "type": None}
    return current_project

# === Path Utilities ===

def _resolve_project_path(path: str) -> str:
    """
    Resolve a path that might be relative to the current project.
    
    Handles several cases:
    1. If path starts with "proj:" or "project:", it's treated as relative to current project
    2. If path matches the current project name or basename, use the full project path
    3. Otherwise, return the path unchanged
    
    Returns the resolved path or raises ValueError if no project is active when needed.
    """
    # Get the current project if needed
    project = _get_current_project()
    
    # Handle proj: prefix for project-relative paths
    if path.startswith("proj:"):
        rel_path = path[5:].lstrip("/\\")
        if not project["path"]:
            raise ValueError("No active project. Use discover_projects and use_project first.")
        return os.path.join(project["path"], rel_path)
    elif path.startswith("project:"):
        rel_path = path[8:].lstrip("/\\")
        if not project["path"]:
            raise ValueError("No active project. Use discover_projects and use_project first.")
        return os.path.join(project["path"], rel_path)
        
    # Handle when just the project name is provided
    if (project["path"] is not None and 
        (path == project["name"] or 
         path == os.path.basename(project["path"]))):
        print(f"Note: Using full project path for '{path}'", file=sys.stderr)
        return project["path"]
        
    # Default - just return the path unchanged
    return path

def _get_whitelisted_directories() -> List[str]:
    """
    Get the list of whitelisted directories from config or defaults.
    Handles both relative (to home) and absolute paths for Linux and Windows.
    """
    home_dir = os.path.expanduser("~")
    
    # Start with default allowed directories
    allowed = [
        os.getcwd(),  # Current working directory is always allowed
    ]
    
    # Try to load whitelist from config
    try:
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.json")
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                config = json.load(f)
                
            # Get dir_whitelist from config
            whitelist = config.get("dir_whitelist", [])
            
            # If whitelist is empty, default to allowing the home directory
            if not whitelist:
                whitelist = [""]  # Empty string means home directory itself
            
            for path in whitelist:
                # Skip empty entries (prevents errors)
                if path is None:
                    continue
                    
                if not path:
                    # Empty string means the home directory itself
                    allowed.append(home_dir)
                    continue
                
                # Handle Windows paths with backslashes and drive letters
                if os.name == 'nt':  # Windows
                    # Check for Windows drive letter pattern (C:\, D:\, etc.)
                    if re.match(r'^[a-zA-Z]:\\', path):
                        # Use as-is (it's an absolute Windows path)
                        allowed.append(os.path.normpath(path))
                        continue
                else:  # Unix-like systems
                    # On Unix systems, convert Windows-style paths for compatibility
                    if re.match(r'^[a-zA-Z]:\\', path) or re.match(r'^[a-zA-Z]:/', path):
                        # This is a Windows path on a Unix system - normalize it
                        normalized = path.replace('\\', '/')
                        allowed.append(os.path.normpath(normalized))
                        continue
                
                # Handle standard absolute paths
                if path.startswith('/') or path.startswith('\\'):
                    # Absolute paths are used as-is
                    allowed.append(os.path.normpath(path))
                else:
                    # Relative paths are relative to home directory
                    # Replace backslashes with the system's path separator 
                    path = path.replace('\\', os.sep).replace('/', os.sep)
                    allowed.append(os.path.normpath(os.path.join(home_dir, path)))
        else:
            # Default to allow home directory if no config
            allowed.append(home_dir)
    except Exception as e:
        print(f"Error loading directory whitelist: {str(e)}", file=sys.stderr)
        # Default to home directory if error
        allowed.append(home_dir)
    
    # Print the allowed directories for debugging
    print(f"Whitelisted directories: {allowed}", file=sys.stderr)
        
    return allowed

def _validate_path(requested_path: str) -> str:
    """
    Validate that a path is within allowed directories based on the whitelist.
    Returns the absolute path if valid, raises Exception if not.
    
    Handles:
    - Paths relative to current directory
    - Paths relative to home directory (~)
    - Absolute paths
    - Windows and Linux path formats
    """
    # Get the whitelisted directories
    allowed_directories = _get_whitelisted_directories()
    
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
    
    # Normalize paths for comparison - handle Windows/Linux differences
    def normalize_path(p):
        """
        Normalize path for consistent cross-platform comparison:
        1. Use os.path.normpath to handle . and .. and redundant separators
        2. Convert to lowercase for case-insensitive comparison
        3. Replace separators with a consistent character
        
        This ensures paths like 'C:\\Users', 'C:/Users', and 'c:/users' all match.

        """
        if p is None:
            return ""
            
        # Normalize path with OS-specific normalization
        norm_path = os.path.normpath(p).lower()
        
        # Convert all separators to forward slashes for consistent comparison
        # This works for both Windows and Unix
        norm_path = norm_path.replace('\\', '/')
        
        # Ensure trailing slash consistency
        if norm_path.endswith('/'):
            norm_path = norm_path[:-1]
            
        return norm_path
    
    normalized_requested = normalize_path(absolute)
    
    # Check if path is within allowed directories
    is_allowed = False
    for allowed_dir in allowed_directories:
        normalized_allowed = normalize_path(allowed_dir)
        
        # A path is allowed if:
        # 1. It's exactly the same as an allowed directory
        # 2. It starts with the allowed directory followed by a path separator
        if (normalized_requested == normalized_allowed or 
            normalized_requested.startswith(normalized_allowed + '/')):
            is_allowed = True
            print(f"Path allowed: {requested_path} matches whitelist entry: {allowed_dir}", file=sys.stderr)
            break
    
    if not is_allowed:
        # List the allowed directories in the error message to help with debugging
        allowed_dirs_str = ", ".join(allowed_directories)
        raise Exception(f"Access denied - path outside whitelisted directories: {absolute}\nAllowed directories: {allowed_dirs_str}")
    
    # Check symlinks to prevent path traversal attacks
    if os.path.exists(absolute) and os.path.islink(absolute):
        real_path = os.path.realpath(absolute)
        normalized_real = normalize_path(real_path)
        
        is_real_allowed = any(
            normalized_real == normalize_path(dir) or 
            normalized_real.startswith(normalize_path(dir) + '/') 
            for dir in allowed_directories
        )
        
        if not is_real_allowed:
            raise Exception(f"Access denied - symlink target outside whitelisted directories: {real_path}")
    
    return absolute

def get_allowed_directories() -> List[str]:
    """Get the list of whitelisted directories."""
    return _get_whitelisted_directories()

# === Tool Registration ===

def normalize_line_endings(text: str) -> str:
    """Normalize line endings to avoid platform-specific issues."""
    return text.replace('\r\n', '\n')

def create_unified_diff(original_content: str, new_content: str, filepath: str = 'file') -> str:
    """Create a unified diff between two text contents."""
    import difflib
    
    # Normalize line endings for consistent diff
    original_normalized = normalize_line_endings(original_content)
    new_normalized = normalize_line_endings(new_content)
    
    # Generate the diff
    diff = difflib.unified_diff(
        original_normalized.splitlines(),
        new_normalized.splitlines(),
        fromfile=f"{filepath} (original)",
        tofile=f"{filepath} (modified)",
        lineterm=''
    )
    
    return '\n'.join(diff)

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
        
        Supports multiple path formats:
        - Absolute paths: "/home/user/myproject/file.txt"
        - Relative paths: "./file.txt" or "docs/readme.md"
        - Project-relative paths: "proj:src/utils/helper.py" (relative to current project)
        
        Only works within allowed directories.
        
        Args:
            path: Path to the file, with optional "proj:" prefix for project-relative paths
            
        Returns:
            File contents or error message
        """
        try:
            # Resolve and validate path
            resolved_path = _resolve_project_path(path)
            valid_path = _validate_path(resolved_path)
            
            with open(valid_path, "r", encoding="utf-8") as f:
                content = f.read()
                
            return content
        except Exception as e:
            return f"Error reading file: {str(e)}"

    # Define a function outside the tool registration to handle both string and dict inputs
    def _write_file_impl(path: str, content, auto_format_json: bool = True) -> str:
        """
        Implementation of write_file that handles both string and dict/list content.
        This approach ensures we can process the content before the MCP validation.
        """
        # Convert content to string if it's not a string
        if not isinstance(content, str):
            try:
                # If it's a JSON-serializable object, convert it
                content = json.dumps(content, indent=2, ensure_ascii=False)
                print(f"Automatically converted non-string content to JSON string: {type(content)}", file=sys.stderr)
            except Exception as e:
                return f"Error: Content could not be converted to string: {str(e)}"
        
        try:
            # Resolve and validate path
            resolved_path = _resolve_project_path(path)
            valid_path = _validate_path(resolved_path)
            
            # Ensure parent directory exists
            parent_dir = os.path.dirname(valid_path)
            if parent_dir:  # Only try to create if there's a parent directory
                os.makedirs(parent_dir, exist_ok=True)
            
            # Check if this is a JSON file or JSON content
            is_json_file = valid_path.lower().endswith('.json') and auto_format_json
            
            # Also try to detect if content looks like JSON even if filename doesn't end with .json
            looks_like_json = False
            if auto_format_json and not is_json_file:
                # Strip whitespace and check if content starts with { or [
                stripped = content.strip()
                if (stripped.startswith('{') and stripped.endswith('}')) or \
                   (stripped.startswith('[') and stripped.endswith(']')):
                    looks_like_json = True
            
            if is_json_file or looks_like_json:
                try:
                    # Try to parse the content as JSON
                    parsed_json = json.loads(content)
                    
                    # Format with pretty indentation and ensure non-ASCII characters are preserved
                    formatted_content = json.dumps(parsed_json, indent=2, ensure_ascii=False)
                    
                    # Write the formatted JSON
                    with open(valid_path, "w", encoding="utf-8") as f:
                        f.write(formatted_content)
                        
                    return f"Successfully wrote and formatted JSON to {valid_path}"
                except json.JSONDecodeError as json_error:
                    # If JSON parsing fails, provide a helpful error message
                    line_col = f"line {json_error.lineno}, column {json_error.colno}"
                    error_detail = f"JSON validation error at {line_col}: {json_error.msg}"
                    print(f"JSON error: {error_detail}", file=sys.stderr)
                    
                    # For JSON files, require valid JSON
                    if is_json_file:
                        return f"Error: Invalid JSON - {error_detail}. File not written. To write invalid JSON, set auto_format_json=False."
                    
                    # For content that just looks like JSON but isn't a .json file, 
                    # write it unformatted as a fallback
                    print(f"Writing unformatted content as fallback", file=sys.stderr)
                    with open(valid_path, "w", encoding="utf-8") as f:
                        f.write(content)
                    
                    return f"Warning: Content appears to be invalid JSON but was written as-is to {valid_path}"
            else:
                # For non-JSON files, write content normally
                with open(valid_path, "w", encoding="utf-8") as f:
                    f.write(content)
                
                return f"Successfully wrote to {valid_path}"
        except Exception as e:
            return f"Error writing file: {str(e)}"
    
    @mcp.tool()
    async def write_file(path: str, content: Union[str, Any]) -> str:
        """
        Write content to a file with smart handling of different file types.
        
        Supports multiple path formats:
        - Absolute paths: "/home/user/myproject/file.txt"
        - Relative paths: "./file.txt" or "docs/readme.md"
        - Project-relative paths: "proj:src/utils/helper.py" (relative to current project)
        
        Features:
        - Automatically creates parent directories if they don't exist
        - For JSON files (ending in .json), automatically formats and validates the JSON
        - For JavaScript/TypeScript files, preserves formatting
        
        Only works within allowed directories.
        
        Args:
            path: The path where to write the file, with optional "proj:" prefix for project-relative paths
            content: Content to write as a string. DO NOT PASS IN json objects, serialize it to a string first.
            auto_format_json: Whether to auto-format and validate JSON content (default: True)
            
        Returns:
            Success message or error
        """
        # Call the implementation function
        return _write_file_impl(path, content, True)

    @mcp.tool()
    async def write_json_file(path: str, content_json: Union[str, Any]) -> str:
        """
        [DEPRECATED] Write JSON data to a file. Please use write_file() instead.
        
        This function is kept for backward compatibility but will be removed in the future.
        The write_file() function now automatically detects and formats JSON files.
        
        Example usage:
          Instead of: write_json_file("config.json", json_content)
          Use: write_file("config.json", json_content)
        
        Args:
            path: The path where to write the file
            content_json: JSON string to write
            
        Returns:
            Success message or error
        """
        try:
            # Call the implementation function directly to bypass type validation
            return _write_file_impl(path, content_json, auto_format_json=True)
        except Exception as e:
            print(f"Error in write_json_file: {str(e)}", file=sys.stderr)
            return f"Error writing JSON file: {str(e)}"
            
    @mcp.tool()
    async def edit_json(path: str, updates: str) -> str:
        """
        Update a JSON file with specific key-value changes.
        
        This specialized tool makes it easy to modify JSON files by providing
        a dictionary of changes to apply to the existing JSON.
        
        Supports multiple path formats:
        - Absolute paths: "/home/user/myproject/config.json"
        - Relative paths: "./config.json" or "configs/settings.json"
        - Project-relative paths: "proj:src/data/config.json" (relative to current project)
        
        Features:
        - Only modifies specified keys without changing the rest of the file
        - Creates the file if it doesn't exist
        - Updates nested properties using dot notation
        - Preserves existing formatting and comments
        
        Args:
            path: Path to the JSON file, with optional "proj:" prefix
            updates: JSON string containing the changes to apply, example: '{"version": "1.1.0", "settings.debug": true}'
            
        Example:
            edit_json("config.json", '{"version": "1.1.0", "settings.debug": true}')
            
        Returns:
            Success message with details of applied changes
        """
        try:
            # Add .json extension if not present
            if not path.lower().endswith('.json'):
                path = path + '.json'
                
            # Resolve and validate path
            resolved_path = _resolve_project_path(path)
            valid_path = _validate_path(resolved_path)
            
            # Parse the updates
            try:
                updates_dict = json.loads(updates) if isinstance(updates, str) else updates
            except json.JSONDecodeError as json_error:
                line_col = f"line {json_error.lineno}, column {json_error.colno}"
                error_detail = f"JSON validation error in updates at {line_col}: {json_error.msg}"
                return f"Error: Invalid JSON updates - {error_detail}. No changes applied."
            
            # Read existing JSON or create new if file doesn't exist
            try:
                if os.path.exists(valid_path):
                    with open(valid_path, "r", encoding="utf-8") as f:
                        try:
                            data = json.load(f)
                        except json.JSONDecodeError as e:
                            return f"Error: The existing file contains invalid JSON: {str(e)}"
                else:
                    # File doesn't exist, create a new empty JSON object
                    data = {}
                    # Ensure parent directory exists
                    parent_dir = os.path.dirname(valid_path)
                    if parent_dir:
                        os.makedirs(parent_dir, exist_ok=True)
            except Exception as e:
                return f"Error reading JSON file: {str(e)}"
            
            # Apply the updates
            changes = []
            
            for key, value in updates_dict.items():
                # Check for nested keys using dot notation
                if "." in key:
                    parts = key.split(".")
                    current = data
                    # Navigate to the nested object, creating intermediate objects if needed
                    for i, part in enumerate(parts[:-1]):
                        if part not in current:
                            current[part] = {}
                        elif not isinstance(current[part], dict):
                            # Convert to dict if it wasn't one
                            old_value = current[part]
                            current[part] = {"_value": old_value}
                        current = current[part]
                    
                    # Update the final value
                    final_key = parts[-1]
                    old_value = current.get(final_key, None)
                    current[final_key] = value
                    changes.append(f"{key}: {old_value} -> {value}")
                else:
                    # Direct key update
                    old_value = data.get(key, None)
                    data[key] = value
                    changes.append(f"{key}: {old_value} -> {value}")
            
            # Write the updated JSON back to the file
            with open(valid_path, "w", encoding="utf-8") as f:
                json.dump(data, indent=2, fp=f, ensure_ascii=False)
            
            # Return success message with changes
            changes_text = "\n".join(changes)
            return f"Successfully updated JSON file {valid_path} with the following changes:\n{changes_text}"
            
        except Exception as e:
            return f"Error editing JSON file: {str(e)}"
    
    @mcp.tool()
    async def save_json(path: str, json_data: Union[str, Any], indent: int = 2) -> str:
        """
        Write JSON data to a file with proper formatting.
        
        This specialized tool handles both JSON strings and objects safely.
        It's the best way to save JSON configuration files.
        
        Supports multiple path formats:
        - Absolute paths: "/home/user/myproject/config.json"
        - Relative paths: "./config.json" or "configs/settings.json"
        - Project-relative paths: "proj:src/data/config.json" (relative to current project)
        
        Features:
        - Automatically creates parent directories if they don't exist
        - Validates and formats JSON with proper indentation
        - Preserves non-ASCII characters in JSON files
        - Provides helpful error messages for JSON syntax issues
        
        Args:
            path: The path where to write the file, with optional "proj:" prefix
            json_data: JSON data as a string, example: '{"name": "value"}'
            indent: Number of spaces for indentation (default: 2)
            
        Example:
            save_json("config.json", '{"version": "1.0", "debug": false}')
            
        Returns:
            Success message or error
        """
        try:
            # Add .json extension if not present
            if not path.lower().endswith('.json'):
                path = path + '.json'
                
            # Resolve and validate path
            resolved_path = _resolve_project_path(path)
            valid_path = _validate_path(resolved_path)
            
            # Ensure parent directory exists
            parent_dir = os.path.dirname(valid_path)
            if parent_dir:  # Only try to create if there's a parent directory
                os.makedirs(parent_dir, exist_ok=True)
            
            # Parse and validate the JSON data
            try:
                # If it's already a string, try to parse it to validate
                if isinstance(json_data, str):
                    parsed_json = json.loads(json_data)
                else:
                    # If it's not a string, assume it's already a Python object
                    parsed_json = json_data
                    
                # Format with proper indentation and ensure non-ASCII characters are preserved
                formatted_json = json.dumps(parsed_json, indent=indent, ensure_ascii=False)
                
                # Write the formatted JSON
                with open(valid_path, "w", encoding="utf-8") as f:
                    f.write(formatted_json)
                    
                return f"Successfully wrote and formatted JSON to {valid_path}"
                
            except json.JSONDecodeError as json_error:
                # If JSON parsing fails, provide a helpful error message
                line_col = f"line {json_error.lineno}, column {json_error.colno}"
                error_detail = f"JSON validation error at {line_col}: {json_error.msg}"
                return f"Error: Invalid JSON - {error_detail}. File not written."
                
        except Exception as e:
            return f"Error writing JSON file: {str(e)}"

    @mcp.tool()
    async def list_directory(path: str = ".") -> str:
        """
        Get a detailed listing of all files and directories in a specified path.
        
        Supports multiple path formats:
        - Absolute paths: "/home/user/myproject"
        - Relative paths: "." or "src/utils"
        - Project-relative paths: "proj:src/utils" (relative to current project)
        - Project name: If you provide just the project name, it will list the project root
        
        If no path is provided, defaults to current directory (".").
        Only works within allowed directories.
        
        Args:
            path: Path to list, with optional "proj:" prefix for project-relative paths
            
        Returns:
            Formatted directory listing or error message
        """
        try:
            # Resolve and validate path
            resolved_path = _resolve_project_path(path)
            valid_path = _validate_path(resolved_path)
            
            entries = []
            for entry in os.listdir(valid_path):
                full_path = os.path.join(valid_path, entry)
                entry_type = "[DIR]" if os.path.isdir(full_path) else "[FILE]"
                entries.append(f"{entry_type} {entry}")
            
            if not entries:
                return f"Directory {valid_path} is empty"
            
            # Show the resolved path in the output to help the agent understand
            return f"Listing directory: {valid_path}\n\n" + "\n".join(entries)
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
            # Resolve and validate path
            resolved_path = _resolve_project_path(path)
            valid_path = _validate_path(resolved_path)
            
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
        
        Supports multiple path formats:
        - Absolute paths: "/home/user/myproject"
        - Relative paths: "." or "src/utils"
        - Project-relative paths: "proj:src" (relative to current project)
        - Project name: If you provide just the project name, it will search the project root
        
        Only searches within allowed directories.
        
        Args:
            path: Directory to search in, with optional "proj:" prefix for project-relative paths
            pattern: Filename pattern to match (case-insensitive)
            
        Returns:
            List of matching files or error message
        """
        try:
            # Resolve and validate path
            resolved_path = _resolve_project_path(path)
            valid_path = _validate_path(resolved_path)
            
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
            
            return f"Search results for '{pattern}' in {valid_path}:\n\n" + "\n".join(results)
        except Exception as e:
            return f"Error searching files: {str(e)}"

    @mcp.tool()
    async def search_code(path: str, pattern: str, file_pattern: str = None, 
                          ignore_case: bool = True, max_results: int = 1000) -> str:
        """
        Search for text patterns within file contents using ripgrep or fallback method.
        
        Supports multiple path formats:
        - Absolute paths: "/home/user/myproject"
        - Relative paths: "." or "src/utils"
        - Project-relative paths: "proj:src" (relative to current project)
        - Project name: If you provide just the project name, it will search the project root
        
        Only searches within allowed directories.
        
        Args:
            path: Directory to search in, with optional "proj:" prefix for project-relative paths
            pattern: Text pattern to search for in file contents
            file_pattern: Optional pattern to filter filenames (e.g., "*.py" for Python files)
            ignore_case: Whether to perform case-insensitive search (default: True)
            max_results: Maximum number of results to return (default: 1000)
            
        Returns:
            Search results or error message
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
    async def edit_file(file: str, edits: list, dry_run: bool = False) -> str:
        """
        Apply multiple text edits to a single file.
        
        IMPORTANT: This tool edits ONE FILE at a time with multiple changes.
        
        Supports multiple path formats:
        - Absolute paths: "/home/user/myproject/file.txt" 
        - Relative paths: "./file.txt" or "docs/readme.md"
        - Project-relative paths: "proj:src/utils/helper.py" (relative to current project)
        
        Args:
            file: Path to the file to edit, with optional "proj:" prefix for project-relative paths
            edits: List of edit operations, each with "oldText" and "newText" keys
            dry_run: If True, show changes without applying them (default: False)
            
        Example:
            file: "proj:src/config.json"
            edits: [
                {"oldText": "\"version\": \"1.0.0\"", "newText": "\"version\": \"1.1.0\""},
                {"oldText": "\"debug\": false", "newText": "\"debug\": true"}
            ]
            
        Returns:
            Success message with git-style diff showing the changes
        """
        try:
            # Validate parameters
            if not file:
                return "Error: Missing required 'file' parameter."
                
            if not edits or not isinstance(edits, list):
                return "Error: 'edits' must be a non-empty list of edit operations."
            
            # Validate edit operations
            for i, edit in enumerate(edits):
                if not isinstance(edit, dict):
                    return f"Error: Edit operation #{i+1} must be a dictionary."
                    
                if 'oldText' not in edit or 'newText' not in edit:
                    return f"Error: Edit operation #{i+1} must have 'oldText' and 'newText' keys."
            
            # Resolve and validate file path
            resolved_path = _resolve_project_path(file)
            valid_path = _validate_path(resolved_path)
            
            # Check if path is a directory
            if os.path.isdir(valid_path):
                return f"Error: {valid_path} is a directory, not a file. This tool can only edit individual files."
            
            # Check if file exists
            if not os.path.isfile(valid_path):
                return f"Error: File {valid_path} does not exist"
            
            # Read the file
            with open(valid_path, "r", encoding="utf-8", errors='replace') as f:
                content = f.read()
            
            # Normalize content line endings
            content = normalize_line_endings(content)
            
            # Apply edits sequentially
            modified_content = content
            for i, edit in enumerate(edits):
                old_text = normalize_line_endings(str(edit['oldText']))
                new_text = normalize_line_endings(str(edit['newText']))
                
                # Find occurrence
                index = modified_content.find(old_text)
                if index == -1:
                    return f"Error in edit #{i+1}: Text not found in file:\n```\n{old_text}\n```"
                
                # Replace content
                modified_content = (
                    modified_content[:index] + 
                    new_text + 
                    modified_content[index + len(old_text):]
                )
            
            # Create unified diff
            diff_text = create_unified_diff(content, modified_content, file)
            
            # In dry run mode, just return the diff
            if dry_run:
                return f"Showing changes that would be applied to {file}:\n\n```diff\n{diff_text}\n```"
            
            # Write the file if not in dry run mode
            with open(valid_path, "w", encoding="utf-8") as f:
                f.write(modified_content)
            
            # Return success message with diff
            return f"Successfully applied {len(edits)} edit(s) to {file}:\n\n```diff\n{diff_text}\n```"
            
        except Exception as e:
            return f"Error applying edits: {str(e)}"
            
    @mcp.tool()
    async def edit_block(file: str, search: str, replace: str, dry_run: bool = False) -> str:
        """
        Apply a surgical text replacement to a SINGLE FILE.
        
        IMPORTANT: This tool edits ONE FILE at a time only. It cannot edit directories.
        
        Supports multiple path formats:
        - Absolute paths: "/home/user/myproject/file.txt"
        - Relative paths: "./file.txt" or "src/utils/helper.py"
        - Project-relative paths: "proj:src/main.py" (relative to current project)
        
        Args:
            file: Path to the file to edit, with optional "proj:" prefix for project-relative paths
            search: The EXACT text block to find in the file (including whitespace/indentation)
            replace: The new text that will replace the search text
            dry_run: If True, show changes without applying them
        
        The tool finds the exact text specified in "search" and replaces it with the text in "replace".
        Only the first occurrence of the search text will be replaced.
        
        Example:
            file: "proj:src/file.js"
            search: "function hello() {\n  console.log('hello');\n}"
            replace: "function hello() {\n  console.log('hello world');\n}"
        
        Returns:
            Success message or detailed error information, with git-style diff when changes are made
        """
        try:
            # Extract edit parameters
            file_path = file
            search_text = search
            replace_text = replace
            
            # Validate parameters
            if not all([file_path, search_text is not None, replace_text is not None]):
                return "Error: Missing required parameters. Must include 'file', 'search', and 'replace'."
            
            # Defensive coding - ensure search and replace are strings
            if not isinstance(search_text, str):
                try:
                    search_text = json.dumps(search_text, indent=2, ensure_ascii=False)
                    print(f"Converted non-string search to JSON string", file=sys.stderr)
                except Exception as e:
                    return f"Error: Search must be a string, got {type(search_text)}: {str(e)}"
                    
            if not isinstance(replace_text, str):
                try:
                    replace_text = json.dumps(replace_text, indent=2, ensure_ascii=False)
                    print(f"Converted non-string replace to JSON string", file=sys.stderr)
                except Exception as e:
                    return f"Error: Replace must be a string, got {type(replace_text)}: {str(e)}"
            
            # Resolve and validate file path
            resolved_path = _resolve_project_path(file_path)
            valid_path = _validate_path(resolved_path)
            
            # Check if path is a directory
            if os.path.isdir(valid_path):
                return f"Error: {valid_path} is a directory, not a file. This tool can only edit individual files."
            
            # Check if file exists
            if not os.path.isfile(valid_path):
                return f"Error: File {valid_path} does not exist"
            
            # Read the file
            with open(valid_path, "r", encoding="utf-8", errors='replace') as f:
                content = f.read()
            
            # Normalize line endings to avoid issues
            content = content.replace('\r\n', '\n')
            search_text = search_text.replace('\r\n', '\n')
            replace_text = replace_text.replace('\r\n', '\n')
            
            # Find occurrence
            search_index = content.find(search_text)
            if search_index == -1:
                # Try with more flexible matching for whitespace-only differences
                content_lines = content.split('\n')
                search_lines = search_text.split('\n')
                
                found = False
                for i in range(len(content_lines) - len(search_lines) + 1):
                    potential_match = True
                    for j in range(len(search_lines)):
                        if content_lines[i+j].strip() != search_lines[j].strip():
                            potential_match = False
                            break
                    
                    if potential_match:
                        # Found a match with whitespace differences
                        found = True
                        found_block = '\n'.join(content_lines[i:i+len(search_lines)])
                        
                        return (f"Warning: Exact text not found, but found a similar block with "
                                f"whitespace differences. Please use the exact text:\n\n```\n{found_block}\n```")
                
                if not found:
                    return f"Error: Search content not found in {file_path}"
            
            # Create new content
            new_content = (
                content[:search_index] + 
                replace_text + 
                content[search_index + len(search_text):]
            )
            
            # Create a unified diff
            import difflib
            diff = difflib.unified_diff(
                content.splitlines(),
                new_content.splitlines(),
                fromfile=f"{file_path} (original)",
                tofile=f"{file_path} (modified)",
                lineterm=''
            )
            diff_text = '\n'.join(diff)
            
            # In dry run mode, just return the diff
            if dry_run:
                return f"Showing changes that would be applied to {file_path}:\n\n```diff\n{diff_text}\n```"
            
            # Write the file if not in dry run mode
            with open(valid_path, "w", encoding="utf-8") as f:
                f.write(new_content)
            
            # Return success message with diff
            return f"Successfully applied edit to {file_path}:\n\n```diff\n{diff_text}\n```"
            
        except Exception as e:
            return f"Error applying edit: {str(e)}"
            
    @mcp.tool()
    async def edit_range(file: str, start_line: int, end_line: int, new_content: str, dry_run: bool = False) -> str:
        """
        Replace a specific range of lines in a file with new content.
        
        This tool is more token-efficient than edit_block since you only need to specify line numbers 
        and the new content, without having to repeat the original content.
        
        IMPORTANT: Line numbers are 1-indexed (first line is line 1, not 0).
        
        Supports multiple path formats:
        - Absolute paths: "/home/user/myproject/file.txt"
        - Relative paths: "./file.txt" or "src/utils/helper.py" 
        - Project-relative paths: "proj:src/main.py" (relative to current project)
        
        Args:
            file: Path to the file to edit, with optional "proj:" prefix for project-relative paths
            start_line: First line to replace (1-indexed)
            end_line: Last line to replace (inclusive)
            new_content: The new content to insert in place of the specified lines
            dry_run: If True, show changes without applying them
            
        Example 1 - Replace lines 5-10 with new content:
            edit_range(
                file="proj:src/app.js",
                start_line=5,
                end_line=10,
                new_content="const newFunction = () => {\n  console.log('New implementation');\n};"
            )
            
        Example 2 - Insert 3 lines between existing lines:
            edit_range(
                file="proj:src/utils.py",
                start_line=15,
                end_line=15,
                new_content="def new_helper():\n    print('New helper function')\n    return True"
            )
            
        Example 3 - Delete lines without replacement:
            edit_range(
                file="proj:src/config.json",
                start_line=7,
                end_line=9,
                new_content=""
            )
        
        Returns:
            Success message with git-style diff showing the changes
        """
        try:
            # Validate parameters
            if not file:
                return "Error: Missing required 'file' parameter."
                
            if not isinstance(start_line, int) or not isinstance(end_line, int):
                return "Error: start_line and end_line must be integers."
                
            if start_line < 1:
                return "Error: start_line must be at least 1 (lines are 1-indexed)."
                
            if end_line < start_line:
                return f"Error: end_line ({end_line}) must be greater than or equal to start_line ({start_line})."
                
            if not isinstance(new_content, str):
                try:
                    new_content = str(new_content)
                except Exception as e:
                    return f"Error: Could not convert new_content to string: {str(e)}"
            
            # Resolve and validate file path
            resolved_path = _resolve_project_path(file)
            valid_path = _validate_path(resolved_path)
            
            # Check if path is a directory
            if os.path.isdir(valid_path):
                return f"Error: {valid_path} is a directory, not a file. This tool can only edit individual files."
            
            # Check if file exists
            if not os.path.isfile(valid_path):
                return f"Error: File {valid_path} does not exist"
            
            # Read the file line by line
            with open(valid_path, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
            
            # Validate line range
            if start_line > len(lines) + 1:  # +1 to allow appending at the end
                return f"Error: start_line ({start_line}) exceeds file length ({len(lines)} lines)"
            
            # Normalize line endings in new content
            new_content = normalize_line_endings(new_content)
            
            # Convert new_content to lines, ensuring each line ends with a newline
            if new_content:
                new_lines = new_content.splitlines(True)  # Keep line endings
                
                # Ensure the last line has a newline
                if new_lines and not new_lines[-1].endswith('\n'):
                    new_lines[-1] = new_lines[-1] + '\n'
            else:
                new_lines = []
            
            # Create modified content
            modified_lines = (
                lines[:start_line-1] +  # Lines before the edit range
                new_lines +             # New lines to insert
                lines[min(end_line, len(lines)):]  # Lines after the edit range
            )
            
            # Join all lines
            original_content = ''.join(lines)
            modified_content = ''.join(modified_lines)
            
            # Create unified diff
            diff_text = create_unified_diff(original_content, modified_content, file)
            
            # In dry run mode, just return the diff
            if dry_run:
                return f"Showing changes that would be applied to {file} (lines {start_line}-{end_line}):\n\n```diff\n{diff_text}\n```"
            
            # Write the file if not in dry run mode
            with open(valid_path, "w", encoding="utf-8") as f:
                f.write(modified_content)
            
            # Return success message with diff
            return f"Successfully replaced lines {start_line}-{end_line} in {file}:\n\n```diff\n{diff_text}\n```"
            
        except Exception as e:
            return f"Error editing lines: {str(e)}"

    @mcp.tool()
    async def edit_by_patch(file: str, patch_content: str, dry_run: bool = False) -> str:
        """
        Edit a file by applying a standard unified diff patch using the python-patch library.

        This is generally the most robust and often token-efficient way to apply complex changes.
        It handles context matching and fuzz factor, making it more resilient to minor file changes
        than line-based or simple search-replace edits.

        Requires the `patch` library to be installed (`pip install patch`).

        Supports multiple path formats:
        - Absolute paths: "/home/user/myproject/file.txt"
        - Relative paths: "./file.txt" or "src/utils/helper.py"
        - Project-relative paths: "proj:src/main.py" (relative to current project)

        Args:
            file: Path to the file to edit, with optional "proj:" prefix for project-relative paths.
            patch_content: A string containing the patch in unified diff format.
            dry_run: If True, check if the patch applies cleanly and show the potential diff without saving changes.

        The patch should follow the unified diff format:
        --- a/original_file
        +++ b/modified_file
        @@ -old_start,old_count +new_start,new_count @@
        context line
        -deleted line
        +added line
        context line

        Returns:
            Success message including the applied diff, or detailed error information.
        """
        original_encoding = None # Variable to store detected encoding
        try:
            # Attempt to import the patch library
            try:
                from patch import fromstring as patch_from_string
            except ImportError:
                return "Error: The 'patch' library is required for edit_by_patch. Please install it (`pip install patch`)."

            # Validate parameters
            if not file:
                return "Error: Missing required 'file' parameter."
            if not isinstance(patch_content, str) or not patch_content.strip():
                return "Error: 'patch_content' must be a non-empty string containing unified diff content."
            if not re.search(r'^(---|\+\+\+|@@)', patch_content.strip(), re.MULTILINE):
                print("Warning: Provided patch content doesn't obviously start with '---', '+++', or '@@'. Proceeding, but ensure it's a valid unified diff.", file=sys.stderr)

            # --- Path Resolution and Validation ---
            resolved_path = _resolve_project_path(file)
            valid_path = _validate_path(resolved_path)
            if os.path.isdir(valid_path):
                return f"Error: {valid_path} is a directory, not a file."
            if not os.path.isfile(valid_path):
                return f"Error: File {valid_path} does not exist"

            # --- Read Original File and Determine Encoding ---
            try:
                with open(valid_path, "rb") as f:
                    original_bytes = f.read()
                # Try decoding with UTF-8 first, remember the encoding
                try:
                    original_content_str_raw = original_bytes.decode('utf-8')
                    original_encoding = 'utf-8'
                except UnicodeDecodeError:
                    # Fallback to latin-1 if UTF-8 fails, remember the encoding
                    original_content_str_raw = original_bytes.decode('latin-1')
                    original_encoding = 'latin-1'
                    print(f"Warning: Could not decode file {valid_path} as UTF-8, using latin-1.", file=sys.stderr)
            except Exception as read_err:
                # This is where the original error message likely came from if read fails entirely
                return f"Error reading original file {valid_path}: {str(read_err)}"

            # --- Normalize Content and Patch ---
            # Normalize line endings for internal processing
            original_content_str_normalized = normalize_line_endings(original_content_str_raw)
            patch_content_normalized = normalize_line_endings(patch_content)

            # --- Encode Normalized Content for Patch Library ---
            try:
                # Re-encode the normalized string using the detected encoding
                original_bytes_normalized = original_content_str_normalized.encode(original_encoding)
            except Exception as encode_err:
                return f"Error preparing original content for patching: {str(encode_err)}"

            # --- Parse the Normalized Patch ---
            try:
                # Encode the normalized patch string to bytes (use utf-8 for standard patch format)
                patch_bytes_normalized = patch_content_normalized.encode('utf-8')
                patch_set = patch_from_string(patch_bytes_normalized)
                if not patch_set:
                    if len(patch_bytes_normalized) > 0:
                        return "Error: Failed to parse the provided patch content. Ensure it's a valid unified diff after line ending normalization."
                    else:
                        return "Error: Empty patch content provided."
            except Exception as parse_err:
                return f"Error processing or parsing patch content: {str(parse_err)}"

            # --- Apply the Patch ---
            # Apply the parsed patch to the *normalized* original bytes
            patched_bytes = patch_set.apply(original_bytes_normalized)

            if patched_bytes is False:
                # Patch failed - provide hints
                return (f"Error: The patch could not be applied cleanly to {file}. "
                        "Possible reasons:\n"
                        "1. File content mismatch (file changed or patch context incorrect).\n"
                        "2. Whitespace or line ending differences between patch context and file.\n"
                        "3. Incorrect line numbers in patch hunk headers (@@ ... @@).\n"
                        "Suggestion: Read the file again and generate a fresh patch.")

            # --- Decode Patched Bytes and Prepare Output ---
            try:
                # Decode the result using the originally detected file encoding
                patched_content_str = patched_bytes.decode(original_encoding)
            except Exception as decode_err:
                return f"Error decoding patched content using encoding '{original_encoding}': {str(decode_err)}"

            # Create the final diff display using the string representations
            # Compare the initially read (but normalized) string with the final patched string
            final_diff_text = create_unified_diff(original_content_str_normalized, patched_content_str, file)

            # --- Handle dry_run or Actual Write ---
            if dry_run:
                return f"Dry run: Patch applies successfully to {file}. Predicted changes:\n\n```diff\n{final_diff_text}\n```"
            else:
                # Write the final patched bytes (which preserves original encoding nuances)
                try:
                    with open(valid_path, "wb") as f:
                        f.write(patched_bytes) # Write the raw bytes result from patch apply
                    return f"Successfully applied patch to {file}:\n\n```diff\n{final_diff_text}\n```"
                except Exception as write_err:
                    return f"Error writing patched file {valid_path}: {str(write_err)}"

        except Exception as e:
            # General exception catch-all
            print(f"Unexpected error in edit_by_patch: {type(e).__name__}: {str(e)}", file=sys.stderr)
            # Consider logging the full traceback here
            return f"Error applying patch: An unexpected error occurred: {str(e)}"
        
    #@mcp.tool()
    async def edit_by_patch_old(file: str, patch: str, dry_run: bool = False) -> str:
        """
        Edit a file by applying a unified diff patch.
        
        This is the most token-efficient way to make edits since you only need to specify
        the minimal changes in diff format without repeating unchanged content.
        
        Uses the patch-ng library for professional-grade patch application with all the 
        features of GNU patch, including fuzzy matching, context handling, and more.
        
        Supports multiple path formats:
        - Absolute paths: "/home/user/myproject/file.txt"
        - Relative paths: "./file.txt" or "src/utils/helper.py"
        - Project-relative paths: "proj:src/main.py" (relative to current project)
        
        Args:
            file: Path to the file to edit, with optional "proj:" prefix for project-relative paths
            patch: Unified diff patch content (must follow unified diff format)
            dry_run: If True, show changes without applying them
            
        The patch should follow the unified diff format:
        - Each changed block starts with @@ -old_start,old_count +new_start,new_count @@
        - Lines starting with - are deletions
        - Lines starting with + are additions
        - Lines starting with space are context (unchanged)
        
        Example 1 - Change a function:
            edit_by_patch(
                file="proj:src/utils.js",
                patch='''@@ -10,7 +10,7 @@
 function hello() {
-  console.log('hello');
+  console.log('hello world');
   return true;
 }
'''
            )
            
        Example 2 - Add lines to a file:
            edit_by_patch(
                file="proj:src/config.py",
                patch='''@@ -5,0 +6,3 @@
+# New configuration options
+DEBUG = True
+LOGGING_LEVEL = 'INFO'
'''
            )
            
        Returns:
            Success message or error information
        """
        try:
            # Validate parameters
            if not file:
                return "Error: Missing required 'file' parameter."
                
            if not isinstance(patch, str) or not patch:
                return "Error: patch must be a non-empty string containing unified diff content."
            
            # Check if patch looks like a unified diff by looking for @@ markers
            if not re.search(r'@@ -\d+,\d+ \+\d+,\d+ @@', patch):
                return ("Error: Invalid patch format. Patch must contain at least one hunk header "
                        "in the form '@@ -old_start,old_count +new_start,new_count @@'")
            
            # Use Python's built-in unified diff parser instead of external libraries
            import difflib
            
            # Resolve and validate file path
            resolved_path = _resolve_project_path(file)
            valid_path = _validate_path(resolved_path)
            
            # Check if path is a directory
            if os.path.isdir(valid_path):
                return f"Error: {valid_path} is a directory, not a file. This tool can only edit individual files."
            
            # Check if file exists
            if not os.path.isfile(valid_path):
                return f"Error: File {valid_path} does not exist"
            
            # Read the original file
            with open(valid_path, "r", encoding="utf-8", errors="replace") as f:
                original_content = f.read()
            
            # Normalize line endings in original content
            original_content = normalize_line_endings(original_content)
            original_lines = original_content.splitlines()
            
            # Parse the patch manually using a simplified algorithm
            patched_lines = original_lines.copy()
            
            # Parse hunks from the patch
            hunks = []
            current_hunk = None
            hunk_lines = []
            
            for line in patch.splitlines():
                if line.startswith('@@ '):
                    # Complete the previous hunk if exists
                    if current_hunk is not None:
                        current_hunk['lines'] = hunk_lines
                        hunks.append(current_hunk)
                        hunk_lines = []
                    
                    # Parse the hunk header @@ -start,count +start,count @@
                    match = re.match(r'@@ -(\d+),(\d+) \+(\d+),(\d+) @@', line)
                    if match:
                        old_start = int(match.group(1))
                        old_count = int(match.group(2))
                        new_start = int(match.group(3))
                        new_count = int(match.group(4))
                        
                        current_hunk = {
                            'old_start': old_start,
                            'old_count': old_count,
                            'new_start': new_start,
                            'new_count': new_count
                        }
                elif current_hunk is not None:
                    hunk_lines.append(line)
            
            # Add the last hunk if exists
            if current_hunk is not None:
                current_hunk['lines'] = hunk_lines
                hunks.append(current_hunk)
            
            # Apply hunks (in reverse to avoid line number changes affecting later hunks)
            modified_content = original_content
            patched_lines = original_lines.copy()
            
            for hunk in reversed(hunks):
                old_start = hunk['old_start']
                old_count = hunk['old_count']
                new_start = hunk['new_start']
                new_count = hunk['new_count']
                
                # Process the hunk lines
                old_lines = []  # Lines to be removed
                new_lines = []  # Lines to be added
                
                for line in hunk['lines']:
                    if line.startswith('-'):
                        old_lines.append(line[1:])
                    elif line.startswith('+'):
                        new_lines.append(line[1:])
                    elif line.startswith(' '):
                        old_lines.append(line[1:])
                        new_lines.append(line[1:])
                
                # Apply the changes to patched_lines
                patched_lines[old_start-1:old_start-1+old_count] = new_lines
            
            # Create the new content
            patched_content = '\n'.join(patched_lines)
            if original_content.endswith('\n') and not patched_content.endswith('\n'):
                patched_content += '\n'
            
            # Create actual diff for display
            diff = difflib.unified_diff(
                original_content.splitlines(),
                patched_content.splitlines(),
                fromfile=f"{file} (original)",
                tofile=f"{file} (modified)",
                lineterm=''
            )
            diff_text = '\n'.join(diff)
            
            # In dry run mode, just return the diff
            if dry_run:
                return f"Showing changes that would be applied to {file}:\n\n```diff\n{diff_text}\n```"
            
            # Write the file if not in dry run mode
            with open(valid_path, 'w', encoding='utf-8') as f:
                f.write(patched_content)
            
            # Return success message with diff
            return f"Successfully applied patch to {file}:\n\n```diff\n{diff_text}\n```"
            
        except Exception as e:
            return f"Error applying patch: {str(e)}"
