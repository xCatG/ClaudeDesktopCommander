#!/usr/bin/env python3
"""
Script to transform an existing Claude memo into the new structured format.
"""

import os
import re
import sys
from datetime import datetime

# Define the new memo structure template
MEMO_TEMPLATE = """# Project: {project_name}

## Overview
{overview}

## Current Status
{current_status}

## Action Items
### TODO
{todos}

### IN PROGRESS
{in_progress}

### BLOCKED
{blocked}

### COMPLETED
{completed}

## Knowledge Base
### Implementation
{implementation}

### Configuration
{configuration}

### Environment
{environment}

## Change Log
{change_log}

## Reference Links
{reference_links}
"""

def extract_section(content, section_name):
    """Extract a section from the old memo format."""
    pattern = rf"## {section_name}\n(.*?)(?:\n## |$)"
    match = re.search(pattern, content, re.DOTALL)
    return match.group(1).strip() if match else ""

def extract_subsections(content):
    """Extract subsections from a section."""
    subsections = {}
    pattern = r"### ([^\n]+)\n(.*?)(?:\n### |$)"
    matches = re.finditer(pattern, content, re.DOTALL)
    
    for match in matches:
        subsection_name = match.group(1).strip()
        subsection_content = match.group(2).strip()
        subsections[subsection_name] = subsection_content
    
    return subsections

def extract_todos(content):
    """Extract TODOs from various sections and format them properly."""
    # Find all bullet points with TODO items from previous memo
    todos = []
    todo_pattern = r"- (Push.*|Test.*|Consider.*)"
    
    for line in content.split("\n"):
        match = re.search(todo_pattern, line)
        if match:
            task = match.group(1).strip()
            # Assign a priority based on keywords or default to Medium
            priority = "High" if "important" in task.lower() or "urgent" in task.lower() else "Medium"
            todos.append(f"- [ ] {priority}: {task}")
    
    return "\n".join(todos) if todos else ""

def extract_changes(content):
    """Extract changes from the old memo and format them as a change log."""
    changes = []
    # Try to find sections that correspond to changes
    change_sections = [
        "Project Tool Fix - March 30, 2025",
        "Project Path Configuration - March 30, 2025",
        "WSL Support - March 29, 2025",
        "Memory Test",
        "Recent Changes"
    ]
    
    for section in change_sections:
        section_content = extract_section(content, section)
        if section_content:
            # Try to extract date from section name
            date_match = re.search(r"(\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\w+ \d{1,2}, \d{4})", section)
            if date_match:
                date_str = date_match.group(1)
                # Convert to standardized format
                try:
                    if "/" in date_str or "-" in date_str:
                        date_obj = datetime.strptime(date_str.replace("-", "/"), "%m/%d/%Y")
                        date_formatted = date_obj.strftime("%Y-%m-%d")
                    else:
                        # March 30, 2025 format
                        date_obj = datetime.strptime(date_str, "%B %d, %Y")
                        date_formatted = date_obj.strftime("%Y-%m-%d")
                except:
                    date_formatted = date_str
            else:
                # Use current date if no date in section name
                date_formatted = datetime.now().strftime("%Y-%m-%d")
            
            # Add section to changes
            changes.append(f"### {date_formatted}")
            
            # Extract bullet points
            for line in section_content.split("\n"):
                if line.startswith("-"):
                    changes.append(line)
                else:
                    # Non-bullet lines become summaries
                    if line.strip() and not changes[-1].endswith(":"):
                        changes.append(f"- {line.strip()}")
    
    return "\n".join(changes) if changes else ""

def transform_memo(old_memo_path, new_memo_path=None):
    """Transform an old memo into the new structured format."""
    # Read the old memo
    with open(old_memo_path, "r") as f:
        old_content = f.read()
    
    # Get project name from the first line
    project_name_match = re.search(r"# ([^\n]+)", old_content)
    project_name = project_name_match.group(1) if project_name_match else "Unknown Project"
    project_name = project_name.replace("- Memory File", "").strip()
    
    # Extract main sections
    overview = extract_section(old_content, "Project Overview")
    implementation_details = extract_section(old_content, "Implementation Details")
    key_features = extract_section(old_content, "Key Features")
    
    # Extract Current Status from Recent Changes and current status
    recent_changes = extract_section(old_content, "Recent Changes")
    current_status = "Current branch: python (with recent commits not pushed to origin)\n\n" + recent_changes
    
    # Extract TODOs
    todos = extract_todos(old_content)
    
    # Extract Knowledge Base content
    usage_notes = extract_section(old_content, "Usage Notes")
    wsl_support = extract_section(old_content, "WSL Support - March 29, 2025")
    
    # Combined implementation details
    implementation = f"{implementation_details}\n\n{key_features}"
    
    # Configuration and Environment sections
    configuration = usage_notes
    environment = wsl_support
    
    # Extract Changes
    change_log = extract_changes(old_content)
    
    # Extract any other project-specific references
    reference_links = "- [GitHub Repository](https://github.com/wonderwhy-er/ClaudeDesktopCommander)"
    
    # Fill the template
    new_content = MEMO_TEMPLATE.format(
        project_name=project_name,
        overview=overview,
        current_status=current_status,
        todos=todos,
        in_progress="",  # No in-progress items identified in old memo
        blocked="",      # No blocked items identified in old memo
        completed="",    # No completed items identified in old memo
        implementation=implementation,
        configuration=configuration,
        environment=environment,
        change_log=change_log,
        reference_links=reference_links
    )
    
    # Write to the new memo file or print to stdout
    if new_memo_path:
        with open(new_memo_path, "w") as f:
            f.write(new_content)
        print(f"Transformed memo written to {new_memo_path}")
    else:
        print(new_content)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python transform_memo.py old_memo_path [new_memo_path]")
        sys.exit(1)
    
    old_memo_path = sys.argv[1]
    new_memo_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    transform_memo(old_memo_path, new_memo_path)
