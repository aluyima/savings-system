"""
Loans Routes
Handles loan applications, approvals, disbursements, and repayments
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, abort
from flask_login import login_required, current_user
from app import db
from app.models.loan import Loan, LoanRepayment
from app.models.member import Member
from app.utils.decorators import executive_required
from datetime import datetime, date
from decimal import Decimal
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
        member_id = current_user.member.id if hasattr(current_user, 'member') else request.form.get('member_id')

        if not member_id:
            flash('Invalid member selection!', 'danger')
            return redirect(url_for('loans.apply'))

        member = Member.query.get(member_id)
        if not member or member.status != 'Active':
            flash('Only active members can apply for loans!', 'danger')
            return redirect(url_for('loans.apply'))

        # Check if member has any active or pending loans
        existing_loan = Loan.query.filter_by(member_id=member.id).filter(
            Loan.status.in_(['Pending Guarantor Approval', 'Returned to Applicant', 'Pending Executive Approval', 'Approved', 'Disbursed', 'Active'])
        ).first()

        if existing_loan:
            flash(f'You already have a pending or active loan (Loan #{existing_loan.loan_number}, Status: {existing_loan.status})! Please complete or resolve your existing loan before applying for a new one.', 'warning')
            return redirect(url_for('loans.view_loan', id=existing_loan.id))

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
            interest_rate=Decimal(current_app.config.get('LOAN_INTEREST_RATE', '5.00')),
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
        members = Member.query.filter_by(status='Active').order_by(Member.member_number).all()
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


@loans.route('/<int:id>/guarantor/approve', methods=['POST'])
@login_required
def approve_as_guarantor(id):
    """Guarantor approves loan application"""
    loan = Loan.query.get_or_404(id)

    # Check if current user is a guarantor for this loan
    if not hasattr(current_user, 'member'):
        flash('You must be a member to approve as guarantor!', 'danger')
        return redirect(url_for('main.dashboard'))

    member_id = current_user.member.id
    is_guarantor1 = (loan.guarantor1_id == member_id)
    is_guarantor2 = (loan.guarantor2_id == member_id)

    if not (is_guarantor1 or is_guarantor2):
        flash('You are not a guarantor for this loan!', 'danger')
        return redirect(url_for('loans.view_loan', id=id))

    # Check if guarantor is qualified for benefits
    if not current_user.member.is_qualified():
        qualification_period = current_app.config.get('QUALIFICATION_PERIOD', 5)
        flash(f'You must be qualified to act as a guarantor! Please complete {qualification_period} consecutive months of contributions first.', 'danger')
        return redirect(url_for('loans.view_loan', id=id))

    # Check if loan is in correct status
    if loan.status not in ['Pending Guarantor Approval', 'Returned to Applicant']:
        flash('This loan is not pending guarantor approval!', 'warning')
        return redirect(url_for('loans.view_loan', id=id))

    # Approve based on which guarantor
    if is_guarantor1:
        if loan.guarantor1_approved is not None:
            flash('You have already responded to this guarantor request!', 'warning')
            return redirect(url_for('loans.view_loan', id=id))
        loan.guarantor1_approved = True
        loan.guarantor1_approval_date = datetime.now()
        guarantor_num = 1
    else:  # is_guarantor2
        if loan.guarantor2_approved is not None:
            flash('You have already responded to this guarantor request!', 'warning')
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
        flash_message = 'Thank you! You have approved this loan. Both guarantors have now approved - the loan is pending executive approval.'
    else:
        flash_message = f'Thank you! You have approved this loan as Guarantor #{guarantor_num}. Waiting for the other guarantor to approve.'

    db.session.commit()

    # Log action
    from app.models.audit import AuditLog
    AuditLog.log_action(
        user_id=current_user.id,
        action_type='GuarantorApproved',
        entity_type='Loan',
        entity_id=loan.id,
        description=f'Approved loan {loan.loan_number} as Guarantor #{guarantor_num}',
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string
    )

    flash(flash_message, 'success')
    return redirect(url_for('loans.view_loan', id=id))


@loans.route('/<int:id>/guarantor/decline', methods=['POST'])
@login_required
def decline_as_guarantor(id):
    """Guarantor declines loan application"""
    loan = Loan.query.get_or_404(id)

    # Check if current user is a guarantor for this loan
    if not hasattr(current_user, 'member'):
        flash('You must be a member to decline as guarantor!', 'danger')
        return redirect(url_for('main.dashboard'))

    member_id = current_user.member.id
    is_guarantor1 = (loan.guarantor1_id == member_id)
    is_guarantor2 = (loan.guarantor2_id == member_id)

    if not (is_guarantor1 or is_guarantor2):
        flash('You are not a guarantor for this loan!', 'danger')
        return redirect(url_for('loans.view_loan', id=id))

    # Check if guarantor is qualified for benefits
    if not current_user.member.is_qualified():
        qualification_period = current_app.config.get('QUALIFICATION_PERIOD', 5)
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

    # Decline based on which guarantor
    if is_guarantor1:
        if loan.guarantor1_approved is not None:
            flash('You have already responded to this guarantor request!', 'warning')
            return redirect(url_for('loans.view_loan', id=id))
        loan.guarantor1_approved = False
        loan.guarantor1_approval_date = datetime.now()
        loan.guarantor1_rejection_reason = rejection_reason
        guarantor_name = current_user.member.full_name
        guarantor_num = 1
    else:  # is_guarantor2
        if loan.guarantor2_approved is not None:
            flash('You have already responded to this guarantor request!', 'warning')
            return redirect(url_for('loans.view_loan', id=id))
        loan.guarantor2_approved = False
        loan.guarantor2_approval_date = datetime.now()
        loan.guarantor2_rejection_reason = rejection_reason
        guarantor_name = current_user.member.full_name
        guarantor_num = 2

    # Return loan to applicant
    loan.status = 'Returned to Applicant'

    db.session.commit()

    # Send notification to applicant
    from app.utils.notifications import NotificationService
    NotificationService.send_guarantor_rejection_notification(loan, guarantor_name, rejection_reason)

    # Log action
    from app.models.audit import AuditLog
    AuditLog.log_action(
        user_id=current_user.id,
        action_type='GuarantorDeclined',
        entity_type='Loan',
        entity_id=loan.id,
        description=f'Declined loan {loan.loan_number} as Guarantor #{guarantor_num}: {rejection_reason}',
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string
    )

    flash('You have declined this guarantor request. The application has been returned to the applicant.', 'info')
    return redirect(url_for('main.dashboard'))


@loans.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_loan(id):
    """Edit and resubmit a returned loan application"""
    loan = Loan.query.get_or_404(id)

    # Check access: only the applicant can edit their returned loan
    if not hasattr(current_user, 'member') or loan.member_id != current_user.member.id:
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

    # Check access: only the applicant can cancel their loan
    if not hasattr(current_user, 'member') or loan.member_id != current_user.member.id:
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
