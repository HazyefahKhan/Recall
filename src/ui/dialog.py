"""
Dialog UI for Recall Anki plugin.
"""

from aqt import mw
from aqt.qt import *
from anki.notes import Note
import re

from ..markdown.converter import convert_markdown_to_html, format_code_block
from ..card_templates.note_types import create_recall_note_type

class RecallInputDialog(QDialog):
    """Dialog for creating recall questions"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.load_last_deck()  # Load last selected deck
        
    def setup_ui(self):
        """Set up the UI components"""
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
        """Parse the input text into structured data for card creation."""
        text = self.input_text.toPlainText()
        
        # First, clean up any variations of the Explanation header
        text = re.sub(r'##### Explanation.*?\n', '##### Explanation\n', text)
        
        # STEP 1: Protect code blocks from interfering with section parsing
        # Store code blocks with placeholders to prevent regex confusion
        code_blocks = {}
        code_block_counter = 0
        
        def extract_code_blocks(match):
            nonlocal code_block_counter
            placeholder = f"__CODE_BLOCK_PLACEHOLDER_{code_block_counter}__"
            code_blocks[placeholder] = match.group(0)
            code_block_counter += 1
            return placeholder
        
        # Extract all code blocks (including those with nested backticks)
        # This pattern handles multi-line code blocks with any language specifier
        # Flexible pattern: optional whitespace after ```, optional language, flexible content
        code_block_pattern = r'```\s*(\w*)\s*([\s\S]*?)```'
        text_with_placeholders = re.sub(code_block_pattern, extract_code_blocks, text)
        
        # STEP 2: Extract main sections using the protected text
        sections = {}
        
        # Extract question section - now using protected text
        question_match = re.search(r'#### Question\s*\n([\s\S]*?)(?=\n(?:___|---)|\Z)', text_with_placeholders, re.DOTALL)
        if question_match:
            question_content = question_match.group(1).strip()
            
            # Restore code blocks in question content
            for placeholder, original in code_blocks.items():
                question_content = question_content.replace(placeholder, original)
            
            sections['question'] = question_content
            
            # Check for preview section in question using the original content
            # Updated regex to handle edge cases better with flexible code block pattern
            preview_regex = r'#### Preview\s*\n(```\s*\w*\s*[\s\S]*?```)'
            preview_match = re.search(preview_regex, question_content, re.DOTALL)
            
            if preview_match:
                full_code_block = preview_match.group(1)
                # Extract language and content from the code block with flexible pattern
                code_block_match = re.match(r'```\s*(\w*)\s*([\s\S]*?)```', full_code_block, re.DOTALL)
                if code_block_match:
                    language = code_block_match.group(1).lower().strip() if code_block_match.group(1) else 'html'
                    code_content = code_block_match.group(2).rstrip()  # Remove trailing whitespace but preserve internal structure
                    
                    sections['question_preview'] = {
                        'language': language,
                        'code': code_content
                    }
                    # For HTML/CSS/JS, we also want to specify the content for iframe rendering
                    if language in ['html', 'css', 'javascript', 'js']:
                        sections['question_preview']['html_to_render'] = code_content
        
        # Initialize option lists
        sections['correct_options'] = []
        sections['incorrect_options'] = []
        
        # STEP 3: Split by section markers using protected text
        # Find all section markers
        section_markers = list(re.finditer(r'\n(?:---|___)\n', text_with_placeholders))
        marker_positions = [m.start() for m in section_markers]
        
        # Add beginning and end positions
        marker_positions = [-1] + marker_positions + [len(text_with_placeholders)]
        
        # Extract sections between markers
        option_sections = []
        for i in range(len(marker_positions) - 1):
            start = marker_positions[i]
            end = marker_positions[i+1]
            
            # Skip the marker itself
            if start >= 0:
                start = marker_positions[i] + len(section_markers[i-1].group(0)) if i > 0 else start + 5
            else:
                start = 0
                
            section = text_with_placeholders[start:end].strip()
            
            # Only include sections that have option headers
            if section and ('#### Correct Option' in section or '#### Incorrect Option' in section):
                # Restore code blocks in this section
                for placeholder, original in code_blocks.items():
                    section = section.replace(placeholder, original)
                option_sections.append(section)
        
        # STEP 4: Parse each option section
        for section in option_sections:
            # Determine if this is a correct or incorrect option
            is_correct = '#### Correct Option' in section
            
            # Extract option text - be more careful about where explanation starts
            option_match = re.search(
                r'#### (?:Correct|Incorrect) Option\s*\n([\s\S]*?)(?=\n##### Explanation|\Z)',
                section, re.DOTALL
            )
            
            # Extract explanation text - be more careful about where preview starts
            explanation_match = re.search(
                r'##### Explanation\s*\n([\s\S]*?)(?=\n#### Preview|\Z)',
                section, re.DOTALL
            )
            
            # Extract preview if it exists - handle edge cases better
            preview_match = re.search(
                r'#### Preview\s*\n(```\s*\w*\s*[\s\S]*?```)',
                section, re.DOTALL
            )
            
            if option_match and explanation_match:
                option_text = option_match.group(1).strip()
                explanation_text = explanation_match.group(1).strip()
                
                option_preview_data = None
                if preview_match:
                    full_code_block = preview_match.group(1)
                    # Extract language and content from the code block with flexible pattern
                    code_block_match = re.match(r'```\s*(\w*)\s*([\s\S]*?)```', full_code_block, re.DOTALL)
                    if code_block_match:
                        language = code_block_match.group(1).lower().strip() if code_block_match.group(1) else 'html'
                        code_content = code_block_match.group(2).rstrip()  # Remove trailing whitespace
                        
                        option_preview_data = {
                            'language': language,
                            'code': code_content
                        }
                        # For HTML/CSS/JS, specify content for iframe rendering
                        if language in ['html', 'css', 'javascript', 'js']:
                            option_preview_data['html_to_render'] = code_content
                
                option_data = {
                    'option': option_text,
                    'explanation': explanation_text,
                    'preview_data': option_preview_data
                }
                
                if is_correct:
                    sections['correct_options'].append(option_data)
                else:
                    sections['incorrect_options'].append(option_data)
        
        # Validate that we have at least some content
        if not sections.get('question'):
            raise ValueError("No question section found. Please ensure your input starts with '#### Question'")
        
        if not sections['correct_options'] and not sections['incorrect_options']:
            raise ValueError("No option sections found. Please ensure you have at least one '#### Correct Option' or '#### Incorrect Option' section")
            
        return sections

    def create_card(self):
        """Create a new card based on the parsed input."""
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
                # Pass language, code, and html_to_render (if available)
                preview_html_content = self.create_general_preview_display_html(
                    preview_data['language'],
                    preview_data['code'],
                    preview_data.get('html_to_render') 
                )
                question_html += preview_html_content
            
            note['Question'] = question_html
            
            # Add correct options
            for i, correct in enumerate(sections['correct_options'], 1):
                suffix = str(i) if correct_count > 1 else ""
                
                # Convert option and explanation to HTML
                option_html = convert_markdown_to_html(correct['option'])
                explanation_html = convert_markdown_to_html(correct['explanation'])
                
                # Add preview HTML if it exists
                if correct.get('preview_data'):
                    preview_data = correct['preview_data']
                    # Create a custom preview HTML section
                    preview_html_content = self.create_general_preview_display_html(
                        preview_data['language'],
                        preview_data['code'],
                        preview_data.get('html_to_render')
                    )
                    # Append this to the explanation
                    explanation_html += preview_html_content
                
                note[f'CorrectOption{suffix}'] = option_html
                note[f'CorrectExplanation{suffix}'] = explanation_html
            
            # Add incorrect options
            for i, incorrect in enumerate(sections['incorrect_options'], 1):
                # Convert option and explanation to HTML
                option_html = convert_markdown_to_html(incorrect['option'])
                explanation_html = convert_markdown_to_html(incorrect['explanation'])
                
                # Add preview HTML if it exists
                if incorrect.get('preview_data'):
                    preview_data = incorrect['preview_data']
                    # Create a custom preview HTML section
                    preview_html_content = self.create_general_preview_display_html(
                        preview_data['language'],
                        preview_data['code'],
                        preview_data.get('html_to_render')
                    )
                    # Append this to the explanation
                    explanation_html += preview_html_content
                
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

    def create_general_preview_display_html(self, language, code, html_to_render_in_iframe=None):
        """Create a formatted HTML container for code display and optional rendered preview."""
        
        # Determine the title for the code block
        code_block_title = f"{language.upper() if language else 'Code'} Source:" if language.lower() in ['html', 'css', 'javascript', 'js'] and html_to_render_in_iframe else f"{language.upper() if language else 'Code'} Preview:"

        # Always include the code display part
        formatted_code = format_code_block(code, language)
        code_display_html = f'''
        <div class="code-display">
            <h5>{code_block_title}</h5>
            {formatted_code}
        </div>
        '''

        # If it's a web language and there's content to render, add the iframe preview
        if language.lower() in ['html', 'css', 'javascript', 'js'] and html_to_render_in_iframe:
            # Sanitize for iframe's srcdoc
            sanitized_html_for_iframe = html_to_render_in_iframe.replace('"', '&quot;')
            
            rendered_preview_html = f'''
            <div class="preview-display">
                <h5>Rendered Preview:</h5>
                <div class="preview-result">
                    <iframe srcdoc="{sanitized_html_for_iframe}" style="width:100%; height:300px; border:none;"></iframe>
                </div>
            </div>
            '''
            
            return f'''
            <!-- Preview HTML section for {language} -->
            <div class="preview-container">
                {code_display_html}
                {rendered_preview_html}
            </div>
            '''
        else:
            # For other languages, or if no specific iframe content, just show the code
            return f'''
            <!-- Preview Code section for {language} -->
            <div class="preview-container-code-only">
                {code_display_html}
            </div>
            '''

def show_recall_input_dialog():
    """Show the recall input dialog."""
    dialog = RecallInputDialog(mw)
    dialog.exec() 