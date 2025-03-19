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
    # Helper function to prevent highlighting text that's already in span tags
    # This prevents nested span tags and resolves issues with overlapping highlighting patterns
    # which would otherwise result in malformed HTML like:
    # <span class="odp-blue">HTTP</span> <span class="odp-green"><span class="odp-blue">protocol</span></span>
    def safe_highlight(pattern, replacement, text, flags=0):
        # Use a more precise regex for span tags that avoids overly greedy matching
        # Non-greedy matching with specific class pattern for our syntax highlighting
        span_pattern = r'<span class="odp-[^"]*">[^<>]*?</span>'
        
        # Split the text into chunks (spans and non-spans)
        chunks = []
        last_end = 0
        
        # Find all existing span tags with our specific class pattern
        for match in re.finditer(span_pattern, text):
            start, end = match.span()
            
            # Add text before the span
            if start > last_end:
                chunks.append((text[last_end:start], False))
            
            # Add the span
            chunks.append((match.group(), True))
            last_end = end
        
        # Add remaining text
        if last_end < len(text):
            chunks.append((text[last_end:], False))
        
        # Process only non-span chunks
        result = ""
        for chunk, is_span in chunks:
            if is_span:
                result += chunk
            else:
                result += re.sub(pattern, replacement, chunk, flags=flags)
        
        return result
    
    # Convert single tilde with backticks to del tags (removing backticks)
    text = re.sub(r'`~([^~\n]+)~`', r'~\1~', text)
    
    # Convert double tilde with backticks to del tags (removing backticks)
    text = re.sub(r'`~~([^~\n]+)~~`', r'~~\1~~', text)
    
    # Convert single tilde to del tags before processing markdown
    text = re.sub(r'(?<!~)~([^~\n]+)~(?!~)', r'<del>\1</del>', text)
    
    # Convert double tildes to del tags
    text = re.sub(r'~~([^~\n]+)~~', r'<del>\1</del>', text)

    # Now use safe_highlight for all syntax highlighting patterns
    # Example of converting the first few patterns:
    
    # Apply syntax highlighting to protocols, API endpoints, and network operations (blue)
    protocol_pattern = r'\b(HTTP|HTTPS|FTP|SMTP|ICMP|TCP|IP|UDP|DNS|SSH|TLS|SSL|ARP|IMAP|HTTP\/1\.1|HTTP\/2|' \
                       r'HTTP 1\.1|Domain Name System|File Transfer Protocol|Hypertext Transfer Protocol|' \
                       r'Secure Sockets Layer|DNS servers|web browsers|DNS resolution|DNS lookup|DNS query|' \
                       r'DNS translation|bookmarking|dedicated, proprietary web browsers|social media algorithms|POP3)\b(?!\w)'
    text = safe_highlight(protocol_pattern, r'<span class="odp-blue">\1</span>', text)
    
    # Handle protocol followed by components (blue for API endpoints and operations)
    protocol_components = r'\b(HTTP|HTTPS|FTP|SMTP|SSH|TCP|IP|UDP|DNS|TLS|SSL) (protocol|request|method|header|body|version)\b'
    text = safe_highlight(protocol_components, r'<span class="odp-blue">\1</span> <span class="odp-blue">\2</span>', text)
    
    # HTTP related components (blue for API endpoints and operations)
    http_components = r'\b(HTTP (response|request|body|status code|response headers|response body|connection|' \
                      r'protocol|method|header|version|verb|authentication|caching|redirect|content type|' \
                      r'content length|user agent|host|referer|origin|accept|authorization|cookie))\b'
    text = safe_highlight(http_components, r'<span class="odp-blue">\1</span>', text)
    
    # Network operations components (blue)
    http_components_extended = r'\b(response body|encrypted payload|browser cookie|numeric status code|' \
                               r'session token|TCP connection|persistent connection|non-persistent connection|' \
                               r'keep-alive connection|connection pooling|connection timeout|handshake|' \
                               r'SSL/TLS handshake|certificate validation|cipher suite|secure connection|' \
                               r'proxy connection|load balancing|content negotiation|content delivery|' \
                               r'content compression|gzip encoding|chunked transfer|byte range|' \
                               r'request timeout|response time|latency|throughput|bandwidth|' \
                               r'DNS resolution|DNS caching|IP routing|packet transmission|' \
                               r'websocket connection|server push|client pull|polling|long polling)\b'
    text = safe_highlight(http_components_extended, r'<span class="odp-blue">\1</span>', text)
    
    # HTTP methods (blue for API endpoints/operations)
    http_methods = r'\b(GET|POST|PUT|DELETE|HEAD|OPTIONS|PATCH|CONNECT|TRACE|PROPFIND|PROPPATCH|' \
                  r'MKCOL|COPY|MOVE|LOCK|UNLOCK|SEARCH)\b'
    text = safe_highlight(http_methods, r'<span class="odp-blue">\1</span>', text)
    
    # HTTP status codes (blue for API operations)
    status_codes = r'\b(\d{3})\s+(OK|Created|Accepted|No Content|Partial Content|' \
                  r'Multiple Choices|Moved Permanently|Found|See Other|Not Modified|Temporary Redirect|' \
                  r'Bad Request|Unauthorized|Forbidden|Not Found|Method Not Allowed|Not Acceptable|' \
                  r'Request Timeout|Conflict|Gone|Length Required|Precondition Failed|' \
                  r'Payload Too Large|URI Too Long|Unsupported Media Type|Range Not Satisfiable|' \
                  r'Expectation Failed|Unprocessable Entity|Too Early|Upgrade Required|' \
                  r'Internal Server Error|Not Implemented|Bad Gateway|Service Unavailable|' \
                  r'Gateway Timeout|HTTP Version Not Supported|Variant Also Negotiates|' \
                  r'Insufficient Storage|Loop Detected|Not Extended|Network Authentication Required|Continue)\b'
    text = safe_highlight(status_codes, r'<span class="odp-blue">\1 \2</span>', text)
    
    # HTTP status code families (blue for API operations)
    http_status_families = r'\b(1xx Informational|2xx Success|3xx Redirection|4xx Client Error|5xx Server Error)\b'
    text = safe_highlight(http_status_families, r'<span class="odp-blue">\1</span>', text)
    
    # HTTP headers (blue for API operations)
    http_headers = r'\b(Content-Type|Content-Length|Authorization|User-Agent|Accept|Accept-Encoding|' \
                   r'Accept-Language|Cache-Control|Connection|Cookie|Host|Origin|Referer|' \
                   r'X-Requested-With|X-Forwarded-For|X-Forwarded-Proto|X-CSRF-Token|' \
                   r'Access-Control-Allow-Origin|Access-Control-Allow-Methods|' \
                   r'Access-Control-Allow-Headers|Access-Control-Max-Age|' \
                   r'ETag|Last-Modified|If-Modified-Since|If-None-Match|' \
                   r'Strict-Transport-Security|X-Content-Type-Options|X-Frame-Options|' \
                   r'X-XSS-Protection|Content-Security-Policy|Public-Key-Pins)\b'
    text = safe_highlight(http_headers, r'<span class="odp-blue">\1</span>', text)
    
    # Cloud services (blue for functions and endpoints)
    cloud_services = r'\b(AWS Lambda|Azure Functions|Google Cloud Functions|S3 bucket|EC2 instance|RDS database|' \
                    r'DynamoDB|Lambda function|Step Function|CloudFormation|CloudFront|ECS|EKS|Fargate|' \
                    r'Azure App Service|Azure Logic Apps|Cosmos DB|Blob Storage|Azure DevOps|' \
                    r'Google Cloud Run|Firebase|Firestore|BigQuery|Cloud Storage|App Engine|' \
                    r'AWS API Gateway|AWS SQS|AWS SNS|AWS Kinesis|AWS Glue|AWS Athena|AWS CloudWatch|' \
                    r'AWS IAM|AWS VPC|AWS Route53|AWS CodePipeline|AWS CodeBuild|AWS CodeDeploy|' \
                    r'Azure API Management|Azure Service Bus|Azure Event Grid|Azure Event Hubs|' \
                    r'Azure Key Vault|Azure Monitor|Azure Active Directory|Azure Virtual Network|' \
                    r'Azure DNS|Azure DevOps Pipelines|Azure Kubernetes Service|Azure Container Registry|' \
                    r'Google Cloud Pub/Sub|Google Cloud Dataflow|Google Cloud Dataproc|Google Cloud IAM|' \
                    r'Google Cloud VPC|Google Cloud DNS|Google Cloud Build|Google Kubernetes Engine|' \
                    r'Heroku|Digital Ocean|Netlify|Vercel|Cloudflare|Akamai|IBM Cloud|Oracle Cloud|' \
                    r'Alibaba Cloud|Tencent Cloud|OpenStack|VMware Cloud|Salesforce Platform|' \
                    r'serverless function|cloud function|microservice|container service|managed service|' \
                    r'cloud database|cloud storage|content delivery network|CDN|load balancer|' \
                    r'auto-scaling group|virtual machine|VM instance|Kubernetes cluster|' \
                    r'S3|EC2|RDS|VPC|IAM|SNS|SQS|EBS|ELB|ALB|NLB|ACM|WAF|' \
                    r'Lambda|Glue|Athena|EMR|Redshift|Aurora|DynamoDB|ElastiCache|' \
                    r'CloudWatch|CloudTrail|CloudFront|Route53|Cognito|Amplify|AppSync|' \
                    r'Beanstalk|Lightsail|Fargate|ECS|EKS|ECR|CodeBuild|CodePipeline|CodeDeploy)\b'
    text = safe_highlight(cloud_services, r'<span class="odp-blue">\1</span>', text)
    
    # Docker commands (blue for operations)
    docker_commands = r'\b(docker run|docker build|docker compose|docker pull|docker push|docker exec|' \
                     r'docker ps|docker images|docker rm|docker rmi|docker start|docker stop|docker restart|' \
                     r'docker-compose up|docker-compose down|docker-compose build|docker-compose logs|' \
                     r'docker volume create|docker volume ls|docker volume rm|docker volume prune|' \
                     r'docker network create|docker network ls|docker network rm|docker network prune|' \
                     r'docker logs|docker inspect|docker stats|docker top|docker attach|docker detach|' \
                     r'docker cp|docker commit|docker diff|docker history|docker info|docker version|' \
                     r'docker save|docker load|docker export|docker import|docker system prune|' \
                     r'docker container|docker image|docker service|docker swarm|docker stack|docker secret|' \
                     r'docker config|docker context|docker manifest|docker buildx|docker scan|' \
                     r'Dockerfile|docker tag|docker login|docker logout|docker search|docker hub|' \
                     r'FROM|RUN|CMD|ENTRYPOINT|WORKDIR|COPY|ADD|ENV|ARG|EXPOSE|VOLUME|USER|LABEL|HEALTHCHECK)\b'
    text = safe_highlight(docker_commands, r'<span class="odp-blue">\1</span>', text)
    
    # CI/CD operations (blue for pipeline operations)
    text = safe_highlight(r'\b(continuous integration|continuous delivery|continuous deployment|build pipeline|' \
                     r'deployment pipeline|automated testing|integration testing|unit testing|end-to-end testing|' \
                     r'smoke testing|regression testing|performance testing|load testing|stress testing|' \
                     r'GitHub Actions|CircleCI|Jenkins|TravisCI|GitLab CI|Bamboo|TeamCity|Azure DevOps|' \
                     r'AWS CodePipeline|Google Cloud Build|Drone CI|Concourse CI|Spinnaker|ArgoCD|Flux CD|' \
                     r'artifact repository|build artifact|deployment target|release candidate|release train|' \
                     r'canary deployment|blue-green deployment|rolling deployment|trunk-based development|' \
                     r'feature flags|feature toggles|A/B testing|dark launching|progressive delivery|' \
                     r'infrastructure as code|IaC|GitOps|DevOps|DevSecOps|shift left|' \
                     r'build stage|test stage|deploy stage|release stage|promote|rollback|hotfix|' \
                     r'CI/CD pipeline|workflow|job|step|task|action|trigger|webhook|' \
                     r'build matrix|build cache|build agent|build runner|build server|' \
                     r'code coverage|code quality|code scanning|static analysis|dynamic analysis|' \
                     r'security scanning|vulnerability scanning|dependency scanning|SAST|DAST|' \
                     r'approval gate|quality gate|deployment gate|manual approval|automated approval)\b', 
                     r'<span class="odp-blue">\1</span>', text)
    
    # Git operations (blue for operations)
    text = safe_highlight(r'\b(git clone|git pull|git push|git commit|git add|git merge|git rebase|' \
                    r'git checkout|git branch|git tag|git stash|git reset|git fetch|git status|' \
                    r'git log|git diff|git show|git remote|git config|git init|git blame|git reflog|' \
                    r'pull request|merge request|feature branch|release branch|master branch|main branch|' \
                    r'development branch|hotfix branch|bugfix branch|release candidate|tag|commit hash|SHA|' \
                    r'git flow|git hooks|git submodule|gitignore|git bisect|git cherry-pick|git revert|' \
                    r'git squash|git amend|git force push|git fork|git upstream|git origin|git HEAD|' \
                    r'merge conflict|conflict resolution|git blame|git history|git commit message|' \
                    r'git staging area|git index|git working tree|git repository|git remote repository|' \
                    r'git local repository|git shallow clone|git bare repository|git worktree)\b', 
                    r'<span class="odp-blue">\1</span>', text)
    
    # REST/GraphQL endpoints (blue for API endpoints)
    text = safe_highlight(r'\b(/api/|/v1/|/v2/|/v3/|/rest/|/graphql|/gql|/swagger|/openapi|' \
                   r'POST /|GET /|PUT /|DELETE /|PATCH /|OPTIONS /|HEAD /|CONNECT /|TRACE /|' \
                   r'REST API|RESTful endpoint|RESTful service|RESTful architecture|REST resource|' \
                   r'GraphQL query|GraphQL mutation|GraphQL subscription|GraphQL schema|GraphQL resolver|' \
                   r'API route|API gateway|API proxy|API facade|API middleware|API controller|' \
                   r'endpoint URL|API version|resource URL|resource identifier|resource representation|' \
                   r'query parameter|path parameter|header parameter|form parameter|cookie parameter|' \
                   r'request payload|request body|request header|request method|request URI|' \
                   r'response data|response body|response header|response code|response status|' \
                   r'API key|bearer token|OAuth token|JWT token|access token|refresh token|' \
                   r'HATEOAS|hypermedia|content negotiation|media type|content type|' \
                   r'rate limiting|throttling|pagination|filtering|sorting|projection|expansion|' \
                   r'idempotent|stateless|cacheable|uniform interface|client-server|layered system)\b', 
                   r'<span class="odp-blue">\1</span>', text)
    
    # Terminal commands and shell scripts (blue for operations)
    text = safe_highlight(r'\b(cd|ls|mkdir|rm|cp|mv|touch|cat|echo|grep|sed|awk|find|chmod|chown|' \
                       r'tar|zip|unzip|ssh|scp|rsync|curl|wget|bash|sh|./|sudo|apt|yum|brew|npm|' \
                       r'yarn|pip|cron|systemctl|service|ps|top|kill|pkill|ifconfig|traceroute|nslookup|' \
                       r'man|less|more|head|tail|sort|uniq|wc|diff|patch|ln|df|du|mount|umount|' \
                       r'ping|netstat|ss|ip|iptables|ufw|nc|telnet|ftp|sftp|git|svn|docker|podman|' \
                       r'python|python3|perl|ruby|node|java|javac|gcc|g\+\+|make|cmake|' \
                       r'history|clear|exit|logout|shutdown|reboot|poweroff|passwd|useradd|userdel|' \
                       r'groupadd|groupdel|chgrp|su|sudo|visudo|crontab|at|batch|bg|fg|jobs|' \
                       r'source|export|alias|unalias|set|unset|env|printenv|xargs|tee|tr|cut|' \
                       r'gzip|gunzip|bzip2|bunzip2|7z|7za|ar|ldd|ldconfig|strace|ltrace|' \
                       r'journalctl|dmesg|lsof|lsblk|lspci|lsusb|lsmod|modprobe|insmod|rmmod)\b', 
                       r'<span class="odp-blue">\1</span>', text)
    
    # Build tools and deployment scripts (blue for operations)
    text = safe_highlight(r'\b(make|ant|maven|gradle|webpack|babel|gulp|grunt|terraform|ansible|chef|puppet|' \
                 r'kubernetes|helm|kubectl|kustomize|skaffold|packer|vagrant|npm run|yarn build|' \
                 r'dotnet build|dotnet publish|mvn package|gradle build|CI pipeline|CD workflow|' \
                 r'bazel|buck|cargo build|cargo run|sbt|leiningen|rake|msbuild|xcodebuild|cmake|' \
                 r'ninja|qmake|autoconf|automake|configure|makefile|dockerfile|docker-compose|' \
                 r'jenkins|travis|circle ci|github actions|gitlab ci|azure pipelines|buildkite|' \
                 r'argocd|flux|spinnaker|octopus deploy|capistrano|fabric|salt|cloudformation|' \
                 r'pulumi|serverless|netlify|vercel|heroku|aws codedeploy|azure devops|' \
                 r'continuous integration|continuous deployment|continuous delivery|infrastructure as code|' \
                 r'configuration management|container orchestration|service mesh|blue-green deployment|' \
                 r'canary deployment|rolling deployment|immutable infrastructure|gitops)\b', 
                 r'<span class="odp-blue">\1</span>', text)
    
    # Database operations (blue for operations)
    text = safe_highlight(r'\b(SELECT|INSERT|UPDATE|DELETE|CREATE|DROP|ALTER|TRUNCATE|JOIN|INNER JOIN|' \
                   r'LEFT JOIN|RIGHT JOIN|FULL JOIN|WHERE|GROUP BY|ORDER BY|HAVING|UNION|' \
                   r'INDEX|PRIMARY KEY|FOREIGN KEY|CONSTRAINT|TRANSACTION|COMMIT|ROLLBACK|' \
                   r'database query|SQL statement|NoSQL operation|aggregation pipeline|' \
                   r'ACID transaction|database migration|MERGE|UPSERT|EXPLAIN|ANALYZE|EXECUTE|' \
                   r'GRANT|REVOKE|VIEW|MATERIALIZED VIEW|STORED PROCEDURE|FUNCTION|TRIGGER|' \
                   r'CASCADE|SET NULL|RESTRICT|NO ACTION|ON DELETE|ON UPDATE|REFERENCES|' \
                   r'UNIQUE|NOT NULL|CHECK|DEFAULT|AUTO_INCREMENT|IDENTITY|SEQUENCE|' \
                   r'SAVEPOINT|BEGIN TRANSACTION|START TRANSACTION|END TRANSACTION|' \
                   r'ISOLATION LEVEL|READ COMMITTED|READ UNCOMMITTED|REPEATABLE READ|SERIALIZABLE|' \
                   r'CURSOR|FETCH|DECLARE|PREPARE|EXECUTE IMMEDIATE|BIND VARIABLE|' \
                   r'PARTITION|SHARDING|REPLICATION|BACKUP|RESTORE|VACUUM|ANALYZE|' \
                   r'INDEX SCAN|TABLE SCAN|FULL SCAN|QUERY PLAN|EXECUTION PLAN|QUERY OPTIMIZATION|' \
                   r'CONNECTION POOL|DATABASE LINK|FEDERATION|SCHEMA|NAMESPACE|COLLECTION|' \
                   r'DOCUMENT|BSON|JSON|JSONB|BLOB|CLOB|TEXT|VARCHAR|INTEGER|NUMERIC|TIMESTAMP|' \
                   r'UPSERT|MERGE|FIND|FINDONE|FINDMANY|INSERTONE|INSERTMANY|UPDATEONE|UPDATEMANY|DELETEONE|DELETEMANY)\b', 
                   r'<span class="odp-blue">\1</span>', text)
    
    # Runtime methods and lifecycle hooks (blue for functions/methods)
    text = safe_highlight(r'\b(addEventListener|removeEventListener|setTimeout|setInterval|clearTimeout|' \
                     r'clearInterval|componentDidMount|componentWillUnmount|useEffect|useState|useContext|' \
                     r'constructor|destructor|ngOnInit|ngOnDestroy|onMounted|beforeDestroy|middleware|' \
                     r'beforeEach|afterEach|beforeAll|afterAll|init|dispose|@BeforeClass|@AfterClass|' \
                     r'__construct|__destruct|@Component|@Injectable|@Controller|@RequestMapping|' \
                     r'function\s+\w+|def\s+\w+|class\s+\w+|interface\s+\w+|method\s+\w+|' \
                     r'render|componentDidUpdate|shouldComponentUpdate|getDerivedStateFromProps|getSnapshotBeforeUpdate|' \
                     r'useMemo|useCallback|useRef|useReducer|useImperativeHandle|useLayoutEffect|useDebugValue|' \
                     r'ngOnChanges|ngDoCheck|ngAfterContentInit|ngAfterContentChecked|ngAfterViewInit|ngAfterViewChecked|' \
                     r'created|mounted|updated|beforeUpdate|activated|deactivated|errorCaptured|renderTracked|renderTriggered|' \
                     r'setup|watch|computed|provide|inject|onBeforeMount|onMounted|onBeforeUpdate|onUpdated|onBeforeUnmount|onUnmounted|' \
                     r'@PostConstruct|@PreDestroy|@Autowired|@Inject|@Service|@Repository|@Transactional|@Scheduled|' \
                     r'__init__|__new__|__del__|__enter__|__exit__|__call__|__getattr__|__setattr__|__getitem__|__setitem__|' \
                     r'@app.route|@blueprint.route|@before_request|@after_request|@errorhandler|@app.middleware|' \
                     r'handleChange|handleSubmit|handleClick|handleInput|onChange|onClick|onSubmit|onFocus|onBlur|onKeyDown|onKeyUp|' \
                     r'subscribe|unsubscribe|dispatch|getState|setState|forceUpdate|connect|mapStateToProps|mapDispatchToProps)\b', 
                     r'<span class="odp-blue">\1</span>', text)
    
    # Code comments (brightBlack for secondary text)
    text = safe_highlight(r'(//.*?$|/\*.*?\*/|#.*?$|--.*?$|<!--|-->|""".*?"""|\'\'\'.*?\'\'\')', 
                          r'<span class="odp-brightBlack">\1</span>', text, flags=re.MULTILINE|re.DOTALL)
    
    # Complexity annotations (brightBlack for complexity notations)
    text = safe_highlight(r'\b(O\(\d*n?(\s*log\s*n)?\)|Θ\(\d*n?(\s*log\s*n)?\)|Ω\(\d*n?(\s*log\s*n)?\)|' \
                            r'O\(1\)|O\(n\)|O\(n²\)|O\(n\^2\)|O\(n\^3\)|O\(log n\)|O\(n log n\)|O\(2\^n\)|' \
                            r'Θ\(n\)|Θ\(n²\)|Θ\(log n\)|Θ\(n log n\)|' \
                            r'worst case|average case|best case|time complexity|space complexity|' \
                            r'amortized time|amortized complexity)\b', 
                            r'<span class="odp-brightBlack">\1</span>', text)
    
    # Documentation notes (brightBlack for secondary notes)
    text = safe_highlight(r'(@param|@return|@throws|@exception|@see|@since|@version|@author|@deprecated|' \
               r'@todo|@note|@example|@file|@class|@interface|@function|@method|' \
               r'@memberof|@private|@public|@protected|@readonly|@type|@typedef|' \
               r'@param \{[\w\|\[\]]+\}|@returns \{[\w\|\[\]]+\}|@throws \{[\w\|\[\]]+\}|' \
               r'TODO:|FIXME:|NOTE:|WARNING:|HACK:|BUG:|XXX:|' \
               r':param|:return|:rtype|:raises|:type|:meta|:cvar|:ivar|' \
               r'\[(IMPORTANT|NOTE|TIP|WARNING|CAUTION|TODO)\])', 
               r'<span class="odp-brightBlack">\1</span>', text)
    
    # Code metadata (brightBlack for secondary information)
    text = safe_highlight(r'\b(v\d+\.\d+\.\d+(-[a-zA-Z0-9.]+)?|version\s+\d+\.\d+\.\d+|' \
                   r'@version\s+\d+\.\d+\.\d+|' \
                   r'line \d+|at line \d+|on line \d+|from line \d+ to \d+|' \
                   r'[Ll]ine \d+(-\d+)?( of | in )[\w\-./]+|' \
                   r'copyright ©|Copyright ©|© \d{4}|' \
                   r'MIT License|Apache License|GPL|GNU|BSD|' \
                   r'last updated|last modified|created on|' \
                   r'source:|ref:|reference:|see:|' \
                   r'file size:|memory usage:|' \
                   r'#pragma|#ifndef|#ifdef|#endif|#define|#include|#import|' \
                   r'Deprecated since|Supported in|Requires|Dependencies|' \
                   r'<summary>|</summary>|<remarks>|</remarks>)\b', 
                   r'<span class="odp-brightBlack">\1</span>', text, flags=re.IGNORECASE)
    
    # Line numbers and references (brightBlack for line indicators)
    text = safe_highlight(r'(\bL\d+\b|\bline \d+(-\d+)?\b|\blines \d+(-\d+)?\b|\bat \d+:\d+\b|' \
               r'\b\w+\.(?:py|js|java|cpp|cs|rb|go|rs|php|html|css|tsx?|jsx?):\d+\b|' \
               r'\b\w+\.(?:py|js|java|cpp|cs|rb|go|rs|php|html|css|tsx?|jsx?):\d+:\d+\b)', 
               r'<span class="odp-brightBlack">\1</span>', text)
    
    # Currently executing code elements (brightBlue for active elements)
    text = safe_highlight(r'\b(currently executing|active process|active thread|current instruction|' \
                    r'current stack frame|execution point|program counter|instruction pointer|' \
                    r'running job|now executing|currently processing|execution focus|' \
                    r'active operation|active transaction|real-time execution|' \
                    r'breakpoint hit|debugger paused|step into|step over|step out|' \
                    r'runtime focus|execution context|execution flow|code path|control flow|' \
                    r'current scope|current lexical environment|current event loop|' \
                    r'active request handling|active computation|thread of execution)\b', 
                    r'<span class="odp-brightBlue">\1</span>', text)
    
    # Main threads and primary call paths (brightBlue for primary processes)
    text = safe_highlight(r'\b(main thread|primary thread|UI thread|event loop|main process|' \
                  r'critical path|hot path|primary call path|main execution path|' \
                  r'request pipeline|core logic|central algorithm|primary workflow|' \
                  r'main program flow|essential operation|critical section|master thread|' \
                  r'dispatch queue|render thread|animation thread|parent process|' \
                  r'primary routine|key function|main entry point|program entry|' \
                  r'application lifecycle|critical execution path)\b', 
                  r'<span class="odp-brightBlue">\1</span>', text)
    
    # Interactive elements (brightBlue for focused UI elements)
    text = safe_highlight(r'\b(active link|current selection|focused element|highlighted item|' \
                          r'selected option|current tab|active view|current panel|' \
                          r'focused input|selected text|active window|current dialog|' \
                          r'modal focus|keyboard focus|hover state|active state|focus state|' \
                          r'current screen|selected row|active menu|current form field|' \
                          r'clicked button|pressed key|dragged element|active navigation|' \
                          r'active filter|current sort|expanded section|focused component)\b', 
                          r'<span class="odp-brightBlue">\1</span>', text)
    
    # Runtime states (brightBlue for execution states)
    text = safe_highlight(r'\b(runtime state|execution state|active configuration|current mode|' \
                    r'process state|thread state|operational mode|execution mode|running state|' \
                    r'active profile|current environment|deployed instance|live deployment|' \
                    r'production deployment|active session|current transaction|open connection|' \
                    r'established session|active listener|hot reload|live reloading|live editing|' \
                    r'runtime modification|dynamic reconfiguration|just-in-time compilation|' \
                    r'active binding|current mount point|active route|current breakpoint)\b', 
                    r'<span class="odp-brightBlue">\1</span>', text)
    
    # Active state keywords (brightBlue for state indicators)
    text = safe_highlight(r'\b(active|executing|running|focused|selected|current|processing|live|' \
                   r'ongoing|highlighted|in progress|in execution|now|presently|at this moment|' \
                   r'operational|connected|established|mounted|rendered|instantiated|initialized|' \
                   r'ready|responsive|real-time|concurrent|parallel)\b', 
                   r'<span class="odp-brightBlue">\1</span>', text)
    
    # Special characters and escape sequences (brightCyan for special syntax)
    text = safe_highlight(r'(\\n|\\r|\\t|\\b|\\f|\\v|\\0|\\x[0-9a-fA-F]{2}|\\u[0-9a-fA-F]{4}|' \
                   r'\\[\'\"\\]|\$\{.*?\}|`.*?`|\$\(.*?\)|&amp;|&lt;|&gt;|&quot;|&apos;|&#\d+;)', 
                   r'<span class="odp-brightCyan">\1</span>', text)
    
    # Regular expression patterns (brightCyan for regex)
    text = safe_highlight(r'(/\^?.*?[^\\]\$/|/\^?.*?\$/|' \
                    r'\[\^?[^\]]*\]|\(\?:[^)]*\)|\(\?<[^>]+>[^)]*\)|\(\?=[^)]*\)|\(\?![^)]*\)|' \
                    r'\.\*|\.\+|\.\?|\d+\{,\d+\}|\d+\{\d+,\}|\d+\{\d+,\d+\}|' \
                    r'\\d|\\w|\\s|\\b|\\W|\\S|\\D|\\B|\\A|\\Z|\\z|\\G|' \
                    r'\^|\$|\||\?|\*|\+|\\|\(|\)|\{|\}|\[|\])', 
                    r'<span class="odp-brightCyan">\1</span>', text)
    
    # Operators (brightCyan for operations)
    text = safe_highlight(r'(\+|-|\*|/|%|\^|&|\||~|!|=|<|>|\?|:|;|,|\.|' \
               r'\+=|-=|\*=|/=|%=|\^=|&=|\|=|<<=|>>=|={1,3}|!=|!==|<=|>=|<>|' \
               r'&&|\|\||>>|<<|\+\+|--|=>|\*\*|//|::|->|@|' \
               r'\.{1,3}|\?\?|!=|!==|<=|>=|\?:|=~|!~|=&gt;|&lt;=&gt;|&amp;&amp;|\|\||&lt;&lt;|&gt;&gt;)', 
               r'<span class="odp-brightCyan">\1</span>', text)
    
    # Pointer dereferencing and memory operations (brightCyan for pointer operations)
    text = safe_highlight(r'(\*\w+|->\w+|&\w+|::\*\w+|\w+\[\d+\]|\w+->\w+|\w+\.\*\w+|' \
                 r'malloc\(|free\(|new\s+\w+|delete\s+\w+|' \
                 r'reference to|dereference|pointer to|address of|memory location|' \
                 r'null pointer|dangling pointer|void pointer|function pointer|' \
                 r'stack pointer|heap allocation|memory leak|buffer overflow)', 
                 r'<span class="odp-brightCyan">\1</span>', text)
    
    # Bitwise operations (brightCyan for bit manipulation)
    text = safe_highlight(r'\b(bitwise AND|bitwise OR|bitwise XOR|bitwise NOT|bit shift|left shift|right shift|' \
                 r'bit manipulation|bit masking|bit field|bit flag|bitmask|bit pattern|bit twiddling|' \
                 r'bit counting|population count|hamming weight|bit extraction|bit insertion|bit rotation|' \
                 r'bit reversal|bit scanning|leading zeros|trailing zeros|' \
                 r'AND operation|OR operation|XOR operation|NOT operation)\b', 
                 r'<span class="odp-brightCyan">\1</span>', text)
    
    # Mathematical operations (brightCyan for math operations)
    text = safe_highlight(r'\b(addition|subtraction|multiplication|division|modulo|exponentiation|' \
              r'square root|cube root|logarithm|natural log|factorial|summation|product|' \
              r'derivative|integral|differentiation|integration|vector|matrix|determinant|' \
              r'dot product|cross product|eigenvalue|eigenvector|transform|rotation|' \
              r'linear algebra|calculus|discrete math|number theory|graph theory)\b', 
              r'<span class="odp-brightCyan">\1</span>', text)
    
    # State transitions (brightCyan for state changes)
    text = safe_highlight(r'\b(transition|state change|state machine|finite automaton|' \
                       r'transition function|transition matrix|transition table|state diagram|' \
                       r'from state|to state|current state|next state|previous state|initial state|' \
                       r'final state|accepting state|error state|' \
                       r'state transition|edge|directed edge|conditional transition|guarded transition|' \
                       r'event-driven transition|epsilon transition|token|lexeme|parser state)\b', 
                       r'<span class="odp-brightCyan">\1</span>', text)
    
    # Pipeline operators (brightCyan for data flow)
    text = safe_highlight(r'\b(pipeline|pipe|filter|map|reduce|transform|stream|flow|' \
                  r'data flow|control flow|event flow|message passing|forwarding|routing|' \
                  r'producer|consumer|publisher|subscriber|worker|orchestrator|coordinator|' \
                  r'message bus|event bus|broker|queue|topic|channel|port|' \
                  r'stdin|stdout|stderr|redirect|input redirection|output redirection)\b', 
                  r'<span class="odp-brightCyan">\1</span>', text)
    
    # Logical gates and boolean operations (brightCyan for logic)
    text = safe_highlight(r'\b(AND gate|OR gate|NOT gate|XOR gate|NAND gate|NOR gate|XNOR gate|' \
                 r'logical AND|logical OR|logical NOT|logical XOR|logical NAND|logical NOR|' \
                 r'boolean algebra|boolean logic|boolean expression|boolean operation|truth table|' \
                 r'conjunction|disjunction|negation|implication|biconditional|tautology|' \
                 r'AND operator|OR operator|NOT operator|XOR operator|logical operator)\b', 
                 r'<span class="odp-brightCyan">\1</span>', text)
    
    # Query operators (brightCyan for database/search operations)
    text = safe_highlight(r'\b(filter by|sort by|group by|order by|aggregate by|join on|left join|right join|' \
               r'inner join|outer join|full join|select from|insert into|update where|delete from|' \
               r'where clause|having clause|distinct|union|intersect|except|' \
               r'query string|search term|filter criteria|sorting criteria|pagination|' \
               r'limit|offset|count|sum|average|min|max|index scan|table scan)\b', 
               r'<span class="odp-brightCyan">\1</span>', text)
    
    # Success messages (brightGreen for positive feedback)
    text = safe_highlight(r'\b(successfully|succeeded|complete|completed|passed|validated|verified|' \
                      r'correct|correctly|fixed|resolved|solved|successful|success|ok|okay|' \
                      r'approved|valid|confirmed|accepted|implemented|accomplished|achieved|' \
                      r'done|finished|ready|available|enabled|activated|working correctly|' \
                      r'working as expected|functioning correctly|all tests passing|' \
                      r'no errors|no warnings|no issues|problem solved|issue resolved)\b', 
                      r'<span class="odp-brightGreen">\1</span>', text)
    
    # Test results (brightGreen for passing tests)
    text = safe_highlight(r'\b(test passed|passing test|tests passing|all tests pass|test suite passed|' \
                  r'build passing|CI passing|green build|integration test passed|unit test passed|' \
                  r'regression test passed|smoke test passed|test coverage|coverage increased|' \
                  r'assertions passed|validation passed|verification passed|quality gate passed|' \
                  r'code review passed|quality check passed|linting passed|formatting passed|' \
                  r'type checking passed|zero defects|zero bugs|no regressions)\b', 
                  r'<span class="odp-brightGreen">\1</span>', text)
    
    # Validated data (brightGreen for valid data)
    text = safe_highlight(r'\b(valid input|valid data|validated data|sanitized input|escaped data|' \
                    r'clean data|well-formed|well formed|proper format|correct format|' \
                    r'properly formatted|valid format|valid syntax|valid schema|conforming to spec|' \
                    r'meeting requirements|matched pattern|passed validation|integrity check passed|' \
                    r'consistency check passed|correctly formatted|correctly structured|' \
                    r'properly escaped|properly sanitized|properly validated)\b', 
                    r'<span class="odp-brightGreen">\1</span>', text)
    
    # Successful operations (brightGreen for completed actions)
    text = safe_highlight(r'\b(operation successful|task completed|action performed|request processed|' \
                    r'transaction committed|data saved|record created|record updated|record deleted|' \
                    r'file uploaded|file downloaded|message sent|email delivered|payment processed|' \
                    r'user registered|user authenticated|login successful|logout successful|' \
                    r'access granted|permission granted|authorization successful|' \
                    r'synchronization complete|migration complete|deployment successful|' \
                    r'installation complete|configuration saved|settings applied)\b', 
                    r'<span class="odp-brightGreen">\1</span>', text)
    
    # Optimization gains (brightGreen for improvements)
    text = safe_highlight(r'\b(optimized|improved|enhanced|faster|quicker|speedup|accelerated|' \
                        r'performance boost|efficiency gain|reduced latency|reduced memory usage|' \
                        r'reduced CPU usage|reduced resource consumption|reduced load time|' \
                        r'improved throughput|improved response time|improved scalability|' \
                        r'better performance|higher throughput|lower latency|smaller footprint|' \
                        r'more efficient|more scalable|more responsive|more reliable)\b', 
                        r'<span class="odp-brightGreen">\1</span>', text)
    
    # Performance improvements (brightGreen for performance metrics)
    text = safe_highlight(r'\b(performance improvement|latency reduction|memory reduction|' \
                              r'CPU reduction|load time decreased|response time decreased|' \
                              r'throughput increased|requests per second increased|' \
                              r'transactions per second increased|render time decreased|' \
                              r'parse time decreased|compile time decreased|startup time decreased|' \
                              r'execution time decreased|processing time decreased|' \
                              r'time complexity reduced|space complexity reduced|' \
                              r'algorithmic improvement|complexity reduction|big O improved)\b', 
                              r'<span class="odp-brightGreen">\1</span>', text)
    
    # Positive metrics (brightGreen for good measurements)
    text = safe_highlight(r'\b(high score|high availability|high throughput|high performance|' \
                      r'high accuracy|high precision|high recall|high F1 score|' \
                      r'low error rate|low defect rate|low latency|low response time|' \
                      r'increased uptime|increased conversion|increased engagement|' \
                      r'increased retention|increased adoption|increased usage|' \
                      r'above threshold|exceeds expectations|exceeds requirements|' \
                      r'meets SLA|within budget|under budget|ahead of schedule)\b', 
                      r'<span class="odp-brightGreen">\1</span>', text)
    
    # Resource efficiencies (brightGreen for resource optimizations)
    text = safe_highlight(r'\b(resource efficient|memory efficient|CPU efficient|' \
                           r'bandwidth efficient|storage efficient|energy efficient|' \
                           r'reduced resource usage|reduced memory footprint|reduced CPU cycles|' \
                           r'reduced bandwidth consumption|reduced storage requirements|' \
                           r'reduced power consumption|optimal resource utilization|' \
                           r'optimal memory usage|optimal CPU usage|balanced load|' \
                           r'efficient caching|efficient indexing|efficient algorithm|' \
                           r'lightweight solution|minimal overhead|minimal footprint)\b', 
                           r'<span class="odp-brightGreen">\1</span>', text)
    
    # Diff additions (brightGreen for added content)
    text = safe_highlight(r'(\+\+\+.*|\+.*|added line|new content|inserted|addition|newly added|' \
                    r'new feature|new functionality|new capability|new method|new function|' \
                    r'new class|new module|new component|new service|new endpoint|' \
                    r'new API|new route|new view|new template|new style|new test|' \
                    r'new dependency|new package|new library|new framework)\b', 
                    r'<span class="odp-brightGreen">\1</span>', text)
    
    # Language keywords (brightPurple for reserved words)
    text = safe_highlight(r'\b(if|else|for|while|do|switch|case|break|continue|return|yield|async|await|' \
                       r'try|catch|finally|throw|throws|new|this|super|extends|implements|interface|' \
                       r'class|enum|struct|namespace|package|import|module|export|require|include|' \
                       r'public|private|protected|static|final|const|let|var|function|def|fn|fun|' \
                       r'method|property|get|set|void|int|float|double|string|boolean|bool|null|nil|' \
                       r'undefined|true|false|typedef|extern|volatile|register|using|lambda|goto)\b', 
                       r'<span class="odp-brightPurple">\1</span>', text)
    
    # Decorators (brightPurple for meta-annotations)
    text = safe_highlight(r'(@\w+(?:\.\w+)*(?:\([^)]*\))?|' \
                r'#\[.*?\]|' \
                r'__\w+__|\[\[.*?\]\]|' \
                r'@decorator|@classmethod|@staticmethod|@property|@overload|@override|' \
                r'@deprecated|@experimental|@api|@internal|@public|@private|@inject|' \
                r'@autowired|@component|@service|@controller|@repository|@entity|' \
                r'@transactional|@async|@synchronized|@volatile|@tailrec|@lazy|' \
                r'@memoized|@cached|@readonly|@virtual|@abstract|@sealed|@required)', 
                r'<span class="odp-brightPurple">\1</span>', text)
    
    # Special directives (brightPurple for compiler instructions)
    text = safe_highlight(r'(#pragma|#define|#undef|#if|#ifdef|#ifndef|#else|#elif|#endif|#error|#warning|' \
                        r'#line|#include|#import|#using|' \
                        r'@directive|@compiler|use strict|use warnings|strict mode|' \
                        r'__asm|__attribute__|__declspec|__forceinline|__restrict|__inline|' \
                        r'"use strict"|\'use strict\'|\'use warnings\'|' \
                        r'#\!.*?/bin/|#\!.*?/usr/bin/|#\!.*?/env\s+\w+)', 
                        r'<span class="odp-brightPurple">\1</span>', text)
    
    # Advanced language features (brightPurple for advanced concepts)
    text = safe_highlight(r'\b(generics|templates|traits|mixins|protocols|macros|reflection|introspection|' \
                       r'metaprogramming|duck typing|dynamic typing|type inference|type erasure|' \
                       r'pattern matching|destructuring|spread operator|rest parameter|variadic templates|' \
                       r'varargs|polymorphism|overloading|overriding|covariance|contravariance|' \
                       r'higher-order functions|closures|currying|partial application|type classes|' \
                       r'monads|functors|applicatives|lazy evaluation|eager evaluation|' \
                       r'tail call optimization|memoization|virtual dispatch|multiple dispatch)\b', 
                       r'<span class="odp-brightPurple">\1</span>', text)
    
    # Metaprogramming concepts (brightPurple for code generation)
    text = safe_highlight(r'\b(code generation|eval|reflection|introspection|type reflection|' \
                     r'runtime type information|RTTI|runtime reflection|mirror API|meta object|' \
                     r'metaclass|metaobject|prototype|monkey patching|aspect-oriented|AOP|' \
                     r'bytecode manipulation|bytecode generation|dynamic code evaluation|' \
                     r'compiler API|AST manipulation|syntax tree|source transformation|' \
                     r'macros|macro expansion|compile-time evaluation|partial evaluation|' \
                     r'staged compilation|template metaprogramming|constexpr|constant expression|' \
                     r'annotations processing|code weaving|proxies|dynamic proxies)\b', 
                     r'<span class="odp-brightPurple">\1</span>', text)
    
    # Reflection capabilities (brightPurple for self-inspection)
    text = safe_highlight(r'\b(reflect|reflection|Type|typeof|instanceof|getClass|isInstance|getMethods|' \
                r'getFields|getConstructors|getInterfaces|getSuperclass|getAnnotations|' \
                r'getMemberType|getDeclaredMethods|getDeclaredFields|getModifiers|' \
                r'isPublic|isPrivate|isProtected|isStatic|isFinal|isAbstract|isInterface|' \
                r'isEnum|isPrimitive|isArray|getComponentType|newInstance|invoke|' \
                r'get|set|class literal|class object|class reference|type descriptor|' \
                r'method reference|field reference|constructor reference)\b', 
                r'<span class="odp-brightPurple">\1</span>', text)
    
    # Compiler directives (brightPurple for build instructions)
    text = safe_highlight(r'\b(inline|noinline|forceinline|noreturn|nodiscard|fallthrough|likely|unlikely|' \
                         r'packed|aligned|deprecated|warning|error|optimize|unroll|vectorize|' \
                         r'restrict|register|extern|volatile|static|thread_local|constexpr|consteval|' \
                         r'dllimport|dllexport|visibility|section|weak|strong|pure|impure|' \
                         r'hot|cold|used|unused|constructor|destructor|malloc|format|' \
                         r'target|tune|arch|feature|pragma once|pragma pack|pragma optimize)\b', 
                         r'<span class="odp-brightPurple">\1</span>', text)
    
    # Preprocessor commands (brightPurple for preprocessing)
    text = safe_highlight(r'(#include\s+["<].*?[">]|#define\s+\w+(\(.*?\))?.*?|' \
                           r'#undef\s+\w+|#if\s+.*?|#ifdef\s+\w+|#ifndef\s+\w+|#else|#elif\s+.*?|#endif|' \
                           r'#error\s+.*?|#warning\s+.*?|#line\s+\d+|#region|#endregion|' \
                           r'#import\s+["<].*?[">]|#pragma\s+.*?|#using\s+.*?)', 
                           r'<span class="odp-brightPurple">\1</span>', text)
    
    # Build configurations (brightPurple for build settings)
    text = safe_highlight(r'\b(DEBUG|RELEASE|TRACE|ASSERT|PROFILE|TEST|PRODUCTION|DEVELOPMENT|' \
                   r'CONFIG|CONFIGURATION|BUILD_TYPE|PLATFORM|TARGET|ARCH|ARCHITECTURE|' \
                   r'x86|x64|ARM|ARM64|INTEL|AMD|APPLE|WINDOWS|LINUX|UNIX|POSIX|ANDROID|IOS|' \
                   r'SIMULATOR|EMULATOR|NATIVE|MANAGED|JIT|AOT|INTERPRETER|COMPILER|' \
                   r'OPTIMIZATION|OPTIMIZE|O0|O1|O2|O3|Os|Oz|Ofast|CMAKE_BUILD_TYPE|' \
                   r'MAKEFILE|CFLAGS|CXXFLAGS|LDFLAGS|LIBS|INCLUDES|DEPENDENCIES)\b', 
                   r'<span class="odp-brightPurple">\1</span>', text)
    
    # Annotations (brightPurple for metadata)
    text = safe_highlight(r'(\[Assembly:.*?\]|\[Attribute:.*?\]|\[Serializable\]|\[Obsolete\]|' \
                 r'\[WebMethod\]|\[WebService\]|\[Route\]|\[HttpGet\]|\[HttpPost\]|' \
                 r'\[Authorize\]|\[AllowAnonymous\]|\[Validate\]|\[Required\]|\[StringLength\]|' \
                 r'\[Remote\]|\[Display\]|\[EditorFor\]|\[Key\]|\[ForeignKey\]|\[Table\]|\[Column\]|' \
                 r'\[JsonProperty\]|\[JsonIgnore\]|\[XmlElement\]|\[XmlAttribute\]|\[XmlIgnore\]|' \
                 r'\[Conditional\]|\[Flags\]|\[ThreadStatic\]|\[ThreadSafe\]|\[MethodImpl\]|' \
                 r'\[StructLayout\]|\[DllImport\]|\[MTAThread\]|\[STAThread\])', 
                 r'<span class="odp-brightPurple">\1</span>', text)
    
    # Transformers and code generators (brightPurple for code transformation)
    text = safe_highlight(r'\b(transformer|code generator|template engine|transpiler|transcompiler|' \
                  r'source-to-source compiler|byte-code generator|byte-code manipulator|' \
                  r'AST transformer|syntax tree transformer|macro processor|preprocessor|' \
                  r'aspect weaver|annotation processor|bytecode enhancer|bytecode instrumentation|' \
                  r'source code generation|auto-generated code|scaffolding|boilerplate generation|' \
                  r'code synthesis|program synthesis|automatic programming|generative programming|' \
                  r'model-driven development|domain-specific language|DSL|template instantiation)\b', 
                  r'<span class="odp-brightPurple">\1</span>', text)
    
    # Error messages (brightRed for errors)
    text = safe_highlight(r'\b(error|exception|failed|failure|invalid|incorrect|wrong|bug|defect|issue|' \
                    r'problem|crash|fault|mistake|malfunction|critical|severe|fatal|broken|corrupt|' \
                    r'unexpected|unhandled|unrecognized|missing|not found|undefined|null reference|' \
                    r'unable to|cannot|could not|compilation error|runtime error|syntax error|' \
                    r'type error|reference error|logic error|assertion failed|stack overflow|' \
                    r'out of memory|segmentation fault|null pointer|access violation)\b', 
                    r'<span class="odp-brightRed">\1</span>', text)
    
    # Exceptions and error states (brightRed for exceptions)
    text = safe_highlight(r'\b(Exception|Error|Throwable|RuntimeException|IOException|FileNotFoundException|' \
                r'NullPointerException|IndexOutOfBoundsException|IllegalArgumentException|' \
                r'UnsupportedOperationException|ClassNotFoundException|SecurityException|' \
                r'try-catch|throw|throws|raise|rescue|catch|finally|except|handle exception|' \
                r'error handling|error recovery|fallback|try-except|try-finally|on error|' \
                r'error state|error condition|error case|error path|error propagation)\b', 
                r'<span class="odp-brightRed">\1</span>', text)
    
    # Failures and bugs (brightRed for failures)
    text = safe_highlight(r'\b(failure|failed test|test failure|edge case|corner case|regression|' \
              r'bug|defect|issue|glitch|flaw|fault|problem|malfunction|regression|' \
              r'known issue|known bug|reported bug|confirmed bug|reproducible bug|' \
              r'intermittent bug|hard-to-reproduce|flaky test|brittle test|' \
              r'failing build|build failure|compile error|runtime error|panic|abort)\b', 
              r'<span class="odp-brightRed">\1</span>', text)
    
    # Vulnerabilities and security threats (brightRed for security issues)
    text = safe_highlight(r'\b(vulnerability|security hole|security flaw|exploit|attack vector|' \
                     r'SQL injection|XSS|cross-site scripting|CSRF|cross-site request forgery|' \
                     r'code injection|shell injection|command injection|path traversal|SSRF|' \
                     r'directory traversal|insecure direct object reference|IDOR|authentication bypass|' \
                     r'authorization bypass|privilege escalation|information disclosure|data leak|' \
                     r'buffer overflow|format string|integer overflow|race condition|TOCTOU|' \
                     r'side-channel attack|timing attack|man-in-the-middle|MITM|CVE|zero-day)\b', 
                     r'<span class="odp-brightRed">\1</span>', text)
    
    # Deprecated features (brightRed for deprecated elements)
    text = safe_highlight(r'\b(deprecated|obsolete|legacy|no longer supported|removed in|will be removed|' \
                r'use instead|replaced by|superseded by|outdated|ancient|unsupported|' \
                r'end-of-life|EOL|sunset|retired|discontinued|phased out|marked for removal|' \
                r'pending deprecation|officially deprecated|soft deprecated|hard deprecated|' \
                r'backward compatibility|backwards compatibility|breaking change)\b', 
                r'<span class="odp-brightRed">\1</span>', text)
    
    # Concurrency issues (brightRed for threading problems)
    text = safe_highlight(r'\b(race condition|deadlock|livelock|starvation|thread safety|' \
                        r'data race|thread interference|atomic operation|non-atomic|' \
                        r'concurrent modification|concurrent access|shared state|mutual exclusion|' \
                        r'lock contention|priority inversion|thread leak|context switch|' \
                        r'inconsistent state|thread dump|blocked thread|hung thread|' \
                        r'thread pool exhaustion|executor shutdown|synchronization issue)\b', 
                        r'<span class="odp-brightRed">\1</span>', text)
    
    # Diff removals (brightRed for removed content)
    text = safe_highlight(r'(-{3}.*|-.*|removed line|deleted content|removed|deletion|removed code|' \
                  r'removed feature|removed functionality|removed capability|removed method|' \
                  r'removed function|removed class|removed module|removed component|' \
                  r'removed service|removed endpoint|removed API|removed route|removed view|' \
                  r'removed template|removed style|removed test|removed dependency)\b', 
                  r'<span class="odp-brightRed">\1</span>', text)
    
    # Core concepts (brightWhite for important text)
    core_concepts = r'\b(algorithm|paradigm|architecture|principle|pattern|concept|methodology|' \
                   r'approach|technique|strategy|best practice|convention|standard|specification|' \
                   r'protocol|rule|guideline|recommendation|framework|system|structure|' \
                   r'foundation|fundamental|essential|critical|key aspect|crucial|vital|' \
                   r'central idea|core functionality|primary concern|main feature|' \
                   r'basic operation|standard practice|common pattern|universal principle)\b'
    text = safe_highlight(core_concepts, r'<span class="odp-brightWhite">\1</span>', text)
    
    # Key principles (brightWhite for principles)
    key_principles = r'\b(DRY|Don\'t Repeat Yourself|SOLID|single responsibility|open-closed|' \
                    r'Liskov substitution|interface segregation|dependency inversion|' \
                    r'separation of concerns|law of Demeter|YAGNI|KISS|principle of least surprise|' \
                    r'principle of least privilege|encapsulation|abstraction|inheritance|' \
                    r'polymorphism|composition over inheritance|convention over configuration|' \
                    r'fail fast|defensive programming|offensive programming|clean code|' \
                    r'code quality|maintainability|readability|testability|scalability|' \
                    r'modularity|cohesion|coupling|reusability|extensibility|flexibility)\b'
    text = safe_highlight(key_principles, r'<span class="odp-brightWhite">\1</span>', text)
    
    # Algorithm names (brightWhite for algorithms)
    algorithm_names = r'\b(binary search|linear search|depth-first search|DFS|breadth-first search|BFS|' \
                     r'backtracking|dynamic programming|greedy algorithm|divide and conquer|' \
                     r'recursion|memoization|sorting algorithm|quicksort|mergesort|heapsort|' \
                     r'insertion sort|selection sort|bubble sort|radix sort|counting sort|' \
                     r'topological sort|graph algorithm|shortest path|Dijkstra\'s algorithm|' \
                     r'Bellman-Ford|A\* search|minimum spanning tree|Kruskal\'s algorithm|' \
                     r'Prim\'s algorithm|union-find|disjoint set|hashing|hash table|' \
                     r'bloom filter|trie|suffix tree|B-tree|red-black tree|AVL tree|' \
                     r'binary heap|priority queue|sliding window|two pointers|fast and slow pointers)\b'
    text = safe_highlight(algorithm_names, r'<span class="odp-brightWhite">\1</span>', text)
    
    # Paradigm names (brightWhite for programming paradigms)
    paradigm_names = r'\b(object-oriented programming|OOP|functional programming|procedural programming|' \
                    r'imperative programming|declarative programming|event-driven programming|' \
                    r'aspect-oriented programming|data-oriented design|component-based|' \
                    r'service-oriented architecture|SOA|microservices|serverless|' \
                    r'reactive programming|concurrent programming|parallel programming|' \
                    r'asynchronous programming|synchronous programming|stream processing|' \
                    r'batch processing|message-driven|command query responsibility segregation|CQRS|' \
                    r'event sourcing|domain-driven design|DDD|test-driven development|TDD|' \
                    r'behavior-driven development|BDD|model-view-controller|MVC|MVVM|MVP)\b'
    text = safe_highlight(paradigm_names, r'<span class="odp-brightWhite">\1</span>', text)
    
    # Function parameters (brightYellow for parameters)
    function_parameters = r'\b(param|parameter|arg|argument|option|flag|switch|config|' \
                         r'configuration|setting|property|attribute|field|variable|prop|' \
                         r'input|output|value|default value|default|required parameter|' \
                         r'optional parameter|named parameter|positional parameter|' \
                         r'rest parameter|variadic parameter|spread parameter|' \
                         r'destructured parameter|typed parameter|generic parameter|' \
                         r'callback parameter|function parameter|object parameter|' \
                         r'array parameter|boolean parameter|string parameter|number parameter)\b'
    text = safe_highlight(function_parameters, r'<span class="odp-brightYellow">\1</span>', text)
    
    # Method arguments (brightYellow for arguments)
    method_arguments = r'(\(\s*[\w\s,]*\s*\)|function\s*\(\s*[\w\s,]*\s*\)|def\s+\w+\s*\(\s*[\w\s,]*\s*\)|' \
                      r'method\s*\(\s*[\w\s,]*\s*\)|lambda\s+[\w\s,]*\s*:|' \
                      r'\(\s*\w+\s*:\s*\w+\s*\)|\(\s*\w+\s*=\s*[^,)]+\s*\)|' \
                      r'\b\w+\s*=\s*[^,)]+(?=[,)])|' \
                      r'@\w+\(\s*[\w\s=,\'\"]*\s*\))'
    text = safe_highlight(method_arguments, r'<span class="odp-brightYellow">\1</span>', text)
    
    # Configuration options (brightYellow for config)
    config_options = r'\b(config|configuration|settings|options|preferences|flags|switches|' \
                    r'parameters|arguments|properties|attributes|environment variable|env var|' \
                    r'config file|configuration file|settings file|properties file|' \
                    r'\.env|\.config|\.ini|\.json|\.yaml|\.yml|\.xml|\.properties|' \
                    r'command-line option|CLI option|CLI argument|system property|' \
                    r'app setting|application setting|user preference|default setting|' \
                    r'override|fallback|config key|config value|config pair|' \
                    r'feature flag|feature toggle|A/B test|experiment)\b'
    text = safe_highlight(config_options, r'<span class="odp-brightYellow">\1</span>', text)
    
    # Environment variables (brightYellow for environment)
    env_variables = r'\b(ENV|ENVIRONMENT|NODE_ENV|PRODUCTION|DEVELOPMENT|STAGING|TEST|DEBUG|' \
                   r'API_KEY|SECRET_KEY|ACCESS_TOKEN|CLIENT_ID|CLIENT_SECRET|APP_ID|APP_SECRET|' \
                   r'DATABASE_URL|DB_HOST|DB_USER|DB_PASSWORD|DB_NAME|DB_PORT|' \
                   r'PORT|HOST|HOSTNAME|IP|URL|BASE_URL|API_URL|ENDPOINT|' \
                   r'PATH|HOME|USER|USERNAME|PWD|TEMP|TMP|SHELL|' \
                   r'LOG_LEVEL|VERBOSE|QUIET|NO_COLOR|FORCE_COLOR|' \
                   r'AWS_|AZURE_|GOOGLE_|GITHUB_|NPM_|DOCKER_|KUBERNETES_|K8S_)\b'
    text = safe_highlight(env_variables, r'<span class="odp-brightYellow">\1</span>', text)

    # Execution pointers (cursorColor for execution points)
    execution_pointers = r'\b(cursor|pointer|insertion point|caret|selection|highlight|' \
                        r'breakpoint|watchpoint|tracepoint|conditional breakpoint|' \
                        r'step over|step into|step out|continue execution|pause execution|' \
                        r'program counter|instruction pointer|execution pointer|' \
                        r'current line|active line|execution line|current statement|' \
                        r'next instruction|previous instruction|call stack|stack frame|' \
                        r'stack trace|current frame|selected frame|memory address|' \
                        r'memory inspection|memory dump|memory view|register view|' \
                        r'variable inspection|watch expression|evaluate expression)\b'
    text = safe_highlight(execution_pointers, r'<span class="odp-cursorColor">\1</span>', text)
    
    # Data transformations (cyan for transformations)
    data_transformations = r'\b(transform|convert|parse|format|serialize|deserialize|encode|decode|' \
                          r'encrypt|decrypt|hash|sign|validate|normalize|canonicalize|escape|unescape|' \
                          r'sanitize|clean|filter|map|reduce|fold|flatMap|flatten|' \
                          r'collect|stream|sort|order|group|aggregate|accumulate|' \
                          r'extract|project|select|reject|exclude|omit|pick|pluck|' \
                          r'merge|combine|compose|pipe|chain|link|connect|join|split|' \
                          r'slice|splice|chunk|batch|window|buffer|pad|trim|truncate)\b'
    text = safe_highlight(data_transformations, r'<span class="odp-cyan">\1</span>', text)
    
    # ETL processes (cyan for ETL)
    etl_processes = r'\b(extract|transform|load|ETL|data pipeline|data flow|data integration|' \
                   r'data migration|data conversion|data transfer|data movement|' \
                   r'source system|target system|upstream|downstream|' \
                   r'batch process|batch job|stream processing|real-time processing|' \
                   r'data extraction|data transformation|data loading|' \
                   r'data cleansing|data enrichment|data validation|' \
                   r'data aggregation|data summarization|data normalization|' \
                   r'data warehousing|data lake|data mart|staging area)\b'
    text = safe_highlight(etl_processes, r'<span class="odp-cyan">\1</span>', text)
    
    # State mutations (cyan for state changes)
    state_mutations = r'\b(mutate|mutation|change state|state change|update state|modify state|' \
                     r'set state|reset state|clear state|initialize state|' \
                     r'state transition|state machine|finite state machine|FSM|' \
                     r'reducer|action|dispatch|store|immutable update|deep copy|' \
                     r'shallow copy|clone|assign|merge|spread|destructure|' \
                     r'side effect|pure function|impure function|idempotent|' \
                     r'transaction|commit|rollback|savepoint|atomic operation|' \
                     r'optimistic update|pessimistic update|concurrent modification)\b'
    text = safe_highlight(state_mutations, r'<span class="odp-cyan">\1</span>', text)
    
    # System transitions (cyan for transitions)
    system_transitions = r'\b(boot|startup|shutdown|restart|reboot|reload|refresh|' \
                        r'initialize|init|start|stop|pause|resume|suspend|hibernate|' \
                        r'activate|deactivate|enable|disable|toggle|switch|' \
                        r'open|close|connect|disconnect|attach|detach|mount|unmount|' \
                        r'register|unregister|subscribe|unsubscribe|listen|unlisten|' \
                        r'bind|unbind|link|unlink|compile|build|deploy|publish|' \
                        r'migrate|upgrade|downgrade|rollback|scale up|scale down)\b'
    text = safe_highlight(system_transitions, r'<span class="odp-cyan">\1</span>', text)
    
    # General explanations (foreground for standard text)
    general_explanations = r'\b(explanation|description|summary|overview|introduction|background|' \
                          r'context|details|information|clarification|elaboration|note|remark|' \
                          r'example|instance|scenario|case study|illustration|demonstration|' \
                          r'definition|meaning|interpretation|understanding|analysis|' \
                          r'breakdown|walkthrough|step-by-step|procedure|process|mechanism|' \
                          r'how it works|underlying concept|basic idea|intuition|analogy|' \
                          r'comparison|contrast|difference|similarity|relationship|interaction)\b'
    text = safe_highlight(general_explanations, r'<span class="odp-foreground">\1</span>', text)
    
    # Algorithm descriptions (foreground for algorithm text)
    algorithm_descriptions = r'\b(algorithm description|pseudocode|high-level description|' \
                            r'implementation details|logic flow|control flow|data flow|' \
                            r'runtime analysis|complexity analysis|space-time tradeoff|' \
                            r'optimization technique|performance improvement|edge case handling|' \
                            r'corner case handling|error handling|termination condition|' \
                            r'base case|recursive case|invariant|pre-condition|post-condition|' \
                            r'input constraints|output format|expected result|actual result|' \
                            r'correctness proof|mathematical proof|inductive proof)\b'
    text = safe_highlight(algorithm_descriptions, r'<span class="odp-foreground">\1</span>', text)
    
    # Web technologies (green for web terms)
    web_technologies = r'\b(HTML|CSS|JavaScript|DOM|Browser API|Web API|Web Component|' \
                      r'React|Angular|Vue|Svelte|jQuery|Bootstrap|Tailwind|' \
                      r'HTTP|HTTPS|REST|GraphQL|WebSocket|SSE|AJAX|Fetch API|' \
                      r'cookie|localStorage|sessionStorage|IndexedDB|Web Storage|' \
                      r'responsive design|mobile-first|progressive enhancement|' \
                      r'single-page application|SPA|server-side rendering|SSR|' \
                      r'client-side rendering|CSR|static site generation|SSG|' \
                      r'web standard|W3C|WHATWG|progressive web app|PWA)\b'
    text = safe_highlight(web_technologies, r'<span class="odp-green">\1</span>', text)
    
    # URLs and file paths (green for paths)
    urls_and_paths = r'(https?://[\w\-\.]+\.\w+(?:[\w\-\._~:/\?#\[\]@!\$&\'\(\)\*\+,;=]|%[0-9A-F]{2})*|' \
                    r'(?:file|ftp|sftp|ssh|git|svn|mailto)://[\w\-\.]+(?:[\w\-\._~:/\?#\[\]@!\$&\'\(\)\*\+,;=]|%[0-9A-F]{2})*|' \
                    r'/[\w\-\.]+(?:/[\w\-\.]+)*(?:\.\w+)?|' \
                    r'(?:\.\.?/)+[\w\-\.]+(?:/[\w\-\.]+)*(?:\.\w+)?|' \
                    r'(?:[A-Za-z]:)?[\\/][\w\-\.]+(?:[\\/][\w\-\.]+)*(?:\.\w+)?|' \
                    r'(?:~|\.\.?)/[\w\-\.]+(?:/[\w\-\.]+)*(?:\.\w+)?)'
    text = safe_highlight(urls_and_paths, r'<span class="odp-green">\1</span>', text)
    
    # UI/UX terminology (green for UI terms)
    ui_terms = r'\b(user interface|UI|user experience|UX|accessibility|a11y|i18n|' \
              r'internationalization|localization|l10n|responsive|adaptive|fluid|' \
              r'layout|component|widget|control|element|container|grid|flexbox|' \
              r'navigation|menu|sidebar|toolbar|header|footer|modal|dialog|popup|' \
              r'tooltip|dropdown|accordion|tab|carousel|slider|pagination|' \
              r'form|input|field|button|checkbox|radio|select|option|label|' \
              r'validation|feedback|notification|alert|toast|banner|card|panel)\b'
    text = safe_highlight(ui_terms, r'<span class="odp-green">\1</span>', text)
    
    # DOM elements (green for DOM)
    dom_elements = r'\b(HTML element|DOM node|document fragment|shadow DOM|' \
                  r'root element|parent element|child element|sibling element|' \
                  r'ancestor element|descendant element|nested element|' \
                  r'div|span|p|h1|h2|h3|h4|h5|h6|ul|ol|li|dl|dt|dd|' \
                  r'table|tr|td|th|thead|tbody|tfoot|' \
                  r'form|input|button|select|option|textarea|label|fieldset|' \
                  r'a|img|audio|video|canvas|svg|path|rect|circle|' \
                  r'header|footer|nav|main|article|section|aside)\b'
    text = safe_highlight(dom_elements, r'<span class="odp-green">\1</span>', text)
    
    # Variable names (red for variables)
    variable_names = r'\b(var|let|const|variable|field|property|attribute|member|' \
                    r'local variable|instance variable|class variable|static variable|' \
                    r'global variable|parameter|argument|temp|temporary|tmp|' \
                    r'counter|index|iterator|enumerator|accumulator|result|' \
                    r'value|values|key|keys|entry|entries|item|items|element|' \
                    r'object|array|list|map|set|collection|sequence|enumerable|' \
                    r'instance|reference|pointer|handle|identifier|id|name|label)\b'
    text = safe_highlight(variable_names, r'<span class="odp-red">\1</span>', text)
    
    # Hardware components (red for hardware)
    hardware_components = r'\b(CPU|processor|core|thread|memory|RAM|cache|L1|L2|L3|' \
                         r'hard drive|HDD|solid state drive|SSD|disk|storage|' \
                         r'motherboard|mainboard|chipset|BIOS|UEFI|firmware|' \
                         r'graphics card|GPU|video card|sound card|network card|' \
                         r'adapter|controller|peripheral|device|driver|' \
                         r'bus|port|interface|connector|cable|socket|slot|' \
                         r'register|address|pointer|memory address|stack|heap|' \
                         r'buffer|page|segment|partition|sector|cluster|block)\b'
    text = safe_highlight(hardware_components, r'<span class="odp-red">\1</span>', text)
    
    # Error conditions (red for errors)
    error_conditions = r'\b(error condition|failure mode|fault|malfunction|crash|hang|freeze|' \
                      r'timeout|deadlock|race condition|memory leak|buffer overflow|' \
                      r'null pointer|segmentation fault|access violation|assertion failure|' \
                      r'stack overflow|out of memory|out of bounds|division by zero|' \
                      r'undefined behavior|unexpected result|incorrect behavior|' \
                      r'corrupted data|data corruption|invalid state|inconsistent state|' \
                      r'edge case|corner case|boundary condition|exceptional case)\b'
    text = safe_highlight(error_conditions, r'<span class="odp-red">\1</span>', text)
    
    # Syntactic elements (white for syntax)
    syntactic_elements = r'(\{|\}|\[|\]|\(|\)|<|>|;|:|,|\.|\'|\"|\`|' \
                        r'\=\>|\-\>|::|\.\.|\.\.\.|' \
                        r'#!|#!/|#include|#define|#ifdef|#ifndef|#endif|' \
                        r'@import|@media|@keyframes|@font-face|@supports|' \
                        r'begin|end|public|private|protected|internal|' \
                        r'package|namespace|module|import|export|from|as|' \
                        r'function|method|constructor|class|interface|enum|' \
                        r'if|else|switch|case|default|for|while|do|break|continue|' \
                        r'return|yield|async|await|try|catch|finally|throw|' \
                        r'let|const|var|static|final|abstract|extends|implements)'
    text = safe_highlight(syntactic_elements, r'<span class="odp-white">\1</span>', text)
    
    # Structural markers (white for structure)
    structural_markers = r'\b(structure|layout|organization|arrangement|composition|' \
                        r'hierarchy|tree|graph|network|chain|sequence|series|' \
                        r'container|wrapper|decorator|adapter|facade|proxy|' \
                        r'component|module|package|library|framework|system|' \
                        r'head|tail|front|back|top|bottom|start|end|begin|finish|' \
                        r'first|last|previous|next|parent|child|ancestor|descendant|' \
                        r'root|leaf|node|vertex|edge|branch|path|route|link)\b'
    text = safe_highlight(structural_markers, r'<span class="odp-white">\1</span>', text)
    
    # Numeric literals (yellow for numbers)
    numeric_literals = r'(\b\d+\b|\b0x[0-9a-fA-F]+\b|\b0b[01]+\b|\b0o[0-7]+\b|' \
                      r'\b\d+\.\d+\b|\b\d+e[+-]?\d+\b|\b\d+\.\d+e[+-]?\d+\b|' \
                      r'\bnull\b|\bnil\b|\bNone\b|\bundefined\b|\bNaN\b|\bInfinity\b|' \
                      r'\btrue\b|\bfalse\b|\bTRUE\b|\bFALSE\b|\bTrue\b|\bFalse\b|' \
                      r'\byes\b|\bno\b|\bon\b|\boff\b)'
    text = safe_highlight(numeric_literals, r'<span class="odp-yellow">\1</span>', text)
    
    # Constants and enum values (yellow for constants)
    constants = r'\b(const|constant|final|readonly|immutable|frozen|sealed|' \
               r'MAX_|MIN_|DEFAULT_|STANDARD_|BASIC_|PRIMARY_|SECONDARY_|' \
               r'SUCCESS_|ERROR_|WARNING_|INFO_|DEBUG_|TRACE_|LOG_|' \
               r'RED|GREEN|BLUE|YELLOW|CYAN|MAGENTA|BLACK|WHITE|GRAY|' \
               r'NORTH|SOUTH|EAST|WEST|UP|DOWN|LEFT|RIGHT|CENTER|' \
               r'MONDAY|TUESDAY|WEDNESDAY|THURSDAY|FRIDAY|SATURDAY|SUNDAY|' \
               r'JANUARY|FEBRUARY|MARCH|APRIL|MAY|JUNE|JULY|AUGUST|SEPTEMBER|OCTOBER|NOVEMBER|DECEMBER|' \
               r'HTTP_OK|HTTP_CREATED|HTTP_ACCEPTED|HTTP_BAD_REQUEST|HTTP_UNAUTHORIZED|HTTP_FORBIDDEN|HTTP_NOT_FOUND)\b'
    text = safe_highlight(constants, r'<span class="odp-yellow">\1</span>', text)
    
    # Status codes and version numbers (yellow for codes)
    status_codes = r'\b(\d{3}|\d{1,3}\.\d{1,3}\.\d{1,3}|\d{1,3}\.\d{1,3}|\d+\.\d+|' \
                  r'v\d+\.\d+\.\d+|v\d+\.\d+|version \d+\.\d+\.\d+|version \d+\.\d+|' \
                  r'HTTP 200|HTTP 201|HTTP 204|HTTP 400|HTTP 401|HTTP 403|HTTP 404|HTTP 500|' \
                  r'2XX|3XX|4XX|5XX|' \
                  r'HTTP_\d{3}|STATUS_\d{3}|EXIT_\d+|ERR_\d+|ERROR_\d+)\b'
    text = safe_highlight(status_codes, r'<span class="odp-yellow">\1</span>', text)
    
    # Memory addresses and indices (yellow for addresses)
    memory_addresses = r'(0x[0-9a-fA-F]+|\[\d+\]|\[\d+:\d+\]|\[\w+\]|' \
                      r'\w+\[\d+\]|\w+\[\w+\]|\w+\[:\]|\w+\[:\d+\]|\w+\[\d+:\]|\w+\[\d+:\d+\]|' \
                      r'&\w+|\*\w+|->\w+|\.\w+|->\w+\.\w+|' \
                      r'pointer to \w+|address of \w+|reference to \w+|' \
                      r'array index|array indices|array offset|memory offset|memory address|pointer address)'
    text = safe_highlight(memory_addresses, r'<span class="odp-yellow">\1</span>', text)
    
    # HTTP status code families (purple for keywords/programming concepts)
    text = safe_highlight(r'\b(\d)xx\b', r'<span class="odp-purple">\1xx</span>', text)
    
    # Protocol full names (purple for programming languages/frameworks/libraries)
    protocol_full_names = r'(Hypertext Transfer Protocol|File Transfer Protocol|Simple Mail Transfer Protocol|' \
                         r'Internet Control Message Protocol|Transmission Control Protocol|User Datagram Protocol|' \
                         r'Domain Name System|Secure Shell Protocol|Transport Layer Security|Secure Sockets Layer|' \
                         r'Internet Protocol|Address Resolution Protocol|integrated media production suites)'
    
    text = safe_highlight(f'{protocol_full_names}(\\s*\\(([^)]+)\\))', 
                  r'<span class="odp-purple">\1</span><span class="odp-brightBlack">\2</span>', text)
    
    # Protocol name keywords (purple for language keywords and frameworks)
    protocol_keywords = r'\b(Hypertext|Transfer|Protocol|File|Simple|Mail|Internet|Control|Message|Transmission|' \
                       r'User|Datagram|Domain|Name|System|Secure|Shell|Transport|Layer|Security|Sockets|Address|' \
                       r'Resolution|WordPress|operating system|numerical address)\b'
    text = safe_highlight(protocol_keywords, r'<span class="odp-purple">\1</span>', text)
    
    # Programming languages, frameworks, and platforms (brightYellow for parameters/configuration options)
    tech_pattern = r'\b(JavaScript|Python|Java|C\+\+|C#|Ruby|PHP|HTML|CSS|React|Angular|Vue|Node\.js|TypeScript|' \
                r'SQL|NoSQL|MongoDB|Redis|Docker|Kubernetes|AWS|Azure|JSON|Google Chrome|Mozilla Firefox|' \
                r'Microsoft Edge|Safari|Developer Tools|DevTools|Web Inspector|JSON web token|blockchain|ledger|' \
                r'Microsoft Excel|text\/html|application\/json|HTML data|XML data|JSON data|Binary data|WordPress|' \
                r'Content Management System|CMS|analytics plugin|content management system|' \
                r'open-source content management systems|security certificate|email marketing software|root access|' \
                r'colocation hosting|managed WordPress hosting|enterprise-level hosting|static site hosting|' \
                r'email hosting|managed hosting|fully managed hosting|site builder platforms|static file storage|' \
                r'Certificate Authorities|DNS record|IP address|device identification|street address|' \
                r'DNS records|resource record|DNS server|definitive records|definitive DNS records|final IP mappings|' \
                r'IP mapping|definitive IP mapping|suffix-level resolution|software applications|security needs|' \
                r'privacy features|JavaScript code|security certificates|safe browsing sessions)\b'
    text = safe_highlight(tech_pattern, r'<span class="odp-brightYellow">\1</span>', text)
    
    # Architecture concepts (yellow for numeric literals/attributes)
    architecture_concepts = r'\b(application layer|transport layer|network layer|link layer|physical layer|' \
                r'network model|protocol stack|network protocol stack|lower-level protocols|TCP\/IP|OSI model|' \
                r'request line|resource address|hardware-level addressing|URL|domain name resolution|status codes|' \
                r'encryption method|content format|key-value pairs|caching policies|security process|' \
                r'encryption handshake|offline caching|success|failure|client-side error|server-side error|' \
                r'informational response|redirect|download speed|network conditions|server capacity|security measures|' \
                r'payment method|content access|styling information|presentation layers|metadata|' \
                r'server-to-client communication|client-side|server-side|stateless|stateful|session layer|layer 7|' \
                r'layer 5|layer 3|layer 1|encryption across all layers|user login|connection|multiple sessions|' \
                r'initiation process|multiple requests|concurrent connections|uptime|root access|' \
                r'administrative privileges|server resources|server storage|loading times|page loading speed|' \
                r'technical features|management level|essential infrastructure|infrastructure|selected hosting type|' \
                r'plan specifications|CPU|RAM|hard drive space|bandwidth|resource allocation|control level|' \
                r'performance|reliability|uptime|technical skills|server administration|command-line operations|' \
                r'setup complexity|pricing|price point|costs|affordable|numerical labels|web navigation|' \
                r'domain-to-IP translation|gateway address|local resolver settings|permanent universal port number|' \
                r'caching mechanism|192\.168\.1\.1|DNS query sequence|query sequence|initial reference|' \
                r'IP information|final IP|definitive record|definitive IP address|ecosystem features|' \
                r'operational details|feature sets|graphical representation|visual layout|page layout|screen sizes|' \
                r'processing capabilities|internet connectivity speeds|service provider configurations|' \
                r'data security|secure connections|built-in protections|system safeguards|network protections)\b'
    text = safe_highlight(architecture_concepts, r'<span class="odp-yellow">\1</span>', text)
    
    # Architecture term keywords (yellow for numeric attributes/constants)
    architecture_keywords = r'\b(application|transport|network|layer|layers|link|physical|model|stack|protocol|' \
                          r'protocols|lower-level|TCP\/IP|OSI|request|line|resource|address|URL|URI|' \
                          r'hardware-level|addressing|status|encryption|keys|values|pairs|format|content|caching|' \
                          r'policy|policies|offline|handshake|security|process|zone|transfers|resolution|driver|' \
                          r'updates|digit|digits|standardized|communication|specificity|complexity|redirect|' \
                          r'download|speed|conditions|capacity|measures|payment|access|styling|presentation|' \
                          r'metadata|client|server|browser|web|technical|infrastructure|specifications|essential|' \
                          r'selected|reliability|performance|uptime|price|cost|affordable|pricing|administration|' \
                          r'complexity|skills|port|gateway|mechanism|universal|permanent|resolver|settings|local)\b'
    text = re.sub(architecture_keywords, r'<span class="odp-yellow">\1</span>', text)
    
    # Protocol positioning with layers
    text = re.sub(r'\b(HTTP|HTTPS|FTP|SMTP|ICMP|TCP|IP|UDP|DNS|SSH|TLS|SSL|ARP|IMAP)' \
                 r'(\s+at\s+the\s+)(application layer|transport layer|network layer|link layer)\b', 
                 r'<span class="odp-blue">\1</span>\2<span class="odp-yellow">\3</span>', text)
    
    # Relationships between protocols and stack (cyan for operators/actions)
    text = re.sub(r'\b(relies on|runs on top of|resides in|below|above|on top of|included in|part of)\b', 
                 r'<span class="odp-cyan">\1</span>', text)
    
    # Relationship keywords (cyan for operators/logical operations)
    relationship_keywords = r'\b(relies|runs|resides|below|above|top|included|part)\b'
    text = re.sub(relationship_keywords, r'<span class="odp-cyan">\1</span>', text)
    
    # Technical actions and data transformations (cyan for operators/transformations)
    actions_pattern = r'\b(enables|transferring|sending|receiving|handles|serving|processing|communicating|' \
                     r'exchanging|forming|providing|operates|functions|managing|ensuring|transmit|forwards|' \
                     r'filter|rewrite|maps|routes|transports|responds|requests|execute|rely|resides|perform|' \
                     r'begin|processes|discarding|redirecting|filtering|blocking|assigned|leased|facilitates|' \
                     r'retrieval|loading|dedicated|restricted|tailored|used for|designed|making|responsible|' \
                     r'might|display|verify|generate|remove|carries|transmitted|conflates|precompiled|' \
                     r'retrieving|pinpoints|embedded|tracking|convey|resolve|rendering|retrieval|submission|' \
                     r'updating|expect|compress|encrypts|indicate|labeled|termed|referred|controls|queried|' \
                     r'works|encrypts|replaces|marks|unrelated|deletes|replaces|blocks|modifies|executing|' \
                     r'triggering|shutting|encountered|frequently|occasionally|commonly|controlling|stripped|' \
                     r'attached|interpret|render|reference|communicate|communicate|represent|receive|answer|' \
                     r'return|reply|confusion|confuses|describes|included|referencing|returned|resolution|' \
                     r'disclosure|conveying|communicate|disclosed|capture|show|prevent|manage|inspect|simplify|' \
                     r'download|parse|overwhelm|flooding|crash|weaponized|denying|mounted|deliberately|reused|' \
                     r'relies on|reusing|consuming|times out|mounted|register|purchasing|allocate|allocating|' \
                     r'set aside|serving|storing|maintain|rent|ensures|supply|supplied|connect|connects|cover|' \
                     r'covers|remain patient|abandoned|wait indefinitely|grant|remain inaccessible|reach|load|' \
                     r'cater|enhance|abandon|catering|misses|missing|uploads|uploading|uploaded|retrieve|' \
                     r'retrieves|retrieving|register|registers|registering|interprets|interpreting|displays|' \
                     r'displaying|resolves|translate|translates|translating|accommodates|configure|configuring|' \
                     r'grant|granting|enable|enabling|return|returning|translating domain names|' \
                     r'memorizing IP addresses|directing Internet traffic|compressing website data|' \
                     r'encrypting online communication|verifying website certificates|locating a specific device|' \
                     r'route data|organize domain names|manually confirm routing|pinpoints|user-friendly browsing|' \
                     r'clears the cache|data encryption|user input|accepts queries|forwards the query|locates|' \
                     r'performs iterative lookups|resolves a domain name|translates a hostname|DNS resolution|' \
                     r'initiates lookups|coordinates the lookup process|DNS lookup|fulfills the query|' \
                     r'narrows down the search|satisfies a client\'s DNS query|sends further requests|' \
                     r'iterative requests|reference|points to|redirects|directs the request|directs queries|' \
                     r'resolves|completes the resolution process|returns the IP address|constructs|' \
                     r'fetching|interprets and runs|encrypt data transmissions|protect users|adding or removing|' \
                     r'fetches data|adds interactivity|collaborate|collaborating|dividing tasks|transform|' \
                     r'adapt|regulate|control|testing|supporting|detect|adjust|present|automate)\b'
    text = re.sub(actions_pattern, r'<span class="odp-cyan">\1</span>', text)
    
    # Singular/plural forms for technical actions (cyan for data transformations)
    actions_singular_plural = r'\b(transfer|transfers|transmitted|transmits|request|response|responses|load|' \
                              r'loads|handle|service|map|route|process|transport|respond|request|execute|' \
                              r'execution|rely|reside|forward|filter|filters|rewrite|rewrites|discard|discards|' \
                              r'redirect|redirects|filter|block|blocks|assign|assigns|lease|leases|facilitate|' \
                              r'retrieve|retrieved|load|loaded|design|designed|make|made|responsible|use|used|' \
                              r'enable|enabled|manage|managed|ensure|ensured|form|formed|provide|provided|' \
                              r'operate|operated|function|functioned|display|displays|verify|verifies|generate|' \
                              r'generates|remove|removes|carry|carries|conflate|conflates|compile|compiles|' \
                              r'retrieve|retrieves|pinpoint|pinpoints|embed|embeds|track|tracks|convey|conveys|' \
                              r'resolve|resolves|render|renders|submit|submits|expect|expects|retrieve|retrieves|' \
                              r'update|updates|compress|compresses|encrypt|encrypts|query|queries|delete|deletes|' \
                              r'modify|modifies|replace|replaces|block|blocks|label|labels|term|terms|refer|' \
                              r'refers|control|controls|mark|marks|execute|executes|trigger|triggers|shutdown|' \
                              r'shutdowns|strip|strips|attach|attaches|interpret|interprets|communicate|' \
                              r'communicates|represent|represents|receive|receives|answer|answers|return|returns|' \
                              r'reply|replies|confuse|confuses|describe|describes|include|includes|reference|' \
                              r'references|disclose|discloses|convey|conveys|travel|travels|parse|parses|' \
                              r'capture|captures|show|shows|prevent|prevents|manage|manages|inspect|inspects|' \
                              r'simplify|simplifies|download|downloads|registers|registered|purchases|purchased|' \
                              r'allocates|allocated|caters|catered|miss|connect|connected|requires|required|' \
                              r'reaches|reached|enhances|enhanced|abandon|abandoned|supply|supplies|supplied|' \
                              r'grant|granted|ensure|ensures|connect|connects|cover|covers|remain|remained|' \
                              r'upload|uploads|uploaded|uploading|configure|configured|configuring|translate|' \
                              r'translates|translated|translating|organize|organizes|organized|organizing|' \
                              r'confirm|confirms|confirmed|encryption|input|inputs|construct|constructs|' \
                              r'fetch|fetches|protect|protects|collaborate|collaborates)\b'
    text = re.sub(actions_singular_plural, r'<span class="odp-cyan">\1</span>', text)
    
    # Browser-specific actions (cyan for operations/transformations)
    browser_actions = r'\b(converts HTML into a webpage|removes HTML content|stores HTML as a text file|' \
                     r'encrypts HTML for security|renders|rendering|translates the code|determines how elements|' \
                     r'arranges them accordingly|loads or interact|reads the code|executes it|handles interactions)\b'
    text = re.sub(browser_actions, r'<span class="odp-cyan">\1</span>', text)
    
    # Web/internet terms (green for strings/URLs/web technologies)
    web_terms = r'\b(World Wide Web|web|internet|online|browser|server|client|request|response|data|resources|' \
               r'systems|foundation|basis|content|communications|information|transfer|packet|frame|message|' \
               r'record|address|routing|addressing|traffic|transaction|network|devices|media|interactive|text|' \
               r'login|command|error|operational|flow|sequence|hypertext|hypertext links|hypertext-linked|' \
               r'website content|webpages|data exchange|diagnostic functions|error reporting|email transmission|' \
               r'data payloads|domain names|inbound packets|congestion|features|core mechanism|' \
               r'general information|corresponding|standard|interaction|communications possible|' \
               r'Internet communication|client application|encoded data|data submission|database query|' \
               r'protocol version|directory structure|encryption key|hardware versions|geographical data|' \
               r'authentication|user agent|content type|anti-malware|form submissions|JSON payloads|' \
               r'authorization key|security configuration|multi-faceted|structured|personal data|metadata|' \
               r'website|webpage|web traffic|cached version|unencrypted data transfer|action indicator|' \
               r'HTTP verb|key-value pairs|textual information|text-based details|structured pairs|metadata|' \
               r'instructions|client browser details|requested data|parameters|JSON syntax|URL parameters|' \
               r'cookie data|session identifiers|browser metadata|form data|multipart form data|' \
               r'URL-encoded key-value pairs|HTTP request body|body of an HTTP request|' \
               r'information being transferred|data payload|submitted information|form inputs|internet server|' \
               r'web client|web clients|internet servers|content details|status details|encryption status|' \
               r'protocol in use|unencrypted resources|encrypted resources|caching|offline caching|direct reply|' \
               r'content returned|specifics of the preceding request|valuable information|offline data|' \
               r'HTTP status code|status codes|language information|language|reading mode|requested information|' \
               r'default error message|stateless protocol|stateful sessions|persistent session data|' \
               r'self-contained|caches resources|indefinite caching|tracking user data|original specification|' \
               r'non-persistent|persistent connections|data transfer|reliable data transmission|overhead|' \
               r'subsequent requests|resource consumption|TCP handshakes|sockets|deliberately closed|OSI model|' \
               r'application layer attacks|network layer attacks|session layer attacks|physical layer attacks|' \
               r'denial-of-service|distributed denial-of-service|DoS|DDoS|excessive requests|' \
               r'massive request volumes|strategic request volumes|legitimate access|domain name|hosting plan|' \
               r'web hosting|hosting provider|website files|server space|web address|functional website|' \
               r'accessibility|online presence|global access|global accessibility|publicly available|' \
               r'online accessibility|unique web address|rented space|web server|website content|viewing online|' \
               r'accessible to visitors|personal blogs|business websites|low cost|high-end business services|' \
               r'sources of sales|sources of leads|personal computer|public server|diverse technical|' \
               r'budget requirements|internet users|search engines|core functionality|user-friendly environment|' \
               r'affordable prices|service level|consistent operation|stable hosting infrastructure|high uptime|' \
               r'minimal free plans|feature-rich business packages|advanced features|support|essential details|' \
               r'fast site speeds|indexing|environment|intended use|required features|available budget|sales|' \
               r'revenue|online platforms|point of contact|performance lags|unexpected fees|downtime|' \
               r'lost visitor opportunities|visitor patience|comprehensive information|considerations|' \
               r'appropriate hosting solution|technology|global availability|performance|service|hosting details|' \
               r'hosting companies|hosting choices|free advertisement|security threats|complimentary promotion|' \
               r'hosting solution|domain registration|complimentary promotion|related services|' \
               r'indexing by external services|worldwide|technology|web hosting|dedicated hosting|shared hosting|' \
               r'VPS hosting|reseller hosting|cloud|website|domain name|online accessibility|' \
               r'continuous website availability|website files|virtualization|virtual server|virtual environment|' \
               r'virtual private server|site builder|web builder|static site|phonebook of the Internet|' \
               r'website names|numeric-only URLs|web addresses|human-readable domain names|' \
               r'machine-readable IP addresses|text-based identifiers|Internet-connected device|networks|webpage|' \
               r'DNS infrastructure|local network|hostname|human-readable hostname|domain name|domain extension|' \
               r'domain suffix|domain extensions|TLD|final segment|DNS resolution path|domain\'s extension|' \
               r'domain to IP address|digital media|online presence|multimedia files|images|videos|' \
               r'interactive content|website|digital platform|brand recognition|' \
               r'internet-based business operations|multimedia content|browser technology|interactivity|' \
               r'button clicks|form submissions|animations|modern web experiences|tab management|web browsing|' \
               r'back and forward buttons|navigation|web page|web pages|Internet\'s vast content|' \
               r'user practices|input methods|interactive elements)\b'
    text = re.sub(web_terms, r'<span class="odp-green">\1</span>', text)
    
    # Individual web/internet terms (green for strings/URLs)
    web_terms_individual = r'\b(World|Wide|Web|website|webpage|page|pages|internetworking|browser|browsers|' \
                          r'server|servers|client|clients|request|requests|response|responses|datum|resource|' \
                          r'system|foundation|content|communication|communicate|inform|information|transfer|' \
                          r'transfers|packet|packets|frame|frames|message|messages|record|records|address|' \
                          r'addresses|route|routes|traffic|transact|transaction|transactions|network|networks|' \
                          r'device|medium|media|interact|interactive|text|texts|login|logins|command|commands|' \
                          r'operation|operations|sequence|sequences|hyper|link|links|linked|site|sites|exchange|' \
                          r'exchanges|diagnostic|diagnose|report|reports|email|emails|payload|payloads|domain|' \
                          r'domains|inbound|outbound|incoming|outgoing|congest|congestion|feature|features|core|' \
                          r'mechanism|mechanisms|general|correspond|corresponds|standard|standards|interact|' \
                          r'interacts|interaction|interactions|encode|encoded|submit|submission|query|queries|' \
                          r'encrypt|encryption|version|versions|structure|structured|authenticate|authentication|' \
                          r'agent|agents|type|types|malware|form|forms|security|secure|multi|faceted|token|' \
                          r'tokens|key|keys|value|values|pair|pairs|textual|text-based|detail|details|' \
                          r'instruction|metadata|parameter|parameters|syntax|URL|cookie|cookies|session|' \
                          r'identifier|identifiers|body|multipart|submitted|inputs|JSON|XML|offline|data|' \
                          r'precedence|preceding|valuable|returned|direct|unencrypted|encrypted|specifics|' \
                          r'details|requested|asked|language|reading|mode|hosting|host|hosts|public|publicly|' \
                          r'accessible|global|globally|functional|budget|sales|leads|load|loading|quick|quickly|' \
                          r'fast|slow|visitors|visitor|allocation|space|spaces|provider|providers|plan|plans|' \
                          r'files|file|user|users|connectivity|rental|rent|renting|hosting|provider|' \
                          r'website files|server space|web address|functional website|accessibility|' \
                          r'online presence|global access|global accessibility|publicly available|' \
                          r'online accessibility|unique web address|rented space|web server|website content|' \
                          r'viewing online|accessible to visitors|personal blogs|business websites|low cost|' \
                          r'high-end business services|sources of sales|sources of leads|personal computer|' \
                          r'public server|beginners|technical|diverse|alternatives|patience|promotion|popularity|' \
                          r'opportunities|affordable|support|platform|information|considerations|solution|' \
                          r'customers|branding|hosting|reliable|conversion|visitor|visitors|search|searches|' \
                          r'high-traffic|static|performance|experience|skills|expertise|convenience|' \
                          r'infrastructure|operation|technical|internet|index|indices|indexed|indexing|device|' \
                          r'devices|available|availability|store|stored|storage|service|services|level|global|' \
                          r'access|world|worldwide|requirement|requirements|beginner|budget|speed|speeds|' \
                          r'business|businesses|engine|engines|ranking|registration|privilege|privileges|trend|' \
                          r'trends|configuration|configurations|visibility|income|technology|virtual|dedicated|' \
                          r'shared|reseller|cloud|phonebook|human-readable|machine-readable|text-based|' \
                          r'numeric-only|connected|infrastructure|webpage|local|hostname|domain|segment|' \
                          r'extension|suffix|rack|library|racks|lookup|lookups|IP|digital|media|presence|' \
                          r'multimedia|image|recognition|interactivity|animation|animations|tab|tabs|interactive|' \
                          r'browsing|back|forward|button|buttons|navigation)\b'
    text = re.sub(web_terms_individual, r'<span class="odp-green">\1</span>', text)
    
    # Networking components and hardware (red for variables/components/errors)
    components = r'\b(server|client machine|router|switch|firewall|DNS queries|static IP address|email message|' \
                r'browsers|hosts|machine addresses|physical machine|networked devices|MAC address|' \
                r'server-side scripts|storage|file system path|web host|domain registrar|verification token|' \
                r'DNS resolver|anti-malware signature|firewall configuration|time-based one-time password|' \
                r'hardware versions|database system|server resource|server memory capacity|compression settings|' \
                r'physical hardware|operating system level|hardware configuration|programming language|' \
                r'network analysis tools|browser\'s developer tools|DNS records|user-agent strings|' \
                r'database schema|IP address|network tab|username|password|credentials|user credentials|' \
                r'client hardware|DNS root record|SSL private key|blockchain ledger|DNS infrastructure|' \
                r'device driver|driver updates|client hardware|routing table|server\'s private key|' \
                r'zone transfers|add-ons manager|reading mode|data inspector|browser extensions|raw HTTP traffic|' \
                r'unauthorized users|unauthorized access|target device|hardware and signal transmission|' \
                r'IP-based operations|personal computer|social media platforms|email marketing software|' \
                r'security certificate|social media manager|graphic designer|custom email address|' \
                r'paid advertising|social media listing|offline marketing campaigns|local hard drive|mirror copy|' \
                r'local network|open-source content management systems|email campaigns|domain registration services|' \
                r'marketing tools|streaming services|analytics plugin|social media followers|government agencies|' \
                r'contact forms|chat features|web server|personal computer|local desktop folder|' \
                r'shared network drive|mobile application repository|server management console|' \
                r'database query engine|peer-to-peer file sharing platform|remote email server|design agency|' \
                r'content delivery network|shared network drive|powerful computer|virtual environments|' \
                r'virtualization software|administrative privileges|IP addresses|manufacturer serial codes|' \
                r'hardware serial numbers|serial numbers|device identifiers|physical device identifiers|hostname|' \
                r'resolvers|MAC address|private device credentials|firewall list|root servers|DNS recursor|' \
                r'DNS recursors|root nameserver|root nameservers|top-level domain nameserver|' \
                r'top-level domain nameservers|authoritative nameserver|authoritative nameservers|' \
                r'TLD nameserver|TLD nameservers|physical locations|offline distribution hubs|user interface|' \
                r'rendering engine|networking component|JavaScript engine|security components|address bar|' \
                r'navigation buttons|specialized components|specialized systems|' \
                r'distinct parts|different components|specialized modules|gadgets|code)\b'
    text = safe_highlight(components, r'<span class="odp-red">\1</span>', text)
    
    # Individual component words (red for variables/hardware)
    components_individual = r'\b(machine|machines|router|routers|switch|switches|firewall|firewalls|query|' \
                           r'queries|static|dynamic|host|hosts|address|addresses|physical|hardware|networked|' \
                           r'network|device|devices|browser|browsers|MAC|server-side|script|scripts|storage|' \
                           r'file|path|paths|host|hosts|registrar|registrars|verification|resolver|resolvers|' \
                           r'signature|signatures|configuration|configurations|password|passwords|time-based|' \
                           r'database|system|systems|memory|capacity|compression|level|resource|resources|' \
                           r'hardware-level|setup|programming|language|languages|environment|environments|' \
                           r'analysis|tools|tool|tab|tabs|developer|schema|schemas|string|strings|record|records|' \
                           r'user-agent|username|credential|credentials|root|ledger|driver|drivers|private|zone|' \
                           r'zones|transfer|transfers|infrastructure|SSL|SMTP|FTP|add-ons|manager|data|inspector|' \
                           r'extensions|raw|unauthorized|access|social|media|platforms|marketing|campaign|' \
                           r'campaigns|certificate|certificates|designer|designers|custom|email|advertisement|' \
                           r'advertising|listing|offline|local|mirror|copy|streaming|plugin|plugins|analytics|' \
                           r'follower|followers|agency|agencies|government|chat|forms|form|contact|personal|' \
                           r'machine|computer|storage|device|brochure|brochures|agency|agencies|control|manager|' \
                           r'token|custom|drive|images|photos|virtualization|virtual|administrative|privileges|' \
                           r'serial|code|codes|hostname|root|firewall|recursor|recursors|nameserver|nameservers|' \
                           r'physical|offline|location|locations|distribution|hubs|hub|logistics|interface|' \
                           r'component|components|module|modules|part|parts|phishing|malware|threats|threat)\b'
    text = safe_highlight(components_individual, r'<span class="odp-red">\1</span>', text)
    
    # Hosting types (brightYellow for configuration options/parameters)
    hosting_types = r'\b(shared hosting|dedicated hosting|VPS hosting|reseller hosting|virtual private server|' \
                   r'free hosting|paid hosting|enterprise hosting|cloud hosting|government hosting|' \
                   r'academic hosting|personal hosting|group hosting|email hosting|video hosting|audio hosting|' \
                   r'image hosting|managed WordPress hosting|dedicated server|shared servers|limited privileges|' \
                   r'advanced configurations|advanced management expertise|user-friendly environment|' \
                   r'moderate technical skills)\b'
    text = safe_highlight(hosting_types, r'<span class="odp-brightYellow">\1</span>', text)
    
    # Error conditions and negation terms (red for errors/exceptions)
    error_conditions = r'\b(not|rather than|instead of|does not|cannot|no|never|unrelated|confuses|' + \
                 r'mandatory|compulsory|required|typically|generally|occur|only|beyond|contradicting|' + \
                 r'without|inaccurate|separate|lack|fails|failed|different|differences|mistakenly|' + \
                 r'wrong|unlikely|ineffective|exclusively|if not|merely|restricted|inappropriate|' + \
                 r'independent|incompatible|inadequate|specialized license|permission)\b'
    text = safe_highlight(error_conditions, r'<span class="odp-red">\1</span>', text)
    
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
    
    # Final check to fix any potential overlapping spans that might have been created during markdown conversion
    # This regex looks for malformed span patterns like nested spans with class="odp-*"
    malformed_span_pattern = r'<span class="odp-([^"]*)">([^<>]*)<span class="odp-[^"]*">([^<>]*)</span>([^<>]*)</span>'
    while re.search(malformed_span_pattern, html):
        html = re.sub(malformed_span_pattern, 
                     r'<span class="odp-\1">\2\3\4</span>',
                     html)
    
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
            border-left: 4px solid #d19a66;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            transition: all 0.3s ease;
        }
        
        /* One Dark Pro Syntax Highlighting */
        /* Main background color for the exam card UI and code editor backgrounds */
        .odp-background { background-color: #282C34; }
        
        /* Used for UI container backgrounds, inactive elements, and secondary panels;
           In CS context: namespaces, scopes, contexts, virtual environments */
        .odp-black { color: #3F4451; }
        
        /* Used for functions, methods, protocols, API endpoints, hooks, callbacks, HTTP components, network operations;
           Also includes: Cloud services (AWS Lambda, Azure Functions), Docker commands, CI/CD operations,
           Git operations, REST/GraphQL endpoints, terminal commands, shell scripts, build tools, deployment scripts,
           database operations (SELECT, INSERT, JOIN), runtime methods, lifecycle hooks */
        .odp-blue { color: #61afef; }
        
        /* Used for secondary text, line numbers in code blocks, comments, documentation notes;
           In CS context: complexity annotations (O(n), Θ(n log n)), code metadata */
        .odp-brightBlack { color: #4F5666; }
        
        /* Used for focused UI elements, selected interactive elements, active states;
           In CS context: currently executing code, runtime focus, primary call paths, main threads */
        .odp-brightBlue { color: #4dc4ff; }
        
        /* Used for highlighting special characters in code, escape sequences, regex patterns;
           In CS context: operators, pointer dereferencing, bitwise operations, mathematical operations,
           state transitions, pipeline operators, logical gates, query operators */
        .odp-brightCyan { color: #4cd1e0; }
        
        /* Used for success messages, correct selections, "added" content in diffs;
           In CS context: passed tests, validated data, successful operations, optimization gains,
           performance improvements, positive metrics, resource efficiencies */
        .odp-brightGreen { color: #a5e075; }
        
        /* Used for highlighted keywords, decorators, special directives in code;
           In CS context: advanced language features, metaprogramming, reflection capabilities,
           compiler directives, preprocessor commands, build configurations, annotations, transformers */
        .odp-brightPurple { color: #de73ff; }
        
        /* Used for error messages, deleted content in explanations, warnings;
           In CS context: exceptions, error states, failures, bugs, vulnerabilities,
           security threats, deprecated features, memory leaks, race conditions, deadlocks */
        .odp-brightRed { color: #be5046; }
        
        /* Primary text color for UI elements and important text, button labels;
           In CS context: core concepts, key principles, algorithm names, paradigm names */
        .odp-brightWhite { color: #e6e6e6; }
        
        /* Used for highlighting parameters, object attributes, property accesses;
           In CS context: function parameters, method arguments, configuration options,
           template variables, environment variables, feature flags */
        .odp-brightYellow { color: #e5c07b; }
        
        /* Used for cursor and selection highlights in editable fields;
           In CS context: execution pointers, breakpoints, step-through debugging, 
           current instruction pointers, memory inspection points */
        .odp-cursorColor { color: #528BFF; }
        
        /* Used for operators, technical actions, logical operations, pipeline steps;
           In CS context: data transformations, ETL processes, state mutations, computations,
           algorithmic operations, data flow indicators, system transitions, queue operations */
        .odp-cyan { color: #56b6c2; }
        
        /* Default text color for most content in the cards, standard code, descriptions;
           In CS context: general explanations, code outlines, pseudocode, algorithm descriptions */
        .odp-foreground { color: #ABB2BF; }
        
        /* Used for strings, web-related terms, URLs, file paths, output text;
           In CS context: web technologies (HTML, CSS, HTTP), network concepts,
           frontend frameworks, UI/UX terminology, rendering processes, DOM elements,
           accessibility terms, internationalization, user interaction patterns */
        .odp-green { color: #98c379; }
        
        /* Used for keywords, protocol names, programming languages, frameworks, libraries;
           In CS context: language-specific keywords (if, for, class, async), type names,
           framework names (React, Angular, Django), design patterns, architectural patterns,
           programming paradigms (OOP, FP), middleware components */
        .odp-purple { color: #c678dd; }
        
        /* Used for variables, negation terms, hardware components, tags, errors;
           In CS context: variable names, field names, error conditions, exception names,
           DOM elements, components, instances, hardware references, memory addresses,
           resource identifiers, destructive operations, system interrupts */
        .odp-red { color: #e06c75; }
        
        /* Used for selection backgrounds, highlighted content;
           In CS context: selected code blocks, diff highlights, comparison sections */
        .odp-selectionBackground { background-color: #ABB2BF; }
        
        /* Used for punctuation, secondary UI elements, structural elements;
           In CS context: brackets, parentheses, syntactic elements, separators,
           structural markers, delimiters, line terminators */
        .odp-white { color: #D7DAE0; }
        
        /* Used for numbers, architecture concepts, attributes, identifiers;
           In CS context: numeric literals, constants, enum values, port numbers,
           status codes, bit flags, bitmasks, version numbers, indices, coordinates,
           memory addresses, capacities, performance metrics, database fields */
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
    # Create exam card type - only 1 correct, 3 incorrect options
    create_exam_note_type(1, 3)  # ExamCard13vx (1 correct, 3 incorrect options)

# Add the init hook
gui_hooks.profile_did_open.append(init) 