import docker
import tempfile
import os
import json
from typing import Dict, Optional
import structlog
from config import settings

log = structlog.get_logger()

SANDBOX_TIMEOUT = settings.SANDBOX_TIMEOUT_SECONDS


def run_in_sandbox(code: str, language: str = "python", payload: str = "") -> Dict:
    """
    Execute a code snippet in an isolated Docker container and return
    its stdout, stderr, exit code, and any anomalous behavior flags.
    """
    client = docker.from_env()

    with tempfile.TemporaryDirectory() as tmpdir:
        if language == "python":
            code_file = os.path.join(tmpdir, "target.py")
            run_cmd = ["python3", "/sandbox/target.py"]
        elif language in ("javascript", "js"):
            code_file = os.path.join(tmpdir, "target.js")
            run_cmd = ["node", "/sandbox/target.js"]
        else:
            return {"error": f"Language {language} not supported in sandbox", "anomalies": []}

        # Inject payload as environment variable
        wrapped_code = f"""
import os, sys, json, traceback
PAYLOAD = {repr(payload)}
try:
{chr(10).join('    ' + line for line in code.split(chr(10)))}
except Exception as e:
    print(json.dumps({{"error": str(e), "traceback": traceback.format_exc()}}), file=sys.stderr)
"""
        with open(code_file, "w") as f:
            f.write(wrapped_code if language == "python" else code)

        try:
            container = client.containers.run(
                image="python:3.11-slim",
                command=run_cmd,
                volumes={tmpdir: {"bind": "/sandbox", "mode": "ro"}},
                network_disabled=True,
                mem_limit="64m",
                cpu_quota=50000,
                remove=True,
                stdout=True,
                stderr=True,
                timeout=SANDBOX_TIMEOUT,
                security_opt=["no-new-privileges"],
            )
            output = container.decode("utf-8", errors="ignore") if isinstance(container, bytes) else str(container)
            return {
                "stdout": output[:2000],
                "stderr": "",
                "exit_code": 0,
                "anomalies": _detect_anomalies(output),
                "timed_out": False,
            }
        except docker.errors.ContainerError as e:
            stderr = e.stderr.decode("utf-8", errors="ignore") if e.stderr else ""
            return {
                "stdout": "",
                "stderr": stderr[:2000],
                "exit_code": e.exit_status,
                "anomalies": _detect_anomalies(stderr),
                "timed_out": False,
            }
        except Exception as e:
            log.warning("Sandbox execution failed", error=str(e))
            return {
                "stdout": "",
                "stderr": str(e),
                "exit_code": -1,
                "anomalies": [],
                "timed_out": "timeout" in str(e).lower(),
                "error": str(e),
            }


def _detect_anomalies(output: str) -> list:
    anomalies = []
    suspicious_patterns = [
        ("etc/passwd", "Potential path traversal — /etc/passwd accessed"),
        ("root:x:", "System file content leaked"),
        ("exec(", "Dynamic code execution detected"),
        ("__import__", "Dynamic import detected"),
        ("os.system", "Shell command execution detected"),
        ("socket.connect", "Unexpected network connection attempt"),
        ("open('/", "File system access outside expected paths"),
    ]
    for pattern, label in suspicious_patterns:
        if pattern.lower() in output.lower():
            anomalies.append(label)
    return anomalies
