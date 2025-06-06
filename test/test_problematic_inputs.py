import pytest
import sys
import os
from unittest.mock import MagicMock, patch

# Add parent directory to path so we can import the plugin
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@pytest.mark.usefixtures("mock_anki")
class TestProblematicInputs:
    """Test parsing of problematic inputs with HTML elements and special markdown"""
    
    @pytest.fixture
    def dialog(self):
        """Create a RecallInputDialog instance"""
        from src.ui.dialog import RecallInputDialog
        dialog = RecallInputDialog()
        return dialog
    
    def test_parse_input_with_code_elements(self, dialog):
        """Test parsing input with <code> elements in the content"""
        test_input = '''#### Question

How should internal JavaScript in the HTML `<head>` that manipulates the DOM be structured to ensure it executes correctly?

---

#### Correct Option

Internal DOM-manipulating JavaScript in `<head>` should be wrapped in a `DOMContentLoaded` listener to run after HTML parsing.

##### Explanation

If you place JavaScript code directly inside a script tag within the HTML <head>, that script will typically execute as soon as the browser encounters it. At this point, the HTML <body> and its elements have not yet been parsed or created in the Document Object Model (DOM). If this script tries to find or change elements in the <body> (DOM manipulation), it will fail because those elements don't exist yet.

To solve this, you can wrap your DOM manipulation code inside an event listener for the DOMContentLoaded event. This event fires only after the entire initial HTML document has been completely loaded and parsed, meaning the DOM is ready.

Example:

document.addEventListener('DOMContentLoaded', function() { // Your DOM manipulation code here });

#### Preview

```
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DOMContentLoaded Example</title>
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            // This JavaScript code will only run after the entire HTML document is loaded and parsed.
            const statusParagraph = document.getElementById('loadingStatus');
            if (statusParagraph) {
                statusParagraph.textContent = 'DOM is fully loaded and ready!';
            }
            
            const dynamicContentDiv = document.getElementById('dynamicContent');
            if (dynamicContentDiv) {
                const newElement = document.createElement('p');
                newElement.textContent = 'This content was added by JavaScript after DOM load.';
                dynamicContentDiv.appendChild(newElement);
            }
        });
    </script>
</head>
<body>
    <p id="loadingStatus">Page is loading...</p>
    <div id="dynamicContent"></div>
    <p>Some static content already present in HTML.</p>
</body>
</html>
```

---

#### Incorrect Option

Internal JavaScript in `<head>` manipulating the DOM should use `setTimeout` with a small delay to wait for elements.

##### Explanation

Using `setTimeout` with an arbitrary delay is a fragile and unreliable way to wait for the DOM to be ready. The time it takes for the DOM to parse can vary significantly based on network speed, page complexity, and device performance. A fixed delay might be too short on slow connections (causing errors) or unnecessarily long on fast ones (delaying script execution). `DOMContentLoaded` is the proper event-based solution.

---'''
        
        # Set the input text
        dialog.input_text = MagicMock()
        dialog.input_text.toPlainText = MagicMock(return_value=test_input)
        
        # Parse the input
        sections = dialog.parse_input()
        
        # Verify the question was parsed correctly
        assert 'question' in sections
        assert '`<head>`' in sections['question']
        assert 'DOM be structured' in sections['question']
        
        # Verify correct option was parsed
        assert 'correct_options' in sections
        assert len(sections['correct_options']) == 1
        assert '`<head>`' in sections['correct_options'][0]['option']
        assert '`DOMContentLoaded`' in sections['correct_options'][0]['option']
        
        # Verify the preview section was captured
        assert sections['correct_options'][0]['preview_data'] is not None
        assert 'DOCTYPE html' in sections['correct_options'][0]['preview_data']['code']
        assert sections['correct_options'][0]['preview_data']['language'] == 'html'
        
        # Verify incorrect option was parsed
        assert 'incorrect_options' in sections
        assert len(sections['incorrect_options']) == 1
        assert '`setTimeout`' in sections['incorrect_options'][0]['option']
    
    def test_parse_input_with_backticks(self, dialog):
        """Test parsing input with backticks in the content"""
        test_input = '''#### Question

How are strings, which represent textual data, typically declared in JavaScript?

---

#### Correct Option

Using either single quotes (`'`) or double quotes (`"`), with consistency for the start and end of each string.

##### Explanation

In JavaScript, a string is a sequence of characters used to represent text. To create a string literal (a fixed string value in your code), you can enclose the text within either single quotes (`'`) or double quotes (`"`). The key is consistency: if you start a string with a single quote, you must end it with a single quote. If you start with a double quote, you must end it with a double quote. For example, both `'hello'` and `"hello"` are valid strings representing the same text. This flexibility allows you to easily include one type of quote within a string defined by the other type (e.g., `"He said 'Hi!'"` or `'She replied, "Okay."'`).

#### Preview

```
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>String Declaration Example</title>
</head>
<body>
    <p id="stringOutput1"></p>
    <p id="stringOutput2"></p>
    <script>
        let doubleQuotedString = "This is a string using double quotes.";
        let singleQuotedString = 'This is a string using single quotes.';

        document.getElementById("stringOutput1").textContent = doubleQuotedString;
        document.getElementById("stringOutput2").textContent = singleQuotedString;
    </script>
</body>
</html>
```

---

#### Incorrect Option

Only using double quotes (`"`) for all string literals.

##### Explanation

While using only double quotes is a valid coding style some developers or teams might adopt, JavaScript as a language allows both single (`'`) and double (`"`) quotes for string literals. Restricting to only double quotes is a convention, not a language requirement.

---

#### Incorrect Option

Using backticks (`` ` ``) exclusively for all string declarations.

##### Explanation

Backticks (`` ` ``) are used to declare a special type of string in JavaScript called a "template literal" (or template string). Template literals offer features like multi-line strings and string interpolation (embedding expressions directly within the string using `${expression}`). While you _can_ use template literals for simple strings where these features aren't needed, they are not the exclusive way to declare strings. Single and double quotes are still perfectly valid and often preferred for basic string literals.

---'''
        
        # Set the input text
        dialog.input_text = MagicMock()
        dialog.input_text.toPlainText = MagicMock(return_value=test_input)
        
        # Parse the input
        sections = dialog.parse_input()
        
        # Verify the question was parsed correctly
        assert 'question' in sections
        assert 'strings' in sections['question']
        
        # Verify correct option was parsed with backticks preserved
        assert 'correct_options' in sections
        assert len(sections['correct_options']) == 1
        assert "(`'`)" in sections['correct_options'][0]['option']
        assert '(`"`)' in sections['correct_options'][0]['option']
        
        # Verify incorrect options were parsed
        assert 'incorrect_options' in sections
        assert len(sections['incorrect_options']) == 2
        
        # Check first incorrect option
        assert '(`"`)' in sections['incorrect_options'][0]['option']
        
        # Check second incorrect option with double backticks
        assert '(`` ` ``)' in sections['incorrect_options'][1]['option']
        assert 'Backticks (`` ` ``)' in sections['incorrect_options'][1]['explanation']
    
    def test_markdown_converter_handles_html_elements(self):
        """Test that the markdown converter properly handles HTML elements"""
        from src.markdown.converter import convert_markdown_to_html
        
        # Test with <code> elements
        text = "This is some text with `<code>` elements and `<script>` tags."
        result = convert_markdown_to_html(text)
        
        # The HTML entities should be escaped within the code blocks
        assert '<code>&lt;code&gt;</code>' in result
        assert '<code>&lt;script&gt;</code>' in result
        
        # Test with nested backticks
        text2 = "Use double backticks `` ` `` to display single backticks."
        result2 = convert_markdown_to_html(text2)
        assert '<code>` </code>' in result2 or '<code>`</code>' in result2 