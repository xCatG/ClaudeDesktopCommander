"""
Memo format documentation and templates.
"""

# Template with documentation for the memo format
MEMO_FORMAT_TEMPLATE = """# Project: {project_name}

## Overview
A brief overview of the project, its purpose, and main technologies.
- Include key technologies and implementations
- Describe high-level functionality
- Note current development status

## Current Status
The current state of the project, recent changes, and active work.
- Branch information
- Recent significant changes
- Any ongoing major refactoring

## Action Items
### TODO
Tasks that need to be completed, with priority levels:
- [ ] High: Critical tasks that block other work
- [ ] Medium: Important tasks that should be done soon
- [ ] Low: Nice-to-have improvements

### IN PROGRESS
Tasks currently being worked on:
- [IP] Task description (who is working on it)

### BLOCKED
Tasks that are blocked and why:
- [B] Task description - Blocked by: reason

### COMPLETED
Recently completed tasks with completion date:
- [✓] YYYY-MM-DD Task description

## Knowledge Base
### Implementation
Technical details about implementation:
- Architecture overview
- Key components and their relationships
- Design patterns or approaches used

### Configuration
Information about configuration:
- Environment setup
- Configuration files and options
- Deployment requirements

### Environment
Development environment details:
- Required dependencies
- Setup instructions
- Environment variables

## File Index
### Core
- **path/to/file.ext**: Brief description of the file's purpose

### Utils
- **path/to/util.ext**: Brief description of utility functions

## Change Log
### YYYY-MM-DD
- Change description
- Bug fixes
- Feature additions

## Usage Guide
### Memo Tools
Available tools for working with this memo:
- `read_memo(section)`: Read the entire memo or a specific section
- `update_memo_section(section, content)`: Update a specific section
- `add_todo(task, priority)`: Add a todo item with priority
- `complete_todo(task_pattern)`: Mark a todo as completed
- `add_change_log(change, version)`: Add a change log entry
- `consolidate_memo()`: Clean up and consolidate the memo

### Best Practices
- Keep sections focused and concise
- Update the Current Status when making significant changes
- Add todos for future work
- Document key implementation decisions
- Index important files for easier navigation
- Add change log entries for significant changes

## Reference Links
- [Link Description](url)
- [Documentation](url)
- [Related Resources](url)
"""

def get_memo_template(project_name):
    """Get a formatted memo template with documentation."""
    return MEMO_FORMAT_TEMPLATE.format(project_name=project_name)

def get_memo_guide():
    """Get just the usage guide section of the memo."""
    guide_section = """## Usage Guide
### Memo Tools
Available tools for working with this memo:
- `read_memo(section)`: Read the entire memo or a specific section
- `update_memo_section(section, content)`: Update a specific section
- `add_todo(task, priority)`: Add a todo item with priority
- `complete_todo(task_pattern)`: Mark a todo as completed
- `add_change_log(change, version)`: Add a change log entry
- `consolidate_memo()`: Clean up and consolidate the memo

### Best Practices
- Keep sections focused and concise
- Update the Current Status when making significant changes
- Add todos for future work
- Document key implementation decisions
- Index important files for easier navigation
- Add change log entries for significant changes
"""
    return guide_section
