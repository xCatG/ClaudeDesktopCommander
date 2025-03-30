"""
Enhanced structured memo tools for the Desktop Commander MCP Server.
Allows Claude to maintain structured context across conversations via a memory file.
"""

import os
import re
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

logger = logging.getLogger(__name__)

class MemoSection:
    """Class representing a section in the memo structure."""
    
    def __init__(self, name: str, level: int, content: str = "", parent=None):
        self.name = name
        self.level = level
        self.content = content
        self.parent = parent
        self.children = []
    
    def add_child(self, child):
        """Add a child section."""
        self.children.append(child)
        child.parent = self
    
    def get_full_path(self):
        """Get the full path to this section."""
        if self.parent is None or self.parent.name == "ROOT":
            return self.name
        return f"{self.parent.get_full_path()}.{self.name}"
    
    def get_markdown(self, include_children=True) -> str:
        """Convert this section to markdown."""
        result = []
        
        # Add the section header
        if self.level > 0:  # Don't add header for root
            result.append(f"{'#' * self.level} {self.name}\n")
        
        # Add the content
        if self.content.strip():
            result.append(f"{self.content.strip()}\n")
        
        # Add children
        if include_children:
            for child in self.children:
                result.append(child.get_markdown())
        
        return "\n".join(result)

class StructuredMemo:
    """Class for handling a structured memo file."""
    
    def __init__(self, memo_path: str):
        self.memo_path = memo_path
        self.root = MemoSection("ROOT", 0)
        self.section_map = {"ROOT": self.root}
        
        # Initialize with default structure if file doesn't exist
        if not os.path.exists(memo_path):
            self._create_default_structure()
            self.save()
        else:
            self.load()
    
    def _create_default_structure(self):
        """Create the default memo structure."""
        project_name = os.path.basename(os.path.dirname(self.memo_path))
        
        # Import memo format template
        from desktop_commander.tools.memo_format import get_memo_template
        
        # Create the memo from template
        template = get_memo_template(project_name)
        self.parse_markdown(template)
    
    def load(self):
        """Load the memo from file and parse it into sections."""
        try:
            with open(self.memo_path, "r") as f:
                content = f.read()
            
            self.parse_markdown(content)
        except Exception as e:
            logger.error(f"Error loading memo file: {e}")
            self._create_default_structure()
    
    def save(self) -> bool:
        """Save the memo structure to file."""
        try:
            content = self.root.get_markdown()
            with open(self.memo_path, "w") as f:
                f.write(content)
            return True
        except Exception as e:
            logger.error(f"Error saving memo file: {e}")
            return False
    
    def parse_markdown(self, content: str):
        """Parse markdown content into structured sections."""
        self.root = MemoSection("ROOT", 0)
        self.section_map = {"ROOT": self.root}
        
        lines = content.split("\n")
        current_section = self.root
        current_content = []
        
        for line in lines:
            # Check if this is a header line
            header_match = re.match(r'^(#+)\s+(.+)$', line)
            
            if header_match:
                # Save content of previous section
                if current_content:
                    current_section.content = "\n".join(current_content).strip()
                    current_content = []
                
                # Create new section
                level = len(header_match.group(1))
                name = header_match.group(2).strip()
                
                # Find parent (section with level one higher in hierarchy)
                parent = current_section
                while parent.level >= level and parent.parent is not None:
                    parent = parent.parent
                
                # Create and add the new section
                new_section = MemoSection(name, level)
                parent.add_child(new_section)
                self.section_map[name] = new_section
                
                # Update current section
                current_section = new_section
            else:
                # Add line to current content
                current_content.append(line)
        
        # Save content of the last section
        if current_content:
            current_section.content = "\n".join(current_content).strip()
    
    def get_section(self, section_path: str) -> Optional[MemoSection]:
        """Get a section by its path."""
        if not section_path:
            return self.root
            
        parts = section_path.split(".")
        current = self.root
        
        for part in parts:
            found = False
            for child in current.children:
                if child.name == part:
                    current = child
                    found = True
                    break
            
            if not found:
                return None
        
        return current
    
    def add_section(self, name: str, level: int, content: str = "", parent_path: str = "ROOT"):
        """Add a new section to the memo."""
        parent = self.get_section(parent_path)
        if not parent:
            logger.error(f"Parent section not found: {parent_path}")
            return False
        
        section = MemoSection(name, level, content, parent)
        parent.add_child(section)
        self.section_map[name] = section
        return True
    
    def update_section(self, section_path: str, content: str) -> bool:
        """Update the content of a section."""
        section = self.get_section(section_path)
        if not section:
            logger.error(f"Section not found: {section_path}")
            return False
        
        section.content = content
        return self.save()
    
    def add_todo(self, task: str, priority: str = "Medium") -> bool:
        """Add a todo item to the TODO section."""
        todo_section = self.get_section("Action Items.TODO")
        if not todo_section:
            logger.error("TODO section not found")
            return False
        
        # Get existing content and add new task
        content = todo_section.content.strip()
        new_task = f"- [ ] {priority}: {task}"
        
        if content:
            todo_section.content = f"{content}\n{new_task}"
        else:
            todo_section.content = new_task
        
        return self.save()
    
    def complete_todo(self, task_pattern: str) -> bool:
        """Mark a todo item as completed and move it to COMPLETED section."""
        todo_section = self.get_section("Action Items.TODO")
        completed_section = self.get_section("Action Items.COMPLETED")
        
        if not todo_section or not completed_section:
            logger.error("TODO or COMPLETED section not found")
            return False
        
        # Look for the task
        lines = todo_section.content.split("\n")
        new_lines = []
        completed_task = None
        
        for line in lines:
            if task_pattern.lower() in line.lower() and "- [ ]" in line:
                # Found the task to complete
                completed_task = line.replace("- [ ]", "- [x]")
            else:
                new_lines.append(line)
        
        if not completed_task:
            logger.error(f"Task not found: {task_pattern}")
            return False
        
        # Update the TODO section
        todo_section.content = "\n".join(new_lines)
        
        # Add to COMPLETED with date
        today = datetime.now().strftime("%Y-%m-%d")
        completed_content = completed_section.content.strip()
        new_completed = f"- [✓] {today} {completed_task[5:]}"  # Remove "- [ ]"
        
        if completed_content:
            completed_section.content = f"{completed_content}\n{new_completed}"
        else:
            completed_section.content = new_completed
        
        return self.save()
    
    def add_change_log(self, change: str, version: str = None) -> bool:
        """Add an entry to the change log."""
        change_log = self.get_section("Change Log")
        if not change_log:
            logger.error("Change Log section not found")
            return False
        
        # Use today's date if no version provided
        if not version:
            version = datetime.now().strftime("%Y-%m-%d")
        
        # Check if the version section exists
        version_section = None
        for child in change_log.children:
            if child.name == version:
                version_section = child
                break
        
        if not version_section:
            # Create a new version section
            self.add_section(version, 3, parent_path="Change Log")
            # Get the newly created section
            for child in change_log.children:
                if child.name == version:
                    version_section = child
                    break
        
        if not version_section:
            logger.error(f"Failed to create or find version section: {version}")
            return False
        
        # Add the change
        version_content = version_section.content.strip()
        new_change = f"- {change}"
        
        if version_content:
            version_section.content = f"{version_content}\n{new_change}"
        else:
            version_section.content = new_change
        
        return self.save()
    
    def consolidate(self) -> bool:
        """Consolidate the memo for better maintainability."""
        # Limit COMPLETED items to last 10
        completed = self.get_section("Action Items.COMPLETED")
        if completed and completed.content:
            lines = completed.content.split("\n")
            if len(lines) > 10:
                completed.content = "\n".join(lines[-10:])
        
        # Consolidate change log entries older than 30 days
        # (Future enhancement would implement this logic)
        
        return self.save()


class StructuredMemoTool:
    """Enhanced memo tool for the Desktop Commander MCP Server."""
    
    def __init__(self, root_dir: str = None):
        """Initialize the memo tool."""
        self.root_dir = root_dir or os.path.expanduser("~")
        # Calculate memo path relative to the current module
        module_dir = os.path.dirname(os.path.abspath(__file__))
        project_dir = os.path.dirname(os.path.dirname(os.path.dirname(module_dir)))
        self.memo_path = os.path.join(project_dir, "claude_memo.md")
        self.memo = StructuredMemo(self.memo_path)
    
    def read_memo(self, section: str = None) -> str:
        """Read the entire memo or a specific section."""
        try:
            if section:
                memo_section = self.memo.get_section(section)
                if not memo_section:
                    return f"Section not found: {section}"
                return memo_section.get_markdown()
            else:
                return self.memo.root.get_markdown()
        except Exception as e:
            logger.error(f"Error reading memo: {e}")
            return f"Error reading memo: {e}"
    
    def update_memo_section(self, section: str, content: str) -> str:
        """Update a specific section of the memo."""
        try:
            if self.memo.update_section(section, content):
                return f"Successfully updated section: {section}"
            return f"Failed to update section: {section}"
        except Exception as e:
            logger.error(f"Error updating memo section: {e}")
            return f"Error updating memo section: {e}"
    
    def add_todo(self, task: str, priority: str = "Medium") -> str:
        """Add a new TODO item with priority."""
        try:
            if priority not in ["High", "Medium", "Low"]:
                priority = "Medium"
                
            if self.memo.add_todo(task, priority):
                return f"Successfully added TODO: {priority}: {task}"
            return f"Failed to add TODO: {task}"
        except Exception as e:
            logger.error(f"Error adding TODO: {e}")
            return f"Error adding TODO: {e}"
    
    def complete_todo(self, task_pattern: str) -> str:
        """Mark a TODO item as completed and move to COMPLETED section."""
        try:
            if self.memo.complete_todo(task_pattern):
                return f"Successfully completed task matching: {task_pattern}"
            return f"Failed to complete task. Task not found: {task_pattern}"
        except Exception as e:
            logger.error(f"Error completing TODO: {e}")
            return f"Error completing TODO: {e}"
    
    def add_change_log(self, change: str, version: str = None) -> str:
        """Add a change log entry."""
        try:
            if self.memo.add_change_log(change, version):
                version = version or datetime.now().strftime("%Y-%m-%d")
                return f"Successfully added change log entry to {version}: {change}"
            return f"Failed to add change log entry: {change}"
        except Exception as e:
            logger.error(f"Error adding change log: {e}")
            return f"Error adding change log: {e}"
    
    def write_memo(self, content: str) -> str:
        """Legacy method to write the entire memo (preserved for compatibility)."""
        try:
            # Parse the new content and replace the memo
            self.memo.parse_markdown(content)
            if self.memo.save():
                return "Memo successfully updated"
            return "Failed to update memo"
        except Exception as e:
            logger.error(f"Error writing memo: {e}")
            return f"Error writing memo: {e}"
    
    def append_memo(self, content: str) -> str:
        """Legacy method to append to the memo (preserved for compatibility)."""
        try:
            # For backward compatibility, try to parse the section
            lines = content.strip().split("\n")
            if lines and lines[0].startswith("##"):
                # This looks like a section, try to extract section name
                section_match = re.match(r'^(#+)\s+(.+)$', lines[0])
                if section_match:
                    section_name = section_match.group(2).strip()
                    section_content = "\n".join(lines[1:]).strip()
                    
                    # Try to add this as a change log entry
                    return self.add_change_log(f"**{section_name}**: {section_content}")
            
            # Default fallback: just add as a change log entry
            if self.memo.add_change_log(content):
                return "Content successfully added to change log"
            return "Failed to add content to memo"
        except Exception as e:
            logger.error(f"Error appending to memo: {e}")
            return f"Error appending to memo: {e}"
    
    def consolidate_memo(self) -> str:
        """Consolidate the memo for better maintainability."""
        try:
            if self.memo.consolidate():
                return "Successfully consolidated memo"
            return "Failed to consolidate memo"
        except Exception as e:
            logger.error(f"Error consolidating memo: {e}")
            return f"Error consolidating memo: {e}"


def register_tools(mcp):
    """Register enhanced memo tools with the MCP server."""
    
    # Create a single instance of the memo tool
    memo_tool = StructuredMemoTool()
    
    @mcp.tool()
    def read_memo(section: str = None) -> str:
        """
        Read the Claude memory file or a specific section.
        
        Args:
            section: Optional section name to read (e.g., "Action Items.TODO")
        """
        return memo_tool.read_memo(section)
    
    @mcp.tool()
    def update_memo_section(section: str, content: str) -> str:
        """
        Update a specific section of the memo.
        
        Args:
            section: Section path using dot notation (e.g., "Action Items.TODO")
            content: New content for the section
        """
        return memo_tool.update_memo_section(section, content)
    
    @mcp.tool()
    def add_todo(task: str, priority: str = "Medium") -> str:
        """
        Add a new TODO item with priority.
        
        Args:
            task: Task description
            priority: Priority level (High, Medium, Low)
        """
        return memo_tool.add_todo(task, priority)
    
    @mcp.tool()
    def complete_todo(task_pattern: str) -> str:
        """
        Mark a TODO item as completed and move to COMPLETED section.
        
        Args:
            task_pattern: Pattern to match the task
        """
        return memo_tool.complete_todo(task_pattern)
    
    @mcp.tool()
    def add_change_log(change: str, version: str = None) -> str:
        """
        Add a change log entry.
        
        Args:
            change: Change description
            version: Optional version or date (defaults to today)
        """
        return memo_tool.add_change_log(change, version)
    
    @mcp.tool()
    def consolidate_memo() -> str:
        """
        Consolidate the memo for better maintainability.
        Limits completed items and consolidates old change log entries.
        """
        return memo_tool.consolidate_memo()
    
    # Legacy methods for backward compatibility
    @mcp.tool()
    def write_memo(content: str) -> str:
        """
        Update the Claude memory file with new content.
        """
        return memo_tool.write_memo(content)
    
    @mcp.tool()
    def append_memo(content: str) -> str:
        """
        Append content to the Claude memory file.
        """
        return memo_tool.append_memo(content)
