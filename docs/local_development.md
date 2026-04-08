# 🛠️ Local Development Guide

This guide covers everything you need to run, modify, and manage the DSP Project Registration site on your local Windows machine.

## 1. Starting the Server
Since Windows often blocks script activation, the most reliable way to start your project is by calling the virtual environment's Python executable directly.

```powershell
# Open your terminal in the project folder and run:
.\.venv\Scripts\python.exe manage.py runserver
```

Once running, your site is available at: **[http://127.0.0.1:8000/](http://127.0.0.1:8000/)**

## 2. Activating the Virtual Environment
If you want to use the virtual environment for other commands (like `pip install`), you might see an "Execution Policy" error. Use this command to bypass it for your current session:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
# Now you can activate:
.\.venv\Scripts\activate
```

## 3. Creating a Superuser (Admin)
If you need to access the Django Admin and don't have an account, create a main administrator account:

```powershell
.\.venv\Scripts\python.exe manage.py createsuperuser
```
Follow the prompts to set your email and password. Then visit `/admin/` to log in.

## 4. Key Project Files
- **`teams/models.py`**: Where the database structure (Student, Teacher, Team) is defined.
- **`teams/views.py`**: The logic that handles registration and dashboards.
- **`teams/templates/`**: The HTML files that define how the website looks.
- **`.env`**: Your local secret settings (Gmail, DEBUG mode).
