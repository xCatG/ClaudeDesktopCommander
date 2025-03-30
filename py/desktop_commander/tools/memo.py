"""
Memo tools for the Desktop Commander MCP Server.
Allows Claude to maintain context across conversations via a memory file.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)

class MemoTool:
    """
    Class for reading and updating the Claude memory file.
    """
    
    def __init__(self, root_dir: str = None):
        """
        Initialize the memo tool.
        
        Args:
            root_dir: Optional root directory to limit file access
        """
        self.root_dir = root_dir or os.path.expanduser("~")
        # Go up two directory levels to reach the project root
        self.memo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__)))), "claude_memo.md")
    
    def read_memo(self) -> str:
        """
        Read the Claude memo file.
        
        Returns:
            Content of the memo file
        """
        try:
            if not os.path.exists(self.memo_path):
                # Create empty memo file if it doesn't exist
                with open(self.memo_path, "w") as f:
                    f.write("# Claude Memory File\n\nNo memories stored yet.")
                
            with open(self.memo_path, "r") as f:
                content = f.read()
                
            return content
        except Exception as e:
            logger.error(f"Error reading memo file: {e}")
            return f"Error reading memo file: {e}"
    
    def write_memo(self, content: str) -> str:
        """
        Write to the Claude memo file.
        
        Args:
            content: New content for the memo file
            
        Returns:
            Success message
        """
        try:
            with open(self.memo_path, "w") as f:
                f.write(content)
                
            return "Memo successfully updated"
        except Exception as e:
            logger.error(f"Error writing to memo file: {e}")
            return f"Error writing to memo file: {e}"
    
    def append_memo(self, content: str) -> str:
        """
        Append to the Claude memo file.
        
        Args:
            content: Content to append to the memo file
            
        Returns:
            Success message
        """
        try:
            current_content = self.read_memo()
            updated_content = current_content + "\n\n" + content
            
            with open(self.memo_path, "w") as f:
                f.write(updated_content)
                
            return "Content successfully appended to memo"
        except Exception as e:
            logger.error(f"Error appending to memo file: {e}")
            return f"Error appending to memo file: {e}"

def register_tools(mcp):
    """Register memo tools with the MCP server."""
    
    # Create a single instance of the memo tool
    memo_tool = MemoTool()
    
    @mcp.tool()
    def read_memo() -> str:
        """
        Read the Claude memory file to recall information about projects.
        """
        return memo_tool.read_memo()
    
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
