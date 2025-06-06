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
    # Generate hidden divs for option content
    hidden_content_divs = []
    
    # Add correct options
    for i in range(correct_options):
        suffix = str(i + 1) if correct_options > 1 else ""
        div_id = f"recall_option_content_correct_{i}"
        hidden_content_divs.append(
            f'<div id="{div_id}" style="display:none;">{{{{CorrectOption{suffix}}}}}</div>'
        )
    
    # Add incorrect options
    for i in range(incorrect_options):
        div_id = f"recall_option_content_incorrect_{i}"
        hidden_content_divs.append(
            f'<div id="{div_id}" style="display:none;">{{{{IncorrectOption{i + 1}}}}}</div>'
        )
    
    hidden_content_html = "\n".join(hidden_content_divs)
    
    # Generate the options array structure
    options_array_items = []
    
    for i in range(correct_options):
        options_array_items.append(
            f'{{ contentId: "recall_option_content_correct_{i}", isCorrect: true }}'
        )
    
    for i in range(incorrect_options):
        options_array_items.append(
            f'{{ contentId: "recall_option_content_incorrect_{i}", isCorrect: false }}'
        )
    
    options_array = ",\n                    ".join(options_array_items)
    shuffled_indices = ", ".join(map(str, range(correct_options + incorrect_options)))
    
    return f"""
    <div class="question">{{{{Question}}}}</div>
    
    <!-- Hidden divs containing option content -->
    <div id="recall_hidden_option_content" style="display:none;">
        {hidden_content_html}
    </div>
    
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
        
        function getOptionContent(contentId) {{
            const contentDiv = document.getElementById(contentId);
            if (contentDiv) {{
                return contentDiv.innerHTML;
            }}
            console.error('Content div not found:', contentId);
            return '';
        }}

        function initializeOptions() {{
            try {{
                // Define options with references to content divs
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
                    if (option && option.contentId) {{
                        const content = getOptionContent(option.contentId);
                        if (content) {{
                            optionsContainer.innerHTML += createOption(newIndex, content);
                        }}
                    }}
                }});

                document.body.setAttribute('data-option-mapping', JSON.stringify({{
                    originalToShuffled,
                    shuffledToOriginal
                }}));
            }} catch (error) {{
                console.error('Error initializing options:', error);
                console.error('Error details:', error.message);
                if (error.stack) {{
                    console.error('Stack trace:', error.stack);
                }}
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
    # Generate all hidden divs for both content and explanations
    hidden_data_divs_list = []
    all_items_array = []
    
    # Add correct options
    for i in range(correct_options):
        suffix = str(i + 1) if correct_options > 1 else ""
        content_id = f"recall_back_content_correct_{i}"
        explanation_id = f"recall_explanation_correct_{suffix}"
        
        # Hidden divs for content and explanation
        hidden_data_divs_list.append(
            f'<div id="{content_id}" style="display:none;">{{{{CorrectOption{suffix}}}}}</div>'
        )
        hidden_data_divs_list.append(
            f'<div id="{explanation_id}" style="display:none;">{{{{CorrectExplanation{suffix}}}}}</div>'
        )
        
        all_items_array.append(
            f'{{ contentId: "{content_id}", explanationId: "{explanation_id}", isCorrect: true }}'
        )
    
    # Add incorrect options
    for i in range(incorrect_options):
        incorrect_suffix = str(i + 1)
        content_id = f"recall_back_content_incorrect_{i}"
        explanation_id = f"recall_explanation_incorrect_{incorrect_suffix}"
        
        hidden_data_divs_list.append(
            f'<div id="{content_id}" style="display:none;">{{{{IncorrectOption{incorrect_suffix}}}}}</div>'
        )
        hidden_data_divs_list.append(
            f'<div id="{explanation_id}" style="display:none;">{{{{IncorrectExplanation{incorrect_suffix}}}}}</div>'
        )
        
        all_items_array.append(
            f'{{ contentId: "{content_id}", explanationId: "{explanation_id}", isCorrect: false }}'
        )
    
    all_items_str = ",\n            ".join(all_items_array)
    hidden_data_divs_html = "\n        ".join(hidden_data_divs_list)
    
    return f"""
    {{{{FrontSide}}}}
    <hr id="answer">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/prism/1.24.1/themes/prism-tomorrow.min.css">
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.24.1/prism.min.js" data-manual></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.24.1/components/prism-markup.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.24.1/components/prism-css.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.24.1/components/prism-javascript.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.24.1/components/prism-csharp.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.24.1/components/prism-python.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.24.1/components/prism-java.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.24.1/components/prism-typescript.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.24.1/components/prism-json.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.24.1/components/prism-sql.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.24.1/components/prism-yaml.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.24.1/components/prism-bash.min.js"></script>
    
    <div id="recall_hidden_explanation_data" style="display:none;">
        {hidden_data_divs_html}
    </div>

    <!-- This container will hold all explanation entries in the randomized order -->
    <div class="answer" id="answers"></div>

    <script>
        // Build an array of all items in the same order they were added on the front side
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
        
        // Safe content extraction from hidden divs
        function getContentFromDiv(divId) {{
            const div = document.getElementById(divId);
            if (div) {{
                return div.innerHTML;
            }}
            console.error('Div not found:', divId);
            return '';
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
                    
                    // Get content and explanation from hidden divs
                    var itemContent = '';
                    var explanationHtml = '';
                    
                    if (item.contentId) {{
                        itemContent = getContentFromDiv(item.contentId);
                    }} else {{
                        console.error('Recall Anki: item missing contentId for originalIndex ' + originalIndex);
                    }}
                    
                    if (item.explanationId) {{
                        explanationHtml = getContentFromDiv(item.explanationId);
                    }} else {{
                        console.error('Recall Anki: item missing explanationId for originalIndex ' + originalIndex);
                    }}

                    container.innerHTML = `
                        <div class="question-reference">Q: ${{htmlEscape(questionText)}}</div>
                        <div class="option-header">${{itemContent}}</div>
                        <div class="explanation">${{explanationHtml}}</div>
                    `;
                    answersDiv.appendChild(container);
                }}
            }} catch (err) {{
                console.error('Recall Anki: Error building answer containers:', err);
                console.error('Error details:', err.message);
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
                
                // Enhanced syntax highlighting for JavaScript
                document.querySelectorAll('.language-javascript, .language-js').forEach(function(codeBlock) {{
                    // Fix common patterns that Prism might miss
                    var html = codeBlock.innerHTML;
                    
                    // Highlight standalone 'document', 'window', 'console' objects
                    html = html.replace(/\b(document|window|console|process|global|module|exports|require)\b(?!<\/span>)(?![^<]*>)/g, 
                        '<span class="token dom variable">$1</span>');
                    
                    // Highlight const/let/var variable declarations
                    html = html.replace(/(<span class="token keyword">(?:const|let|var)<\/span>\s+)([a-zA-Z_$][a-zA-Z0-9_$]*)(?![^<]*>)/g, 
                        '$1<span class="token variable">$2</span>');
                    
                    // Highlight properties after dots (but not methods)
                    html = html.replace(/(\.)([a-zA-Z_$][a-zA-Z0-9_$]*)(?=\s*[^(])/g, 
                        '$1<span class="token property">$2</span>');
                    
                    // Update the code block
                    codeBlock.innerHTML = html;
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
        background-color: #282C34;
        padding: 15px;
        border-radius: 8px;
        overflow-x: auto;
        margin: 15px 0;
        border: 1px solid rgba(62, 68, 81, 0.5);
        box-shadow: inset 0 1px 8px rgba(0, 0, 0, 0.2);
        white-space: pre;
        word-wrap: normal;
        overflow-wrap: normal;
    }

    code {
        font-family: 'JetBrains Mono', 'Consolas', 'Monaco', monospace;
        font-size: 14px;
        color: #ABB2BF;
        background-color: transparent;
    }

    /* Inline code */
    p code {
        background-color: #21252b;
        padding: 2px 5px;
        border-radius: 3px;
        border: 1px solid rgba(62, 68, 81, 0.5);
        font-family: 'JetBrains Mono', 'Consolas', 'Monaco', monospace;
    }

    /* Code block specific styling */
    .code-block {
        background-color: #21252b;
        border-radius: 8px;
        margin: 15px 0;
        overflow-x: auto;
        padding: 1px;
    }
    
    .code-block pre {
        background-color: #282C34;
        border: none;
        box-shadow: none;
        margin: 0;
        padding: 15px;
        border-radius: 7px;
    }
    
    .code-block pre code {
        background-color: transparent;
        padding: 0;
        border: none;
    }

    /* One Dark Pro Syntax Highlighting - Exact VS Code Colors */
    
    /* CRITICAL: JavaScript variable and property fixes */
    
    /* Force proper tokenization for common patterns */
    .language-javascript .token.constant,
    .language-js .token.constant,
    .language-javascript .token.variable,
    .language-js .token.variable {
        color: #E5C07B !important;
    }
    
    /* Special handling for 'document', 'window', 'console' etc. */
    .language-javascript .token.dom,
    .language-js .token.dom,
    .language-javascript .token.console,
    .language-js .token.console {
        color: #E5C07B !important;
    }
    
    /* Properties after dot notation */
    .language-javascript .token.property,
    .language-js .token.property,
    .language-javascript .token.method .token.property,
    .language-js .token.method .token.property {
        color: #E06C75 !important;
    }
    
    /* Variables and built-in objects */
    .language-javascript .token.variable,
    .language-js .token.variable,
    .language-javascript .token.dom.variable,
    .language-js .token.dom.variable {
        color: #E5C07B !important;
    }
    
    /* Override for specific common objects */
    .language-javascript .token.keyword + .token,
    .language-js .token.keyword + .token {
        /* Variables after const/let/var */
        color: #E5C07B !important;
    }
    
    /* Comments */
    .token.comment,
    .token.prolog,
    .token.cdata {
        color: #5C6370;
        font-style: italic;
    }

    /* Punctuation and plain text */
    .token.punctuation {
        color: #ABB2BF;
    }
    
    /* HTML/XML Tags */
    .token.tag,
    .token.selector,
    .token.doctype .token.name,
    .token.doctype-tag {
        color: #E06C75;
    }
    
    /* HTML Attributes */
    .token.attr-name,
    .token.attribute {
        color: #D19A66;
    }
    
    /* Strings and attribute values */
    .token.string,
    .token.attr-value,
    .token.char {
        color: #98C379;
    }
    
    /* JavaScript/CSS Keywords (let, const, var, function, etc) */
    .token.keyword,
    .token.control,
    .token.directive,
    .token.storage {
        color: #C678DD;
    }
    
    /* Operators (=, +, -, etc) */
    .token.operator,
    .token.entity,
    .token.url,
    .token.variable.interpolation {
        color: #56B6C2;
    }
    
    /* Function/Method names */
    .token.function,
    .token.method,
    .token.function-name {
        color: #61AFEF;
    }
    
    /* Class names, built-in objects (document, window, etc) */
    .token.class-name,
    .token.builtin,
    .token.console {
        color: #E5C07B;
    }
    
    /* Variables and properties - generic rules */
    .token.variable {
        color: #E5C07B;
    }
    
    .token.property {
        color: #E06C75;
    }
    
    .token.constant,
    .token.symbol {
        color: #E06C75;
    }
    
    /* Numbers */
    .token.number {
        color: #D19A66;
    }
    
    /* Booleans */
    .token.boolean {
        color: #D19A66;
    }
    
    /* Regex */
    .token.regex {
        color: #98C379;
    }
    
    /* Important */
    .token.important {
        color: #C678DD;
        font-weight: bold;
    }
    
    /* Special cases for better HTML highlighting */
    .language-html .token.tag .token.punctuation,
    .language-xml .token.tag .token.punctuation {
        color: #ABB2BF;
    }
    
    .language-html .token.tag .token.tag,
    .language-xml .token.tag .token.tag {
        color: #E06C75;
    }
    
    /* Special cases for JavaScript highlighting */
    .language-javascript .token.keyword,
    .language-js .token.keyword {
        color: #C678DD;
    }
    
    .language-javascript .token.function,
    .language-js .token.function {
        color: #61AFEF;
    }
    
    .language-javascript .token.class-name,
    .language-js .token.class-name,
    .language-javascript .token.maybe-class-name,
    .language-js .token.maybe-class-name {
        color: #E5C07B;
    }
    
    .language-javascript .token.operator,
    .language-js .token.operator {
        color: #56B6C2;
    }
    
    .language-javascript .token.property-access .token.property,
    .language-js .token.property-access .token.property {
        color: #E06C75;
    }
    
    /* Additional token types for better coverage */
    .token.atrule {
        color: #C678DD;
    }
    
    .token.attr-equals {
        color: #ABB2BF;
    }
    
    .token.namespace {
        color: #E06C75;
    }
    
    .token.doctype .token.doctype-tag {
        color: #ABB2BF;
    }
    
    .token.doctype .token.name {
        color: #E06C75 !important;
    }
    
    .token.doctype .token.string {
        color: #98C379;
    }
    
    /* Override Prism's default styles to ensure our colors take precedence */
    pre[class*="language-"],
    code[class*="language-"] {
        color: #ABB2BF;
        background: #282C34;
        text-shadow: none;
    }
    
    /* Make sure code blocks have the right background */
    pre[class*="language-"] {
        background-color: #282C34;
    }
    
    :not(pre) > code[class*="language-"],
    pre[class*="language-"] {
        background: #282C34;
    }
    
    /* Additional specific overrides for better One Dark Pro matching */
    
    /* DOCTYPE specific styling */
    .language-html .token.doctype .token.tag,
    .language-markup .token.doctype .token.tag {
        color: #ABB2BF;
    }
    
    .language-html .token.doctype .token.name,
    .language-markup .token.doctype .token.name {
        color: #E06C75;
    }
    
    /* JavaScript DOM objects and properties */
    .language-javascript .token.dom,
    .language-js .token.dom,
    .language-javascript .token.constant:not(.token.boolean):not(.token.number),
    .language-js .token.constant:not(.token.boolean):not(.token.number) {
        color: #E5C07B;
    }
    
    /* Special handling for common DOM objects */
    .language-javascript .token.keyword + .token.punctuation + .token.maybe-class-name,
    .language-js .token.keyword + .token.punctuation + .token.maybe-class-name {
        color: #E5C07B;
    }
    
    /* Property access in JavaScript */
    .language-javascript .token.punctuation.dot,
    .language-js .token.punctuation.dot {
        color: #ABB2BF;
    }
    
    /* Force specific token combinations */
    .language-javascript .token.variable:first-child,
    .language-js .token.variable:first-child {
        color: #E06C75;
    }
    
    /* Ensure assignment patterns work correctly */
    .language-javascript .token.keyword + .token.variable,
    .language-js .token.keyword + .token.variable {
        color: #E06C75;
    }
    
    /* String template literals */
    .token.template-string,
    .token.template-punctuation {
        color: #98C379;
    }
    
    /* Fix for inline HTML script tags */
    .language-html .token.script .token.language-javascript,
    .language-markup .token.script .token.language-javascript {
        color: #ABB2BF;
    }
    
    /* Ensure proper cascading for nested tokens */
    .token.tag .token.attr-name {
        color: #D19A66 !important;
    }
    
    .token.tag .token.attr-value {
        color: #98C379 !important;
    }
    
    .token.tag .token.punctuation:not(.token.attr-equals) {
        color: #ABB2BF !important;
    }
    
    /* Fix for equals sign in attributes */
    .token.attr-equals,
    .token.tag .token.attr-equals {
        color: #ABB2BF !important;
    }
    
    /* Ensure DOCTYPE styling takes precedence */
    .token.doctype {
        color: #ABB2BF !important;
    }
    
    .token.doctype .token.tag {
        color: #ABB2BF !important;
    }
    
    .token.doctype .token.name {
        color: #E06C75 !important;
    }
    
    /* Additional comprehensive token rules for robustness */
    
    /* General language constructs */
    .token.decorator,
    .token.annotation {
        color: #E5C07B;
    }
    
    .token.interpolation {
        color: #E06C75;
    }
    
    .token.parameter {
        color: #E06C75;
    }
    
    .token.property-access {
        color: #E06C75;
    }
    
    .token.namespace {
        color: #E5C07B;
    }
    
    /* CSS specific tokens */
    .language-css .token.selector,
    .language-scss .token.selector {
        color: #E06C75;
    }
    
    .language-css .token.property,
    .language-scss .token.property {
        color: #61AFEF;
    }
    
    .language-css .token.function,
    .language-scss .token.function {
        color: #61AFEF;
    }
    
    .language-css .token.important,
    .language-scss .token.important {
        color: #C678DD;
    }
    
    .language-css .token.unit,
    .language-scss .token.unit {
        color: #D19A66;
    }
    
    /* JavaScript/TypeScript specific patterns */
    .language-javascript .token.spread,
    .language-js .token.spread,
    .language-typescript .token.spread,
    .language-ts .token.spread {
        color: #56B6C2;
    }
    
    .language-javascript .token.arrow,
    .language-js .token.arrow,
    .language-typescript .token.arrow,
    .language-ts .token.arrow {
        color: #C678DD;
    }
    
    .language-javascript .token.module,
    .language-js .token.module,
    .language-typescript .token.module,
    .language-ts .token.module {
        color: #C678DD;
    }
    
    .language-javascript .token.async,
    .language-js .token.async,
    .language-typescript .token.async,
    .language-ts .token.async {
        color: #C678DD;
    }
    
    /* Python specific */
    .language-python .token.decorator {
        color: #E5C07B;
    }
    
    .language-python .token.builtin {
        color: #E5C07B;
    }
    
    /* JSON specific */
    .language-json .token.property {
        color: #E06C75;
    }
    
    /* SQL specific */
    .language-sql .token.keyword {
        color: #C678DD;
    }
    
    .language-sql .token.function {
        color: #61AFEF;
    }
    
    /* Additional pattern matching for complex cases */
    
    /* Object property notation */
    .token.property + .token.punctuation + .token.property {
        color: #E06C75;
    }
    
    /* Method chaining */
    .token.punctuation + .token.method {
        color: #61AFEF;
    }
    
    /* Template literal expressions */
    .token.template-string .token.interpolation {
        color: #ABB2BF;
    }
    
    .token.template-string .token.interpolation .token.interpolation-punctuation {
        color: #C678DD;
    }
    
    /* Import/Export statements */
    .token.keyword.module {
        color: #C678DD;
    }
    
    /* Catch common patterns that might be missed */
    .token.boolean,
    .token.null,
    .token.undefined {
        color: #D19A66;
    }
    
    .token.this,
    .token.self,
    .token.super {
        color: #E06C75;
    }
    
    /* Regular expression components */
    .token.regex-delimiter,
    .token.regex-flags {
        color: #98C379;
    }
    
    .token.regex-source {
        color: #98C379;
    }
    
    /* Handle special punctuation cases */
    .token.punctuation.brace-open,
    .token.punctuation.brace-close {
        color: #ABB2BF;
    }
    
    .token.punctuation.bracket-open,
    .token.punctuation.bracket-close {
        color: #ABB2BF;
    }
    
    /* JSX/TSX specific */
    .language-jsx .token.tag,
    .language-tsx .token.tag {
        color: #E06C75;
    }
    
    .language-jsx .token.attr-name,
    .language-tsx .token.attr-name {
        color: #D19A66;
    }
    
    .language-jsx .token.script,
    .language-tsx .token.script {
        color: #ABB2BF;
    }
    
    /* Generic fallbacks for unknown tokens */
    .token.unknown {
        color: #ABB2BF;
    }
    
    /* Ensure consistency across different Prism.js versions */
    .token.tag:not(.punctuation):not(.attr-name):not(.attr-value):not(.script) {
        color: #E06C75;
    }
    
    .token.constant.language {
        color: #D19A66;
    }
    
    .token.storage.type {
        color: #C678DD;
    }
    
    .token.storage.modifier {
        color: #C678DD;
    }
    
    .token.variable.language {
        color: #E06C75;
    }
    
    /* Override any conflicting Prism.js theme styles */
    .prism-tomorrow {
        display: none !important;
    }
    
    /* Ensure our styles cascade properly */
    .code-block code[class*="language-"] .token {
        font-family: inherit;
        font-size: inherit;
        line-height: inherit;
    }
    
    /* Selection colors */
    pre[class*="language-"]::-moz-selection,
    pre[class*="language-"] ::-moz-selection,
    code[class*="language-"]::-moz-selection,
    code[class*="language-"] ::-moz-selection {
        background: rgba(67, 84, 103, 0.7);
        color: inherit;
    }
    
    pre[class*="language-"]::selection,
    pre[class*="language-"] ::selection,
    code[class*="language-"]::selection,
    code[class*="language-"] ::selection {
        background: rgba(67, 84, 103, 0.7);
        color: inherit;
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