"""
Project navigation and context tools for Desktop Commander MCP Server.
Helps with discovering and navigating project structures and loading project contexts.

The tools scan the ~/src directory by default for projects (configurable via project_default_path
in config.json), looking both at direct subdirectories and one level deeper to find relevant projects.
"""

import os
import sys
import json
import glob
from typing import List, Dict, Optional
from pathlib import Path
from datetime import datetime

# No longer importing the structured memo creator

# Load configuration
def load_config():
    """Load configuration from config.json file."""
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.json")
    try:
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                return json.load(f)
        else:
            print(f"Warning: Config file not found at {config_path}", file=sys.stderr)
            return {"project_default_path": "src"}
    except Exception as e:
        print(f"Error loading config: {str(e)}", file=sys.stderr)
        return {"project_default_path": "src"}

# Get the project default path from config
config = load_config()
PROJECT_DEFAULT_PATH = config.get("project_default_path", "src")

# Expand the project path
def get_project_base_dir():
    """Get the expanded project base directory."""
    home_dir = os.path.expanduser("~")
    # If PROJECT_DEFAULT_PATH is an absolute path, use it directly
    if os.path.isabs(PROJECT_DEFAULT_PATH):
        return PROJECT_DEFAULT_PATH
    # Otherwise, join with home directory
    return os.path.join(home_dir, PROJECT_DEFAULT_PATH)

# Track the currently active project
current_project = {
    "path": None,
    "name": None,
    "memo_path": None,
    "has_memo": False
}

def register_tools(mcp):
    """Register project navigation tools with the MCP server."""
    
    @mcp.tool()
    def explore_project(project_path: str = None) -> str:
        """
        Explore a project and generate a high-level understanding.
        
        Args:
            project_path: Optional path to the project (uses current project if not specified)
            
        Returns:
            Summary of project exploration and analysis
        """
        try:
            # Use current project if no path specified
            if not project_path:
                if not current_project["path"]:
                    return "No active project. Use discover_projects and use_project to select a project."
                project_path = current_project["path"]
            
            project_path = os.path.abspath(project_path)
            if not os.path.exists(project_path):
                return f"Project not found: {project_path}"
            
            # Get project info
            project_info = _check_if_project(project_path) or {}
            project_name = project_info.get("name") or os.path.basename(project_path)
            
            # Create project analysis
            analysis = {}
            
            # Check for repository information
            git_path = os.path.join(project_path, ".git")
            has_git = os.path.exists(git_path)
            analysis["has_git"] = has_git
            
            # Check for common project files
            common_files = {
                "package.json": "Node.js/JavaScript",
                "setup.py": "Python",
                "requirements.txt": "Python",
                "Cargo.toml": "Rust",
                "pom.xml": "Java/Maven",
                "build.gradle": "Java/Gradle",
                "CMakeLists.txt": "C++/CMake",
                "Makefile": "C/C++",
                "Dockerfile": "Docker",
                "docker-compose.yml": "Docker Compose",
                "go.mod": "Go",
                "mix.exs": "Elixir",
                "Gemfile": "Ruby"
            }
            
            detected_types = []
            for file, tech_type in common_files.items():
                if os.path.exists(os.path.join(project_path, file)):
                    detected_types.append(tech_type)
            
            analysis["detected_types"] = detected_types
            
            # Collect directory structure information
            dirs = []
            files_by_ext = {}
            
            for root, directories, files in os.walk(project_path, topdown=True):
                # Skip git and virtual environment directories
                directories[:] = [d for d in directories if d not in [".git", "node_modules", "__pycache__", "venv", ".venv", "env", ".env"]]
                
                rel_path = os.path.relpath(root, project_path)
                if rel_path != ".":
                    dirs.append(rel_path)
                
                # Count file extensions
                for file in files:
                    _, ext = os.path.splitext(file)
                    if ext:
                        ext = ext.lower()
                        files_by_ext[ext] = files_by_ext.get(ext, 0) + 1
            
            analysis["directories"] = dirs[:10]  # Limit to top 10 directories
            analysis["file_types"] = {k: v for k, v in sorted(files_by_ext.items(), key=lambda item: item[1], reverse=True)[:10]}
            
            # Generate summary text
            summary = [f"# Project Analysis: {project_name}"]
            
            # Project type
            if detected_types:
                summary.append("\n## Project Type")
                summary.append(f"This appears to be a {', '.join(detected_types)} project.")
            
            # Repository info
            summary.append("\n## Repository")
            if has_git:
                summary.append("This project is a Git repository.")
            else:
                summary.append("This project is not a Git repository.")
            
            # Structure summary
            summary.append("\n## Structure Overview")
            if dirs:
                summary.append("Key directories:")
                for d in analysis["directories"][:5]:
                    summary.append(f"- {d}")
            
            # File types
            if files_by_ext:
                summary.append("\nFile types:")
                for ext, count in analysis["file_types"].items():
                    summary.append(f"- {ext}: {count} files")
            
            # Create memo suggestion
            memo_suggestion = "\n## Suggested Memo Content\n"
            memo_suggestion += f"""
# Project: {project_name}

## Overview
- {project_name} is a {'/'.join(detected_types[:2]) if detected_types else 'software'} project
- {len(analysis.get('directories', []))} directories and multiple file types found
- Main technologies: {', '.join(detected_types) if detected_types else 'Unknown'}

## Current Status
- Initial project exploration completed on {datetime.now().strftime('%Y-%m-%d')}
- Further analysis needed for specific functionality

## Action Items
### TODO
- [ ] High: Review project documentation
- [ ] Medium: Identify key components
- [ ] Medium: Document project architecture

## Knowledge Base
### Implementation
- {', '.join(detected_types) if detected_types else 'Unknown'} project structure
- Key directories: {', '.join(analysis.get('directories', [])[:3]) if analysis.get('directories') else 'None identified'}
"""
            
            # Combine everything
            result = "\n".join(summary) + "\n\n" + memo_suggestion
            
            # Create a basic memo structure if there's no memo
            if not project_info.get("has_memo"):
                memo_path = os.path.join(project_path, "claude_memo.md")
                try:
                    with open(memo_path, "w") as f:
                        f.write(memo_suggestion.strip())
                    result += f"\n\nCreated initial memo file at: {memo_path}"
                except Exception as e:
                    result += f"\n\nFailed to create memo file: {str(e)}"
            
            return result
        except Exception as e:
            return f"Error exploring project: {str(e)}"
    
    @mcp.tool()
    def discover_projects(base_dir: Optional[str] = None) -> str:
        """
        Discover potential projects in the specified directory or default project directory.
        
        A directory is considered a potential project if it contains:
        - A git repository (.git directory)
        - A package.json, setup.py, or similar project definition file
        - A claude_memo.md file
        
        Args:
            base_dir: Base directory to search for projects (defaults to configured project_default_path)
        
        Returns:
            List of potential projects with their metadata
        """
        base_dir = base_dir or get_project_base_dir()
        try:
            base_dir = os.path.abspath(base_dir)
            if not os.path.exists(base_dir):
                return f"Directory not found: {base_dir}"
                
            projects = []
            
            # Look for direct subdirectories that might be projects
            for item in os.listdir(base_dir):
                item_path = os.path.join(base_dir, item)
                if not os.path.isdir(item_path):
                    continue
                
                # Check if this directory looks like a project
                project_info = _check_if_project(item_path)
                if project_info:
                    projects.append(project_info)
                    
                # If it's not a project itself, check one level deeper
                elif os.path.isdir(item_path):
                    try:
                        for subitem in os.listdir(item_path):
                            subitem_path = os.path.join(item_path, subitem)
                            if not os.path.isdir(subitem_path):
                                continue
                            
                            # Check if this subdirectory looks like a project
                            sub_project_info = _check_if_project(subitem_path)
                            if sub_project_info:
                                projects.append(sub_project_info)
                    except (PermissionError, OSError):
                        # Skip directories we can't access
                        pass
            
            if not projects:
                return f"No projects found in {base_dir}"
                
            # Format results
            result = [f"Found {len(projects)} projects in {base_dir}:"]
            for project in projects:
                memo_status = "Has memo" if project["has_memo"] else "No memo"
                project_type = f"Type: {project['type']}" if project.get("type") else ""
                result.append(f"- {project['name']} ({memo_status}) {project_type} - {project['path']}")
                
            return "\n".join(result)
        except Exception as e:
            return f"Error discovering projects: {str(e)}"
    
    @mcp.tool()
    def use_project(project_path: str) -> str:
        """
        Set the current working project and load its context.
        
        Args:
            project_path: Path to the project directory
            
        Returns:
            Project context summary if available, otherwise basic project info
        """
        try:
            project_path = os.path.abspath(project_path)
            if not os.path.exists(project_path):
                return f"Project not found: {project_path}"
                
            if not os.path.isdir(project_path):
                return f"Not a directory: {project_path}"
            
            # Update the current project
            project_info = _check_if_project(project_path)
            if not project_info:
                return f"Not a recognized project: {project_path}"
                
            # Update current project and change directory
            global current_project
            current_project = project_info
            os.chdir(project_path)
            
            # If there's a memo, load and return it
            if project_info["has_memo"]:
                memo_content = _load_memo(project_info["memo_path"])
                return f"Switched to project: {project_info['name']}\n\nProject memo found! Reading context...\n\nProject context from memo:\n\n{memo_content}"
            else:
                # No memo, suggest exploration and creation
                return f"""Switched to project: {project_info['name']}

No project memo found. Would you like me to:
1. Explore the project and create an initial understanding?
2. Create a basic memo structure for this project?
3. Continue without a project memo?

Creating a project memo would help maintain knowledge about this project across conversations."""
        except Exception as e:
            return f"Error using project: {str(e)}"
    
    @mcp.tool()
    def get_current_project() -> str:
        """
        Get information about the currently active project.
        
        Returns:
            Current project info or message if no project is active
        """
        global current_project
        if not current_project["path"]:
            return "No active project. Use discover_projects and use_project to select a project."
            
        result = [f"Current project: {current_project['name']}"]
        result.append(f"Path: {current_project['path']}")
        result.append(f"Has memo: {current_project['has_memo']}")
        
        if current_project.get("type"):
            result.append(f"Type: {current_project['type']}")
            
        if current_project["has_memo"]:
            result.append("\nUse read_memo() to view the full project context.")
            
        return "\n".join(result)
    
    @mcp.tool()
    def create_project_memo(content: str) -> str:
        """
        Create a memo file for the current project with the specified content.
        
        Args:
            content: Content to write to the memo file
            
        Returns:
            Success message or error
        """
        global current_project
        if not current_project["path"]:
            return "No active project. Use discover_projects and use_project to select a project."
            
        try:
            memo_path = os.path.join(current_project["path"], "claude_memo.md")
            with open(memo_path, "w") as f:
                f.write(content)
                
            # Update current project info
            current_project["has_memo"] = True
            current_project["memo_path"] = memo_path
            
            return f"Created project memo for {current_project['name']}"
        except Exception as e:
            return f"Error creating project memo: {str(e)}"
            
    @mcp.tool()
    def search_for_project(name: str, base_dir: Optional[str] = None) -> str:
        """
        Search for a project by name in the specified base directory.
        
        Args:
            name: Name or partial name of the project
            base_dir: Base directory to search in (defaults to configured project_default_path)
            
        Returns:
            Project matches if found
        """
        base_dir = base_dir or get_project_base_dir()
        try:
            base_dir = os.path.abspath(base_dir)
            if not os.path.exists(base_dir):
                return f"Base directory not found: {base_dir}"
                
            # Use glob to find matching directories
            pattern = os.path.join(base_dir, f"**/*{name}*")
            matches = []
            
            for path in glob.glob(pattern, recursive=True):
                if os.path.isdir(path):
                    project_info = _check_if_project(path)
                    if project_info:
                        matches.append(project_info)
            
            if not matches:
                return f"No projects matching '{name}' found in {base_dir}"
                
            # Format results
            result = [f"Found {len(matches)} projects matching '{name}':"]
            for project in matches:
                memo_status = "Has memo" if project["has_memo"] else "No memo"
                project_type = f"Type: {project['type']}" if project.get("type") else ""
                result.append(f"- {project['name']} ({memo_status}) {project_type} - {project['path']}")
                result.append(f"  Use project with: use_project(\"{project['path']}\")")
                
            return "\n".join(result)
        except Exception as e:
            return f"Error searching for projects: {str(e)}"

    # Helper functions (not exposed as tools)
    def _check_if_project(directory: str) -> Optional[Dict]:
        """Check if a directory is a project and return project info."""
        if not os.path.isdir(directory):
            return None
            
        dir_name = os.path.basename(directory)
        
        # Initialize project info
        project_info = {
            "name": dir_name,
            "path": directory,
            "memo_path": None,
            "has_memo": False,
            "type": None
        }
        
        # Check for memo file
        memo_path = os.path.join(directory, "claude_memo.md")
        if os.path.exists(memo_path):
            project_info["memo_path"] = memo_path
            project_info["has_memo"] = True
        
        # Check for project indicators
        if os.path.exists(os.path.join(directory, ".git")):
            project_info["type"] = "git"
            return project_info
            
        if os.path.exists(os.path.join(directory, "package.json")):
            project_info["type"] = "node"
            return project_info
            
        if os.path.exists(os.path.join(directory, "setup.py")):
            project_info["type"] = "python"
            return project_info
            
        if os.path.exists(os.path.join(directory, "pom.xml")):
            project_info["type"] = "java"
            return project_info
            
        if os.path.exists(os.path.join(directory, "Cargo.toml")):
            project_info["type"] = "rust"
            return project_info
            
        # If it has a memo file but no other indicators, still consider it a project
        if project_info["has_memo"]:
            return project_info
            
        # Look for common project directories
        common_dirs = ["src", "lib", "app", "source"]
        for common_dir in common_dirs:
            if os.path.isdir(os.path.join(directory, common_dir)):
                return project_info
                
        # Not enough evidence this is a project
        return None
        
    def _load_memo(memo_path: str) -> str:
        """Load memo content from file."""
        try:
            with open(memo_path, "r") as f:
                return f.read()
        except Exception as e:
            return f"Error loading memo: {str(e)}"
