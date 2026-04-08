# 🧪 Testing Manual

This project includes a comprehensive test suite to ensure that authentication and registration logic remains bug-free.

## 1. Running Automated Tests
The automated tests check for role-based permissions, redirects, and Gmail triggers.

```powershell
# Run all tests for the teams app:
.\.venv\Scripts\python.exe manage.py test teams

# Run in "Verbose" mode to see exactly which test cases passed:
.\.venv\Scripts\python.exe manage.py test teams -v 2
```

## 2. What is being tested?
- **Auth Redirections**: Verifies that Students go to their dashboard and Teachers go to theirs.
- **Permissions**: Verifies that Students are blocked from the Teacher Dashboard.
- **Gmail Logic**: Verified that a "Password Set" email is correctly addressed and triggered upon signup.
- **Team Join**: Verifies that students can still join teams in the new auth system.

## 3. Manual Verification Checklist
Before every `git push`, you should perform these manual checks:
1.  **Signup**: Does a new user get redirected correctly and is the success message shown?
2.  **Login**: Does the login form correctly show red error boxes for wrong passwords?
3.  **Role**: Does the blue bar say "Teacher Dashboard" when logged in as a lecturer?
4.  **Security**: Does trying to access `/teacher/` while logged out redirect you to `/login/`?
