# Bug Fix: Guarantor Access to Loan View

## Problem

Guarantors could not view loans they were assigned to approve. When clicking "Review & Respond" from the dashboard's "Pending Guarantor Approval Requests" section, they would see:

> "You do not have permission to view this loan!"

This prevented guarantors from:
- Viewing loan details
- Approving the loan
- Declining the loan
- Completing their role in the approval workflow

## Root Cause

The access control check in [app/routes/loans.py:240-244](app/routes/loans.py#L240-L244) was too restrictive. It only allowed:
- ✅ Executives
- ✅ Super Admins
- ✅ Auditors
- ✅ The loan applicant

But it did NOT allow:
- ❌ **Guarantors** (the people who need to approve/decline)

## Solution

Updated the access control logic to include guarantors:

**File**: [app/routes/loans.py:240-253](app/routes/loans.py#L240-L253)

**Before**:
```python
# Check access: executives/auditors can see all, members can only see their own
if not (current_user.is_executive() or current_user.is_super_admin() or current_user.is_auditor()):
    if not hasattr(current_user, 'member') or loan.member_id != current_user.member.id:
        flash('You do not have permission to view this loan!', 'danger')
        return redirect(url_for('main.dashboard'))
```

**After**:
```python
# Check access: executives/auditors can see all, members can see their own or loans they're guaranteeing
if not (current_user.is_executive() or current_user.is_super_admin() or current_user.is_auditor()):
    if not hasattr(current_user, 'member'):
        flash('You do not have permission to view this loan!', 'danger')
        return redirect(url_for('main.dashboard'))

    # Allow access if user is the applicant OR one of the guarantors
    is_applicant = loan.member_id == current_user.member.id
    is_guarantor = (loan.guarantor1_id == current_user.member.id or
                   loan.guarantor2_id == current_user.member.id)

    if not (is_applicant or is_guarantor):
        flash('You do not have permission to view this loan!', 'danger')
        return redirect(url_for('main.dashboard'))
```

## Changes Made

1. **Split the access check**: Separate check for member existence from loan access
2. **Added guarantor check**: Check if current user is Guarantor #1 OR Guarantor #2
3. **Updated logic**: Allow access if user is applicant OR guarantor
4. **Updated comment**: Clarified that guarantors can view loans

## Access Control Matrix

After this fix, here's who can view a loan:

| User Role | Can View? | Condition |
|-----------|-----------|-----------|
| Super Admin | ✅ Always | Admin privilege |
| Executive | ✅ Always | Executive privilege |
| Auditor | ✅ Always | Auditor privilege |
| Member (Applicant) | ✅ Yes | If they are the loan applicant |
| Member (Guarantor #1) | ✅ Yes | If they are listed as guarantor1 |
| Member (Guarantor #2) | ✅ Yes | If they are listed as guarantor2 |
| Member (Other) | ❌ No | No connection to the loan |

## User Experience

### Before Fix
1. Member sees "Pending Guarantor Approval Requests" on dashboard
2. Clicks "Review & Respond" button
3. **Gets error**: "You do not have permission to view this loan!"
4. **Cannot complete action**: Stuck, cannot approve or decline

### After Fix
1. Member sees "Pending Guarantor Approval Requests" on dashboard
2. Clicks "Review & Respond" button
3. **Views loan details**: Can see amount, purpose, applicant, etc.
4. **Can take action**: "Approve as Guarantor" or "Decline as Guarantor" buttons visible
5. **Workflow completes**: Approval/decline is processed

## Security Considerations

### Maintains Security
- ✅ Members still cannot view random loans
- ✅ Only applicants and guarantors can view specific loan
- ✅ Executives/Auditors maintain full access
- ✅ No privilege escalation possible

### Privacy Appropriate
- ✅ Guarantors NEED to see loan details to make informed decision
- ✅ Guarantors are already part of the loan contract
- ✅ Applicant selected these guarantors (gave implicit permission)

### Prevents Issues
- ✅ Guarantor cannot view loans they're not involved in
- ✅ Member cannot "guess" loan IDs to view others' loans
- ✅ Proper authentication still required

## Testing Checklist

- [x] Guarantor #1 can view loan they're assigned to
- [x] Guarantor #2 can view loan they're assigned to
- [x] Applicant can view their own loan
- [x] Random member CANNOT view loan they're not involved in
- [x] Executive can view any loan
- [x] Auditor can view any loan
- [x] Guarantor can click "Approve as Guarantor" button
- [x] Guarantor can click "Decline as Guarantor" button
- [x] Approval/decline functionality works after viewing

## Integration with Existing Features

### Works With
- ✅ Guarantor approval workflow
- ✅ Dashboard guarantor requests section
- ✅ Loan resubmission (guarantors change)
- ✅ Qualification checks
- ✅ Audit logging

### Related Features
- Dashboard: Shows "Pending Guarantor Approval Requests"
- Loan View: Shows guarantor action buttons
- Approve Route: Processes guarantor approval
- Decline Route: Processes guarantor decline
- Notifications: Sent to guarantors

## Related Files

### Modified
- ✅ [app/routes/loans.py](app/routes/loans.py) - Lines 240-253 (view_loan function)

### Related (Not Modified)
- [app/routes/loans.py](app/routes/loans.py) - approve_as_guarantor (line ~460)
- [app/routes/loans.py](app/routes/loans.py) - decline_as_guarantor (line ~530)
- [app/templates/dashboard/member.html](app/templates/dashboard/member.html) - Guarantor requests section
- [app/templates/loans/view.html](app/templates/loans/view.html) - Guarantor action buttons

## Impact

**Severity**: Critical
**Impact**: Blocking - guarantor workflow completely broken without this fix
**User Impact**: High (positive) - restores essential functionality
**Breaking Changes**: None
**Data Changes**: None

## Summary

This fix restores the guarantor approval workflow by allowing guarantors to view loans they need to approve. The access control now properly checks if the user is:
1. An applicant (can view their own loan)
2. A guarantor (can view loans they're assigned to)
3. An executive/admin/auditor (can view all loans)

**Status**: ✅ Fixed and tested
