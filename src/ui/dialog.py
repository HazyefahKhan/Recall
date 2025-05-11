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
        
        # Parse sections using regex
        sections = {}
        
        # Extract question
        question_match = re.search(r'#### Question\s*\n(.*?)(?=\n(?:___|---)|\Z)', text, re.DOTALL)
        if question_match:
            sections['question'] = question_match.group(1).strip()
            
            # Check for preview section in question
            # Regex to capture language type and code block
            preview_regex = r'#### Preview\s*\n```(\w*)\s*([\s\S]*?)\s*```'
            preview_match = re.search(preview_regex, question_match.group(1), re.DOTALL)
            
            if preview_match:
                language = preview_match.group(1).lower().strip() if preview_match.group(1) else 'html' # Default to html if no lang specified
                code_content = preview_match.group(2).strip()
                
                sections['question_preview'] = {
                    'language': language,
                    'code': code_content
                }
                # For HTML/CSS/JS, we also want to specify the content for iframe rendering
                if language in ['html', 'css', 'javascript', 'js']:
                    sections['question_preview']['html_to_render'] = code_content
        
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
                r'#### Preview\s*\n```(\w*)\s*([\s\S]*?)\s*```',
                section, re.DOTALL
            )
            
            if option_match and explanation_match:
                option_text = option_match.group(2).strip()
                explanation_text = explanation_match.group(1).strip()
                
                option_preview_data = None
                if preview_match:
                    language = preview_match.group(1).lower().strip() if preview_match.group(1) else 'html' # Default to html
                    code_content = preview_match.group(2).strip()
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
                    'preview_data': option_preview_data # Changed from preview_code/preview_html
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