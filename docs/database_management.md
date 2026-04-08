# 🗄️ Database Management

The site uses **SQLite** for local development and remains SQLite-compatible for Docker deployments.

## 1. Viewing Data & Schema
As discussed, there are several ways to inspect your data:
- **Django Admin** (Recommended): Visit `/admin/` while the server is running.
- **Inspect Schema**: 
  ```powershell
  .\.venv\Scripts\python.exe manage.py sqlmigrate teams 0001
  ```
- **Inspect Models**:
  ```powershell
  .\.venv\Scripts\python.exe manage.py inspectdb
  ```

## 2. Understanding Migrations
Whenever you change `models.py`, you must sync the database:
1.  **Stage changes**: `.\.venv\Scripts\python.exe manage.py makemigrations` (Creates a blueprint file in `teams/migrations/`).
2.  **Appy changes**: `.\.venv\Scripts\python.exe manage.py migrate` (Actually modifies the `db.sqlite3` file).

## 3. Database Reset (Emergency Only)
If your database gets corrupted or you want to start fresh with a new user system:
1.  Delete `db.sqlite3`.
2.  Delete all files in `teams/migrations/` (except `__init__.py`).
3.  Run `makemigrations` and `migrate`.

## 4. Why SQLite?
SQLite is excellent for class-sized projects because it is "zero-config" (no server to install) and lives entirely in the `db.sqlite3` file. For larger-scale deployments, Django makes it easy to switch to PostgreSQL by changing the `DATABASES` setting.
