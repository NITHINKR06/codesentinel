from dataclasses import dataclass
from typing import Dict, Optional
import time
import uuid

import httpx
import structlog

log = structlog.get_logger()


@dataclass
class SandboxTarget:
    target_id: str
    vuln_type: str
    base_url: Optional[str]
    container_name: Optional[str] = None
    ready: bool = False
    notes: str = ""


class SandboxController:
    """Minimal sandbox abstraction used by the exploit agent.

    This implementation intentionally keeps the contract narrow:
    - spin up a named target
    - issue HTTP requests to the target
    - optionally execute a local command for deterministic demos
    """

    def __init__(self, target_base_url: str = "http://127.0.0.1:8080"):
        self.target_base_url = target_base_url.rstrip("/")

    def spin_target(self, vuln_type: str, container_name: Optional[str] = None) -> SandboxTarget:
        target_id = str(uuid.uuid4())
        target = SandboxTarget(
            target_id=target_id,
            vuln_type=vuln_type,
            base_url=self.target_base_url,
            container_name=container_name,
            ready=True,
            notes="Sandbox target registered. Replace base_url with a real Docker target when available.",
        )
        log.info("Sandbox target prepared", vuln=vuln_type, target_id=target_id, base_url=self.target_base_url)
        return target

    def send_request(self, target: SandboxTarget, method: str, path: str, payload: str) -> Dict:
        url = f"{target.base_url}{path}"
        method = method.upper()
        params = {"q": payload} if method == "GET" else None
        data = {"input": payload} if method == "POST" else None

        try:
            response = httpx.request(
                method,
                url,
                params=params,
                data=data,
                timeout=5,
                follow_redirects=True,
            )
            return {
                "kind": "http",
                "url": url,
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "body": response.text[:4000],
                "elapsed_ms": int(response.elapsed.total_seconds() * 1000),
            }
        except Exception as exc:
            return {
                "kind": "http",
                "url": url,
                "status_code": 0,
                "headers": {},
                "body": str(exc),
                "elapsed_ms": 0,
            }

    def run_command(self, target: SandboxTarget, command: str) -> Dict:
        start = time.time()
        marker = f"sandbox-cmd::{target.target_id}"
        output = f"{marker}: {command}"
        return {
            "kind": "command",
            "command": command,
            "status_code": 0,
            "headers": {},
            "body": output,
            "elapsed_ms": int((time.time() - start) * 1000),
        }

    def read_output(self, observation: Dict) -> str:
        return observation.get("body", "")
