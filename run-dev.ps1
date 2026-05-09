param(
  [switch]$BackendOnly
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendDir = Join-Path $root 'backend'
$frontendDir = Join-Path $root 'frontend'
$backendVenv = Join-Path $backendDir '.venv'
$backendPython = Join-Path $backendVenv 'Scripts\python.exe'
$backendUvicorn = Join-Path $backendVenv 'Scripts\uvicorn.exe'

function Ensure-BackendVenv {
  if (-not (Test-Path $backendPython)) {
    Write-Host 'Backend venv chua co. Dang tao .venv...' -ForegroundColor Yellow
    Push-Location $backendDir
    try {
      py -3 -m venv .venv
    }
    finally {
      Pop-Location
    }
  }
}

Ensure-BackendVenv

if (-not (Test-Path $backendPython)) {
  throw 'Khong tim thay Python trong backend\\.venv. Hay cai Python hoac tao lai virtual environment.'
}

if (-not (Test-Path $backendUvicorn)) {
  Write-Host 'Dang cai backend dependencies...' -ForegroundColor Yellow
  Push-Location $backendDir
  try {
    & $backendPython -m pip install --upgrade pip
    & $backendPython -m pip install --only-binary=:all: -r requirements.txt
  }
  finally {
    Pop-Location
  }
}

Write-Host 'Khoi dong backend...' -ForegroundColor Cyan
$backendProcess = Start-Process -FilePath $backendPython -ArgumentList @('-m', 'uvicorn', 'main:app', '--host', '0.0.0.0', '--port', '8000', '--reload') -WorkingDirectory $backendDir -PassThru

if ($BackendOnly) {
  Write-Host "Backend dang chay tai http://localhost:8000 (PID $($backendProcess.Id))" -ForegroundColor Green
  Wait-Process -Id $backendProcess.Id
  exit
}

Write-Host 'Khoi dong frontend...' -ForegroundColor Cyan
$npmCmd = Join-Path $env:ProgramFiles 'nodejs\npm.cmd'
if (-not (Test-Path $npmCmd)) {
  $npmCmd = 'npm.cmd'
}
$frontendProcess = Start-Process -FilePath $npmCmd -ArgumentList @('start') -WorkingDirectory $frontendDir -PassThru

Write-Host "Backend:  http://localhost:8000" -ForegroundColor Green
Write-Host "Frontend: http://localhost:3000" -ForegroundColor Green
Write-Host 'Nhan Ctrl+C trong terminal nay se khong tu dong tat 2 process. Hãy dong 2 cua so hoac dung Stop-Process neu can.' -ForegroundColor Yellow

Wait-Process -Id $backendProcess.Id, $frontendProcess.Id
