# 🧪 Testing Manual

This project includes a comprehensive test suite to ensure that authentication and registration logic remains bug-free.

## 1. Running Automated Tests
```powershell
# Run all tests for the teams app:
.\.venv\Scripts\python.exe manage.py test teams

# Run in "Verbose" mode to see exactly which test cases passed:
.\.venv\Scripts\python.exe manage.py test teams -v 2
```

## 2. What Is Being Tested?
- **Auth Redirections**: Verifies that Students go to `/hub/` and Lecturers are redirected to `/teacher/`.
- **Permissions**: Verifies that Students are blocked from the Lecturer and Developer dashboards.
- **Role Enforcement**: Verifies that public signup correctly assigns Student, Lecturer, or Dev roles and triggers the `is_approved` security gate where necessary.
- **Approval System**: Verifies that unapproved staff are blocked from dashboards and correctly redirected to the pending status page.
- **Team Join**: Verifies that students can join or create teams, and the first member is assigned as leader.
- **Grading Flow**: Verifies that only Lecturers and Developers can grade submissions and release results.

## 3. Manual Verification Checklist
Before every major release, perform these manual infrastructure checks:

### Registration & Approval Workflow
1.  **Staff Signup**: Register as a **Lecturer**. Are you redirected to `/pending-approval/`?
2.  **Admin Alert**: Check the administrator email. Was there an alert about the new access request?
3.  **Approval**: Log in as a **Dev**, visit the `/dev-dashboard/`, and **Approve** the new Lecturer.
4.  **Welcome Email**: As the new Lecturer, did you receive a premium HTML "Welcome" email?
5.  **Denial**: Repeat with a test account and verify the "Denial" email is sent and access remains blocked.

### Infrastructure & Alerts
6.  **Critical Errors**: Deliberately trigger an error (or use the shell to create a `SystemError`). Does the admin receive a **Critical Alert** email?
7.  **Uptime Pulse**: Run `python manage.py log_pulse`. Does the dashboard update with the latest latency?
8.  **Prod Uptime**: Ensure an external pinger (UptimeRobot) is active and correctly hitting the root URL.

### Latest Activities Feed
9.  **Live Polling**: On the student dashboard, trigger an action (e.g., update project details). Within 30 seconds, does the new event slide into the **Latest Activities** tile with a pulse glow?
10. **View All Modal**: Click the **View All** link. Does the Activity History modal open with a spinner, then load the full timeline?
11. **Load More**: If the team has >15 logged events, does the **Load More** button appear and fetch additional pages? Does "You've reached the beginning" appear at the end?
