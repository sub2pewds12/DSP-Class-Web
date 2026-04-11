# 🔑 Authentication & Role Guide

The site uses a dual-role system (Student vs. Teacher) with a simple, direct registration process.

## 1. Direct Registration
Unlike traditional "email-first" onboarding, this site uses **Direct Registration** to ensure reliability on all hosting platforms (like Render Free).

- **How it works**: New users choose their password immediately during signup.
- **Login**: Users are automatically logged in upon successful registration.
- **Username**: Your **Email Address** serves as your username for logging in.

## 2. User Roles
- **Student**: Can join or create a team after logging in.
- **Lecturer / Teacher**: Gain access to the **Teacher Dashboard** (`/teacher/`) to oversee all class activity.

## 3. Gmail Configuration (Optional)
Gmail is **only** required if a user forgets their password and needs to reset it.

> [!TIP]
> If you are on a "Free" render tier, automated emails may be blocked. Teachers can manually reset a student's password using the terminal command:
> `python manage.py changepassword student-email@gmail.com`

## 4. URL Map for Accounts
- Login: `/login/`
- Signup: `/signup/`
- Logout: `/logout/`
- Password Reset: `/password-reset/`
