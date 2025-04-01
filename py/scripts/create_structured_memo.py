#!/usr/bin/env python3
"""
Script to create a structured JSON memo for a project according to the enhanced-project-memo-schema.json.
This tool can be used to generate standardized project memos that can be used across different projects.
"""

import os
import sys
import json
import re
import glob
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add the project root to the Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(script_dir))
sys.path.insert(0, project_root)

# Load the schema
SCHEMA_PATH = os.path.join(project_root, "py/desktop_commander/tools/data/enhanced-project-memo-schema.json")

def load_schema():
    """Load the memo schema definition."""
    try:
        with open(SCHEMA_PATH, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading schema: {e}")
        return None

def analyze_project(project_path: str) -> Dict[str, Any]:
    """
    Analyze a project directory to generate project information.
    
    Args:
        project_path: Path to the project directory
        
    Returns:
        Dictionary with project analysis results
    """
    project_path = os.path.abspath(project_path)
    project_name = os.path.basename(project_path)
    
    # Initialize analysis dictionary
    analysis = {
        "name": project_name,
        "path": project_path,
        "detected_types": [],
        "has_git": False,
        "directories": [],
        "file_types": {},
    }
    
    # Check for repository information
    git_path = os.path.join(project_path, ".git")
    analysis["has_git"] = os.path.exists(git_path)
    
    # Get current branch if it's a git repository
    current_branch = None
    if analysis["has_git"]:
        try:
            head_path = os.path.join(git_path, "HEAD")
            if os.path.exists(head_path):
                with open(head_path, "r") as f:
                    head_content = f.read().strip()
                    ref_match = re.search(r"ref: refs/heads/(.+)$", head_content)
                    if ref_match:
                        current_branch = ref_match.group(1)
        except Exception:
            pass
    
    analysis["current_branch"] = current_branch
    
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
    
    for file, tech_type in common_files.items():
        if os.path.exists(os.path.join(project_path, file)):
            analysis["detected_types"].append(tech_type)
    
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
    
    analysis["directories"] = dirs[:20]  # Limit to top 20 directories
    analysis["file_types"] = {k: v for k, v in sorted(files_by_ext.items(), key=lambda item: item[1], reverse=True)[:15]}
    
    # Try to detect README for overview
    readme_paths = glob.glob(os.path.join(project_path, "README*"))
    readme_content = ""
    if readme_paths:
        try:
            with open(readme_paths[0], "r", encoding="utf-8", errors="ignore") as f:
                readme_content = f.read()
        except Exception:
            pass
    
    analysis["readme"] = readme_content
    
    return analysis

def create_structured_memo(project_path: str, output_path: Optional[str] = None) -> str:
    """
    Create a structured memo for a project based on the schema.
    
    Args:
        project_path: Path to the project directory
        output_path: Optional path to save the structured memo JSON
        
    Returns:
        Path to the created memo file
    """
    schema = load_schema()
    if not schema:
        return "Failed to load schema"
    
    # Analyze the project
    analysis = analyze_project(project_path)
    
    # Extract project name and overview
    project_name = analysis["name"]
    overview = []
    
    # Extract overview from README if available
    if analysis["readme"]:
        # Try to get the first paragraph after the title
        readme_lines = analysis["readme"].split("\n")
        in_paragraph = False
        paragraph = []
        
        for line in readme_lines[1:]:  # Skip title line
            line = line.strip()
            if line and not line.startswith("#") and not line.startswith("---"):
                in_paragraph = True
                paragraph.append(line)
            elif in_paragraph and not line:
                break
        
        if paragraph:
            overview.append(" ".join(paragraph))
    
    # Add detected technologies
    if analysis["detected_types"]:
        overview.append(f"Uses {', '.join(analysis['detected_types'])}")
    
    # Create the structured memo
    today = datetime.now().strftime("%Y-%m-%d")
    
    structured_memo = {
        "project": {
            "name": project_name,
            "overview": overview or [f"{project_name} project - needs description"]
        },
        "currentStatus": {
            "branch": analysis.get("current_branch") or "main",
            "highlights": ["Initial project analysis completed"],
            "lastUpdated": datetime.now().isoformat()
        },
        "actionItems": {
            "todo": [
                {
                    "task": "Review project documentation",
                    "priority": "High"
                },
                {
                    "task": "Identify key components",
                    "priority": "Medium"
                }
            ],
            "inProgress": [],
            "blocked": [],
            "completed": []
        },
        "knowledgeBase": {
            "implementation": [
                f"{', '.join(analysis['detected_types']) if analysis['detected_types'] else 'Unknown'} project structure",
                f"Key directories: {', '.join(analysis['directories'][:5]) if analysis['directories'] else 'None identified'}"
            ],
            "configuration": [],
            "environment": []
        },
        "fileIndex": {},
        "changeLog": [
            {
                "date": today,
                "changes": ["Initial project memo created"]
            }
        ],
        "metaData": {
            "lastUpdated": datetime.now().isoformat(),
            "version": "1.0.0",
            "schemaUrl": "enhanced-project-memo-schema.json"
        }
    }
    
    # Add some key files to the fileIndex
    for dir_name in analysis["directories"][:3]:
        files = glob.glob(os.path.join(project_path, dir_name, "*.*"))
        for file_path in files[:3]:
            rel_path = os.path.relpath(file_path, project_path)
            key = rel_path.replace("/", "_").replace(".", "_")
            structured_memo["fileIndex"][key] = {
                "path": rel_path,
                "description": f"File in {dir_name} directory",
                "category": dir_name.split("/")[0].capitalize()
            }
    
    # Determine output path if not provided
    if not output_path:
        output_path = os.path.join(project_path, "claude_memo.json")
    
    # Write the structured memo to file
    with open(output_path, "w") as f:
        json.dump(structured_memo, f, indent=2)
    
    print(f"Created structured memo at: {output_path}")
    return output_path

def main():
    parser = argparse.ArgumentParser(description="Create a structured memo for a project")
    parser.add_argument("project_path", help="Path to the project directory")
    parser.add_argument("-o", "--output", help="Path to save the structured memo JSON", default=None)
    args = parser.parse_args()
    
    create_structured_memo(args.project_path, args.output)

if __name__ == "__main__":
    main()