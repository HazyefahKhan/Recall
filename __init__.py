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
            "CorrectOptions"
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
                
                // Store selected options in a data attribute for the answer side
                document.body.setAttribute('data-selected-options', Array.from(selectedOptions).join(','));
                
                // Disable further selections
                document.getElementById('submit-btn').disabled = true;
                
                // Show answer
                pycmd('ans');
            }
        </script>
        """
        template['afmt'] = """
        {{FrontSide}}
        <hr id="answer">
        <div class="answer">
            <div class="options-explanations">
                <div id="optionAExplanation" class="option-explanation">
                    <div class="option-header">A. {{OptionA}}</div>
                    <div class="explanation">{{ExplanationA}}</div>
                </div>
                
                <div id="optionBExplanation" class="option-explanation">
                    <div class="option-header">B. {{OptionB}}</div>
                    <div class="explanation">{{ExplanationB}}</div>
                </div>
                
                <div id="optionCExplanation" class="option-explanation">
                    <div class="option-header">C. {{OptionC}}</div>
                    <div class="explanation">{{ExplanationC}}</div>
                </div>
                
                <div id="optionDExplanation" class="option-explanation">
                    <div class="option-header">D. {{OptionD}}</div>
                    <div class="explanation">{{ExplanationD}}</div>
                </div>
            </div>
        </div>
        <script>
            // Function to check if an option is correct
            function isCorrectAnswer(option) {
                var correctAnswers = '{{CorrectOptions}}'.split(',').map(s => s.trim());
                return correctAnswers.includes(option);
            }

            // Apply colors and show selections
            function applyColorsAndSelections() {
                var selectedOptions = (document.body.getAttribute('data-selected-options') || '').split(',');
                
                ['A', 'B', 'C', 'D'].forEach(function(option) {
                    var explanationDiv = document.getElementById('option' + option + 'Explanation');
                    var headerDiv = explanationDiv.querySelector('.option-header');
                    
                    if (explanationDiv) {
                        // Apply correct/incorrect colors
                        if (isCorrectAnswer(option)) {
                            explanationDiv.classList.add('correct-answer');
                        } else {
                            explanationDiv.classList.add('incorrect-answer');
                        }
                        
                        // Show selection by adding blue background to header
                        if (selectedOptions.includes(option)) {
                            headerDiv.classList.add('was-selected');
                        }
                    }
                });
            }

            // Call when DOM is loaded
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', applyColorsAndSelections);
            } else {
                applyColorsAndSelections();
            }
        </script>
        """
        mm.add_template(m, template)

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
            background-color: #666;
            cursor: not-allowed;
        }

        .options-explanations {
            margin-top: 20px;
        }

        .option-explanation {
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
        """
        
        mm.add(m)
        return m

# Initialize the plugin
def init():
    init_mcq_note_type()

# Add the init hook
gui_hooks.profile_did_open.append(init) 