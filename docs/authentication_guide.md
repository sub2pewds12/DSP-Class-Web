# 🔑 Authentication & Role Guide

The site uses a **three-role system** (Student, Lecturer, Developer) with a simple, direct registration process.

## 1. Registration Process
The platform uses a **hybrid registration flow** to balance student ease-of-use with administrative security.

- **Students**: Direct registration. Students pick their password and access the `/hub/` immediately.
- **Lecturers & Admins**: Choice-based registration with a **Security Gate**. These roles default to `is_approved = False`.
- **Approval Flow**: New staff must await manual approval via the **Developer Dashboard**. Automated HTML emails are sent upon approval or denial.
- **Username**: Your **Email Address** serves as your username for logging in.

## 2. User Roles
| Role | Access Level | Dashboard |
| :--- | :--- | :--- |
| **Student** | Join/create teams, submit assignments, view grades | `/hub/` |
| **Lecturer** | Upload documents, create assignments, grade submissions, release results | `/teacher/` |
| **Developer** | Full system access, analytics, infrastructure portals, Django Admin | `/dev-dashboard/` |

### Role Permissions in Code
- **Lecturers** are auto-granted `is_staff = True` (admin panel access).
- **Developers** are auto-granted `is_staff = True` and `is_superuser = True`.
- **Students** have `is_staff = False` and `is_superuser = False`.

## 3. Gmail Configuration (Optional)
Gmail is **only** required if a user forgets their password and needs to reset it via the built-in password reset flow.

> [!TIP]
> If you are on a "Free" Render tier, automated emails may be blocked. Admins can manually reset a student's password using the terminal command:
> `.\.venv\Scripts\python.exe manage.py changepassword student-email@gmail.com`

## 4. URL Map for Accounts
| Route | Purpose |
| :--- | :--- |
| `/login/` | Login page (also served at `/`) |
| `/signup/` | Student registration |
| `/logout/` | Log out |
| `/password-reset/` | Email-based password reset |
| `/hub/` | Student dashboard (redirects Lecturers to `/teacher/`) |
| `/teacher/` | Lecturer dashboard |
| `/dev-dashboard/` | Developer dashboard |
| `/gallery/` | Public team showcase (no login required) |
| `/guide/` | User guide (no login required) |
