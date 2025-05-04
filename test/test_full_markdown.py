"""Test full markdown processing with CSS comments"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the converter directly to avoid mocks
from src.markdown.converter import format_code_block

def test_html_with_css_comments():
    """Test that HTML with CSS comments is properly processed"""
    # HTML code with CSS comments from the user's example
    html_code = """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <title>Non-Inherited Width Demo</title>
    <style>
      .parent {
        width: 50%;            /* 50 % of the viewport */
        margin: 0 auto;
        background: lightblue;
      }
      .child {
        background: coral;     /* no width declared here */
      }
    </style>
  </head>
  <body>
    <div class="parent">
      <div class="child">
        This nested element expands to its content's natural width because
        <code>width</code> is not inherited from <code>.parent</code>.
      </div>
    </div>
  </body>
</html>"""
    
    # Process the code block
    processed_html = format_code_block(html_code, "html")
    
    # Print output for inspection
    print(processed_html)
    
    # Test that CSS comments are properly preserved
    assert "/* 50 % of the viewport */" in processed_html
    assert "/* no width declared here */" in processed_html
    
    print("\nTest passed! CSS comments in HTML are preserved correctly.")

if __name__ == "__main__":
    test_html_with_css_comments() 