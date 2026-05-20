# Quick Reference Guide

Fast reference for common tasks in the Old Timers Savings System.

---

## Common Tasks

### Record a Contribution
1. **Contributions** → **Record Contribution**
2. Select member
3. Enter amount and date
4. Choose payment method
5. Click "Record Contribution"

### Add New Member
1. **Members** → **Add New Member**
2. Fill in name, phone, and date joined
3. Click "Save Member"

### Apply for Loan (Member)
1. Dashboard → **Apply for Loan**
2. Enter amount and purpose
3. Select 2 guarantors or upload collateral
4. Submit application

### Approve Loan (Executive)
1. **Loans** → Filter by "Pending Executive Approval"
2. Click loan to review
3. Click "Approve" and enter amount
4. Confirm

### Record Loan Payment
1. **Loans** → Find active loan
2. Click "Record Payment"
3. Enter amount and date
4. Save

### Submit Welfare Request (Member)
1. Dashboard → **Submit Welfare Request**
2. Select type and enter details
3. Submit

### Approve Welfare (Chairman)
1. **Welfare** → Filter by "Under Review"
2. Click request
3. Click "Approve" and enter amount
4. Confirm

### Schedule Meeting
1. **Meetings** → **Schedule Meeting**
2. Enter date, time, venue, agenda
3. Save

### Record Attendance
1. **Meetings** → Click meeting
2. Click "Record Attendance"
3. Check present members
4. Save

### Generate Financial Report
1. **Reports** → **Financial Summary**
2. Select date range
3. Click "Generate Report"

---

## Access by Role

### Super Admin Can:
✅ Everything (full access)

### Executive Can:
✅ Add/edit members
✅ Record contributions
✅ Record membership fees
✅ Approve loans
✅ Approve welfare
✅ Schedule meetings
✅ Record attendance
✅ Record expenses
✅ View all reports
❌ Manage user accounts

### Auditor Can:
✅ View all data (read-only)
✅ View all reports
✅ View audit logs
❌ Edit or create anything

### Member Can:
✅ View own profile
✅ Apply for loans
✅ Submit welfare requests
✅ Approve/decline guarantor requests
✅ View own statement
❌ View other members' details
❌ Record contributions

---

## Status Meanings

### Member Status
- **Active**: Full member in good standing
- **Suspended**: Temporarily unable to access benefits
- **Inactive**: No longer participating
- **Expelled**: Removed from group

### Loan Status
- **Pending Guarantor Approval**: Waiting for guarantors
- **Returned to Applicant**: Needs revision
- **Pending Executive Approval**: Awaiting chairman/executive
- **Approved**: Approved, awaiting disbursement
- **Disbursed/Active**: Money given, repayment in progress
- **Completed**: Fully repaid
- **Rejected**: Application denied
- **Defaulted**: Payment overdue

### Welfare Status
- **Submitted/Pending**: Just submitted
- **Under Review**: Secretary reviewing
- **Approved**: Chairman approved
- **Paid**: Payment completed
- **Rejected**: Request denied

### Meeting Status
- **Scheduled**: Upcoming meeting
- **Completed**: Meeting held
- **Cancelled**: Meeting cancelled

---

## Important Numbers

- **Membership Fee**: UGX 20,000 (one-time)
- **Monthly Contribution**: UGX 100,000
- **Bereavement Amount**: UGX 500,000
- **Loan Interest Rate**: 5%
- **Qualification Period**: 5 consecutive months
- **Quorum Requirement**: 5 members
- **Max Login Attempts**: 5 (then 30-min lockout)

---

## File Size Limits

- **Maximum Upload**: 10 MB
- **Supported Formats**:
  - Documents: PDF
  - Images: JPG, PNG
  - Combined: PDF, JPG, PNG

---

## Auto-Generated Numbers

- **Member Number**: OT-001, OT-002, etc.
- **Receipt Number**: OT-2024-01-0001 (year-month-sequence)
- **Loan Number**: LN-2024-0001
- **Welfare Request**: WR-2024-0001
- **Welfare Voucher**: WV-2024-0001
- **Expense Number**: EX-2024-0001

---

## Notification Channels

✅ **Email**: Enabled (all users)
⚙️ **SMS**: Optional (configurable)
⚙️ **WhatsApp**: Optional (configurable)

---

## Keyboard Shortcuts

- `Alt + D` - Dashboard
- `Alt + M` - Members
- `Alt + C` - Contributions
- `Alt + L` - Loans
- `Alt + W` - Welfare
- `Alt + R` - Reports

---

## Mobile Tips

- Tap **☰** for navigation menu
- Swipe tables left/right
- Use landscape for tables
- Portrait for forms
- Add to home screen for quick access

---

## Emergency Contacts

**System Administrator**: admin@oldtimerssavings.org
**Chairman**: [Contact from group]
**Treasurer**: [Contact from group]
**Secretary**: [Contact from group]

---

## Quick Troubleshooting

| Problem | Quick Fix |
|---------|-----------|
| Can't login | Wait 30 min if locked, or contact admin |
| Page not loading | Refresh (F5), clear cache, or try another browser |
| Receipt not generating | Wait, check popup blocker, try again |
| File won't upload | Check size (<10MB) and format (PDF/JPG/PNG) |
| Mobile issues | Clear cache, use HTTPS, see [Mobile Guide](MOBILE_LOGIN_TROUBLESHOOTING.md) |

---

## Financial Year

**July 1 - June 30**

Example: FY 2024-2025 runs from July 1, 2024 to June 30, 2025

---

## Data Retention

- **Audit Logs**: Kept indefinitely
- **Contributions**: Permanent record
- **Loans**: Permanent record
- **Welfare**: Permanent record
- **Meetings**: Permanent record
- **Expenses**: Permanent record

---

## Backup Schedule

**Recommended**: Daily automatic backup
**Manual Backup**: Use `flask clear-database` with `--keep-admin` for clean start

---

## Security Features

✅ Password hashing
✅ Account lockout protection
✅ HTTPS encryption
✅ Role-based access control
✅ Complete audit trail
✅ Session timeout (30 minutes)

---

## For More Information

**Full User Guide**: [USER_GUIDE.md](USER_GUIDE.md)
**Mobile Guide**: [MOBILE_OPTIMIZATION.md](MOBILE_OPTIMIZATION.md)
**Deployment Guide**: [PYTHONANYWHERE_DEPLOYMENT.md](PYTHONANYWHERE_DEPLOYMENT.md)
**Documentation Index**: [INDEX.md](INDEX.md)
