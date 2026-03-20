"""
Attack Narrative Generator
LLM writes a full attacker story — how a real threat actor would breach this app,
step by step, from initial recon to full compromise.
"""
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from typing import Dict, List, Optional
import structlog
from config import settings

log = structlog.get_logger()

NARRATIVE_PROMPT = PromptTemplate(
    input_variables=[
        "repo_name", "tech_stack", "findings_summary",
        "ghost_commits", "recon_summary", "threat_actor"
    ],
    template="""You are a senior red team operator writing an attack narrative report.

Target: {repo_name}
Tech Stack: {tech_stack}
Threat Actor Profile Match: {threat_actor}

Vulnerabilities Found:
{findings_summary}

Git History Secrets: {ghost_commits}

Recon Intelligence: {recon_summary}

Write a realistic, step-by-step attack narrative showing exactly how a skilled attacker would compromise this application. Format it as a numbered attack playbook.

Rules:
- Write from the attacker's perspective ("I would...", "The attacker...")
- Be specific to the actual vulnerabilities found above
- Show the attack chain from initial access to full compromise
- Each step should reference the actual file paths and vulnerability types found
- Include estimated time for each phase
- End with "Impact" — what the attacker achieves
- Keep it under 400 words
- Make it realistic and technical, not generic

Write the narrative now:
""",
)


class AttackNarrativeGenerator:
    def __init__(self):
        self.llm = ChatGroq(
            model=settings.GROQ_MODEL,
            api_key=settings.GROQ_API_KEY,
            temperature=0.4,
        )

    def generate(
        self,
        repo_name: str,
        findings: List[Dict],
        ghost_commits: List[Dict],
        recon_data: Dict,
        threat_actor: Optional[Dict],
        chains: List[Dict],
    ) -> str:
        if not settings.GROQ_API_KEY:
            return self._fallback_narrative(findings, chains)

        # Build findings summary
        critical = [f for f in findings if f.get("severity") in ("critical", "high")][:8]
        findings_summary = "\n".join(
            f"- {f.get('severity','').upper()}: {f.get('title','')} "
            f"in {f.get('file_path','')}:{f.get('line_number','')} — "
            f"{f.get('plain_impact','')}"
            for f in critical
        ) or "No critical findings"

        # Tech stack
        tech_stack = ", ".join(
            t["tech"] for t in recon_data.get("tech_stack", [])
        ) or "Unknown"

        # Ghost commits
        ghost_summary = (
            f"{len(ghost_commits)} secrets found in git history: "
            + ", ".join(g.get("secret_type", "") for g in ghost_commits[:3])
            if ghost_commits else "None"
        )

        # Recon summary
        recon_summary = recon_data.get("recon_summary", "No recon data")
        endpoints = recon_data.get("attack_surface", [])
        if endpoints:
            recon_summary += f"\n{len(endpoints)} endpoints mapped: " + ", ".join(
                f"{e.get('method')} {e.get('path')}" for e in endpoints[:5]
            )

        # Threat actor
        actor_info = (
            f"{threat_actor['name']} ({threat_actor['origin']}) — "
            f"matched on: {', '.join(threat_actor.get('matched_vulns', []))}"
            if threat_actor else "Unknown threat actor"
        )

        try:
            chain = NARRATIVE_PROMPT | self.llm | StrOutputParser()
            narrative = chain.invoke({
                "repo_name": repo_name,
                "tech_stack": tech_stack,
                "findings_summary": findings_summary,
                "ghost_commits": ghost_summary,
                "recon_summary": recon_summary,
                "threat_actor": actor_info,
            })
            log.info("Attack narrative generated", repo=repo_name)
            return narrative.strip()
        except Exception as e:
            log.warning("Narrative generation failed", error=str(e))
            return self._fallback_narrative(findings, chains)

    def _fallback_narrative(self, findings: List[Dict], chains: List[Dict]) -> str:
        """Generate a template narrative when LLM is unavailable."""
        critical = [f for f in findings if f.get("severity") == "critical"]
        high = [f for f in findings if f.get("severity") == "high"]

        steps = []
        step = 1

        steps.append(f"**Step {step}: Reconnaissance** (~5 min)")
        steps.append("Clone the repository and scan for exposed secrets, tech stack fingerprinting, and endpoint mapping.")
        step += 1

        if critical:
            f = critical[0]
            steps.append(f"\n**Step {step}: Initial Access** (~10 min)")
            steps.append(f"Exploit {f.get('title','')} in `{f.get('file_path','')}:{f.get('line_number','')}`.")
            steps.append(f"Impact: {f.get('plain_impact','')}")
            step += 1

        if len(critical) > 1 or high:
            target = critical[1] if len(critical) > 1 else high[0]
            steps.append(f"\n**Step {step}: Privilege Escalation** (~15 min)")
            steps.append(f"Chain {target.get('title','')} to escalate access.")
            step += 1

        if chains:
            steps.append(f"\n**Step {step}: Lateral Movement**")
            steps.append(f"Follow exploit chain: {chains[0].get('attack_narrative','')[:200]}")
            step += 1

        steps.append(f"\n**Impact:** Full application compromise — database access, credential theft, potential server takeover.")

        return "\n".join(steps)
