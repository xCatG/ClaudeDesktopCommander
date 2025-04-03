#!/usr/bin/env python3
"""
Script to add smart project management TODOs to the memo.
"""

import os
import re
from datetime import datetime

# Find the memo file
def find_memo_file():
    project_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    memo_path = os.path.join(project_dir, "claude_memo.md")
    return memo_path

# Function to update a section in the memo
def update_section(content, section_name, new_content):
    pattern = rf"(### {section_name}\n)(.*?)(\n###|\Z)"
    match = re.search(pattern, content, re.DOTALL)
    
    if match:
        return content.replace(match.group(0), f"{match.group(1)}{new_content}\n{match.group(3)}")
    return content

# Main function to add TODOs
def add_smart_project_todos():
    memo_path = find_memo_file()
    
    # Read the current memo
    with open(memo_path, "r") as f:
        content = f.read()
    
    # Define new TODOs to add
    todos = """- [ ] High: Implement auto-memo reading for project context
- [ ] High: Add project exploration and indexing for new projects
- [ ] Medium: Add memo format self-documentation for better agent usage
- [ ] Medium: Create file indexing system for tracking project components"""

    # Update the TODO section
    new_todo_section = update_section(content, "TODO", todos)
    
    # Create implementation plans
    implementation_plan = """
## Implementation Plans

### Auto-Memo Reading Plan
1. **Objective**: Automatically suggest reading project memo when switching to a project
2. **Steps**:
   - Modify `use_project` function to check for memo existence
   - Add prompt in response if memo exists: "Project memo found, reading context..."
   - Add prompt if no memo: "No project memo found. Would you like to explore and create one?"
   - Create helper function to determine if a project is new to this agent
3. **Testing**:
   - Test with existing project that has memo
   - Test with project without memo
   - Verify appropriate prompts are shown
4. **Completion Criteria**:
   - Agent automatically reads memo on project switch
   - Agent offers exploration for new projects

### Project Exploration and Indexing Plan
1. **Objective**: Create initial project understanding when none exists
2. **Steps**:
   - Create `explore_project` function that identifies key files
   - Analyze project structure (directories, file types)
   - Identify common patterns (frameworks, languages)
   - Generate high-level summary of project purpose and structure
   - Create initial memo with findings
3. **Testing**:
   - Test on various project types (Python, TypeScript, etc.)
   - Verify summary includes key components
   - Ensure memo creation works correctly
4. **Completion Criteria**:
   - Agent can identify project type and structure
   - Initial memo provides useful project overview

### Memo Format Documentation Plan
1. **Objective**: Add self-documentation to memo format
2. **Steps**:
   - Create "Usage Guide" section in the memo template
   - Document available tools and their purposes
   - Provide examples of memo usage patterns
   - Add best practices for memo organization
3. **Testing**:
   - Verify guide is understandable by other agents
   - Test by asking agent to perform tasks using the guide
4. **Completion Criteria**:
   - New agents can understand and use memo effectively
   - Documentation explains all tools and sections

### File Indexing System Plan
1. **Objective**: Track which files have been analyzed/modified
2. **Steps**: 
   - Create "File Index" section in Knowledge Base
   - Add tracking for file path, purpose, and last modification
   - Implement automatic updating when files are changed
   - Add categorization of files by function
3. **Testing**:
   - Verify files are correctly tracked when modified
   - Test categorization on various file types
   - Check search functionality for finding files
4. **Completion Criteria**:
   - All modified files are tracked in index
   - Index provides useful context about file purposes
   - Index helps navigate project structure
"""

    # Add implementation plans to the memo
    updated_content = new_todo_section + implementation_plan

    # Write the updated memo back to the file
    with open(memo_path, "w") as f:
        f.write(updated_content)
    
    print(f"Updated memo with smart project management TODOs and implementation plans.")

if __name__ == "__main__":
    add_smart_project_todos()
