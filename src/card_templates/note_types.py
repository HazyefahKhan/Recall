"""
Note type creation for Recall Anki plugin.
"""

from aqt import mw
from aqt.qt import *
from anki.models import ModelManager

def create_recall_note_type(correct_options, incorrect_options):
    """
    Create a recall note type with code examples.
    
    Args:
        correct_options (int): Number of correct options
        incorrect_options (int): Number of incorrect options
        
    Returns:
        dict: The created note type model
    """
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
        template['qfmt'] = create_front_template(correct_options, incorrect_options)

        # Back template
        template['afmt'] = create_back_template(correct_options, incorrect_options)

        # Add CSS
        m['css'] = get_card_styling()

        # Add template to model
        mm.add_template(m, template)
        
        # Add the model to the collection
        mm.add(m)
        return m

def create_front_template(correct_options, incorrect_options):
    """
    Create the front template for the card.
    
    Args:
        correct_options (int): Number of correct options
        incorrect_options (int): Number of incorrect options
        
    Returns:
        str: The front template HTML/JS
    """
    # Generate the options array based on the number of correct and incorrect options
    options_array = ""
    for i in range(correct_options):
        suffix = str(i + 1) if correct_options > 1 else ""
        options_array += f"{{ content: `{{{{CorrectOption{suffix}}}}}`, isCorrect: true }}"
        if i < correct_options - 1 or incorrect_options > 0:
            options_array += ",\n"
            
    if incorrect_options > 0:
        for i in range(incorrect_options):
            options_array += f"{{ content: `{{{{IncorrectOption{i + 1}}}}}`, isCorrect: false }}"
            if i < incorrect_options - 1:
                options_array += ",\n"
    
    shuffled_indices = ", ".join(map(str, range(correct_options + incorrect_options)))
    
    return f"""
    <div class="question">{{{{Question}}}}</div>
    <div id="options" class="options"></div>
    <button onclick="submitAnswer()" id="submit-btn" class="submit-button">Submit</button>

    <script>
        var selectedOptions = new Set();
        var submitted = false;
        var originalToShuffled = {{}};
        var shuffledToOriginal = {{}};

        function shuffleArray(array) {{
            for (let i = array.length - 1; i > 0; i--) {{
                const j = Math.floor(Math.random() * (i + 1));
                [array[i], array[j]] = [array[j], array[i]];
            }}
            return array;
        }}

        function createOption(index, content) {{
            return `
                <div class="option" onclick="selectOption(${{index}})" id="option${{index}}" data-index="${{index}}">
                    <input type="checkbox" name="option" id="checkbox${{index}}" class="option-checkbox">
                    <label>${{content}}</label>
                </div>
            `;
        }}

        function initializeOptions() {{
            try {{
                const options = [
                    {options_array}
                ];

                const shuffledIndices = shuffleArray([{shuffled_indices}]);
                
                const optionsContainer = document.getElementById('options');
                if (!optionsContainer) {{
                    console.error('Options container not found');
                    return;
                }}

                // Clear existing options
                optionsContainer.innerHTML = '';
                
                shuffledIndices.forEach((originalIndex, newIndex) => {{
                    originalToShuffled[originalIndex] = newIndex;
                    shuffledToOriginal[newIndex] = originalIndex;
                    const option = options[originalIndex];
                    if (option && option.content) {{
                        optionsContainer.innerHTML += createOption(newIndex, option.content);
                    }}
                }});

                document.body.setAttribute('data-option-mapping', JSON.stringify({{
                    originalToShuffled,
                    shuffledToOriginal
                }}));
            }} catch (error) {{
                console.error('Error initializing options:', error);
            }}
        }}

        function selectOption(index) {{
            if (submitted) return;
            
            const checkbox = document.getElementById('checkbox' + index);
            const optionDiv = document.getElementById('option' + index);
            
            if (selectedOptions.has(index)) {{
                selectedOptions.delete(index);
                optionDiv.classList.remove('selected');
                checkbox.checked = false;
            }} else {{
                selectedOptions.add(index);
                optionDiv.classList.add('selected');
                checkbox.checked = true;
            }}
        }}

        function submitAnswer() {{
            if (submitted || selectedOptions.size === 0) return;
            submitted = true;
            
            const originalSelected = Array.from(selectedOptions).map(index => shuffledToOriginal[index]);
            document.body.setAttribute('data-selected-options', JSON.stringify(originalSelected));
            
            document.getElementById('submit-btn').disabled = true;
            pycmd('ans');
        }}

        // Initialize options when the document is ready
        if (document.readyState === 'loading') {{
            document.addEventListener('DOMContentLoaded', initializeOptions);
        }} else {{
            setTimeout(initializeOptions, 0);
        }}
    </script>
    """

def create_back_template(correct_options, incorrect_options):
    """
    Create the back template for the card.
    
    Args:
        correct_options (int): Number of correct options
        incorrect_options (int): Number of incorrect options
        
    Returns:
        str: The back template HTML/JS
    """
    # Generate all items array based on the number of correct and incorrect options
    hidden_data_divs_list = []
    all_items_array = []
    
    # Add correct options
    for i in range(correct_options):
        suffix = str(i + 1) if correct_options > 1 else ""
        explanation_id = f"recall_explanation_correct_{suffix}" # Unique ID
        # Store the raw field reference for the hidden div
        hidden_data_divs_list.append(
            f'<div id="{explanation_id}" style="display:none;">{{{{CorrectExplanation{suffix}}}}}</div>'
        )
        all_items_array.append(
            # Use simple string for ID, no URL encoding needed here for explanation_id
            # Use a more robust approach for content that might have special characters
            f'{{ content: `{{{{CorrectOption{suffix}}}}}`, explanation_id: "{explanation_id}", isCorrect: true }}'
        )
    
    # Add incorrect options
    for i in range(incorrect_options):
        incorrect_suffix = str(i + 1) # Incorrect options always have a suffix
        explanation_id = f"recall_explanation_incorrect_{incorrect_suffix}" # Unique ID
        hidden_data_divs_list.append(
            f'<div id="{explanation_id}" style="display:none;">{{{{IncorrectExplanation{incorrect_suffix}}}}}</div>'
        )
        all_items_array.append(
            # Use backtick literals instead of URL encoding/decoding to preserve exact content
            f'{{ content: `{{{{IncorrectOption{incorrect_suffix}}}}}`, explanation_id: "{explanation_id}", isCorrect: false }}'
        )
    
    all_items_str = ",\n".join(all_items_array)
    hidden_data_divs_html = "\n".join(hidden_data_divs_list)
    
    return f"""
    {{{{FrontSide}}}}
    <hr id="answer">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/prism/1.24.1/themes/prism-tomorrow.min.css">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.24.1/prism.min.js" data-manual></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.24.1/components/prism-csharp.min.js"></script>
    
    <div id="recall_hidden_explanation_data" style="display:none;">
        {hidden_data_divs_html}
    </div>

    <!-- This container will hold all explanation entries in the randomized order -->
    <div class="answer" id="answers"></div>

    <script>
        // Build an array of all items in the same order they were added on the front side:
        var allItems = [
            {all_items_str}
        ];

        // HTML escape function to prevent HTML interpretation
        function htmlEscape(text) {{
            if (typeof text !== 'string') return '';
            return text
                .replace(/&/g, '&amp;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;')
                .replace(/"/g, '&quot;')
                .replace(/'/g, '&#39;');
        }}
        
        // Safe content extraction - ensures content is always treated as plain text
        function safeExtractContent(item) {{
            try {{
                if (!item || typeof item.content === 'undefined') return '';
                // Return as-is if it's already a string
                if (typeof item.content === 'string') return item.content;
                // Try to convert to string if it's something else
                return String(item.content);
            }} catch (err) {{
                console.error('Error extracting content:', err);
                return '';
            }}
        }}

        function buildAnswerContainers() {{
            try {{
                var mappingStr = document.body.getAttribute('data-option-mapping');
                if (!mappingStr) {{
                    console.error('Recall Anki: data-option-mapping not found on body.');
                    return; 
                }}
                var mapping = JSON.parse(mappingStr);
                var stO = mapping.shuffledToOriginal; 
                var answersDiv = document.getElementById('answers');
                if (!answersDiv) {{
                    console.error('Recall Anki: answers div not found.');
                    return;
                }}
                
                var questionDiv = document.querySelector('.question');
                var questionText = questionDiv ? (questionDiv.textContent || questionDiv.innerText || '') : '';
                
                answersDiv.innerHTML = '';

                for (var newIndex = 0; newIndex < allItems.length; newIndex++) {{
                    if (!stO || typeof stO[newIndex] === 'undefined') {{
                        console.error('Recall Anki: shuffledToOriginal mapping missing for index ' + newIndex);
                        continue;
                    }}
                    var originalIndex = stO[newIndex];
                    if (!allItems || typeof allItems[originalIndex] === 'undefined') {{
                        console.error('Recall Anki: allItems missing for originalIndex ' + originalIndex);
                        continue;
                    }}
                    var item = allItems[originalIndex];
                    var container = document.createElement('div');
                    container.className = 'explanation-container ' + 
                        (item.isCorrect ? 'correct-answer' : 'incorrect-answer');
                    container.setAttribute('data-option-index', originalIndex);
                    
                    var explanationHtml = '';
                    if (item.explanation_id) {{
                        var explanationDiv = document.getElementById(item.explanation_id);
                        if (explanationDiv) {{
                            explanationHtml = explanationDiv.innerHTML;
                        }} else {{
                            console.error('Recall Anki: Hidden explanation div not found: ' + item.explanation_id);
                        }}
                    }} else {{
                        console.warn('Recall Anki: item found without explanation_id for originalIndex ' + originalIndex, item);
                    }}
                    
                    // Use the safe content extraction function
                    var itemContent = safeExtractContent(item);

                    container.innerHTML = `
                        <div class="question-reference">Q: ${{htmlEscape(questionText)}}</div>
                        <div class="option-header">${{itemContent}}</div>
                        <div class="explanation">${{explanationHtml}}</div>
                    `;
                    answersDiv.appendChild(container);
                }}
            }} catch (err) {{
                console.error('Recall Anki: Error building answer containers:', err);
                if (err.stack) {{
                    console.error(err.stack);
                }}
            }}
        }}

        function highlightSelection() {{
            try {{
                var selectedOptionsStr = document.body.getAttribute('data-selected-options');
                if (!selectedOptionsStr) return;

                var selectedOptions = JSON.parse(selectedOptionsStr);
                var containers = document.querySelectorAll('.explanation-container');
                
                containers.forEach(container => {{
                    const optionIndexStr = container.getAttribute('data-option-index');
                    if (optionIndexStr === null) return; // Skip if attribute is missing
                    const optionIndex = parseInt(optionIndexStr);
                    if (selectedOptions.includes(optionIndex)) {{
                        container.classList.add('was-selected');
                        const header = container.querySelector('.option-header');
                        if (header) header.classList.add('was-selected');
                    }}
                }});

                document.querySelectorAll('pre code').forEach(function(block) {{
                    Prism.highlightElement(block);
                }});
            }} catch (error) {{
                console.error('Recall Anki: Error in highlightSelection:', error);
                 if (error.stack) {{
                    console.error(error.stack);
                }}
            }}
        }}

        if (document.readyState === 'loading') {{
            document.addEventListener('DOMContentLoaded', () => {{
                buildAnswerContainers();
                highlightSelection();
            }});
        }} else {{
            buildAnswerContainers();
            highlightSelection();
        }}
    </script>
    """

def get_card_styling():
    """
    Get the CSS styling for the card.
    
    Returns:
        str: The CSS styling
    """
    return """
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
        overflow-x: visible;
        margin: 15px 0;
        border: 1px solid rgba(62, 68, 81, 0.5);
        box-shadow: inset 0 1px 8px rgba(0, 0, 0, 0.2);
        white-space: pre-wrap;
        word-wrap: break-word;
        overflow-wrap: break-word;
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
        overflow-x: visible;
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