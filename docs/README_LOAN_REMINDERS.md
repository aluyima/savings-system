# Loan Due Date & Automated Reminder System

## Quick Start

### 1. Run Database Migration
```bash
cd /home/alex/savings-system
python migrations/add_loan_due_date.py
```
Type `yes` when prompted.

### 2. Install Dependency
```bash
source venv/bin/activate
pip install python-dateutil==2.8.2
```

### 3. Test the System
```bash
flask send-loan-reminders
```

### 4. Set Up Daily Automation
```bash
# Make script executable
chmod +x send_loan_reminders.sh

# Create logs directory
mkdir -p logs

# Add to crontab (runs daily at 8:00 AM)
crontab -e
```
Add this line:
```
0 8 * * * /home/alex/savings-system/send_loan_reminders.sh >> /home/alex/savings-system/logs/loan_reminders.log 2>&1
```

## What It Does

✅ **Automatic Due Date**: Calculated when loan is disbursed (disbursement_date + repayment_period_months)

✅ **Daily Reminders**: Sends notifications one day before due date to:
- Borrower (Email/SMS/WhatsApp)
- All executives (Email/SMS)

✅ **Visual Indicators**: Loan view shows due date with badges:
- 🔴 Red: Overdue
- 🟡 Yellow: Due today/tomorrow
- 🔵 Blue: Due within 7 days

✅ **Management Commands**:
```bash
flask send-loan-reminders      # Send reminders for loans due tomorrow
flask check-overdue-loans       # List overdue loans
flask check-upcoming-loans      # Show loans due soon
```

## Configuration

### Email (Required)
Add to `.env`:
```bash
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
BASE_URL=http://localhost:5000
```

### SMS/WhatsApp (Optional)
See [LOAN_REMINDER_SETUP.md](LOAN_REMINDER_SETUP.md) for details.

## Files

- 📄 **FEATURE_LOAN_DUE_DATE_REMINDERS.md** - Complete technical documentation
- 📄 **LOAN_REMINDER_SETUP.md** - Detailed setup guide with troubleshooting
- 📄 **README_LOAN_REMINDERS.md** - This file (quick reference)

## Support

For issues:
1. Check logs: `tail -f logs/loan_reminders.log`
2. Review setup guide: `LOAN_REMINDER_SETUP.md`
3. Read full documentation: `FEATURE_LOAN_DUE_DATE_REMINDERS.md`

**Status**: ✅ Ready for production
