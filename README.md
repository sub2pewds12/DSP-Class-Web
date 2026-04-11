# DSP Project Registration Platform

A comprehensive, production-ready platform designed to manage student team registrations, assignment submissions, and grading for the Digital Signal Processing (DSP) class.

## 🚀 Tech Stack
- **Backend**: Django 4.2+ (Python)
- **Database**: PostgreSQL (Production-grade relational storage)
- **Storage**: Cloudinary (Persistent cloud storage for student submissions and instructions)
- **Frontend**: Vanilla CSS & JavaScript + Bootstrap 5 (Clean, responsive dashboard UI)
- **Platform**: Render (Automated CI/CD deployment)

## 🌟 Key Features
- **Team Registration**: Specialized logic for creating and joining teams with leader-auto-assignment.
- **Structured Assignments**: Lecturers define tasks with specific deadlines and upload-specific slots.
- **Manual Grading**: Dedicated numeric score (0-100) and qualitative feedback system.
- **Result Release Control**: Grades are kept private until deliberately released by the lecturer.
- **Resource Repository**: Central hub for class materials and PDFs.
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
