import subprocess
import sys
import time
import os
import socket
import json
from pathlib import Path

# Disable SSL verification for HuggingFace downloads (local dev workaround)
os.environ['CURL_CA_BUNDLE'] = ''
os.environ['REQUESTS_CA_BUNDLE'] = ''

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_CANDIDATES = [BASE_DIR / ".env", BASE_DIR / ".env.local", BASE_DIR / ".env.example"]
SERVICE_REGISTRY_FILE = str(BASE_DIR / ".service-pids.json")
service_registry = {"services": []}


def load_env_from_file():
    """Populate os.environ from the first env file we find."""
    for env_path in ENV_CANDIDATES:
        if env_path.exists():
            try:
                with open(env_path, "r", encoding="utf-8") as env_file:
                    for raw_line in env_file:
                        line = raw_line.strip()
                        if not line or line.startswith("#"):
                            continue
                        if "=" not in line:
                            continue
                        key, value = line.split("=", 1)
                        clean_value = value.split(" #", 1)[0].strip().strip('"').strip("'")
                        os.environ[key.strip()] = clean_value
                print(f"Loaded environment variables from {env_path.name}")
                return env_path
            except OSError as exc:
                print(f"[WARN] Unable to read {env_path}: {exc}")
    print("[WARN] No .env file found. Falling back to existing environment variables.")
    return None


ACTIVE_ENV_FILE = load_env_from_file()


def _write_service_registry():
    """Persist the running service metadata so stop.ps1 can terminate them."""
    try:
        with open(SERVICE_REGISTRY_FILE, "w", encoding="utf-8") as f:
            json.dump(service_registry, f, indent=2)
    except OSError as exc:
        print(f"[WARN] Could not write service registry: {exc}")


def register_service(name, command, pid, port=None):
    entry = {
        "name": name,
        "pid": pid,
        "command": command,
        "port": port,
        "started_at": time.time()
    }
    service_registry["services"] = [svc for svc in service_registry["services"] if svc.get("name") != name]
    service_registry["services"].append(entry)
    _write_service_registry()


def clear_service_registry():
    service_registry["services"] = []
    try:
        if os.path.exists(SERVICE_REGISTRY_FILE):
            os.remove(SERVICE_REGISTRY_FILE)
    except OSError:
        pass

def ensure_port_available(port, service_name):
    """Ensure the given TCP port is free before starting a service."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind(('0.0.0.0', port))
        except OSError:
            print(f"\n[ERROR] {service_name} cannot start because port {port} is already in use.")
            print("        Run .\\stop.ps1 (or terminate the existing uvicorn/python process) and try again.\n")
            raise SystemExit(1)


def build_uvicorn_command(app_path: str, port: int) -> list:
    return [
        sys.executable,
        "-m",
        "uvicorn",
        app_path,
        "--host",
        "0.0.0.0",
        "--port",
        str(port)
    ]


def run_service(name, command_args, port=None):
    print(f"Starting {name}...")
    if port:
        print(f"  -> Listening on port {port}")
    
    process = subprocess.Popen(
        command_args,
        cwd=str(BASE_DIR),
        env=os.environ.copy()  # Pass the modified environment to child processes
    )
    command_display = " ".join(command_args)
    register_service(name, command_display, process.pid, port)
    return process

def main():
    services = []
    try:
        clear_service_registry()
        # 0. Initialize Database
        print("Initializing Database...")
        subprocess.run(
            "python services/shared/init_db.py",
            shell=True,
            check=True,
            env=os.environ.copy()  # Pass env to init_db too
        )

        # 1. Ingestion Service (Port 8001)
        ensure_port_available(8001, "Ingestion Service")
        services.append(run_service(
            "Ingestion Service",
            build_uvicorn_command("services.ingestion-indexer.main:app", 8001),
            8001
        ))
        
        # Wait a bit for ingestion to start
        time.sleep(2)

        # 2. Chat Orchestrator (Port 8002)
        ensure_port_available(8002, "Chat Orchestrator")
        services.append(run_service(
            "Chat Orchestrator",
            build_uvicorn_command("services.chat-orchestrator.main:app", 8002),
            8002
        ))

        # 3. Gateway API (Port 8000)
        ensure_port_available(8000, "Gateway API")
        services.append(run_service(
            "Gateway API",
            build_uvicorn_command("services.gateway-api.main:app", 8000),
            8000
        ))

        # 4. Voice Orchestrator (Port 8004)
        ensure_port_available(8004, "Voice Orchestrator")
        services.append(run_service(
            "Voice Orchestrator",
            build_uvicorn_command("services.voice-orchestrator.main:app", 8004),
            8004
        ))

        # 5. Email Responder (Worker)
        print("Starting Email Responder (Worker)...")
        services.append(run_service(
            "Email Responder",
            [sys.executable, "services/email-responder/worker.py"]
        ))

        print("\nAll services started. Press Ctrl+C to stop.")

        print("Web Widget available at: clients/web-widget/index.html")
        
        # Keep main thread alive
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nStopping services...")
        for p in services:
            p.terminate()
        sys.exit(0)

if __name__ == "__main__":
    main()
