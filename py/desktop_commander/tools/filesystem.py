import os
import pathlib
import shutil
from typing import List, Dict, Any
import asyncio

# Store allowed directories
allowed_directories = [
    os.getcwd(),         # Current working directory
    os.path.expanduser("~")  # User's home directory
]


def normalize_path(p: str) -> str:
    """Normalize path for consistent comparison."""
    return os.path.normpath(p).lower()


def expand_home(filepath: str) -> str:
    """Expand ~ to user's home directory."""
    if filepath.startswith("~/") or filepath == "~":
        return os.path.join(os.path.expanduser("~"), filepath[1:] if filepath != "~" else "")
    return filepath


async def validate_path(requested_path: str) -> str:
    """
    Validate that a path is within allowed directories.
    Returns the absolute path if valid, raises Exception if not.
    """
    expanded_path = expand_home(requested_path)
    absolute = (
        os.path.abspath(expanded_path) if os.path.isabs(expanded_path) 
        else os.path.abspath(os.path.join(os.getcwd(), expanded_path))
    )
    
    normalized_requested = normalize_path(absolute)
    
    # Check if path is within allowed directories
    is_allowed = any(
        normalized_requested.startswith(normalize_path(dir)) 
        for dir in allowed_directories
    )
    
    if not is_allowed:
        raise Exception(f"Access denied - path outside allowed directories: {absolute}")
    
    # Handle symlinks by checking their real path
    try:
        if os.path.exists(absolute):
            real_path = os.path.realpath(absolute)
            normalized_real = normalize_path(real_path)
            
            is_real_path_allowed = any(
                normalized_real.startswith(normalize_path(dir)) 
                for dir in allowed_directories
            )
            
            if not is_real_path_allowed:
                raise Exception("Access denied - symlink target outside allowed directories")
                
            return real_path
    except Exception as e:
        pass
    
    # For new files that don't exist yet, verify parent directory
    parent_dir = os.path.dirname(absolute)
    try:
        if os.path.exists(parent_dir):
            real_parent_path = os.path.realpath(parent_dir)
            normalized_parent = normalize_path(real_parent_path)
            
            is_parent_allowed = any(
                normalized_parent.startswith(normalize_path(dir)) 
                for dir in allowed_directories
            )
            
            if not is_parent_allowed:
                raise Exception("Access denied - parent directory outside allowed directories")
                
            return absolute
        else:
            raise Exception(f"Parent directory does not exist: {parent_dir}")
    except Exception as e:
        raise Exception(f"Parent directory does not exist: {parent_dir}")


# File operation tools
async def read_file(file_path: str) -> str:
    """Read the contents of a file."""
    valid_path = await validate_path(file_path)
    async with asyncio.to_thread():
        with open(valid_path, "r", encoding="utf-8") as f:
            return f.read()


async def write_file(file_path: str, content: str) -> None:
    """Write content to a file."""
    valid_path = await validate_path(file_path)
    async with asyncio.to_thread():
        with open(valid_path, "w", encoding="utf-8") as f:
            f.write(content)


async def read_multiple_files(paths: List[str]) -> List[str]:
    """Read the contents of multiple files."""
    results = []
    for file_path in paths:
        try:
            valid_path = await validate_path(file_path)
            content = await asyncio.to_thread(lambda: open(valid_path, "r", encoding="utf-8").read())
            results.append(f"{file_path}:\n{content}\n")
        except Exception as e:
            results.append(f"{file_path}: Error - {str(e)}")
    return results


async def create_directory(dir_path: str) -> None:
    """Create a directory or ensure it exists."""
    valid_path = await validate_path(dir_path)
    async with asyncio.to_thread():
        os.makedirs(valid_path, exist_ok=True)


async def list_directory(dir_path: str) -> List[str]:
    """List the contents of a directory."""
    valid_path = await validate_path(dir_path)
    
    async with asyncio.to_thread():
        entries = []
        for entry in os.listdir(valid_path):
            full_path = os.path.join(valid_path, entry)
            entry_type = "[DIR]" if os.path.isdir(full_path) else "[FILE]"
            entries.append(f"{entry_type} {entry}")
        return entries


async def move_file(source_path: str, destination_path: str) -> None:
    """Move a file or directory to a new location."""
    valid_source = await validate_path(source_path)
    valid_dest = await validate_path(destination_path)
    
    async with asyncio.to_thread():
        shutil.move(valid_source, valid_dest)


async def search_files(root_path: str, pattern: str) -> List[str]:
    """Search for files matching a pattern."""
    results = []
    
    async def search(current_path: str) -> None:
        try:
            entries = os.listdir(current_path)
            for entry in entries:
                full_path = os.path.join(current_path, entry)
                
                try:
                    # Validate path is allowed
                    await validate_path(full_path)
                    
                    if pattern.lower() in entry.lower():
                        results.append(full_path)
                    
                    if os.path.isdir(full_path):
                        await search(full_path)
                except Exception:
                    continue
        except Exception:
            pass
    
    valid_path = await validate_path(root_path)
    await search(valid_path)
    return results


async def get_file_info(file_path: str) -> Dict[str, Any]:
    """Get detailed information about a file or directory."""
    valid_path = await validate_path(file_path)
    
    async with asyncio.to_thread():
        stats = os.stat(valid_path)
        
        return {
            "size": stats.st_size,
            "created": stats.st_ctime,
            "modified": stats.st_mtime,
            "accessed": stats.st_atime,
            "is_directory": os.path.isdir(valid_path),
            "is_file": os.path.isfile(valid_path),
            "permissions": oct(stats.st_mode)[-3:],
        }


def list_allowed_directories() -> List[str]:
    """Get a list of directories that the server is allowed to access."""
    return allowed_directories