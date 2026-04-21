# 🚀 Deployment Checklist (Render)

The website is fully compatible with **Render.com** using Docker. Whenever you `git push` to your main branch, Render will automatically rebuild and update your live link.

## 1. Environment Variables in Render
For your live site to work securely, you **must** add these variables in the Render Dashboard (under the "Environment" tab):

### Core Settings
| Key | Value |
| :--- | :--- |
| `DEBUG` | `False` |
| `SECRET_KEY` | *(A long random string)* |
| `DATABASE_URL` | *(The **Internal Database URL** from your Render PostgreSQL)* |
| `ALLOWED_HOSTS` | `your-app-name.onrender.com` |
| `CSRF_TRUSTED_ORIGINS` | `https://your-app-name.onrender.com` |

### Email (Optional — for password resets)
| Key | Value |
| :--- | :--- |
| `EMAIL_HOST_USER` | `your-email@gmail.com` |
| `EMAIL_HOST_PASSWORD` | `xxxx-xxxx-xxxx-xxxx` (App Password) |

### Cloudinary (Required — for media file storage)
| Key | Value |
| :--- | :--- |
| `CLOUDINARY_CLOUD_NAME` | *(Your Cloudinary cloud name)* |
| `CLOUDINARY_API_KEY` | *(Your Cloudinary API key)* |
| `CLOUDINARY_API_SECRET` | *(Your Cloudinary API secret)* |

> [!IMPORTANT]
> **Database Persistence**: To keep your users/teams forever, you must click **"New +" -> "PostgreSQL"** in Render. Copy the **Internal Database URL** and add it as `DATABASE_URL`.

> [!IMPORTANT]
> **Media Persistence**: Without Cloudinary configured, uploaded documents and submissions will be lost on each deployment. Sign up at [cloudinary.com](https://cloudinary.com) for a free account.

## 2. Deployment Process
1.  **Commit**: `git add .` then `git commit -m "Update message"`
2.  **Push**: `git push origin main`
3.  **Wait**: Monitor the "Deploys" tab in Render. It will automatically run:
    -   `python manage.py collectstatic` (to prepare CSS/JS).
    -   `python manage.py migrate` (to update your database).
    -   `gunicorn config.wsgi` (to start the production server).

## 3. Important Files for Hosting
| File | Purpose |
| :--- | :--- |
| `Dockerfile` | Tells Render how to build the environment |
| `Procfile` | Tells Render how to start the web server |
| `build.sh` | Installs requirements and runs static collection |
| `.dockerignore` | Ensures secrets (like `.env`) are not baked into the image |
| `runtime.txt` | Specifies the Python version |
| `requirements.txt` | Python dependencies |

## 4. Production Security & Resilience (Phase 4 Hardened)
When `DEBUG=False`, the following security settings are automatically active:
- **HSTS**: 1 year, including subdomains, with preload.
- **Header Hardening**: `X-Frame-Options: DENY`, `SECURE_CONTENT_TYPE_NOSNIFF`, and `SECURE_REFERRER_POLICY: same-origin`.
- **CSP**: Content Security Policy is active (refer to `production.py`).
- **Resilience**: Analytics caching and automated self-healing are enabled.

## 5. Docker Orchestration
For local production simulation or containerized cloud hosting:
1.  **Build**: `docker-compose build`
2.  **Run**: `docker-compose up -d`
3.  **Logs**: `docker-compose logs -f web`
4.  **Admin Check**: Visit `localhost:8000/dev-dashboard/`
