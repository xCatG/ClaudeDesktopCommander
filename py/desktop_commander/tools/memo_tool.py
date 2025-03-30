#!/usr/bin/env python3
"""
Tool for Claude to manage its memory file.
This allows Claude to maintain context about projects between conversations.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)

class MemoTool:
    """
    Tool for Claude to read and update its memory file.
    """
    
    def __init__(self, root_dir: str = None):
        """
        Initialize the memo tool.
        
        Args:
            root_dir: Optional root directory to limit file access
        """
        self.root_dir = root_dir or os.path.expanduser("~")
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
    
    def write_memo(self, content: str) -> Dict[str, Any]:
        """
        Write to the Claude memo file.
        
        Args:
            content: New content for the memo file
            
        Returns:
            Result status
        """
        try:
            with open(self.memo_path, "w") as f:
                f.write(content)
                
            return {
                "success": True,
                "message": "Memo successfully updated"
            }
        except Exception as e:
            logger.error(f"Error writing to memo file: {e}")
            return {
                "success": False,
                "message": f"Error writing to memo file: {e}"
            }
    
    def append_memo(self, content: str) -> Dict[str, Any]:
        """
        Append to the Claude memo file.
        
        Args:
            content: Content to append to the memo file
            
        Returns:
            Result status
        """
        try:
            current_content = self.read_memo()
            updated_content = current_content + "\n\n" + content
            
            return self.write_memo(updated_content)
        except Exception as e:
            logger.error(f"Error appending to memo file: {e}")
            return {
                "success": False,
                "message": f"Error appending to memo file: {e}"
            }

# Register tool functions
def get_tool_functions() -> Dict[str, Dict[str, Any]]:
    """
    Get the tool functions for the MCP server.
    
    Returns:
        Dict of tool functions with their definitions
    """
    memo_tool = MemoTool()
    
    return {
        "read_memo": {
            "description": "Read the Claude memory file to recall information about projects.",
            "parameters": {},
            "function": memo_tool.read_memo
        },
        "write_memo": {
            "description": "Update the Claude memory file with new content.",
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "New content for the memo file"
                    }
                },
                "required": ["content"]
            },
            "function": memo_tool.write_memo
        },
        "append_memo": {
            "description": "Append content to the Claude memory file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "Content to append to the memo file"
                    }
                },
                "required": ["content"]
            },
            "function": memo_tool.append_memo
        }
    }
