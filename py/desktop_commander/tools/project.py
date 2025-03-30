"""
Project navigation and context tools for Desktop Commander MCP Server.
Helps with discovering and navigating project structures and loading project contexts.
"""

import os
import sys
import json
import glob
from typing import List, Dict, Optional
from pathlib import Path

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
    def discover_projects(base_dir: Optional[str] = None) -> str:
        """
        Discover potential projects in the specified directory or current directory.
        
        A directory is considered a potential project if it contains:
        - A git repository (.git directory)
        - A package.json, setup.py, or similar project definition file
        - A claude_memo.md file
        
        Args:
            base_dir: Base directory to search for projects (defaults to current directory)
        
        Returns:
            List of potential projects with their metadata
        """
        base_dir = base_dir or os.getcwd()
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
                return f"Switched to project: {project_info['name']}\n\nProject context from memo:\n\n{memo_content}"
            else:
                # No memo, return basic project info
                return f"Switched to project: {project_info['name']}\n\nNo memo file found. Creating a new project context would help maintain knowledge about this project."
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
            base_dir: Base directory to search in (defaults to parent of current directory)
            
        Returns:
            Project matches if found
        """
        base_dir = base_dir or os.path.dirname(os.getcwd())
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
