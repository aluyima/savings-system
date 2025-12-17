# Auditor Account Setup and Management Guide

## Overview
This guide explains how to properly configure and manage Auditor accounts for the Old Timers Savings Club system. Auditors have read-only access to all system records for conducting quarterly audits.

## Auditor Role Permissions

### What Auditors CAN Do:
- ✅ View all financial reports (Financial Summary, Meetings Report)
- ✅ Access audit trail and system logs
- ✅ View member records (read-only)
- ✅ View contributions, loans, and welfare records (read-only)
- ✅ View meeting records and minutes (read-only)
- ✅ Generate and export reports
- ✅ Access their own personal member account (if linked)
- ✅ Apply for loans and welfare for themselves (if they are members)

### What Auditors CANNOT Do:
- ❌ Create or modify member records
- ❌ Record contributions or membership fees
- ❌ Approve or disburse loans
- ❌ Approve welfare requests
- ❌ Modify financial records
- ❌ Access user management (SuperAdmin only)
- ❌ Record operational expenses (Executive only)

## Setting Up an Auditor Account

### Step 1: Create the User Account (SuperAdmin Required)

1. Login as SuperAdmin
2. Navigate to **User Management** → **Create User**
3. Fill in the form:
   - **Username**: Choose a unique username (e.g., "auditor2025")
   - **Password**: Set a strong initial password (min 8 characters)
   - **Role**: Select **Auditor**
   - **Link to Member**: (Optional) If the auditor is also a club member, link their user account to their member profile

4. Click **Create User**

### Step 2: Inform the Auditor

Provide the auditor with:
- Their username
- Temporary password
- Instructions to change password on first login
- Link to system: [http://your-system-url.com](http://your-system-url.com)

### Step 3: First Login

The auditor will be required to:
1. Login with temporary credentials
2. Change password immediately (system enforced)
3. Review their dashboard and available reports

## Quarterly Audit Process

### Before the Audit (Preparation)

1. **Activate Auditor Account** (if temporarily deactivated)
   - SuperAdmin navigates to User Management
   - Finds the auditor account
   - Ensures account is **Active**

2. **Verify Access**
   - Auditor logs in
   - Confirms access to all required reports
   - Tests report generation

### During the Audit (3-Month Period)

The auditor should:

1. **Review Financial Summary**
   - Navigate to Reports → Financial Summary
   - Filter by audit period dates
   - Review income, expenses, and net position

2. **Verify Member Records**
   - Check member registrations and status changes
   - Review membership fee payments

3. **Audit Contributions**
   - Review monthly contribution collection rates
   - Verify receipt numbers and payment records

4. **Examine Loan Portfolio**
   - Review all loans (pending, active, completed)
   - Verify disbursements and repayments
   - Check interest calculations

5. **Review Welfare Disbursements**
   - Verify welfare request approvals
   - Check payment records

6. **Check Operational Expenses**
   - Review expense categories and amounts
   - Verify receipt documentation

7. **Review Audit Logs**
   - Check system activity logs
   - Identify any unusual transactions
   - Verify user actions

8. **Export Reports**
   - Generate PDF reports for record-keeping
   - Save copies for audit documentation

### After the Audit (Cleanup)

1. **Auditor Submits Report**
   - Auditor prepares audit findings
   - Submits to Executive Committee

2. **Optional: Deactivate Account**
   - If auditor only needs quarterly access
   - SuperAdmin can deactivate account until next audit
   - Navigate to User Management → View User → Deactivate

## Best Practices for Auditor Account Management

### Security Measures

1. **Strong Passwords**
   - Enforce minimum 12-character passwords for auditors
   - Require combination of uppercase, lowercase, numbers, and symbols
   - Change passwords after each audit period

2. **Account Monitoring**
   - Review auditor login history regularly
   - Check audit logs for auditor actions
   - Monitor unusual access patterns

3. **Limited Duration Access**
   - Consider activating accounts only during audit periods
   - Deactivate between audits if appropriate
   - Reactivate for each quarterly review

### Audit Schedule

Recommended quarterly schedule:
- **Q1 Audit**: January-March (Audit in early April)
- **Q2 Audit**: April-June (Audit in early July)
- **Q3 Audit**: July-September (Audit in early October)
- **Q4 Audit**: October-December (Audit in early January)

### Documentation Requirements

Auditors should maintain:
- ✅ Audit checklists
- ✅ Financial reconciliation worksheets
- ✅ Exception reports (discrepancies found)
- ✅ Recommendations for improvements
- ✅ Signed audit completion certificates

## Multiple Auditors

If the club has multiple auditors:

1. **Create Separate Accounts**
   - Each auditor gets their own user account
   - Different usernames (e.g., "auditor1", "auditor2")
   - Individual passwords

2. **Coordinate Audit Activities**
   - Assign specific areas to each auditor
   - Example:
     - Auditor 1: Financial records, contributions
     - Auditor 2: Loans, welfare, expenses

3. **Track Individual Actions**
   - System logs all actions by username
   - Easy to identify who performed what review

## Linking Auditor to Member Profile

### When to Link:

Link an auditor account to a member profile if:
- ✅ The auditor is also a club member
- ✅ They need to access their personal account information
- ✅ They want to apply for loans or welfare

### Benefits of Linking:

1. **Personal Account Access**
   - View personal contribution history
   - Check own loan status
   - Submit welfare requests
   - View personal statement

2. **Dashboard Features**
   - Auditor dashboard shows "My Personal Account" section
   - Quick access to personal information
   - Separate from audit functions

### How to Link:

1. SuperAdmin creates/edits user account
2. In "Link to Member" dropdown, select the auditor's member profile
3. Save changes

**Note**: Linking does NOT give additional privileges - auditor still has read-only access to other members' records.

## Troubleshooting

### Account Locked

If auditor account gets locked (failed login attempts):
1. SuperAdmin navigates to User Management → View User
2. Click **Unlock Account** button
3. Inform auditor to try again

### Password Reset

If auditor forgets password:
1. SuperAdmin navigates to User Management → View User
2. Use **Reset Password** function
3. Set new temporary password
4. Inform auditor (they must change on next login)

### Missing Reports

If auditor cannot see expected reports:
1. Verify account role is "Auditor" (not "Member")
2. Check account is **Active**
3. Clear browser cache
4. Try different browser

### Access Denied Errors

If auditor gets "Permission Denied":
1. Check they're logged in correctly
2. Verify their role is "Auditor"
3. Confirm they're not trying to access SuperAdmin/Executive functions
4. Check audit logs for details

## Audit Trail

All auditor actions are logged in the system audit trail:

**Logged Actions Include:**
- Login/Logout events
- Reports viewed
- Records accessed
- Filters applied
- Exports generated

**To View Audit Logs:**
1. SuperAdmin or Executive login
2. Navigate to User Management → View User (Auditor)
3. Scroll to "Recent Activity" section

## Recommended: Auditor Checklist Template

```
QUARTERLY AUDIT CHECKLIST - Q___ 20___

Date: ________________
Auditor: ________________

□ 1. FINANCIAL SUMMARY VERIFIED
   □ Total income matches records
   □ Total expenses verified
   □ Net position calculated correctly

□ 2. MEMBERSHIP RECORDS REVIEWED
   □ New member registrations checked
   □ Membership fees verified
   □ Status changes documented

□ 3. CONTRIBUTIONS AUDITED
   □ Monthly collection rates reviewed
   □ Receipt numbers sequential
   □ Payment methods verified

□ 4. LOAN PORTFOLIO EXAMINED
   □ All loan applications reviewed
   □ Disbursements verified
   □ Repayments recorded correctly
   □ Interest calculations checked
   □ Outstanding balances verified

□ 5. WELFARE REQUESTS VERIFIED
   □ Approvals documented
   □ Payments recorded
   □ Supporting documents checked

□ 6. OPERATIONAL EXPENSES REVIEWED
   □ All categories checked
   □ Receipts available
   □ Amounts reasonable

□ 7. SYSTEM INTEGRITY CHECKED
   □ Audit logs reviewed
   □ No unauthorized access detected
   □ User activity appropriate

□ 8. RECOMMENDATIONS
   [Space for auditor notes]

AUDIT STATUS: □ APPROVED  □ QUALIFIED  □ ADVERSE

Auditor Signature: _________________
Date: _________________
```

## Contact

For questions about auditor setup or audit procedures:
- Contact: Club Secretary
- Email: [secretary@oldtimerssavingsclub.org]
- Phone: [Contact Number]

---

**Document Version**: 1.0
**Last Updated**: December 2025
**Review Frequency**: Annually or as needed
