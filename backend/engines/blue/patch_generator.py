from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from typing import Dict, Optional, List
import structlog
from config import settings

log = structlog.get_logger()

PATCH_PROMPT = PromptTemplate(
    input_variables=["vuln_type", "file_path", "vulnerable_code", "surrounding_context", "description"],
    template="""You are a senior security engineer fixing a vulnerability in production code.

Vulnerability: {vuln_type}
File: {file_path}
Issue: {description}

Surrounding Context (for style reference):
```
{surrounding_context}
```

Vulnerable Code to Fix:
```
{vulnerable_code}
```

Rules:
- Fix ONLY this specific vulnerability
- Preserve the existing logic exactly
- Match the code style of the surrounding context
- Do not add unnecessary imports unless required for the fix
- Add a brief inline comment explaining the security fix
- Return ONLY the fixed code, no markdown fences, no explanation

Fixed code:
""",
)

# Language-specific fix templates as fallback
FALLBACK_FIXES = {
    "sqli": {
        "python": "# Use parameterized query\ncursor.execute('SELECT * FROM users WHERE id = %s', (user_id,))",
        "javascript": "// Use parameterized query\ndb.query('SELECT * FROM users WHERE id = ?', [userId], callback);",
        "php": "// Use prepared statement\n$stmt = $pdo->prepare('SELECT * FROM users WHERE id = ?');\n$stmt->execute([$id]);",
    },
    "xss": {
        "javascript": "// Sanitize output\nconst safe = DOMPurify.sanitize(userInput);\nelement.textContent = safe;",
        "python": "# Use template auto-escaping (Jinja2 default)\n# Ensure autoescape=True in Environment",
    },
    "hardcoded_secret": {
        "python": "import os\n# Load from environment variable\nsecret = os.environ.get('SECRET_KEY')\nif not secret:\n    raise RuntimeError('SECRET_KEY environment variable not set')",
        "javascript": "// Load from environment variable\nconst secret = process.env.SECRET_KEY;\nif (!secret) throw new Error('SECRET_KEY not set');",
    },
    "command_injection": {
        "python": "import subprocess, shlex\n# Use list form (never shell=True with user input)\nresult = subprocess.run(['command', shlex.quote(user_input)], capture_output=True, timeout=10)",
        "javascript": "const { execFile } = require('child_process');\n// Use execFile (never exec with user input)\nexecFile('command', [safeArg], callback);",
    },
    "weak_crypto": {
        "python": "import hashlib\n# Use bcrypt or argon2 for passwords; SHA-256+ for integrity\nhashed = hashlib.sha256(data.encode()).hexdigest()",
        "javascript": "const crypto = require('crypto');\n// Use SHA-256 minimum; use bcrypt for passwords\nconst hash = crypto.createHash('sha256').update(data).digest('hex');",
    },
    "insecure_deserialization": {
        "python": "import json\n# Use json instead of pickle for untrusted data\ndata = json.loads(untrusted_string)",
    },
    "path_traversal": {
        "python": "import os\n# Validate and sanitize path\nbase_dir = '/safe/base/dir'\nrequested = os.path.realpath(os.path.join(base_dir, user_input))\nif not requested.startswith(base_dir):\n    raise ValueError('Path traversal detected')",
        "javascript": "const path = require('path');\nconst baseDir = '/safe/base/dir';\nconst safePath = path.resolve(baseDir, userInput);\nif (!safePath.startsWith(baseDir)) throw new Error('Invalid path');",
    },
}

EXT_TO_LANG = {
    ".py": "python", ".js": "javascript", ".ts": "javascript",
    ".tsx": "javascript", ".jsx": "javascript", ".php": "php",
    ".go": "go", ".rb": "ruby", ".java": "java",
}


class PatchGenerator:
    def __init__(self):
        self.llm = ChatGroq(
            model=settings.GROQ_MODEL,
            api_key=settings.GROQ_API_KEY,
            temperature=0.1,
        )

    def generate_patch(self, finding: Dict, file_content: str) -> Optional[str]:
        vuln_line = finding.get("line_number", 1)
        lines = file_content.split("\n")
        start = max(0, vuln_line - 11)
        end = min(len(lines), vuln_line + 10)
        surrounding = "\n".join(lines[start:end])
        vulnerable_code = finding.get("vulnerable_code", lines[vuln_line - 1] if vuln_line <= len(lines) else "")

        try:
            chain = PATCH_PROMPT | self.llm | StrOutputParser()
            result = chain.invoke({
                "vuln_type": finding.get("vuln_type", ""),
                "file_path": finding.get("file_path", ""),
                "vulnerable_code": vulnerable_code,
                "surrounding_context": surrounding,
                "description": finding.get("description", ""),
            })
            patched = result.strip()
            log.info("Patch generated", vuln=finding.get("vuln_type"), file=finding.get("file_path"))
            return patched
        except Exception as e:
            log.error("Patch generation failed, using fallback", error=str(e))
            return self._fallback_patch(finding)

    def _fallback_patch(self, finding: Dict) -> Optional[str]:
        vuln_type = finding.get("vuln_type", "")
        ext = "." + finding.get("file_path", "").split(".")[-1]
        lang = EXT_TO_LANG.get(ext, "python")
        fixes = FALLBACK_FIXES.get(vuln_type, {})
        return fixes.get(lang) or fixes.get("python") or f"# TODO: Fix {vuln_type} vulnerability\n# See OWASP guidelines for {vuln_type}"

    def generate_security_headers(self, framework: str = "generic") -> Dict[str, str]:
        headers = {
            "Content-Security-Policy": "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'",
            "X-Frame-Options": "DENY",
            "X-Content-Type-Options": "nosniff",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
        }

        code_snippets = {
            "express": "\n".join([
                "const helmet = require('helmet');",
                "app.use(helmet());",
                "// Or manually:",
                *[f"app.use((req, res, next) => {{ res.setHeader('{k}', '{v}'); next(); }});" for k, v in list(headers.items())[:3]],
            ]),
            "fastapi": "\n".join([
                "from fastapi.middleware.trustedhost import TrustedHostMiddleware",
                "from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware",
                "",
                "@app.middleware('http')",
                "async def add_security_headers(request, call_next):",
                "    response = await call_next(request)",
                *[f"    response.headers['{k}'] = '{v}'" for k, v in list(headers.items())[:4]],
                "    return response",
            ]),
            "django": "\n".join([
                "# settings.py",
                "SECURE_HSTS_SECONDS = 31536000",
                "SECURE_HSTS_INCLUDE_SUBDOMAINS = True",
                "SECURE_HSTS_PRELOAD = True",
                "X_FRAME_OPTIONS = 'DENY'",
                "SECURE_CONTENT_TYPE_NOSNIFF = True",
                "SECURE_BROWSER_XSS_FILTER = True",
                "CSP_DEFAULT_SRC = (\"'self'\",)",
            ]),
        }

        return {
            "headers": headers,
            "implementation": code_snippets.get(framework, code_snippets["fastapi"]),
        }

    def patch_all_findings(self, findings: List[Dict], files: List[Dict]) -> List[Dict]:
        file_map = {f["path"]: f["content"] for f in files}
        patches = []
        for finding in findings:
            if finding.get("severity") not in ("critical", "high"):
                continue
            file_content = file_map.get(finding.get("file_path", ""), "")
            if not file_content:
                continue
            patched_code = self.generate_patch(finding, file_content)
            if patched_code:
                patches.append({
                    "finding_id": finding.get("id"),
                    "file_path": finding.get("file_path"),
                    "vuln_type": finding.get("vuln_type"),
                    "original_code": finding.get("vulnerable_code", ""),
                    "patched_code": patched_code,
                    "validated": False,
                    "validation_attempts": 0,
                })
        return patches