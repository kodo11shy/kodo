$ErrorActionPreference = "Stop"

$BackendRoot = Split-Path -Parent $PSScriptRoot
Set-Location $BackendRoot

if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
  python -m venv .venv
}

.\.venv\Scripts\python.exe -c "import fastapi, uvicorn, sqlalchemy" 2>$null
if ($LASTEXITCODE -ne 0) {
  .\.venv\Scripts\python.exe -m pip install -r requirements.txt
}

$env:DATABASE_URL = "sqlite:///./tuoban_dev.db"
$env:TOKEN_SECRET = "dev-test-secret"
$env:AUTO_CREATE_TABLES = "true"

$Port = if ($env:PORT) { [int]$env:PORT } else { 8000 }

function Stop-PortListener {
  param([int]$Port)

  $processIds = @()
  if (Get-Command Get-NetTCPConnection -ErrorAction SilentlyContinue) {
    $processIds = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue |
      Select-Object -ExpandProperty OwningProcess -Unique
  }

  if (-not $processIds -or $processIds.Count -eq 0) {
    $lines = netstat -ano | Select-String ":$Port\s+.*LISTENING"
    $processIds = $lines | ForEach-Object {
      $parts = ($_ -split "\s+") | Where-Object { $_ }
      if ($parts.Count -gt 0) { [int]$parts[-1] }
    } | Select-Object -Unique
  }

  foreach ($processId in $processIds) {
    if ($processId -and $processId -ne $PID) {
      try {
        $process = Get-Process -Id $processId -ErrorAction Stop
        Write-Host "Stopping existing listener on port ${Port}: PID $processId ($($process.ProcessName))"
        Stop-Process -Id $processId -Force -ErrorAction Stop
      } catch {
        Write-Host "Could not stop PID $processId on port ${Port}: $($_.Exception.Message)"
      }
    }
  }

  Start-Sleep -Milliseconds 800
}

function Test-PortBusy {
  param([int]$Port)
  $connection = $null
  if (Get-Command Get-NetTCPConnection -ErrorAction SilentlyContinue) {
    $connection = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
  }
  if ($connection) { return $true }
  return [bool](netstat -ano | Select-String ":$Port\s+.*LISTENING")
}

Stop-PortListener -Port $Port
if (Test-PortBusy -Port $Port) {
  $fallbackPort = $Port + 1
  Write-Host "Port $Port is still busy. Falling back to port $fallbackPort."
  $Port = $fallbackPort
  Stop-PortListener -Port $Port
}

Write-Host "Starting backend on http://0.0.0.0:$Port"
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port $Port --reload
