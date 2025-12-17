# Guarantor Qualification Check Feature

## Overview
This feature ensures that only qualified members (those who have completed 5 consecutive months of contributions) can act as guarantors for loan applications.

## Implementation Date
December 17, 2025

---

## Business Logic

### Why Qualification is Required for Guarantors

1. **Risk Management**: Qualified members have demonstrated financial commitment and stability
2. **Fair Practice**: If qualification is required to receive a loan, it should be required to guarantee one
3. **Member Protection**: Prevents new members from taking on financial obligations they may not be ready for
4. **System Consistency**: Aligns guarantor requirements with loan eligibility requirements

### Qualification Criteria

A member qualifies for benefits when:
- `consecutive_months_paid >= QUALIFICATION_PERIOD` (default: 5 months)
- `status == 'Active'`

This is checked via the `Member.is_qualified()` method in [app/models/member.py:86-88](app/models/member.py#L86-L88).

---

## Features Implemented

### 1. Runtime Validation in Approval Routes

**Files**: [app/routes/loans.py:492-496](app/routes/loans.py#L492-L496) and [app/routes/loans.py:566-570](app/routes/loans.py#L566-L570)

**Routes**:
- `/loans/<id>/approve_as_guarantor` (POST)
- `/loans/<id>/decline_as_guarantor` (POST)

**Functionality**:
When a member attempts to approve or decline as a guarantor, the system checks if they are qualified:

```python
# Check if guarantor is qualified for benefits
if not current_user.member.is_qualified():
    qualification_period = current_app.config.get('QUALIFICATION_PERIOD', 5)
    flash(f'You must be qualified to act as a guarantor! Please complete {qualification_period} consecutive months of contributions first.', 'danger')
    return redirect(url_for('loans.view_loan', id=id))
```

**User Experience**:
- Unqualified member clicks "Approve" or "Decline" button
- Redirected back to loan view with error message
- Error message explains qualification requirement

---

### 2. Filtered Guarantor Selection (Loan Application)

**File**: [app/routes/loans.py:222-229](app/routes/loans.py#L222-L229)

**Route**: `/loans/apply` (GET)

**Functionality**:
The loan application form only shows qualified members in the guarantor dropdown:

**For Executives/SuperAdmins**:
```python
guarantors = Member.query.filter_by(status='Active', qualified_for_benefits=True).order_by(Member.member_number).all()
```

**For Regular Members**:
```python
guarantors = Member.query.filter_by(status='Active', qualified_for_benefits=True).filter(
    Member.id != current_user.member.id
).order_by(Member.member_number).all()
```

**User Experience**:
- Only qualified members appear in guarantor dropdown
- Applicant cannot accidentally select unqualified guarantor
- Info message explains why some members don't appear

---

### 3. Filtered Guarantor Selection (Edit Loan)

**File**: [app/routes/loans.py:751-754](app/routes/loans.py#L751-L754)

**Route**: `/loans/<id>/edit` (GET)

**Functionality**:
When editing a returned loan application, only qualified members are available as guarantors:

```python
# Get only qualified members for guarantor selection (excluding the applicant)
members = Member.query.filter_by(status='Active', qualified_for_benefits=True).filter(
    Member.id != loan.member_id
).order_by(Member.member_number).all()
```

**User Experience**:
- Consistent with new loan application form
- Prevents selecting unqualified replacement guarantor
- Warning message explains qualification requirement

---

### 4. Visual Qualification Status Indicators

**File**: [app/templates/loans/view.html:109-113, 140-144](app/templates/loans/view.html#L109-L113)

**Location**: Loan detail view - Guarantor section

**Functionality**:
Each guarantor's qualification status is displayed with a badge:

**Qualified Member**:
```html
<span class="badge bg-success" title="Qualified for benefits">
    <i class="bi bi-check-circle-fill"></i> Qualified
</span>
```

**Unqualified Member**:
```html
<span class="badge bg-secondary" title="Not yet qualified">
    <i class="bi bi-hourglass-split"></i> Not Qualified
</span>
```

**User Experience**:
- Clear visual indicator next to each guarantor's name
- Green badge for qualified members
- Gray badge for unqualified members (if they were selected before this feature)
- Tooltip provides additional context

---

### 5. Informational Messages

#### Loan Application Form
**File**: [app/templates/loans/apply.html:86-88](app/templates/loans/apply.html#L86-L88)

```html
<div class="alert alert-info">
    <small><i class="bi bi-info-circle"></i> Only <strong>qualified</strong> members (5+ consecutive months of contributions) appear in the guarantor list. Both guarantors must approve your loan before executive review.</small>
</div>
```

#### Edit Loan Form
**File**: [app/templates/loans/edit.html:83-85](app/templates/loans/edit.html#L83-L85)

```html
<div class="alert alert-warning">
    <small><i class="bi bi-exclamation-triangle"></i> Both guarantors must be <strong>qualified</strong> active members (5+ consecutive months of contributions) and must approve your loan before executive review.</small>
</div>
```

---

## Protection Layers

The feature implements **three layers of protection**:

### Layer 1: Frontend Prevention
- Only qualified members appear in guarantor dropdowns
- User cannot select unqualified member

### Layer 2: Runtime Validation
- Even if someone bypasses frontend, backend checks qualification
- Approval/decline actions blocked for unqualified members

### Layer 3: Visual Feedback
- Qualification status clearly displayed
- Error messages explain requirements
- Info messages set expectations upfront

---

## User Workflows

### Scenario 1: New Loan Application

1. **Member applies for loan**
2. **Selects guarantors** from dropdown (only qualified members shown)
3. **Info message** explains only qualified members appear
4. **Submits application**
5. **Guarantor receives notification** to approve
6. **Guarantor attempts to approve**:
   - ✅ If qualified: Approval processed
   - ❌ If not qualified: Error message, redirected back

### Scenario 2: Editing Returned Loan

1. **Member's loan was returned** (guarantor declined)
2. **Member clicks "Revise"**
3. **Edit form loads** with only qualified members in dropdown
4. **Warning message** reminds about qualification requirement
5. **Member selects new guarantor** (must be qualified)
6. **Resubmits application**
7. **New guarantor workflow** begins (with qualification check)

### Scenario 3: Unqualified Member Attempts Approval

1. **Unqualified member logs in**
2. **Views loan** where they are listed as guarantor
3. **Clicks "Approve as Guarantor"**
4. **System blocks action** with error message:
   - "You must be qualified to act as a guarantor! Please complete 5 consecutive months of contributions first."
5. **Redirected back** to loan view
6. **Loan status** remains "Pending Guarantor Approval"

---

## Edge Cases Handled

### 1. Member Becomes Unqualified After Selection
**Scenario**: Member was qualified when selected, but status changes before approval

**Handling**:
- Runtime check catches this
- Approval blocked with error message
- Applicant can edit loan to select different guarantor

### 2. Legacy Loans with Unqualified Guarantors
**Scenario**: Loan created before this feature, has unqualified guarantor

**Handling**:
- Qualification badge shows "Not Qualified" status
- Unqualified guarantor cannot approve/decline
- Loan may need administrative intervention

### 3. Consecutive Months Reset
**Scenario**: Member was qualified, but consecutive_months_paid reset due to missed payment

**Handling**:
- `is_qualified()` returns False
- Member cannot approve new guarantor requests
- Existing approved guarantees remain valid

---

## Configuration

The qualification period is configurable in [app/__init__.py:52](app/__init__.py#L52):

```python
app.config['QUALIFICATION_PERIOD'] = int(os.getenv('QUALIFICATION_PERIOD', 5))
```

To change the requirement:
1. Update `.env` file: `QUALIFICATION_PERIOD=6`
2. Restart application
3. Messages will automatically reflect new requirement

---

## Testing Checklist

### Basic Qualification Check
- [ ] Unqualified member cannot approve as guarantor
- [ ] Unqualified member cannot decline as guarantor
- [ ] Error message displays correctly
- [ ] User redirected back to loan view
- [ ] Loan status unchanged after blocked action

### Guarantor Selection Filtering
- [ ] Only qualified members appear in application form dropdown
- [ ] Only qualified members appear in edit form dropdown
- [ ] Applicant excluded from dropdown (cannot guarantee own loan)
- [ ] Info message displays on application form
- [ ] Warning message displays on edit form

### Visual Indicators
- [ ] Qualified guarantor shows green "Qualified" badge
- [ ] Unqualified guarantor shows gray "Not Qualified" badge
- [ ] Badge appears for both Guarantor #1 and Guarantor #2
- [ ] Tooltip displays on hover
- [ ] Badge displays correctly alongside approval status

### Member Qualification Status
- [ ] New member (0 months) is not qualified
- [ ] Member with 4 months is not qualified
- [ ] Member with 5 months IS qualified
- [ ] Member with 6+ months IS qualified
- [ ] Suspended member is not qualified (even with 5+ months)

### Integration with Existing Workflow
- [ ] Loan application flow works normally with qualified guarantors
- [ ] Both guarantors can approve (when qualified)
- [ ] Loan progresses to "Pending Executive Approval" after both approve
- [ ] Edit/resubmit flow works with new guarantor selection
- [ ] Audit logs record qualification check failures

---

## Files Modified

### Backend (Python)
- ✅ [app/routes/loans.py:492-496](app/routes/loans.py#L492-L496) - Added qualification check to approve_as_guarantor
- ✅ [app/routes/loans.py:566-570](app/routes/loans.py#L566-L570) - Added qualification check to decline_as_guarantor
- ✅ [app/routes/loans.py:222-229](app/routes/loans.py#L222-L229) - Filtered guarantors in loan application
- ✅ [app/routes/loans.py:751-754](app/routes/loans.py#L751-L754) - Filtered guarantors in edit loan

### Frontend (Templates)
- ✅ [app/templates/loans/view.html:109-113](app/templates/loans/view.html#L109-L113) - Added qualification badge for Guarantor #1
- ✅ [app/templates/loans/view.html:140-144](app/templates/loans/view.html#L140-L144) - Added qualification badge for Guarantor #2
- ✅ [app/templates/loans/apply.html:86-88](app/templates/loans/apply.html#L86-L88) - Added info message
- ✅ [app/templates/loans/edit.html:83-85](app/templates/loans/edit.html#L83-L85) - Added warning message

---

## Database Impact

**No database changes required!**

This feature uses existing fields:
- `Member.qualified_for_benefits` (boolean)
- `Member.consecutive_months_paid` (integer)
- `Member.status` (string)

The `is_qualified()` method already exists in the Member model.

---

## Benefits

✅ **Risk Mitigation**:
- Ensures guarantors have proven financial stability
- Reduces risk of guarantor default

✅ **Fair Policy Enforcement**:
- Consistent requirements for borrowers and guarantors
- No "shortcuts" around qualification rules

✅ **Member Protection**:
- Prevents new members from over-committing
- Allows time to understand group obligations

✅ **Clear Communication**:
- Visual indicators show qualification status
- Error messages explain requirements
- Info messages set expectations

✅ **Administrative Control**:
- Configurable qualification period
- Automatic enforcement
- Complete audit trail

---

## Integration with Existing Features

### Works With:
- ✅ Guarantor approval workflow (QUICK_START_GUARANTOR_WORKFLOW.md)
- ✅ Loan resubmission feature (LOAN_RESUBMISSION_FEATURE.md)
- ✅ Member qualification tracking (contribution system)
- ✅ Audit logging system
- ✅ Notification system

### Does Not Affect:
- ✅ Collateral-based loans (no guarantors needed)
- ✅ Executive approval process
- ✅ Loan disbursement
- ✅ Repayment tracking

---

## Future Enhancements (Optional)

1. **Notification to Unqualified Members**
   - Email/SMS when they become qualified
   - "You can now act as a guarantor!"

2. **Dashboard Indicator**
   - Show member's own qualification status
   - "You are qualified to act as guarantor"

3. **Guarantor Qualification Report**
   - List all qualified members
   - Useful for applicants choosing guarantors

4. **Grace Period**
   - Allow guarantor approval if member was qualified when loan was submitted
   - Even if they become unqualified before responding

---

## Summary

The guarantor qualification check feature ensures that only financially stable, proven members can guarantee loans. This protects both the member (from over-commitment) and the group (from financial risk).

**Key Points**:
- ✅ Only qualified members (5+ consecutive months) can be guarantors
- ✅ Three-layer protection: frontend filter, runtime validation, visual feedback
- ✅ Clear error messages and informational alerts
- ✅ No database changes required
- ✅ Fully integrated with existing workflows

**Status**: ✅ Complete and Ready for Testing
