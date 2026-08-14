"""
Loans Routes
Handles loan applications, approvals, disbursements, and repayments
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, abort
from flask_login import login_required, current_user
from app import db
from app.models.loan import Loan, LoanRepayment
from app.models.member import Member
from app.utils.decorators import executive_required, super_admin_required
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
from sqlalchemy import func, extract

loans = Blueprint('loans', __name__, url_prefix='/loans')


@loans.route('/')
@login_required
def list_loans():
    """List all loans with filtering - Auditors have read-only access"""
    if not (current_user.is_executive() or current_user.is_super_admin() or current_user.is_auditor()):
        abort(403)
    status_filter = request.args.get('status', '')
    member_filter = request.args.get('member', '')

    query = Loan.query.join(Member, Loan.member_id == Member.id)

    if status_filter:
        query = query.filter(Loan.status == status_filter)

    if member_filter:
        query = query.filter(Member.member_number.contains(member_filter))

    loans_list = query.order_by(Loan.created_at.desc()).all()

    # Calculate statistics
    total_disbursed = db.session.query(func.sum(Loan.amount_approved)).filter(
        Loan.status.in_(['Disbursed', 'Active', 'Completed'])
    ).scalar() or 0

    total_outstanding = db.session.query(func.sum(Loan.balance)).filter(
        Loan.status == 'Active'
    ).scalar() or 0

    active_loans_count = Loan.query.filter_by(status='Active').count()

    return render_template('loans/list.html',
                         loans=loans_list,
                         status_filter=status_filter,
                         member_filter=member_filter,
                         total_disbursed=total_disbursed,
                         total_outstanding=total_outstanding,
                         active_loans_count=active_loans_count)


@loans.route('/apply', methods=['GET', 'POST'])
@login_required
def apply():
    """Submit loan application"""
    if request.method == 'POST':
        # Executives/SuperAdmin may file on behalf of another member (selected on the
        # form); everyone else can only apply for themselves.
        if (current_user.is_executive() or current_user.is_super_admin()) and request.form.get('member_id'):
            member_id = request.form.get('member_id')
        else:
            member_id = current_user.member.id if hasattr(current_user, 'member') else None

        if not member_id:
            flash('Invalid member selection!', 'danger')
            return redirect(url_for('loans.apply'))

        member = Member.query.get(member_id)
        if not member or member.status != 'Active':
            flash('Only active members can apply for loans!', 'danger')
            return redirect(url_for('loans.apply'))

        # The administrator account is not a real group member and cannot borrow
        if member.user and member.user.role == 'SuperAdmin':
            flash('The administrator is not a group member and cannot take a loan.', 'danger')
            return redirect(url_for('loans.apply'))

        # Check minimum contribution months for loan eligibility
        min_contributions = current_app.config.get('LOAN_MIN_CONTRIBUTIONS', 3)
        if member.consecutive_months_paid < min_contributions:
            flash(f'You need at least {min_contributions} months of contributions to apply for a loan. You currently have {member.consecutive_months_paid}.', 'danger')
            return redirect(url_for('loans.apply'))

        try:
            amount_requested = Decimal(request.form.get('amount_requested'))
            if amount_requested <= 0:
                flash('Loan amount must be greater than zero!', 'danger')
                return redirect(url_for('loans.apply'))
        except (ValueError, TypeError):
            flash('Invalid loan amount!', 'danger')
            return redirect(url_for('loans.apply'))

        # Get security type
        security_type = request.form.get('security_type')
        if not security_type:
            flash('Please select a security type!', 'danger')
            return redirect(url_for('loans.apply'))

        guarantor1_id = None
        guarantor2_id = None
        collateral_description = None
        collateral_value = None
        collateral_documents_path = None

        if security_type == 'Guarantors':
            # Validate guarantors
            guarantor1_id = request.form.get('guarantor1_id')
            guarantor2_id = request.form.get('guarantor2_id')

            if not guarantor1_id or not guarantor2_id:
                flash('Two guarantors are required!', 'danger')
                return redirect(url_for('loans.apply'))

            if guarantor1_id == guarantor2_id:
                flash('Guarantors must be different members!', 'danger')
                return redirect(url_for('loans.apply'))

            if guarantor1_id == str(member.id) or guarantor2_id == str(member.id):
                flash('You cannot be your own guarantor!', 'danger')
                return redirect(url_for('loans.apply'))

        elif security_type == 'Collateral':
            # Validate collateral
            collateral_description = request.form.get('collateral_description')
            if not collateral_description:
                flash('Collateral description is required!', 'danger')
                return redirect(url_for('loans.apply'))

            try:
                collateral_value = Decimal(request.form.get('collateral_value', '0'))
                if collateral_value < amount_requested:
                    flash('Collateral value must be at least equal to the loan amount!', 'danger')
                    return redirect(url_for('loans.apply'))
            except (ValueError, TypeError):
                flash('Invalid collateral value!', 'danger')
                return redirect(url_for('loans.apply'))

            # Handle file upload
            if 'collateral_documents' in request.files:
                file = request.files['collateral_documents']
                if file and file.filename:
                    import os
                    from werkzeug.utils import secure_filename

                    # Create upload directory if it doesn't exist
                    upload_folder = current_app.config['UPLOAD_FOLDER']
                    collateral_folder = os.path.join(upload_folder, 'collateral')
                    os.makedirs(collateral_folder, exist_ok=True)

                    # Save file with unique name
                    filename = secure_filename(file.filename)
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    unique_filename = f"{member.member_number}_{timestamp}_{filename}"
                    file_path = os.path.join(collateral_folder, unique_filename)
                    file.save(file_path)

                    collateral_documents_path = f'collateral/{unique_filename}'
                else:
                    flash('Please upload collateral documents!', 'danger')
                    return redirect(url_for('loans.apply'))

        # Generate loan number
        today = date.today()
        year = today.year
        prefix = f'LN-{year}-'

        result = db.session.execute(
            db.select(func.max(Loan.loan_number)).where(
                Loan.loan_number.like(f'{prefix}%')
            )
        ).scalar()

        if result:
            last_num = int(result.split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1

        loan_number = f'{prefix}{new_num:04d}'

        # Create loan application
        loan = Loan(
            loan_number=loan_number,
            member_id=member.id,
            amount_requested=amount_requested,
            purpose=request.form.get('purpose'),
            repayment_period_months=int(request.form.get('repayment_period_months', 2)),
            interest_rate=Decimal(str(current_app.config.get('LOAN_INTEREST_RATE', '10.00'))),
            security_type=security_type,
            guarantor1_id=int(guarantor1_id) if guarantor1_id else None,
            guarantor2_id=int(guarantor2_id) if guarantor2_id else None,
            guarantor1_approved=None if guarantor1_id else None,  # None = pending, True = approved, False = rejected
            guarantor2_approved=None if guarantor2_id else None,
            collateral_description=collateral_description,
            collateral_value=collateral_value,
            collateral_documents_path=collateral_documents_path,
            status='Pending Guarantor Approval' if security_type == 'Guarantors' else 'Pending Executive Approval'
        )

        db.session.add(loan)
        db.session.commit()

        # Send notifications to guarantors if applicable
        if security_type == 'Guarantors':
            from app.utils.notifications import NotificationService
            guarantor1 = Member.query.get(guarantor1_id)
            guarantor2 = Member.query.get(guarantor2_id)

            if guarantor1:
                NotificationService.send_guarantor_request_notification(loan, guarantor1, 1)
            if guarantor2:
                NotificationService.send_guarantor_request_notification(loan, guarantor2, 2)

            flash(f'Loan application submitted successfully! Loan Number: {loan_number}. Guarantors have been notified.', 'success')
        else:
            flash(f'Loan application submitted successfully! Loan Number: {loan_number}', 'success')

        return redirect(url_for('loans.view_loan', id=loan.id))

    # GET request - show application form
    # For executive users, show all active members; for regular members, show only themselves
    if current_user.is_executive() or current_user.is_super_admin():
        # Exclude administrator accounts - they are not real group members and cannot borrow
        members = [m for m in Member.query.filter_by(status='Active').order_by(Member.member_number).all()
                   if not (m.user and m.user.role == 'SuperAdmin')]
        # Only qualified members can be guarantors
        guarantors = Member.query.filter_by(status='Active', qualified_for_benefits=True).order_by(Member.member_number).all()
    else:
        members = [current_user.member] if hasattr(current_user, 'member') else []
        # Only qualified members (excluding self) can be guarantors
        guarantors = Member.query.filter_by(status='Active', qualified_for_benefits=True).filter(
            Member.id != current_user.member.id
        ).order_by(Member.member_number).all() if hasattr(current_user, 'member') else []

    return render_template('loans/apply.html', members=members, guarantors=guarantors)


@loans.route('/<int:id>')
@login_required
def view_loan(id):
    """View loan details"""
    loan = Loan.query.get_or_404(id)

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

    # Get repayments sorted by date (newest first)
    repayments = loan.repayments.order_by(LoanRepayment.payment_date.desc()).all()

    # Pass today's date for due date calculations
    from datetime import date
    today = date.today()

    return render_template('loans/view.html', loan=loan, repayments=repayments, today=today)


@loans.route('/<int:id>/approve', methods=['POST'])
@login_required
@executive_required
def approve_loan(id):
    """Approve loan application (requires all 3 executives)"""
    loan = Loan.query.get_or_404(id)

    # Check if loan is pending executive approval
    if loan.status not in ['Pending Executive Approval', 'Approved']:  # Allow re-approval for updates
        flash('This loan is not ready for executive approval!', 'warning')
        return redirect(url_for('loans.view_loan', id=id))

    # Check if guarantors have approved (for guarantor-based loans)
    if loan.security_type == 'Guarantors' and not loan.both_guarantors_approved():
        flash('Cannot approve loan! Both guarantors must approve first.', 'danger')
        return redirect(url_for('loans.view_loan', id=id))

    # Check if current executive is a guarantor for this loan
    if hasattr(current_user, 'member'):
        member_id = current_user.member.id
        if loan.guarantor1_id == member_id or loan.guarantor2_id == member_id:
            flash('You cannot approve this loan because you are a guarantor! Another executive must approve this loan.', 'danger')
            return redirect(url_for('loans.view_loan', id=id))

    amount_approved = request.form.get('amount_approved')
    if not amount_approved:
        flash('Approved amount is required!', 'danger')
        return redirect(url_for('loans.view_loan', id=id))

    try:
        loan.amount_approved = Decimal(amount_approved)
    except (ValueError, TypeError):
        flash('Invalid approved amount!', 'danger')
        return redirect(url_for('loans.view_loan', id=id))

    loan.approval_notes = request.form.get('approval_notes')
    loan.approval_date = date.today()
    loan.executive_approved = True
    loan.status = 'Approved'

    # Calculate total payable
    loan.calculate_total_payable()

    # For simplicity, record current user as approver
    # In production, you'd have a full workflow for all 3 executives
    loan.approved_by_chairman = current_user.id

    db.session.commit()

    flash('Loan approved successfully!', 'success')
    return redirect(url_for('loans.view_loan', id=id))


@loans.route('/<int:id>/reject', methods=['POST'])
@login_required
@executive_required
def reject_loan(id):
    """Reject loan application"""
    loan = Loan.query.get_or_404(id)

    if loan.status not in ['Pending Guarantor Approval', 'Pending Executive Approval']:
        flash('Only pending loans can be rejected!', 'warning')
        return redirect(url_for('loans.view_loan', id=id))

    loan.status = 'Rejected'
    loan.approval_notes = request.form.get('rejection_reason')
    loan.approval_date = date.today()

    db.session.commit()

    flash('Loan application rejected.', 'info')
    return redirect(url_for('loans.view_loan', id=id))


@loans.route('/<int:id>/disburse', methods=['GET', 'POST'])
@login_required
@executive_required
def disburse_loan(id):
    """Disburse approved loan"""
    loan = Loan.query.get_or_404(id)

    if loan.status != 'Approved':
        flash('Only approved loans can be disbursed!', 'warning')
        return redirect(url_for('loans.view_loan', id=id))

    if request.method == 'POST':
        try:
            disbursement_date = datetime.strptime(request.form.get('disbursement_date'), '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid disbursement date!', 'danger')
            return redirect(url_for('loans.disburse_loan', id=id))

        # Handle file upload
        if 'withdrawal_document' not in request.files:
            flash('Withdrawal document is required!', 'danger')
            return redirect(url_for('loans.disburse_loan', id=id))

        file = request.files['withdrawal_document']
        if file.filename == '':
            flash('No file selected!', 'danger')
            return redirect(url_for('loans.disburse_loan', id=id))

        if file:
            from werkzeug.utils import secure_filename
            import os

            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            unique_filename = f"{loan.loan_number}_{timestamp}_{filename}"

            # Create disbursement folder if it doesn't exist
            disbursement_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'disbursements')
            os.makedirs(disbursement_folder, exist_ok=True)

            file_path = os.path.join(disbursement_folder, unique_filename)
            file.save(file_path)

            # Store relative path in database
            loan.disbursement_document_path = f"disbursements/{unique_filename}"

        loan.disbursement_date = disbursement_date
        loan.disbursement_method = 'Cash Withdrawal from Bank Account'
        loan.disbursement_reference = request.form.get('withdrawal_reference')
        loan.disbursed = True
        loan.status = 'Active'

        # Calculate due date: disbursement_date + repayment_period_months
        from dateutil.relativedelta import relativedelta
        loan.due_date = disbursement_date + relativedelta(months=loan.repayment_period_months)

        db.session.commit()

        flash('Loan disbursed successfully!', 'success')
        return redirect(url_for('loans.view_loan', id=id))

    return render_template('loans/disburse.html', loan=loan)


@loans.route('/<int:id>/repay', methods=['GET', 'POST'])
@login_required
@executive_required
def record_repayment(id):
    """Record loan repayment"""
    loan = Loan.query.get_or_404(id)

    if loan.status not in ['Active', 'Disbursed']:
        flash('Cannot record repayment for this loan!', 'warning')
        return redirect(url_for('loans.view_loan', id=id))

    if request.method == 'POST':
        try:
            amount = Decimal(request.form.get('amount'))
            if amount <= 0:
                flash('Repayment amount must be greater than zero!', 'danger')
                return redirect(url_for('loans.record_repayment', id=id))
        except (ValueError, TypeError):
            flash('Invalid repayment amount!', 'danger')
            return redirect(url_for('loans.record_repayment', id=id))

        try:
            payment_date = datetime.strptime(request.form.get('payment_date'), '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid payment date!', 'danger')
            return redirect(url_for('loans.record_repayment', id=id))

        # Generate receipt number
        year = payment_date.year
        month = payment_date.month
        prefix = f'LR-{year}-{month:02d}-'

        result = db.session.execute(
            db.select(func.max(LoanRepayment.receipt_number)).where(
                LoanRepayment.receipt_number.like(f'{prefix}%')
            )
        ).scalar()

        if result:
            last_num = int(result.split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1

        receipt_number = f'{prefix}{new_num:04d}'

        # Calculate principal and interest portions
        # Simple calculation: proportional split
        total_payable = float(loan.total_payable)
        principal = float(loan.amount_approved)
        interest_total = total_payable - principal

        principal_ratio = principal / total_payable
        interest_ratio = interest_total / total_payable

        principal_portion = amount * Decimal(str(principal_ratio))
        interest_portion = amount * Decimal(str(interest_ratio))

        # Create repayment record
        repayment = LoanRepayment(
            loan_id=loan.id,
            receipt_number=receipt_number,
            payment_date=payment_date,
            amount_paid=amount,
            principal_portion=principal_portion,
            interest_portion=interest_portion,
            payment_method=request.form.get('payment_method'),
            transaction_reference=request.form.get('transaction_reference'),
            notes=request.form.get('notes'),
            recorded_by=current_user.id
        )

        db.session.add(repayment)

        # Update loan balance
        loan.total_paid = (loan.total_paid or 0) + amount
        loan.balance = loan.total_payable - loan.total_paid

        if loan.balance <= 0:
            loan.status = 'Completed'

        db.session.commit()

        flash(f'Repayment recorded successfully! Receipt: {receipt_number}', 'success')
        return redirect(url_for('loans.view_loan', id=id))

    return render_template('loans/repay.html', loan=loan)


def _resolve_guarantor_slot(loan):
    """Determine which guarantor slot the current user is acting on.

    A SuperAdmin may act on behalf of a guarantor who cannot use the system by
    submitting 'guarantor_position' ('1' or '2'); otherwise the slot is derived
    from the logged-in member.

    Returns a tuple (is_guarantor1, is_guarantor2, guarantor_member, acting_as_admin).
    Raises ValueError with a user-facing message if the slot cannot be resolved.
    """
    if current_user.is_super_admin():
        position = request.form.get('guarantor_position')
        if position not in ('1', '2'):
            raise ValueError('Please select which guarantor you are acting on behalf of.')
        is_guarantor1 = (position == '1')
        guarantor_id = loan.guarantor1_id if is_guarantor1 else loan.guarantor2_id
        if not guarantor_id:
            raise ValueError('This loan does not have the selected guarantor.')
        return is_guarantor1, not is_guarantor1, Member.query.get(guarantor_id), True

    if not hasattr(current_user, 'member'):
        raise ValueError('You must be a member to act as a guarantor!')

    member_id = current_user.member.id
    is_guarantor1 = (loan.guarantor1_id == member_id)
    is_guarantor2 = (loan.guarantor2_id == member_id)
    if not (is_guarantor1 or is_guarantor2):
        raise ValueError('You are not a guarantor for this loan!')
    return is_guarantor1, is_guarantor2, current_user.member, False


@loans.route('/<int:id>/guarantor/approve', methods=['POST'])
@login_required
def approve_as_guarantor(id):
    """Guarantor approves loan application (SuperAdmin may act on their behalf)"""
    loan = Loan.query.get_or_404(id)

    try:
        is_guarantor1, is_guarantor2, guarantor_member, acting_as_admin = _resolve_guarantor_slot(loan)
    except ValueError as e:
        flash(str(e), 'danger')
        return redirect(url_for('loans.view_loan', id=id))

    # The guarantor (not the admin acting for them) must be qualified for benefits
    if not guarantor_member.is_qualified():
        qualification_period = current_app.config.get('QUALIFICATION_PERIOD', 3)
        if acting_as_admin:
            flash(f'{guarantor_member.full_name} is not yet qualified to act as a guarantor ({qualification_period} consecutive months of contributions required).', 'danger')
        else:
            flash(f'You must be qualified to act as a guarantor! Please complete {qualification_period} consecutive months of contributions first.', 'danger')
        return redirect(url_for('loans.view_loan', id=id))

    # Check if loan is in correct status
    if loan.status not in ['Pending Guarantor Approval', 'Returned to Applicant']:
        flash('This loan is not pending guarantor approval!', 'warning')
        return redirect(url_for('loans.view_loan', id=id))

    # Approve based on which guarantor
    if is_guarantor1:
        if loan.guarantor1_approved is not None:
            flash('This guarantor has already responded to the request!', 'warning')
            return redirect(url_for('loans.view_loan', id=id))
        loan.guarantor1_approved = True
        loan.guarantor1_approval_date = datetime.now()
        guarantor_num = 1
    else:  # is_guarantor2
        if loan.guarantor2_approved is not None:
            flash('This guarantor has already responded to the request!', 'warning')
            return redirect(url_for('loans.view_loan', id=id))
        loan.guarantor2_approved = True
        loan.guarantor2_approval_date = datetime.now()
        guarantor_num = 2

    # Check if both guarantors have approved
    if loan.both_guarantors_approved():
        loan.status = 'Pending Executive Approval'
        # Send notification to applicant
        from app.utils.notifications import NotificationService
        NotificationService.send_guarantor_approval_notification(loan)
        if acting_as_admin:
            flash_message = f"Recorded {guarantor_member.full_name}'s approval. Both guarantors have now approved - the loan is pending executive approval."
        else:
            flash_message = 'Thank you! You have approved this loan. Both guarantors have now approved - the loan is pending executive approval.'
    else:
        if acting_as_admin:
            flash_message = f"Recorded {guarantor_member.full_name}'s approval as Guarantor #{guarantor_num}. Waiting for the other guarantor to approve."
        else:
            flash_message = f'Thank you! You have approved this loan as Guarantor #{guarantor_num}. Waiting for the other guarantor to approve.'

    db.session.commit()

    # Log action
    from app.models.audit import AuditLog
    description = f'Approved loan {loan.loan_number} as Guarantor #{guarantor_num}'
    if acting_as_admin:
        description += f' on behalf of {guarantor_member.full_name}'
    AuditLog.log_action(
        user_id=current_user.id,
        action_type='GuarantorApproved',
        entity_type='Loan',
        entity_id=loan.id,
        description=description,
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string
    )

    flash(flash_message, 'success')
    return redirect(url_for('loans.view_loan', id=id))


@loans.route('/<int:id>/guarantor/decline', methods=['POST'])
@login_required
def decline_as_guarantor(id):
    """Guarantor declines loan application (SuperAdmin may act on their behalf)"""
    loan = Loan.query.get_or_404(id)

    try:
        is_guarantor1, is_guarantor2, guarantor_member, acting_as_admin = _resolve_guarantor_slot(loan)
    except ValueError as e:
        flash(str(e), 'danger')
        return redirect(url_for('loans.view_loan', id=id))

    # The guarantor (not the admin acting for them) must be qualified for benefits
    if not guarantor_member.is_qualified():
        qualification_period = current_app.config.get('QUALIFICATION_PERIOD', 3)
        if acting_as_admin:
            flash(f'{guarantor_member.full_name} is not yet qualified to act as a guarantor ({qualification_period} consecutive months of contributions required).', 'danger')
        else:
            flash(f'You must be qualified to act as a guarantor! Please complete {qualification_period} consecutive months of contributions first.', 'danger')
        return redirect(url_for('loans.view_loan', id=id))

    # Check if loan is in correct status
    if loan.status not in ['Pending Guarantor Approval', 'Returned to Applicant']:
        flash('This loan is not pending guarantor approval!', 'warning')
        return redirect(url_for('loans.view_loan', id=id))

    # Get rejection reason
    rejection_reason = request.form.get('rejection_reason', '').strip()
    if not rejection_reason:
        flash('Please provide a reason for declining!', 'danger')
        return redirect(url_for('loans.view_loan', id=id))

    guarantor_name = guarantor_member.full_name

    # Decline based on which guarantor
    if is_guarantor1:
        if loan.guarantor1_approved is not None:
            flash('This guarantor has already responded to the request!', 'warning')
            return redirect(url_for('loans.view_loan', id=id))
        loan.guarantor1_approved = False
        loan.guarantor1_approval_date = datetime.now()
        loan.guarantor1_rejection_reason = rejection_reason
        guarantor_num = 1
    else:  # is_guarantor2
        if loan.guarantor2_approved is not None:
            flash('This guarantor has already responded to the request!', 'warning')
            return redirect(url_for('loans.view_loan', id=id))
        loan.guarantor2_approved = False
        loan.guarantor2_approval_date = datetime.now()
        loan.guarantor2_rejection_reason = rejection_reason
        guarantor_num = 2

    # Return loan to applicant
    loan.status = 'Returned to Applicant'

    db.session.commit()

    # Send notification to applicant
    from app.utils.notifications import NotificationService
    NotificationService.send_guarantor_rejection_notification(loan, guarantor_name, rejection_reason)

    # Log action
    from app.models.audit import AuditLog
    description = f'Declined loan {loan.loan_number} as Guarantor #{guarantor_num}: {rejection_reason}'
    if acting_as_admin:
        description += f' (on behalf of {guarantor_name})'
    AuditLog.log_action(
        user_id=current_user.id,
        action_type='GuarantorDeclined',
        entity_type='Loan',
        entity_id=loan.id,
        description=description,
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string
    )

    if acting_as_admin:
        flash(f"Recorded {guarantor_name}'s decline. The application has been returned to the applicant.", 'info')
        return redirect(url_for('loans.view_loan', id=id))

    flash('You have declined this guarantor request. The application has been returned to the applicant.', 'info')
    return redirect(url_for('main.dashboard'))


@loans.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_loan(id):
    """Edit and resubmit a returned loan application"""
    loan = Loan.query.get_or_404(id)

    # Check access: the applicant, or a SuperAdmin acting on their behalf, can edit
    if not (current_user.is_super_admin() or
            (hasattr(current_user, 'member') and loan.member_id == current_user.member.id)):
        flash('You do not have permission to edit this loan!', 'danger')
        return redirect(url_for('main.dashboard'))

    # Only allow editing if loan is "Returned to Applicant"
    if loan.status != 'Returned to Applicant':
        flash('Only returned loan applications can be edited!', 'warning')
        return redirect(url_for('loans.view_loan', id=id))

    if request.method == 'POST':
        # Get form data
        amount_requested = request.form.get('amount_requested')
        purpose = request.form.get('purpose')
        repayment_period = request.form.get('repayment_period_months')
        security_type = request.form.get('security_type')

        # Validate required fields
        if not all([amount_requested, purpose, repayment_period, security_type]):
            flash('All fields are required!', 'danger')
            return redirect(url_for('loans.edit_loan', id=id))

        # Update loan details
        loan.amount_requested = Decimal(amount_requested)
        loan.purpose = purpose
        loan.repayment_period_months = int(repayment_period)
        loan.security_type = security_type

        # Handle security type changes
        if security_type == 'Guarantors':
            guarantor1_id = request.form.get('guarantor1_id')
            guarantor2_id = request.form.get('guarantor2_id')

            if not guarantor1_id or not guarantor2_id:
                flash('Two guarantors are required!', 'danger')
                return redirect(url_for('loans.edit_loan', id=id))

            if guarantor1_id == guarantor2_id:
                flash('Guarantors must be different members!', 'danger')
                return redirect(url_for('loans.edit_loan', id=id))

            # Update guarantors
            loan.guarantor1_id = int(guarantor1_id)
            loan.guarantor2_id = int(guarantor2_id)

            # Reset guarantor approvals
            loan.guarantor1_approved = None
            loan.guarantor2_approved = None
            loan.guarantor1_approval_date = None
            loan.guarantor2_approval_date = None
            loan.guarantor1_rejection_reason = None
            loan.guarantor2_rejection_reason = None

            # Reset collateral fields
            loan.collateral_description = None
            loan.collateral_value = None
            loan.collateral_documents_path = None

            # Update status
            loan.status = 'Pending Guarantor Approval'

        elif security_type == 'Collateral':
            collateral_description = request.form.get('collateral_description')
            collateral_value = request.form.get('collateral_value')

            if not collateral_description or not collateral_value:
                flash('Collateral details are required!', 'danger')
                return redirect(url_for('loans.edit_loan', id=id))

            # Update collateral
            loan.collateral_description = collateral_description
            loan.collateral_value = Decimal(collateral_value)

            # Reset guarantor fields
            loan.guarantor1_id = None
            loan.guarantor2_id = None
            loan.guarantor1_approved = None
            loan.guarantor2_approved = None
            loan.guarantor1_approval_date = None
            loan.guarantor2_approval_date = None
            loan.guarantor1_rejection_reason = None
            loan.guarantor2_rejection_reason = None

            # Update status - skip guarantor approval
            loan.status = 'Pending Executive Approval'

        db.session.commit()

        # Send notifications to new guarantors if applicable
        if security_type == 'Guarantors':
            from app.utils.notifications import NotificationService
            guarantor1 = Member.query.get(loan.guarantor1_id)
            guarantor2 = Member.query.get(loan.guarantor2_id)

            if guarantor1:
                NotificationService.send_guarantor_request_notification(loan, guarantor1, 1)
            if guarantor2:
                NotificationService.send_guarantor_request_notification(loan, guarantor2, 2)

        # Log action
        from app.models.audit import AuditLog
        AuditLog.log_action(
            user_id=current_user.id,
            action_type='LoanResubmitted',
            entity_type='Loan',
            entity_id=loan.id,
            description=f'Resubmitted loan {loan.loan_number} after being returned',
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string
        )

        flash(f'Loan application resubmitted successfully! Status: {loan.status}', 'success')
        return redirect(url_for('loans.view_loan', id=id))

    # GET request - show edit form
    # Get only qualified members for guarantor selection (excluding the applicant)
    members = Member.query.filter_by(status='Active', qualified_for_benefits=True).filter(
        Member.id != loan.member_id
    ).order_by(Member.member_number).all()

    return render_template('loans/edit.html', loan=loan, members=members)


@loans.route('/<int:id>/cancel', methods=['POST'])
@login_required
def cancel_loan(id):
    """Cancel a returned loan application"""
    loan = Loan.query.get_or_404(id)

    # Check access: the applicant, or a SuperAdmin acting on their behalf, can cancel
    if not (current_user.is_super_admin() or
            (hasattr(current_user, 'member') and loan.member_id == current_user.member.id)):
        flash('You do not have permission to cancel this loan!', 'danger')
        return redirect(url_for('main.dashboard'))

    # Only allow canceling if loan is "Returned to Applicant" or "Pending Guarantor Approval"
    if loan.status not in ['Returned to Applicant', 'Pending Guarantor Approval']:
        flash('Only pending or returned loan applications can be canceled!', 'warning')
        return redirect(url_for('loans.view_loan', id=id))

    # Update status
    old_status = loan.status
    loan.status = 'Rejected'
    loan.approval_notes = f'Canceled by applicant (was {old_status})'
    loan.approval_date = date.today()

    db.session.commit()

    # Log action
    from app.models.audit import AuditLog
    AuditLog.log_action(
        user_id=current_user.id,
        action_type='LoanCanceled',
        entity_type='Loan',
        entity_id=loan.id,
        description=f'Canceled loan {loan.loan_number}',
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string
    )

    flash('Loan application has been canceled.', 'info')
    return redirect(url_for('main.dashboard'))


@loans.route('/<int:id>/application-fee', methods=['POST'])
@login_required
@executive_required
def record_application_fee(id):
    """Record (or update) the loan application fee deposited in the bank"""
    loan = Loan.query.get_or_404(id)

    try:
        amount = Decimal(request.form.get('amount'))
        if amount < 0:
            flash('Application fee cannot be negative!', 'danger')
            return redirect(url_for('loans.view_loan', id=id))
    except (ValueError, TypeError, InvalidOperation):
        flash('Invalid application fee amount!', 'danger')
        return redirect(url_for('loans.view_loan', id=id))

    fee_date_raw = request.form.get('fee_date')
    try:
        fee_date = datetime.strptime(fee_date_raw, '%Y-%m-%d').date() if fee_date_raw else date.today()
    except ValueError:
        flash('Invalid fee date!', 'danger')
        return redirect(url_for('loans.view_loan', id=id))

    was_recorded = loan.application_fee_paid

    loan.application_fee_amount = amount
    loan.application_fee_date = fee_date
    loan.application_fee_reference = request.form.get('reference') or None
    loan.application_fee_notes = request.form.get('notes') or None
    loan.application_fee_paid = True
    loan.application_fee_recorded_by = current_user.id

    db.session.commit()

    # Log action
    from app.models.audit import AuditLog
    action = 'LoanApplicationFeeUpdated' if was_recorded else 'LoanApplicationFeeRecorded'
    AuditLog.log_action(
        user_id=current_user.id,
        action_type=action,
        entity_type='Loan',
        entity_id=loan.id,
        description=f'{"Updated" if was_recorded else "Recorded"} application fee of UGX {float(amount):,.0f} for loan {loan.loan_number}',
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string
    )

    flash(f'Application fee of UGX {float(amount):,.0f} {"updated" if was_recorded else "recorded"}.', 'success')
    return redirect(url_for('loans.view_loan', id=id))


@loans.route('/<int:id>/shorten', methods=['POST'])
@login_required
@executive_required
def shorten_loan(id):
    """Shorten an active loan's repayment period (early payoff) and reduce interest"""
    loan = Loan.query.get_or_404(id)

    if loan.status not in ['Active', 'Disbursed']:
        flash('Only active (disbursed) loans can have their period adjusted!', 'warning')
        return redirect(url_for('loans.view_loan', id=id))

    try:
        new_months = int(request.form.get('repayment_period_months'))
    except (ValueError, TypeError):
        flash('Invalid repayment period!', 'danger')
        return redirect(url_for('loans.view_loan', id=id))

    if new_months < 1:
        flash('Repayment period must be at least 1 month!', 'danger')
        return redirect(url_for('loans.view_loan', id=id))

    if new_months >= loan.repayment_period_months:
        flash('The new period must be shorter than the current period.', 'warning')
        return redirect(url_for('loans.view_loan', id=id))

    old_months = loan.repayment_period_months
    old_total = float(loan.total_payable or 0)

    loan.repayment_period_months = new_months
    loan.recompute_payable()

    db.session.commit()

    # Log action
    from app.models.audit import AuditLog
    AuditLog.log_action(
        user_id=current_user.id,
        action_type='LoanPeriodShortened',
        entity_type='Loan',
        entity_id=loan.id,
        description=(f'Shortened loan {loan.loan_number} from {old_months} to {new_months} month(s); '
                     f'total payable {old_total:,.0f} -> {float(loan.total_payable):,.0f}'),
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string
    )

    msg = f'Loan period shortened to {new_months} month(s). New total payable: UGX {float(loan.total_payable):,.0f}.'
    if loan.status == 'Completed':
        msg += ' The loan balance is fully covered and it is now marked Completed.'
    flash(msg, 'success')
    return redirect(url_for('loans.view_loan', id=id))


@loans.route('/<int:id>/delete', methods=['POST'])
@login_required
@super_admin_required
def delete_loan(id):
    """Delete an un-guaranteed loan application (SuperAdmin only)"""
    loan = Loan.query.get_or_404(id)

    if not loan.can_be_deleted():
        flash('This loan cannot be deleted because it has already been guaranteed, approved, or disbursed.', 'danger')
        return redirect(url_for('loans.view_loan', id=id))

    loan_number = loan.loan_number

    # Remove any repayments first (none expected for un-disbursed loans), then the loan
    loan.repayments.delete()
    db.session.delete(loan)
    db.session.commit()

    # Log action
    from app.models.audit import AuditLog
    AuditLog.log_action(
        user_id=current_user.id,
        action_type='LoanDeleted',
        entity_type='Loan',
        entity_id=id,
        description=f'Deleted loan application {loan_number}',
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string
    )

    flash(f'Loan application {loan_number} has been deleted.', 'success')
    return redirect(url_for('loans.list_loans'))


@loans.route('/<int:id>/repayments/<int:repayment_id>/delete', methods=['POST'])
@login_required
@super_admin_required
def delete_repayment(id, repayment_id):
    """Reverse a wrongly entered loan repayment (SuperAdmin only).

    Deletes the LoanRepayment row and recomputes the loan's total_paid, balance
    and status from the repayments that remain, so a mistyped amount can be
    corrected without hand-editing the database. A reason is mandatory and is
    written to Loan.recovery_notes, which keeps the correction on the loan record
    itself in addition to the audit log.
    """
    loan = Loan.query.get_or_404(id)

    # Scope the repayment to this loan so a crafted id cannot reverse a payment
    # recorded against a different loan.
    repayment = LoanRepayment.query.filter_by(id=repayment_id, loan_id=loan.id).first()
    if repayment is None:
        flash('That repayment does not belong to this loan.', 'danger')
        return redirect(url_for('loans.view_loan', id=id))

    reason = (request.form.get('reason') or '').strip()
    if len(reason) < 5:
        flash('Please give a reason for deleting this repayment (at least 5 characters).', 'danger')
        return redirect(url_for('loans.view_loan', id=id))

    # Capture details before the row disappears
    receipt_number = repayment.receipt_number or f'#{repayment.id}'
    amount = float(repayment.amount_paid or 0)
    payment_date = repayment.payment_date
    status_before = loan.status
    balance_before = float(loan.balance or 0)

    db.session.delete(repayment)
    db.session.flush()  # exclude the deleted row from the recompute below
    loan.recompute_from_repayments()

    # Keep a permanent trace on the loan itself, not just in the audit log
    entry = (f"[{datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC] Repayment {receipt_number} of "
             f"UGX {amount:,.0f} dated {payment_date.strftime('%d/%m/%Y')} was deleted by "
             f"{current_user.username}. Reason: {reason}")
    loan.recovery_notes = f'{loan.recovery_notes}\n{entry}' if loan.recovery_notes else entry

    db.session.commit()

    # Log action
    from app.models.audit import AuditLog
    AuditLog.log_action(
        user_id=current_user.id,
        action_type='LoanRepaymentDeleted',
        entity_type='LoanRepayment',
        entity_id=repayment_id,
        description=(f'Deleted repayment {receipt_number} of UGX {amount:,.0f} on loan '
                     f'{loan.loan_number}. Reason: {reason}. Balance {balance_before:,.0f} '
                     f'-> {float(loan.balance or 0):,.0f}'),
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string
    )

    _notify_repayment_deleted(loan, receipt_number, amount, reason)

    msg = (f'Repayment {receipt_number} of UGX {amount:,.0f} has been deleted. '
           f'New balance: UGX {float(loan.balance or 0):,.0f}.')
    if status_before == 'Completed' and loan.status == 'Active':
        msg += ' The loan was re-opened as Active because a balance is now outstanding.'
    flash(msg, 'success')
    return redirect(url_for('loans.view_loan', id=id))


def _notify_repayment_deleted(loan, receipt_number, amount, reason):
    """Notify the borrower and the executives that a repayment was reversed.

    Money coming off a member's loan record must never be silent, so both the
    borrower and every executive/admin are told, whoever performed the correction.
    """
    from app.models.notification import Notification
    from app.models.user import User

    title = f'Repayment reversed on loan {loan.loan_number}'
    message = (f'A repayment of UGX {amount:,.0f} (receipt {receipt_number}) recorded against loan '
               f'{loan.loan_number} was entered in error and has been removed. Reason: {reason}. '
               f'The outstanding balance is now UGX {float(loan.balance or 0):,.0f}.')
    link = f'/loans/{loan.id}'

    if loan.member and getattr(loan.member, 'user', None):
        Notification.create_notification(
            user_id=loan.member.user.id, title=title, message=message,
            notification_type='Warning', category='Loan', link_url=link, priority='High'
        )

    exec_user_ids = [u.id for u in User.query.filter(User.role.in_(['Executive', 'SuperAdmin'])).all()]
    if exec_user_ids:
        Notification.create_bulk_notification(
            user_ids=exec_user_ids, title=title, message=message,
            notification_type='Warning', category='Loan', link_url=link, priority='High'
        )


@loans.route('/<int:id>/freeze-interest', methods=['POST'])
@login_required
@super_admin_required
def freeze_interest(id):
    """Freeze interest accrual on a running loan (SuperAdmin only).

    A frozen loan is skipped by the daily overdue auto-extension job, so no more
    monthly interest is added and its due date stops advancing. Only allowed once
    the loan has been running at least a month (Loan.can_freeze_interest()).
    Everything else - overdue display, reminders, repayments - is unchanged.
    """
    loan = Loan.query.get_or_404(id)

    if not loan.can_freeze_interest():
        flash('Interest cannot be frozen on this loan. It must be an active loan '
              'with an outstanding balance that has been running for at least one month.', 'danger')
        return redirect(url_for('loans.view_loan', id=id))

    reason = (request.form.get('reason') or '').strip()
    if len(reason) < 5:
        flash('Please give a reason for freezing interest (at least 5 characters).', 'danger')
        return redirect(url_for('loans.view_loan', id=id))

    loan.interest_frozen = True
    loan.interest_frozen_date = datetime.utcnow()
    loan.interest_frozen_by = current_user.id
    loan.interest_frozen_reason = reason

    entry = (f"[{datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC] Interest frozen by "
             f"{current_user.username} at balance UGX {float(loan.balance or 0):,.0f}. Reason: {reason}")
    loan.recovery_notes = f'{loan.recovery_notes}\n{entry}' if loan.recovery_notes else entry

    db.session.commit()

    from app.models.audit import AuditLog
    AuditLog.log_action(
        user_id=current_user.id,
        action_type='LoanInterestFrozen',
        entity_type='Loan',
        entity_id=loan.id,
        description=(f'Froze interest on loan {loan.loan_number} at balance '
                     f'UGX {float(loan.balance or 0):,.0f}. Reason: {reason}'),
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string
    )

    _notify_interest_freeze(loan, frozen=True, reason=reason)

    flash(f'Interest on loan {loan.loan_number} has been frozen. The balance will no '
          f'longer grow while frozen.', 'success')
    return redirect(url_for('loans.view_loan', id=id))


@loans.route('/<int:id>/unfreeze-interest', methods=['POST'])
@login_required
@super_admin_required
def unfreeze_interest(id):
    """Resume interest accrual on a frozen loan (SuperAdmin only).

    Clears the freeze so the overdue auto-extension job considers the loan again.
    Interest is not applied retroactively for the frozen period - accrual simply
    resumes from the current due date going forward.
    """
    loan = Loan.query.get_or_404(id)

    if not loan.interest_frozen:
        flash('This loan is not frozen.', 'warning')
        return redirect(url_for('loans.view_loan', id=id))

    reason = (request.form.get('reason') or '').strip()
    if len(reason) < 5:
        flash('Please give a reason for unfreezing interest (at least 5 characters).', 'danger')
        return redirect(url_for('loans.view_loan', id=id))

    loan.interest_frozen = False
    loan.interest_frozen_date = None
    loan.interest_frozen_by = None
    loan.interest_frozen_reason = None

    entry = (f"[{datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC] Interest unfrozen by "
             f"{current_user.username}. Reason: {reason}")
    loan.recovery_notes = f'{loan.recovery_notes}\n{entry}' if loan.recovery_notes else entry

    db.session.commit()

    from app.models.audit import AuditLog
    AuditLog.log_action(
        user_id=current_user.id,
        action_type='LoanInterestUnfrozen',
        entity_type='Loan',
        entity_id=loan.id,
        description=f'Resumed interest on loan {loan.loan_number}. Reason: {reason}',
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string
    )

    _notify_interest_freeze(loan, frozen=False, reason=reason)

    flash(f'Interest on loan {loan.loan_number} has resumed.', 'success')
    return redirect(url_for('loans.view_loan', id=id))


def _notify_interest_freeze(loan, frozen, reason):
    """Notify the borrower and the executives that interest was frozen or resumed."""
    from app.models.notification import Notification
    from app.models.user import User

    if frozen:
        title = f'Interest frozen on loan {loan.loan_number}'
        message = (f'Interest on loan {loan.loan_number} has been frozen. The outstanding balance '
                   f'of UGX {float(loan.balance or 0):,.0f} will not grow while frozen. Reason: {reason}.')
    else:
        title = f'Interest resumed on loan {loan.loan_number}'
        message = (f'Interest on loan {loan.loan_number} has resumed accruing from now on. '
                   f'Reason: {reason}.')
    link = f'/loans/{loan.id}'

    if loan.member and getattr(loan.member, 'user', None):
        Notification.create_notification(
            user_id=loan.member.user.id, title=title, message=message,
            notification_type='Info', category='Loan', link_url=link, priority='Normal'
        )

    exec_user_ids = [u.id for u in User.query.filter(User.role.in_(['Executive', 'SuperAdmin'])).all()]
    if exec_user_ids:
        Notification.create_bulk_notification(
            user_ids=exec_user_ids, title=title, message=message,
            notification_type='Info', category='Loan', link_url=link, priority='Normal'
        )
