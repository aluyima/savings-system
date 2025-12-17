# Quick Start Guide: Guarantor Approval Workflow

## Step 1: Run Database Migration

```bash
cd /home/alex/savings-system
python migrations/add_guarantor_approval_fields.py
```

When prompted, type `yes` to proceed.

---

## Step 2: Configure Email Notifications (Minimum Setup)

### Option A: Using Gmail

1. Create a Gmail app password:
   - Go to Google Account settings
   - Security → 2-Step Verification → App passwords
   - Generate password for "Mail"

2. Update your `.env` file:
```bash
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password-here
BASE_URL=http://localhost:5000
```

3. Update `config.py` (if not already configured):
```python
MAIL_SERVER = 'smtp.gmail.com'
MAIL_PORT = 587
MAIL_USE_TLS = True
MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
MAIL_DEFAULT_SENDER = 'Old Timers Savings Club <noreply@oldtimerssavings.org>'
BASE_URL = os.environ.get('BASE_URL', 'http://localhost:5000')
```

### Option B: Skip Email for Now (Testing Only)

The system will work without email, but guarantors won't receive notifications. They'll need to manually check their dashboard.

---

## Step 3: Test the Workflow

### 3.1 Create Test Users (If Needed)

```bash
flask shell
```

```python
from app import db
from app.models.user import User
from app.models.member import Member

# Get three members
member1 = Member.query.filter_by(member_number='M-2025-0001').first()  # Applicant
member2 = Member.query.filter_by(member_number='M-2025-0002').first()  # Guarantor 1
member3 = Member.query.filter_by(member_number='M-2025-0003').first()  # Guarantor 2

print(f"Applicant: {member1.full_name if member1 else 'Not found'}")
print(f"Guarantor 1: {member2.full_name if member2 else 'Not found'}")
print(f"Guarantor 2: {member3.full_name if member3 else 'Not found'}")
```

### 3.2 Test Loan Application

1. **Login as Member** (applicant)
2. Go to **Loans → Apply for Loan**
3. Fill in loan details:
   - Amount: UGX 500,000
   - Purpose: "Business expansion"
   - Repayment Period: 2 months
   - Security Type: **Guarantors**
   - Select 2 different members as guarantors
4. Submit application
5. Check status: Should be "Pending Guarantor Approval"

### 3.3 Test Guarantor Approval

1. **Logout**
2. **Login as Guarantor 1**
3. Check dashboard → Should see "Pending Guarantor Approval Requests" section
4. Click "Review & Respond"
5. Review loan details
6. Click "Approve as Guarantor"
7. Check status: Still "Pending Guarantor Approval" (waiting for Guarantor 2)

8. **Logout**
9. **Login as Guarantor 2**
10. Approve the loan
11. Check status: Now "Pending Executive Approval"

### 3.4 Test Executive Approval

1. **Logout**
2. **Login as Executive** (who is NOT a guarantor)
3. Go to **Loans → View All Loans**
4. Click on the test loan
5. Should see "Executive Actions" section
6. Enter approved amount and notes
7. Click "Approve Loan"
8. Status changes to "Approved"

### 3.5 Test Executive Restriction (Important!)

1. **Logout**
2. **Login as Executive** who IS one of the guarantors
3. View the same loan
4. Should see red error message:
   - "You cannot approve this loan!"
   - "You are a guarantor for this loan. Another executive must approve it."
5. Approval form should NOT be visible

### 3.6 Test Guarantor Rejection

1. Create another test loan with 2 guarantors
2. Login as one of the guarantors
3. View the loan
4. Enter a rejection reason (e.g., "Insufficient information about repayment plan")
5. Click "Decline as Guarantor"
6. Check status: Should be "Returned to Applicant"
7. Applicant should be able to see rejection reason

---

## Step 4: Verify Dashboard Display

### Member Dashboard
- Login as a member who is selected as a guarantor
- Should see yellow warning card: "Pending Guarantor Approval Requests"
- Badge shows count of pending requests
- Table shows loan details and "Review & Respond" button

### Loan View
- Guarantor section shows approval status for each guarantor:
  - Green badge: ✓ Approved (with timestamp)
  - Red badge: ✗ Declined (with reason)
  - Yellow badge: ⏳ Pending

---

## Step 5: Check Audit Logs

```bash
flask shell
```

```python
from app.models.audit import AuditLog

# View recent guarantor actions
logs = AuditLog.query.filter(
    AuditLog.action_type.in_(['GuarantorApproved', 'GuarantorDeclined'])
).order_by(AuditLog.timestamp.desc()).limit(10).all()

for log in logs:
    print(f"{log.timestamp} - {log.user.username}: {log.description}")
```

---

## Step 6: (Optional) Add SMS Notifications

### Using Africa's Talking

1. Sign up at https://africastalking.com
2. Get API key
3. Update `.env`:
```bash
SMS_ENABLED=True
SMS_API_URL=https://api.africastalking.com/version1/messaging
SMS_API_KEY=your-api-key-here
SMS_SENDER_ID=OTSC
```

4. Update `config.py`:
```python
SMS_ENABLED = os.environ.get('SMS_ENABLED', 'False') == 'True'
SMS_API_URL = os.environ.get('SMS_API_URL')
SMS_API_KEY = os.environ.get('SMS_API_KEY')
SMS_SENDER_ID = os.environ.get('SMS_SENDER_ID', 'OTSC')
```

5. Ensure members have phone numbers in `phone_primary` field

---

## Troubleshooting

### Email Not Sending
```bash
flask shell
```
```python
from flask_mail import Message
from app import mail

msg = Message(
    'Test Email',
    recipients=['test@example.com'],
    body='This is a test'
)
mail.send(msg)
# Check for errors
```

### Guarantors Not Receiving Notifications
1. Check member email addresses in database
2. Check spam folder
3. Verify MAIL_USERNAME and MAIL_PASSWORD are correct
4. Check Flask logs for error messages

### Status Not Changing
- Check that both guarantors have approved (for "Pending Executive Approval")
- Verify database updates: `SELECT * FROM loans WHERE id = X;`
- Check audit logs for actions

### Executive Cannot Approve
- Verify the executive is not a guarantor on the loan
- Check that status is "Pending Executive Approval"
- For guarantor loans, ensure both guarantors approved

---

## New Loan Statuses

| Status | Description |
|--------|-------------|
| **Pending Guarantor Approval** | Waiting for both guarantors to approve |
| **Returned to Applicant** | A guarantor declined; member needs to resubmit |
| **Pending Executive Approval** | Both guarantors approved; waiting for executive |
| **Approved** | Executive approved; ready for disbursement |
| **Disbursed / Active** | Loan money given to member |
| **Completed** | Fully repaid |
| **Rejected** | Application rejected by executives |

---

## Key Features Summary

✅ **Guarantor Workflow**: Both guarantors must approve before executive approval
✅ **Notifications**: Email/SMS/WhatsApp to guarantors and applicants
✅ **Executive Restrictions**: Executives who are guarantors cannot approve
✅ **Dashboard Integration**: Guarantors see pending requests prominently
✅ **Rejection Handling**: Loans return to applicant with reason
✅ **Audit Trail**: All actions logged with timestamp and user
✅ **Status Tracking**: Clear visual indicators throughout

---

## Need Help?

1. Check `GUARANTOR_APPROVAL_IMPLEMENTATION.md` for detailed documentation
2. Check `NOTIFICATION_CONFIGURATION.md` for notification setup
3. Review audit logs for troubleshooting
4. Test in development environment first

---

**Ready to Test!** 🎉

Start with Step 1 (database migration) and work your way through the testing steps.
