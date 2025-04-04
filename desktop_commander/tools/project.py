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
    "type": None
}

def register_tools(mcp):
    """Register project navigation tools with the MCP server."""
    
    # Import the knowledge graph manager here to avoid circular imports
    from desktop_commander.tools.knowledge_graph import graph_manager
    
    @mcp.tool()
    def explore_project(project_path: str = None) -> str:
        """
        Provides instructions for an agent to explore a project and store knowledge.
        
        Args:
            project_path: Optional path to the project (uses current project if not specified)
            
        Returns:
            Instructions for project exploration
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
            project_type = project_info.get("type")
            
            # Get type-specific file suggestions
            type_specific_files = _get_type_specific_files(project_type, project_path)
            
            # Instructions for the agent
            instructions = f"""# Project Exploration Instructions: {project_name}

I'll assist you in exploring this project. Here's what you should do:

1. **Basic Project Analysis**:
   - Examine key files like `README.md`, `package.json`, `setup.py`, etc.
   - Look for documentation in `/docs` or similar directories
   - Identify main technologies and frameworks used

{type_specific_files}

2. **Code Structure Analysis**:
   - Identify core directories (src, lib, app, etc.)
   - Map key components and their relationships
   - Determine entry points and main modules

3. **Store Project Knowledge**:
   After exploration, capture your knowledge by creating a structured knowledge graph:
   ```json
   {{
     "project_name": "{project_name}",
     "entities": [
       {{"id": "1", "name": "Component1", "entityType": "component", "description": "..."}},
       {{"id": "2", "name": "Component2", "entityType": "module", "description": "..."}}
     ],
     "relations": [
       {{"source": "1", "target": "2", "relationship": "depends_on", "description": "..."}}
     ],
     "file_exploration_tips": [
       {{"project_type": "{project_type}", "key_files": ["file1.py", "file2.py"], "description": "These files are important entry points"}}
     ]
   }}
   ```

4. **Save Knowledge**:
   Use `export_project_to_knowledge_graph()` with your JSON structure to save this knowledge

5. **Contribute Exploration Tips**:
   Include any file exploration tips you discover in the knowledge graph's `file_exploration_tips` section. These tips will help future explorations of similar projects.

Once saved, the knowledge will be accessible via:
- `knowledge://{project_name}/graph`
- `knowledge://{project_name}/entities`
- Other knowledge resources

You can also use `sync_memory_to_project_knowledge("{project_name}")` if you've already stored this information in memory.

Would you like me to start exploring the project now?
"""
            return instructions
        except Exception as e:
            return f"Error preparing project exploration: {str(e)}"
            
    def _get_type_specific_files(project_type, project_path):
        """
        Get type-specific file suggestions based on project type.
        
        Args:
            project_type: Type of project (python, node, rust, etc.)
            project_path: Path to the project
            
        Returns:
            Type-specific file suggestions
        """
        # Initialize suggestions
        suggestions = "\n   **Key Files to Examine First**:"
        
        # Get file suggestions based on project type
        if project_type == "python":
            suggestions += """
   - Look for `setup.py` or `pyproject.toml` for project configuration
   - Check for `requirements.txt` or `Pipfile` for dependencies
   - Look for `__main__.py` files as entry points
   - Examine any files named like `app.py`, `main.py`, or `run.py`
   - If a Django project, check for `settings.py`, `urls.py`, and `models.py`
   - If a Flask project, look for an `app` variable or `create_app()` function"""
        elif project_type == "node":
            suggestions += """
   - Examine `package.json` for dependencies and scripts
   - Check for configuration files like `.babelrc`, `tsconfig.json`, `.eslintrc`
   - Look for entry points in `index.js`, `app.js`, or files referenced in package.json "main" field
   - Review `webpack.config.js` or similar build configs
   - If a React project, look for components in `src/components` or similar directories"""
        elif project_type == "rust":
            suggestions += """
   - Check `Cargo.toml` for dependencies and project metadata
   - Look at `src/main.rs` or `src/lib.rs` for entry points
   - Review `build.rs` if it exists for build configurations
   - Examine `.cargo/config.toml` for toolchain configuration"""
        elif project_type == "java":
            suggestions += """
   - Examine `pom.xml` (Maven) or `build.gradle` (Gradle) for dependencies
   - Look for main application classes that have a `main()` method
   - Review `application.properties` or `application.yml` for Spring Boot projects
   - Check for `src/main/java` and `src/test/java` directories"""
        elif project_type == "git":
            # Generic suggestions for git repos without specific project type indicators
            suggestions += """
   - Look for README.md or similar documentation
   - Check for license files
   - Examine any Dockerfile or docker-compose.yml
   - Look for CI/CD configuration files (.github/workflows, .gitlab-ci.yml, etc.)
   - Find entry point files like index.js, main.py, etc. in root or src directories"""
        else:
            # Generic suggestions
            suggestions += """
   - Look for README.md or similar documentation files
   - Check for configuration files in the project root
   - Examine any build or package files
   - Look for source code directories (src, lib, app, etc.)
   - Try to identify main entry point files"""
           
        # Check for file existence and add actual files found
        actual_files = []
        if os.path.exists(os.path.join(project_path, "README.md")):
            actual_files.append("README.md")
        
        if actual_files:
            suggestions += f"\n   - Found key files: {', '.join(actual_files)}"
            
        return suggestions
    
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
                project_type = f"Type: {project['type']}" if project.get("type") else ""
                result.append(f"- {project['name']} {project_type} - {project['path']}")
                
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
            base_dir = get_project_base_dir()
            base_dir = os.path.abspath(base_dir)
            if not os.path.exists(base_dir):
                return f"Base directory not found: {base_dir}"
            # If project_path contains multiple parts, use the last part
            project_name = os.path.basename(os.path.normpath(project_path))

            # Form the absolute path by appending the project name to base_dir
            project_path = os.path.join(base_dir, project_name)
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
            
            # Return project info message with path prefix guidance
            return f"""Switched to project: {project_info['name']}
Current working directory is now: {project_path}

Working with the project files:
- List files with: list_directory("{project_path}") or list_directory(".")
- Use project-relative paths with "proj:" prefix: list_directory("proj:src")
- Read files with: read_file("proj:README.md")
- Write files with: write_file("proj:package.json", json_content) - auto-formats JSON files
- Search with: search_files("proj:src", "*.py")

Would you like me to:
1. Explore the project and create an initial understanding?
2. List the project files with list_directory(".")?
3. Continue without exploration?

You can use explore_project() to analyze the project structure."""
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
        
        if current_project.get("type"):
            result.append(f"Type: {current_project['type']}")
            
        return "\n".join(result)
    
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
                project_type = f"Type: {project['type']}" if project.get("type") else ""
                result.append(f"- {project['name']} {project_type} - {project['path']}")
                result.append(f"  Use project with: use_project(\"{project['path']}\")")
                
            return "\n".join(result)
        except Exception as e:
            return f"Error searching for projects: {str(e)}"
            
    @mcp.tool()
    def export_project_to_knowledge_graph(project_knowledge: str) -> str:
        """
        Export project knowledge to the knowledge graph storage.
        
        This tool takes structured knowledge about a project as a JSON STRING (not a Python object/dictionary)
        and stores it in the knowledge graph for future reference.
        
        Args:
            project_knowledge: JSON string containing project entity and relation data. 
                Must be a properly formatted JSON string (use json.dumps() to convert Python objects).
                Expected format (as a string):
                {
                  "project_name": "MyProject",
                  "entities": [...],
                  "relations": [...]
                }
                
        Example usage:
            knowledge_object = {
                "project_name": "MyProject",
                "entities": [...],
                "relations": [...]
            }
            # Convert to JSON string before passing:
            result = export_project_to_knowledge_graph(json.dumps(knowledge_object))
            
        Returns:
            Success or error message
        """
        try:
            # Access the knowledge_graph manager
            from desktop_commander.tools.knowledge_graph import graph_manager
            
            # Parse the knowledge data
            data = json.loads(project_knowledge)
            
            # Validate required fields
            if "project_name" not in data:
                return "Error: Missing required 'project_name' field in knowledge data"
                
            if "entities" not in data or "relations" not in data:
                return "Error: Knowledge data must contain both 'entities' and 'relations' arrays"
                
            project_name = data["project_name"]
            
            # Extract the key fields
            graph_data = {
                "entities": data["entities"],
                "relations": data["relations"],
                "metadata": {
                    "exported_at": datetime.now().isoformat(),
                    "entity_count": len(data["entities"]),
                    "relation_count": len(data["relations"])
                }
            }
            
            # Save to the knowledge graph
            success = graph_manager.save_graph(project_name, graph_data)
            
            if success:
                return f"""Successfully exported knowledge graph for project: {project_name}
                
Knowledge Graph Resources:
- Complete graph: knowledge://{project_name}/graph
- Entities only: knowledge://{project_name}/entities
- Relations only: knowledge://{project_name}/relations
- Entity by name: knowledge://{project_name}/entity/{{entity_name}}
- Entities by type: knowledge://{project_name}/entity_type/{{entity_type}}"""
            else:
                return f"Failed to export knowledge graph for project: {project_name}"
        except json.JSONDecodeError:
            return "Error: Invalid JSON data provided for knowledge graph"
        except Exception as e:
            return f"Error exporting project to knowledge graph: {str(e)}"
            
    @mcp.tool()
    def import_project_from_knowledge_graph(project_name: str) -> str:
        """
        Import project knowledge from the knowledge graph storage.
        
        Args:
            project_name: Name of the project to import
            
        Returns:
            Project knowledge as JSON string or error message
        """
        try:
            # Access the knowledge_graph manager
            from desktop_commander.tools.knowledge_graph import graph_manager
            
            # Load from the knowledge graph
            graph_data = graph_manager.load_graph(project_name)
            
            if not graph_data:
                return f"No knowledge graph found for project: {project_name}"
                
            # Format the output
            result = {
                "project_name": project_name,
                "entities": graph_data.get("entities", []),
                "relations": graph_data.get("relations", []),
                "metadata": graph_data.get("metadata", {})
            }
            
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error importing project from knowledge graph: {str(e)}"

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
            "type": None
        }
        
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
            
        # Look for common project directories
        common_dirs = ["src", "lib", "app", "source"]
        for common_dir in common_dirs:
            if os.path.isdir(os.path.join(directory, common_dir)):
                return project_info
                
        # Not enough evidence this is a project
        return None
        
