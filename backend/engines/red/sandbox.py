from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional
import os
import shutil
import subprocess
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
        self.service_map = {
            "sqli": "demo-sqli",
            "xss": "demo-xss",
            "path_traversal": "demo-path",
            "ssrf": "demo-ssrf",
            "rce": "demo-rce",
        }
        # Ports exposed in docker-compose.yml for local development.
        self.local_port_map = {
            "demo-sqli": 8101,
            "demo-xss": 8102,
            "demo-path": 8103,
            "demo-ssrf": 8104,
            "demo-rce": 8105,
        }
        self.compose_root = Path(__file__).resolve().parents[3]

    def _running_in_container(self) -> bool:
        """Best-effort detection of running inside a container.

        We avoid relying only on `/.dockerenv` because some environments may
        expose it unexpectedly. Checking cgroups makes this more reliable.
        """
        try:
            if Path("/.dockerenv").exists():
                # Confirm with cgroups if possible.
                try:
                    cgroup = Path("/proc/1/cgroup").read_text(encoding="utf-8", errors="ignore")
                    lowered = cgroup.lower()
                    if any(token in lowered for token in ("docker", "kubepods", "containerd", "libpod")):
                        return True
                except Exception:
                    return True
                return False

            cgroup = Path("/proc/1/cgroup").read_text(encoding="utf-8", errors="ignore")
            lowered = cgroup.lower()
            return any(token in lowered for token in ("docker", "kubepods", "containerd", "libpod"))
        except Exception:
            return False

    def _base_url_for_service(self, service_name: str) -> str:
        # Override:
        # - CODESENTINEL_SANDBOX_NETWORK=host  -> always use localhost port mapping
        # - CODESENTINEL_SANDBOX_NETWORK=docker -> always use Docker DNS
        network = (os.getenv("CODESENTINEL_SANDBOX_NETWORK") or "").strip().lower()
        if network == "docker":
            return f"http://{service_name}:5000"
        if network == "host":
            port = self.local_port_map.get(service_name)
            if port:
                return f"http://127.0.0.1:{port}"

        if self._running_in_container():
            return f"http://{service_name}:5000"
        port = self.local_port_map.get(service_name)
        if port:
            return f"http://127.0.0.1:{port}"
        return f"http://127.0.0.1:5000"

    def _probe_ready(self, base_url: str) -> bool:
        try:
            response = httpx.get(f"{base_url}/", timeout=2)
            return response.status_code == 200
        except Exception:
            return False

    def spin_target(self, vuln_type: str, container_name: Optional[str] = None) -> SandboxTarget:
        target_id = str(uuid.uuid4())
        service_name = container_name or self.service_map.get(vuln_type, f"demo-{vuln_type}")
        base_url = self._base_url_for_service(service_name)

        ready = False
        startup_note = "Sandbox target registered."
        if shutil.which("docker"):
            try:
                subprocess.run(
                    ["docker", "compose", "up", "-d", service_name],
                    cwd=str(self.compose_root),
                    check=True,
                    capture_output=True,
                    text=True,
                )
                # Give the container a brief moment to start, then probe readiness.
                time.sleep(0.5)
                ready = self._probe_ready(base_url)
                startup_note = (
                    f"Started compose service {service_name}."
                    if ready
                    else f"Started compose service {service_name}, but it did not become ready at {base_url}."
                )
            except Exception as exc:
                startup_note = f"Could not start compose service {service_name}: {exc}"
        else:
            startup_note = f"Docker not available; expected service {service_name} at {base_url}."

        if not ready:
            # If docker wasn't available or readiness probe failed, don't block the run.
            # The oracle will report INCONCLUSIVE with the error body.
            ready = self._probe_ready(base_url)

        target = SandboxTarget(
            target_id=target_id,
            vuln_type=vuln_type,
            base_url=base_url,
            container_name=service_name,
            ready=ready,
            notes=startup_note,
        )
        log.info("Sandbox target prepared", vuln=vuln_type, target_id=target_id, base_url=base_url, service=service_name)
        return target

    def send_request(self, target: SandboxTarget, method: str, path: str, payload: str, param_name: Optional[str] = None) -> Dict:
        url = f"{target.base_url}{path}"
        method = method.upper()
        key = param_name or self._default_param_for_path(path)
        params = {key: payload} if method == "GET" else None
        data = {key: payload} if method == "POST" else None

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

    def _default_param_for_path(self, path: str) -> str:
        path = path.lower()
        if "download" in path:
            return "file"
        if "fetch" in path:
            return "url"
        if "run" in path:
            return "cmd"
        return "q"
