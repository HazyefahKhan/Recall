"""
Markdown to HTML conversion for Recall Anki plugin.
"""

import re
import markdown
import urllib.request
import urllib.parse
import urllib.error
import os
import hashlib
from aqt import mw

# This is a dummy function that does nothing, to replace the syntax highlighting functionality
def safe_highlight(pattern, replacement, text, flags=0):
    """Simple helper function that just returns the input text without any syntax highlighting."""
    # Simply return the text unchanged
    return text

def convert_markdown_to_html(text):
    """
    Convert markdown text to HTML with simple color formatting for options.
    
    Args:
        text (str): The markdown text to convert
        
    Returns:
        str: The converted HTML
    """
    # Define a helper function to escape HTML entities
    def html_escape(text):
        return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace("'", '&#39;')
    
    # Extract Preview sections first (before any other processing)
    preview_sections = {}
    preview_counter = 0
    
    def extract_preview_sections(match):
        nonlocal preview_counter
        # The HTML content is inside the code block
        html_code_block = match.group(2)
        
        # Check if we have a code block with html tag
        # Updated pattern to handle optional whitespace and newlines
        code_match = re.match(r'```\s*(\w*)\s*([\s\S]*?)\s*```', html_code_block, re.DOTALL)
        if code_match:
            # Extract the raw HTML content without the code block markers
            language = code_match.group(1).lower() if code_match.group(1) else 'html'
            html_content = code_match.group(2).strip()
            placeholder = f"PREVIEW_SECTION_PLACEHOLDER_{preview_counter}"
            
            # Store both the formatted code block (for display) and the raw HTML (for rendering)
            preview_sections[placeholder] = {
                'code': format_code_block(html_content, language),
                'html': html_content if language == 'html' else None
            }
            preview_counter += 1
            return placeholder
        
        # If no code block with proper format is found, just keep the original text
        return match.group(0)
    
    # Match "#### Preview" followed by a code block
    preview_pattern = r'#### Preview\s*([\s\S]*?)(?=\n(?:---|\Z|#### ))'
    text = re.sub(preview_pattern, extract_preview_sections, text, flags=re.DOTALL)
    
    # Helper function to download external images and save them to Anki's media collection
    def retrieve_external_image(url):
        try:
            # Generate a filename for the image
            # Use the last part of the URL path, or a hash if that doesn't work
            filename = os.path.basename(urllib.parse.urlparse(url).path)
            # Ensure the filename is valid and not too long
            if not filename or len(filename) > 50 or not re.match(r'^[a-zA-Z0-9._-]+$', filename):
                # Use a hash of the URL as the filename with the correct extension
                file_ext = os.path.splitext(filename)[1] if filename else '.jpg'
                if not file_ext or len(file_ext) < 2:
                    file_ext = '.jpg'  # Default to .jpg if no extension
                filename = hashlib.md5(url.encode('utf-8')).hexdigest() + file_ext
            
            # Check if the file already exists in media collection
            if not os.path.exists(os.path.join(mw.col.media.dir(), filename)):
                # Download the image
                req = urllib.request.Request(
                    url, 
                    headers={'User-Agent': 'Mozilla/5.0 (Anki Image Downloader)'}
                )
                with urllib.request.urlopen(req, timeout=5) as response:
                    image_data = response.read()
                
                # Save the image to Anki's media collection
                with open(os.path.join(mw.col.media.dir(), filename), 'wb') as f:
                    f.write(image_data)
            
            return filename
        except Exception as e:
            print(f"Error retrieving image {url}: {e}")
            return url  # Return the original URL if download fails
    
    # STEP 1: Process and preserve code blocks FIRST (before any other processing)
    # This ensures CSS comments and other special characters in code are preserved
    code_blocks = {}
    code_block_counter = 0
    
    def extract_code_blocks(match):
        nonlocal code_block_counter
        language = match.group(1).strip() if match.group(1) else 'text'
        code = match.group(2)
        placeholder = f"CODE_BLOCK_PLACEHOLDER_{code_block_counter}"
        code_blocks[placeholder] = format_code_block(code, language)
        code_block_counter += 1
        return placeholder
    
    # Update the regex pattern to handle code blocks more flexibly
    # This pattern now handles:
    # - Optional whitespace after opening ```
    # - Optional language specifier
    # - Content that may or may not start with a newline
    code_block_pattern = r'```\s*(\w*)\s*([\s\S]*?)```'
    text = re.sub(code_block_pattern, extract_code_blocks, text, flags=re.DOTALL)
    
    # STEP 2: Process images (and other elements that should be processed early)
    # Match image markdown pattern and directly convert to HTML
    def convert_images(text):
        image_pattern = r'!\[(.*?)\]\((.*?)\)'
        
        def image_replacer(match):
            alt_text = html_escape(match.group(1))
            url = match.group(2).strip()
            
            # For external URLs, try to download the image to Anki's media collection
            if url.startswith(('http://', 'https://')):
                try:
                    # Download the image and get the local filename
                    filename = retrieve_external_image(url)
                    return f'<img src="{filename}" alt="{alt_text}" style="max-width: 100%;">'
                except Exception as e:
                    # If download fails, use the original URL but with warning text
                    print(f"Failed to download image {url}: {e}")
                    return f'<img src="{url}" alt="{alt_text}" style="max-width: 100%;"> (external image - may not display properly)'
            else:
                # Local image - handle relative paths
                return f'<img src="{url}" alt="{alt_text}">'
        
        return re.sub(image_pattern, image_replacer, text)
    
    text = convert_images(text)
    
    # STEP 3: Process inline code with better handling of edge cases
    def convert_inline_code(text):
        # Handle triple backticks (for code blocks) - should already be processed at this point
        # but this is a safety check to prevent conflicts with inline code processing
        triple_backtick_pattern = r'```[\s\S]*?```'
        triple_backtick_matches = re.findall(triple_backtick_pattern, text)
        placeholders = {}
        
        # Replace triple backtick blocks with placeholders to protect them
        for i, match in enumerate(triple_backtick_matches):
            placeholder = f"TRIPLE_BACKTICK_PLACEHOLDER_{i}"
            placeholders[placeholder] = match
            text = text.replace(match, placeholder)
        
        # Handle double backticks first (for inline code containing single backticks)
        # Pattern: `` ... `` where ... can contain single backticks
        double_backtick_pattern = r'``([^`]+?)``'
        text = re.sub(double_backtick_pattern, lambda m: f'<code>{html_escape(m.group(1))}</code>', text)
        
        # Handle single backticks for inline code
        # Updated pattern to be more precise and avoid edge cases
        # This matches single backticks that are not part of double/triple backticks
        single_backtick_pattern = r'(?<!`)(`(?!`))((?:[^`]|(?<=\\)`)+?)(?<!`)(`(?!`))'
        text = re.sub(single_backtick_pattern, lambda m: f'<code>{html_escape(m.group(2))}</code>', text)
        
        # Restore triple backtick blocks
        for placeholder, original in placeholders.items():
            text = text.replace(placeholder, original)
        
        return text
    
    # STEP 4: Process other markdown elements
    # First, process inline code to protect content inside backticks
    text = convert_inline_code(text)
    
    # UPDATED TILDE HANDLING:
    # 1. Explicitly preserve tildes in mathematical expressions and technical patterns
    # - Replace tildes in common technical patterns (like ~/, ~username, etc.)
    text = re.sub(r'(~\/|~[a-zA-Z0-9_-]+)', lambda m: m.group(0).replace('~', '&#126;'), text)
    
    # - Preserve isolated tildes (that are clearly not part of strikethrough)
    text = re.sub(r'(?<![~`\\])~(?![~\w])', r'&#126;', text)  # Isolated tildes not followed by word char
    text = re.sub(r'(?<=\s)~(?=\s)', r'&#126;', text)         # Tildes between spaces
    text = re.sub(r'(?<=\()~(?=[\w])', r'&#126;', text)       # Tilde after open parenthesis 
    text = re.sub(r'(?<=[=:])~(?=[\w])', r'&#126;', text)     # Tilde after equals or colon
    
    # 2. Standard markdown strikethrough with double tildes
    text = re.sub(r'~~([^~\n]+?)~~', r'<del>\1</del>', text)
    
    # 3. Special case: single tilde pairs that clearly wrap content for strikethrough
    # This is a more restrictive pattern to avoid false positives
    text = re.sub(r'(?<![~`\\])~([^\s~][^~\n]{1,40}?[^\s~])~(?![~])', r'<del>\1</del>', text)

    # Apply color for correct options (green)
    text = re.sub(r'(Correct Option:.*?(?=\n\n|\n[^\n]|\n$|$))', 
                  r'<span style="color: #98c379;">\1</span>', 
                  text, flags=re.DOTALL)
    
    # Apply color for incorrect options (red)
    text = re.sub(r'(Incorrect Option:.*?(?=\n\n|\n[^\n]|\n$|$))', 
                  r'<span style="color: #e06c75;">\1</span>', 
                  text, flags=re.DOTALL)
    
    # Apply color for selected options (blue) - this overrides the previous colors
    text = re.sub(r'(Selected Option:.*?(?=\n\n|\n[^\n]|\n$|$))', 
                  r'<span style="color: #61afef;">\1</span>', 
                  text, flags=re.DOTALL)
    
    # Process inline code (this must happen after color processing but before emphasis)
    text = convert_inline_code(text)
    
    # RESTORE CODE BLOCKS BEFORE EMPHASIS PROCESSING
    # This prevents placeholders from being affected by emphasis formatting
    for placeholder, code_html in code_blocks.items():
        text = text.replace(placeholder, code_html)
    
    # Convert headers
    for i in range(6, 0, -1):
        hash_marks = '#' * i
        text = re.sub(f'^{hash_marks}\\s+(.*?)$', 
                      lambda m: f'<h{i}>{m.group(1)}</h{i}>', 
                      text, 
                      flags=re.MULTILINE)
    
    # Convert lists - improved handling for consecutive items
    # First, handle unordered lists
    lines = text.split('\n')
    result_lines = []
    in_ul = False
    in_ol = False
    
    for line in lines:
        # Check if this line is an unordered list item (support both * and -)
        ul_match = re.match(r'^[\*\-]\s+(.*)$', line)
        # Check if this line is an ordered list item
        ol_match = re.match(r'^\d+\.\s+(.*)$', line)
        
        if ul_match:
            # This is an unordered list item
            if not in_ul:
                # Start a new list
                result_lines.append('<ul>')
                in_ul = True
            # Close any open ordered list
            if in_ol:
                result_lines.append('</ol>')
                in_ol = False
            # Add the list item
            result_lines.append(f'<li>{ul_match.group(1)}</li>')
        elif ol_match:
            # This is an ordered list item
            if not in_ol:
                # Start a new list
                result_lines.append('<ol>')
                in_ol = True
            # Close any open unordered list
            if in_ul:
                result_lines.append('</ul>')
                in_ul = False
            # Add the list item
            result_lines.append(f'<li>{ol_match.group(1)}</li>')
        else:
            # This is not a list item
            # Close any open lists
            if in_ul:
                result_lines.append('</ul>')
                in_ul = False
            if in_ol:
                result_lines.append('</ol>')
                in_ol = False
            # Add the regular line
            result_lines.append(line)
    
    # Close any remaining open lists at the end
    if in_ul:
        result_lines.append('</ul>')
    if in_ol:
        result_lines.append('</ol>')
    
    # Join the lines back together
    text = '\n'.join(result_lines)
    
    # Convert emphasis and strong emphasis
    text = re.sub(r'(?<!\*)\*(?!\*)([^\*\n]+?)(?<!\*)\*(?!\*)', r'<em>\1</em>', text)
    text = re.sub(r'\*\*([^\*\n]+?)\*\*', r'<strong>\1</strong>', text)
    
    # Add support for underscore-based emphasis and strong emphasis
    text = re.sub(r'(?<!_)_(?!_)([^_\n]+?)(?<!_)_(?!_)', r'<em>\1</em>', text)
    text = re.sub(r'__([^_\n]+?)__', r'<strong>\1</strong>', text)
    
    # Convert links - do this after the other formatting
    link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
    text = re.sub(link_pattern, r'<a href="\2">\1</a>', text)
    
    # Convert paragraphs (multiple newlines to paragraph breaks)
    text = re.sub(r'\n\s*\n', '\n<br><br>\n', text)
    
    # FINAL STEP: Restore Preview sections with both code display and rendered HTML
    for placeholder, content in preview_sections.items():
        # Create a container with both the code display and the rendered HTML
        preview_html = f'''
        <div class="preview-container">
            <div class="code-display">
                <h5>HTML Code:</h5>
                {content['code']}
            </div>
            <div class="preview-display">
                <h5>Rendered Preview:</h5>
                <div class="preview-result">
                    <iframe srcdoc="{content['html'].replace('"', '&quot;')}" style="width:100%; height:300px; border:none;"></iframe>
                </div>
            </div>
        </div>
        '''
        text = text.replace(placeholder, preview_html)
    
    return text

def format_code_block(code, language=None):
    """
    Format a code block with proper styling and line breaks.
    
    Args:
        code (str): The code to format
        language (str, optional): The programming language for syntax highlighting
        
    Returns:
        str: The formatted HTML for the code block
    """
    # Helper function to encode critical characters with HTML entities
    def encode_with_html_entities(text):
        """Encode text with HTML entities for critical characters"""
        return (text.replace('&', '&amp;')
                    .replace('<', '&lt;')
                    .replace('>', '&gt;'))
    
    # Clean up the code
    code = code.strip()
    
    # Apply HTML escaping to the entire code block for safety
    escaped_code = encode_with_html_entities(code)
    
    # Determine the language class for Prism.js
    # Map common language aliases to Prism.js language classes
    language_map = {
        'js': 'javascript',
        'ts': 'typescript',
        'py': 'python',
        'rb': 'ruby',
        'cs': 'csharp',
        'cpp': 'cpp',
        'c++': 'cpp',
        'html': 'html',
        'css': 'css',
        'sql': 'sql',
        'json': 'json',
        'xml': 'xml',
        'bash': 'bash',
        'shell': 'bash',
        'sh': 'bash',
        'yaml': 'yaml',
        'yml': 'yaml'
    }
    
    # Normalize language name
    if language:
        language_lower = language.lower()
        prism_language = language_map.get(language_lower, language_lower)
    else:
        prism_language = 'plaintext'
    
    # Add CSS to ensure proper styling and fallback behavior
    css_for_code_block = """
    <style>
    /* Import JetBrains Mono font */
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&display=swap');
    
    /* Fallback styling when Prism.js is not active */
    .code-block {
        background-color: #21252b; /* Darker outer background */
        padding: 1px;
        border-radius: 8px;
        margin: 15px 0;
        overflow-x: auto;
    }
    
    .code-block pre {
        background-color: #282C34; /* Main code background */
        padding: 15px;
        border-radius: 7px;
        margin: 0;
        border: none;
        box-shadow: none;
        white-space: pre;
        word-wrap: normal;
        overflow-wrap: normal;
    }
    
    .code-block pre code {
        font-family: 'JetBrains Mono', 'Consolas', 'Monaco', monospace;
        font-size: 14px;
        color: #ABB2BF;
        background: none;
        padding: 0;
        border: none;
        display: block;
        white-space: pre;
        overflow-x: auto;
    }
    
    /* Ensure Prism.js styles take precedence when loaded */
    .code-block pre[class*="language-"] {
        background-color: #282C34 !important;
    }
    </style>
    """
    
    # Return the code block formatted for Prism.js
    # The structure is: <pre><code class="language-{lang}">{escaped_code}</code></pre>
    # This allows Prism.js to apply syntax highlighting while maintaining safety
    return f'''
    {css_for_code_block}
    <div class="code-block">
        <pre><code class="language-{prism_language}">{escaped_code}</code></pre>
    </div>
    ''' 