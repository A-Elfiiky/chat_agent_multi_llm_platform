# Copilot Platform - Management Scripts

## Available Scripts

### PowerShell Scripts (Recommended for Windows)

| Script | Description | Usage |
|--------|-------------|-------|
| `start.ps1` | Start all services | `.\start.ps1` |
| `stop.ps1` | Stop all services | `.\stop.ps1` |
| `restart.ps1` | Restart all services | `.\restart.ps1` |
| `status.ps1` | Check service status | `.\status.ps1` |

### Batch Scripts (Command Prompt)

| Script | Description | Usage |
|--------|-------------|-------|
| `start.bat` | Start all services | `start.bat` |
| `stop.bat` | Stop all services | `stop.bat` |

### Manual Control

| Command | Description |
|---------|-------------|
| `python run_local.py` | Start all services manually |
| `Ctrl+C` | Stop all services (when running manually) |

## Script Features

### start.ps1 / start.bat
- Checks if services are already running
- Starts all 5 microservices in the background
- Waits for initialization
- Verifies services are responding
- Displays service URLs and quick links

**Example Output:**
```
✅ Platform is running!

Services:
  • Gateway API        → http://localhost:8000
  • Chat Orchestrator  → http://localhost:8002
  • Ingestion Service  → http://localhost:8001
  • Voice Orchestrator → http://localhost:8004
  • Email Worker       → Running in background

Quick Access:
  • API Documentation  → http://localhost:8000/docs
  • Web Chat Widget    → clients/web-widget/index.html
  • Admin Console      → clients/admin-console/index.html
```

### stop.ps1 / stop.bat
- Finds all running platform processes
- Gracefully terminates services
- Reports number of processes stopped
- Cleans up background workers

**Example Output:**
```
✅ Stopped 5 process(es)

💡 To start again, run: .\start.ps1
```

### status.ps1
- Checks health of each service
- Verifies HTTP endpoints are responding
- Shows active Python processes
- Provides quick links if all services are running

**Example Output:**
```
Gateway API (Port 8000): ✅ Running
Ingestion Service (Port 8001): ✅ Running
Chat Orchestrator (Port 8002): ✅ Running
Voice Orchestrator (Port 8004): ✅ Running
Email Worker: ✅ Running

🎉 All services are operational!
```

### restart.ps1
- Combines stop and start operations
- Waits for cleanup between stop/start
- Useful for applying configuration changes

## Usage Examples

### Typical Workflow

**Start the platform:**
```powershell
.\start.ps1
```

**Check if everything is running:**
```powershell
.\status.ps1
```

**Make configuration changes, then restart:**
```powershell
# Edit config.yaml
.\restart.ps1
```

**Stop when done:**
```powershell
.\stop.ps1
```

### Development Workflow

**Quick iteration cycle:**
```powershell
# Make code changes
.\restart.ps1  # Apply changes

# Test
.\status.ps1   # Verify services restarted

# View logs in terminal or use Admin Console
```

### Troubleshooting

**Services won't start:**
```powershell
# Check what's running
.\status.ps1

# Force stop everything
.\stop.ps1

# Try starting again
.\start.ps1
```

**Port conflicts:**
```powershell
# Stop platform
.\stop.ps1

# Check for processes using ports
netstat -ano | findstr "8000 8001 8002 8004"

# Kill conflicting processes
taskkill /PID <process_id> /F

# Start platform
.\start.ps1
```

## Script Permissions

### PowerShell Execution Policy

If you get an error like `cannot be loaded because running scripts is disabled`, run this command as Administrator:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Or run scripts with:
```powershell
powershell -ExecutionPolicy Bypass -File .\start.ps1
```

### Batch Files

Batch files (`.bat`) typically don't require special permissions and will run directly in Command Prompt.

## Advanced Usage

### Running in Background (Detached)

The scripts automatically run services in the background. To see console output:

```bash
# Manual start with visible output
python run_local.py
```

### Custom Port Configuration

Edit `config.yaml` to change ports, then restart:
```powershell
# Edit config.yaml
.\restart.ps1
```

### Running Specific Services Only

Edit `run_local.py` and comment out services you don't need, then:
```powershell
python run_local.py
```

## Integration with VS Code

You can create VS Code tasks to run these scripts:

**`.vscode/tasks.json`:**
```json
{
    "version": "2.0.0",
    "tasks": [
        {
            "label": "Start Platform",
            "type": "shell",
            "command": ".\\start.ps1",
            "problemMatcher": []
        },
        {
            "label": "Stop Platform",
            "type": "shell",
            "command": ".\\stop.ps1",
            "problemMatcher": []
        },
        {
            "label": "Check Status",
            "type": "shell",
            "command": ".\\status.ps1",
            "problemMatcher": []
        }
    ]
}
```

Then use `Ctrl+Shift+P` → "Tasks: Run Task" → Select the task.

## Notes

- Scripts are designed for Windows environments
- For Linux/Mac, use `python run_local.py` directly or create equivalent shell scripts
- Background processes may continue running if stopped improperly - use `stop.ps1` to clean up
- Services take ~8-10 seconds to fully initialize

---

**For more information, see:**
- `GETTING_STARTED.md` - Full platform setup guide
- `MANUAL_TESTS.md` - API testing commands
- `STATUS.md` - Current platform status
