# Loan Resubmission Feature

## Overview
This feature allows members whose loan applications were returned (due to guarantor rejection) to revise and resubmit their applications.

## Implementation Date
December 16, 2025

---

## Features Implemented

### 1. Applicant Actions Card (Loan View)

**File**: `app/templates/loans/view.html` (Lines 260-301)

When a member views their own loan that has status "Returned to Applicant", they see:

- **Red warning card** with "Loan Application Returned" header
- **Clear explanation** of why the loan was returned
  - Shows which guarantor(s) declined
  - Shows rejection reason(s) from the guarantor(s)
- **Options available**:
  - Select a new guarantor to replace the one who declined
  - Change security type to Collateral instead
  - Modify loan amount or purpose
- **Action buttons**:
  - "Revise & Resubmit Application" (primary button)
  - "Cancel Application" (secondary button with confirmation)

---

### 2. Edit/Resubmit Route

**File**: `app/routes/loans.py` (Lines 616-740)

**Route**: `/loans/<id>/edit` (GET, POST)

**Access Control**:
- Only the applicant can edit their own loan
- Only works for loans with status "Returned to Applicant"
- Returns 403 if unauthorized, redirects if wrong status

**Functionality**:
- **GET**: Shows edit form with current loan data pre-filled
- **POST**: Updates the loan and resubmits

**What can be changed**:
- ✅ Loan amount
- ✅ Purpose
- ✅ Repayment period (1 or 2 months)
- ✅ Security type (Guarantors ↔ Collateral)
- ✅ Guarantor selection (if using guarantors)
- ✅ Collateral details (if using collateral)

**Smart Status Updates**:
- If security type = **Guarantors**: Status → "Pending Guarantor Approval"
  - Resets guarantor approval fields
  - Sends notifications to new guarantors
- If security type = **Collateral**: Status → "Pending Executive Approval"
  - Skips guarantor approval step

**Audit Trail**:
- Logs action as "LoanResubmitted"
- Includes loan number and timestamp
- Records user, IP address, and user agent

---

### 3. Cancel Loan Route

**File**: `app/routes/loans.py` (Lines 743-780)

**Route**: `/loans/<id>/cancel` (POST)

**Access Control**:
- Only the applicant can cancel their own loan
- Works for loans with status "Returned to Applicant" or "Pending Guarantor Approval"

**Functionality**:
- Changes loan status to "Rejected"
- Adds note: "Canceled by applicant (was [previous status])"
- Sets approval date to today

**Audit Trail**:
- Logs action as "LoanCanceled"
- Includes loan number and timestamp

---

### 4. Edit Loan Template

**File**: `app/templates/loans/edit.html` (NEW FILE)

**Features**:
- Yellow warning card styling (matches "returned" status theme)
- Shows loan number at top
- Alert explaining the loan was returned
- All form fields pre-populated with current values
- **Security type toggle**:
  - JavaScript dynamically shows/hides sections
  - Updates required field validation
- **Guarantor selection**:
  - Excludes the applicant from guarantor list
  - Pre-selects current guarantors
- **Collateral fields**:
  - Pre-fills description and value
- **Action buttons**:
  - Cancel (returns to view)
  - Resubmit (submits form)

---

### 5. Dashboard Status Badges

**File**: `app/templates/dashboard/member.html` (Lines 187-230)

**Updated Status Badges**:
- **Pending Guarantor Approval** → Yellow badge "Pending Guarantors"
- **Returned to Applicant** → Red badge "Returned - Action Required"
- **Pending Executive Approval** → Blue badge "Pending Executive Review"
- **Approved** → Blue badge "Approved - Awaiting Disbursement"
- **Active/Disbursed** → Green badge "Active"
- **Completed** → Gray badge "Completed"
- **Rejected** → Red badge "Rejected"

**Updated Action Buttons**:
- If loan status = "Returned to Applicant":
  - Shows **orange "Revise"** button instead of "View"
  - Links directly to edit form
- All other statuses:
  - Shows blue "View" button

---

## User Flow

### Scenario: Guarantor Declines Loan

1. **Member applies** for loan with 2 guarantors
2. **Guarantor #1 approves**
3. **Guarantor #2 declines** with reason "Insufficient repayment plan details"
4. **Loan status changes** to "Returned to Applicant"
5. **Member receives notification** via email/SMS/WhatsApp
6. **Member logs in** and sees:
   - Dashboard shows loan with red "Returned - Action Required" badge
   - Orange "Revise" button next to the loan
7. **Member clicks "Revise"** or views loan and clicks "Revise & Resubmit"
8. **Edit form appears** with:
   - Current loan details pre-filled
   - Warning showing which guarantor declined and why
9. **Member has options**:
   - **Option A**: Select different guarantor
   - **Option B**: Change to Collateral security
   - **Option C**: Modify amount/purpose and keep same guarantors
   - **Option D**: Cancel the application
10. **Member resubmits** with new guarantor
11. **System processes**:
    - Resets guarantor approval fields
    - Changes status to "Pending Guarantor Approval"
    - Sends notifications to new guarantors
    - Logs resubmission in audit trail
12. **Workflow continues** from guarantor approval step

---

## Validation & Security

### Access Control
- ✅ Only applicant can edit their own loan
- ✅ Only "Returned to Applicant" loans can be edited
- ✅ Proper authentication checks
- ✅ Member ID validation

### Input Validation
- ✅ All required fields validated
- ✅ Amount must be positive
- ✅ Two different guarantors required (if using guarantors)
- ✅ Cannot select self as guarantor
- ✅ Collateral description and value required (if using collateral)

### Data Integrity
- ✅ Guarantor approvals properly reset when changing guarantors
- ✅ Collateral fields cleared when switching to guarantors
- ✅ Guarantor fields cleared when switching to collateral
- ✅ Status updated appropriately based on security type
- ✅ Audit trail complete

---

## Testing Checklist

### Basic Resubmission
- [ ] Member applies for loan with 2 guarantors
- [ ] Guarantor declines
- [ ] Loan status changes to "Returned to Applicant"
- [ ] Member sees red badge on dashboard
- [ ] Member clicks "Revise" button
- [ ] Edit form shows with pre-filled data
- [ ] Member selects new guarantor
- [ ] Member resubmits
- [ ] Status changes to "Pending Guarantor Approval"
- [ ] New guarantor receives notification
- [ ] Old rejection reason cleared

### Security Type Change
- [ ] Member's loan returned (guarantor declined)
- [ ] Member clicks "Revise"
- [ ] Member changes from "Guarantors" to "Collateral"
- [ ] Collateral fields appear
- [ ] Member fills collateral details
- [ ] Member resubmits
- [ ] Status changes to "Pending Executive Approval" (skips guarantor step)
- [ ] Guarantor fields cleared in database

### Cancel Application
- [ ] Member views returned loan
- [ ] Member clicks "Cancel Application"
- [ ] Confirmation dialog appears
- [ ] Member confirms
- [ ] Loan status changes to "Rejected"
- [ ] Note added: "Canceled by applicant"
- [ ] Action logged in audit trail

### Access Control
- [ ] Different member cannot access edit form for another's loan
- [ ] Executive cannot edit member's loan via this route
- [ ] Cannot edit loan that is not "Returned to Applicant"
- [ ] Proper error messages shown

### Edge Cases
- [ ] Member selects same 2 guarantors - error shown
- [ ] Member selects self as guarantor - not in list
- [ ] Form submission with missing fields - validation errors
- [ ] Multiple rapid submissions - handled properly

---

## Files Modified/Created

### New Files
- ✅ `app/templates/loans/edit.html` - Edit/resubmit form template

### Modified Files
- ✅ `app/routes/loans.py` - Added edit_loan and cancel_loan routes
- ✅ `app/templates/loans/view.html` - Added applicant actions card
- ✅ `app/templates/dashboard/member.html` - Updated status badges and action buttons

---

## Database Impact

**No new tables or columns required!**

This feature uses existing Loan table fields:
- Updates existing loan record
- Resets guarantor approval fields
- Changes status field
- Uses existing audit log table

---

## Benefits

✅ **Member Experience**:
- Clear feedback on why loan was returned
- Easy process to fix and resubmit
- No need to create new application from scratch
- Maintains loan number and history

✅ **System Efficiency**:
- Reuses existing loan record
- Complete audit trail preserved
- Notifications sent automatically
- Proper workflow state management

✅ **Flexibility**:
- Can change security type
- Can modify any aspect of application
- Can cancel if desired
- Multiple resubmission attempts allowed

---

## Future Enhancements (Optional)

1. **Limit resubmission attempts**
   - After 3 resubmissions, require manual review

2. **Track resubmission history**
   - Show timeline of guarantor changes
   - Show reason for each resubmission

3. **Notification to previous guarantors**
   - Let them know they were replaced

4. **Bulk edit**
   - Allow member to edit multiple returned loans at once

---

## Summary

The loan resubmission feature is now complete and allows members to:
- ✅ View why their loan was returned
- ✅ Revise and resubmit their application
- ✅ Change guarantors or switch to collateral
- ✅ Cancel unwanted applications
- ✅ Track status through the entire process

All changes are logged, validated, and secure. The feature integrates seamlessly with the existing guarantor approval workflow.

**Status**: ✅ Complete and Ready for Testing
