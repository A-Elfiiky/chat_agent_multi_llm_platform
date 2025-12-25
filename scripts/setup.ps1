# Check if Python is installed
if (-not (Get-Command "python" -ErrorAction SilentlyContinue)) {
    Write-Host "Error: Python is not installed or not in PATH." -ForegroundColor Red
    exit 1
}

# Create Virtual Environment
Write-Host "Creating virtual environment..."
python -m venv venv

# Activate Virtual Environment
Write-Host "Activating virtual environment..."
.\venv\Scripts\Activate.ps1

# Upgrade pip
Write-Host "Upgrading pip..."
python -m pip install --upgrade pip

# Install Dependencies
Write-Host "Installing dependencies..."
# We'll install all requirements from the services
$reqFiles = @(
    "services\ingestion-indexer\requirements.txt",
    "services\chat-orchestrator\requirements.txt",
    "services\gateway-api\requirements.txt"
)

foreach ($file in $reqFiles) {
    if (Test-Path $file) {
        Write-Host "Installing from $file..."
        pip install -r $file
    }
}

# Install additional dev tools
pip install requests

Write-Host "Setup complete!" -ForegroundColor Green
Write-Host "To start the platform, run: python run_local.py"
Write-Host "Note: You may need to activate the venv first: .\venv\Scripts\Activate"
