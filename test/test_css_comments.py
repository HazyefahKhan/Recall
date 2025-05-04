import re

def process_css_comments(code):
    """Simulate the CSS comment processing from the converter.py file"""
    processed_code = ""
    pos = 0
    
    for match in re.finditer(r'/\*(.*?)\*/', code, flags=re.DOTALL):
        start, end = match.span()
        comment_content = match.group(1)
        
        # Add the code before the comment
        processed_code += code[pos:start]
        
        # For testing, we'll just wrap the comment content in a special marker
        processed_code += f'COMMENT[{comment_content}]'
        
        # Update the position
        pos = end
    
    # Add any remaining code after the last comment
    processed_code += code[pos:]
    return processed_code

def test_css_comment_processing():
    """Test our new CSS comment processing approach"""
    # Test cases
    test_cases = [
        {
            "input": "width: 50%;            /* 50 % of the viewport */",
            "expected": "width: 50%;            COMMENT[ 50 % of the viewport ]"
        },
        {
            "input": "background: coral;     /* no width declared here */",
            "expected": "background: coral;     COMMENT[ no width declared here ]"
        },
        {
            "input": "/* comment with * asterisk inside */",
            "expected": "COMMENT[ comment with * asterisk inside ]"
        },
        {
            "input": "/* comment with ** multiple asterisks inside */",
            "expected": "COMMENT[ comment with ** multiple asterisks inside ]"
        },
        {
            "input": "/* nested /* comment structure */ remaining text",
            "expected": "COMMENT[ nested /* comment structure ] remaining text"
        },
        {
            "input": "/* multi-line\n * comment\n * with asterisks\n */",
            "expected": "COMMENT[ multi-line\n * comment\n * with asterisks\n ]"
        },
        {
            "input": ".parent { width: 50%; /* 50 % of the viewport */ margin: 0 auto; } .child { background: coral; /* no width declared here */ }",
            "expected": ".parent { width: 50%; COMMENT[ 50 % of the viewport ] margin: 0 auto; } .child { background: coral; COMMENT[ no width declared here ] }"
        }
    ]
    
    for i, test_case in enumerate(test_cases):
        input_text = test_case["input"]
        expected = test_case["expected"]
        
        actual = process_css_comments(input_text)
        assert actual == expected, f"Test case {i+1} failed: Expected '{expected}', got '{actual}'"
        print(f"Test case {i+1} passed!")
    
    print("All CSS comment processing tests passed!")

if __name__ == "__main__":
    test_css_comment_processing() 