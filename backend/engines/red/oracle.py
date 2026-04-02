from dataclasses import dataclass
from typing import Dict, List


@dataclass
class OracleResult:
    confirmed: bool
    evidence: str
    signal: str

    def to_dict(self) -> Dict:
        return {
            "confirmed": self.confirmed,
            "evidence": self.evidence,
            "signal": self.signal,
        }


class ConfirmationOracle:
    """Type-specific exploit verifier.

    The oracle is intentionally conservative: it only confirms when the
    response contains a clear marker that matches the vulnerability class.
    """

    SIGNALS = {
        "sqli": ["rows returned", "admin", "root:", "total_rows", "union"],
        "xss": ["<script", "onerror", "document.domain", "confirm("],
        "path_traversal": ["root:x:0:0", "[extensions]", "[fonts]", "[boot loader]"],
        "ssrf": ["metadata", "localhost", "127.0.0.1", "open port"],
        "rce": ["uid=", "whoami", "sandbox-cmd::", "code_sentinel_rce_test"],
    }

    def verify(self, vuln_type: str, observation: Dict) -> OracleResult:
        body = (observation.get("body") or "").lower()
        signal_list = self.SIGNALS.get(vuln_type, [])
        matched = next((signal for signal in signal_list if signal.lower() in body), None)
        confirmed = matched is not None
        evidence = matched or "No confirmation marker found"
        return OracleResult(confirmed=confirmed, evidence=evidence, signal=matched or "none")
