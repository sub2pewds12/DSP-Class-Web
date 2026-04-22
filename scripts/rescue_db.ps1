# DSP Class Web - Database Rescue Script
# This script creates a secure backup of your production Render database.

$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$BackupDir = Join-Path $PSScriptRoot "..\backups"
$BackupFile = Join-Path $BackupDir "production_rescue_$Timestamp.sql"

# 1. Ensure backup directory exists
if (-not (Test-Path $BackupDir)) {
    New-Item -ItemType Directory -Path $BackupDir | Out-Null
}

# 2. Check for pg_dump
if (-not (Get-Command pg_dump -ErrorAction SilentlyContinue)) {
    Write-Host "CRITICAL ERROR: pg_dump not found in your PATH." -ForegroundColor Red
    Write-Host "Please install PostgreSQL Command Line Tools or add them to your PATH."
    Write-Host "Download link: https://www.postgresql.org/download/windows/"
    exit
}

# 3. Get Credentials
$DBUrl = [System.Environment]::GetEnvironmentVariable("DATABASE_URL")
if (-not $DBUrl) {
    Write-Host "DATABASE_URL environment variable is not set." -ForegroundColor Yellow
    $DBUrl = Read-Host "Please paste your Render External Database URL"
}

# 4. Perform Backup
Write-Host "Rescue in progress... saving to $BackupFile" -ForegroundColor Cyan
try {
    # Extracting connection details from URL if possible, or passing URL directly
    # pg_dump can take a connection string as the first argument
    & pg_dump $DBUrl --no-owner --no-privileges --file=$BackupFile
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "SUCCESS! Your production data is safe." -ForegroundColor Green
        Write-Host "Backup location: $BackupFile"
    } else {
        Write-Host "ERROR: pg_dump failed with exit code $LASTEXITCODE" -ForegroundColor Red
    }
} catch {
    Write-Host "CRITICAL FAILURE: $_" -ForegroundColor Red
}
