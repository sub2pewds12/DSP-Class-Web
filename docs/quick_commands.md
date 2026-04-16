# ⚡ Quick Commands & Links

A one-page cheat sheet for common commands and essential links.

## 🌐 Essential Links (Local)
| Page | URL |
| :--- | :--- |
| **Login** | [http://127.0.0.1:8000/](http://127.0.0.1:8000/) |
| **Student Dashboard** | [http://127.0.0.1:8000/hub/](http://127.0.0.1:8000/hub/) |
| **Lecturer Dashboard** | [http://127.0.0.1:8000/teacher/](http://127.0.0.1:8000/teacher/) |
| **Dev Dashboard** | [http://127.0.0.1:8000/dev-dashboard/](http://127.0.0.1:8000/dev-dashboard/) |
| **Public Gallery** | [http://127.0.0.1:8000/gallery/](http://127.0.0.1:8000/gallery/) |
| **User Guide** | [http://127.0.0.1:8000/guide/](http://127.0.0.1:8000/guide/) |
| **Admin Panel** | [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/) |
| **Signup** | [http://127.0.0.1:8000/signup/](http://127.0.0.1:8000/signup/) |

## 🚀 External Services
| Service | URL |
| :--- | :--- |
| **Render Dashboard** | [https://dashboard.render.com/](https://dashboard.render.com/) |
| **Cloudinary Console** | [https://cloudinary.com/console](https://cloudinary.com/console) |
| **GitHub** | [https://github.com/](https://github.com/) |
| **Django Docs** | [https://docs.djangoproject.com/en/5.0/](https://docs.djangoproject.com/en/5.0/) |

---

## 💻 Console Commands (PowerShell)

### Server Management
| Action | Command |
| :--- | :--- |
| **Start Server** | `.\.venv\Scripts\python.exe manage.py runserver` |
| **Fix Execution Policy** | `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process` |
| **Activate Venv** | `.\.venv\Scripts\activate` |

### Database & Admin
| Action | Command |
| :--- | :--- |
| **Create Admin** | `.\.venv\Scripts\python.exe manage.py createsuperuser` |
| **Stage Model Changes** | `.\.venv\Scripts\python.exe manage.py makemigrations` |
| **Apply Model Changes** | `.\.venv\Scripts\python.exe manage.py migrate` |
| **Inspect DB SQL** | `.\.venv\Scripts\python.exe manage.py sqlmigrate teams 0001` |
| **Seed Test Data** | `.\.venv\Scripts\python.exe manage.py seed_dsp` |
| **Clear Test Data** | `.\.venv\Scripts\python.exe manage.py seed_dsp --clear` |

### Testing & Verification
| Action | Command |
| :--- | :--- |
| **Run Tests** | `.\.venv\Scripts\python.exe manage.py test teams` |
| **Run Verbose Tests** | `.\.venv\Scripts\python.exe manage.py test teams -v 2` |
| **Health Check** | `.\.venv\Scripts\python.exe manage.py check` |
| **Collect Static** | `.\.venv\Scripts\python.exe manage.py collectstatic --noinput` |

---

## 🔒 Security Configuration (.env)
Remember to keep these set in your `.env` file for local development:
- `SECRET_KEY=...`
- `DEBUG=True`
- `EMAIL_HOST_USER=...`
- `EMAIL_HOST_PASSWORD=...`
- `CLOUDINARY_CLOUD_NAME=...`
- `CLOUDINARY_API_KEY=...`
- `CLOUDINARY_API_SECRET=...`
