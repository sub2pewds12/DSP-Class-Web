# 🗄️ Database Management

## 1. Storage Architecture
The project uses a **dual-storage** strategy:

| **Database** | SQLite (`db.sqlite3`) or `.env` | **Supabase PostgreSQL** (Tokyo Cluster) |
| **Media Files** | Cloudinary | Cloudinary (Persistent Cloud Storage) |
| **Static Files** | Django dev server | WhiteNoise (Compressed & Buffered) |

The database backend is selected automatically via `dj-database-url`. Locally, it defaults to SQLite unless a `DATABASE_URL` is found in your `.env` file.

**Supabase Production Connectivity**: Always use the **Transaction Pooler** (Port 6543) with `?pgbouncer=true`. This ensures compatibility with IPv4-only networks (like Render) and provides high-performance connection management. 
- **Pool Management**: In `settings.py`, ensure `CONN_MAX_AGE` is set appropriately for your environment. For serverless or high-concurrency scenarios (Render/Supabase), `CONN_MAX_AGE = 0` is recommended to prevent idle connection buildup.
- **SSL Configuration**: Ensure `sslmode=require` is active to protect data in transit.

**Cloudinary** handles all user-uploaded files (assignment instructions, team submissions, class documents) so they persist across deployments regardless of ephemeral hosting.

## 2. Viewing Data & Schema
- **Django Admin** (Recommended): Visit `/admin/` while the server is running.
- **Inspect Schema**: 
  ```powershell
  .\.venv\Scripts\python.exe manage.py sqlmigrate teams 0001
  ```
- **Inspect Models**:
  ```powershell
  .\.venv\Scripts\python.exe manage.py inspectdb
  ```

## 3. Understanding Migrations
Whenever you change `models.py`, you must sync the database:
1.  **Stage changes**: `.\.venv\Scripts\python.exe manage.py makemigrations` (Creates a blueprint file in `teams/migrations/`).
2.  **Apply changes**: `.\.venv\Scripts\python.exe manage.py migrate` (Actually modifies the database).

## 4. Seed Data
Populate the database with realistic test data for development:
```powershell
.\.venv\Scripts\python.exe manage.py seed_dsp
```
Remove only seeded test data while preserving real accounts:
```powershell
.\.venv\Scripts\python.exe manage.py seed_dsp --clear
```

## 5. Database Reset (Emergency Only)
If your database gets corrupted or you want to start fresh:
1.  Delete `db.sqlite3` (local only — for production, drop and recreate the PostgreSQL database).
2.  Delete all files in `teams/migrations/` (except `__init__.py`).
3.  Run `makemigrations` and `migrate`.

> [!WARNING]
> A database reset will permanently delete all user accounts, teams, submissions, and grades.

## 6. Data Models Overview
| Model | Purpose |
| :--- | :--- |
| `CustomUser` | Extended user with role field (Student/Lecturer/Dev) |
| `SystemSettings` | Singleton config for max team size |
| `Team` | Team with name, project details, and leader reference |
| `Student` | Student profile linked to a user and an optional team |
| `Lecturer` | Lecturer profile with department field |
| `Developer` | Developer profile with access level |
| `ClassDocument` | Uploaded class materials (PDFs, etc.) |
| `Assignment` | Tasks with deadlines and grade-release control |
| `TeamSubmission` | Team uploads linked to assignments, with grade and feedback |
## 7. Row Level Security (RLS) & Cloaking
To protect student data, we employ a "Database Cloaking" strategy via Supabase RLS:
- **Locked by Default**: All tables have RLS enabled, meaning direct API access is denied.
- **Backend Only**: Only the server-side Django service (authenticated via PostgreSQL) can read and write data.
- **Verification**: New tables must have RLS enabled via the Supabase SQL Editor:
  ```sql
  ALTER TABLE public.new_table ENABLE ROW LEVEL SECURITY;
  ```
