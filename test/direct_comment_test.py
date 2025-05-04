"""Direct test of CSS comment regex handling"""
import re

def process_css_comments(code):
    """Process CSS comments with our new approach"""
    processed_code = ""
    pos = 0
    
    # Use the same regex pattern we implemented in the converter.py file
    for match in re.finditer(r'/\*.*?\*/', code, flags=re.DOTALL):
        start, end = match.span()
        full_comment = match.group(0)  # Get the entire comment with /* */
        
        # Add the code before the comment
        processed_code += code[pos:start]
        
        # For testing, just mark the comment
        processed_code += f'COMMENT[{full_comment}]'
        
        # Update the position
        pos = end
    
    # Add any remaining code after the last comment
    processed_code += code[pos:]
    return processed_code

def test_html_code_with_css_comments():
    """Test our CSS comment regex with HTML containing CSS comments"""
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
        This nested element expands to its content's natural width.
      </div>
    </div>
  </body>
</html>"""
    
    # Process the HTML code
    processed_html = process_css_comments(html_code)
    
    # Print the processed HTML for verification
    print("Processed HTML:")
    print(processed_html)
    
    # Check that both CSS comments are properly preserved
    assert "COMMENT[/* 50 % of the viewport */]" in processed_html
    assert "COMMENT[/* no width declared here */]" in processed_html
    
    print("\nTest passed! CSS comments are properly processed with our regex.")

if __name__ == "__main__":
    test_html_code_with_css_comments() 