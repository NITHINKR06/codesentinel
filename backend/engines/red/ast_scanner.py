import math
import re
from typing import Dict, List

import structlog

from engines.red.taint_engine import scan_python_file

log = structlog.get_logger()

SEVERITY_WEIGHTS = {"critical": 40, "high": 20, "medium": 10, "low": 5}

PATTERNS = {
    "sqli": {
        "severity": "critical",
        "patterns": [
            r"(execute|query|cursor\.execute)\s*\(\s*[\"\'].*%[s].*[\"\']",
            r"(execute|query)\s*\(\s*f[\"\'].*\{",
            r"SELECT.*\+.*request\.",
            r"(\"|\').*\+\s*(request|req|params|body)\.",
            r"raw\s*\(\s*f[\"\']",
            r"\.raw\s*\(.*\+",
        ],
        "title": "SQL Injection",
        "description": "User-controlled input is directly interpolated into a SQL query.",
        "plain_impact": "An attacker can read, modify, or delete your entire database with a single request.",
        "mitre_technique": "T1190",
        "mitre_tactic": "Initial Access",
    },
    "xss": {
        "severity": "high",
        "patterns": [
            r"dangerouslySetInnerHTML",
            r"innerHTML\s*=\s*.*\+",
            r"document\.write\s*\(",
            r"\.html\s*\(\s*(req|request|params)",
            r"res\.send\s*\(\s*req\.",
            r"render_template_string\s*\(",
        ],
        "title": "Cross-Site Scripting (XSS)",
        "description": "Unsanitized user input is reflected into the HTML response.",
        "plain_impact": "Attackers can steal session tokens or run malicious scripts in victims' browsers.",
        "mitre_technique": "T1059.007",
        "mitre_tactic": "Execution",
    },
    "hardcoded_secret": {
        "severity": "critical",
        "patterns": [
            r"(password|passwd|pwd|secret|api_key|apikey|token|auth_token)\s*=\s*[\"\'][^\"\']{6,}[\"\']",
            r"(AWS_SECRET|AWS_KEY|PRIVATE_KEY)\s*=\s*[\"\'][^\"\']+[\"\']",
            r"-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----",
            r"sk-[a-zA-Z0-9]{32,}",
            r"ghp_[a-zA-Z0-9]{36}",
            r"AKIA[0-9A-Z]{16}",
        ],
        "title": "Hardcoded Secret / Credential",
        "description": "A secret key, password, or API token is hardcoded in source code.",
        "plain_impact": "Anyone with access to your repo can use these credentials to access your systems or third-party services.",
        "mitre_technique": "T1552.001",
        "mitre_tactic": "Credential Access",
    },
    "command_injection": {
        "severity": "critical",
        "patterns": [
            r"os\.system\s*\(\s*.*\+",
            r"os\.popen\s*\(\s*.*\+",
            r"subprocess\.(call|run|Popen)\s*\(.*shell\s*=\s*True",
            r"exec\s*\(\s*.*\+",
            r"eval\s*\(\s*.*\+",
            r"child_process\.exec\s*\(\s*.*\+",
        ],
        "title": "Command Injection",
        "description": "User input is passed to shell commands or eval().",
        "plain_impact": "An attacker can execute arbitrary commands on your server with full OS access.",
        "mitre_technique": "T1059",
        "mitre_tactic": "Execution",
    },
    "path_traversal": {
        "severity": "high",
        "patterns": [
            r"open\s*\(\s*.*\+.*request",
            r"open\s*\(\s*f[\"\'].*\{",
            r"readFile\s*\(\s*.*\+.*req\.",
            r"sendFile\s*\(\s*.*\+.*req\.",
            r"path\.join\s*\(.*req\.",
        ],
        "title": "Path Traversal",
        "description": "User input is used to construct file paths without sanitization.",
        "plain_impact": "Attackers can read any file on your server, including /etc/passwd or private keys.",
        "mitre_technique": "T1083",
        "mitre_tactic": "Discovery",
    },
    "missing_auth": {
        "severity": "high",
        "patterns": [
            r"@app\.route\([\"\'][^\"\']+[\"\'],\s*methods=\[.*POST.*\]\)",
            r"router\.(post|put|delete|patch)\s*\([\"\'][^\"\']+[\"\']",
        ],
        "title": "Potentially Unprotected Route",
        "description": "An endpoint that modifies data may be missing authentication checks.",
        "plain_impact": "Unauthenticated users might be able to perform privileged actions.",
        "mitre_technique": "T1078",
        "mitre_tactic": "Defense Evasion",
    },
    "insecure_deserialization": {
        "severity": "critical",
        "patterns": [
            r"pickle\.loads?\s*\(",
            r"yaml\.load\s*\([^,)]+\)",
            r"jsonpickle\.decode\s*\(",
            r"marshal\.loads?\s*\(",
        ],
        "title": "Insecure Deserialization",
        "description": "Unsafe deserialization of untrusted data.",
        "plain_impact": "An attacker can execute arbitrary code on the server by sending a crafted payload.",
        "mitre_technique": "T1190",
        "mitre_tactic": "Initial Access",
    },
    "sensitive_logging": {
        "severity": "medium",
        "patterns": [
            r"(log|logger|print|console\.log)\s*\(.*password",
            r"(log|logger|print|console\.log)\s*\(.*token",
            r"(log|logger|print|console\.log)\s*\(.*secret",
        ],
        "title": "Sensitive Data Logged",
        "description": "Passwords, tokens, or secrets appear to be written to logs.",
        "plain_impact": "Log files can be accessed by attackers to harvest credentials.",
        "mitre_technique": "T1552",
        "mitre_tactic": "Credential Access",
    },
    "weak_crypto": {
        "severity": "high",
        "patterns": [
            r"hashlib\.md5\s*\(",
            r"hashlib\.sha1\s*\(",
            r"MD5\s*\(",
            r"DES\s*\(",
            r"RC4\s*\(",
            r"createHash\s*\(\s*[\"\']md5[\"\']",
            r"createHash\s*\(\s*[\"\']sha1[\"\']",
        ],
        "title": "Weak Cryptographic Algorithm",
        "description": "MD5 or SHA-1 is used for security-sensitive operations.",
        "plain_impact": "Attackers can crack hashed passwords or forge signatures using modern hardware.",
        "mitre_technique": "T1600",
        "mitre_tactic": "Defense Evasion",
    },
}


def _entropy(value: str) -> float:
    if not value:
        return 0.0
    frequency = {}
    for char in value:
        frequency[char] = frequency.get(char, 0) + 1
    return -sum((count / len(value)) * math.log2(count / len(value)) for count in frequency.values())


def scan_file(file_info: Dict) -> List[Dict]:
    content = file_info["content"]
    path = file_info["path"]
    findings = []

    lines = content.split("\n")

    for vuln_key, vuln_def in PATTERNS.items():
        for pattern in vuln_def["patterns"]:
            for line_number, line in enumerate(lines, start=1):
                if re.search(pattern, line, re.IGNORECASE):
                    if any(
                        finding["file_path"] == path
                        and finding["line_number"] == line_number
                        and finding["vuln_type"] == vuln_key
                        for finding in findings
                    ):
                        continue

                    findings.append(
                        {
                            "vuln_type": vuln_key,
                            "severity": vuln_def["severity"],
                            "file_path": path,
                            "line_number": line_number,
                            "title": vuln_def["title"],
                            "description": vuln_def["description"],
                            "plain_impact": vuln_def["plain_impact"],
                            "vulnerable_code": line.strip(),
                            "mitre_technique": vuln_def.get("mitre_technique"),
                            "mitre_tactic": vuln_def.get("mitre_tactic"),
                        }
                    )

    for line_number, line in enumerate(lines, start=1):
        matches = re.findall(r'["\']([a-zA-Z0-9+/=_\-]{20,})["\']', line)
        for match in matches:
            if _entropy(match) > 4.5:
                findings.append(
                    {
                        "vuln_type": "high_entropy_secret",
                        "severity": "high",
                        "file_path": path,
                        "line_number": line_number,
                        "title": "Possible Hardcoded Secret (high entropy)",
                        "description": "High-entropy string detected that may be a secret or key.",
                        "plain_impact": "This string may be a credential or key embedded in code.",
                        "vulnerable_code": line.strip(),
                        "mitre_technique": "T1552.001",
                        "mitre_tactic": "Credential Access",
                    }
                )

    return findings


def scan_files(files: List[Dict]) -> List[Dict]:
    all_findings = []
    for file_info in files:
        extension = file_info.get("extension", "").lower()
        if extension in (".jpg", ".png", ".gif", ".ico", ".woff"):
            continue
        if extension == ".py":
            all_findings.extend(scan_python_file(file_info))
        else:
            all_findings.extend(scan_file(file_info))
    log.info("AST scan complete", files=len(files), findings=len(all_findings))
    return all_findings
