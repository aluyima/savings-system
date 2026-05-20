# Guarantor Approval Workflow Implementation

## Overview
This document describes the complete guarantor approval workflow implementation for the Old Timers Savings Club Kiteezi loan system.

## Implementation Date
December 16, 2025

---

## Workflow Description

### Loan Status Flow
```
1. Member applies for loan with 2 guarantors
   ↓
2. Status: "Pending Guarantor Approval"
   - Guarantors receive email/SMS/WhatsApp notifications
   - Guarantors can approve or decline
   ↓
3a. If BOTH guarantors approve:
    → Status: "Pending Executive Approval"
    → Applicant notified via email/SMS/WhatsApp
    → Executives can now approve the loan
    ↓
3b. If ANY guarantor declines:
    → Status: "Returned to Applicant"
    → Applicant notified with reason
    → Member can select new guarantor or switch to collateral
    ↓
4. Executive approves (NOT if they're a guarantor)
   → Status: "Approved"
   ↓
5. Loan disbursed
   → Status: "Active"
   ↓
6. Loan fully repaid
   → Status: "Completed"
```

---

## Key Features Implemented

### 1. Database Changes

**File**: `app/models/loan.py`

**New Fields Added**:
- `guarantor1_approval_date` (DATETIME) - When guarantor 1 approved/declined
- `guarantor2_approval_date` (DATETIME) - When guarantor 2 approved/declined
- `guarantor1_rejection_reason` (TEXT) - Reason if guarantor 1 declined
- `guarantor2_rejection_reason` (TEXT) - Reason if guarantor 2 declined

**Updated Fields**:
- `status` column size increased to VARCHAR(30) to support longer status names
- `guarantor1_approved` and `guarantor2_approved` now use `None` for pending (was `False`)

**New Helper Methods**:
- `both_guarantors_approved()` - Check if both guarantors approved
- `any_guarantor_rejected()` - Check if any guarantor rejected
- `pending_guarantor_approval()` - Check if waiting for guarantor approval

**Migration Script**: `migrations/add_guarantor_approval_fields.py`

---

### 2. Notification System

**File**: `app/utils/notifications.py`

**Notification Class**: `NotificationService`

**Supported Channels**:
- ✅ **Email** (Primary - always enabled via Flask-Mail)
- ✅ **SMS** (Optional - via Africa's Talking or Twilio)
- ✅ **WhatsApp** (Optional - via WhatsApp Business API)

**Notification Types**:
1. **Guarantor Request** - Sent when guarantor is selected
   - Includes loan details, applicant info, login link
   - Sent to both guarantors immediately upon application

2. **Guarantor Approval Complete** - Sent when both guarantors approve
   - Notifies applicant that loan is pending executive approval
   - Includes updated status

3. **Guarantor Rejection** - Sent when guarantor declines
   - Notifies applicant immediately
   - Includes rejection reason
   - Explains options (new guarantor or collateral)

**Configuration**: See `NOTIFICATION_CONFIGURATION.md` for setup instructions

---

### 3. Guarantor Approval Routes

**File**: `app/routes/loans.py`

**New Routes**:

#### `/loans/<id>/guarantor/approve` (POST)
- Allows guarantor to approve loan
- Checks if user is the actual guarantor
- Prevents double-approval
- Updates loan status to "Pending Executive Approval" if both approve
- Sends notifications
- Logs audit trail

#### `/loans/<id>/guarantor/decline` (POST)
- Allows guarantor to decline with reason
- Returns loan to applicant
- Updates status to "Returned to Applicant"
- Sends notifications with reason
- Logs audit trail

**Updated Routes**:

#### `/loans/apply` (POST)
- Sets initial status based on security type:
  - Guarantors → "Pending Guarantor Approval"
  - Collateral → "Pending Executive Approval"
- Sends notifications to guarantors immediately
- Sets `guarantor1_approved` and `guarantor2_approved` to `None` (pending)

#### `/loans/<id>/approve` (POST)
- **NEW VALIDATION**: Checks if guarantors have approved (for guarantor loans)
- **NEW RESTRICTION**: Blocks approval if current executive is a guarantor
- Shows clear error message: "You cannot approve this loan because you are a guarantor!"
- Only allows approval when status is "Pending Executive Approval"

#### `/loans/<id>/reject` (POST)
- Updated to handle new statuses
- Can reject loans in "Pending Guarantor Approval" or "Pending Executive Approval"

---

### 4. Member Dashboard Updates

**File**: `app/routes/main.py`

**New Dashboard Section**: Pending Guarantor Requests

**Query Added**:
```python
guarantor_requests = Loan.query.filter(
    db.or_(
        db.and_(Loan.guarantor1_id == member.id, Loan.guarantor1_approved == None),
        db.and_(Loan.guarantor2_id == member.id, Loan.guarantor2_approved == None)
    ),
    Loan.status.in_(['Pending Guarantor Approval', 'Returned to Applicant'])
).order_by(Loan.created_at.desc()).all()
```

**Updated Loan Query**:
- Now includes all statuses: 'Pending Guarantor Approval', 'Returned to Applicant', 'Pending Executive Approval', 'Approved', 'Active', 'Disbursed'

---

### 5. Dashboard Template Updates

**File**: `app/templates/dashboard/member.html`

**New Section**: "Pending Guarantor Approval Requests"
- Shows as warning card with yellow/orange styling
- Badge showing number of pending requests
- Table with:
  - Loan number
  - Applicant name and member number
  - Amount requested
  - Purpose (truncated)
  - Guarantor role (Guarantor #1 or #2)
  - Status badge
  - "Review & Respond" button

**Styling**:
- Card border: `border-warning`
- Header: `bg-warning text-dark`
- Badge count: `badge bg-dark`
- Alert: `alert-warning` with info icon

---

### 6. Loan View Template Updates

**File**: `app/templates/loans/view.html`

**Updated Status Badges**:
```html
Pending Guarantor Approval → bg-warning (yellow)
Returned to Applicant → bg-secondary (gray)
Pending Executive Approval → bg-info (blue)
Approved → bg-info (blue)
Active/Disbursed → bg-primary (dark blue)
Completed → bg-success (green)
Rejected → bg-danger (red)
```

**Enhanced Guarantor Section**:
- Shows approval status for each guarantor:
  - ✓ Approved (green badge) with timestamp
  - ✗ Declined (red badge) with rejection reason
  - ⏳ Pending (yellow badge)

**New Guarantor Actions Card**:
- Shown only to guarantors for pending approvals
- Yellow warning card with clear call-to-action
- Two forms:
  - Approve button (green, full width)
  - Decline form with required reason textarea (red, full width)
- Shows confirmation message after approval/decline

**Updated Executive Actions**:
- Renamed to "Executive Actions" (was just "Actions")
- **Warning Message**: Shows if guarantors haven't approved yet
  - "This loan cannot be approved until both guarantors approve"
  - Shows current status of both guarantors
- **Error Message**: Shows if current executive is a guarantor
  - "You cannot approve this loan!"
  - "You are a guarantor for this loan. Another executive must approve it."
  - Red danger alert
- Approval form only shown when:
  - Both guarantors have approved (for guarantor loans), OR
  - Loan uses collateral security
  - AND current executive is not a guarantor

---

## Security & Business Rules

### Guarantor Approval Rules
1. ✅ Guarantors must be active members
2. ✅ Both guarantors must approve before executive approval
3. ✅ If ANY guarantor declines, loan returns to applicant
4. ✅ Guarantors can only approve/decline once
5. ✅ Guarantors cannot approve their own loans (prevented at application)

### Executive Approval Rules
1. ✅ Executives cannot approve if they are a guarantor on the loan
2. ✅ System shows clear error message if executive is guarantor
3. ✅ Other executives can still approve
4. ✅ Must wait for guarantor approval (for guarantor-based loans)
5. ✅ Collateral loans bypass guarantor approval

### Notification Rules
1. ✅ Guarantors notified immediately when selected
2. ✅ Applicant notified when both guarantors approve
3. ✅ Applicant notified immediately if guarantor declines
4. ✅ All notifications logged in audit trail

---

## Testing Checklist

### Database Migration
- [ ] Run migration script: `python migrations/add_guarantor_approval_fields.py`
- [ ] Verify new columns exist in `loans` table
- [ ] Check existing loans still work

### Notification Setup
- [ ] Configure email settings in config.py
- [ ] Test email delivery
- [ ] (Optional) Configure SMS provider
- [ ] (Optional) Configure WhatsApp Business API

### Guarantor Workflow
- [ ] Member applies for loan with 2 guarantors
- [ ] Both guarantors receive notifications
- [ ] Guarantor 1 logs in and approves
- [ ] Guarantor 2 logs in and approves
- [ ] Status changes to "Pending Executive Approval"
- [ ] Applicant receives notification

### Guarantor Rejection Workflow
- [ ] Member applies for loan
- [ ] Guarantor logs in and declines with reason
- [ ] Status changes to "Returned to Applicant"
- [ ] Applicant receives notification with reason
- [ ] Member can resubmit with new guarantor

### Executive Restrictions
- [ ] Executive who is a guarantor views loan
- [ ] Error message displayed: "You cannot approve"
- [ ] Approval form hidden
- [ ] Different executive can approve
- [ ] Loan processes normally after approval

### Dashboard Display
- [ ] Member with pending guarantor requests sees warning card
- [ ] Badge shows correct count
- [ ] "Review & Respond" button navigates to loan view
- [ ] After approval/decline, request disappears from dashboard

### Audit Trail
- [ ] Guarantor approval logged
- [ ] Guarantor decline logged with reason
- [ ] Executive approval logged
- [ ] All actions include user, timestamp, IP

---

## Configuration Required

### 1. Email (Required)
Add to `config.py`:
```python
MAIL_SERVER = 'smtp.gmail.com'
MAIL_PORT = 587
MAIL_USE_TLS = True
MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
MAIL_DEFAULT_SENDER = 'Old Timers Savings Club <noreply@oldtimerssavings.org>'
BASE_URL = os.environ.get('BASE_URL', 'http://localhost:5000')
```

### 2. SMS (Optional)
Add to `config.py`:
```python
SMS_ENABLED = True
SMS_API_URL = os.environ.get('SMS_API_URL')
SMS_API_KEY = os.environ.get('SMS_API_KEY')
SMS_SENDER_ID = 'OTSC'
```

### 3. WhatsApp (Optional)
Add to `config.py`:
```python
WHATSAPP_ENABLED = True
WHATSAPP_API_URL = 'https://graph.facebook.com/v18.0'
WHATSAPP_API_TOKEN = os.environ.get('WHATSAPP_API_TOKEN')
WHATSAPP_PHONE_ID = os.environ.get('WHATSAPP_PHONE_ID')
```

See `NOTIFICATION_CONFIGURATION.md` for detailed setup instructions.

---

## Files Modified

### Models
- ✅ `app/models/loan.py` - Added guarantor approval fields and helper methods

### Routes
- ✅ `app/routes/loans.py` - Added guarantor approval routes, updated application and approval logic
- ✅ `app/routes/main.py` - Added guarantor requests to member dashboard

### Templates
- ✅ `app/templates/dashboard/member.html` - Added guarantor requests section
- ✅ `app/templates/loans/view.html` - Added guarantor actions, updated status badges, enhanced guarantor display

### Utilities
- ✅ `app/utils/notifications.py` - Created notification service (NEW FILE)

### Migrations
- ✅ `migrations/add_guarantor_approval_fields.py` - Database migration script (NEW FILE)

### Documentation
- ✅ `NOTIFICATION_CONFIGURATION.md` - Notification setup guide (NEW FILE)
- ✅ `GUARANTOR_APPROVAL_IMPLEMENTATION.md` - This file (NEW FILE)

---

## Summary

The guarantor approval workflow has been fully implemented with:

1. ✅ **Complete workflow** from application to executive approval
2. ✅ **Multi-channel notifications** (Email, SMS, WhatsApp)
3. ✅ **Guarantor approval interface** with approve/decline options
4. ✅ **Executive restrictions** preventing guarantors from approving
5. ✅ **Member dashboard** showing pending guarantor requests
6. ✅ **Audit trail** for all actions
7. ✅ **Comprehensive validation** and error handling
8. ✅ **Status tracking** with visual badges
9. ✅ **Flexible notification system** supporting multiple channels

The system is now ready for testing. Start with email notifications only, then add SMS/WhatsApp as needed.

---

## Next Steps

1. **Run Database Migration**:
   ```bash
   python migrations/add_guarantor_approval_fields.py
   ```

2. **Configure Email**:
   - Set up Gmail app password or SMTP service
   - Add credentials to `.env` file

3. **Test Workflow**:
   - Create test loan application
   - Test guarantor approval
   - Test guarantor rejection
   - Test executive restrictions

4. **(Optional) Add SMS/WhatsApp**:
   - Sign up for Africa's Talking (SMS)
   - Set up WhatsApp Business API
   - Configure credentials

5. **Train Users**:
   - Show guarantors how to approve/decline
   - Explain executive restrictions
   - Demonstrate notification system

---

## Support

For questions or issues:
1. Check `NOTIFICATION_CONFIGURATION.md` for notification setup
2. Review audit logs for troubleshooting
3. Test in development environment first
4. Monitor email delivery rates

---

**Implementation Complete**: December 16, 2025
**Status**: ✅ Ready for Testing
