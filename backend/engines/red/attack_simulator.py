"""Compatibility wrapper for the exploit agent."""

from typing import Dict, List

from engines.red.exploit_agent import ExploitAgent, simulate_all_findings


class LiveAttackSimulator:
    def __init__(self):
        self.agent = ExploitAgent()

    def simulate(self, finding: Dict, poc_exploit: str = "") -> Dict:
        result = self.agent.run(finding)
        result["poc_code"] = poc_exploit
        result["executed"] = bool(result.get("observations"))
        result["output"] = result.get("evidence", "")
        result.setdefault("confirmation_message", "")
        result.setdefault("duration_ms", 0)
        result.setdefault("simulation_notes", "Constrained exploit agent run")
        return result
