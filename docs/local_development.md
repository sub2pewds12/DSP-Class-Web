# 🛠️ Local Development Guide

This guide covers everything you need to run, modify, and manage the DSP Project Registration site on your local Windows machine.

## 1. Starting the Server
Since Windows often blocks script activation, the most reliable way to start your project is by calling the virtual environment's Python executable directly.

```powershell
# Open your terminal in the project folder and run:
.\.venv\Scripts\python.exe manage.py runserver
```

Once running, your site is available at: **[http://127.0.0.1:8000/](http://127.0.0.1:8000/)**

## 2. Configuration & Optimization (SQLite)
To prevent "Database is Locked" errors during local development (especially when using the API docs), ensure your `config/settings.py` includes these optimizations:

- **Increased Timeout**: The database configuration should include `'timeout': 20` in its options.
- **Session Persistence**: Set `SESSION_SAVE_EVERY_REQUEST = False`. This prevents redundant database writes on every GET request, which is critical for handling the multiple concurrent requests fired by the Swagger UI.
- **Pooled Database Optimization**: When using Supabase Transaction Pooler (Port 6543), set `CONN_MAX_AGE = 0`. This ensures that connections are released back to the pool immediately, preventing connection exhaustion during development.

## 3. Activating the Virtual Environment
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
DATABASE_URL=postgresql://postgres:password@db.zidhrjftuoyrvoxfnyev.supabase.co:6543/postgres?pgbouncer=true
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

## 7. High-Fidelity Monitoring (Smart Heartbeat)

The project includes an autonomous "Ghost Heartbeat" monitor that tracks database latency with high precision.

- **Automatic Activation**: The monitor starts automatically as soon as any visitor (you or a student) accesses the site. No manual commands are required.
- **Smart Idle**: To save resources on the free tier, the monitor will stay active for a **30-minute grace period** after the last site interaction, then gracefully shut down until the next visit.
- **Production Tracking**: If you set `PROD_DB_URL` in your `.env`, the local Developer Dashboard will track the latency of your **Live Production Database** instead of your local SQLite file, giving you a real-time health check of the production environment while you develop.
- **Manual Control**: If you need to run the monitor as a persistent foreground process for testing, use:
  ```powershell
  python manage.py log_pulse --loop --interval 60
  ```

## 8. Telemetry Simulation & Real-time Capture
The **Developer Dashboard** includes a real-time traffic pulse histogram. To facilitate development, the system behaves differently depending on your environment:

### Simulation Baseline
When `DEBUG=True` and your telemetry cache is empty, the system automatically seeds **100 mock pulses**. This ensures you have a visual baseline to test the dashboard's toggles (Linear vs. Logarithmic) and heatmap colors immediately upon startup.

### Verifying Real-time Capture
To verify that the middleware is correctly capturing your activity:
1. Open the **Dev Dashboard**.
2. In a separate tab, navigate around the site (e.g., visit the Admin panel, the Hub, or a Team page).
3. Refresh the Dev Dashboard. You will see your actual requests appearing as new bars on the right side of the "Traffic Pulse" graph.
4. **Note**: Static files (`/static/`) and the telemetry endpoint itself are filtered out to keep the graph focused on functional app logic.
