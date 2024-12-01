from aqt import mw
from aqt import gui_hooks
from aqt.qt import *
from anki.models import ModelManager
from anki.notes import Note

def init_mcq_note_type():
    # Check if our note type already exists
    model_name = "MCQ Card"
    if model_name not in mw.col.models.all_names():
        # Create the note type
        mm = mw.col.models
        m = mm.new(model_name)
        
        # Add fields
        for field_name in [
            "Question",
            "OptionA",
            "OptionB",
            "OptionC",
            "OptionD",
            "CorrectOptions",
            "CorrectExplanations",
            "IncorrectOptions",
            "IncorrectExplanations",
            "SelectedOptions"
        ]:
            field = mm.new_field(field_name)
            mm.add_field(m, field)

        # Add templates
        template = mm.new_template("MCQ Card")
        template['qfmt'] = """
        <div class="question">{{Question}}</div>
        <div class="options" id="options">
            <div class="option" onclick="toggleOption('A')" id="optionA">
                <input type="checkbox" id="checkA" class="option-check">
                <label>A. {{OptionA}}</label>
            </div>
            <div class="option" onclick="toggleOption('B')" id="optionB">
                <input type="checkbox" id="checkB" class="option-check">
                <label>B. {{OptionB}}</label>
            </div>
            <div class="option" onclick="toggleOption('C')" id="optionC">
                <input type="checkbox" id="checkC" class="option-check">
                <label>C. {{OptionC}}</label>
            </div>
            <div class="option" onclick="toggleOption('D')" id="optionD">
                <input type="checkbox" id="checkD" class="option-check">
                <label>D. {{OptionD}}</label>
            </div>
        </div>
        <button onclick="submitAnswer()" id="submit-btn" class="submit-button">Submit</button>
        <script>
            // Store selected options
            var selectedOptions = new Set();
            var submitted = false;

            // Toggle option selection
            function toggleOption(option) {
                if (submitted) return;  // Prevent changes after submission
                
                var checkbox = document.getElementById('check' + option);
                var optionDiv = document.getElementById('option' + option);
                
                if (selectedOptions.has(option)) {
                    selectedOptions.delete(option);
                    checkbox.checked = false;
                    optionDiv.classList.remove('selected');
                } else {
                    selectedOptions.add(option);
                    checkbox.checked = true;
                    optionDiv.classList.add('selected');
                }
            }

            // Submit answer
            function submitAnswer() {
                if (submitted) return;
                submitted = true;
                
                // Store selections in the hidden field
                var selections = Array.from(selectedOptions).join(',');
                document.getElementById('selected-options').value = selections;
                
                // Disable further selections
                document.getElementById('submit-btn').disabled = true;
                
                // Show answer
                pycmd('ans');
            }

            // Initialize from previous selections if they exist
            document.addEventListener('DOMContentLoaded', function() {
                var savedSelections = '{{SelectedOptions}}'.split(',');
                if (savedSelections[0] !== '') {
                    savedSelections.forEach(function(option) {
                        toggleOption(option.trim());
                    });
                }
            });
        </script>
        <input type="hidden" id="selected-options" name="selected-options">
        """
        template['afmt'] = """
        {{FrontSide}}
        <hr id="answer">
        <div class="answer">
            <div class="correct-options">
                <h3>Correct Options:</h3>
                {{CorrectOptions}}
            </div>
            <div class="explanations">
                <h3>Explanations:</h3>
                {{CorrectExplanations}}
            </div>
        </div>
        <script>
            // Highlight correct and incorrect answers after submission
            document.addEventListener('DOMContentLoaded', function() {
                var correctAnswers = '{{CorrectOptions}}'.split(',').map(s => s.trim());
                var selected = document.getElementById('selected-options').value.split(',');
                
                correctAnswers.forEach(function(option) {
                    var optionDiv = document.getElementById('option' + option);
                    if (optionDiv) {
                        optionDiv.classList.add('correct');
                    }
                });
                
                selected.forEach(function(option) {
                    if (!correctAnswers.includes(option)) {
                        var optionDiv = document.getElementById('option' + option);
                        if (optionDiv) {
                            optionDiv.classList.add('incorrect');
                        }
                    }
                });
            });
        </script>
        """
        mm.add_template(m, template)

        # Add CSS
        m['css'] = """
        .card {
            font-family: arial;
            font-size: 20px;
            text-align: left;
            color: black;
            background-color: white;
            padding: 20px;
        }

        .question {
            margin-bottom: 20px;
            font-weight: bold;
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
        }

        .option:hover {
            background-color: #f0f0f0;
        }

        .option.selected {
            background-color: #e3f2fd;
            border-color: #2196f3;
        }

        .option.correct {
            background-color: #e8f5e9;
            border-color: #4caf50;
        }

        .option.incorrect {
            background-color: #ffebee;
            border-color: #f44336;
        }

        .option-check {
            margin-right: 10px;
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
            background-color: #ccc;
            cursor: not-allowed;
        }

        .correct-options {
            border: 2px solid #4caf50;
            padding: 10px;
            margin: 10px 0;
            border-radius: 5px;
        }

        .explanations {
            border: 2px solid #2196f3;
            padding: 10px;
            margin: 10px 0;
            border-radius: 5px;
        }
        """
        
        mm.add(m)
        return m

# Initialize the plugin
def init():
    init_mcq_note_type()

# Add the init hook
gui_hooks.profile_did_open.append(init) 