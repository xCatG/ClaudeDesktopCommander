import os
import re
import subprocess
import shutil
from typing import List, Dict, Any, Optional
import asyncio

from desktop_commander.tools.filesystem import validate_path
from desktop_commander.types import SearchResult


async def search_code(options: Dict[str, Any]) -> List[SearchResult]:
    """
    Search file contents using ripgrep.
    Falls back to manual search if ripgrep is not available.
    """
    # Extract options
    root_path = options.get("path", ".")
    pattern = options.get("pattern", "")
    file_pattern = options.get("file_pattern")
    ignore_case = options.get("ignore_case", True)
    max_results = options.get("max_results", 1000)
    include_hidden = options.get("include_hidden", False)
    context_lines = options.get("context_lines", 0)
    
    # Validate path for security
    valid_path = await validate_path(root_path)
    
    # Check if ripgrep is available
    rg_path = shutil.which("rg")
    if not rg_path:
        # Fallback to manual search
        return await search_code_fallback(options)
    
    # Build ripgrep command
    args = [
        rg_path,
        "--json",  # Output in JSON format
        "--line-number",  # Include line numbers
    ]
    
    if ignore_case:
        args.append("-i")
    
    if max_results:
        args.extend(["-m", str(max_results)])
    
    if include_hidden:
        args.append("--hidden")
    
    if context_lines > 0:
        args.extend(["-C", str(context_lines)])
    
    if file_pattern:
        args.extend(["-g", file_pattern])
    
    # Add pattern and path
    args.extend([pattern, valid_path])
    
    # Run ripgrep command
    results = []
    try:
        process = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            text=True
        )
        
        stdout, stderr = await process.communicate()
        
        # Process the output
        if process.returncode in (0, 1):  # 0: matches found, 1: no matches
            for line in stdout.splitlines():
                if not line:
                    continue
                
                try:
                    result = json.loads(line)
                    if result.get("type") == "match":
                        data = result.get("data", {})
                        path = data.get("path", {}).get("text", "")
                        line_number = data.get("line_number", 0)
                        
                        for submatch in data.get("submatches", []):
                            match_text = submatch.get("match", {}).get("text", "")
                            results.append(SearchResult(
                                file=path,
                                line=line_number,
                                match=match_text
                            ))
                    
                    elif result.get("type") == "context" and context_lines > 0:
                        data = result.get("data", {})
                        path = data.get("path", {}).get("text", "")
                        line_number = data.get("line_number", 0)
                        lines_text = data.get("lines", {}).get("text", "").strip()
                        
                        results.append(SearchResult(
                            file=path,
                            line=line_number,
                            match=lines_text
                        ))
                except Exception:
                    # Skip non-JSON lines
                    continue
        
        return results
    except Exception as e:
        # Fallback to manual search if ripgrep fails
        return await search_code_fallback(options)


async def search_code_fallback(options: Dict[str, Any]) -> List[SearchResult]:
    """
    Manual implementation of code search using Python.
    Used as fallback when ripgrep is not available.
    """
    # Extract options
    root_path = options.get("path", ".")
    pattern = options.get("pattern", "")
    file_pattern = options.get("file_pattern")
    ignore_case = options.get("ignore_case", True)
    max_results = options.get("max_results", 1000)
    exclude_dirs = options.get("exclude_dirs", ["node_modules", ".git", "dist"])
    context_lines = options.get("context_lines", 0)
    
    # Validate path for security
    valid_path = await validate_path(root_path)
    
    # Prepare regex patterns
    flags = re.IGNORECASE if ignore_case else 0
    try:
        pattern_regex = re.compile(pattern, flags)
    except re.error:
        # If pattern is not a valid regex, use it as a literal string
        pattern_regex = re.compile(re.escape(pattern), flags)
    
    file_regex = None
    if file_pattern:
        try:
            file_regex = re.compile(file_pattern)
        except re.error:
            # If pattern is not a valid regex, use it as a glob pattern
            import fnmatch
            file_regex = lambda name: fnmatch.fnmatch(name, file_pattern)
    
    results = []
    
    async def search_dir(dir_path: str) -> None:
        if len(results) >= max_results:
            return
        
        try:
            entries = os.listdir(dir_path)
            
            for entry in entries:
                if len(results) >= max_results:
                    break
                
                full_path = os.path.join(dir_path, entry)
                
                try:
                    # Validate path is allowed
                    await validate_path(full_path)
                    
                    if os.path.isdir(full_path):
                        if entry not in exclude_dirs:
                            await search_dir(full_path)
                    elif os.path.isfile(full_path):
                        if not file_regex or file_regex.search(entry):
                            # Read file content
                            try:
                                with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                                    lines = f.readlines()
                                
                                for i, line in enumerate(lines):
                                    if pattern_regex.search(line):
                                        # Add the match
                                        results.append(SearchResult(
                                            file=full_path,
                                            line=i + 1,
                                            match=line.strip()
                                        ))
                                        
                                        # Add context lines
                                        if context_lines > 0:
                                            start_idx = max(0, i - context_lines)
                                            end_idx = min(len(lines) - 1, i + context_lines)
                                            
                                            for j in range(start_idx, end_idx + 1):
                                                if j != i:  # Skip the match line
                                                    results.append(SearchResult(
                                                        file=full_path,
                                                        line=j + 1,
                                                        match=lines[j].strip()
                                                    ))
                                        
                                        if len(results) >= max_results:
                                            break
                            except Exception:
                                # Skip files we can't read
                                pass
                except Exception:
                    # Skip files/directories we can't access
                    continue
        except Exception:
            # Skip directories we can't read
            pass
    
    await search_dir(valid_path)
    return results


async def search_text_in_files(options: Dict[str, Any]) -> List[SearchResult]:
    """
    Main search function that tries ripgrep first, falls back to manual implementation.
    """
    try:
        return await search_code(options)
    except Exception as e:
        # Fallback to manual search
        return await search_code_fallback({
            **options,
            "exclude_dirs": ["node_modules", ".git", "dist"]
        })