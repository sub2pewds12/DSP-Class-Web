# 🗄️ Database Management

## 1. Storage Architecture
The project uses a **dual-storage** strategy:

| Layer | Local Development | Production (Render) |
| :--- | :--- | :--- |
| **Database** | SQLite (`db.sqlite3`) | PostgreSQL (via `DATABASE_URL`) |
| **Media Files** | Cloudinary | Cloudinary |
| **Static Files** | Django dev server | WhiteNoise (compressed) |

The database backend is selected automatically via `dj-database-url`. Locally, it defaults to SQLite. In production, set the `DATABASE_URL` environment variable to your PostgreSQL connection string.

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
