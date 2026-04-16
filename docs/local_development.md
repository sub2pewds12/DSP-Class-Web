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

### Configuration
| File | Purpose |
| :--- | :--- |
| `config/settings.py` | Django settings (database, email, Cloudinary, security) |
| `config/urls.py` | Root URL configuration |
| `.env` | Local secret settings (secret key, Gmail, Cloudinary, DEBUG) |
| `requirements.txt` | Python package dependencies |

### Application (`teams/`)
| File | Purpose |
| :--- | :--- |
| `models.py` | Database models (CustomUser, Team, Student, Assignment, etc.) |
| `views.py` | View logic for dashboards, signup, grading, and galleries |
| `urls.py` | App-level URL routing |
| `forms.py` | Django forms for registration, submissions, and grading |
| `admin.py` | Django Admin configuration and custom actions |
| `templates/` | HTML templates for all pages |
| `static/` | CSS, JavaScript, and image assets |
| `management/commands/` | Custom management commands (e.g., `seed_dsp`) |
| `tests/` | Automated test suite |

## 5. Environment Variables (`.env`)
Your `.env` file should contain:
```env
SECRET_KEY=your-secret-key
DEBUG=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=xxxx-xxxx-xxxx-xxxx
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret
```

## 6. Production Uptime (Render Free Tier)
Because this project is configured for the **Render Free Tier**, the web service will automatically "Spin Down" after 15 minutes of inactivity.

- **Impact**: The first request after a sleep period will take ~30 seconds to wake the server.
- **Monitoring**: Infrastructure alerts (Database Pulse & Runtime Errors) only trigger when the server is "Awake."
- **Solution**: Use a free service like **UptimeRobot** to ping your root URL (`/`) every 5 minutes. This keeps the site active 24/7 and ensures you are the first to know if a real outage occurs.
