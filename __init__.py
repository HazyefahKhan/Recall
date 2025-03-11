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
    
    # SECTION 1: Organization by COLOR CLASSES according to One Dark Pro Styling Highlighting Guide
    # Within each color class, we process multi-word terms before individual words
    # to ensure proper highlighting precedence

    # 1.1 - RED: Variables, properties, components, tags (.odp-red)
    # Multi-word component terms first
    components_multiword = r'\b(client machine|static IP address|email message|' + \
                         r'machine addresses|physical machine|networked devices|MAC address|server-side scripts|file system path|' + \
                         r'web host|domain registrar|verification token|DNS resolver|anti-malware signature|firewall configuration|' + \
                         r'time-based one-time password|hardware versions|database system|server resource|server memory capacity|' + \
                         r'compression settings|physical hardware|operating system level|hardware configuration|programming language|' + \
                         r'network analysis tools|browser\'s developer tools|DNS records|user-agent strings|database schema|network tab|' + \
                         r'user credentials|client hardware|DNS root record|SSL private key|blockchain ledger|' + \
                         r'DNS infrastructure|device driver|driver updates|routing table|server\'s private key|zone transfers|' + \
                         r'add-ons manager|reading mode|data inspector|browser extensions|raw HTTP traffic|unauthorized users|unauthorized access|target device|' + \
                         r'hardware and signal transmission|IP-based operations|Trumpet Winsock|TCP\/IP stack implementation|South Korean boy band|British online service|aging copper lines|wired internet connection|copper cables|deteriorating copper cables|phone masts|high-voltage power lines|cable modems|fiber cables|dedicated bandwidth|remote locations|specialized hardware|obstructive barriers|mobile hardware|network card|network card drivers|browser adoption|cloud platform|custom application logic|lower-level system operations|hardware-level elements|internal development tools|development services|development approach|major browsers|Litespeed server|Apache HTTP Server|Microsoft IIS|Node\.js server|content delivery network infrastructure|CDN infrastructure|reverse proxy server|dedicated reverse proxy|third-party libraries|external dependencies|closed-source modules|proprietary scripting|verified work|QUIC-based implementations|unproven libraries|production environments|e-commerce sites|public IP address|internal domain|universal code|hardware identifiers|offline servers|offline backups|security systems|local network connections|local networks|shared internal domain)\b'
    text = re.sub(components_multiword, r'<span class="odp-red">\1</span>', text)
    
    # Then individual component terms
    components_individual = r'\b(machine|machines|router|routers|switch|switches|firewall|firewalls|query|queries|static|dynamic|' + \
                          r'host|hosts|address|addresses|physical|hardware|networked|network|device|devices|browser|browsers|' + \
                          r'MAC|server-side|script|scripts|storage|file|path|paths|host|hosts|registrar|registrars|verification|' + \
                          r'resolver|resolvers|signature|signatures|configuration|configurations|password|passwords|time-based|' + \
                          r'database|system|systems|memory|capacity|compression|level|resource|resources|hardware-level|setup|' + \
                          r'programming|language|languages|environment|environments|analysis|tools|tool|tab|tabs|developer|schema|schemas|' + \
                          r'string|strings|record|records|user-agent|username|credential|credentials|root|ledger|driver|drivers|private|' + \
                          r'zone|zones|transfer|transfers|infrastructure|add-ons|manager|data|inspector|extensions|raw|unauthorized|access|' + \
                          r'Trumpet|Winsock|stack|implementation|boy|band|CIX|British|service|copper|lines|aging|deteriorating|cables|masts|voltage|modems|fiber|dedicated|bandwidth|remote|specialized|barriers|mobile|' + \
                          r'Litespeed|Apache|IIS|NGINX|Node\.js|CDN|CDNs|reverse|proxy|libraries|dependencies|modules|proprietary|verified|production|e-commerce|' + \
                          r'server|router|switch|firewall|DNS|browsers|hosts|IP|SSL|SMTP|FTP|CPU|GPU|IPv4|IPv6|backbone|' + \
                          r'not|rather than|instead of|does not|cannot|no|never|unrelated|confuses|mandatory|compulsory|required|typically|generally|occur|only|beyond|contradicting)\b'
    text = re.sub(components_individual, r'<span class="odp-red">\1</span>', text)

    # 1.2 - GREEN: Strings, URLs, web-related terms (.odp-green)
    # Multi-word web terms first
    web_multiword = r'\b(World Wide Web|hypertext links|hypertext-linked|website content|diagnostic functions|error reporting|email transmission|' + \
                  r'data payloads|domain names|inbound packets|core mechanism|general information|Internet communication|client application|encoded data|data submission|' + \
                  r'database query|protocol version|directory structure|encryption key|hardware versions|geographical data|' + \
                  r'user agent|content type|anti-malware|form submissions|JSON payloads|authorization key|security configuration|multi-faceted|' + \
                  r'personal data|web traffic|cached version|unencrypted data transfer|action indicator|HTTP verb|' + \
                  r'key-value pairs|textual information|text-based details|structured pairs|client browser details|requested data|' + \
                  r'JSON syntax|URL parameters|cookie data|session identifiers|browser metadata|form data|multipart form data|URL-encoded key-value pairs|' + \
                  r'HTTP request body|body of an HTTP request|information being transferred|data payload|submitted information|form inputs|internet server|web client|' + \
                  r'web clients|internet servers|content details|status details|encryption status|protocol in use|unencrypted resources|encrypted resources|' + \
                  r'offline caching|direct reply|content returned|specifics of the preceding request|valuable information|offline data|HTTP status code|status codes|' + \
                  r'language information|requested information|default error message|stateless protocol|stateful sessions|persistent session data|self-contained|' + \
                  r'caches resources|indefinite caching|tracking user data|original specification|non-persistent|persistent connections|data transfer|reliable data transmission|' + \
                  r'subsequent requests|resource consumption|TCP handshakes|deliberately closed|OSI model|application layer attacks|network layer attacks|session layer attacks|physical layer attacks|' + \
                  r'denial-of-service|distributed denial-of-service|excessive requests|massive request volumes|strategic request volumes|legitimate access|online conferencing system|message board|British online service|South Korean boy band|formal communications|personal computers|internet access|dial-up internet access|bullet data|game player|player data|game bullets|lost packet|rapid data transmissions|fire and forget|loss-tolerant data|rapid transmissions|internet\'s popularity|internet\'s widespread use|security layer|security protocol|key security protocol|packet loss|aging copper lines|copper lines|copper cables|wired lines|wired connections|wired internet connections|Internet connectivity|portable connectivity|obstructive barriers|phone masts|man-in-the-middle attacks|home internet usage|on-the-go connectivity|security best practices|mobile internet usage|late 2020|early 2016|early 2022|late 2019|25 July 2022|30 June 2022|10 August 2022|1 September 2022|version numbers|protocol adoption status|browser development approach|test connection|mobile device users|cellular connections|corporate office workers|local networks|public library patrons|shared terminals|satellite internet subscribers|remote areas|domain registrar|caching plugin|content delivery network deployment|private hardware|HTTP\/3 adoption|uneven adoption|unevenly adopted|web server environment|QUIC-based implementations|user experience advantages|metaverse worlds|security and speed|human-readable address|human-readable solution|memorable addresses|global Internet|global DNS|global recognition|Internet infrastructure|Internet routing|random sequence of numbers|temporary code|one-time codes|text-only URL|numeric elements)\b'
    text = re.sub(web_multiword, r'<span class="odp-green">\1</span>', text)
    
    # Then individual web terms
    web_individual = r'\b(web|internet|online|browser|server|client|request|response|data|resources|systems|foundation|basis|' + \
                    r'content|communications|information|transfer|packet|frame|message|record|address|routing|addressing|traffic|transaction|' + \
                    r'network|devices|media|interactive|text|login|command|error|operational|flow|sequence|hypertext|' + \
                    r'webpages|exchange|congestion|features|mechanism|corresponding|' + \
                    r'standard|interaction|communications|possible|application|submission|' + \
                    r'authentication|agent|type|types|malware|form|forms|security|secure|multi|faceted|structured|' + \
                    r'metadata|website|webpage|verb|' + \
                    r'parameters|syntax|URL|cookie|cookies|session|identifier|identifiers|body|multipart|submitted|inputs|JSON|XML|offline|data|precedence|preceding|' + \
                    r'language|reading|mode|reliability|reliable|overhead|sockets|DoS|DDoS|noise|interference|wireless|attacks|unauthorized|man-in-the-middle|mobile|fiber|QUIC|QUIC\'s|DSL|satellite|remote|standardized|production|dependencies|Web3|metaverse|' + \
                    r'World|Wide|Web|website|webpage|page|pages|internetworking|browser|browsers|server|servers|client|clients|' + \
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
                    r'cookie|session|identifier|identifiers|body|multipart|submitted|inputs|JSON|XML|offline|data|precedence|preceding|' + \
                    r'valuable|returned|direct|unencrypted|encrypted|specifics|details|requested|asked|language|reading|mode|boy|band|conferencing|connectivity|bullet|bullets|formal|lost|rapid|fire|forget|reliability|reliable|internet\'s|widespread|popularity|copper|lines|noise|interference|wired|connections|aging|connectivity|portable|obstructive|barriers|masts|phone|wireless|attacks|home|mobile|fiber|remote|memorable|human-readable|numerical|numeric|global)\b'
    text = re.sub(web_individual, r'<span class="odp-green">\1</span>', text)

    # 1.3 - YELLOW: Constants, structural keywords, concepts (.odp-yellow)
    # Multi-word concept terms first
    yellow_multiword = r'\b(application layer|transport layer|network layer|link layer|protocol definitions|' + \
                      r'Type Checkers|GraphQL schema|JSON keys|YAML attributes|configuration keys|' + \
                      r'Cloud Design Patterns|Design Patterns|Web Security|Web Accessibility|Server-side rendering|' + \
                      r'OSI model|TCP\/IP model|protocol stack|network architecture|backbone of the Internet)\b'
    text = re.sub(yellow_multiword, r'<span class="odp-yellow">\1</span>', text)
    
    # Then individual concept terms
    yellow_individual = r'\b(encryption|security|constants|enums|metadata|annotations|' + \
                       r'class|interface|enum|extends|implements|types|interfaces|' + \
                       r'Architecture|Scalability|Authentication|Virtualization|Containerization|backbone)\b'
    text = re.sub(yellow_individual, r'<span class="odp-yellow">\1</span>', text)

    # 1.4 - BLUE: Functions, methods, network protocols, server operations (.odp-blue)
    # Multi-word protocol terms first
    protocol_multiword = r'\b(HTTP protocol|HTTPS protocol|FTP protocol|SMTP protocol|SSH protocol|HTTP\/3 protocol|' + \
                        r'HTTP request|HTTP method|HTTP header|HTTP body|HTTP version|HTTP version type|HTTP verb|HTTP status|HTTP headers|HTTP response|' + \
                        r'HTTP response codes|HTTP status code|HTTP response headers|HTTP response body|HTTP stateless protocol|HTTP stateful protocol|' + \
                        r'HTTP compliance|HTTP adoption|HTTP support|HTTP implementation|HTTP deployment|HTTP benefits|HTTP libraries|' + \
                        r'HTTP response|HTTP request|HTTP body|HTTP status code|HTTP response headers|HTTP response body|HTTP connection|' + \
                        r'HTTP compliance|HTTP adoption|HTTP support|response body|encrypted payload|browser cookie|numeric status code|session token|' + \
                        r'TCP connection|persistent connection|non-persistent connection|connection-oriented|connectionless|HTTP\/3 compliance|HTTP\/3 adoption|' + \
                        r'HTTP\/3 support|HTTP\/3 implementation|HTTP\/3 deployment|HTTP\/3 benefits|HTTP\/3 libraries|QUIC functionality|QUIC protocol|QUIC-based|address resolution)\b'
    text = re.sub(protocol_multiword, r'<span class="odp-blue">\1</span>', text)
    
    # HTTP status codes with descriptions
    text = re.sub(r'\b(\d{3})\s+(OK|Not Found|Multiple Choices|Continue|Internal Server Error|Moved Permanently)\b', 
                r'<span class="odp-blue">\1 \2</span>', text)
    
    # Protocols with layers - special case with two different colors
    text = re.sub(r'\b(HTTP|HTTPS|FTP|SMTP|ICMP|TCP|IP|UDP|DNS|SSH|TLS|SSL|ARP|IMAP)(\s+at\s+the\s+)(application layer|transport layer|network layer|link layer)\b', 
                r'<span class="odp-blue">\1</span>\2<span class="odp-yellow">\3</span>', text)
    
    # Then individual protocol terms
    protocol_pattern = r'\b(HTTP|HTTPS|FTP|SMTP|ICMP|TCP|IP|UDP|DNS|SSH|TLS|SSL|ARP|IMAP|HTTP\/1\.1|HTTP\/2|HTTP\/3|HTTP 1\.1|QUIC)\b(?!\w)'
    text = re.sub(protocol_pattern, r'<span class="odp-blue">\1</span>', text)
    
    # HTTP methods
    text = re.sub(r'\b(GET|POST|PUT|DELETE|HEAD|OPTIONS|PATCH)\b', r'<span class="odp-blue">\1</span>', text)
    
    # 1.5 - PURPLE: Keywords, data types, languages, frameworks (.odp-purple)
    # Multi-word language/framework terms first
    protocol_full_names = r'(Hypertext Transfer Protocol|File Transfer Protocol|Simple Mail Transfer Protocol|Internet Control Message Protocol|' + \
                         r'Transmission Control Protocol|User Datagram Protocol|Domain Name System|Secure Shell Protocol|Transport Layer Security|' + \
                         r'Secure Sockets Layer|Internet Protocol|Address Resolution Protocol|Quick UDP Internet Connections)'
    
    text = re.sub(f'{protocol_full_names}(\\s*\\(([^)]+)\\))', 
                r'<span class="odp-purple">\1</span><span class="odp-black">\2</span>', text)
    
    # HTTP status code families
    text = re.sub(r'\b(\d)xx\b', r'<span class="odp-purple">\1xx</span>', text)
    
    # Then individual language/keyword terms
    protocol_keywords = r'\b(Hypertext|Transfer|Protocol|File|Simple|Mail|Internet|Control|Message|Transmission|' + \
                       r'User|Datagram|Domain|Name|System|Secure|Shell|Transport|Layer|Security|Sockets|Address|Resolution|Quick|IPv4|IPv6)\b'
    text = re.sub(protocol_keywords, r'<span class="odp-purple">\1</span>', text)
    
    # 1.6 - CYAN: Technical actions, operators, operations (.odp-cyan)
    # Multi-word action terms first
    action_multiword = r'\b(relies on|runs on top of|resides in|below|above|on top of|included in|part of|built on top of|built for|suited for|operates above|operates on|designed for|' + \
                     r'converts HTML into a webpage|removes HTML content|stores HTML as a text file|encrypts HTML for security|hard to remember|difficult to remember|easy to remember|memorize|recall|identify the server owner|determine the operator|reassign|might change over time|remain the same|remain constant)\b'
    text = re.sub(action_multiword, r'<span class="odp-cyan">\1</span>', text)
    
    # Then individual action terms
    action_individual = r'\b(relies|runs|resides|below|above|top|included|part|built|suited|operates|designed|renders|rendering|' + \
                       r'transfer|transfers|transmitted|transmits|request|response|responses|load|loads|handle|service|map|route|' + \
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
                              r'convey|conveys|travel|travels|parse|parses|capture|captures|show|shows|prevent|prevents|manage|manages|inspect|inspects|simplify|simplifies|download|downloads|guarantee|guarantees|establish|establishes|disrupt|disrupts|wait|waits|acknowledge|acknowledges|allow|allows|disappear|disappeared|enable|enables|connect|connects|supply|supplies|introduce|introduces|result|results|manage|manages|handle|handles|' + \
                              r'promote|promotes|advance|advances|prioritize|prioritizes|shift|shifts|standardize|standardizes|endorse|endorses|experience|experiences|implement|implements|migrate|migrates|add|adds|face|faces|reuse|reuses|serve|serves|maintain|maintains|depend|depends|develop|develops|run|runs|memorize|recall|remember|identify|determine|reassign|change|remain|convert|mask|access|route|process|interpret)\b'
    text = re.sub(action_individual, r'<span class="odp-cyan">\1</span>', text)

    # 1.7 - ORANGE: Numbers, attributes, values, configurations (.odp-orange)
    # Multi-word architecture/configuration terms first
    orange_multiword = r'\b(TCP\/IP stack|OSI reference model|hardware-level addressing|caching policy|offline handshake|content delivery network|hexadecimal format|numerical segments|numerical complexity|numerical sequences|numeric IP addresses|numeric identifiers|numerical notation)\b'
    text = re.sub(orange_multiword, r'<span class="odp-orange">\1</span>', text)
    
    # Then individual architecture/configuration terms
    architecture_keywords = r'\b(application|transport|network|layer|layers|link|physical|model|stack|protocol|protocols|lower-level|TCP\/IP|OSI|request|line|resource|address|URL|URI|hardware-level|addressing|status|encryption|keys|values|pairs|format|content|caching|policy|policies|offline|handshake|security|process|zone|transfers|resolution|driver|updates|digit|digits|standardized|communication|specificity|complexity|redirect|download|speed|conditions|capacity|measures|payment|access|styling|presentation|metadata|client|server|browser|web|reliable|unreliable|ordering|delivery|retransmissions|hexadecimal|segments|notation|complexity|sequences|identifiers)\b'
    text = re.sub(architecture_keywords, r'<span class="odp-orange">\1</span>', text)
    
    # 1.8 - BLACK: Comments, descriptive text (.odp-black)
    # This is applied in protocol_full_names regex above

    # Note: The white color (.odp-white) would be the default color for text without specific categorization 
    # so we don't need to explicitly apply it
    
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
            model_name = f"ExamCard{correct_count}{incorrect_count}v3"
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
    model_name = f"ExamCard{correct_options}{incorrect_options}v3"
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
            font-family: 'Fira Code', Consolas, 'Courier New', monospace;
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
            border-left: 4px solid #e5c07b;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            transition: all 0.3s ease;
        }

    /* One Dark Pro Syntax Highlighting Guide*/

    .odp-red {
        color: #e06c75; /* Variables, properties, tags, custom elements, HTML/XML tags, component names, Web Components, GraphQL fields */
    }

    .odp-green {
        color: #98c379; /* Strings, URLs, file paths, web-related terms (Frontend, Backend, DevOps, Internet, HTML, CSS, Progressive Web Applications, Static Site Generators, Frameworks, Architecture terms) */
    }

    .odp-yellow {
        color: #e5c07b; /* Constants, enums, metadata, annotations, protocol definitions, structural keywords (class, interface, enum, extends, implements), types/interfaces, Type Checkers annotations, GraphQL schema definitions, JSON keys, YAML attributes, configuration keys, Protocol definitions, important concepts (Architecture, Scalability, Cloud Design Patterns, Design Patterns, Authentication, Web Security, Web Accessibility, Server-side rendering, Virtualization, Containerization) */
    }

    .odp-blue {
        color: #56b6c2; /* Functions, methods, API endpoints, cloud operations, network protocols, server operations (HTTP, HTTPS, FTP, SSH, Cloud Providers, Serverless, Protocols, Provisioning, Terminal commands, Operating Systems, Shell scripting commands, CLI tools, Module Bundlers, Build Tools, Package Managers, Linters and Formatters, Testing frameworks, Terminal commands, Virtual Environments) */
    }

    .odp-purple {
        color: #c678dd; /* Keywords, data types, modules, frameworks, libraries, preprocessors, programming languages (JavaScript, TypeScript, Python, Java, Rust, etc.), Frameworks (React, Vue, Angular, Express, Django, Next.js, Static Site Generators, Progressive Web Applications, Web Frameworks), Type Checkers, Module Bundlers, Framework-related annotations, middleware components, GraphQL schemas, Static Site Generators */
    }

    .odp-cyan {
        color: #56b6c2; /* Operators, technical actions, mathematical operations, logical operators, CI/CD actions, Deployment commands, Version Control Systems (VCS) operations (Git commands), Package Manager commands (npm, yarn), Infrastructure as Code (IaC), Provisioning commands, Container orchestration, build actions, deployment scripts */
    }

    .odp-orange {
        color: #d19a66; /* Numbers, attributes, numeric values, configuration values, ports, indexes, performance metrics, Real-Time Data streams, Message Broker topics, caching strategies, numerical parameters, attributes, identifiers, Static Site Generation parameters, Progressive Web Application (PWA) configurations, Operating System identifiers, Web Server ports/configurations, HTTP status codes */
    }

    .odp-black {
        color: #5c6370; /* Comments, parentheses, brackets, braces, documentation annotations, descriptive texts, explanatory notes, generic terms, placeholder text, negation terms, general explanatory or supplemental information */
    }

    .odp-white {
        color: #abb2bf; /* Default text, regular code elements, normal punctuation, general documentation, descriptions, narrative text, plain content without specific technical categorization */
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

# Add the init hook
gui_hooks.profile_did_open.append(init) 