"""Comprehensive test of our complete solution for CSS comments in code blocks"""
import re

def encode_with_html_entities(text):
    """Encode text with HTML entities for critical characters"""
    encoded = ""
    for char in text:
        if char == '/':
            encoded += '&#47;'
        elif char == '*':
            encoded += '&#42;'
        elif char == '<':
            encoded += '&lt;'
        elif char == '>':
            encoded += '&gt;'
        elif char == '&':
            encoded += '&amp;'
        else:
            encoded += char
    return encoded

def process_css_comments(code):
    """Process CSS comments with robust encoding"""
    processed_code = ""
    pos = 0
    
    # Use a regex that identifies CSS comments precisely
    for match in re.finditer(r'/\*.*?\*/', code, flags=re.DOTALL):
        start, end = match.span()
        full_comment = match.group(0)  # Get the entire comment with /* */
        
        # Add the code before the comment
        processed_code += code[pos:start]
        
        # Encode comment with HTML entities
        encoded_comment = encode_with_html_entities(full_comment)
        
        # Add the styled comment with robust encoding
        processed_code += f'<span class="token comment">{encoded_comment}</span>'
        
        # Update the position
        pos = end
    
    # Add any remaining code after the last comment
    processed_code += code[pos:]
    return processed_code

def test_complete_solution():
    """Test our complete solution with the example from the user"""
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
    
    # Process CSS comments
    processed_html = process_css_comments(html_code)
    
    # Print processed HTML for verification
    print("Processed HTML (trimmed for readability):")
    for line in processed_html.split('\n'):
        if "comment" in line:
            print(line)
    
    # These are the key assertions to verify our approach:
    # 1. The original comments should not be present (they've been replaced)
    assert "/* 50 % of the viewport */" not in processed_html
    assert "/* no width declared here */" not in processed_html
    
    # 2. The encoded comments should be present
    comment1 = encode_with_html_entities("/* 50 % of the viewport */")
    comment2 = encode_with_html_entities("/* no width declared here */")
    
    assert comment1 in processed_html
    assert comment2 in processed_html
    
    # 3. The comments should be wrapped in styled spans
    assert f'<span class="token comment">{comment1}</span>' in processed_html
    assert f'<span class="token comment">{comment2}</span>' in processed_html
    
    # Print encoded comments for verification
    print("\nEncoded Comments:")
    print(f"Original: /* 50 % of the viewport */")
    print(f"Encoded : {comment1}")
    print(f"Original: /* no width declared here */")
    print(f"Encoded : {comment2}")
    
    print("\nTest passed! CSS comments are robustly encoded and preserved.")

if __name__ == "__main__":
    test_complete_solution() 