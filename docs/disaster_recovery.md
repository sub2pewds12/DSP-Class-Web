# Disaster Recovery Guide

This document outlines the procedures for backing up and restoring the DSP Class Web database, especially in light of the Render Free Tier expiration.

## Emergency Backup (Manual)

If you need to pull data right now, use the provided rescue script.

### Prerequisites
1. **PostgreSQL Tools**: Ensure `pg_dump` is installed and in your PATH.
2. **Database URL**: You will need the **External Database URL** from your Render Dashboard (under the 'Connect' button).

### Instructions
1. Open PowerShell.
2. Navigate to the project root.
3. Run the rescue script:
   ```powershell
   .\scripts\rescue_db.ps1
   ```
4. When prompted, paste your **External Database URL**.
5. The backup will be saved to the `backups/` directory as `production_rescue_YYYYMMDD_HHMMSS.sql`.

## Database Restoration

To restore your data to a NEW provider (like Supabase or Neon):

1. Set up a new database on the provider.
2. Get the new connection string.
3. Run the following command from your terminal:
   ```bash
   psql "NEW_DATABASE_URL" -f backups/production_rescue_XXXX.sql
   ```

## Critical Dates
- **2026-05-11**: Render database expiration date. Data must be migrated before this day.
