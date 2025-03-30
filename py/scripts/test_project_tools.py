#!/usr/bin/env python3
"""
Test script for the enhanced project tools.
This script verifies that the project exploration, memo creation, and file indexing work as expected.
"""

import os
import sys
import shutil
import tempfile
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import the project tools
from desktop_commander.tools.project import register_tools, current_project, _check_if_project, _load_memo

# Mock MCP server class for testing
class MockMCP:
    def __init__(self):
        self.tools = {}
        
    def tool(self):
        def decorator(func):
            self.tools[func.__name__] = func
            return func
        return decorator
    
    def run_tool(self, name, *args, **kwargs):
        if name in self.tools:
            return self.tools[name](*args, **kwargs)
        raise ValueError(f"Tool not found: {name}")

def run_tests():
    print("Running project tools tests...")
    
    # Create a mock MCP server
    mcp = MockMCP()
    
    # Register tools with the mock server
    register_tools(mcp)
    
    # Create a temporary test project
    with tempfile.TemporaryDirectory() as temp_dir:
        # Setup a test project structure
        project_dir = os.path.join(temp_dir, "test_project")
        os.makedirs(project_dir)
        os.makedirs(os.path.join(project_dir, "src"))
        os.makedirs(os.path.join(project_dir, "tests"))
        
        # Create some test files
        with open(os.path.join(project_dir, "README.md"), "w") as f:
            f.write("# Test Project\n\nA test project for verifying project tools.")
            
        with open(os.path.join(project_dir, "setup.py"), "w") as f:
            f.write("from setuptools import setup\n\nsetup(name='test_project')")
            
        with open(os.path.join(project_dir, "src", "main.py"), "w") as f:
            f.write("def main():\n    print('Hello, world!')")
        
        # Test 1: Check if directory is recognized as a project
        print("\nTest 1: Check if directory is recognized as a project")
        project_info = _check_if_project(project_dir)
        print(f"Project info: {project_info}")
        assert project_info is not None, "Failed to recognize directory as a project"
        assert project_info["name"] == "test_project", "Incorrect project name"
        assert project_info["type"] == "python", "Incorrect project type"
        print("✅ Test 1 passed")
        
        # Test 2: Switch to the project
        print("\nTest 2: Switch to the project")
        result = mcp.run_tool("use_project", project_dir)
        print(f"Switch result: {result}")
        assert "No project memo found" in result, "Expected 'No project memo found' message"
        assert current_project["path"] == project_dir, "Failed to set current project"
        print("✅ Test 2 passed")
        
        # Test 3: Explore the project
        print("\nTest 3: Explore the project")
        result = mcp.run_tool("explore_project")
        print(f"Exploration result: {result}")
        assert "Project Analysis: test_project" in result, "Expected project analysis"
        assert "Python" in result, "Expected to detect Python project"
        print("✅ Test 3 passed")
        
        # Test 4: Check if memo was created
        print("\nTest 4: Check if memo was created")
        memo_path = os.path.join(project_dir, "claude_memo.md")
        assert os.path.exists(memo_path), "Memo file not created"
        memo_content = _load_memo(memo_path)
        print(f"Memo content: {memo_content[:100]}...")
        assert "# Project: test_project" in memo_content, "Expected project name in memo"
        print("✅ Test 4 passed")
        
        # Test 5: Create a new memo with template
        print("\nTest 5: Create a new memo with template")
        result = mcp.run_tool("create_project_memo", "# Custom Content")
        print(f"Create memo result: {result}")
        assert "with template and documentation" in result, "Expected template usage"
        memo_content = _load_memo(memo_path)
        assert "## Usage Guide" in memo_content, "Expected usage guide in memo"
        print("✅ Test 5 passed")
        
        # Test 6: Index a file
        print("\nTest 6: Index a file")
        file_path = "src/main.py"
        description = "Main entry point for the application"
        category = "Core"
        result = mcp.run_tool("index_file", file_path, description, category)
        print(f"Index file result: {result}")
        assert "Successfully indexed file" in result, "Expected successful indexing"
        memo_content = _load_memo(memo_path)
        assert "## File Index" in memo_content, "Expected file index section"
        assert file_path in memo_content, "Expected file path in memo"
        assert description in memo_content, "Expected description in memo"
        print("✅ Test 6 passed")
        
    print("\nAll tests passed! ✨")

if __name__ == "__main__":
    run_tests()
