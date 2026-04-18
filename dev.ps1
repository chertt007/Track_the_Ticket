# Dev launcher: starts frontend and API, cleans up on exit.
# Usage: .\dev.ps1

$ErrorActionPreference = "Stop"

function Kill-Port($port) {
    $pids = netstat -ano | Select-String ":$port\s" | ForEach-Object {
        ($_ -split '\s+')[-1]
    } | Select-Object -Unique
    foreach ($p in $pids) {
        if ($p -match '^\d+$' -and $p -ne '0') {
            try { taskkill /F /T /PID $p 2>$null } catch {}
        }
    }
}

Write-Host "Cleaning up ports 5173 and 8000..." -ForegroundColor Cyan
Kill-Port 5173
Kill-Port 8000
Start-Sleep -Milliseconds 500

$root = $PSScriptRoot

# Use the project venv python explicitly — system python may lack playwright etc.
$venvPython = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Write-Host "ERROR: venv python not found at $venvPython" -ForegroundColor Red
    Write-Host "Create the venv first: python -m venv .venv && .\.venv\Scripts\activate && pip install -r services\requirements.txt" -ForegroundColor Yellow
    exit 1
}

Write-Host "Starting API (port 8000)..." -ForegroundColor Green
$api = Start-Process -FilePath $venvPython `
    -ArgumentList "run.py" `
    -WorkingDirectory "$root\services" `
    -PassThru -NoNewWindow

Write-Host "Starting Frontend (port 5173)..." -ForegroundColor Green
$fe = Start-Process -FilePath "cmd" `
    -ArgumentList "/C npm run dev" `
    -WorkingDirectory "$root\frontend" `
    -PassThru -NoNewWindow

Write-Host ""
Write-Host "Running. Press Ctrl+C to stop all." -ForegroundColor Yellow
Write-Host "  Frontend: http://localhost:5173" -ForegroundColor White
Write-Host "  API:      http://localhost:8000" -ForegroundColor White
Write-Host ""

try {
    while ($true) { Start-Sleep -Seconds 1 }
} finally {
    Write-Host "`nStopping..." -ForegroundColor Cyan
    if ($api -and !$api.HasExited) {
        taskkill /F /T /PID $api.Id 2>$null
    }
    if ($fe -and !$fe.HasExited) {
        taskkill /F /T /PID $fe.Id 2>$null
    }
    # Also clean up by port in case of orphans
    Kill-Port 5173
    Kill-Port 8000
    Write-Host "Done." -ForegroundColor Green
}
