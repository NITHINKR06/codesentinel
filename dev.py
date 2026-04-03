import subprocess
import time
import sys
import socket


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

def main():
    print("Starting background services (Redis, DB)...")
    subprocess.run(["docker", "compose", "up", "-d", "redis", "db"], check=True)

    backend_port = _pick_free_port(8001)
    if backend_port != 8001:
        print(f"Port 8001 is busy; using backend port {backend_port} instead")

    commands = [
        {
            "name": "Celery",
            "cmd": "cd backend && source /home/nithin/Documents/codesentinel/backend/venv/bin/activate.fish && celery -A workers.celery_app worker --loglevel=info --concurrency=1"
        },
        {
            "name": "Backend",
            "cmd": f"cd backend && python3 -m venv venv && source /home/nithin/Documents/codesentinel/backend/venv/bin/activate.fish && uvicorn main:app --reload --port {backend_port}"
        },
        {
            "name": "Frontend",
            "cmd": f"cd frontend && NEXT_PUBLIC_API_URL=http://localhost:{backend_port} NEXT_PUBLIC_WS_URL=ws://localhost:{backend_port} yarn dev"
        }
    ]

    processes = []
    
    for c in commands:
        print(f"Starting {c['name']}...")
        # Spawning processes using fish as requested
        p = subprocess.Popen(['fish', '-c', c['cmd']])
        processes.append((c['name'], p))

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
