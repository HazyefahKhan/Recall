from aqt import mw
from aqt import gui_hooks
from aqt.qt import *
from anki.models import ModelManager
from anki.notes import Note
from anki.utils import html_to_text_line
import re
import markdown

def convert_markdown_to_html(text):
    """Convert markdown text to HTML with proper formatting."""
    # Convert markdown to HTML using Anki's built-in markdown
    html = markdown.markdown(text)
    
    # Remove paragraph tags around the text (Anki adds its own)
    html = re.sub(r'^\s*<p>(.*?)</p>\s*$', r'\1', html, flags=re.DOTALL)
    
    # Convert code blocks to match Anki's styling
    html = re.sub(
        r'<pre><code>(.*?)</code></pre>',
        lambda m: f'<div class="code-example"><pre><code>{m.group(1)}</code></pre></div>',
        html,
        flags=re.DOTALL
    )
    
    return html

class ExamInputDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.load_last_deck()  # Load last selected deck
        
    def setup_ui(self):
        self.setWindowTitle("Create Exam Question")
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
[Insert option text (70-90 words) here]

##### Explanation
[Insert detailed explanation of this option]
##### Code Example
```
[Insert code example here]
```
___
#### Incorrect Option
[Insert option text (70-90 words) here]

##### Incorrect Option Explanation
###### What reasoning lead to this incorrect answer
[Insert a reason why this option might seem correct compared to the actual correct option and make sure it is an actual reasonable reason to think this was the correct option]

###### Why the reasoning is wrong
[Insert why reasoning is incorrect and correct it]
##### Code Example
```
[Insert code example here]
```
___
#### Incorrect Option
[Insert option text (70-90 words) here]
##### Incorrect Option Explanation
###### What reasoning lead to this incorrect answer
[Insert a reason why this option might seem correct compared to the actual correct option and make sure it is an actual reasonable reason to think this was the correct option]
###### Why the reasoning is wrong
[Insert why reasoning is incorrect and correct it]
##### Code Example
```
[Insert code example here]
```
___
#### Incorrect Option
[Insert option text (70-90 words) here]
##### Incorrect Option Explanation
###### Why reasoning lead to this incorrect answer
[Insert a reason why this option might seem correct compared to the actual correct option and make sure it is an actual reasonable reason to think this was the correct option]

###### Why the reasoning is wrong
[Insert why reasoning is incorrect and correct it]
##### Code Example
```
[Insert code example here]
```
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
        last_deck_id = mw.pm.profile.get('exam_simulator_last_deck', None)
        if last_deck_id is not None:
            # Find the index of the last used deck in the combo box
            index = self.deck_combo.findData(last_deck_id)
            if index >= 0:
                self.deck_combo.setCurrentIndex(index)

    def save_last_deck(self):
        """Save the currently selected deck ID to Anki's configuration."""
        deck_id = self.deck_combo.currentData()
        mw.pm.profile['exam_simulator_last_deck'] = deck_id

    def parse_input(self):
        text = self.input_text.toPlainText()
        
        # Parse sections using regex
        sections = {}
        
        # Extract question
        question_match = re.search(r'#### Question\s*\n(.*?)(?=\n___|\Z)', text, re.DOTALL)
        if question_match:
            sections['question'] = question_match.group(1).strip()
        
        # Initialize correct options list
        sections['correct_options'] = []
        
        # Find all correct options sections
        correct_sections = re.finditer(
            r'#### Correct Option:?\s*(?:[A-Z]\.\s*)?([^\n]+)\s*\n\n?' +  # Option text with optional letter prefix
            r'##### Explanation\s*\n(.*?)(?=\n##### Code Example|\n---|\n___|\Z)\s*' +  # Explanation
            r'(?:##### Code Example\s*\n```(?:\w+)?\s*\n(.*?)```\s*(?=\n---|\n___|\Z))?',  # Optional code example
            text, re.DOTALL
        )
        
        for match in correct_sections:
            option_text = match.group(1).strip()
            explanation = match.group(2).strip()
            code = match.group(3).strip() if match.group(3) else ""
            
            sections['correct_options'].append({
                'option': option_text,
                'explanation': explanation,
                'code': code
            })
        
        # If no correct options found with new format, try old format
        if not sections['correct_options']:
            old_format_match = re.search(
                r'#### Correct Option\s*\n(.*?)\n\n?' +
                r'##### Explanation\s*\n(.*?)(?=\n##### Code Example|\n___|\Z)\s*' +
                r'(?:##### Code Example\s*\n```(?:\w+)?\s*\n(.*?)```)?',
                text, re.DOTALL
            )
            if old_format_match:
                sections['correct_options'].append({
                    'option': old_format_match.group(1).strip(),
                    'explanation': old_format_match.group(2).strip(),
                    'code': old_format_match.group(3).strip() if old_format_match.group(3) else ""
                })
        
        # Extract incorrect options with updated pattern for optional code blocks
        incorrect_sections = re.finditer(
            r'#### Incorrect Option:?\s*(?:[A-Z]\.\s*)?([^\n]+)\s*\n\n?' +  # Option text with optional letter prefix
            r'##### Incorrect Option Explanation\s*\n' +  # Explanation header
            r'###### (?:What|Why) reasoning lead(?:s|ed)? to this incorrect answer\s*\n(.*?)\n\n?' +  # Reasoning
            r'###### Why the reasoning is wrong(?:\s*\[.*?\])?\s*\n(.*?)' +  # Why wrong
            r'(?:\n##### Code Example\s*\n```(?:\w+)?\s*\n(.*?)```|\n---|\n___|\Z)',  # Optional code example
            text, re.DOTALL
        )
        
        sections['incorrect_options'] = []
        for match in incorrect_sections:
            option_text = match.group(1).strip()
            reasoning = match.group(2).strip()
            why_wrong = match.group(3).strip()
            code = match.group(4).strip() if len(match.groups()) > 3 and match.group(4) else ""
            
            explanation = f"<b>What reasoning lead to this incorrect answer:</b> {reasoning}<br><br>" + \
                         f"<b>Why the reasoning is wrong</b>: {why_wrong}"
            
            sections['incorrect_options'].append({
                'option': option_text,
                'explanation': explanation,
                'code': code
            })

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
            
            # Create note
            model_name = f"ExamCard{correct_count}{incorrect_count}"
            model = mw.col.models.by_name(model_name)
            if not model:
                create_exam_note_type(correct_count, incorrect_count)
                model = mw.col.models.by_name(model_name)
                
            note = Note(mw.col, model)
            
            # Fill note fields with converted HTML
            note['Question'] = convert_markdown_to_html(sections['question'])
            
            # Add correct options
            for i, correct in enumerate(sections['correct_options'], 1):
                suffix = str(i) if correct_count > 1 else ""
                note[f'CorrectOption{suffix}'] = convert_markdown_to_html(correct['option'])
                note[f'CorrectExplanation{suffix}'] = convert_markdown_to_html(correct['explanation'])
                note[f'CorrectCodeExample{suffix}'] = correct['code']
            
            # Add incorrect options
            for i, incorrect in enumerate(sections['incorrect_options'], 1):
                note[f'IncorrectOption{i}'] = convert_markdown_to_html(incorrect['option'])
                note[f'IncorrectExplanation{i}'] = incorrect['explanation']
                note[f'IncorrectCodeExample{i}'] = incorrect['code']
            
            # Add note to selected deck
            mw.col.add_note(note, deck_id)
            mw.reset()
            
            QMessageBox.information(self, "Success", f"Card created successfully with {correct_count} correct and {incorrect_count} incorrect options!")
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create card: {str(e)}")

def show_exam_input_dialog():
    dialog = ExamInputDialog(mw)
    dialog.exec()

# Add menu item
action = QAction("Create Exam Question", mw)
action.triggered.connect(show_exam_input_dialog)
action.setShortcut(QKeySequence("Ctrl+Shift+E"))  # Add keyboard shortcut
mw.form.menuTools.addAction(action)

def create_exam_note_type(correct_options, incorrect_options):
    """Create an exam note type with code examples.
    
    Args:
        correct_options (int): Number of correct options
        incorrect_options (int): Number of incorrect options
    """
    model_name = f"ExamCard{correct_options}{incorrect_options}"
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
                f"CorrectExplanation{suffix}",
                f"CorrectCodeExample{suffix}"
            ])
        
        # Add incorrect options fields
        for i in range(incorrect_options):
            fields.extend([
                f"IncorrectOption{i + 1}",
                f"IncorrectExplanation{i + 1}",
                f"IncorrectCodeExample{i + 1}"
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
        <div class="answer">
            """ + "\n".join([f"""
            <div class="explanation-container correct-answer">
                <div class="option-header">Correct Answer: {{{{CorrectOption{str(i + 1) if correct_options > 1 else ''}}}}}</div>
                <div class="explanation">{{{{CorrectExplanation{str(i + 1) if correct_options > 1 else ''}}}}}</div>
                <div class="code-example">
                    <pre><code>{{{{CorrectCodeExample{str(i + 1) if correct_options > 1 else ''}}}}}</code></pre>
                </div>
            </div>""" for i in range(correct_options)]) + """

            """ + "\n".join([f"""
            <div class="explanation-container incorrect-answer">
                <div class="option-header">{{{{IncorrectOption{i + 1}}}}}</div>
                <div class="explanation">{{{{IncorrectExplanation{i + 1}}}}}</div>
                <div class="code-example">
                    <pre><code>{{{{IncorrectCodeExample{i + 1}}}}}</code></pre>
                </div>
            </div>""" for i in range(incorrect_options)]) + """

        </div>

        <script>
            // Fix for line breaks in Prism
            Prism.hooks.add("before-highlight", function (env) {
                env.code = env.element.innerText;
            });

            function highlightSelection() {
                var selectedOptionsStr = document.body.getAttribute('data-selected-options');
                var selectedOptions = JSON.parse(selectedOptionsStr);
                var containers = document.querySelectorAll('.explanation-container');
                
                selectedOptions.forEach(selectedOption => {
                    if (selectedOption < """ + str(correct_options) + """) {
                        containers[selectedOption].classList.add('selected-correct');
                    } else {
                        containers[selectedOption].classList.add('selected-incorrect');
                    }
                });
                
                // Initialize Prism.js highlighting for all code blocks
                document.querySelectorAll('code').forEach(function(code) {
                    Prism.highlightElement(code);
                });
            }

            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', highlightSelection);
            } else {
                highlightSelection();
            }
        </script>
        """

        # Add CSS
        m['css'] = """
        .card {
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 16px;
            line-height: 1.6;
            text-align: left;
            color: white;
            background-color: #2f2f2f;
            padding: 30px;
            max-width: 900px;
            margin: 0 auto;
        }

        .question {
            margin-bottom: 30px;
            font-weight: bold;
            font-size: 1.3em;
            color: white;
            line-height: 1.5;
            padding: 15px;
            background-color: rgba(255, 255, 255, 0.1);
            border-radius: 8px;
        }

        .option {
            margin: 15px 0;
            padding: 15px 20px;
            border: 1px solid #ccc;
            border-radius: 8px;
            cursor: pointer;
            display: flex;
            align-items: flex-start;
            transition: all 0.3s ease;
            background-color: #3f3f3f;
            color: white;
            line-height: 1.6;
        }

        .option:hover {
            background-color: #4f4f4f;
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        }

        .option.selected {
            background-color: #1a237e;
            border-color: #3949ab;
        }

        .submit-button {
            margin-top: 30px;
            padding: 12px 25px;
            background-color: #2196f3;
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 16px;
            transition: all 0.3s ease;
        }

        .submit-button:hover:not(:disabled) {
            background-color: #1976d2;
            transform: translateY(-2px);
        }

        .submit-button:disabled {
            background-color: #666;
            cursor: not-allowed;
        }

        .explanation-container {
            margin: 25px 0;
            padding: 20px;
            border-radius: 8px;
            background-color: #3f3f3f;
            color: white;
            border: 2px solid transparent;
            line-height: 1.6;
        }

        .correct-answer {
            border: 2px solid #4caf50 !important;
            background-color: #1b5e20 !important;
        }

        .incorrect-answer {
            border: 2px solid #f44336 !important;
            background-color: #b71c1c !important;
        }

        .option-header {
            font-weight: bold;
            margin-bottom: 15px;
            padding: 12px 15px;
            border-radius: 8px;
            background-color: rgba(255, 255, 255, 0.1);
            font-size: 1.1em;
        }

        .option-header.was-selected {
            background-color: #1a237e !important;
        }

        .explanation {
            padding: 20px;
            margin: 15px 0;
            background-color: rgba(0, 0, 0, 0.2);
            border-radius: 8px;
            color: #fff;
            line-height: 1.7;
            font-size: 1em;
        }

        .explanation b {
            color: #90caf9;
            display: block;
            margin: 15px 0 8px 0;
            font-size: 1.1em;
        }

        hr {
            margin: 30px 0;
            border: none;
            border-top: 2px solid #666;
        }

        /* Code example styling */
        .code-example {
            margin: 20px 0;
            padding: 20px;
            background-color: #282C34;
            border-radius: 8px;
            overflow-x: auto;
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        }

        .code-example pre {
            margin: 0;
            padding: 0;
            background: transparent;
            white-space: pre-wrap !important;
        }

        .code-example code {
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 14px;
            line-height: 1.6;
            background: transparent;
            white-space: pre-wrap !important;
            color: #ABB2BF;
        }

        .selected-correct {
            border: 3px solid #4caf50 !important;
            background-color: #1b5e20 !important;
        }

        .selected-incorrect {
            border: 3px solid #f44336 !important;
            background-color: #b71c1c !important;
        }

        .option-checkbox {
            margin: 3px 15px 0 0;
            transform: scale(1.2);
        }

        /* Language-specific syntax highlighting */
        .language-csharp .keyword { color: #569CD6; }
        .language-csharp .string { color: #CE9178; }
        .language-csharp .function { color: #DCDCAA; }
        .language-csharp .class-name { color: #4EC9B0; }
        .language-csharp .comment { color: #6A9955; }
        .language-csharp .number { color: #B5CEA8; }
        .language-csharp .operator { color: #D4D4D4; }
        """

        # Add template to model
        mm.add_template(m, template)
        
        # Add the model to the collection
        mm.add(m)
        return m

def init():
    # Create exam card types
    create_exam_note_type(1, 3)  # ExamCard13 (1 correct, 3 incorrect options)
    create_exam_note_type(1, 4)  # ExamCard14 (1 correct, 4 incorrect options)
    create_exam_note_type(1, 5)  # ExamCard15 (1 correct, 5 incorrect options)
    create_exam_note_type(2, 3)  # ExamCard23 (2 correct, 3 incorrect options)
    create_exam_note_type(3, 2)  # ExamCard32 (3 correct, 2 incorrect options)

# Add the init hook
gui_hooks.profile_did_open.append(init) 