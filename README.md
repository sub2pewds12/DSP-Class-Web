# DSP Project Registration Platform

A comprehensive, production-ready platform designed to manage student team registrations, assignment submissions, and grading for the Digital Signal Processing (DSP) class.

## 🚀 Tech Stack
- **Backend / API**: Django 5.0 (Python) + **Django Ninja** (Schema-driven API layer)
- **Database**: SQLite (Local) / PostgreSQL (Production via `dj-database-url`)
- **Media Storage**: Cloudinary (Persistent cloud storage for student submissions and instructions)
- **Static Files**: WhiteNoise (Compressed static asset serving)
- **Frontend**: Vanilla CSS & JavaScript + Bootstrap 5 (Modern, AJAX-driven Dashboard UI)
- **Platform**: Render (Automated CI/CD deployment via Docker)

## 🌟 Key Features
- **Team Registration**: Specialized logic for creating and joining teams with leader-auto-assignment.
- **Structured Assignments**: Lecturers define tasks with specific deadlines and upload-specific slots.
- **Modern AJAX Dashboards**: All state-modifying actions (grading, uploads, role edits) are handled via a centralized API utility, eliminating page reloads.
- **Interactive API Documentation**: Full Swagger / OpenAPI portal for system integration and diagnostic testing.
- **Manual Grading**: Dedicated numeric score (0-100) and qualitative feedback system.
- **Result Release Control**: Grades are kept private until deliberately released by the lecturer.
- **Resource Repository**: Central hub for class materials and PDFs.
- **Role-Based Approval**: Secure gatekeeping where Lecturers and Admins require manual verification before access.
- **System Telemetry & Monitoring**: Real-time tracking of DB latency and runtime errors with automated emergency alerting.
- **Dev Center Portals**: Deep-linked management tools for Render, Cloudinary, and UptimeRobot analytics.
- **Seed Engine**: Custom `seed_dsp` command for surgical test data management.

## 🛠️ Management Commands
Populate your local or remote database with realistic test data:
```bash
.\.venv\Scripts\python.exe manage.py seed_dsp
```
Surgically remove only test data while preserving real user accounts:
```bash
.\.venv\Scripts\python.exe manage.py seed_dsp --clear
```

## 📂 Documentation
Detailed guides are available in the [`docs/`](docs/) folder:
- [Local Development](docs/local_development.md) — Running the server and setting up your environment.
- [Authentication & Roles](docs/authentication_guide.md) — User roles and the registration flow.
- [Database Management](docs/database_management.md) — Migrations, resets, and storage architecture.
- [Deployment Checklist](docs/deployment_checklists.md) — Environment variables and Render setup.
- [Quick Commands](docs/quick_commands.md) — Essential command line tools and reference links.
- [Testing Manual](docs/testing_manual.md) — Automated tests and manual verification steps.
