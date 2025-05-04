from aqt import mw
from aqt import gui_hooks
from aqt.qt import *
from anki.models import ModelManager
from anki.notes import Note
from anki.utils import html_to_text_line
import re
import markdown
import urllib.request
import urllib.parse
import urllib.error
import os
import hashlib
import re

# This is a dummy function that does nothing, to replace the syntax highlighting functionality
def safe_highlight(pattern, replacement, text, flags=0):
    """Simple helper function that just returns the input text without any syntax highlighting."""
    # Simply return the text unchanged
    return text

def convert_markdown_to_html(text):
    """Convert markdown text to HTML with simple color formatting for options."""
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
    """Format a code block with proper styling and line breaks."""
    # Clean up the code
    code = code.strip()
    
    # Pre-process the entire code block for multi-line CSS comments
    if language and language.lower() in ['css', 'html', 'javascript', 'js']:
        # First, create a list of all CSS comments and their positions
        comment_positions = []
        for match in re.finditer(r'/\*(.*?)\*/', code, flags=re.DOTALL):
            comment_positions.append((match.start(), match.end(), match.group(1)))
        
        # Now replace comments one by one, from the end so positions remain valid
        comment_positions.sort(reverse=True)
        for start, end, content in comment_positions:
            # Escape special characters
            escaped_content = content.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            replacement = f'<span class="token comment">/*{escaped_content}*/</span>'
            code = code[:start] + replacement + code[end:]
    
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
            line = re.sub(r'(?<!<span class="token comment">)(//.*?)$', 
                          r'<span class="token comment">\1</span>', line)
        
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
    
    # Add CSS to ensure comments are properly styled
    css_for_comments = """
    <style>
    .token.comment {
        color: #5c6370 !important;
        font-style: normal !important;
    }
    </style>
    """
    
    return f'''
    {css_for_comments}
    <div class="code-block">
        <pre>{code}</pre>
    </div>
    '''

class RecallInputDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.load_last_deck()  # Load last selected deck
        
    def setup_ui(self):
        self.setWindowTitle("Create Recall Question")
        self.setMinimumWidth(800)
        
        layout = QVBoxLayout(self)
        
        # Deck selector
        deck_layout = QHBoxLayout()
        deck_label = QLabel("Select Deck:")
        self.deck_combo = QComboBox()
        self.populate_deck_list()
        deck_layout.addWidget(deck_label)
        deck_layout.addWidget(self.deck_combo)
        layout.addLayout(deck_layout)
        
        # Input area
        self.input_text = QPlainTextEdit()
        self.input_text.setPlaceholderText("""#### Question 
[Insert question text here]
___
#### Correct Option
[Insert option text here] 

##### Explanation
[Insert detailed explanation on why this option is correct]

#### Preview
```html
<!-- Optional HTML preview that will be rendered as-is -->
<div style="background-color: #f0f0f0; padding: 10px;">
  <p>This is a preview of HTML content</p>
</div>
```
___
#### Incorrect Option
[Insert option text here including] 

##### Explanation
[Insert detailed explanation on why this option is incorrect]
___""")
        self.input_text.setMinimumHeight(400)
        layout.addWidget(self.input_text)
        
        # Buttons
        button_layout = QHBoxLayout()
        self.create_button = QPushButton("Create Card")
        self.create_button.clicked.connect(self.create_card)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(self.create_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)

    def populate_deck_list(self):
        """Populate the deck selector with all available decks and subdecks."""
        decks = mw.col.decks.all_names_and_ids()
        for deck in decks:
            deck_name = deck.name
            indent = deck_name.count("::") * 4  # 4 spaces per level
            display_name = " " * indent + deck_name.split("::")[-1]
            self.deck_combo.addItem(display_name, deck.id)

    def load_last_deck(self):
        """Load the last selected deck from Anki's configuration."""
        last_deck_id = mw.pm.profile.get('recall_last_deck', None)
        if last_deck_id is not None:
            # Find the index of the last used deck in the combo box
            index = self.deck_combo.findData(last_deck_id)
            if index >= 0:
                self.deck_combo.setCurrentIndex(index)

    def save_last_deck(self):
        """Save the currently selected deck ID to Anki's configuration."""
        deck_id = self.deck_combo.currentData()
        mw.pm.profile['recall_last_deck'] = deck_id

    def parse_input(self):
        text = self.input_text.toPlainText()
        
        # First, clean up any variations of the Explanation header
        text = re.sub(r'##### Explanation.*?\n', '##### Explanation\n', text)
        
        # Parse sections using regex
        sections = {}
        
        # Extract question
        question_match = re.search(r'#### Question\s*\n(.*?)(?=\n(?:___|---)|\Z)', text, re.DOTALL)
        if question_match:
            sections['question'] = question_match.group(1).strip()
            
            # Check for preview section in question
            preview_match = re.search(r'#### Preview\s*\n```html\s*(.*?)\s*```', question_match.group(1), re.DOTALL)
            if preview_match:
                # Store both the raw HTML and the code block for display
                preview_html = preview_match.group(1).strip()
                sections['question_preview'] = {
                    'code': preview_html,  # The raw code to display
                    'html': preview_html   # The HTML to render
                }
        
        # Initialize correct options list
        sections['correct_options'] = []
        
        # First, extract all complete option sections (between section markers)
        section_markers = [m.start() for m in re.finditer(r'\n---\n', text)]
        section_markers = [-1] + section_markers + [len(text)]
        
        option_sections = []
        for i in range(len(section_markers) - 1):
            start = section_markers[i] + 5 if i > 0 else 0  # Skip the --- marker except for first section
            end = section_markers[i+1]
            section = text[start:end].strip()
            if section and ('#### Correct Option' in section or '#### Incorrect Option' in section):
                option_sections.append(section)
        
        # Now parse each option section
        for section in option_sections:
            # Determine if this is a correct or incorrect option
            is_correct = '#### Correct Option' in section
            
            # Extract option text, explanation, and preview
            option_match = re.search(
                r'#### (Correct|Incorrect) Option\s*\n(.*?)(?=\n##### Explanation)',
                section, re.DOTALL
            )
            
            explanation_match = re.search(
                r'##### Explanation\s*\n(.*?)(?=\n#### Preview|\Z)',
                section, re.DOTALL
            )
            
            preview_match = re.search(
                r'#### Preview\s*\n```html\s*(.*?)\s*```',
                section, re.DOTALL
            )
            
            if option_match and explanation_match:
                option_text = option_match.group(2).strip()
                explanation_text = explanation_match.group(1).strip()
                
                preview_html = None
                preview_code = None
                if preview_match:
                    preview_html = preview_match.group(1).strip()
                    preview_code = preview_html
                
                option_data = {
                    'option': option_text,
                    'explanation': explanation_text,
                    'preview_code': preview_code,
                    'preview_html': preview_html
                }
                
                if is_correct:
                    sections['correct_options'].append(option_data)
                else:
                    if 'incorrect_options' not in sections:
                        sections['incorrect_options'] = []
                    sections['incorrect_options'].append(option_data)
        
        # Make sure incorrect_options exists even if empty
        if 'incorrect_options' not in sections:
            sections['incorrect_options'] = []
            
        return sections

    def create_card(self):
        try:
            sections = self.parse_input()
            
            # Get selected deck ID
            deck_id = self.deck_combo.currentData()
            if not deck_id:
                QMessageBox.critical(self, "Error", "Please select a deck")
                return

            # Save the selected deck before creating the card
            self.save_last_deck()
            
            # Count correct and incorrect options
            correct_count = len(sections['correct_options'])
            incorrect_count = len(sections['incorrect_options'])
            
            # Create note with appropriate model name
            if correct_count == 1 and incorrect_count == 1:
                model_name = "Recall"
            else:
                model_name = f"Recall{correct_count}{incorrect_count}"
                
            model = mw.col.models.by_name(model_name)
            if not model:
                create_recall_note_type(correct_count, incorrect_count)
                model = mw.col.models.by_name(model_name)
                
            note = Note(mw.col, model)
            
            # Fill note fields with converted HTML
            question_html = convert_markdown_to_html(sections['question'])
            
            # Add question preview section if exists
            if 'question_preview' in sections:
                preview_data = sections['question_preview']
                preview_html = self.create_preview_html(preview_data['code'], preview_data['html'])
                question_html += preview_html
            
            note['Question'] = question_html
            
            # Add correct options
            for i, correct in enumerate(sections['correct_options'], 1):
                suffix = str(i) if correct_count > 1 else ""
                
                # Convert option and explanation to HTML
                option_html = convert_markdown_to_html(correct['option'])
                explanation_html = convert_markdown_to_html(correct['explanation'])
                
                # Add preview HTML if it exists - here was the issue
                if correct['preview_html']:
                    # Create a custom preview HTML section with both code and rendered view
                    preview_html = self.create_preview_html(correct['preview_code'], correct['preview_html'])
                    # Append this to the explanation
                    explanation_html += preview_html
                
                note[f'CorrectOption{suffix}'] = option_html
                note[f'CorrectExplanation{suffix}'] = explanation_html
            
            # Add incorrect options
            for i, incorrect in enumerate(sections['incorrect_options'], 1):
                # Convert option and explanation to HTML
                option_html = convert_markdown_to_html(incorrect['option'])
                explanation_html = convert_markdown_to_html(incorrect['explanation'])
                
                # Add preview HTML if it exists
                if incorrect['preview_html']:
                    # Create a custom preview HTML section with both code and rendered view
                    preview_html = self.create_preview_html(incorrect['preview_code'], incorrect['preview_html'])
                    # Append this to the explanation
                    explanation_html += preview_html
                
                note[f'IncorrectOption{i}'] = option_html
                note[f'IncorrectExplanation{i}'] = explanation_html
            
            # Add note to selected deck
            mw.col.add_note(note, deck_id)
            mw.reset()
            
            QMessageBox.information(self, "Success", f"Card created successfully with {correct_count} correct and {incorrect_count} incorrect options!")
            self.accept()
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            QMessageBox.critical(self, "Error", f"Failed to create card: {str(e)}\n\nDetails:\n{error_details}")

    def create_preview_html(self, code, html):
        """Create a formatted HTML container with both code display and rendered preview."""
        # Add debug information as a comment
        return f'''
        <!-- Preview HTML section -->
        <div class="preview-container">
            <div class="code-display">
                <h5>HTML Code:</h5>
                {format_code_block(code, 'html')}
            </div>
            <div class="preview-display">
                <h5>Rendered Preview:</h5>
                <div class="preview-result">
                    <iframe srcdoc="{html.replace('"', '&quot;')}" style="width:100%; height:300px; border:none;"></iframe>
                </div>
            </div>
        </div>
        '''

def show_recall_input_dialog():
    dialog = RecallInputDialog(mw)
    dialog.exec()

# Add menu item
action = QAction("Create Recall Question", mw)
action.triggered.connect(show_recall_input_dialog)
action.setShortcut(QKeySequence("Ctrl+Shift+R"))  # Updated keyboard shortcut
mw.form.menuTools.addAction(action)

def create_recall_note_type(correct_options, incorrect_options):
    """Create a recall note type with code examples."""
    # Rename from ExamCard to Recall with special case for 1-1 configuration
    if correct_options == 1 and incorrect_options == 1:
        model_name = "Recall"
    else:
        model_name = f"Recall{correct_options}{incorrect_options}"
    
    if model_name not in mw.col.models.all_names():
        mm = mw.col.models
        m = mm.new(model_name)
        
        # Add fields
        fields = ["Question"]
        
        # Add correct options fields
        for i in range(correct_options):
            suffix = str(i + 1) if correct_options > 1 else ""
            fields.extend([
                f"CorrectOption{suffix}",
                f"CorrectExplanation{suffix}"
            ])
        
        # Add incorrect options fields
        for i in range(incorrect_options):
            fields.extend([
                f"IncorrectOption{i + 1}",
                f"IncorrectExplanation{i + 1}"
            ])
        
        for field in fields:
            mm.add_field(m, mm.new_field(field))

        # Create template
        template = mm.new_template(model_name)
        
        # Front template
        template['qfmt'] = """
        <div class="question">{{Question}}</div>
        <div id="options" class="options"></div>
        <button onclick="submitAnswer()" id="submit-btn" class="submit-button">Submit</button>

        <script>
            var selectedOptions = new Set();
            var submitted = false;
            var originalToShuffled = {};
            var shuffledToOriginal = {};

            function shuffleArray(array) {
                for (let i = array.length - 1; i > 0; i--) {
                    const j = Math.floor(Math.random() * (i + 1));
                    [array[i], array[j]] = [array[j], array[i]];
                }
                return array;
            }

            function createOption(index, content) {
                return `
                    <div class="option" onclick="selectOption(${index})" id="option${index}" data-index="${index}">
                        <input type="checkbox" name="option" id="checkbox${index}" class="option-checkbox">
                        <label>${content}</label>
                    </div>
                `;
            }

            function initializeOptions() {
                try {
                    const options = [""" + \
                    ",\n".join([f"{{ content: `{{{{CorrectOption{str(i + 1) if correct_options > 1 else ''}}}}}`, isCorrect: true }}" for i in range(correct_options)]) + \
                    ",\n" + \
                    ",\n".join([f"{{ content: `{{{{IncorrectOption{i + 1}}}}}`, isCorrect: false }}" for i in range(incorrect_options)]) + \
                    """
                    ];

                    const shuffledIndices = shuffleArray([""" + ", ".join(map(str, range(correct_options + incorrect_options))) + """]);
                    
                    const optionsContainer = document.getElementById('options');
                    if (!optionsContainer) {
                        console.error('Options container not found');
                        return;
                    }

                    // Clear existing options
                    optionsContainer.innerHTML = '';
                    
                    shuffledIndices.forEach((originalIndex, newIndex) => {
                        originalToShuffled[originalIndex] = newIndex;
                        shuffledToOriginal[newIndex] = originalIndex;
                        const option = options[originalIndex];
                        if (option && option.content) {
                            optionsContainer.innerHTML += createOption(newIndex, option.content);
                        }
                    });

                    document.body.setAttribute('data-option-mapping', JSON.stringify({
                        originalToShuffled,
                        shuffledToOriginal
                    }));
                } catch (error) {
                    console.error('Error initializing options:', error);
                }
            }

            function selectOption(index) {
                if (submitted) return;
                
                const checkbox = document.getElementById('checkbox' + index);
                const optionDiv = document.getElementById('option' + index);
                
                if (selectedOptions.has(index)) {
                    selectedOptions.delete(index);
                    optionDiv.classList.remove('selected');
                    checkbox.checked = false;
                } else {
                    selectedOptions.add(index);
                    optionDiv.classList.add('selected');
                    checkbox.checked = true;
                }
            }

            function submitAnswer() {
                if (submitted || selectedOptions.size === 0) return;
                submitted = true;
                
                const originalSelected = Array.from(selectedOptions).map(index => shuffledToOriginal[index]);
                document.body.setAttribute('data-selected-options', JSON.stringify(originalSelected));
                
                document.getElementById('submit-btn').disabled = true;
                pycmd('ans');
            }

            // Initialize options when the document is ready
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', initializeOptions);
            } else {
                setTimeout(initializeOptions, 0);
            }
        </script>
        """

        # Back template
        template['afmt'] = """
        {{FrontSide}}
        <hr id="answer">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/prism/1.24.1/themes/prism-tomorrow.min.css">
        <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.24.1/prism.min.js" data-manual></script>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.24.1/components/prism-csharp.min.js"></script>
        
        <!-- This container will hold all explanation entries in the randomized order -->
        <div class="answer" id="answers"></div>

        <script>
            // Build an array of all items in the same order they were added on the front side:
            var allItems = [
                """ + ",\n".join([
                    f"{{ content: `{{{{CorrectOption{str(i + 1) if correct_options > 1 else ''}}}}}`, explanation: `{{{{CorrectExplanation{str(i + 1) if correct_options > 1 else ''}}}}}`, isCorrect: true }}"
                    for i in range(correct_options)
                ]) + (
                    ",\n" if correct_options and incorrect_options else ""
                ) + ",\n".join([
                    f"{{ content: `{{{{IncorrectOption{i + 1}}}}}`, explanation: `{{{{IncorrectExplanation{i + 1}}}}}`, isCorrect: false }}"
                    for i in range(incorrect_options)
                ]) + """
            ];

            // HTML escape function to prevent HTML interpretation
            function htmlEscape(text) {
                return text
                    .replace(/&/g, '&amp;')
                    .replace(/</g, '&lt;')
                    .replace(/>/g, '&gt;')
                    .replace(/"/g, '&quot;')
                    .replace(/'/g, '&#39;');
            }

            function buildAnswerContainers() {
                try {
                    var mappingStr = document.body.getAttribute('data-option-mapping');
                    if (!mappingStr) return; // No mapping found
                    var mapping = JSON.parse(mappingStr);
                    var stO = mapping.shuffledToOriginal; // Maps displayedIndex -> originalIndex
                    var answersDiv = document.getElementById('answers');
                    if (!answersDiv) return;
                    
                    // Get the question text
                    var questionDiv = document.querySelector('.question');
                    var questionText = questionDiv ? questionDiv.textContent : '';
                    
                    // Clear existing content
                    answersDiv.innerHTML = '';

                    // Build explanation containers in the same order as displayed on the front
                    for (var newIndex = 0; newIndex < allItems.length; newIndex++) {
                        var originalIndex = stO[newIndex];
                        var item = allItems[originalIndex];
                        // Create container
                        var container = document.createElement('div');
                        container.className = 'explanation-container ' + 
                            (item.isCorrect ? 'correct-answer' : 'incorrect-answer');
                        container.setAttribute('data-option-index', originalIndex);
                        
                        container.innerHTML = `
                            <div class="question-reference">Q: ${htmlEscape(questionText)}</div>
                            <div class="option-header">${item.content}</div>
                            <div class="explanation">${item.explanation}</div>
                        `;
                        answersDiv.appendChild(container);
                    }
                } catch (err) {
                    console.error('Error building answer containers:', err);
                }
            }

            // Prism and highlightSelection logic is kept, but updated to highlight the newly added containers
            function highlightSelection() {
                try {
                    var selectedOptionsStr = document.body.getAttribute('data-selected-options');
                    if (!selectedOptionsStr) return;

                    var selectedOptions = JSON.parse(selectedOptionsStr);
                    var containers = document.querySelectorAll('.explanation-container');
                    
                    // Mark any options that were selected
                    containers.forEach(container => {
                        const optionIndex = parseInt(container.getAttribute('data-option-index'));
                        if (selectedOptions.includes(optionIndex)) {
                            container.classList.add('was-selected');
                            const header = container.querySelector('.option-header');
                            if (header) header.classList.add('was-selected');
                        }
                    });

                    // Highlight code blocks with Prism
                    document.querySelectorAll('pre code').forEach(function(block) {
                        Prism.highlightElement(block);
                    });
                } catch (error) {
                    console.error('Error in highlightSelection:', error);
                }
            }

            // Build explanations and then highlight
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', () => {
                    buildAnswerContainers();
                    highlightSelection();
                });
            } else {
                buildAnswerContainers();
                highlightSelection();
            }
        </script>
        """

        # Add CSS - One Dark Pro theme with syntax highlighting
        m['css'] = """
        .card {
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 16px;
            line-height: 1.6;
            text-align: left;
            color: #abb2bf;
            background-color: #282c34;
            padding: 30px;
            max-width: 900px;
            margin: 0 auto;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
            border-radius: 12px;
        }

        /* Question styling */
        .question {
            margin-bottom: 30px;
            font-weight: 600;
            font-size: 1.3em;
            color: #e5c07b;
            line-height: 1.5;
            padding: 18px 20px;
            background-color: #2c313a;
            border-radius: 10px;
            border-left: 4px solid #d19a66;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            transition: all 0.3s ease;
        }
        
        /* Preview Container Styling */
        .preview-container {
            margin: 25px 0;
            border: 1px solid rgba(97, 175, 239, 0.3);
            border-radius: 10px;
            overflow: hidden;
            background-color: rgba(30, 34, 42, 0.6);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
        }
        
        .code-display {
            background-color: #21252b;
            padding: 15px;
            border-bottom: 1px solid rgba(97, 175, 239, 0.2);
        }
        
        .code-display h5 {
            color: #56b6c2;
            margin-top: 0;
            margin-bottom: 10px;
            font-size: 0.9em;
            font-weight: 600;
        }
        
        .preview-display {
            padding: 15px;
        }
        
        .preview-display h5 {
            color: #98c379;
            margin-top: 0;
            margin-bottom: 10px;
            font-size: 0.9em;
            font-weight: 600;
        }
        
        .preview-result {
            background-color: #fff;
            color: #000;
            border-radius: 8px;
            padding: 0;
            overflow: hidden;
            max-height: 400px;
        }
        
        .preview-result iframe {
            width: 100%;
            height: 300px;
            border: none;
            background-color: #fff;
            border-radius: 8px;
        }
        
        /* One Dark Pro Colors */
        .odp-background { background-color: #282C34; }
        .odp-black { color: #3F4451; }
        .odp-blue { color: #61afef; }
        .odp-brightBlack { color: #4F5666; }
        .odp-brightBlue { color: #4dc4ff; }
        .odp-brightCyan { color: #4cd1e0; }
        .odp-brightGreen { color: #a5e075; }
        .odp-brightPurple { color: #de73ff; }
        .odp-brightRed { color: #be5046; }
        .odp-brightWhite { color: #e6e6e6; }
        .odp-brightYellow { color: #e5c07b; }
        .odp-cursorColor { color: #528BFF; }
        .odp-cyan { color: #56b6c2; }
        .odp-foreground { color: #ABB2BF; }
        .odp-green { color: #98c379; }
        .odp-purple { color: #c678dd; }
        .odp-red { color: #e06c75; }
        .odp-selectionBackground { background-color: #ABB2BF; }
        .odp-white { color: #D7DAE0; }
        .odp-yellow { color: #d19a66; }
        
        /* Option styling */
        .option {
            margin: 15px 0;
            padding: 16px 20px;
            border: 1px solid rgba(62, 68, 81, 0.5);
            border-radius: 10px;
            cursor: pointer;
            display: flex;
            align-items: flex-start;
            transition: all 0.3s ease;
            background-color: rgba(44, 49, 58, 0.7);
            color: #abb2bf;
            line-height: 1.6;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }

        /* Explanation styling */
        .explanation {
            padding: 20px;
            margin: 15px 0;
            background-color: rgba(44, 49, 58, 0.7);
            border-radius: 10px;
            color: #abb2bf;
            line-height: 1.7;
            font-size: 1em;
            border-left: 4px solid transparent;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }

        /* New styles for markdown elements */
        .explanation ul, 
        .explanation ol {
            margin: 10px 0;
            padding-left: 25px;
        }

        .explanation li {
            margin: 8px 0;
            line-height: 1.6;
        }

        /* Global text formatting colors */
        .explanation del {
            color: #e06c75;
            text-decoration: line-through;
        }

        .explanation p {
            margin: 12px 0;
        }

        .explanation h1, 
        .explanation h2, 
        .explanation h3, 
        .explanation h4, 
        .explanation h5 {
            color: #61afef;
            margin: 20px 0 10px 0;
        }

        /* Code styling */
        pre {
            background-color: #21252b;
            padding: 15px;
            border-radius: 8px;
            overflow-x: auto;
            margin: 15px 0;
            border: 1px solid rgba(62, 68, 81, 0.5);
            box-shadow: inset 0 1px 8px rgba(0, 0, 0, 0.2);
        }

        code {
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 14px;
            color: #abb2bf;
        }

        /* Inline code */
        p code {
            background-color: #21252b;
            padding: 2px 5px;
            border-radius: 3px;
            border: 1px solid rgba(62, 68, 81, 0.5);
        }

        /* Code block specific styling */
        .code-block {
            background-color: #21252b;
            border-radius: 8px;
            margin: 15px 0;
            padding: 15px;
            overflow-x: auto;
            border: 1px solid rgba(62, 68, 81, 0.5);
            box-shadow: inset 0 1px 8px rgba(0, 0, 0, 0.2);
        }

        /* Syntax highlighting colors - One Dark Pro */
        .token.comment,
        .token.prolog,
        .token.doctype,
        .token.cdata {
            color: #5c6370;
        }

        .token.punctuation {
            color: #abb2bf;
        }

        .token.selector,
        .token.tag {
            color: #e06c75;
        }

        .token.property,
        .token.boolean,
        .token.number,
        .token.constant,
        .token.symbol,
        .token.attr-name,
        .token.deleted {
            color: #d19a66;
        }

        .token.string,
        .token.char,
        .token.attr-value,
        .token.builtin,
        .token.inserted {
            color: #98c379;
        }

        .token.operator,
        .token.entity,
        .token.url,
        .language-css .token.string,
        .style .token.string {
            color: #56b6c2;
        }

        .token.atrule,
        .token.keyword {
            color: #c678dd;
        }

        .token.function,
        .token.class-name {
            color: #61afef;
        }

        .token.regex,
        .token.important,
        .token.variable {
            color: #c678dd;
        }

        /* Option selection styling */
        .option:hover {
            background-color: rgba(58, 64, 75, 0.9);
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
            border-color: rgba(97, 175, 239, 0.3);
        }

        .option.selected {
            background-color: rgba(58, 64, 75, 0.9);
            border-color: #61afef;
            box-shadow: 0 0 0 1px #61afef, 0 4px 12px rgba(97, 175, 239, 0.2);
        }

        .option-checkbox {
            margin: 3px 15px 0 0;
            transform: scale(1.2);
        }

        /* Submit button styling */
        .submit-button {
            margin-top: 30px;
            padding: 12px 28px;
            background-color: #61afef;
            color: #282c34;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 16px;
            transition: all 0.3s ease;
            font-weight: 600;
            box-shadow: 0 4px 12px rgba(97, 175, 239, 0.3);
        }

        .submit-button:hover:not(:disabled) {
            background-color: #56b6c2;
            transform: translateY(-2px);
            box-shadow: 0 6px 16px rgba(86, 182, 194, 0.4);
        }

        .submit-button:disabled {
            background-color: #4b5263;
            cursor: not-allowed;
            color: #abb2bf;
            box-shadow: none;
        }

        /* Answer feedback styling */
        .explanation-container {
            margin: 25px 0;
            padding: 20px;
            border-radius: 10px;
            background-color: rgba(44, 49, 58, 0.7);
            border: 2px solid transparent;
            transition: all 0.3s ease;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        }

        .correct-answer {
            border-color: rgba(152, 195, 121, 0.7);
            background-color: rgba(152, 195, 121, 0.05);
        }

        .correct-answer .explanation {
            border-left-color: #98c379; /* Green border for correct explanations */
        }

        .incorrect-answer {
            border-color: rgba(224, 108, 117, 0.7);
            background-color: rgba(224, 108, 117, 0.05);
        }

        .incorrect-answer .explanation {
            border-left-color: #e06c75; /* Red border for incorrect explanations */
        }

        .was-selected {
            border-color: rgba(97, 175, 239, 0.7);
            box-shadow: 0 0 15px rgba(97, 175, 239, 0.2);
        }
        
        .was-selected .explanation {
            border-left-color: #61afef !important; /* Blue border for selected option's explanation (overrides other colors) */
        }

        /* Divider styling */
        hr {
            margin: 30px 0;
            border: none;
            height: 1px;
            background: linear-gradient(to right, transparent, rgba(62, 68, 81, 0.7), transparent);
        }

        .question-reference {
            font-style: italic;
            font-size: 0.85em;
            color: #7f8c98;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 1px solid rgba(62, 68, 81, 0.5);
            font-weight: 500;
            letter-spacing: 0.3px;
        }

        /* Modified bold text coloring based on answer type */
        .correct-answer .explanation strong {
            font-weight: bold;
        }

        .incorrect-answer .explanation strong {
            font-weight: bold;
        }

        /* Option header styling */
        .option-header {
            font-weight: bold;
            padding: 12px 15px;
            margin-bottom: 12px;
            border-radius: 6px;
            background-color: rgba(33, 37, 43, 0.8);
            color: #e5c07b;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }

        .option-header.was-selected {
            background-color: rgba(43, 75, 94, 0.8);
            color: #61afef;
            box-shadow: 0 2px 8px rgba(97, 175, 239, 0.2);
        }
        """

        # Add template to model
        mm.add_template(m, template)
        
        # Add the model to the collection
        mm.add(m)
        return m

def init():
    # Create default Recall12 card (1 correct, 2 incorrect options)
    create_recall_note_type(1, 2)
    

# Add the init hook
gui_hooks.profile_did_open.append(init) 