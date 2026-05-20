# Old Timers Savings System - Complete User Guide

**Version 1.0**
**Last Updated: December 2025**

Complete guide to all features and functionality in the Old Timers Savings Group Digital Records Management System.

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Member Management](#member-management)
3. [Contributions](#contributions)
4. [Membership Fees](#membership-fees)
5. [Loans](#loans)
6. [Welfare](#welfare)
7. [Meetings](#meetings)
8. [Expenses](#expenses)
9. [Reports](#reports)
10. [User Management](#user-management)
11. [Notifications](#notifications)
12. [Mobile Access](#mobile-access)

---

## Getting Started

### Logging In

1. Open your web browser
2. Navigate to `https://yourusername.pythonanywhere.com`
3. Enter your username and password
4. Click "Login"

**Security Features**:
- Account locks after 5 failed login attempts for 30 minutes
- Password must be at least 8 characters
- First-time users must change their password

### Dashboard Overview

After logging in, you'll see a dashboard customized to your role:

**Super Admin & Executive**:
- Total members count
- Pending welfare requests
- Pending loan applications
- Recent contributions
- Upcoming meetings
- Quick action buttons

**Auditor**:
- Read-only view of all data
- Financial statistics
- Audit trail access
- Audit tools

**Member**:
- Personal contribution summary
- Qualification status
- Active loans
- Guarantor requests
- Quick access to apply for loans/welfare

---

## Member Management

### Adding a New Member

**Who can do this**: Super Admin, Executive

**Steps**:
1. Navigate to **Members** → **Add New Member**
2. Fill in required information:
   - Full Name
   - National ID (optional)
   - Date of Birth
   - Gender
   - Primary Phone Number
   - Secondary Phone (optional)
   - Email (optional)
   - Physical Address
   - Occupation
   - Date Joined
3. Click "Save Member"

**Important**:
- Member number is auto-generated (format: OT-001, OT-002, etc.)
- Primary phone number is required
- All members start with "Active" status

### Viewing Member Profile

**Steps**:
1. Go to **Members** → **List Members**
2. Search or browse for the member
3. Click member name or "View" button

**Profile Shows**:
- Personal information
- Contribution statistics
- Membership fee status
- Qualification status
- Next of kin
- Active loans

### Editing Member Information

**Steps**:
1. View member profile
2. Click "Edit Member" button
3. Update information
4. Click "Update Member"

### Adding Next of Kin

**Steps**:
1. View member profile
2. Click "Add Next of Kin"
3. Fill in details:
   - Type (Primary or Alternative)
   - Full Name
   - Relationship
   - National ID
   - Phone numbers
   - Email
   - Address
   - Distribution Percentage
4. Click "Save Next of Kin"

**Notes**:
- Each member can have multiple next of kin
- Distribution percentage determines share of benefits
- Only Executive members can view next of kin details

### Suspending/Activating Members

**Steps**:
1. View member profile
2. Click "Suspend Member" or "Activate Member"
3. Provide reason (for suspension)
4. Confirm action

**Suspension Rules**:
- Suspended members cannot apply for loans
- Suspended members cannot receive welfare
- Contributions can still be recorded

---

## Contributions

### Recording a Single Contribution

**Who can do this**: Super Admin, Executive

**Steps**:
1. Go to **Contributions** → **Record Contribution**
2. Select member from dropdown
3. Enter contribution details:
   - Amount (default: UGX 100,000)
   - Payment Date
   - Contribution Month (YYYY-MM format)
   - Payment Method (Cash, Mobile Money, Bank Transfer, etc.)
   - Transaction Reference (optional)
   - Notes (optional)
4. Click "Record Contribution"

**Result**:
- Receipt number auto-generated
- Member stats updated
- Qualification status checked

### Batch Recording Contributions

**Steps**:
1. Go to **Contributions** → **Batch Record**
2. Select contribution month
3. Select payment date
4. Select payment method
5. Check members who have paid
6. Enter amount for each (or use default)
7. Click "Record Batch Contributions"

**Benefits**:
- Record multiple contributions quickly
- Useful for monthly collection meetings
- All receipts generated at once

### Viewing Contribution History

**Members can view their own**:
1. Dashboard shows recent contributions
2. Click "View My Statement" for full history

**Executives can view all**:
1. Go to **Contributions** → **List Contributions**
2. Use filters:
   - Month
   - Member
   - Payment method
3. Click contribution to view details

### Editing Contributions

**Steps**:
1. Find contribution in list
2. Click "Edit"
3. Update details
4. Click "Update Contribution"

**Notes**:
- Only authorized users can edit
- Edit is logged in audit trail

### Generating Receipts

Receipts are auto-generated, but you can:
1. View contribution
2. Click "Download Receipt"
3. PDF receipt downloads

**Receipt includes**:
- Receipt number
- Member details
- Amount paid
- Month
- Payment date and method
- Recorded by

---

## Membership Fees

### Recording Membership Fee Payment

**Who can do this**: Super Admin, Executive

**Steps**:
1. Go to **Membership Fees** → **List Members**
2. Find member with "Unpaid" status
3. Click "Record Payment"
4. Enter payment details:
   - Payment Date
   - Payment Method
   - Transaction Reference
   - Receipt Number (auto-generated)
5. Click "Record Payment"

**Fee Amount**: UGX 20,000 (one-time payment)

### Viewing Unpaid Members

**Steps**:
1. Go to **Membership Fees** → **Unpaid Members**
2. See list of members who haven't paid
3. Record payments as needed

### Downloading Receipt

**Steps**:
1. Go to member profile
2. Under membership fee section
3. Click "View Receipt" or "Download PDF"

---

## Loans

### For Members: Applying for a Loan

**Steps**:
1. From dashboard, click "Apply for Loan"
2. Or navigate to **Loans** → **Apply for Loan**
3. Fill in application details:
   - Amount Requested
   - Purpose
   - Repayment Period (months)
   - Security Type (Guarantors or Collateral)

**If using Guarantors**:
4. Select 2 qualified guarantors from dropdown
   - Must have 5+ consecutive months of contributions
   - Cannot be yourself
5. Guarantors will be notified

**If using Collateral**:
4. Specify collateral type
5. Enter estimated value
6. Upload collateral documents (photos, ownership docs)

7. Review and submit application

**After Submission**:
- Loan number assigned (LN-YYYY-XXXX)
- Status: "Pending Guarantor Approval" or "Pending Executive Approval"
- Notification sent to guarantors (if applicable)

### For Guarantors: Approving/Declining Requests

**When you're selected as guarantor**:
1. You'll see notification on dashboard
2. Under "Pending Guarantor Approval Requests"
3. Click "Review & Respond"
4. View applicant details and loan amount
5. Click "Approve" or "Decline"
6. If declining, provide reason
7. Confirm action

**Important**:
- Both guarantors must approve
- Applicant is notified of your decision

### For Executives: Reviewing Applications

**Steps**:
1. Go to **Loans** → **List Loans**
2. Filter by "Pending Executive Approval"
3. Click loan to view details
4. Review:
   - Applicant information
   - Requested amount
   - Purpose
   - Repayment capacity
   - Guarantors/collateral
5. Make decision:
   - **Approve**: Enter approved amount (can be less than requested)
   - **Return to Applicant**: Request changes with note
   - **Reject**: Provide rejection reason

### Disbursing Loans

**Who can do this**: Super Admin, Executive

**Steps**:
1. Go to **Loans** → **List Loans**
2. Filter by "Approved" status
3. Click "Disburse" button
4. Enter disbursement details:
   - Disbursement Date
   - Disbursement Method (Cash, Bank Transfer, etc.)
   - Reference Number
   - Upload withdrawal document (bank slip)
5. Click "Confirm Disbursement"

**Result**:
- Loan status changes to "Active" or "Disbursed"
- Due date calculated automatically
- Member notified

### Recording Loan Repayments

**Steps**:
1. Go to **Loans** → **List Loans**
2. Find active loan
3. Click "Record Payment"
4. Enter payment details:
   - Payment Amount
   - Payment Date
   - Payment Method
   - Transaction Reference
5. Click "Record Repayment"

**Automatic Calculation**:
- Interest portion calculated
- Principal portion calculated
- New balance updated
- If balance = 0, loan marked "Completed"

### Viewing Loan Details

**Steps**:
1. Go to **Loans** → **List Loans**
2. Click loan number
3. View:
   - Application details
   - Guarantors/collateral
   - Approval history
   - Disbursement info
   - Repayment history
   - Current balance

---

## Welfare

### Submitting a Welfare Request

**Who can do this**: All qualified members

**Steps**:
1. From dashboard, click "Submit Welfare Request"
2. Or **Welfare** → **Submit Request**
3. Fill in request form:
   - Request Type (Bereavement, Medical, Celebration)
   - Affected Person (name and relationship)
   - Incident Date
   - Amount Requested
   - Description/Reason
4. Click "Submit Request"

**Types of Welfare**:
- **Bereavement**: Death of member or close relative (UGX 500,000)
- **Medical**: Serious illness requiring hospitalization
- **Celebration**: Wedding, childbirth, etc.

**After Submission**:
- Request number assigned (WR-YYYY-XXXX)
- Status: "Submitted" or "Pending"
- Secretary notified

### For Executives: Reviewing Welfare Requests

**Secretary Review**:
1. Go to **Welfare** → **List Requests**
2. Filter by "Submitted"
3. Click request to view details
4. Click "Mark Under Review"
5. Request moves to Chairman for approval

**Chairman Approval**:
1. Filter by "Under Review"
2. Review request details
3. Make decision:
   - **Approve**: Enter approved amount
   - **Reject**: Provide reason
4. Confirm action

### Recording Welfare Payments

**Steps**:
1. Go to **Welfare** → **List Requests**
2. Filter by "Approved"
3. Click "Record Payment"
4. Enter payment details:
   - Payment Amount
   - Payment Date
   - Payment Method
   - Voucher Number (auto-generated)
   - Upload bank withdrawal document
   - Upload beneficiary receipt
5. Click "Record Payment"

**Result**:
- Voucher number generated (WV-YYYY-XXXX)
- Status changes to "Paid"
- Member notified

---

## Meetings

### Scheduling a Meeting

**Who can do this**: Super Admin, Executive

**Steps**:
1. Go to **Meetings** → **Schedule Meeting**
2. Enter meeting details:
   - Meeting Type (General, Executive, Emergency, Annual, etc.)
   - Date and Time
   - Venue
   - Agenda
3. Click "Schedule Meeting"

**Result**:
- Meeting appears on all dashboards
- Members see upcoming meeting notification

### Recording Attendance

**Steps**:
1. Go to **Meetings** → **List Meetings**
2. Click meeting
3. Click "Record Attendance"
4. For each member:
   - Check "Present" box
   - Or select "Absent" or "Excused"
   - Note arrival time (optional)
5. Click "Save Attendance"

**Quorum Check**:
- System shows if quorum met (minimum 5 members)
- Quorum requirement configurable

### Uploading Meeting Minutes

**Steps**:
1. View meeting details
2. Click "Upload Minutes"
3. Select PDF file
4. Add resolution summary (optional)
5. Click "Upload"

### Managing Action Items

**Adding Action Items**:
1. View meeting details
2. Under "Action Items" section
3. Click "Add Action Item"
4. Fill in:
   - Description
   - Assigned To (member)
   - Deadline
5. Click "Add"

**Updating Status**:
1. Find action item
2. Click "Update Status"
3. Select status (Pending, In Progress, Completed)
4. Add completion notes
5. Save

---

## Expenses

### Recording an Expense

**Who can do this**: Super Admin, Executive

**Steps**:
1. Go to **Expenses** → **Record Expense**
2. Enter expense details:
   - Category (Stationery, Airtime, Transport, Meetings, Bank Charges, etc.)
   - Amount
   - Expense Date
   - Payee (who was paid)
   - Payment Method
   - Transaction Reference
   - Description
   - Upload receipt (PDF, JPG, PNG)
3. Click "Record Expense"

**Result**:
- Expense number generated
- Reflected in financial reports

### Viewing Expenses

**Steps**:
1. Go to **Expenses** → **List Expenses**
2. Filter by:
   - Category
   - Month
   - Date range
3. Click expense to view details

### Editing/Deleting Expenses

**Edit**:
1. View expense details
2. Click "Edit"
3. Update information
4. Save changes

**Delete**:
1. View expense details
2. Click "Delete"
3. Confirm deletion
4. Logged in audit trail

---

## Reports

### Financial Summary Report

**Who can access**: Super Admin, Executive, Auditor

**Steps**:
1. Go to **Reports** → **Financial Summary**
2. Select date range (Start Date - End Date)
3. Click "Generate Report"

**Report Shows**:
- **Income**:
  - Membership fees collected
  - Total contributions
  - Loan repayments (interest + principal)
- **Expenses**:
  - Loans disbursed
  - Welfare payments
  - Operational expenses
- **Net Position**: Income - Expenses
- **Outstanding Loans**: Total balance owed

### Contributions Report

**Steps**:
1. Go to **Reports** → **Contributions Report**
2. Select month or date range
3. Generate

**Shows**:
- Monthly breakdown
- Top contributors
- Payment methods analysis
- Collection rate
- Individual member contributions

### Loans Report

**Steps**:
1. Go to **Reports** → **Loans Report**
2. Select filters (status, date range)
3. Generate

**Shows**:
- Total loans disbursed
- Outstanding balance
- Active loans count
- Completed loans
- Defaulted loans
- Interest earned

### Welfare Report

**Steps**:
1. Go to **Reports** → **Welfare Report**
2. Select date range
3. Generate

**Shows**:
- Total requests
- Approved vs. rejected
- Amount approved vs. paid
- Request types breakdown
- Pending payments

### Meetings Report

**Steps**:
1. Go to **Reports** → **Meetings Report**
2. Select date range
3. Generate

**Shows**:
- Total meetings held
- Average attendance
- Quorum compliance
- Meeting types breakdown

### Member Statement

**For members to view their own**:
1. Dashboard → "View My Statement"

**For executives to generate for any member**:
1. Go to **Reports** → **Member Statement**
2. Select member
3. Select date range
4. Generate

**Shows**:
- Membership fee status
- Contribution history
- Total contributed
- Qualification status
- Loan history
- Active loan balances
- Welfare assistance received

---

## User Management

**Who can access**: Super Admin Only

### Creating User Accounts

**Steps**:
1. Go to **User Management** → **Create User**
2. Select existing member
3. Enter username
4. Assign role:
   - **SuperAdmin**: Full system access
   - **Executive**: Manage members, contributions, loans, welfare, meetings
   - **Auditor**: Read-only access to all data
   - **Member**: View own information only
5. Set initial password
6. Check "Must change password on first login"
7. Click "Create User"

**Important**:
- Each member can have only one user account
- Username must be unique
- User receives notification with login credentials

### Managing Users

**View All Users**:
1. Go to **User Management** → **List Users**
2. Filter by role or status

**Edit User**:
1. Click user to view details
2. Click "Edit User"
3. Update role or member association
4. Save changes

**Reset Password**:
1. View user details
2. Click "Reset Password"
3. Enter new password
4. Check "Force change on next login"
5. Save

**Activate/Deactivate**:
1. View user details
2. Click "Deactivate Account" or "Activate Account"
3. Confirm

**Unlock Locked Account**:
1. View user details
2. If account is locked, click "Unlock Account"
3. Failed login attempts reset to 0

### Viewing User Activity

**Steps**:
1. View user details
2. Scroll to "Recent Activity" section
3. See audit log of user actions

---

## Notifications

### Viewing Notifications

**Steps**:
1. Click notification bell icon (shows count)
2. See list of unread notifications
3. Click notification to view details

**Notification Types**:
- Guarantor requests
- Guarantor approvals/rejections
- Loan status updates
- Welfare status updates
- Meeting reminders

### Managing Notifications

**Mark as Read**:
- Click notification
- Automatically marked as read

**Mark All as Read**:
- Click "Mark All as Read" button

### Notification Channels

**Email** (Primary):
- All users receive email notifications
- Uses email address from member profile

**SMS** (Optional):
- If enabled by admin
- Sent to primary phone number

**WhatsApp** (Optional):
- If enabled by admin
- Sent via WhatsApp Business API

---

## Mobile Access

### Accessing on Smartphone

1. Open mobile browser (Safari, Chrome, etc.)
2. Navigate to your system URL
3. Login with credentials

**Mobile Features**:
- Hamburger menu for navigation (☰)
- Touch-friendly buttons
- Scrollable tables
- Mobile-optimized forms
- Quick action buttons

**Tips**:
- Add to home screen for quick access
- Use landscape mode for tables
- Swipe tables left/right to see more columns

**Detailed Mobile Guide**: See [MOBILE_OPTIMIZATION.md](MOBILE_OPTIMIZATION.md)

---

## Best Practices

### For Treasurers/Secretaries

**Monthly Routine**:
1. Record all contributions using batch entry
2. Generate contribution report
3. Follow up with non-payers
4. Record membership fees for new members
5. Process loan repayments
6. Update welfare payments

**Meeting Day**:
1. Record attendance
2. Note action items
3. Upload minutes within 24 hours

### For Chairperson

**Regular Tasks**:
- Review pending welfare requests
- Approve/reject loan applications
- Review financial reports monthly
- Check action items completion

### For Auditors

**Quarterly Review**:
1. Generate financial summary
2. Review all expense records
3. Check loan disbursement documentation
4. Verify welfare payment documentation
5. Review audit trail for anomalies

### For Members

**Stay Qualified**:
- Pay contributions on time each month
- Maintain 5+ consecutive months for loan qualification
- Update contact information when it changes
- Respond to guarantor requests promptly

---

## Keyboard Shortcuts

**Global**:
- `Alt + D` - Go to Dashboard
- `Alt + M` - Go to Members
- `Alt + C` - Go to Contributions
- `Alt + L` - Go to Loans
- `Alt + W` - Go to Welfare
- `Alt + R` - Go to Reports

**Forms**:
- `Tab` - Move to next field
- `Shift + Tab` - Move to previous field
- `Enter` - Submit form (when on button)

---

## Troubleshooting

### Cannot Login

**Check**:
- Username and password are correct
- Account is not locked (wait 30 minutes or contact admin)
- Account is active (contact admin)

### Page Not Loading

**Try**:
- Refresh page (F5 or pull down on mobile)
- Clear browser cache
- Check internet connection
- Try different browser

### Receipt Not Generating

**Solution**:
- Wait a moment and try again
- Check if PDF popup is blocked
- Contact admin if persists

### Cannot Upload Document

**Check**:
- File size under 10MB
- File type is supported (PDF, JPG, PNG)
- Internet connection is stable

### Mobile Login Issues

**See**: [MOBILE_LOGIN_TROUBLESHOOTING.md](MOBILE_LOGIN_TROUBLESHOOTING.md)

---

## Glossary

**Member Number**: Unique identifier (e.g., OT-001)
**Receipt Number**: Contribution receipt ID (e.g., OT-2024-01-0001)
**Loan Number**: Loan application ID (e.g., LN-2024-0001)
**Voucher Number**: Welfare payment ID (e.g., WV-2024-0001)
**Qualified Member**: Member with 5+ consecutive monthly contributions
**Quorum**: Minimum 5 members required for valid meeting
**Guarantor**: Member who guarantees loan repayment
**Collateral**: Asset pledged as loan security
**Welfare**: Financial assistance for bereavement, medical, celebration
**Executive**: Member of executive committee
**Auditor**: Read-only oversight role

---

## Support

### Getting Help

**For Technical Issues**:
- Check this user guide first
- Contact system administrator
- Email: admin@oldtimerssavings.org

**For Policy Questions**:
- Consult group constitution
- Contact executive committee
- Raise at general meeting

### Reporting Bugs

When reporting an issue:
1. Describe what you were trying to do
2. Note what happened instead
3. Include screenshot if possible
4. Note your device/browser (e.g., "Chrome on Android")

---

## System Information

**Version**: 1.0
**Developer**: Claude Code
**Deployment Platform**: PythonAnywhere
**Technology**: Python Flask, SQLite
**Security**: HTTPS, Role-Based Access Control, Audit Logging

---

**For Full Documentation Index**: See [INDEX.md](INDEX.md)

**For Mobile Guide**: See [MOBILE_OPTIMIZATION.md](MOBILE_OPTIMIZATION.md)

**For Deployment Guide**: See [PYTHONANYWHERE_DEPLOYMENT.md](PYTHONANYWHERE_DEPLOYMENT.md)
