# ⚡ Quick Commands & Links

A one-page cheat sheet for common commands and essential links.

## 🌐 Essential Links (Local)
- **Home / Dashboard**: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Admin Panel**: [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)
- **User Signup**: [http://127.0.0.1:8000/signup/](http://127.0.0.1:8000/signup/)
- **Public Gallery**: [http://127.0.0.1:8000/gallery/](http://127.0.0.1:8000/gallery/)

## 🚀 Deployment & Docs
- **Render Dashboard**: [https://dashboard.render.com/](https://dashboard.render.com/)
- **GitHub Dashboard**: [https://github.com/](https://github.com/)
- **Django Docs (Home)**: [https://docs.djangoproject.com/en/5.0/](https://docs.djangoproject.com/en/5.0/)
- **Deployment Checklist**: [https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/](https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/)
- **Static Files Guide**: [https://docs.djangoproject.com/en/5.0/howto/static-files/](https://docs.djangoproject.com/en/5.0/howto/static-files/)

---

## 💻 Terminal Commands (PowerShell)

### Server Management
| Action | Command |
| :--- | :--- |
| **Start Server** | `.\.venv\Scripts\python.exe manage.py runserver` |
| **Fix App Errors** | `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process` |
| **Activate Venv** | `.\.venv\Scripts\activate` |

### Database & Admin
| Action | Command |
| :--- | :--- |
| **Create Admin** | `.\.venv\Scripts\python.exe manage.py createsuperuser` |
| **Save Profile Changes** | `.\.venv\Scripts\python.exe manage.py makemigrations` |
| **Apply Profile Changes** | `.\.venv\Scripts\python.exe manage.py migrate` |
| **Inspect DB SQL** | `.\.venv\Scripts\python.exe manage.py sqlmigrate teams 0001` |

### Testing & Verification
| Action | Command |
| :--- | :--- |
| **Run Fast Tests** | `.\.venv\Scripts\python.exe manage.py test teams` |
| **Run Detailed Tests** | `.\.venv\Scripts\python.exe manage.py test teams -v 2` |
| **Health Check** | `.\.venv\Scripts\python.exe manage.py check` |

---

## 🔒 Security Configuration (.env)
Remember to keep these set in your `.env` file for local development:
- `DEBUG=True`
- `EMAIL_HOST_USER=...`
- `EMAIL_HOST_PASSWORD=...`
