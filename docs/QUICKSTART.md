# Old Timers Savings Group - Quick Start Guide

## Prerequisites
- Python 3.8+ installed
- Virtual environment created and dependencies installed (`pip install -r requirements.txt`)

## Quick Setup (3 Steps)

### Option 1: Automated Setup Script
Run the setup script that does everything for you:

```bash
./setup.sh
```

This will:
1. Check your virtual environment
2. Initialize the database
3. Create the first admin user
4. Show you how to start the app

---

### Option 2: Manual Setup

#### Step 1: Activate Virtual Environment
```bash
source venv/bin/activate
```

You should see `(venv)` at the beginning of your prompt.

#### Step 2: Set Flask App Environment Variable
```bash
export FLASK_APP=run.py
```

#### Step 3: Initialize Database
```bash
flask init-db
```

You should see:
```
✓ Database initialized successfully!
✓ System settings initialized
```

#### Step 4: Create Super Admin User
```bash
flask create-admin
```

You'll be prompted for:
- **Full Name**: e.g., "Alex Smith"
- **Phone Number**: e.g., "0756123456" (this becomes your username)
- **Email Address**: e.g., "admin@example.com" (optional)
- **Initial Password**: Must be at least 8 characters
- **Confirm Password**: Re-enter the same password

Example:
```
==================================================
Creating Super Admin Account
==================================================
Full Name [System Administrator]: Alex Smith
Phone Number (e.g., 0700000000) [0700000000]: 0756123456
Email Address (optional):
 admin@oldtimers.org
Initial Password (min 8 characters):
Confirm Password:

==================================================
✓ Super Admin created successfully!
==================================================
Username: 0756123456
Member Number: OT-001

⚠️  You will be required to change your password on first login.

To start the application, run: flask run
Then visit: http://127.0.0.1:5000
==================================================
```

#### Step 5: Run the Application
```bash
flask run
```

Or alternatively:
```bash
python run.py
```

You should see:
```
 * Running on http://127.0.0.1:5000
```

#### Step 6: Access the Application
Open your web browser and go to:
```
http://127.0.0.1:5000
```

Login with:
- **Username**: Your phone number (e.g., `0756123456`)
- **Password**: Your initial password

**Important**: You'll be required to change your password on first login.

---

## All Commands in Sequence

For a fresh setup, here's the complete command sequence:

```bash
# Navigate to project directory
cd /home/alex/savings-system

# Activate virtual environment
source venv/bin/activate

# Set Flask app
export FLASK_APP=run.py

# Initialize database
flask init-db

# Create admin user (interactive)
flask create-admin

# Run the application
flask run
```

---

## Available Flask Commands

| Command | Description |
|---------|-------------|
| `flask init-db` | Initialize database tables and system settings |
| `flask create-admin` | Create the first Super Admin user (interactive) |
| `flask run` | Start the development server |
| `flask shell` | Open Python shell with app context |

---

## Troubleshooting

### Problem: "flask: command not found"
**Solution**: Activate your virtual environment
```bash
source venv/bin/activate
```

### Problem: "Could not locate a Flask application"
**Solution**: Set the FLASK_APP environment variable
```bash
export FLASK_APP=run.py
```

### Problem: "Super Admin already exists"
**Solution**: An admin was already created. Check the database or delete it to start over:
```bash
rm instance/oldtimerssavings.db
flask init-db
flask create-admin
```

### Problem: Can't remember admin password
**Solution**: You'll need to delete the database and recreate it, or manually reset the password in the database.

### Problem: Port 5000 already in use
**Solution**: Run Flask on a different port:
```bash
flask run --port 5001
```

---

## Next Steps

After logging in successfully:

1. **Change your password** (required on first login)
2. **Explore the Executive Dashboard** to see statistics and pending actions
3. **Add more members** (Phase 2 - Coming soon)
4. **Record contributions** (Phase 3 - Coming soon)

---

## System Configuration

The system uses default values from the specification:
- Membership Fee: UGX 20,000
- Monthly Contribution: UGX 100,000
- Bereavement Amount: UGX 500,000
- Loan Interest Rate: 5% per month
- Maximum Loan Period: 2 months
- Quorum Requirement: 5 members
- Qualification Period: 5 consecutive months

These can be modified in the `.env` file or through the System Settings interface (SuperAdmin only).

---

## Database Location

The SQLite database is created at:
```
instance/oldtimerssavings.db
```

---

## Need Help?

Refer to the full [README.md](README.md) for detailed documentation.
