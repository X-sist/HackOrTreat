<#
.SYNOPSIS
  Environment setup helper for HackOrTreat Receiver (Laptop 2 / CS2).
  Creates receiver/.venv, checks Node 24 runtime, and runs test verification.
#>

$ErrorActionPreference = "Stop"

Write-Host "=======================================================" -ForegroundColor Cyan
Write-Host "  HACKORTREAT — RECEIVER ENVIRONMENT SETUP (@Xsist)    " -ForegroundColor Cyan
Write-Host "=======================================================" -ForegroundColor Cyan

# 1. Check Python
Write-Host "`n[1/4] Checking Python..." -ForegroundColor Yellow
$pyVersion = python --version 2>&1
Write-Host "Found: $pyVersion" -ForegroundColor Green

# 2. Setup Python Virtual Environment (.venv)
Write-Host "`n[2/4] Setting up Python virtual environment in receiver/.venv..." -ForegroundColor Yellow
$venvPath = Join-Path $PSScriptRoot ".venv"
if (-not (Test-Path $venvPath)) {
    Write-Host "Creating venv at $venvPath..." -ForegroundColor Gray
    python -m venv $venvPath
    Write-Host "Virtual environment created." -ForegroundColor Green
} else {
    Write-Host "Virtual environment already exists at $venvPath." -ForegroundColor Green
}

# 3. Check Node.js and npm
Write-Host "`n[3/4] Checking Node.js and npm baseline..." -ForegroundColor Yellow
$nodeVersion = node --version 2>&1
$npmVersion = npm --version 2>&1
Write-Host "Node: $nodeVersion (Baseline: 24.15.0)" -ForegroundColor Green
Write-Host "npm:  v$npmVersion (Baseline: 11.12.1)" -ForegroundColor Green

# 4. Run Receiver StreamParser Tests
Write-Host "`n[4/4] Running StreamParser tests and shared fixture replays..." -ForegroundColor Yellow
$testScript = Join-Path $PSScriptRoot "tests/test_stream_parser.mjs"
node $testScript

Write-Host "`n=======================================================" -ForegroundColor Green
Write-Host "  ENVIRONMENT READY FOR HACKATHON PERFORMANCE!         " -ForegroundColor Green
Write-Host "=======================================================" -ForegroundColor Green
Write-Host "`nTo activate your Python virtual environment, run:" -ForegroundColor White
Write-Host "  .\receiver\.venv\Scripts\Activate.ps1`n" -ForegroundColor Cyan
Write-Host "To launch the Ouija Spirit Plane Web UI, run:" -ForegroundColor White
Write-Host "  node receiver/src/server.mjs" -ForegroundColor Cyan
Write-Host "  (Open http://localhost:3000 in your browser)`n" -ForegroundColor Gray
Write-Host "To launch the Plain-Text CLI, run:" -ForegroundColor White
Write-Host "  node receiver/src/cli.mjs --simulate`n" -ForegroundColor Cyan
