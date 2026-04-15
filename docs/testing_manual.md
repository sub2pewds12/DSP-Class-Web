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
- **Role Enforcement**: Verifies that public signup always creates Student accounts regardless of request data.
- **Team Join**: Verifies that students can join or create teams, and the first member is assigned as leader.
- **Grading Flow**: Verifies that only Lecturers and Developers can grade submissions and release results.

## 3. Manual Verification Checklist
Before every `git push`, you should perform these manual checks:
1.  **Signup**: Does a new user get redirected to `/hub/` and is the success message shown?
2.  **Login**: Does the login form correctly show error messages for incorrect credentials?
3.  **Role Redirect**: Does a Lecturer login redirect to `/teacher/` automatically?
4.  **Security**: Does accessing `/teacher/` while logged out redirect to `/login/`?
5.  **Gallery**: Does `/gallery/` load without requiring login and show all teams?
6.  **Assignments**: Can a Lecturer create an assignment and can a Student submit to it?
7.  **Grading**: Can a Lecturer grade a submission and release results?
8.  **Dev Dashboard**: Does `/dev-dashboard/` show analytics charts and system info (DEV role only)?
