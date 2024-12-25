from aqt import mw
from aqt import gui_hooks
from aqt.qt import *
from anki.models import ModelManager
from anki.notes import Note

def create_mcq_note_type(num_options, model_name):
    """Create an MCQ note type with the specified number of options."""
    if model_name not in mw.col.models.all_names():
        mm = mw.col.models
        m = mm.new(model_name)
        
        # Add Question field
        mm.add_field(m, mm.new_field("Question"))
        
        # Add option and explanation fields
        letters = [chr(65 + i) for i in range(num_options)]  # A, B, C, etc.
        for letter in letters:
            mm.add_field(m, mm.new_field(f"Option{letter}"))
            mm.add_field(m, mm.new_field(f"Explanation{letter}"))
        
        # Add CorrectOptions field
        mm.add_field(m, mm.new_field("CorrectOptions"))

        # Create front template with dynamic options
        options_html = ""
        for letter in letters:
            options_html += f"""
                <div class="option" onclick="toggleOption('{letter}')" id="option{letter}" data-original="{letter}">
                    <input type="checkbox" id="check{letter}" class="option-check">
                    <label>{{{{Option{letter}}}}}</label>
                </div>"""

        # Create explanations HTML for the back template
        explanations_html = ""
        for letter in letters:
            explanations_html += f"""
                <div id="option{letter}Explanation" class="option-explanation">
                    <div class="option-header">{{{{Option{letter}}}}}</div>
                    <div class="explanation">{{{{Explanation{letter}}}}}</div>
                </div>"""

        # Create template
        template = mm.new_template(model_name)
        template['qfmt'] = f"""
        <div class="question">{{{{Question}}}}</div>
        <div id="options" class="options"></div>
        <button onclick="submitAnswer()" id="submit-btn" class="submit-button">Submit</button>

        <script>
            // Store selected options and original option mapping
            var selectedOptions = new Set();
            var submitted = false;
            var originalToShuffled = {{}};
            var shuffledToOriginal = {{}};

            // Fisher-Yates shuffle algorithm
            function shuffleArray(array) {{
                for (let i = array.length - 1; i > 0; i--) {{
                    const j = Math.floor(Math.random() * (i + 1));
                    [array[i], array[j]] = [array[j], array[i]];
                }}
                return array;
            }}

            // Create option element
            function createOption(letter, content) {{
                return `
                    <div class="option" onclick="toggleOption('${{letter}}')" id="option${{letter}}" data-original="${{letter}}">
                        <input type="checkbox" id="check${{letter}}" class="option-check">
                        <label>${{content}}</label>
                    </div>
                `;
            }}

            // Initialize options in random order
            function initializeOptions() {{
                const options = [
                    {', '.join([f"{{ letter: '{letter}', content: `{{{{Option{letter}}}}}` }}" for letter in letters])}
                ];

                // Create shuffled indices
                const shuffledIndices = shuffleArray([{', '.join(map(str, range(num_options)))}]);
                const letters = [{', '.join([f"'{letter}'" for letter in letters])}];
                
                // Create mappings
                shuffledIndices.forEach((originalIndex, newIndex) => {{
                    originalToShuffled[letters[originalIndex]] = letters[newIndex];
                    shuffledToOriginal[letters[newIndex]] = letters[originalIndex];
                }});

                // Create options HTML
                const optionsContainer = document.getElementById('options');
                shuffledIndices.forEach((originalIndex, newIndex) => {{
                    const option = options[originalIndex];
                    optionsContainer.innerHTML += createOption(letters[newIndex], option.content);
                }});

                // Store mappings for the answer side
                document.body.setAttribute('data-option-mapping', JSON.stringify({{
                    originalToShuffled,
                    shuffledToOriginal
                }}));
            }}

            // Toggle option selection
            function toggleOption(letter) {{
                if (submitted) return;  // Prevent changes after submission
                
                var checkbox = document.getElementById('check' + letter);
                var optionDiv = document.getElementById('option' + letter);
                
                if (selectedOptions.has(letter)) {{
                    selectedOptions.delete(letter);
                    checkbox.checked = false;
                    optionDiv.classList.remove('selected');
                }} else {{
                    selectedOptions.add(letter);
                    checkbox.checked = true;
                    optionDiv.classList.add('selected');
                }}
            }}

            // Submit answer
            function submitAnswer() {{
                if (submitted) return;
                submitted = true;
                
                // Convert selected options back to original letters before storing
                const originalSelected = Array.from(selectedOptions).map(letter => shuffledToOriginal[letter]);
                document.body.setAttribute('data-selected-options', originalSelected.join(','));
                
                // Disable further selections
                document.getElementById('submit-btn').disabled = true;
                
                // Show answer
                pycmd('ans');
            }}

            // Only initialize if this is a new card (not the answer side)
            if (!document.getElementById('answer')) {{
                if (document.readyState === 'loading') {{
                    document.addEventListener('DOMContentLoaded', initializeOptions);
                }} else {{
                    initializeOptions();
                }}
            }} else {{
                // Hide submit button if this is the answer side
                var submitBtn = document.getElementById('submit-btn');
                if (submitBtn) {{
                    submitBtn.style.display = 'none';
                }}
            }}
        </script>
        """

        template['afmt'] = f"""
        {{{{FrontSide}}}}
        <hr id="answer">
        <div class="answer">
            <div class="options-explanations">
                {explanations_html}
            </div>
        </div>
        <script>
            // Hide submit button on answer side
            var submitBtn = document.getElementById('submit-btn');
            if (submitBtn) {{
                submitBtn.style.display = 'none';
            }}

            // Function to check if an option is correct
            function isCorrectAnswer(option) {{
                var correctAnswers = '{{{{CorrectOptions}}}}'.split(',').map(s => s.trim());
                return correctAnswers.includes(option);
            }}

            // Apply colors and show selections
            function applyColorsAndSelections() {{
                // Get the original selected options
                var selectedOptions = (document.body.getAttribute('data-selected-options') || '').split(',');
                
                [{', '.join([f"'{letter}'" for letter in letters])}].forEach(function(option) {{
                    var explanationDiv = document.getElementById('option' + option + 'Explanation');
                    var headerDiv = explanationDiv.querySelector('.option-header');
                    
                    if (explanationDiv) {{
                        // Apply correct/incorrect colors
                        if (isCorrectAnswer(option)) {{
                            explanationDiv.classList.add('correct-answer');
                        }} else {{
                            explanationDiv.classList.add('incorrect-answer');
                        }}
                        
                        // Show selection by adding blue background to header
                        if (selectedOptions.includes(option)) {{
                            headerDiv.classList.add('was-selected');
                        }}
                    }}
                }});
            }}

            // Call when DOM is loaded
            if (document.readyState === 'loading') {{
                document.addEventListener('DOMContentLoaded', applyColorsAndSelections);
            }} else {{
                applyColorsAndSelections();
            }}
        </script>
        """

        # Add template to model before adding CSS
        mm.add_template(m, template)

        # Add CSS (unchanged)
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
        
        # Add the model to the collection
        mm.add(m)
        return m

def create_csharp_note_type():
    """Create a C# specific note type with code examples."""
    model_name = "CSharpCard"
    if model_name not in mw.col.models.all_names():
        mm = mw.col.models
        m = mm.new(model_name)
        
        # Add fields
        fields = [
            "Question",
            "CorrectOption",
            "CorrectExplanation",
            "CorrectCodeExample",
            "IncorrectOption1",
            "IncorrectExplanation1",
            "IncorrectCodeExample1",
            "IncorrectOption2",
            "IncorrectExplanation2",
            "IncorrectCodeExample2",
            "IncorrectOption3",
            "IncorrectExplanation3",
            "IncorrectCodeExample3"
        ]
        
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
                    { content: `{{IncorrectOption1}}`, isCorrect: false },
                    { content: `{{IncorrectOption2}}`, isCorrect: false },
                    { content: `{{IncorrectOption3}}`, isCorrect: false }
                ];

                const shuffledIndices = shuffleArray([0, 1, 2, 3]);
                
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

            <div class="explanation-container incorrect-answer">
                <div class="option-header">{{IncorrectOption1}}</div>
                <div class="explanation">{{IncorrectExplanation1}}</div>
                <div class="code-example">
                    <pre><code class="language-csharp">{{IncorrectCodeExample1}}</code></pre>
                </div>
            </div>

            <div class="explanation-container incorrect-answer">
                <div class="option-header">{{IncorrectOption2}}</div>
                <div class="explanation">{{IncorrectExplanation2}}</div>
                <div class="code-example">
                    <pre><code class="language-csharp">{{IncorrectCodeExample2}}</code></pre>
                </div>
            </div>

            <div class="explanation-container incorrect-answer">
                <div class="option-header">{{IncorrectOption3}}</div>
                <div class="explanation">{{IncorrectExplanation3}}</div>
                <div class="code-example">
                    <pre><code class="language-csharp">{{IncorrectCodeExample3}}</code></pre>
                </div>
            </div>
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
            background-color: #1e1e1e;
            border-radius: 5px;
            overflow-x: auto;
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
            line-height: 1.5;
            background: transparent;
            white-space: pre-wrap !important;
        }

        /* Override Prism.js styles */
        code[class*="language-"],
        pre[class*="language-"] {
            white-space: pre-wrap !important;
            word-break: break-all;
            word-wrap: break-word;
            background: transparent;
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
    # Create existing MCQ variants
    create_mcq_note_type(2, "MCQ--")
    create_mcq_note_type(3, "MCQ-")
    create_mcq_note_type(4, "MCQ")
    create_mcq_note_type(5, "MCQ+")
    create_mcq_note_type(6, "MCQ++")
    
    # Create the new C# card type
    create_csharp_note_type()

# Add the init hook
gui_hooks.profile_did_open.append(init) 