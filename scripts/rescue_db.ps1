# DSP Class Web - Database Rescue Script
# This script creates a secure backup of your production Render database.

$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$BackupDir = Join-Path $PSScriptRoot "..\backups"
$BackupFile = Join-Path $BackupDir "production_rescue_$Timestamp.sql"

# 1. Ensure backup directory exists
if (-not (Test-Path $BackupDir)) {
    New-Item -ItemType Directory -Path $BackupDir | Out-Null
}

# 2. Check for pg_dump (with common fallbacks)
$PgDumpPath = "pg_dump"
if (-not (Get-Command $PgDumpPath -ErrorAction SilentlyContinue)) {
    $CommonPaths = @(
        "C:\Program Files\PostgreSQL\18\bin\pg_dump.exe",
        "C:\Program Files\PostgreSQL\17\bin\pg_dump.exe",
        "C:\Program Files\PostgreSQL\16\bin\pg_dump.exe"
    )
    foreach ($Path in $CommonPaths) {
        if (Test-Path $Path) {
            $PgDumpPath = "& `"$Path`""
            break
        }
    }
}

if (-not ($PgDumpPath -match "pg_dump")) {
    Write-Host "CRITICAL ERROR: pg_dump not found." -ForegroundColor Red
    Write-Host "Please install PostgreSQL Command Line Tools."
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
    Invoke-Expression "$PgDumpPath `"$DBUrl`" --no-owner --no-privileges --file=`"$BackupFile`""
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "SUCCESS! Your production data is safe." -ForegroundColor Green
        Write-Host "Backup location: $BackupFile"
    } else {
        Write-Host "ERROR: pg_dump failed with exit code $LASTEXITCODE" -ForegroundColor Red
    }
} catch {
    Write-Host "CRITICAL FAILURE: $_" -ForegroundColor Red
}
