# PythonAnywhere Loan Interest Rate Migration Guide

## Your Setup Details
- **Username**: `oldtimers`
- **Virtual Environment**: `/home/oldtimers/.virtualenvs/savings-env`
- **Project Path**: `/home/oldtimers/savings-system`
- **Domain**: `https://oldtimers.pythonanywhere.com`

---

## Step 1: Run the Migration Script

1. **Log into PythonAnywhere** → Dashboard
2. **Open Bash Console** (right menu → "Consoles" → "Bash Console")
3. **Run these commands**:

```bash
cd /home/oldtimers/savings-system
source /home/oldtimers/.virtualenvs/savings-env/bin/activate
python migrations/update_loan_interest_rates.py 3.50 --auto
```

### Expected Output:
```
================================================================================
LOAN INTEREST RATE UPDATE MIGRATION
================================================================================
...
================================================================================
MIGRATION COMPLETED SUCCESSFULLY!
================================================================================

Updated: X loan(s)
Interest rate: 3.50%
Log file: /home/oldtimers/savings-system/migrations/loan_interest_rate_update_YYYY-MM-DD_HH-MM-SS.log
```

---

## Step 2: Update Environment Variables

1. **Edit the .env file**:
```bash
nano /home/oldtimers/savings-system/.env
```

2. **Find this line**:
```
LOAN_INTEREST_RATE=5.00
```

3. **Change it to**:
```
LOAN_INTEREST_RATE=3.50
```

4. **Save** (Ctrl+O, Enter, Ctrl+X)

---

## Step 3: Reload the Web App

1. **Go to PythonAnywhere Web Tab**: https://www.pythonanywhere.com/user/oldtimers/webapps/
2. **Click the "Reload" button** for your web app
3. **Wait 2-3 seconds** for it to reload

---

## Step 4: Verify the Changes

### Option A: Check via CLI
```bash
cd /home/oldtimers/savings-system
source /home/oldtimers/.virtualenvs/savings-env/bin/activate
python -c "from app import create_app; app = create_app(); print(f'Loan Interest Rate: {app.config.get(\"LOAN_INTEREST_RATE\")}%')"
```

Expected output: `Loan Interest Rate: 3.5%`

### Option B: Check in Browser
1. Visit: https://oldtimers.pythonanywhere.com/admin/settings
2. Look for **LOAN_INTEREST_RATE** setting
3. Should show: **3.50**

### Option C: Create a New Loan
1. Apply for a new loan
2. Verify it uses the new 3.50% rate

---

## Step 5: View Migration Log

To see details of what was updated:

```bash
ls -lt /home/oldtimers/savings-system/migrations/loan_interest_rate_update*.log
tail -50 /home/oldtimers/savings-system/migrations/loan_interest_rate_update_2026-*.log
```

---

## Rollback (If Needed)

If you need to revert to the previous rate:

```bash
cd /home/oldtimers/savings-system
source /home/oldtimers/.virtualenvs/savings-env/bin/activate
python migrations/update_loan_interest_rates.py 5.00 --auto
```

Then update `.env` with `LOAN_INTEREST_RATE=5.00` and reload the web app.

---

## Troubleshooting

### Migration script not found
- Ensure you're in the correct directory: `/home/oldtimers/savings-system`
- Check: `ls migrations/update_loan_interest_rates.py`

### Virtual environment not activating
```bash
source /home/oldtimers/.virtualenvs/savings-env/bin/activate
```

### Web app still showing old rate
- Clear browser cache (Ctrl+Shift+Del)
- Check that .env was updated: `cat /home/oldtimers/savings-system/.env | grep LOAN_INTEREST_RATE`
- Verify web app was reloaded

### Check error logs
```bash
tail -50 /var/log/oldtimers.pythonanywhere.com.error.log
```

---

## Quick Reference Commands

```bash
# Activate environment
source /home/oldtimers/.virtualenvs/savings-env/bin/activate

# Navigate to project
cd /home/oldtimers/savings-system

# Run migration to 3.50%
python migrations/update_loan_interest_rates.py 3.50 --auto

# Run migration to 5.00% (revert)
python migrations/update_loan_interest_rates.py 5.00 --auto

# View .env setting
grep LOAN_INTEREST_RATE /home/oldtimers/savings-system/.env

# Check current app config
python -c "from app import create_app; app = create_app(); print(f'Rate: {app.config[\"LOAN_INTEREST_RATE\"]}%')"

# View migration logs
ls -lt /home/oldtimers/savings-system/migrations/loan_interest_rate_update*.log
```
