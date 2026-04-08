# 🚀 Deployment Checklist (Render)

The website is fully compatible with **Render.com** using Docker. Whenever you `git push` to your main branch, Render will automatically rebuild and update your live link.

## 1. Environment Variables in Render
For your live site to work securely, you **must** add these variables in the Render Dashboard (under the "Environment" tab):

| Key | Value |
| :--- | :--- |
| `DEBUG` | `False` |
| `SECRET_KEY` | *(A long random string)* |
| `ALLOWED_HOSTS` | `your-app-name.onrender.com` |
| `CSRF_TRUSTED_ORIGINS` | `https://your-app-name.onrender.com` |
| `EMAIL_HOST_USER` | `your-email@gmail.com` |
| `EMAIL_HOST_PASSWORD` | `xxxx-xxxx-xxxx-xxxx` (App Password) |

## 2. Deployment Process
1.  **Commit**: `git add .` then `git commit -m "Update message"`
2.  **Push**: `git push origin main`
3.  **Wait**: Monitor the "Deploys" tab in Render. It will automatically run:
    -   `python manage.py collectstatic` (to prepare CSS/JS).
    -   `python manage.py migrate` (to update your database).
    -   `gunicorn config.wsgi` (to start the production server).

## 3. Important Files for Hosting
- **`Dockerfile`**: Tells Render how to build the environment.
- **`Procfile`**: Tells Render how to start the web server.
- **`build.sh`**: Standard script for installing requirements and running static collection.
- **`.dockerignore`**: Ensures secrets (like `.env`) are not accidentally baked into the public image.
