from aqt import mw
from aqt import gui_hooks
from aqt.qt import *
from anki.models import ModelManager
from anki.notes import Note
import re

class ExamInputDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
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
        self.input_text.setPlaceholderText("""Convert the following C# Doc
___

to this outline
___
......
##### Question 
[Insert question text here]
___
##### Correct Option
[Insert option text (70-90 words) here]

##### Explanation
[Insert detailed explanation of this option]
##### Code Example
```csharp

[Insert code example here]

```
___
##### Incorrect Option
[Insert option text (70-90 words) here]

##### Incorrect Option Explanation
**What reasoning lead to this incorrect answer:** [Insert a reason why this option might seem correct]
**Why the reasoning is wrong**: [Insert why reasoning is incorrect and correct it]
##### Code Example
```csharp

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

    def parse_input(self):
        text = self.input_text.toPlainText()
        
        # Parse sections using regex
        sections = {}
        
        # Skip the initial "Convert the following..." part
        text = text.split("___\n......\n", 1)[-1]
        
        # Extract question
        question_match = re.search(r'##### Question\s*\n(.*?)(?=\n___|\Z)', text, re.DOTALL)
        if question_match:
            sections['question'] = question_match.group(1).strip()
            
        # Extract correct option
        correct_match = re.search(r'##### Correct Option\s*\n(.*?)(?=\n##### Explanation|\n___|\Z)', text, re.DOTALL)
        if correct_match:
            sections['correct_option'] = correct_match.group(1).strip()
            
        # Extract correct explanation
        correct_exp_match = re.search(r'##### Explanation\s*\n(.*?)(?=\n##### Code Example|\n___|\Z)', text, re.DOTALL)
        if correct_exp_match:
            sections['correct_explanation'] = correct_exp_match.group(1).strip()
            
        # Extract correct code example
        correct_code_match = re.search(r'##### Code Example\s*\n```csharp\s*\n(.*?)```', text, re.DOTALL)
        if correct_code_match:
            sections['correct_code'] = correct_code_match.group(1).strip()
            
        # Extract incorrect options
        incorrect_sections = re.finditer(
            r'##### Incorrect Option\s*\n(.*?)\n\n##### Incorrect Option Explanation\s*\n' + 
            r'\*\*What reasoning lead to this incorrect answer:\*\* (.*?)\n' +
            r'\*\*Why the reasoning is wrong\*\*: (.*?)\n' +
            r'##### Code Example\s*\n```csharp\s*\n(.*?)```',
            text, re.DOTALL
        )
        
        sections['incorrect_options'] = []
        for match in incorrect_sections:
            option_text = match.group(1).strip()
            reasoning = match.group(2).strip()
            why_wrong = match.group(3).strip()
            code = match.group(4).strip()
            
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
            
            # Count correct and incorrect options
            correct_count = 1  # Since we're parsing one correct option
            incorrect_count = len(sections['incorrect_options'])
            
            # Create note
            model_name = f"ExamCard{correct_count}{incorrect_count}"
            model = mw.col.models.by_name(model_name)
            if not model:
                create_exam_note_type(correct_count, incorrect_count)
                model = mw.col.models.by_name(model_name)
                
            note = Note(mw.col, model)
            
            # Fill note fields
            note['Question'] = sections['question']
            note['CorrectOption'] = sections['correct_option']
            note['CorrectExplanation'] = sections['correct_explanation']
            note['CorrectCodeExample'] = sections['correct_code']
            
            for i, incorrect in enumerate(sections['incorrect_options'], 1):
                note[f'IncorrectOption{i}'] = incorrect['option']
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
            var selectedOption = null;
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
                        <input type="radio" name="option" id="radio${index}" class="option-radio">
                        <label>${content}</label>
                    </div>
                `;
            }

            function initializeOptions() {
                const options = [
                    { content: `{{CorrectOption}}`, isCorrect: true },
                    """ + ",\n".join([f"{{ content: `{{{{IncorrectOption{i + 1}}}}}`, isCorrect: false }}" for i in range(incorrect_options)]) + """
                ];

                const shuffledIndices = shuffleArray([""" + ", ".join(map(str, range(incorrect_options + 1))) + """]);
                
                const optionsContainer = document.getElementById('options');
                shuffledIndices.forEach((originalIndex, newIndex) => {
                    originalToShuffled[originalIndex] = newIndex;
                    shuffledToOriginal[newIndex] = originalIndex;
                    optionsContainer.innerHTML += createOption(newIndex, options[originalIndex].content);
                });

                document.body.setAttribute('data-option-mapping', JSON.stringify({
                    originalToShuffled,
                    shuffledToOriginal
                }));
            }

            function selectOption(index) {
                if (submitted) return;
                
                selectedOption = index;
                document.querySelectorAll('.option').forEach(opt => {
                    opt.classList.remove('selected');
                    opt.querySelector('input[type="radio"]').checked = false;
                });
                
                const selectedDiv = document.getElementById('option' + index);
                selectedDiv.classList.add('selected');
                selectedDiv.querySelector('input[type="radio"]').checked = true;
            }

            function submitAnswer() {
                if (submitted || selectedOption === null) return;
                submitted = true;
                
                const originalSelected = shuffledToOriginal[selectedOption];
                document.body.setAttribute('data-selected-option', originalSelected);
                
                document.getElementById('submit-btn').disabled = true;
                pycmd('ans');
            }

            if (!document.getElementById('answer')) {
                if (document.readyState === 'loading') {
                    document.addEventListener('DOMContentLoaded', initializeOptions);
                } else {
                    initializeOptions();
                }
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
            <div class="explanation-container correct-answer">
                <div class="option-header">Correct Answer: {{CorrectOption}}</div>
                <div class="explanation">{{CorrectExplanation}}</div>
                <div class="code-example">
                    <pre><code class="language-csharp">{{CorrectCodeExample}}</code></pre>
                </div>
            </div>

            """ + "\n".join([f"""
            <div class="explanation-container incorrect-answer">
                <div class="option-header">{{{{IncorrectOption{i + 1}}}}}</div>
                <div class="explanation">{{{{IncorrectExplanation{i + 1}}}}}</div>
                <div class="code-example">
                    <pre><code class="language-csharp">{{{{IncorrectCodeExample{i + 1}}}}}</code></pre>
                </div>
            </div>""" for i in range(incorrect_options)]) + """

        </div>

        <script>
            // Fix for line breaks in Prism
            Prism.hooks.add("before-highlight", function (env) {
                env.code = env.element.innerText;
            });

            function highlightSelection() {
                var selectedOption = parseInt(document.body.getAttribute('data-selected-option'));
                var containers = document.querySelectorAll('.explanation-container');
                
                if (selectedOption === 0) {
                    containers[0].classList.add('selected-correct');
                } else {
                    containers[selectedOption].classList.add('selected-incorrect');
                }
                
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
            font-family: arial;
            font-size: 20px;
            text-align: left;
            color: white;
            background-color: #2f2f2f;
            padding: 20px;
            max-width: 800px;
            margin: 0 auto;
        }

        .question {
            margin-bottom: 20px;
            font-weight: bold;
            font-size: 1.2em;
            color: white;
        }

        .option {
            margin: 10px 0;
            padding: 10px;
            border: 1px solid #ccc;
            border-radius: 5px;
            cursor: pointer;
            display: flex;
            align-items: center;
            transition: all 0.3s ease;
            background-color: #3f3f3f;
            color: white;
        }

        .option:hover {
            background-color: #4f4f4f;
        }

        .option.selected {
            background-color: #1a237e;
            border-color: #3949ab;
        }

        .submit-button {
            margin-top: 20px;
            padding: 10px 20px;
            background-color: #2196f3;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
        }

        .submit-button:disabled {
            background-color: #666;
            cursor: not-allowed;
        }

        .explanation-container {
            margin: 15px 0;
            padding: 15px;
            border-radius: 5px;
            background-color: #3f3f3f;
            color: white;
            border: 2px solid transparent;
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
            margin-bottom: 10px;
            padding: 10px;
            border-radius: 5px;
            background-color: rgba(255, 255, 255, 0.1);
        }

        .option-header.was-selected {
            background-color: #1a237e !important;
        }

        .explanation {
            padding: 15px;
            margin-top: 10px;
            background-color: rgba(0, 0, 0, 0.2);
            border-radius: 5px;
            color: #fff;
            line-height: 1.5;
        }

        hr {
            margin: 20px 0;
            border: none;
            border-top: 2px solid #666;
        }

        /* Code example styling with Prism.js compatibility */
        .code-example {
            margin: 10px 0;
            padding: 15px;
            background-color: #282C34;
            border-radius: 5px;
            overflow-x: auto;
            box-shadow: 0 2px 4px rgba(0,0,0,0.3);
        }

        .code-example pre {
            margin: 0;
            padding: 0;
            background: transparent;
            white-space: pre-wrap !important;
        }

        .code-example code {
            font-family: 'Fira Code', 'Consolas', monospace;
            font-size: 14px;
            line-height: 1.6;
            background: transparent;
            white-space: pre-wrap !important;
            color: #ABB2BF;
        }

        /* Syntax highlighting colors */
        .token.comment,
        .token.prolog,
        .token.doctype,
        .token.cdata {
            color: #5C6370 !important;
            font-style: italic !important;
        }

        .token.function {
            color: #61AFEF !important;
        }

        .token.class-name {
            color: #E5C07B !important;
        }

        .token.keyword {
            color: #C678DD !important;
        }

        .token.boolean,
        .token.number {
            color: #D19A66 !important;
        }

        .token.string {
            color: #98C379 !important;
        }

        .token.operator {
            color: #56B6C2 !important;
            background: none !important;
        }

        .token.punctuation {
            color: #ABB2BF !important;
        }

        .token.property {
            color: #E06C75 !important;
        }

        .token.tag {
            color: #E06C75 !important;
        }

        .token.attr-name {
            color: #D19A66 !important;
        }

        .token.attr-value {
            color: #98C379 !important;
        }

        /* Override Prism.js styles */
        code[class*="language-"],
        pre[class*="language-"] {
            color: #ABB2BF;
            background: transparent;
            text-shadow: none;
            font-family: 'Fira Code', 'Consolas', monospace;
            font-size: 14px;
            text-align: left;
            white-space: pre-wrap;
            word-spacing: normal;
            word-break: normal;
            word-wrap: break-word;
            line-height: 1.6;
            tab-size: 4;
            hyphens: none;
        }

        .selected-correct {
            border: 3px solid #4caf50 !important;
            background-color: #1b5e20 !important;
        }

        .selected-incorrect {
            border: 3px solid #f44336 !important;
            background-color: #b71c1c !important;
        }

        .option-radio {
            margin-right: 10px;
        }
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
    create_exam_note_type(1, 5)  # ExamCard14 (1 correct, 4 incorrect options)

# Add the init hook
gui_hooks.profile_did_open.append(init) 