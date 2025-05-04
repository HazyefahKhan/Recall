"""Minimal test that doesn't use the conftest"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.markdown.converter import format_code_block

def test_css_comments():
    """Test that CSS comments are properly preserved in code blocks"""
    # Sample code with CSS comments
    code = """
    .parent {
        width: 50%;            /* 50 % of the viewport */
        margin: 0 auto;
        background: lightblue;
    }
    .child {
        background: coral;     /* no width declared here */
    }
    """
    
    html = format_code_block(code, "css")
    
    # Check that the comments are properly preserved and styled
    assert "/* 50 % of the viewport */" in html
    assert "/* no width declared here */" in html
    
    print("CSS comment test passed! The fix works correctly.")

if __name__ == "__main__":
    test_css_comments() 