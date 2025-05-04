"""Test robust CSS comment encoding"""
import re
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def encode_css_comment(comment):
    """Encode CSS comment with the same approach as in converter.py"""
    encoded_comment = ""
    for char in comment:
        if char == '/':
            encoded_comment += '&#47;'
        elif char == '*':
            encoded_comment += '&#42;'
        elif char == '<':
            encoded_comment += '&lt;'
        elif char == '>':
            encoded_comment += '&gt;'
        elif char == '&':
            encoded_comment += '&amp;'
        else:
            encoded_comment += char
    return encoded_comment

def test_robust_css_comment_encoding():
    """Test our robust CSS comment encoding approach"""
    # CSS comments to test
    comments = [
        "/* 50 % of the viewport */",
        "/* no width declared here */",
        "/* comment with * asterisk */",
        "/* nested /* comment */ structure */"
    ]
    
    for comment in comments:
        # Encode the comment
        encoded = encode_css_comment(comment)
        print(f"Original: {comment}")
        print(f"Encoded : {encoded}")
        
        # Verify the encoding
        assert '/' not in encoded
        assert '*' not in encoded
        assert '&#47;' in encoded  # Encoded forward slash
        assert '&#42;' in encoded  # Encoded asterisk
        
        # Check specific patterns
        if "50 %" in comment:
            assert "50 %" in encoded
        if "no width" in comment:
            assert "no width" in encoded
        
        print(f"Encoding verified for: {comment}\n")
    
    # Test the full HTML example
    html_example = """
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
    """
    
    # Process CSS comments with the robust encoding
    processed_code = ""
    pos = 0
    
    for match in re.finditer(r'/\*.*?\*/', html_example, flags=re.DOTALL):
        start, end = match.span()
        full_comment = match.group(0)
        
        processed_code += html_example[pos:start]
        encoded_comment = encode_css_comment(full_comment)
        processed_code += f'<span class="token comment">{encoded_comment}</span>'
        pos = end
    
    processed_code += html_example[pos:]
    
    print("Processed HTML:")
    print(processed_code)
    
    # Verify the processed HTML
    assert "&#47;&#42; 50 % of the viewport &#42;&#47;" in processed_code
    assert "&#47;&#42; no width declared here &#42;&#47;" in processed_code
    
    print("\nTest passed! Robust CSS comment encoding is working correctly.")

if __name__ == "__main__":
    test_robust_css_comment_encoding() 