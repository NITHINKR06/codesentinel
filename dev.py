import subprocess
import time
import sys

def main():
    print("Starting background services (Redis, DB)...")
    subprocess.run(["docker", "compose", "up", "-d", "redis", "db"], check=True)

    commands = [
        {
            "name": "Celery",
            "cmd": "cd backend && source /home/nithin/Documents/codesentinel/backend/venv/bin/activate.fish && celery -A workers.celery_app worker --loglevel=info --concurrency=1"
        },
        {
            "name": "Backend",
            "cmd": "cd backend && python3 -m venv venv && source /home/nithin/Documents/codesentinel/backend/venv/bin/activate.fish && uvicorn main:app --reload --port 8001"
        },
        {
            "name": "Frontend",
            "cmd": "cd frontend && NEXT_PUBLIC_API_URL=http://localhost:8001 NEXT_PUBLIC_WS_URL=ws://localhost:8001 yarn dev"
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
