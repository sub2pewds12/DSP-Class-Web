# 🔑 Authentication & Role Guide

The site uses a dual-role system (Student vs. Teacher) with a secure "Email-First" onboarding process.

## 1. Gmail Configuration (Required)
For the website to send the "Set Password" invites or reset passwords, you must configure a Gmail account in your `.env` file.

> [!IMPORTANT]
> **Do not use your regular Gmail password.** You must generate an **App Password**.
> 1. Go to your [Google Account Security](https://myaccount.google.com/security).
> 2. Enable 2-Step Verification.
> 3. Search for "App Passwords" and create one labeled "Django".
> 4. Copy the 16-character code into your `.env`:

```text
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=xxxx-xxxx-xxxx-xxxx
```

## 2. User Roles
- **Student**: Land on the standard dashboard to join or create a project team.
- **Lecturer / Teacher**: Land on the **Teacher Dashboard** (`/teacher/`) which shows an overview of all teams and their members.

## 3. Onboarding Flow
1. **Signup**: User enters Name, Email, and Role. No password is asked for.
2. **Invite**: The system sends a Gmail with a secure link.
3. **Set Password**: The user clicks the link and creates their password.
4. **Login**: User can now log in normally.

## 4. URL Map for Accounts
- Login: `/login/`
- Signup: `/signup/`
- Logout: `/logout/`
- Password Reset: `/password-reset/`
