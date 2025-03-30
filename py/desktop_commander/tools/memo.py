"""
Enhanced memo tools for the Desktop Commander MCP Server.
Allows Claude to maintain structured context across conversations via a memory file.

This module provides both legacy memo functions and enhanced structured memo tools
that support section-based updates, todos, and change logs.
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Import the structured memo implementation
from desktop_commander.tools.structured_memo import StructuredMemoTool

logger = logging.getLogger(__name__)

def register_tools(mcp):
    """Register memo tools with the MCP server."""
    
    # Create a single instance of the structured memo tool
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
