# Mobile Login Troubleshooting Guide

Quick guide to fix login issues on mobile devices (smartphones and tablets).

---

## Problem: Cannot Login on Mobile (Works on Laptop)

### Symptoms
- Login works perfectly on laptop/desktop
- Same credentials fail on smartphone/tablet
- No error message, just redirects back to login page
- Or shows "Invalid credentials" even though they're correct

---

## Root Causes

### 1. Session Cookie Settings
The most common cause is incorrect session cookie configuration.

**Technical Details**:
- `SESSION_COOKIE_SECURE=True` requires HTTPS
- Mobile browsers are stricter about cookie security
- `SESSION_COOKIE_SAMESITE` affects cross-site cookie behavior

### 2. HTTP vs HTTPS Access
- Laptop might be accessing via HTTP (localhost)
- Mobile must access via HTTPS (production URL)

### 3. Browser Cache Issues
- Old cookies from failed login attempts
- Cached login pages with wrong CSRF tokens

---

## Solutions

### Solution 1: Verify Your .env Configuration (PythonAnywhere)

**On PythonAnywhere bash console**:

```bash
cd ~/savings-system
nano .env
```

**Ensure these settings are present**:

```bash
# Session Configuration
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_SAMESITE=Lax
PERMANENT_SESSION_LIFETIME=1800
```

**Save and exit**: Ctrl+X, then Y, then Enter

**Reload web app**: Go to Web tab → Click "Reload"

---

### Solution 2: Verify HTTPS Access

**Make sure your smartphone is accessing the site via HTTPS**:

✅ **Correct URL**: `https://oldtimers.pythonanywhere.com`

❌ **Wrong URL**: `http://oldtimers.pythonanywhere.com`

**How to check**:
1. Look at the browser address bar
2. Should show a lock icon 🔒
3. URL should start with `https://`

---

### Solution 3: Clear Mobile Browser Cache

#### For iPhone/iPad (Safari)
1. Go to **Settings**
2. Scroll down to **Safari**
3. Tap **Clear History and Website Data**
4. Confirm by tapping **Clear History and Data**

#### For Android (Chrome)
1. Open **Chrome** app
2. Tap three dots (⋮) in top right
3. Go to **Settings**
4. Tap **Privacy and security**
5. Tap **Clear browsing data**
6. Select:
   - Cookies and site data
   - Cached images and files
7. Tap **Clear data**

#### For Android (Samsung Internet)
1. Open **Samsung Internet** app
2. Tap three lines (≡) in bottom right
3. Tap **Settings**
4. Tap **Privacy and security**
5. Tap **Delete browsing data**
6. Select cookies and cache
7. Tap **Delete**

---

### Solution 4: Try Different SameSite Setting

If the above solutions don't work, try relaxing the SameSite policy:

**Edit .env on PythonAnywhere**:
```bash
nano .env
```

**Change**:
```bash
SESSION_COOKIE_SAMESITE=None
```

**Important**: This is less secure, so only use if `Lax` doesn't work.

**Reload the web app** after making this change.

---

### Solution 5: Check for Account Lockout

If you've tried logging in multiple times unsuccessfully:

1. Your account may be locked for 30 minutes
2. Wait 30 minutes and try again
3. Or ask an admin to unlock your account

**To check if locked (admin only)**:
```bash
cd ~/savings-system
workon savings-env
flask shell
```

```python
from app.models.user import User
from datetime import datetime

user = User.query.filter_by(username='your-username').first()
if user.account_locked_until:
    print(f"Account locked until: {user.account_locked_until}")
    # To unlock:
    user.account_locked_until = None
    user.failed_login_attempts = 0
    from app import db
    db.session.commit()
    print("Account unlocked!")
else:
    print("Account is not locked")
exit()
```

---

### Solution 6: Test with Different Browser

Try accessing the site from a different browser on your mobile:

- **iPhone**: Try Chrome instead of Safari (or vice versa)
- **Android**: Try Samsung Internet instead of Chrome (or vice versa)

This helps identify if it's a browser-specific issue.

---

## Quick Checklist

Before troubleshooting, verify:

- [ ] Using HTTPS URL (https://...)
- [ ] Correct username and password
- [ ] Account is not locked
- [ ] .env file has correct session settings
- [ ] Web app was reloaded after .env changes
- [ ] Mobile browser cache is cleared
- [ ] Not using incognito/private mode (can cause cookie issues)

---

## Still Not Working?

If none of the above solutions work:

### Check Error Logs

**On PythonAnywhere**:
```bash
tail -50 /var/log/oldtimers.pythonanywhere.com.error.log
```

Look for errors related to:
- Session handling
- Cookie errors
- Authentication failures

### Verify Database Connection

```bash
cd ~/savings-system
workon savings-env
flask shell
```

```python
from app.models.user import User
user = User.query.filter_by(username='your-username').first()
print(f"User found: {user}")
print(f"Active: {user.is_active if user else 'N/A'}")
print(f"Role: {user.role if user else 'N/A'}")
exit()
```

### Contact Support

If the issue persists:
1. Note the exact error message (if any)
2. Note your mobile device and browser
3. Check if the issue happens on all mobile devices or just one
4. Provide this information when seeking help

---

## Prevention

To avoid future mobile login issues:

1. Always use HTTPS in production
2. Keep `SESSION_COOKIE_SECURE=True` in production
3. Use `SESSION_COOKIE_SAMESITE=Lax` as default
4. Test login on mobile devices after deployment
5. Document the production URL for users

---

## Technical Notes

### How Session Cookies Work

1. User submits login form
2. Server validates credentials
3. Server creates session and sends session cookie
4. Browser stores cookie
5. Browser sends cookie with each request
6. Server validates cookie to maintain login

### Cookie Attributes

- **Secure**: Only sent over HTTPS
- **HttpOnly**: Cannot be accessed by JavaScript
- **SameSite**: Controls cross-site cookie behavior
  - `Strict`: Never sent in cross-site requests
  - `Lax`: Sent in top-level navigation (recommended)
  - `None`: Sent in all contexts (requires Secure flag)

---

## Summary

Most mobile login issues are caused by:
1. ❌ Incorrect session cookie configuration
2. ❌ Accessing via HTTP instead of HTTPS
3. ❌ Cached browser data

The fix is usually:
1. ✅ Set `SESSION_COOKIE_SECURE=True` in .env
2. ✅ Access via HTTPS URL
3. ✅ Clear mobile browser cache
4. ✅ Reload web app

After these steps, mobile login should work perfectly!
