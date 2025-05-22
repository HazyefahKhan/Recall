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
        code_match = re.match(r'```html\s*([\s\S]*?)\s*```', html_code_block, re.DOTALL)
        if code_match:
            # Extract the raw HTML content without the code block markers
            html_content = code_match.group(1).strip()
            placeholder = f"PREVIEW_SECTION_PLACEHOLDER_{preview_counter}"
            
            # Store both the formatted code block (for display) and the raw HTML (for rendering)
            preview_sections[placeholder] = {
                'code': format_code_block(html_content, 'html'),
                'html': html_content
            }
            preview_counter += 1
            return placeholder
        
        # If no code block with html tag is found, just keep the original text
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
        language = match.group(1).strip() or 'text'
        code = match.group(2)
        placeholder = f"CODE_BLOCK_PLACEHOLDER_{code_block_counter}"
        code_blocks[placeholder] = format_code_block(code, language)
        code_block_counter += 1
        return placeholder
    
    code_block_pattern = r'```(.*?)\n(.*?)```'
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
    
    # STEP 3: Process inline code
    def convert_inline_code(text):
        # Handle double backticks (for inline code with literal backticks)
        double_backtick_pattern = r'``([^`]+)``'
        text = re.sub(double_backtick_pattern, lambda m: f'<code>{html_escape(m.group(1))}</code>', text)
        
        # Handle single backticks for inline code
        text = re.sub(r'(?<!`)`(?!`)(.*?)(?<!`)`(?!`)', lambda m: f'<code>{html_escape(m.group(1))}</code>', text)
        
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
    
    # Convert bullet points and numbered lists
    text = re.sub(r'^\*\s+(.*?)$', r'<ul><li>\1</li></ul>', text, flags=re.MULTILINE)
    text = re.sub(r'^\d+\.\s+(.*?)$', r'<ol><li>\1</li></ol>', text, flags=re.MULTILINE)
    
    # Fix multiple consecutive list items (collapse adjacent ul/ol tags)
    text = re.sub(r'</ul>\s*<ul>', '', text)
    text = re.sub(r'</ol>\s*<ol>', '', text)
    
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
    
    # Clean up the code
    code = code.strip()
    
    # Pre-process the entire code block for multi-line CSS comments
    if language and language.lower() in ['css', 'html', 'javascript', 'js']:
        # Process CSS comments with robust encoding
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
        code = processed_code
    
    # Process the code block line by line for remaining processing
    lines = []
    for line in code.split('\n'):
        # Escape HTML special characters (except for already processed comments)
        if '<span class="token comment">' not in line:
            line = (line.replace('&', '&amp;')
                       .replace('<', '&lt;')
                       .replace('>', '&gt;'))
        
        # Special handling for JS single-line comments
        if language and language.lower() in ['javascript', 'js']:
            # Pattern for single-line comments that avoids already processed spans
            js_comment_matches = re.finditer(r'(?<!<span class="token comment">)(//.*?)$', line)
            
            for match in js_comment_matches:
                full_comment = match.group(1)
                start, end = match.span(1)
                
                # Use the same robust encoding for JS comments
                encoded_comment = encode_with_html_entities(full_comment)
                
                # Replace the comment with robustly encoded version
                line = line[:start] + f'<span class="token comment">{encoded_comment}</span>' + line[end:]
        
        # Add proper indentation (preserving spans)
        parts = []
        in_span = False
        for part in re.split(r'(<span.*?>|</span>)', line):
            if part.startswith('<span') or part == '</span>':
                parts.append(part)
                in_span = part.startswith('<span')
            else:
                parts.append(part.replace(' ', '&nbsp;') if not in_span else part)
        
        lines.append(''.join(parts))
    
    code = '<br>'.join(lines)
    
    # Add CSS to ensure comments are properly styled and code wraps properly on mobile
    css_for_comments = """
    <style>
    .token.comment {
        color: #5c6370 !important;
        font-style: normal !important;
    }
    .code-block pre {
        white-space: pre-wrap !important;
        word-wrap: break-word !important;
        overflow-wrap: break-word !important;
        overflow-x: visible !important;
    }
    </style>
    """
    
    return f'''
    {css_for_comments}
    <div class="code-block">
        <pre>{code}</pre>
    </div>
    ''' 