## Loan Due Date Reminder System - Setup Guide

## Overview
This system automatically sends payment reminders to borrowers and executives one day before a loan's due date.

---

## Quick Setup

### Step 1: Run Database Migration

```bash
cd /home/alex/savings-system
python migrations/add_loan_due_date.py
```

Type `yes` when prompted. This will:
- Add `due_date` column to loans table
- Calculate due dates for existing disbursed loans

---

### Step 2: Install Required Package

```bash
source venv/bin/activate
pip install python-dateutil==2.8.2
```

---

### Step 3: Test the Notification System

#### Test Reminder Sending (Manual)
```bash
flask send-loan-reminders
```

This checks for loans due tomorrow and sends notifications.

#### Check Overdue Loans
```bash
flask check-overdue-loans
```

#### Check Upcoming Loans (Next 7 Days)
```bash
flask check-upcoming-loans --days 7
```

---

### Step 4: Set Up Automated Daily Reminders

#### Option A: Cron Job (Linux/WSL - Recommended)

1. **Make script executable**:
```bash
chmod +x send_loan_reminders.sh
```

2. **Edit crontab**:
```bash
crontab -e
```

3. **Add this line** (runs daily at 8:00 AM):
```
0 8 * * * /home/alex/savings-system/send_loan_reminders.sh >> /home/alex/savings-system/logs/loan_reminders.log 2>&1
```

4. **Create logs directory**:
```bash
mkdir -p /home/alex/savings-system/logs
```

5. **Verify cron job** is set:
```bash
crontab -l
```

#### Option B: Windows Task Scheduler

1. Create a batch file `send_loan_reminders.bat`:
```batch
@echo off
cd /d C:\path\to\savings-system
call venv\Scripts\activate.bat
flask send-loan-reminders
```

2. Open **Task Scheduler**
3. Create a new **Basic Task**:
   - Name: "Loan Payment Reminders"
   - Trigger: Daily at 8:00 AM
   - Action: Start a program → Select your batch file

#### Option C: systemd Timer (Linux)

Create `/etc/systemd/system/loan-reminders.service`:
```ini
[Unit]
Description=Send Loan Due Date Reminders
After=network.target

[Service]
Type=oneshot
User=alex
WorkingDirectory=/home/alex/savings-system
ExecStart=/home/alex/savings-system/venv/bin/flask send-loan-reminders
```

Create `/etc/systemd/system/loan-reminders.timer`:
```ini
[Unit]
Description=Daily Loan Reminders Timer
Requires=loan-reminders.service

[Timer]
OnCalendar=daily
OnCalendar=08:00
Persistent=true

[Install]
WantedBy=timers.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable loan-reminders.timer
sudo systemctl start loan-reminders.timer
```

---

## How It Works

### 1. Due Date Calculation
When a loan is disbursed:
```
due_date = disbursement_date + repayment_period_months
```

Example:
- Disbursement: January 15, 2025
- Repayment Period: 2 months
- Due Date: March 15, 2025

### 2. Daily Check (Automated)
Every day at the scheduled time:
1. System checks for loans due **tomorrow**
2. For each loan found:
   - Send notification to borrower (Email/SMS/WhatsApp)
   - Send notification to all executives (Email/SMS)

### 3. Notification Content

**To Borrower**:
- Loan number
- Amount borrowed
- Total payable
- Current balance
- Due date

**To Executives**:
- Borrower details
- Loan details
- Link to loan view
- Follow-up reminder

---

## Notification Channels

### Email
- **Always sent** if recipient has email address
- Uses Flask-Mail configuration from `.env`

### SMS (Optional)
- Requires `SMS_ENABLED=True` in `.env`
- Requires SMS API configuration

### WhatsApp (Optional)
- Requires `WHATSAPP_ENABLED=True` in `.env`
- Requires WhatsApp API configuration

---

## Testing Checklist

### Pre-Deployment Testing

1. **Database Migration**
   - [ ] Migration ran successfully
   - [ ] Due dates calculated for existing loans
   - [ ] No errors in migration output

2. **Manual Command Testing**
   - [ ] `flask send-loan-reminders` runs without errors
   - [ ] `flask check-overdue-loans` shows correct data
   - [ ] `flask check-upcoming-loans` shows correct data

3. **Notification Testing**
   - [ ] Email notifications received
   - [ ] SMS notifications received (if enabled)
   - [ ] WhatsApp notifications received (if enabled)
   - [ ] Notifications contain correct loan details

4. **Scheduler Testing**
   - [ ] Cron job/task scheduler configured
   - [ ] Script runs at scheduled time
   - [ ] Logs are created
   - [ ] No permission errors

### Post-Deployment Monitoring

- **Check logs daily** for the first week:
```bash
tail -f /home/alex/savings-system/logs/loan_reminders.log
```

- **Verify notifications** are being sent
- **Monitor for errors** in log file

---

## Troubleshooting

### Issue: "Column due_date does not exist"
**Solution**: Run the migration script:
```bash
python migrations/add_loan_due_date.py
```

### Issue: "ModuleNotFoundError: No module named 'dateutil'"
**Solution**: Install python-dateutil:
```bash
pip install python-dateutil==2.8.2
```

### Issue: Cron job not running
**Solution**:
1. Check cron is enabled: `sudo service cron status`
2. Check logs: `grep CRON /var/log/syslog`
3. Verify script has execute permission: `chmod +x send_loan_reminders.sh`
4. Test script manually: `./send_loan_reminders.sh`

### Issue: Notifications not sending
**Solution**:
1. Check email configuration in `.env`
2. Verify MAIL_USERNAME and MAIL_PASSWORD are correct
3. Check Flask logs for errors
4. Test email manually: `flask shell` then run notification code

### Issue: No loans found but loans exist
**Solution**:
1. Check loan status (must be 'Active' or 'Disbursed')
2. Verify due_date is set for loans
3. Check system date is correct
4. Run: `flask check-upcoming-loans --days 30` to see all upcoming loans

---

## Monitoring & Maintenance

### Daily Monitoring
- Check log file for errors
- Verify notifications are being sent
- Monitor overdue loans

### Weekly Tasks
- Review overdue loans report:
```bash
flask check-overdue-loans
```

### Monthly Tasks
- Review upcoming loans for the month:
```bash
flask check-upcoming-loans --days 30
```

---

## Logs

Logs are stored in: `/home/alex/savings-system/logs/loan_reminders.log`

**Log rotation** (recommended):
Create `/etc/logrotate.d/loan-reminders`:
```
/home/alex/savings-system/logs/loan_reminders.log {
    daily
    rotate 30
    compress
    missingok
    notifempty
}
```

---

## Configuration

### Environment Variables (`.env`)

```bash
# Email (Required for notifications)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
BASE_URL=http://localhost:5000

# SMS (Optional)
SMS_ENABLED=False
SMS_API_URL=https://api.africastalking.com/version1/messaging
SMS_API_KEY=your-sms-api-key
SMS_SENDER_ID=OTSC

# WhatsApp (Optional)
WHATSAPP_ENABLED=False
WHATSAPP_API_URL=https://graph.facebook.com/v17.0
WHATSAPP_API_TOKEN=your-whatsapp-token
WHATSAPP_PHONE_ID=your-phone-id
```

---

## Security Considerations

1. **Protect the script**: Ensure only the app user can execute it
```bash
chmod 750 send_loan_reminders.sh
```

2. **Secure logs**: Restrict log file access
```bash
chmod 640 logs/loan_reminders.log
```

3. **Environment variables**: Never commit `.env` to version control

4. **Email credentials**: Use app-specific passwords, not your main password

---

## Benefits

✅ **Automated Reminders**: No manual tracking needed
✅ **Improved Collection**: Borrowers reminded before due date
✅ **Executive Awareness**: All executives notified automatically
✅ **Audit Trail**: All reminders logged
✅ **Multi-Channel**: Email, SMS, and WhatsApp support
✅ **Scalable**: Handles any number of loans

---

## Summary

1. ✅ Run migration: `python migrations/add_loan_due_date.py`
2. ✅ Install package: `pip install python-dateutil==2.8.2`
3. ✅ Test: `flask send-loan-reminders`
4. ✅ Set up cron: Add to crontab
5. ✅ Monitor: Check logs daily

**Status**: Ready for production use
