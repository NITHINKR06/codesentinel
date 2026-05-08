import subprocess
import time
import sys
import socket
import os
import shutil
from pathlib import Path
import urllib.request
import urllib.error


ROOT = Path(__file__).resolve().parent
BACKEND_DIR = ROOT / "backend"
BACKEND_VENV = BACKEND_DIR / "venv"
BACKEND_PYTHON = BACKEND_VENV / "bin" / "python"
BACKEND_REQUIREMENTS = BACKEND_DIR / "requirements.txt"
BACKEND_SETUP_STAMP = BACKEND_VENV / ".requirements-installed"

FRONTEND_DIR = ROOT / "frontend"
FRONTEND_SETUP_STAMP = FRONTEND_DIR / ".node_modules-installed"
FRONTEND_BUILD_DIR = FRONTEND_DIR / ".next"


def _is_port_free(port: int, host: str = "127.0.0.1") -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.bind((host, port))
            return True
        except OSError:
            return False


def _pick_free_port(preferred: int, host: str = "127.0.0.1", max_tries: int = 20) -> int:
    for offset in range(max_tries):
        candidate = preferred + offset
        if _is_port_free(candidate, host=host):
            return candidate
    raise RuntimeError(f"Could not find a free port starting at {preferred}")


def _wait_for_port(port: int, host: str = "127.0.0.1", timeout: int = 60) -> None:
    """Wait for a service to be ready on a port by attempting to connect."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                s.connect((host, port))
                return  # Connection successful, service is ready
        except (OSError, socket.timeout):
            time.sleep(0.5)
    raise RuntimeError(f"Timed out waiting for {host}:{port} to become ready")


def _wait_for_backend_ready(port: int, host: str = "127.0.0.1", timeout: int = 60) -> None:
    """Wait for the backend API to be fully ready by checking the health endpoint."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            url = f"http://{host}:{port}/health"
            with urllib.request.urlopen(url, timeout=2) as response:
                if response.status == 200:
                    return  # Backend is fully ready
        except (urllib.error.URLError, urllib.error.HTTPError, OSError, socket.timeout):
            time.sleep(0.5)
    raise RuntimeError(f"Timed out waiting for backend at {host}:{port} to be ready")


def _run_checked(command: list[str], cwd: Path) -> None:
    subprocess.run(command, cwd=cwd, check=True)


def _is_stale(marker: Path, dependency: Path) -> bool:
    return not marker.exists() or marker.stat().st_mtime < dependency.stat().st_mtime


def _ensure_backend_environment() -> None:
    if not BACKEND_PYTHON.exists():
        print("Creating backend virtual environment...")
        _run_checked([sys.executable, "-m", "venv", str(BACKEND_VENV)], cwd=BACKEND_DIR)

    if _is_stale(BACKEND_SETUP_STAMP, BACKEND_REQUIREMENTS):
        print("Installing backend Python dependencies...")
        _run_checked([str(BACKEND_PYTHON), "-m", "pip", "install", "-r", str(BACKEND_REQUIREMENTS)], cwd=BACKEND_DIR)
        BACKEND_SETUP_STAMP.touch()


def _ensure_frontend_environment() -> None:
    if FRONTEND_BUILD_DIR.exists():
        print("Removing stale frontend build cache...")
        shutil.rmtree(FRONTEND_BUILD_DIR)

    dependency_files = [FRONTEND_DIR / "package.json", FRONTEND_DIR / "yarn.lock"]
    marker_is_stale = not FRONTEND_SETUP_STAMP.exists() or any(
        FRONTEND_SETUP_STAMP.stat().st_mtime < dependency_file.stat().st_mtime
        for dependency_file in dependency_files
        if dependency_file.exists()
    )

    if marker_is_stale:
        print("Installing frontend dependencies...")
        if shutil.which("yarn"):
            _run_checked(["yarn", "install"], cwd=FRONTEND_DIR)
        else:
            _run_checked(["npm", "install"], cwd=FRONTEND_DIR)
        FRONTEND_SETUP_STAMP.touch()

def main():
    print("Starting background services (Redis, DB)...")
    subprocess.run(["docker", "compose", "up", "-d", "redis", "db"], cwd=ROOT, check=True)

    _ensure_backend_environment()
    _ensure_frontend_environment()

    backend_port = _pick_free_port(8001)
    if backend_port != 8001:
        print(f"Port 8001 is busy; using backend port {backend_port} instead")

    common_backend_env = os.environ.copy()
    common_backend_env["CODESENTINEL_SANDBOX_NETWORK"] = "host"

    frontend_env = os.environ.copy()
    frontend_env["NEXT_PUBLIC_API_URL"] = f"http://localhost:{backend_port}"
    frontend_env["NEXT_PUBLIC_WS_URL"] = f"ws://localhost:{backend_port}"

    commands = [
        {
            "name": "Celery",
            "cmd": [str(BACKEND_PYTHON), "-m", "celery", "-A", "workers.celery_app", "worker", "--loglevel=info", "--concurrency=1"],
            "cwd": BACKEND_DIR,
            "env": common_backend_env,
        },
        {
            "name": "Backend",
            "cmd": [str(BACKEND_PYTHON), "-m", "uvicorn", "main:app", "--reload", "--port", str(backend_port)],
            "cwd": BACKEND_DIR,
            "env": common_backend_env,
        },
        {
            "name": "Frontend",
            "cmd": ["yarn", "dev"] if (FRONTEND_DIR / "yarn.lock").exists() and shutil.which("yarn") else ["npm", "run", "dev"],
            "cwd": FRONTEND_DIR,
            "env": frontend_env,
        }
    ]

    processes = []
    
    # Start Celery and Backend first
    for c in commands[:2]:
        print(f"Starting {c['name']}...")
        p = subprocess.Popen(c["cmd"], cwd=c["cwd"], env=c["env"])
        processes.append((c['name'], p))

    print(f"Waiting for backend on port {backend_port} to be fully ready...")
    _wait_for_backend_ready(backend_port)
    print(f"Backend is ready on port {backend_port}")

    # Now start Frontend with correct environment variables
    frontend_command = commands[2]
    print(f"Starting {frontend_command['name']}...")
    frontend_process = subprocess.Popen(frontend_command["cmd"], cwd=frontend_command["cwd"], env=frontend_command["env"])
    processes.append((frontend_command['name'], frontend_process))

    print("\nAll services started! Press Ctrl+C to stop.\n")

    try:
        # Keep the main thread alive while background processes run
        while len(processes) > 0:
            time.sleep(1)
            
            # check if anything crashed unexpectedly
            for name, p in processes[:]:
                if p.poll() is not None:
                    print(f"[{name}] exited unexpectedly with code {p.returncode}")
                    processes.remove((name, p))
                    print(f"Shutting down all remaining services because {name} failed...")
                    for oname, op in processes:
                        print(f"Stopping {oname}...")
                        op.terminate()
                    sys.exit(1)
                    
    except KeyboardInterrupt:
        print("\n\nShutting down all services...")
        
        # Terminate all gracefully
        for name, p in processes:
            print(f"Stopping {name}...")
            p.terminate()
            
        # Wait for all to finish
        for name, p in processes:
            p.wait()
            
        print("All services stopped.")
        sys.exit(0)

if __name__ == "__main__":
    main()
