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
            "ExplanationA",
            "OptionB",
            "ExplanationB",
            "OptionC",
            "ExplanationC",
            "OptionD",
            "ExplanationD",
            "CorrectOptions",
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
                savedSelections.forEach(function(option) {
                    if (option.trim() !== '') {
                        selectedOptions.add(option.trim());
                        var checkbox = document.getElementById('check' + option.trim());
                        var optionDiv = document.getElementById('option' + option.trim());
                        if (checkbox && optionDiv) {
                            checkbox.checked = true;
                            optionDiv.classList.add('selected');
                        }
                    }
                });
            });
        </script>
        <input type="hidden" id="selected-options" name="selected-options" value="{{SelectedOptions}}">
        """
        template['afmt'] = """
        {{FrontSide}}
        <hr id="answer">
        <div class="answer">
            <div class="options-explanations">
                <div id="optionAExplanation" class="option-explanation">
                    <div class="option-text">A. {{OptionA}}</div>
                    <div class="explanation">
                        <strong>Explanation:</strong><br>
                        {{ExplanationA}}
                    </div>
                </div>
                
                <div id="optionBExplanation" class="option-explanation">
                    <div class="option-text">B. {{OptionB}}</div>
                    <div class="explanation">
                        <strong>Explanation:</strong><br>
                        {{ExplanationB}}
                    </div>
                </div>
                
                <div id="optionCExplanation" class="option-explanation">
                    <div class="option-text">C. {{OptionC}}</div>
                    <div class="explanation">
                        <strong>Explanation:</strong><br>
                        {{ExplanationC}}
                    </div>
                </div>
                
                <div id="optionDExplanation" class="option-explanation">
                    <div class="option-text">D. {{OptionD}}</div>
                    <div class="explanation">
                        <strong>Explanation:</strong><br>
                        {{ExplanationD}}
                    </div>
                </div>
            </div>
            
            <div class="correct-answers">
                <h3>Correct Answer(s):</h3>
                <div class="correct-options">{{CorrectOptions}}</div>
            </div>
        </div>
        <script>
            document.addEventListener('DOMContentLoaded', function() {
                var correctAnswers = '{{CorrectOptions}}'.split(',').map(s => s.trim());
                var selected = '{{SelectedOptions}}'.split(',').map(s => s.trim());
                
                // Process all options
                ['A', 'B', 'C', 'D'].forEach(function(option) {
                    var optionDiv = document.getElementById('option' + option);
                    var explanationDiv = document.getElementById('option' + option + 'Explanation');
                    
                    if (correctAnswers.includes(option)) {
                        // Correct answer
                        optionDiv.classList.add('correct');
                        explanationDiv.classList.add('correct-explanation');
                    } else {
                        // Incorrect answer
                        optionDiv.classList.add('incorrect');
                        explanationDiv.classList.add('incorrect-explanation');
                    }
                    
                    // Mark selected options
                    if (selected.includes(option)) {
                        optionDiv.classList.add('selected');
                        var checkbox = document.getElementById('check' + option);
                        if (checkbox) {
                            checkbox.checked = true;
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
            max-width: 800px;
            margin: 0 auto;
        }

        .question {
            margin-bottom: 20px;
            font-weight: bold;
            font-size: 1.2em;
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

        .options-explanations {
            margin-top: 20px;
        }

        .option-explanation {
            margin: 15px 0;
            padding: 15px;
            border-radius: 5px;
            border: 1px solid #ccc;
        }

        .correct-explanation {
            border-color: #4caf50;
            background-color: #f1f8e9;
        }

        .incorrect-explanation {
            border-color: #f44336;
            background-color: #ffebee;
        }

        .option-text {
            font-weight: bold;
            margin-bottom: 10px;
        }

        .explanation {
            padding: 10px;
            border-left: 3px solid #2196f3;
            background-color: #f5f5f5;
            margin-top: 10px;
        }

        .correct-answers {
            margin-top: 20px;
            padding: 15px;
            border: 2px solid #4caf50;
            border-radius: 5px;
            background-color: #f1f8e9;
        }

        h3 {
            margin: 0 0 10px 0;
            color: #333;
        }

        hr {
            margin: 20px 0;
            border: none;
            border-top: 2px solid #ccc;
        }
        """
        
        mm.add(m)
        return m

# Initialize the plugin
def init():
    init_mcq_note_type()

# Add the init hook
gui_hooks.profile_did_open.append(init) 