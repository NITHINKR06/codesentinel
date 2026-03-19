from typing import Dict, List
import structlog
from engines.red.poc_generator import PoCGenerator

log = structlog.get_logger()

MAX_RETRIES = 3


class PatchValidator:
    def __init__(self):
        self.poc_gen = PoCGenerator()

    def validate(self, finding: Dict, patch: Dict) -> Dict:
        poc = finding.get("poc_exploit")
        if not poc:
            # Generate PoC first
            poc = self.poc_gen.generate_poc(finding)
            finding["poc_exploit"] = poc

        attempts = 0
        current_patch = patch["patched_code"]

        while attempts < MAX_RETRIES:
            attempts += 1
            result = self.poc_gen.validate_patch(finding, current_patch, poc)

            if result["blocked"]:
                log.info("Patch verified", file=patch["file_path"], attempts=attempts)
                return {
                    **patch,
                    "validated": True,
                    "validation_attempts": attempts,
                    "validation_notes": f"Verified after {attempts} attempt(s). {result['reason']}",
                }
            else:
                log.warning("Patch bypassed, regenerating", attempt=attempts, reason=result["reason"])
                if attempts < MAX_RETRIES:
                    # Ask for a stronger patch
                    from engines.blue.patch_generator import PatchGenerator
                    pg = PatchGenerator()
                    improved = pg.generate_patch(
                        {**finding, "description": f"{finding.get('description','')} Previous fix was bypassed: {result['reason']}"},
                        current_patch,
                    )
                    if improved:
                        current_patch = improved

        log.warning("Patch could not be fully validated", file=patch["file_path"])
        return {
            **patch,
            "patched_code": current_patch,
            "validated": False,
            "validation_attempts": attempts,
            "validation_notes": "Could not verify patch after 3 attempts. Manual review recommended.",
        }

    def validate_all(self, findings: List[Dict], patches: List[Dict]) -> List[Dict]:
        finding_map = {f.get("id", f.get("file_path", "") + str(f.get("line_number", ""))): f for f in findings}
        validated = []
        for patch in patches:
            fid = patch.get("finding_id")
            finding = finding_map.get(fid)
            if not finding:
                validated.append({**patch, "validated": False, "validation_notes": "Finding not found"})
                continue
            validated.append(self.validate(finding, patch))
        return validated
