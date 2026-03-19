import re
from typing import List, Dict


FRAMEWORK_DETECTORS = {
    "express": [r"require\(['\"]express['\"]", r"app\.listen\(", r"app\.use\("],
    "fastapi": [r"from fastapi", r"FastAPI\(", r"@app\.(get|post|put|delete)"],
    "django": [r"from django", r"INSTALLED_APPS", r"urlpatterns"],
    "flask": [r"from flask", r"Flask\(__name__\)", r"@app\.route"],
    "nextjs": [r"next/headers", r"NextResponse", r"getServerSideProps"],
}


def detect_framework(files: List[Dict]) -> str:
    content_all = " ".join(f.get("content", "") for f in files[:30])
    for framework, patterns in FRAMEWORK_DETECTORS.items():
        if all(re.search(p, content_all) for p in patterns[:1]):
            return framework
    return "generic"


def generate_header_config(framework: str) -> Dict:
    headers = {
        "Content-Security-Policy": "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; object-src 'none'",
        "X-Frame-Options": "DENY",
        "X-Content-Type-Options": "nosniff",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
        "X-XSS-Protection": "1; mode=block",
    }

    snippets = {
        "express": """// Install: npm install helmet
const helmet = require('helmet');
app.use(helmet());
app.use(helmet.contentSecurityPolicy({
  directives: {
    defaultSrc: ["'self'"],
    scriptSrc: ["'self'"],
    styleSrc: ["'self'", "'unsafe-inline'"],
    objectSrc: ["'none'"],
  },
}));""",

        "fastapi": """# Add to main.py
from starlette.middleware.base import BaseHTTPMiddleware

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        return response

app.add_middleware(SecurityHeadersMiddleware)""",

        "django": """# settings.py
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_SSL_REDIRECT = True
X_FRAME_OPTIONS = "DENY"
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Install: pip install django-csp
CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = ("'self'",)
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'")
CSP_OBJECT_SRC = ("'none'",)""",

        "flask": """# Install: pip install flask-talisman
from flask_talisman import Talisman

csp = {
    'default-src': "'self'",
    'script-src': "'self'",
    'style-src': ["'self'", "'unsafe-inline'"],
    'object-src': "'none'",
}
Talisman(app, content_security_policy=csp, force_https=True)""",

        "nextjs": """// next.config.js
const securityHeaders = [
  { key: 'X-DNS-Prefetch-Control', value: 'on' },
  { key: 'Strict-Transport-Security', value: 'max-age=63072000; includeSubDomains; preload' },
  { key: 'X-Frame-Options', value: 'DENY' },
  { key: 'X-Content-Type-Options', value: 'nosniff' },
  { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
  { key: 'Content-Security-Policy', value: "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'" },
];
module.exports = {
  async headers() {
    return [{ source: '/(.*)', headers: securityHeaders }];
  },
};""",

        "generic": """# Nginx config snippet
add_header Content-Security-Policy "default-src 'self'" always;
add_header X-Frame-Options "DENY" always;
add_header X-Content-Type-Options "nosniff" always;
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
add_header Permissions-Policy "camera=(), microphone=(), geolocation=()" always;""",
    }

    return {
        "framework": framework,
        "headers": headers,
        "implementation_snippet": snippets.get(framework, snippets["generic"]),
        "finding": {
            "title": "Missing Security Headers",
            "severity": "medium",
            "description": f"Security headers are not configured for your {framework} application.",
            "plain_impact": "Without these headers, your app is vulnerable to clickjacking, MIME sniffing, and other browser-based attacks.",
        },
    }
