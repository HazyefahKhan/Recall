"""Simple test of CSS comment encoding"""

def encode_css_comment(comment):
    """Encode CSS comment with HTML entities for critical characters"""
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

def test_simple_encoding():
    """Test the essential comment encoding"""
    comment1 = "/* 50 % of the viewport */"
    comment2 = "/* no width declared here */"
    
    encoded1 = encode_css_comment(comment1)
    encoded2 = encode_css_comment(comment2)
    
    print(f"Original 1: {comment1}")
    print(f"Encoded  1: {encoded1}")
    print(f"Original 2: {comment2}")
    print(f"Encoded  2: {encoded2}")
    
    # Verify encodings
    assert encoded1 == "&#47;&#42; 50 % of the viewport &#42;&#47;"
    assert encoded2 == "&#47;&#42; no width declared here &#42;&#47;"
    
    print("\nEncoding test passed!")

if __name__ == "__main__":
    test_simple_encoding() 