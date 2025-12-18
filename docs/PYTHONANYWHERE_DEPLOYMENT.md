# PythonAnywhere Deployment Guide

Complete guide for deploying the Old Timers Savings System to PythonAnywhere.

---

## Prerequisites

- PythonAnywhere account (Free or Paid)
- Git repository access
- Email account for notifications
- Basic familiarity with Bash console

---

## Deployment Overview

```
Local Development → Git Push → PythonAnywhere → Configure → Launch
```

---

## Step 1: Prepare Local Repository

### 1.1 Commit All Changes

```bash
cd /home/alex/savings-system

# Check status
git status

# Add all changes
git add .

# Commit
git commit -m "Prepare for PythonAnywhere deployment"

# Push to repository
git push origin main
```

### 1.2 Verify Requirements

Make sure `requirements.txt` is up to date:

```bash
cat requirements.txt
```

Should include:
```
Flask==3.0.0
Flask-SQLAlchemy==3.1.1
Flask-Login==0.6.3
Flask-WTF==1.2.1
Flask-Mail==0.10.0
requests==2.32.5
python-dateutil==2.8.2
reportlab==4.0.7
python-dotenv==1.0.0
phonenumbers==8.13.26
pytz==2023.3.post1
```

---

## Step 2: Set Up PythonAnywhere

### 2.1 Create Account

1. Go to https://www.pythonanywhere.com/
2. Sign up for free or paid account
3. Confirm email address
4. Log in to dashboard

### 2.2 Open Bash Console

From PythonAnywhere dashboard:
1. Click "Consoles" tab
2. Click "Bash"
3. A new bash console will open

---

## Step 3: Clone Repository

### In PythonAnywhere Bash Console:

```bash
# Clone your repository
git clone https://github.com/yourusername/savings-system.git
cd savings-system

# Or if using a different git provider
git clone <your-git-url>
cd savings-system
```

---

## Step 4: Set Up Virtual Environment

```bash
# Create virtual environment (Python 3.10 recommended)
mkvirtualenv --python=/usr/bin/python3.10 savings-env

# Activate it (should auto-activate, but if not:)
workon savings-env

# Install dependencies
pip install -r requirements.txt
```

**Note**: This may take several minutes. PythonAnywhere has good bandwidth.

---

## Step 5: Configure Environment Variables

### 5.1 Create .env File

```bash
nano .env
```

### 5.2 Add Configuration

```bash
# Flask Configuration
SECRET_KEY=396c6bb96740299d4709507f5d8470a8
FLASK_ENV=production

# Database (SQLite for free account)
# Use absolute path for PythonAnywhere
DATABASE_URL=sqlite:////home/oldtimers/savings-system/instance/oldtimerssavings.db
# OR use relative path (will be converted to absolute automatically):
# DATABASE_URL=sqlite:///instance/oldtimerssavings.db

# Application Settings
APP_NAME=Old Timers Savings Club Kiteezi
BASE_URL=https://oldtimers.pythonanywhere.com

# Session Configuration
# IMPORTANT: Set to True for production HTTPS, False for local HTTP development
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_SAMESITE=Lax
PERMANENT_SESSION_LIFETIME=1800

# System Configuration
MEMBERSHIP_FEE=20000
MONTHLY_CONTRIBUTION=100000
BEREAVEMENT_AMOUNT=500000
LOAN_INTEREST_RATE=5.00
LOAN_MAX_PERIOD=2
QUALIFICATION_PERIOD=5
TIMEZONE=Africa/Kampala

# Email Configuration (Gmail example)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=CLouds#122
MAIL_DEFAULT_SENDER=Old Timers Savings Club <noreply@oldtimerssavings.org>

# Optional: SMS Configuration (Africa's Talking)
SMS_ENABLED=False
SMS_API_URL=https://api.africastalking.com/version1/messaging
SMS_API_KEY=atsk_9cb2059497df47f74dfc948284b7f8da3c862a523ced1f1773ce8251411ab730f51fd350
SMS_SENDER_ID=OTSC

# Optional: WhatsApp Configuration
WHATSAPP_ENABLED=False
WHATSAPP_API_URL=https://graph.facebook.com/v17.0
WHATSAPP_API_TOKEN=your-token
WHATSAPP_PHONE_ID=your-phone-id
```

**Important**:
- Change `SECRET_KEY` to a random string
- Update `BASE_URL` with your PythonAnywhere username
- Use Gmail App Password (not regular password)
- Save: Ctrl+X, then Y, then Enter

---

## Step 6: Initialize Database

### 6.1 Create Instance Directory

```bash
mkdir -p instance
```

### 6.2 Initialize Database

```bash
# Open Flask shell
flask shell
```

In the Flask shell:
```python
from app import db
db.create_all()
exit()
```

### 6.3 Run Migrations

```bash
# Run due date migration
python migrations/add_loan_due_date.py --auto
```

---

## Step 7: Create Web App

### 7.1 Go to Web Tab

1. In PythonAnywhere dashboard, click "Web" tab
2. Click "Add a new web app"
3. Choose your domain: `yourusername.pythonanywhere.com`
4. Select "Manual configuration"
5. Choose Python 3.10

### 7.2 Configure WSGI File

1. In Web tab, find "Code" section
2. Click on WSGI configuration file link
3. Delete all existing content
4. Add this configuration:

```python
import sys
import os
from dotenv import load_dotenv

# Add your project directory to the sys.path
project_home = '/home/yourusername/savings-system'
if project_home not in sys.path:
    sys.path = [project_home] + sys.path

# Load environment variables
load_dotenv(os.path.join(project_home, '.env'))

# Import Flask app
from app import create_app
application = create_app()
```

**Replace** `yourusername` with your PythonAnywhere username.

Save the file (Ctrl+S or click Save).

### 7.3 Configure Virtual Environment

In Web tab, "Virtualenv" section:
1. Click "Enter path to a virtualenv"
2. Enter: `/home/yourusername/.virtualenvs/savings-env`
3. Click checkmark

### 7.4 Configure Static Files

In Web tab, "Static files" section, add:

| URL | Directory |
|-----|-----------|
| /static/ | /home/yourusername/savings-system/app/static/ |

Click the checkmark to save.

---

## Step 8: Set Up Upload Directories

```bash
# Create upload directories
mkdir -p app/static/uploads/collateral
mkdir -p app/static/uploads/disbursements
mkdir -p app/static/uploads/profiles

# Set permissions (if needed)
chmod 755 app/static/uploads
chmod 755 app/static/uploads/collateral
chmod 755 app/static/uploads/disbursements
chmod 755 app/static/uploads/profiles
```

---

## Step 9: Reload Web App

1. In Web tab, scroll to top
2. Click green "Reload" button
3. Wait for reload to complete (green checkmark)

---

## Step 10: Test Deployment

### 10.1 Access Your Site

Visit: `https://yourusername.pythonanywhere.com`

### 10.2 Create Super Admin User

**Option 1: Using the CLI Command (Recommended)**

In PythonAnywhere Bash console:

```bash
cd ~/savings-system
workon savings-env
flask create-superadmin
```

Follow the prompts to enter:
- Username (e.g., `admin`)
- Phone number (e.g., `0700000000`)
- Email (default: `admin@oldtimerssavings.org`)
- Full name (default: `System Administrator`)
- Password (will be hidden, requires confirmation)

**Option 2: Manual Creation via Flask Shell**

In PythonAnywhere Bash console:

```bash
cd ~/savings-system
workon savings-env
flask shell
```

In Flask shell:
```python
from app import db
from app.models.user import User
from app.models.member import Member
from datetime import date

# First, create a Member for the admin
admin_member = Member(
    full_name='System Administrator',
    phone_primary='0700000000',
    email='admin@oldtimerssavings.org',
    date_joined=date.today(),
    status='Active',
    membership_fee_paid=True
)

db.session.add(admin_member)
db.session.flush()  # Get the member ID

# Now create the User linked to this member
admin_user = User(
    member_id=admin_member.id,
    username='admin',
    role='SuperAdmin'
)
admin_user.set_password('ChangeThisPassword123!')

db.session.add(admin_user)
db.session.commit()

print(f"Admin created: {admin_user.username} (Member: {admin_member.full_name})")
exit()
```

### 10.3 Test Login

1. Go to your site
2. Click "Login"
3. Use credentials:
   - Username: `admin`
   - Password: `ChangeThisPassword123!`
4. **Change password immediately** after first login!

---

## Step 11: Set Up Scheduled Tasks

### For Loan Reminders (Daily at 8:00 AM)

1. In PythonAnywhere dashboard, click "Tasks" tab
2. Add a new scheduled task:
   - **Time**: 08:00 (8:00 AM, UTC time - adjust for your timezone)
   - **Command**:
     ```bash
     /home/oldtimers/.virtualenvs/savings-env/bin/flask send-loan-reminders
     ```
   - **Working directory**: `/home/yourusername/savings-system`
3. Click "Create"

**Note**:
- Free accounts get 1 scheduled task
- Paid accounts get more
- Times are in UTC - calculate your local time offset

---

## Step 12: Configure Logging

### 12.1 Create Logs Directory

```bash
mkdir -p logs
chmod 755 logs
```

### 12.2 View Logs

```bash
# Application logs
tail -f /var/log/oldtimers.pythonanywhere.com.error.log

# Scheduled task logs (after they run)
cat /home/yourusername/savings-system/logs/loan_reminders.log
```

---

## Database Management

### Clear Database Data

If you need to remove test data or start fresh while keeping your admin account:

```bash
cd ~/savings-system
workon savings-env
flask clear-database
```

The command will:
- Ask for confirmation (type `y` to proceed)
- Delete all members, contributions, loans, meetings, etc.
- **Keep the super admin account** and its associated member record
- Reset the admin member's statistics (contributions, qualification status, etc.)
- Show a summary of deleted records

**Warning**: This action cannot be undone! Make sure you have a backup if needed.

To delete **everything** including the admin account:
```bash
# This will require you to create a new admin account after
# Note: By default, --keep-admin is True, so you don't need to specify it
# To delete admin too, run without the flag or explicitly set it to false
flask clear-database
# Then when prompted, the admin will be kept by default

# If you want to skip the admin preservation (advanced use case):
# You would need to modify the command parameters
```

**Note**: The command keeps the admin by default. This is the safest option.

---

## Troubleshooting

### Issue: 500 Internal Server Error

**Check error log**:
```bash
tail -50 /var/log/yourusername.pythonanywhere.com.error.log
```

**Common causes**:
- Wrong Python version in WSGI file
- Missing dependencies in requirements.txt
- Database not initialized
- Wrong file paths in WSGI configuration

### Issue: Static Files Not Loading

**Solution**:
1. Check static files configuration in Web tab
2. Verify path: `/home/yourusername/savings-system/app/static/`
3. Reload web app

### Issue: Database Errors

**Error: "unable to open database file"**

This means SQLite cannot create or access the database file, usually due to:
1. Missing instance directory
2. Incorrect permissions
3. Wrong database path in .env

**Solution**:
```bash
cd ~/savings-system
workon savings-env

# Create instance directory with proper permissions
mkdir -p instance
chmod 755 instance

# Verify your .env has the correct DATABASE_URL
# Should be either:
# DATABASE_URL=sqlite:////home/oldtimers/savings-system/instance/oldtimerssavings.db
# OR
# DATABASE_URL=sqlite:///instance/oldtimerssavings.db (will be converted to absolute)

# Initialize database
flask shell
```

```python
from app import db
db.create_all()
exit()
```

Then reload web app.

**Other database errors**:
```bash
cd ~/savings-system
workon savings-env
flask shell
```

```python
from app import db
db.create_all()
exit()
```

Then reload web app.

### Issue: Import Errors

**Solution**:
```bash
workon savings-env
pip install -r requirements.txt --upgrade
```

Then reload web app.

### Issue: Cannot Login on Mobile/Smartphone (Works on Laptop)

**Symptoms**: Login works on laptop but fails on smartphone with same credentials.

**Cause**: Session cookie configuration issue. The `SESSION_COOKIE_SECURE` setting affects how cookies are sent.

**Solution**:

1. Check your `.env` file on PythonAnywhere:
```bash
nano .env
```

2. Ensure you have these session settings:
```bash
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_SAMESITE=Lax
```

3. **Important**: Make sure you're accessing via HTTPS on your phone:
   - ✅ Correct: `https://oldtimers.pythonanywhere.com`
   - ❌ Wrong: `http://oldtimers.pythonanywhere.com` (no 's')

4. If still not working, try setting `SESSION_COOKIE_SAMESITE=None` temporarily:
```bash
SESSION_COOKIE_SAMESITE=None
```

5. Clear browser cache/cookies on your smartphone:
   - Safari (iOS): Settings > Safari > Clear History and Website Data
   - Chrome (Android): Settings > Privacy > Clear browsing data

6. Reload the web app on PythonAnywhere

7. Try logging in again from your smartphone

**Note**: The default `SESSION_COOKIE_SECURE=False` in development allows HTTP (localhost). In production with HTTPS, it should be `True`.

### Issue: Scheduled Task Not Running

**Solution**:
1. Check task is created in Tasks tab
2. Verify time is correct (UTC)
3. Check task output in task history
4. Free accounts: Ensure you're within daily quota

---

## Performance Optimization

### For Free Accounts

1. **Use SQLite** (included)
2. **Minimize external API calls** (disable SMS/WhatsApp if not needed)
3. **Cache static files** (PythonAnywhere does this automatically)

### For Paid Accounts

Consider upgrading to:
- PostgreSQL database (more robust)
- More scheduled tasks
- Longer-running processes
- Custom domains

---

## Database Backups

### Manual Backup

```bash
cd ~/savings-system
cp instance/oldtimerssavings.db backups/backup-$(date +%Y%m%d).db
```

### Automated Backup Script

Create `backup.sh`:
```bash
#!/bin/bash
cd /home/yourusername/savings-system
mkdir -p backups
cp instance/oldtimerssavings.db backups/backup-$(date +%Y%m%d-%H%M).db

# Keep only last 30 days
find backups/ -name "backup-*.db" -mtime +30 -delete
```

Add as scheduled task (daily at midnight):
```bash
/bin/bash /home/yourusername/savings-system/backup.sh
```

---

## Security Checklist

After deployment:

- [ ] Changed SECRET_KEY to random value
- [ ] Using Gmail App Password (not regular password)
- [ ] SESSION_COOKIE_SECURE=True
- [ ] Changed default admin password
- [ ] Email notifications working
- [ ] HTTPS enabled (automatic on PythonAnywhere)
- [ ] Database backups configured
- [ ] Error logs monitored
- [ ] Scheduled tasks tested

---

## Updating the Application

### When You Make Changes

**On local machine**:
```bash
git add .
git commit -m "Description of changes"
git push origin main
```

**On PythonAnywhere**:
```bash
cd ~/savings-system
git pull origin main
workon savings-env
pip install -r requirements.txt --upgrade
```

**In Web tab**:
- Click "Reload" button

---

## Monitoring

### Daily Checks

```bash
# Check error logs
tail -20 /var/log/yourusername.pythonanywhere.com.error.log

# Check scheduled task logs
cat logs/loan_reminders.log

# Check database size
du -h instance/oldtimerssavings.db
```

### Weekly Checks

```bash
# Check for overdue loans
flask check-overdue-loans

# Check upcoming loans
flask check-upcoming-loans --days 7
```

---

## Cost Considerations

### Free Account
- ✅ One web app
- ✅ 512 MB storage
- ✅ One scheduled task per day
- ✅ HTTPS included
- ❌ No custom domain
- ❌ Limited CPU

**Suitable for**: Testing, small groups (<50 members)

### Paid Accounts (Hacker Plan: $5/month)
- ✅ Multiple web apps
- ✅ More storage
- ✅ More scheduled tasks
- ✅ Custom domains
- ✅ Better CPU allocation
- ✅ MySQL/PostgreSQL databases

**Suitable for**: Production use, larger groups

---

## Support Resources

### PythonAnywhere Help
- Forums: https://www.pythonanywhere.com/forums/
- Help pages: https://help.pythonanywhere.com/
- Email: support@pythonanywhere.com

### Application Documentation
- See `docs/INDEX.md` for all documentation
- Email setup: `docs/NOTIFICATION_CONFIGURATION.md`
- Loan reminders: `docs/README_LOAN_REMINDERS.md`

---

## Quick Reference Commands

```bash
# Navigate to project
cd ~/savings-system

# Activate virtual environment
workon savings-env

# Update code
git pull origin main

# Install/update packages
pip install -r requirements.txt

# Create super admin user
flask create-superadmin

# Clear database (keeps super admin)
flask clear-database

# Open Flask shell
flask shell

# View error logs
tail -f /var/log/yourusername.pythonanywhere.com.error.log

# Check scheduled tasks
flask send-loan-reminders
flask check-overdue-loans
flask check-upcoming-loans
```

---

## Deployment Checklist

Complete deployment steps:

### Pre-Deployment
- [ ] All changes committed and pushed to Git
- [ ] requirements.txt up to date
- [ ] Documentation reviewed
- [ ] Database migrations tested locally

### On PythonAnywhere
- [ ] Repository cloned
- [ ] Virtual environment created
- [ ] Dependencies installed
- [ ] .env file configured
- [ ] Database initialized
- [ ] Migrations run
- [ ] WSGI file configured
- [ ] Virtual environment path set
- [ ] Static files configured
- [ ] Upload directories created
- [ ] Web app reloaded

### Post-Deployment
- [ ] Site accessible via HTTPS
- [ ] Admin user created
- [ ] Login tested
- [ ] Admin password changed
- [ ] Email configuration tested
- [ ] Scheduled task created
- [ ] Logs checked
- [ ] Backup strategy implemented

### Optional
- [ ] Custom domain configured (paid)
- [ ] SMS enabled
- [ ] WhatsApp enabled
- [ ] Additional users created

---

## Summary

**Deployment Steps**:
1. Prepare repository
2. Clone to PythonAnywhere
3. Set up virtual environment
4. Configure .env
5. Initialize database
6. Configure WSGI
7. Set static files path
8. Reload web app
9. Create admin user
10. Set up scheduled tasks
11. Test everything

**Your Site**: `https://yourusername.pythonanywhere.com`

**Mobile Access**: Fully optimized for smartphones and tablets!

**Status**: Ready to deploy! 🚀

### Important Notes

✅ **Mobile-Optimized**: The system is now fully responsive and works great on smartphones
✅ **HTTPS Enabled**: Secure access from any device
✅ **Session Management**: Proper cookie configuration for mobile browsers
✅ **Touch-Friendly**: All buttons and forms optimized for touch screens

For detailed documentation, see:
- `docs/INDEX.md` - Main documentation index
- `docs/MOBILE_OPTIMIZATION.md` - Mobile usage guide
- `docs/MOBILE_LOGIN_TROUBLESHOOTING.md` - Mobile login issues
