# ✅ Loan Due Date & Reminder System - Installation Complete

## What Was Installed

### 1. Database Migration ✅
- Added `due_date` column to loans table
- Calculated due dates for 3 existing disbursed loans
- Migration completed successfully

### 2. Dependencies Installed ✅
- `python-dateutil==2.8.2` - For date calculations
- `six==1.17.0` - Required dependency

### 3. System Verified ✅
All Flask CLI commands working:
- ✅ `flask send-loan-reminders` - Ready to send notifications
- ✅ `flask check-overdue-loans` - No overdue loans currently
- ✅ `flask check-upcoming-loans` - No loans due in next 30 days

---

## Next Steps

### Step 1: Configure Email Notifications (Required)

Edit your `.env` file and add/update these settings:

```bash
# Email Configuration (Required for notifications)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-gmail-app-password
MAIL_DEFAULT_SENDER=Old Timers Savings Club <noreply@oldtimerssavings.org>
BASE_URL=http://localhost:5000
```

**Important**:
- For Gmail, you need an "App Password" (not your regular password)
- Go to: Google Account → Security → 2-Step Verification → App passwords
- Generate a password for "Mail"

### Step 2: Set Up Daily Automation

#### Create logs directory:
```bash
mkdir -p logs
```

#### Make script executable:
```bash
chmod +x send_loan_reminders.sh
```

#### Set up cron job:
```bash
crontab -e
```

Add this line (sends reminders daily at 8:00 AM):
```
0 8 * * * /home/alex/savings-system/send_loan_reminders.sh >> /home/alex/savings-system/logs/loan_reminders.log 2>&1
```

Save and exit.

#### Verify cron job:
```bash
crontab -l
```

### Step 3: Test the System

#### Test email configuration:
```bash
flask shell
```

Then in the shell:
```python
from app.utils.notifications import NotificationService
NotificationService.send_email('your-email@gmail.com', 'Test', 'This is a test email')
```

If successful, you'll receive a test email.

#### Test reminder system:
```bash
flask send-loan-reminders
```

You should see:
```
✓ Reminders sent successfully!
```

---

## How It Works

### When a Loan is Disbursed

1. Executive enters disbursement date (e.g., January 15, 2025)
2. System automatically calculates due date:
   - If loan period = 2 months
   - Due date = March 15, 2025
3. Due date is saved and displayed on loan view

### Daily at 8:00 AM

1. Cron job runs: `flask send-loan-reminders`
2. System checks for loans due **tomorrow**
3. For each loan found:
   - Sends email to borrower
   - Sends SMS to borrower (if SMS enabled)
   - Sends WhatsApp to borrower (if WhatsApp enabled)
   - Sends email to all executives
4. Logs results to `logs/loan_reminders.log`

### Visual Indicators

When viewing a loan, the due date shows with color-coded badges:
- 🔴 **Red**: "X days overdue"
- 🟡 **Yellow**: "Due today" or "Due tomorrow"
- 🔵 **Blue**: "Due in X days" (within 7 days)
- ⚪ **None**: More than 7 days away

---

## Testing Checklist

Before going live, test these scenarios:

### ✅ Already Completed
- [x] Migration ran successfully
- [x] Dependencies installed
- [x] CLI commands work
- [x] Due dates calculated for existing loans

### ⏳ To Test
- [ ] Email configuration works (send test email)
- [ ] Disbursing a new loan sets due date correctly
- [ ] Loan view displays due date with correct badge
- [ ] Cron job is configured
- [ ] Cron job runs at scheduled time
- [ ] Logs are created in logs directory
- [ ] Check logs after first automated run

---

## Monitoring

### Daily
Check logs to ensure reminders are being sent:
```bash
tail -20 logs/loan_reminders.log
```

### Weekly
Review upcoming loans:
```bash
flask check-upcoming-loans --days 7
```

Check for overdue loans:
```bash
flask check-overdue-loans
```

### Monthly
Review all loans due in the coming month:
```bash
flask check-upcoming-loans --days 30
```

---

## Optional: SMS & WhatsApp

### SMS Configuration
If you want to send SMS notifications:

1. Sign up for SMS service (e.g., Africa's Talking)
2. Add to `.env`:
```bash
SMS_ENABLED=True
SMS_API_URL=https://api.africastalking.com/version1/messaging
SMS_API_KEY=your-api-key
SMS_SENDER_ID=OTSC
```

### WhatsApp Configuration
If you want to send WhatsApp notifications:

1. Set up WhatsApp Business API
2. Add to `.env`:
```bash
WHATSAPP_ENABLED=True
WHATSAPP_API_URL=https://graph.facebook.com/v17.0
WHATSAPP_API_TOKEN=your-token
WHATSAPP_PHONE_ID=your-phone-id
```

---

## Documentation

Detailed documentation available:

1. **[README_LOAN_REMINDERS.md](README_LOAN_REMINDERS.md)** - Quick reference
2. **[LOAN_REMINDER_SETUP.md](LOAN_REMINDER_SETUP.md)** - Complete setup guide with troubleshooting
3. **[FEATURE_LOAN_DUE_DATE_REMINDERS.md](FEATURE_LOAN_DUE_DATE_REMINDERS.md)** - Full technical documentation

---

## Troubleshooting

### Issue: Reminders not sending
**Solution**: Check email configuration in `.env`, test with `flask shell`

### Issue: Cron job not running
**Solution**:
```bash
sudo service cron status  # Check if cron is running
grep CRON /var/log/syslog  # Check cron logs
```

### Issue: No due dates showing
**Solution**: Disburse a loan and verify due date is calculated

For more help, see [LOAN_REMINDER_SETUP.md](LOAN_REMINDER_SETUP.md)

---

## Summary

✅ **System installed and verified**
✅ **3 existing loans updated with due dates**
✅ **All CLI commands working**
✅ **Ready for email configuration and cron setup**

**Next Action**: Configure email in `.env` and set up cron job for daily automation.

**Status**: Installation complete! 🎉
