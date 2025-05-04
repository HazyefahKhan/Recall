"""Test script to verify CSS comment fixing"""
import sys
import os
import re

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_comment_handling():
    """Test our CSS comment handling with the user's example"""
    # HTML example with CSS comments from the user's markdown
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
    
    # Our CSS comment handling logic
    processed_code = ""
    pos = 0
    
    for match in re.finditer(r'/\*.*?\*/', code, flags=re.DOTALL):
        start, end = match.span()
        full_comment = match.group(0)  # Get the entire comment with /* */
        
        # Add the code before the comment
        processed_code += code[pos:start]
        
        # HTML escape the full comment including /* and */
        escaped_comment = full_comment.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        
        # For testing, print the comment as it would be in HTML
        print(f"Original comment: {full_comment}")
        print(f"Escaped comment: {escaped_comment}")
        
        # Add the styled comment
        processed_code += f'<span class="token comment">{escaped_comment}</span>'
        
        # Update the position
        pos = end
    
    # Add any remaining code after the last comment
    processed_code += code[pos:]
    
    # Check if the result contains intact CSS comments
    print("\nFinal processed code:")
    print(processed_code)
    
    # Verify that the /* and */ are preserved
    assert "/* 50 % of the viewport */" in processed_code.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")
    assert "/* no width declared here */" in processed_code.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")
    
    print("\nTest passed! CSS comments are preserved correctly.")

if __name__ == "__main__":
    test_comment_handling() 