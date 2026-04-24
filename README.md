# DSP Project Registration Platform

A comprehensive, production-ready platform designed to manage student team registrations, assignment submissions, and grading for the Digital Signal Processing (DSP) class.

## 🚀 Tech Stack
- **Backend / API**: Django 5.0 (Python) + **Django Ninja** (Schema-driven API layer)
- **Database**: **Supabase PostgreSQL** (Tokyo Cluster) with Row Level Security (RLS)
- **Dashboard UI**: **Django Unfold** (Premium, Dark-mode responsive admin portal)
- **Media Storage**: Cloudinary (Persistent cloud storage for student submissions)
- **Static Files**: WhiteNoise (Compressed static asset serving)
- **Frontend**: Vanilla CSS & JavaScript + Bootstrap 5
- **Platform**: Render (Automated CI/CD deployment via Docker)

## 🌟 Key Features
- **Modern Unfold Dashboard**: High-end administrative interface with dark mode and streamlined navigation.
- **Structured Assignments**: Lecturers define tasks with specific deadlines and upload-specific slots.
- **API Shielding & Security**: Global **CORS** headers, **IP-based Rate Limiting**, and **Host Hardening**.
- **Modern AJAX Dashboards**: All state-modifying actions are handled via a centralized API utility.
- **Interactive API Documentation**: Full Swagger / OpenAPI portal for system integration.
- **Manual Grading**: Dedicated numeric score (0-100) and qualitative feedback system.
- **Result Release Control**: Grades are kept private until deliberately released.
- **Resource Repository**: Central hub for class materials and PDFs.
- **Role-Based Approval**: Secure gatekeeping where Lecturers and Admins require manual verification.
- **NOC-Style System Telemetry**: High-density real-time tracking of DB latency, system load, and runtime errors with automated emergency alerting.
- **Automated Storage Maintenance**: Submission engine automatically purges old records and files when students upload replacements, preventing database bloat.
- **Scalable Dashboard Logic**: Optimized database prefetching solves N+1 performance bottlenecks for the student interface.
- **Database Cloaking**: Row Level Security (RLS) enabled on all tables to prevent public API exposure.
- **Dev Center Portals**: Deep-linked management tools for Render, Cloudinary, and UptimeRobot analytics.
- **Cloud Command Center**: Integrated storage analytics portal for deep visibility into media integrity and Cloudinary usage patterns.
- **Connection Resilience**: Engineered for Supabase Transaction Pooling with aggressive idle-connection pruning (`CONN_MAX_AGE=0`).
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

- [System Pulse & Resilience](docs/resilience_guide.md) — Self-healing engine and analytics caching.

## 🐳 Docker Deployment
The platform is fully containerized for consistent deployment:
1. **Build & Start**: `docker-compose up --build -d`
2. **Setup**: The container automatically handles migrations and static collection.
3. **Check**: Access the dev-dashboard at `localhost:8000/dev-dashboard/` to verify health.

## 📂 Documentation
Detailed guides are available in the [`docs/`](docs/) folder:
- [Local Development](docs/local_development.md) — Running the server and setting up your environment.
- [Authentication & Roles](docs/authentication_guide.md) — User roles and the registration flow.
- [Database Management](docs/database_management.md) — Migrations, resets, and storage architecture.
- [Deployment Checklist](docs/deployment_checklists.md) — Environment variables and Render setup.
- [Quick Commands](docs/quick_commands.md) — Essential command line tools and reference links.
- [Testing Manual](docs/testing_manual.md) — Automated tests and manual verification steps.
