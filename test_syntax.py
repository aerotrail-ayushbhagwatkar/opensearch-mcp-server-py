#!/usr/bin/env python3
"""Test script to validate FastMCP implementation syntax and structure."""

import ast
import sys
import os

def test_syntax(file_path):
    """Test if a Python file has valid syntax."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        ast.parse(content)
        print(f"✓ {file_path} - Syntax is valid")
        return True
    except SyntaxError as e:
        print(f"✗ {file_path} - Syntax error: {e}")
        return False
    except Exception as e:
        print(f"✗ {file_path} - Error: {e}")
        return False

def main():
    """Run syntax tests on key files."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    src_dir = os.path.join(base_dir, 'src')
    
    test_files = [
        'src/mcp_server_opensearch/__init__.py',
        'src/mcp_server_opensearch/fastmcp_server.py',
        'src/mcp_server_opensearch/legacy_main.py',
        'tests/mcp_server_opensearch/test_fastmcp_server.py',
    ]
    
    print("Testing FastMCP implementation syntax...")
    print("=" * 50)
    
    all_passed = True
    for file_path in test_files:
        if os.path.exists(file_path):
            if not test_syntax(file_path):
                all_passed = False
        else:
            print(f"⚠ {file_path} - File not found")
    
    print("=" * 50)
    if all_passed:
        print("✓ All syntax tests passed!")
    else:
        print("✗ Some tests failed!")
    
    return 0 if all_passed else 1

if __name__ == '__main__':
    sys.exit(main())
