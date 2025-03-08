from aqt import mw
from aqt import gui_hooks
from aqt.qt import *
from anki.models import ModelManager
from anki.notes import Note
from anki.utils import html_to_text_line
import re
import markdown

def convert_markdown_to_html(text):
    """Convert markdown text to HTML with proper formatting and One Dark Pro syntax highlighting."""
    # Convert single tilde with backticks to del tags (removing backticks)
    text = re.sub(r'`~([^~\n]+)~`', r'~\1~', text)
    
    # Convert double tilde with backticks to del tags (removing backticks)
    text = re.sub(r'`~~([^~\n]+)~~`', r'~~\1~~', text)
    
    # Convert single tilde to del tags before processing markdown
    text = re.sub(r'(?<!~)~([^~\n]+)~(?!~)', r'<del>\1</del>', text)
    
    # Convert double tildes to del tags
    text = re.sub(r'~~([^~\n]+)~~', r'<del>\1</del>', text)
    
    # Apply One Dark Pro syntax highlighting to common protocols and technical terms (blue for functions/methods/protocols)
    protocol_pattern = r'\b(HTTP|HTTPS|FTP|SMTP|ICMP|TCP|IP|UDP|DNS|SSH|TLS|SSL|ARP|IMAP|HTTP\/1\.1|HTTP\/2|HTTP 1\.1)\b(?!\w)'
    text = re.sub(protocol_pattern, r'<span class="odp-blue">\1</span>', text)
    
    # Handle protocol followed by "protocol" word or specific components
    text = re.sub(r'\b(HTTP|HTTPS|FTP|SMTP|SSH) (protocol|request|method|header|body|version|version type|verb|status|headers|response|response codes|status code|response headers|response body|stateless protocol|stateful protocol)\b', 
                 r'<span class="odp-blue">\1</span> <span class="odp-blue">\2</span>', text)
    
    # HTTP related components and concepts (blue for specific HTTP elements)
    http_components = r'\b(HTTP (response|request|body|status code|response headers|response body|connection))\b'
    text = re.sub(http_components, r'<span class="odp-blue">\1</span>', text)
    
    # Extend HTTP components more granularly (blue)
    http_components_extended = r'\b(response body|encrypted payload|browser cookie|numeric status code|session token|TCP connection|persistent connection|non-persistent connection)\b'
    text = re.sub(http_components_extended, r'<span class="odp-blue">\1</span>', text)
    
    # HTTP methods highlighting (blue for functions)
    text = re.sub(r'\b(GET|POST|PUT|DELETE|HEAD|OPTIONS|PATCH)\b', r'<span class="odp-blue">\1</span>', text)
    
    # HTTP status codes highlighting (blue for specific codes)
    text = re.sub(r'\b(\d{3})\s+(OK|Not Found|Multiple Choices|Continue|Internal Server Error|Moved Permanently)\b', 
                 r'<span class="odp-blue">\1 \2</span>', text)
    
    # HTTP status code families (purple for keywords)
    text = re.sub(r'\b(\d)xx\b', r'<span class="odp-purple">\1xx</span>', text)
    
    # Apply One Dark Pro syntax highlighting to protocol names with parentheses (purple for keywords)
    protocol_full_names = r'(Hypertext Transfer Protocol|File Transfer Protocol|Simple Mail Transfer Protocol|Internet Control Message Protocol|' + \
                         r'Transmission Control Protocol|User Datagram Protocol|Domain Name System|Secure Shell Protocol|Transport Layer Security|' + \
                         r'Secure Sockets Layer|Internet Protocol|Address Resolution Protocol)'
    
    text = re.sub(f'{protocol_full_names}(\\s*\\(([^)]+)\\))', 
                  r'<span class="odp-purple">\1</span><span class="odp-black">\2</span>', text)
    
    # Color individual protocol name words (purple)
    protocol_keywords = r'\b(Hypertext|Transfer|Protocol|File|Simple|Mail|Internet|Control|Message|Transmission|' + \
                       r'User|Datagram|Domain|Name|System|Secure|Shell|Transport|Layer|Security|Sockets|Address|Resolution)\b'
    text = re.sub(protocol_keywords, r'<span class="odp-purple">\1</span>', text)
    
    # Highlight programming languages, frameworks, and technical platforms (yellow for constants)
    tech_pattern = r'\b(JavaScript|Python|Java|C\+\+|Ruby|PHP|HTML|CSS|React|Angular|Vue|Node\.js|TypeScript|SQL|NoSQL|MongoDB|Redis|Docker|Kubernetes|AWS|Azure|JSON|Google Chrome|Mozilla Firefox|Microsoft Edge|Safari|Developer Tools|DevTools|Web Inspector|JSON web token|blockchain|ledger|Microsoft Excel|text\/html|application\/json|HTML data|XML data|JSON data|Binary data)\b'
    text = re.sub(tech_pattern, r'<span class="odp-yellow">\1</span>', text)
    
    # Highlight network architecture concepts (orange for properties/attributes)
    network_architecture = r'\b(application layer|transport layer|network layer|link layer|physical layer|network model|protocol stack|network protocol stack|lower-level protocols|TCP\/IP|OSI model|request line|resource address|hardware-level addressing|URL|domain name resolution|status codes|encryption method|content format|key-value pairs|caching policies|security process|encryption handshake|offline caching|success|failure|client-side error|server-side error|informational response|redirect|download speed|network conditions|server capacity|security measures|payment method|content access|styling information|presentation layers|metadata|server-to-client communication|client-side|server-side|stateless|stateful|session layer|layer 7|layer 5|layer 3|layer 1|encryption across all layers|user login|connection|multiple sessions|initiation process|multiple requests|concurrent connections)\b'
    text = re.sub(network_architecture, r'<span class="odp-orange">\1</span>', text)
    
    # Color individual architecture words (orange)
    architecture_keywords = r'\b(application|transport|network|layer|layers|link|physical|model|stack|protocol|protocols|lower-level|TCP\/IP|OSI|request|line|resource|address|URL|URI|hardware-level|addressing|status|encryption|keys|values|pairs|format|content|caching|policy|policies|offline|handshake|security|process|zone|transfers|resolution|driver|updates|digit|digits|standardized|communication|specificity|complexity|redirect|download|speed|conditions|capacity|measures|payment|access|styling|presentation|metadata|client|server|browser|web)\b'
    text = re.sub(architecture_keywords, r'<span class="odp-orange">\1</span>', text)
    
    # Highlight protocol positioning with layers
    text = re.sub(r'\b(HTTP|HTTPS|FTP|SMTP|ICMP|TCP|IP|UDP|DNS|SSH|TLS|SSL|ARP|IMAP)(\s+at\s+the\s+)(application layer|transport layer|network layer|link layer)\b', 
                 r'<span class="odp-blue">\1</span>\2<span class="odp-orange">\3</span>', text)
    
    # Highlight relationships between protocols and stack
    text = re.sub(r'\b(relies on|runs on top of|resides in|below|above|on top of|included in|part of)\b', 
                 r'<span class="odp-cyan">\1</span>', text)
    
    # Color individual relationship words (cyan)
    relationship_keywords = r'\b(relies|runs|resides|below|above|top|included|part)\b'
    text = re.sub(relationship_keywords, r'<span class="odp-cyan">\1</span>', text)
    
    # Highlight technical actions and verbs (cyan for operators)
    actions_pattern = r'\b(enables|transferring|sending|receiving|handles|serving|processing|communicating|exchanging|forming|providing|' + \
                     r'operates|functions|managing|ensuring|transmit|forwards|filter|rewrite|maps|routes|transports|responds|requests|execute|rely|resides|' + \
                     r'perform|begin|processes|discarding|redirecting|filtering|blocking|assigned|leased|facilitates|retrieval|loading|dedicated|' + \
                     r'restricted|tailored|used for|designed|making|responsible|might|display|verify|generate|remove|carries|transmitted|conflates|' + \
                     r'precompiled|retrieving|pinpoints|embedded|tracking|convey|resolve|rendering|retrieval|submission|updating|expect|compress|encrypts|' + \
                     r'indicate|labeled|termed|referred|controls|queried|works|encrypts|replaces|marks|unrelated|deletes|replaces|blocks|modifies|' + \
                     r'executing|triggering|shutting|encountered|frequently|occasionally|commonly|controlling|stripped|attached|interpret|render|reference|' + \
                     r'communicate|communicate|represent|receive|answer|return|reply|confusion|confuses|describes|included|referencing|returned|resolution|disclosure|conveying|communicate|disclosed|capture|show|prevent|manage|inspect|simplify|download|parse|overwhelm|flooding|crash|weaponized|denying|mounted|deliberately|reused|relies on|reusing|consuming|times out|mounted)\b'
    text = re.sub(actions_pattern, r'<span class="odp-cyan">\1</span>', text)
    
    # Add singular/plural forms for technical actions (cyan)
    actions_singular_plural = r'\b(transfer|transfers|transmitted|transmits|request|response|responses|load|loads|handle|service|map|route|' + \
                              r'process|transport|respond|request|execute|execution|rely|reside|forward|filter|filters|rewrite|rewrites|' + \
                              r'discard|discards|redirect|redirects|filter|block|blocks|assign|assigns|lease|leases|facilitate|retrieve|' + \
                              r'retrieved|load|loaded|design|designed|make|made|responsible|use|used|enable|enabled|manage|managed|ensure|' + \
                              r'ensured|form|formed|provide|provided|operate|operated|function|functioned|display|displays|verify|verifies|' + \
                              r'generate|generates|remove|removes|carry|carries|conflate|conflates|compile|compiles|retrieve|retrieves|' + \
                              r'pinpoint|pinpoints|embed|embeds|track|tracks|convey|conveys|resolve|resolves|render|renders|submit|submits|' + \
                              r'expect|expects|retrieve|retrieves|update|updates|compress|compresses|encrypt|encrypts|query|queries|' + \
                              r'delete|deletes|modify|modifies|replace|replaces|block|blocks|label|labels|term|terms|refer|refers|' + \
                              r'control|controls|mark|marks|execute|executes|trigger|triggers|shutdown|shutdowns|strip|strips|attach|attaches|' + \
                              r'interpret|interprets|communicate|communicates|represent|represents|receive|receives|answer|answers|return|returns|' + \
                              r'reply|replies|confuse|confuses|describe|describes|include|includes|reference|references|disclose|discloses|' + \
                              r'convey|conveys|travel|travels|parse|parses|capture|captures|show|shows|prevent|prevents|manage|manages|inspect|inspects|simplify|simplifies|download|downloads)\b'
    text = re.sub(actions_singular_plural, r'<span class="odp-cyan">\1</span>', text)
    
    # Add browser-specific actions (cyan)
    browser_actions = r'\b(converts HTML into a webpage|removes HTML content|stores HTML as a text file|encrypts HTML for security|renders|rendering)\b'
    text = re.sub(browser_actions, r'<span class="odp-cyan">\1</span>', text)
    
    # Highlight important web/internet terms (green for strings)
    web_terms = r'\b(World Wide Web|web|internet|online|browser|server|client|request|response|data|resources|systems|foundation|basis|' + \
               r'content|communications|information|transfer|packet|frame|message|record|address|routing|addressing|traffic|transaction|' + \
               r'network|devices|media|interactive|text|login|command|error|operational|flow|sequence|hypertext|hypertext links|' + \
               r'hypertext-linked|website content|webpages|data exchange|diagnostic functions|error reporting|email transmission|' + \
               r'data payloads|domain names|inbound packets|congestion|features|core mechanism|general information|corresponding|' + \
               r'standard|interaction|communications possible|Internet communication|client application|encoded data|data submission|' + \
               r'database query|protocol version|directory structure|encryption key|hardware versions|geographical data|authentication|' + \
               r'user agent|content type|anti-malware|form submissions|JSON payloads|authorization key|security configuration|multi-faceted|structured|' + \
               r'personal data|metadata|website|webpage|web traffic|cached version|unencrypted data transfer|action indicator|HTTP verb|' + \
               r'key-value pairs|textual information|text-based details|structured pairs|metadata|instructions|client browser details|requested data|' + \
               r'parameters|JSON syntax|URL parameters|cookie data|session identifiers|browser metadata|form data|multipart form data|URL-encoded key-value pairs|' + \
               r'HTTP request body|body of an HTTP request|information being transferred|data payload|submitted information|form inputs|internet server|web client|' + \
               r'web clients|internet servers|content details|status details|encryption status|protocol in use|unencrypted resources|encrypted resources|caching|' + \
               r'offline caching|direct reply|content returned|specifics of the preceding request|valuable information|offline data|HTTP status code|status codes|' + \
               r'language information|language|reading mode|requested information|default error message|stateless protocol|stateful sessions|persistent session data|self-contained|' + \
               r'caches resources|indefinite caching|tracking user data|original specification|non-persistent|persistent connections|data transfer|reliable data transmission|overhead|' + \
               r'subsequent requests|resource consumption|TCP handshakes|sockets|deliberately closed|OSI model|application layer attacks|network layer attacks|session layer attacks|physical layer attacks|' + \
               r'denial-of-service|distributed denial-of-service|DoS|DDoS|excessive requests|massive request volumes|strategic request volumes|legitimate access)\b'
    text = re.sub(web_terms, r'<span class="odp-green">\1</span>', text)
    
    # Add individual web/internet terms (green)
    web_terms_individual = r'\b(World|Wide|Web|website|webpage|page|pages|internetworking|browser|browsers|server|servers|client|clients|' + \
                          r'request|requests|response|responses|datum|resource|system|foundation|content|communication|communicate|' + \
                          r'inform|information|transfer|transfers|packet|packets|frame|frames|message|messages|record|records|address|' + \
                          r'addresses|route|routes|traffic|transact|transaction|transactions|network|networks|device|medium|media|' + \
                          r'interact|interactive|text|texts|login|logins|command|commands|operation|operations|sequence|sequences|' + \
                          r'hyper|link|links|linked|site|sites|exchange|exchanges|diagnostic|diagnose|report|reports|email|emails|' + \
                          r'payload|payloads|domain|domains|inbound|outbound|incoming|outgoing|congest|congestion|feature|features|' + \
                          r'core|mechanism|mechanisms|general|correspond|corresponds|standard|standards|interact|interacts|interaction|interactions|' + \
                          r'encode|encoded|submit|submission|query|queries|encrypt|encryption|version|versions|structure|structured|' + \
                          r'authenticate|authentication|agent|agents|type|types|malware|form|forms|security|secure|multi|faceted|token|tokens|' + \
                          r'key|keys|value|values|pair|pairs|textual|text-based|detail|details|instruction|metadata|parameter|parameters|syntax|' + \
                          r'URL|cookie|cookies|session|identifier|identifiers|body|multipart|submitted|inputs|JSON|XML|offline|data|precedence|preceding|' + \
                          r'valuable|returned|direct|unencrypted|encrypted|specifics|details|requested|asked|language|reading|mode)\b'
    text = re.sub(web_terms_individual, r'<span class="odp-green">\1</span>', text)
    
    # Highlight networking components and hardware (red for variables/tags)
    components = r'\b(server|client machine|router|switch|firewall|DNS queries|static IP address|email message|browsers|hosts|' + \
                r'machine addresses|physical machine|networked devices|MAC address|server-side scripts|storage|file system path|' + \
                r'web host|domain registrar|verification token|DNS resolver|anti-malware signature|firewall configuration|' + \
                r'time-based one-time password|hardware versions|database system|server resource|server memory capacity|' + \
                r'compression settings|physical hardware|operating system level|hardware configuration|programming language|' + \
                r'network analysis tools|browser\'s developer tools|DNS records|user-agent strings|database schema|IP address|network tab|' + \
                r'username|password|credentials|user credentials|client hardware|DNS root record|SSL private key|blockchain ledger|' + \
                r'DNS infrastructure|device driver|driver updates|client hardware|routing table|server\'s private key|zone transfers|' + \
                r'add-ons manager|reading mode|data inspector|browser extensions|raw HTTP traffic|unauthorized users|unauthorized access|target device|' + \
                r'hardware and signal transmission|IP-based operations)\b'
    text = re.sub(components, r'<span class="odp-red">\1</span>', text)
    
    # Add individual component words (red)
    components_individual = r'\b(machine|machines|router|routers|switch|switches|firewall|firewalls|query|queries|static|dynamic|' + \
                           r'host|hosts|address|addresses|physical|hardware|networked|network|device|devices|browser|browsers|' + \
                           r'MAC|server-side|script|scripts|storage|file|path|paths|host|hosts|registrar|registrars|verification|' + \
                           r'resolver|resolvers|signature|signatures|configuration|configurations|password|passwords|time-based|' + \
                           r'database|system|systems|memory|capacity|compression|level|resource|resources|hardware-level|setup|' + \
                           r'programming|language|languages|environment|environments|analysis|tools|tool|tab|tabs|developer|schema|schemas|' + \
                           r'string|strings|record|records|user-agent|username|credential|credentials|root|ledger|driver|drivers|private|' + \
                           r'zone|zones|transfer|transfers|infrastructure|SSL|SMTP|FTP|add-ons|manager|data|inspector|extensions|raw|unauthorized|access)\b'
    text = re.sub(components_individual, r'<span class="odp-red">\1</span>', text)
    
    # Highlight "not" statements in incorrect explanations
    text = re.sub(r'\b(not|rather than|instead of|does not|cannot|no|never|unrelated|confuses|mandatory|compulsory|required|typically|generally|occur|only|beyond|contradicting)\b', r'<span class="odp-red">\1</span>', text)
    
    # Convert markdown to HTML using Anki's built-in markdown
    html = markdown.markdown(text)
    
    # Remove paragraph tags around the text (Anki adds its own)
    html = re.sub(r'^\s*<p>(.*?)</p>\s*$', r'\1', html, flags=re.DOTALL)
    
    # Convert code blocks to match Anki's styling with better formatting
    html = re.sub(
        r'```(\w*)\s*(.*?)```',  # Modified to capture language and handle multiline
        lambda m: format_code_block(m.group(2), m.group(1) if m.group(1) else None),
        html,
        flags=re.DOTALL
    )
    
    return html

def format_code_block(code, language=None):
    """Format a code block with proper styling and line breaks."""
    # Clean up the code
    code = code.strip()
    
    # Process the code block
    lines = []
    for line in code.split('\n'):
        # Escape HTML special characters
        line = (line.replace('&', '&amp;')
                   .replace('<', '&lt;')
                   .replace('>', '&gt;'))
        # Add proper indentation
        line = line.replace(' ', '&nbsp;')
        lines.append(line)
    
    code = '<br>'.join(lines)
    
    # Only add language class if a valid language is specified
    lang_class = f" class=\"language-{language}\"" if language and language.strip() else ""
    return f'''
    <div class="code-block">
        <pre><code{lang_class}>{code}</code></pre>
    </div>
    '''

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
[Insert option text here] 

##### Explanation
[Insert detailed explanation on why this option is correct]

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
        
        # First, clean up any variations of the Explanation header
        text = re.sub(r'##### Explanation.*?\n', '##### Explanation\n', text)
        
        # Parse sections using regex
        sections = {}
        
        # Extract question
        question_match = re.search(r'#### Question\s*\n(.*?)(?=\n(?:___|---)|\Z)', text, re.DOTALL)
        if question_match:
            sections['question'] = question_match.group(1).strip()
        
        # Initialize correct options list
        sections['correct_options'] = []
        
        # Find all correct options sections
        correct_sections = re.finditer(
            r'#### Correct Option\s*\n(.*?)(?=\n##### Explanation\s*\n)' +  # Option text (multi-line)
            r'\n##### Explanation\s*\n(.*?)(?=\n(?:___|---)|\Z)',  # Explanation
            text, re.DOTALL
        )
        
        for match in correct_sections:
            sections['correct_options'].append({
                'option': match.group(1).strip(),
                'explanation': match.group(2).strip()
            })
        
        # Extract incorrect options
        incorrect_sections = re.finditer(
            r'#### Incorrect Option\s*\n(.*?)(?=\n##### Explanation\s*\n)' +  # Option text (multi-line)
            r'\n##### Explanation\s*\n(.*?)(?=\n(?:___|---)|\Z)',  # Explanation
            text, re.DOTALL
        )
        
        sections['incorrect_options'] = []
        for match in incorrect_sections:
            sections['incorrect_options'].append({
                'option': match.group(1).strip(),
                'explanation': match.group(2).strip()
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
            
            # Create note with version number
            model_name = f"ExamCard{correct_count}{incorrect_count}v2"
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
            
            # Add incorrect options
            for i, incorrect in enumerate(sections['incorrect_options'], 1):
                note[f'IncorrectOption{i}'] = convert_markdown_to_html(incorrect['option'])
                note[f'IncorrectExplanation{i}'] = convert_markdown_to_html(incorrect['explanation'])
            
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
    """Create an exam note type with code examples."""
    model_name = f"ExamCard{correct_options}{incorrect_options}v1"
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
        
        <!-- This container will hold all explanation entries in the randomized order -->
        <div class="answer" id="answers"></div>

        <script>
            // Build an array of all items in the same order they were added on the front side:
            var allItems = [
                """ + ",\n".join([
                    f"{{ content: `{{{{CorrectOption{str(i + 1) if correct_options > 1 else ''}}}}}`, explanation: `{{{{CorrectExplanation{str(i + 1) if correct_options > 1 else ''}}}}}`, isCorrect: true }}"
                    for i in range(correct_options)
                ]) + (
                    ",\n" if correct_options and incorrect_options else ""
                ) + ",\n".join([
                    f"{{ content: `{{{{IncorrectOption{i + 1}}}}}`, explanation: `{{{{IncorrectExplanation{i + 1}}}}}`, isCorrect: false }}"
                    for i in range(incorrect_options)
                ]) + """
            ];

            function buildAnswerContainers() {
                try {
                    var mappingStr = document.body.getAttribute('data-option-mapping');
                    if (!mappingStr) return; // No mapping found
                    var mapping = JSON.parse(mappingStr);
                    var stO = mapping.shuffledToOriginal; // Maps displayedIndex -> originalIndex
                    var answersDiv = document.getElementById('answers');
                    if (!answersDiv) return;
                    
                    // Get the question text
                    var questionDiv = document.querySelector('.question');
                    var questionText = questionDiv ? questionDiv.textContent : '';
                    
                    // Clear existing content
                    answersDiv.innerHTML = '';

                    // Build explanation containers in the same order as displayed on the front
                    for (var newIndex = 0; newIndex < allItems.length; newIndex++) {
                        var originalIndex = stO[newIndex];
                        var item = allItems[originalIndex];
                        // Create container
                        var container = document.createElement('div');
                        container.className = 'explanation-container ' + 
                            (item.isCorrect ? 'correct-answer' : 'incorrect-answer');
                        container.setAttribute('data-option-index', originalIndex);
                        
                        container.innerHTML = `
                            <div class="question-reference">Q: ${questionText}</div>
                            <div class="option-header">${item.content}</div>
                            <div class="explanation">${item.explanation}</div>
                        `;
                        answersDiv.appendChild(container);
                    }
                } catch (err) {
                    console.error('Error building answer containers:', err);
                }
            }

            // Prism and highlightSelection logic is kept, but updated to highlight the newly added containers
            function highlightSelection() {
                try {
                    var selectedOptionsStr = document.body.getAttribute('data-selected-options');
                    if (!selectedOptionsStr) return;

                    var selectedOptions = JSON.parse(selectedOptionsStr);
                    var containers = document.querySelectorAll('.explanation-container');
                    
                    // Mark any options that were selected
                    containers.forEach(container => {
                        const optionIndex = parseInt(container.getAttribute('data-option-index'));
                        if (selectedOptions.includes(optionIndex)) {
                            container.classList.add('was-selected');
                            const header = container.querySelector('.option-header');
                            if (header) header.classList.add('was-selected');
                        }
                    });

                    // Highlight code blocks with Prism
                    document.querySelectorAll('pre code').forEach(function(block) {
                        Prism.highlightElement(block);
                    });
                } catch (error) {
                    console.error('Error in highlightSelection:', error);
                }
            }

            // Build explanations and then highlight
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', () => {
                    buildAnswerContainers();
                    highlightSelection();
                });
            } else {
                buildAnswerContainers();
                highlightSelection();
            }
        </script>
        """

        # Add CSS - One Dark Pro theme with syntax highlighting
        m['css'] = """
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
            border-left: 4px solid #61afef;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            transition: all 0.3s ease;
        }

        /* One Dark Pro syntax highlighting classes */
        .odp-red {
            color: #e06c75; /* Used for variables, properties, tags */
        }
        
        .odp-green {
            color: #98c379; /* Used for strings, web terms */
        }
        
        .odp-yellow {
            color: #e5c07b; /* Used for this, constants, programming languages */
        }
        
        .odp-blue {
            color: #61afef; /* Used for functions, methods, protocols */
        }
        
        .odp-purple {
            color: #c678dd; /* Used for keywords, protocol full names */
        }
        
        .odp-cyan {
            color: #56b6c2; /* Used for operators, technical actions */
        }
        
        .odp-orange {
            color: #d19a66; /* Used for numbers, attributes */
        }
        
        .odp-black {
            color: #5c6370; /* Used for comments, parentheses */
        }
        
        .odp-white {
            color: #abb2bf; /* Used for regular text */
        }

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
            border-left: 4px solid #56b6c2;
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

        .explanation strong {
            color: #98c379;
            font-weight: bold;
        }

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
            overflow-x: auto;
            margin: 15px 0;
            border: 1px solid rgba(62, 68, 81, 0.5);
            box-shadow: inset 0 1px 8px rgba(0, 0, 0, 0.2);
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
            overflow-x: auto;
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

        .incorrect-answer {
            border-color: rgba(224, 108, 117, 0.7);
            background-color: rgba(224, 108, 117, 0.05);
        }

        .was-selected {
            border-color: rgba(97, 175, 239, 0.7);
            box-shadow: 0 0 15px rgba(97, 175, 239, 0.2);
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
            color: #98c379;
            font-weight: bold;
        }

        .incorrect-answer .explanation strong {
            color: #e06c75;
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

        # Add template to model
        mm.add_template(m, template)
        
        # Add the model to the collection
        mm.add(m)
        return m

def init():
    # Create exam card types
    create_exam_note_type(1, 3)  # ExamCard13v1 (1 correct, 3 incorrect options)
    create_exam_note_type(1, 4)  # ExamCard14v1 (1 correct, 4 incorrect options)
    create_exam_note_type(1, 5)  # ExamCard15v1 (1 correct, 5 incorrect options)
    create_exam_note_type(2, 3)  # ExamCard23v1 (2 correct, 3 incorrect options)
    create_exam_note_type(3, 2)  # ExamCard32v1 (3 correct, 2 incorrect options)

# Add the init hook
gui_hooks.profile_did_open.append(init) 