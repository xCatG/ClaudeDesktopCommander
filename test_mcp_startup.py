#!/usr/bin/env python3
"""
Quick test script to verify that the MCP server initializes correctly
after removing the old memo tools.
"""

import os
import sys
import importlib
import traceback

def test_import_modules():
    """Test importing all required modules."""
    modules_to_test = [
        "desktop_commander.mcp_server",
        "desktop_commander.mcp_implementation",
        "desktop_commander.tools.filesystem",
        "desktop_commander.tools.process",
        "desktop_commander.tools.terminal",
        "desktop_commander.tools.project"
    ]
    
    for module_name in modules_to_test:
        try:
            print(f"Testing import of {module_name}...")
            module = importlib.import_module(module_name)
            print(f"✅ Successfully imported {module_name}")
        except Exception as e:
            print(f"❌ Error importing {module_name}: {e}")
            traceback.print_exc()
            return False
    
    return True

def test_mcp_initialization():
    """Test MCP server initialization."""
    try:
        print("Testing MCP initialization...")
        # Import without executing run()
        from desktop_commander.mcp_implementation import mcp
        print(f"✅ Successfully initialized MCP server: {mcp}")
        return True
    except Exception as e:
        print(f"❌ Error initializing MCP server: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Add project root to sys.path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, script_dir)
    
    # Run tests
    import_ok = test_import_modules()
    if not import_ok:
        print("❌ Module import tests failed!")
        sys.exit(1)
    
    mcp_ok = test_mcp_initialization()
    if not mcp_ok:
        print("❌ MCP initialization test failed!")
        sys.exit(1)
    
    print("✅ All tests passed! The MCP server should start correctly.")