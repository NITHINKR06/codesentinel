from typing import List, Dict, Optional
import structlog

log = structlog.get_logger()

# Curated threat actor profiles mapped to vulnerability signatures
# Based on publicly documented MITRE ATT&CK threat intelligence
THREAT_ACTORS = [
    {
        "name": "Lazarus Group",
        "aliases": ["APT38", "Hidden Cobra"],
        "origin": "North Korea",
        "motivation": "Financial theft, espionage",
        "targets": ["Financial institutions", "Cryptocurrency exchanges", "Government"],
        "signature_vulns": ["sqli", "command_injection", "hardcoded_secret"],
        "signature_tactics": ["Initial Access", "Credential Access", "Execution"],
        "known_attacks": [
            "Bangladesh Bank heist ($81M stolen via SWIFT manipulation)",
            "WannaCry ransomware deployment",
            "Crypto exchange targeting via supply chain",
        ],
        "mitre_groups": ["G0032"],
        "risk_level": "critical",
    },
    {
        "name": "APT29 (Cozy Bear)",
        "aliases": ["The Dukes", "Midnight Blizzard"],
        "origin": "Russia (SVR)",
        "motivation": "Espionage, intelligence gathering",
        "targets": ["Government", "Think tanks", "Healthcare", "Energy"],
        "signature_vulns": ["missing_auth", "insecure_deserialization", "path_traversal"],
        "signature_tactics": ["Initial Access", "Persistence", "Defense Evasion"],
        "known_attacks": [
            "SolarWinds Orion supply chain compromise",
            "Democratic National Committee breach",
            "COVID-19 vaccine research targeting",
        ],
        "mitre_groups": ["G0016"],
        "risk_level": "critical",
    },
    {
        "name": "FIN7",
        "aliases": ["Carbanak", "Navigator Group"],
        "origin": "Eastern Europe (cybercriminal)",
        "motivation": "Financial theft",
        "targets": ["Retail", "Hospitality", "Finance", "E-commerce"],
        "signature_vulns": ["sqli", "xss", "hardcoded_secret", "sensitive_logging"],
        "signature_tactics": ["Initial Access", "Credential Access", "Exfiltration"],
        "known_attacks": [
            "Chipotle, Arby's, Red Robin POS system breaches",
            "Over $1B stolen from financial institutions",
            "Carbanak banking malware campaigns",
        ],
        "mitre_groups": ["G0046"],
        "risk_level": "high",
    },
    {
        "name": "Scattered Spider",
        "aliases": ["UNC3944", "Roasted 0ktapus"],
        "origin": "English-speaking cybercriminal",
        "motivation": "Financial extortion, data theft",
        "targets": ["SaaS companies", "Telecom", "Gaming", "Retail"],
        "signature_vulns": ["missing_auth", "hardcoded_secret", "weak_crypto"],
        "signature_tactics": ["Initial Access", "Privilege Escalation", "Exfiltration"],
        "known_attacks": [
            "MGM Resorts $100M ransomware attack",
            "Caesars Entertainment breach",
            "Twilio and Cloudflare phishing campaigns",
        ],
        "mitre_groups": ["G1015"],
        "risk_level": "high",
    },
    {
        "name": "Anonymous / Script Kiddies",
        "aliases": ["Opportunistic attackers"],
        "origin": "Global",
        "motivation": "Notoriety, defacement, data exposure",
        "targets": ["Any publicly accessible web application"],
        "signature_vulns": ["sqli", "xss", "path_traversal", "command_injection"],
        "signature_tactics": ["Initial Access", "Discovery"],
        "known_attacks": [
            "Mass SQLi database dumps posted publicly",
            "Website defacement campaigns",
            "Credential stuffing from leaked databases",
        ],
        "mitre_groups": [],
        "risk_level": "medium",
    },
]


def match_threat_actors(findings: List[Dict]) -> Optional[Dict]:
    """
    Cross-reference scan findings against threat actor profiles.
    Returns the best-matching actor with a match score and explanation.
    """
    if not findings:
        return None

    found_vuln_types = set(f.get("vuln_type") for f in findings)
    found_tactics = set(f.get("mitre_tactic") for f in findings if f.get("mitre_tactic"))

    best_match = None
    best_score = 0

    for actor in THREAT_ACTORS:
        vuln_overlap = found_vuln_types & set(actor["signature_vulns"])
        tactic_overlap = found_tactics & set(actor["signature_tactics"])

        score = len(vuln_overlap) * 2 + len(tactic_overlap)
        if score > best_score:
            best_score = score
            best_match = actor
            best_match = dict(actor)
            best_match["match_score"] = score
            best_match["matched_vulns"] = list(vuln_overlap)
            best_match["matched_tactics"] = list(tactic_overlap)
            best_match["match_explanation"] = _build_explanation(actor, vuln_overlap, tactic_overlap)

    if best_score < 2:
        return None

    log.info("Threat actor matched", actor=best_match["name"], score=best_score)
    return best_match


def _build_explanation(actor: Dict, vuln_overlap: set, tactic_overlap: set) -> str:
    vuln_list = ", ".join(vuln_overlap) if vuln_overlap else "general weaknesses"
    return (
        f"Your application's vulnerability profile ({vuln_list}) matches known attack "
        f"patterns used by {actor['name']}. This group has previously exploited identical "
        f"weaknesses against {', '.join(actor['targets'][:2])}."
    )
