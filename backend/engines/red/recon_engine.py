"""
Attacker Recon Engine
Simulates what a black-hat sees BEFORE touching the code.
No exploitation — pure intelligence gathering.
"""
import re
import httpx
from typing import Dict, List, Optional
from pathlib import Path
import structlog

log = structlog.get_logger()

# Known CVE-affected dependency versions (simplified — real tool would use OSV/NVD API)
KNOWN_VULNERABLE_DEPS = {
    "express": [("< 4.17.3", "XSS via response splitting", "HIGH")],
    "lodash": [("< 4.17.21", "Prototype pollution", "CRITICAL")],
    "axios": [("< 0.21.2", "SSRF via redirect", "HIGH")],
    "django": [("< 3.2.13", "SQL injection", "CRITICAL")],
    "flask": [("< 2.0.0", "Open redirect", "MEDIUM")],
    "numpy": [("< 1.22.0", "Buffer overflow", "HIGH")],
    "pillow": [("< 9.0.0", "Arbitrary code execution", "CRITICAL")],
    "requests": [("< 2.27.0", "Header injection", "MEDIUM")],
    "jsonwebtoken": [("< 8.5.1", "Algorithm confusion attack", "CRITICAL")],
    "mongoose": [("< 5.13.15", "Prototype pollution", "HIGH")],
    "next": [("< 13.4.0", "Open redirect", "MEDIUM")],
    "react-scripts": [("< 5.0.0", "Dependency confusion", "HIGH")],
}

SENSITIVE_FILE_PATTERNS = [
    r"\.env$", r"\.env\.", r"config\.json$", r"secrets\.json$",
    r"credentials\.json$", r"private\.key$", r"id_rsa$",
    r"\.pem$", r"database\.yml$", r"settings\.py$",
    r"application\.properties$", r"wp-config\.php$",
]

INTERESTING_EXTENSIONS = {".env", ".key", ".pem", ".p12", ".pfx", ".cer"}

TECH_INDICATORS = {
    "Next.js": ["next.config.js", "next.config.ts", ".next"],
    "React": ["package.json:react", "src/App.jsx", "src/App.tsx"],
    "FastAPI": ["main.py:fastapi", "requirements.txt:fastapi"],
    "Django": ["manage.py", "settings.py", "urls.py"],
    "Flask": ["app.py:flask", "requirements.txt:flask"],
    "Express": ["package.json:express", "app.js:express"],
    "Docker": ["Dockerfile", "docker-compose.yml"],
    "Firebase": ["firebase.json", ".firebaserc"],
    "MongoDB": ["requirements.txt:pymongo", "package.json:mongoose"],
    "PostgreSQL": ["requirements.txt:psycopg2", "package.json:pg"],
    "Redis": ["requirements.txt:redis", "package.json:redis"],
}


class AttackerRecon:
    def __init__(self, repo_url: str, files: List[Dict], repo_path: Optional[str] = None):
        self.repo_url = repo_url
        self.files = files
        self.repo_path = repo_path
        self.file_map = {f["path"]: f["content"] for f in files}
        self.findings = []

    def run_full_recon(self) -> Dict:
        log.info("Starting attacker recon", url=self.repo_url)

        result = {
            "tech_stack": self._fingerprint_tech_stack(),
            "exposed_secrets": self._find_exposed_secrets(),
            "sensitive_files": self._find_sensitive_files(),
            "dependency_vulns": self._scan_dependencies(),
            "attack_surface": self._map_attack_surface(),
            "readme_intel": self._extract_readme_intel(),
            "env_example_leaks": self._check_env_examples(),
            "recon_summary": "",
        }

        result["recon_summary"] = self._build_summary(result)
        log.info("Recon complete", findings=len(result["exposed_secrets"]) + len(result["dependency_vulns"]))
        return result

    def _fingerprint_tech_stack(self) -> List[Dict]:
        detected = []
        all_content = " ".join(self.file_map.values())
        all_paths = " ".join(self.file_map.keys())

        for tech, indicators in TECH_INDICATORS.items():
            for indicator in indicators:
                if ":" in indicator:
                    fname, keyword = indicator.split(":", 1)
                    for path, content in self.file_map.items():
                        if fname in path and keyword.lower() in content.lower():
                            detected.append({"tech": tech, "indicator": indicator, "confidence": "high"})
                            break
                else:
                    if indicator in all_paths:
                        detected.append({"tech": tech, "indicator": indicator, "confidence": "high"})

        return detected

    def _find_exposed_secrets(self) -> List[Dict]:
        secrets = []
        secret_patterns = [
            (r'AKIA[0-9A-Z]{16}', "AWS Access Key ID", "CRITICAL"),
            (r'ghp_[a-zA-Z0-9]{36}', "GitHub Personal Token", "CRITICAL"),
            (r'sk-[a-zA-Z0-9]{32,}', "OpenAI API Key", "CRITICAL"),
            (r'AIza[0-9A-Za-z\-_]{35}', "Google API Key", "HIGH"),
            (r'xox[baprs]-[0-9A-Za-z\-]{10,}', "Slack Token", "CRITICAL"),
            (r'-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----', "Private Key", "CRITICAL"),
            (r'mongodb(\+srv)?://[^@\s]+:[^@\s]+@', "MongoDB URI with credentials", "CRITICAL"),
            (r'postgresql://[^@\s]+:[^@\s]+@', "PostgreSQL URI with credentials", "CRITICAL"),
            (r'(password|passwd|pwd)\s*[=:]\s*["\'][^"\']{8,}["\']', "Hardcoded password", "HIGH"),
            (r'(api_key|apikey|api_secret)\s*[=:]\s*["\'][^"\']{10,}["\']', "Hardcoded API key", "HIGH"),
            (r'(secret_key|jwt_secret|session_secret)\s*[=:]\s*["\'][^"\']{8,}["\']', "Hardcoded secret", "HIGH"),
        ]

        for path, content in self.file_map.items():
            for pattern, label, severity in secret_patterns:
                for match in re.finditer(pattern, content, re.IGNORECASE):
                    preview = match.group(0)[:50]
                    # Mask middle of secret for display
                    if len(preview) > 20:
                        preview = preview[:8] + "..." + preview[-6:]
                    secrets.append({
                        "file": path,
                        "type": label,
                        "severity": severity,
                        "preview": preview,
                        "line": content[:match.start()].count("\n") + 1,
                        "attacker_value": self._explain_secret_value(label),
                    })

        return secrets

    def _explain_secret_value(self, secret_type: str) -> str:
        explanations = {
            "AWS Access Key ID": "Full AWS account access — S3, EC2, IAM, everything",
            "GitHub Personal Token": "Read/write all repos, create webhooks, access org secrets",
            "OpenAI API Key": "Unlimited API calls billed to victim — costs thousands",
            "Google API Key": "Access Maps, GCP services, potentially admin console",
            "Slack Token": "Read all messages, DMs, files in the workspace",
            "Private Key": "Impersonate the server, decrypt all TLS traffic",
            "MongoDB URI with credentials": "Full database read/write/delete access",
            "PostgreSQL URI with credentials": "Full database access including schema changes",
            "Hardcoded password": "Direct credential for the application or database",
            "Hardcoded API key": "Direct API access to third-party service",
            "Hardcoded secret": "JWT forgery, session hijacking, or service access",
        }
        return explanations.get(secret_type, "Direct unauthorized access to protected resource")

    def _find_sensitive_files(self) -> List[Dict]:
        sensitive = []
        for path in self.file_map.keys():
            for pattern in SENSITIVE_FILE_PATTERNS:
                if re.search(pattern, path, re.IGNORECASE):
                    sensitive.append({
                        "file": path,
                        "reason": f"Sensitive file pattern: {pattern}",
                        "risk": "HIGH",
                        "attacker_note": "Attackers scan for these first — automated tools find these in seconds",
                    })
                    break
            ext = Path(path).suffix.lower()
            if ext in INTERESTING_EXTENSIONS:
                sensitive.append({
                    "file": path,
                    "reason": f"Sensitive extension: {ext}",
                    "risk": "CRITICAL",
                    "attacker_note": f"{ext} files should never be in a repository",
                })
        return sensitive

    def _scan_dependencies(self) -> List[Dict]:
        vulns = []
        # Check package.json
        for path, content in self.file_map.items():
            if "package.json" in path and "node_modules" not in path:
                try:
                    import json
                    pkg = json.loads(content)
                    deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
                    for dep, version in deps.items():
                        dep_lower = dep.lower()
                        if dep_lower in KNOWN_VULNERABLE_DEPS:
                            for vuln_range, desc, severity in KNOWN_VULNERABLE_DEPS[dep_lower]:
                                vulns.append({
                                    "package": dep,
                                    "version": version,
                                    "vulnerable_range": vuln_range,
                                    "description": desc,
                                    "severity": severity,
                                    "file": path,
                                })
                except Exception:
                    pass

            # Check requirements.txt
            if "requirements" in path and path.endswith(".txt"):
                for line in content.split("\n"):
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    pkg_name = re.split(r"[>=<!]", line)[0].strip().lower()
                    if pkg_name in KNOWN_VULNERABLE_DEPS:
                        for vuln_range, desc, severity in KNOWN_VULNERABLE_DEPS[pkg_name]:
                            vulns.append({
                                "package": pkg_name,
                                "version": line,
                                "vulnerable_range": vuln_range,
                                "description": desc,
                                "severity": severity,
                                "file": path,
                            })
        return vulns

    def _map_attack_surface(self) -> List[Dict]:
        """Find all exposed endpoints/routes."""
        endpoints = []
        route_patterns = [
            # FastAPI/Flask
            (r'@(?:app|router)\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']', "Python route"),
            # Express
            (r'(?:app|router)\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']', "Express route"),
            # Next.js API
            (r'export\s+(?:default\s+)?(?:async\s+)?function\s+\w+.*pages/api', "Next.js API"),
        ]

        for path, content in self.file_map.items():
            for pattern, route_type in route_patterns:
                for match in re.finditer(pattern, content, re.IGNORECASE):
                    method = match.group(1).upper() if match.lastindex >= 1 else "GET"
                    endpoint = match.group(2) if match.lastindex >= 2 else path
                    endpoints.append({
                        "method": method,
                        "path": endpoint,
                        "file": path,
                        "line": content[:match.start()].count("\n") + 1,
                        "type": route_type,
                        "risk": "HIGH" if method in ("POST", "PUT", "DELETE", "PATCH") else "MEDIUM",
                    })

        return endpoints[:30]  # cap at 30

    def _extract_readme_intel(self) -> Dict:
        """Extract intelligence from README that attackers use."""
        intel = {
            "urls": [],
            "technologies": [],
            "credentials_mentioned": [],
            "architecture_hints": [],
        }

        for path, content in self.file_map.items():
            if "readme" in path.lower():
                # URLs
                urls = re.findall(r'https?://[^\s\)\"\']+', content)
                intel["urls"] = list(set(urls))[:10]

                # Tech mentions
                techs = re.findall(r'\b(MongoDB|PostgreSQL|MySQL|Redis|AWS|GCP|Azure|Docker|Kubernetes|nginx|Apache)\b', content, re.IGNORECASE)
                intel["technologies"] = list(set(techs))

                # Credential hints
                cred_hints = re.findall(r'(?:default\s+(?:password|credentials?|login)|test\s+(?:user|account)|admin\s+(?:panel|dashboard))[^\n]*', content, re.IGNORECASE)
                intel["credentials_mentioned"] = cred_hints[:5]

                # Architecture
                arch_hints = re.findall(r'(?:runs on|deployed on|hosted on|uses)[^\n]+', content, re.IGNORECASE)
                intel["architecture_hints"] = arch_hints[:5]

        return intel

    def _check_env_examples(self) -> List[Dict]:
        """Find .env.example files that reveal what secrets exist."""
        leaks = []
        for path, content in self.file_map.items():
            if ".env" in path.lower() or "env.example" in path.lower() or "env.sample" in path.lower():
                keys = []
                for line in content.split("\n"):
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key = line.split("=")[0].strip()
                        value = line.split("=", 1)[1].strip() if "=" in line else ""
                        keys.append({
                            "key": key,
                            "has_value": bool(value and value not in ("", '""', "''", "your_key_here", "changeme")),
                        })
                if keys:
                    leaks.append({
                        "file": path,
                        "keys_exposed": keys,
                        "attacker_note": "Reveals exactly what secrets to hunt for — a shopping list for attackers",
                        "severity": "MEDIUM",
                    })
        return leaks

    def _build_summary(self, result: Dict) -> str:
        critical_secrets = sum(1 for s in result["exposed_secrets"] if s["severity"] == "CRITICAL")
        high_secrets = sum(1 for s in result["exposed_secrets"] if s["severity"] == "HIGH")
        dep_vulns = len(result["dependency_vulns"])
        endpoints = len(result["attack_surface"])
        tech_count = len(result["tech_stack"])

        lines = [
            f"Target fingerprinted: {tech_count} technologies detected.",
            f"Attack surface: {endpoints} exposed endpoints mapped.",
        ]
        if critical_secrets:
            lines.append(f"CRITICAL: {critical_secrets} hardcoded secret(s) found — immediate account compromise possible.")
        if high_secrets:
            lines.append(f"HIGH: {high_secrets} additional credential(s) exposed.")
        if dep_vulns:
            lines.append(f"{dep_vulns} vulnerable dependency version(s) identified.")
        if result["env_example_leaks"]:
            lines.append(f".env example files reveal {sum(len(e['keys_exposed']) for e in result['env_example_leaks'])} secret key names.")

        return " ".join(lines)
