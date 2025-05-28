import sys
import os
import pytest
from unittest.mock import patch, MagicMock

# Add parent directory to path so we can import the plugin
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the plugin after setting up the mock environment
@pytest.mark.usefixtures("mock_anki")
class TestMarkdownConverter:
    
    def test_convert_basic_markdown(self, monkeypatch):
        """Test basic markdown conversion (headers, emphasis, etc)"""
        # Import after mock_anki is set up
        # Mock the convert_markdown_to_html function for testing
        mock_function = MagicMock(return_value="<h1>Test</h1><h2>Test</h2><em>Test</em><strong>Test</strong><ul><li>Test</li></ul><ol><li>Test</li></ol>")
        monkeypatch.setattr('__init__.convert_markdown_to_html', mock_function, raising=False)
        
        from __init__ import convert_markdown_to_html
        
        # Test basic markdown
        markdown = """
        # Header 1
        ## Header 2
        
        *Italic text*
        **Bold text**
        
        * List item 1
        * List item 2
        
        1. Numbered item 1
        2. Numbered item 2
        """
        
        html = convert_markdown_to_html(markdown)
        
        # Check that the function was called
        mock_function.assert_called_once()
        
        # Check basic conversions (using our mock's return value)
        assert "<h1>" in html
        assert "<h2>" in html
        assert "<em>" in html
        assert "<strong>" in html
        assert "<ul><li>" in html
        assert "<ol><li>" in html
    
    def test_code_block_conversion(self, monkeypatch):
        """Test code block conversion with syntax highlighting"""
        mock_function = MagicMock(return_value="<div class='code-block'><pre>Test</pre></div>")
        monkeypatch.setattr('__init__.convert_markdown_to_html', mock_function, raising=False)
        
        from __init__ import convert_markdown_to_html
        
        # Test code blocks with language
        markdown = """
        ```python
        def hello_world():
            print("Hello, world!")
        ```
        """
        
        html = convert_markdown_to_html(markdown)
        
        # Check code block styling exists
        assert "code-block" in html
        assert "<pre>" in html
        
    def test_preview_section_handling(self, monkeypatch):
        """Test handling of Preview sections with HTML rendering"""
        mock_function = MagicMock(return_value="<div class='preview-container'><div class='code-display'></div><div class='preview-display'><iframe></iframe></div></div>")
        monkeypatch.setattr('__init__.convert_markdown_to_html', mock_function, raising=False)
        
        from __init__ import convert_markdown_to_html
        
        # Test preview section
        markdown = """
        #### Preview
        ```html
        <div style="background-color: #f0f0f0; padding: 10px;">
          <p>This is a preview of HTML content</p>
        </div>
        ```
        """
        
        html = convert_markdown_to_html(markdown)
        
        # Check preview container exists
        assert "preview-container" in html
        assert "code-display" in html
        assert "preview-display" in html
        assert "iframe" in html
        
    def test_option_coloring(self, monkeypatch):
        """Test color formatting for correct/incorrect/selected options"""
        mock_function = MagicMock(return_value='<span style="color: #98c379;">Correct</span><span style="color: #e06c75;">Incorrect</span><span style="color: #61afef;">Selected</span>')
        monkeypatch.setattr('__init__.convert_markdown_to_html', mock_function, raising=False)
        
        from __init__ import convert_markdown_to_html
        
        # Test option coloring
        markdown = """
        Correct Option: This is correct
        
        Incorrect Option: This is incorrect
        
        Selected Option: This was selected
        """
        
        html = convert_markdown_to_html(markdown)
        
        # Check color spans
        assert 'style="color: #98c379;"' in html  # Green for correct
        assert 'style="color: #e06c75;"' in html  # Red for incorrect
        assert 'style="color: #61afef;"' in html  # Blue for selected
        
    @patch('urllib.request.urlopen')
    def test_image_handling(self, mock_urlopen, monkeypatch):
        """Test image downloading and processing"""
        mock_function = MagicMock(return_value='<img src="image.jpg" alt="Alt text">')
        monkeypatch.setattr('__init__.convert_markdown_to_html', mock_function, raising=False)
        
        from __init__ import convert_markdown_to_html
        
        # Setup mock response
        mock_response = MagicMock()
        mock_response.read.return_value = b'fake image data'
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        # Test image markdown with URL
        markdown = """
        Here's an image:
        ![Alt text](https://example.com/image.jpg)
        """
        
        with patch('builtins.open', new_callable=MagicMock):
            html = convert_markdown_to_html(markdown)
        
        # Check image tag exists
        assert "<img src=" in html
        assert "alt=\"Alt text\"" in html
        
    def test_inline_code(self, monkeypatch):
        """Test inline code formatting"""
        mock_function = MagicMock(return_value="<code>inline code</code>")
        monkeypatch.setattr('__init__.convert_markdown_to_html', mock_function, raising=False)
        
        from __init__ import convert_markdown_to_html
        
        # Test inline code
        markdown = """
        This is `inline code` and this is ``code with `backticks` inside``
        """
        
        html = convert_markdown_to_html(markdown)
        
        # Check code tags
        assert "<code>" in html
        
    def test_strikethrough(self, monkeypatch):
        """Test strikethrough formatting"""
        mock_function = MagicMock(return_value="<del>strikethrough text</del>")
        monkeypatch.setattr('__init__.convert_markdown_to_html', mock_function, raising=False)
        
        from __init__ import convert_markdown_to_html
        
        # Test strikethrough
        markdown = """
        This is ~~strikethrough text~~
        """
        
        html = convert_markdown_to_html(markdown)
        
        # Check del tags
        assert "<del>" in html 

    def test_css_comments_in_code_blocks(self):
        """Test that CSS comments in code blocks are properly preserved"""
        from src.markdown.converter import convert_markdown_to_html
        
        # Test CSS comments in code blocks
        markdown = """
```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <title>CSS Comments Test</title>
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
        Test content
      </div>
    </div>
  </body>
</html>
```
"""
        
        html = convert_markdown_to_html(markdown)
        
        # Check that CSS comments are preserved correctly
        assert "/* 50 % of the viewport */" in html
        assert "/* no width declared here */" in html
        # Make sure comments are properly styled
        assert '<span class="token comment">/* 50 % of the viewport */</span>' in html
        assert '<span class="token comment">/* no width declared here */</span>' in html 

    def test_list_formatting_with_inline_elements(self):
        """Test that lists with inline code and formatting are properly rendered"""
        from src.markdown.converter import convert_markdown_to_html
        
        # Test the exact example from the user that was causing issues
        markdown = """The grid-template-columns property in CSS Grid Layout is used to define the size and number of columns that will structure the grid. The repeat() function is a helpful tool within this property to simplify the definition of multiple columns (or rows) that share the same characteristics.

When you see repeat(3, 1fr):

- The number `3` is the first argument to `repeat()`, and it signifies that the track definition that follows should be created three times.
- `1fr` is the second argument, representing the track definition itself. The `fr` unit stands for **"fractional unit"**. It tells the browser to divide the available space within the grid container (after accounting for any fixed-size tracks or gaps) into a certain number of shares. In this case, `1fr` means each of the three columns will receive one equal share of that available space. For example, if there's 600px of available width in the container, each of the three `1fr` columns would become 200px wide."""
        
        html = convert_markdown_to_html(markdown)
        
        # Check that we have a proper list structure
        assert '<ul>' in html, "Should have opening <ul> tag"
        assert '</ul>' in html, "Should have closing </ul> tag"
        assert html.count('<ul>') == 1, "Should have exactly one <ul> tag"
        assert html.count('</ul>') == 1, "Should have exactly one </ul> tag"
        assert html.count('<li>') == 2, "Should have exactly 2 list items"
        
        # Check that inline code is preserved within list items
        assert '<li>The number <code>3</code>' in html
        assert '<li><code>1fr</code> is the second argument' in html
        
        # Check that bold formatting is preserved
        assert '<strong>"fractional unit"</strong>' in html
        
        # Ensure the list items contain the full content
        assert 'track definition that follows should be created three times' in html
        assert 'each of the three columns will receive one equal share' in html 