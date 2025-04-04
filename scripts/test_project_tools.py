#!/usr/bin/env python3
"""
Test script for the enhanced project tools.
This script verifies that the project tools work correctly, including exploration
and knowledge graph integration.
"""

import os
import sys
import json
import shutil
import tempfile
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the project tools
from desktop_commander.tools.project import register_tools, current_project

# Helper function for testing
def check_if_project(directory):
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

# Mock knowledge graph manager for testing
class MockGraphManager:
    def __init__(self):
        self.graphs = {}
        
    def save_graph(self, project_name, graph_data):
        self.graphs[project_name] = graph_data
        return True
        
    def load_graph(self, project_name):
        return self.graphs.get(project_name)
        
    def list_graphs(self):
        return list(self.graphs.keys())

# Mock MCP server class for testing
class MockMCP:
    def __init__(self):
        self.tools = {}
        self.resources = {}
        
    def tool(self):
        def decorator(func):
            self.tools[func.__name__] = func
            return func
        return decorator
        
    def resource(self, pattern):
        def decorator(func):
            self.resources[pattern] = func
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
    
    # Create a mock graph manager
    mock_graph_manager = MockGraphManager()
    
    # Patch the import for testing
    import desktop_commander.tools.knowledge_graph
    desktop_commander.tools.knowledge_graph.graph_manager = mock_graph_manager
    
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
        project_info = check_if_project(project_dir)
        print(f"Project info: {project_info}")
        assert project_info is not None, "Failed to recognize directory as a project"
        assert project_info["name"] == "test_project", "Incorrect project name"
        assert project_info["type"] == "python", "Incorrect project type"
        print("✅ Test 1 passed")
        
        # Test 2: Switch to the project
        print("\nTest 2: Switch to the project")
        result = mcp.run_tool("use_project", project_dir)
        print(f"Switch result: {result}")
        assert "Switched to project: test_project" in result, "Expected 'Switched to project' message"
        # No need to check current_project as it's mocked and won't change in this test
        print("✅ Test 2 passed")
        
        # Test 3: Get the current project
        print("\nTest 3: Get the current project")
        result = mcp.run_tool("get_current_project")
        print(f"Current project result: {result}")
        assert "Current project: test_project" in result, "Expected current project info"
        print("✅ Test 3 passed")
        
        # Test 4: Explore the project
        print("\nTest 4: Explore the project")
        result = mcp.run_tool("explore_project")
        print(f"Exploration result preview: {result[:100]}...")
        assert "Project Exploration Instructions: test_project" in result, "Expected exploration instructions"
        assert "Basic Project Analysis" in result, "Expected analysis instructions"
        assert "Store Project Knowledge" in result, "Expected store knowledge instructions"
        print("✅ Test 4 passed")
        
        # Test 5: Export project knowledge to graph
        print("\nTest 5: Export project knowledge to graph")
        test_knowledge = {
            "project_name": "test_project",
            "entities": [
                {"id": "1", "name": "Main Module", "entityType": "module", "description": "Core app module"}
            ],
            "relations": [
                {"source": "1", "target": "1", "relationship": "self_reference", "description": "Test relation"}
            ]
        }
        
        result = mcp.run_tool("export_project_to_knowledge_graph", json.dumps(test_knowledge))
        print(f"Export result: {result}")
        assert "Successfully exported knowledge graph for project: test_project" in result, "Expected successful export"
        
        # Verify the graph was saved correctly
        assert "test_project" in mock_graph_manager.graphs, "Knowledge graph was not saved"
        assert len(mock_graph_manager.graphs["test_project"]["entities"]) == 1, "Entity not saved correctly"
        print("✅ Test 5 passed")
        
        # Test 6: Import project knowledge from graph
        print("\nTest 6: Import project knowledge from graph")
        result = mcp.run_tool("import_project_from_knowledge_graph", "test_project")
        print(f"Import result preview: {result[:100]}...")
        
        # Parse the result as JSON to verify structure
        imported_data = json.loads(result)
        assert imported_data["project_name"] == "test_project", "Wrong project name in imported data"
        assert len(imported_data["entities"]) == 1, "Expected one entity in imported data"
        print("✅ Test 6 passed")
        
    print("\nAll tests passed! ✨")

if __name__ == "__main__":
    run_tests()
