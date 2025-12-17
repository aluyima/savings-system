"""
Welfare Routes
Handles welfare requests and payments for bereavement, medical, and celebrations
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from app import db
from app.models.welfare import WelfareRequest, WelfarePayment
from app.models.member import Member
from app.utils.decorators import executive_required
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import func

welfare = Blueprint('welfare', __name__, url_prefix='/welfare')


@welfare.route('/')
@login_required
def list_requests():
    """List all welfare requests"""
    status_filter = request.args.get('status', '')
    type_filter = request.args.get('type', '')

    query = WelfareRequest.query.join(Member, WelfareRequest.member_id == Member.id)

    if status_filter:
        query = query.filter(WelfareRequest.status == status_filter)

    if type_filter:
        query = query.filter(WelfareRequest.request_type == type_filter)

    # Check access - Auditors can see all, Members see only their own
    if current_user.is_executive() or current_user.is_super_admin() or current_user.is_auditor():
        # Executives and Auditors can see all requests
        pass
    else:
        # Members can only see their own requests
        if hasattr(current_user, 'member'):
            query = query.filter(WelfareRequest.member_id == current_user.member.id)
        else:
            query = query.filter(WelfareRequest.id == -1)  # No results

    requests_list = query.order_by(WelfareRequest.submitted_date.desc()).all()

    # Calculate statistics for executives and auditors
    stats = {}
    if current_user.is_executive() or current_user.is_super_admin() or current_user.is_auditor():
        stats['pending'] = WelfareRequest.query.filter_by(status='Submitted').count()
        stats['approved'] = WelfareRequest.query.filter_by(status='Approved').count()
        stats['total_paid'] = db.session.query(func.sum(WelfarePayment.amount_paid)).scalar() or 0

    return render_template('welfare/list.html',
                         requests=requests_list,
                         status_filter=status_filter,
                         type_filter=type_filter,
                         stats=stats)


@welfare.route('/request', methods=['GET', 'POST'])
@login_required
def submit_request():
    """Submit a welfare request"""
    if request.method == 'POST':
        member_id = current_user.member.id if hasattr(current_user, 'member') else request.form.get('member_id')

        if not member_id:
            flash('Invalid member selection!', 'danger')
            return redirect(url_for('welfare.submit_request'))

        member = Member.query.get(member_id)
        if not member or member.status != 'Active':
            flash('Only active members can submit welfare requests!', 'danger')
            return redirect(url_for('welfare.submit_request'))

        try:
            incident_date = datetime.strptime(request.form.get('incident_date'), '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid incident date!', 'danger')
            return redirect(url_for('welfare.submit_request'))

        # Generate request number
        today = date.today()
        year = today.year
        prefix = f'WR-{year}-'

        result = db.session.execute(
            db.select(func.max(WelfareRequest.request_number)).where(
                WelfareRequest.request_number.like(f'{prefix}%')
            )
        ).scalar()

        if result:
            last_num = int(result.split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1

        request_number = f'{prefix}{new_num:04d}'

        # Get amount requested if provided
        amount_requested = None
        if request.form.get('amount_requested'):
            try:
                amount_requested = Decimal(request.form.get('amount_requested'))
            except (ValueError, TypeError):
                pass

        # Create welfare request
        welfare_request = WelfareRequest(
            request_number=request_number,
            member_id=member.id,
            request_type=request.form.get('request_type'),
            affected_person=request.form.get('affected_person'),
            relationship=request.form.get('relationship'),
            incident_date=incident_date,
            description=request.form.get('description'),
            amount_requested=amount_requested,
            status='Submitted',
            submitted_date=datetime.utcnow()
        )

        db.session.add(welfare_request)
        db.session.commit()

        flash(f'Welfare request submitted successfully! Request Number: {request_number}', 'success')
        return redirect(url_for('welfare.view_request', id=welfare_request.id))

    # GET request - show form
    if current_user.is_executive() or current_user.is_super_admin():
        members = Member.query.filter_by(status='Active').order_by(Member.member_number).all()
    else:
        members = [current_user.member] if hasattr(current_user, 'member') else []

    return render_template('welfare/request.html', members=members)


@welfare.route('/<int:id>')
@login_required
def view_request(id):
    """View welfare request details"""
    welfare_request = WelfareRequest.query.get_or_404(id)

    # Check access - Auditors can view all, Members can view their own
    if not (current_user.is_executive() or current_user.is_super_admin() or current_user.is_auditor()):
        if not hasattr(current_user, 'member') or welfare_request.member_id != current_user.member.id:
            flash('You do not have permission to view this request!', 'danger')
            return redirect(url_for('main.dashboard'))

    return render_template('welfare/view.html', welfare_request=welfare_request)


@welfare.route('/<int:id>/review', methods=['POST'])
@login_required
@executive_required
def review_request(id):
    """Secretary reviews welfare request"""
    welfare_request = WelfareRequest.query.get_or_404(id)

    if welfare_request.status != 'Submitted':
        flash('Only submitted requests can be reviewed!', 'warning')
        return redirect(url_for('welfare.view_request', id=id))

    welfare_request.status = 'UnderReview'
    welfare_request.reviewed_by_secretary = current_user.id
    welfare_request.secretary_review_date = datetime.utcnow()
    welfare_request.secretary_notes = request.form.get('secretary_notes')

    db.session.commit()

    flash('Request marked as under review!', 'success')
    return redirect(url_for('welfare.view_request', id=id))


@welfare.route('/<int:id>/approve', methods=['POST'])
@login_required
@executive_required
def approve_request(id):
    """Chairman approves welfare request"""
    welfare_request = WelfareRequest.query.get_or_404(id)

    if welfare_request.status not in ['Submitted', 'UnderReview']:
        flash('Only pending requests can be approved!', 'warning')
        return redirect(url_for('welfare.view_request', id=id))

    try:
        amount_approved = Decimal(request.form.get('amount_approved'))
        if amount_approved <= 0:
            flash('Approved amount must be greater than zero!', 'danger')
            return redirect(url_for('welfare.view_request', id=id))
    except (ValueError, TypeError):
        flash('Invalid approved amount!', 'danger')
        return redirect(url_for('welfare.view_request', id=id))

    welfare_request.status = 'Approved'
    welfare_request.approved_by_chairman = current_user.id
    welfare_request.chairman_approval_date = datetime.utcnow()
    welfare_request.amount_approved = amount_approved
    welfare_request.chairman_notes = request.form.get('chairman_notes')

    db.session.commit()

    flash('Welfare request approved!', 'success')
    return redirect(url_for('welfare.view_request', id=id))


@welfare.route('/<int:id>/reject', methods=['POST'])
@login_required
@executive_required
def reject_request(id):
    """Reject welfare request"""
    welfare_request = WelfareRequest.query.get_or_404(id)

    if welfare_request.status not in ['Submitted', 'UnderReview']:
        flash('Only pending requests can be rejected!', 'warning')
        return redirect(url_for('welfare.view_request', id=id))

    welfare_request.status = 'Rejected'
    welfare_request.rejection_reason = request.form.get('rejection_reason')
    welfare_request.approved_by_chairman = current_user.id
    welfare_request.chairman_approval_date = datetime.utcnow()

    db.session.commit()

    flash('Welfare request rejected.', 'info')
    return redirect(url_for('welfare.view_request', id=id))


@welfare.route('/<int:id>/pay', methods=['GET', 'POST'])
@login_required
@executive_required
def record_payment(id):
    """Record payment for approved welfare request"""
    welfare_request = WelfareRequest.query.get_or_404(id)

    if welfare_request.status != 'Approved':
        flash('Only approved requests can be paid!', 'warning')
        return redirect(url_for('welfare.view_request', id=id))

    if welfare_request.payment:
        flash('Payment has already been recorded for this request!', 'warning')
        return redirect(url_for('welfare.view_request', id=id))

    if request.method == 'POST':
        try:
            amount_paid = Decimal(request.form.get('amount_paid'))
            if amount_paid <= 0:
                flash('Payment amount must be greater than zero!', 'danger')
                return redirect(url_for('welfare.record_payment', id=id))
        except (ValueError, TypeError):
            flash('Invalid payment amount!', 'danger')
            return redirect(url_for('welfare.record_payment', id=id))

        try:
            payment_date = datetime.strptime(request.form.get('payment_date'), '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid payment date!', 'danger')
            return redirect(url_for('welfare.record_payment', id=id))

        # Handle withdrawal document upload
        if 'withdrawal_document' not in request.files:
            flash('Bank withdrawal document is required!', 'danger')
            return redirect(url_for('welfare.record_payment', id=id))

        withdrawal_file = request.files['withdrawal_document']
        if withdrawal_file.filename == '':
            flash('No withdrawal document selected!', 'danger')
            return redirect(url_for('welfare.record_payment', id=id))

        # Handle beneficiary receipt upload
        if 'beneficiary_receipt' not in request.files:
            flash('Beneficiary proof of receipt is required!', 'danger')
            return redirect(url_for('welfare.record_payment', id=id))

        receipt_file = request.files['beneficiary_receipt']
        if receipt_file.filename == '':
            flash('No beneficiary receipt selected!', 'danger')
            return redirect(url_for('welfare.record_payment', id=id))

        # Generate voucher number
        year = payment_date.year
        prefix = f'WV-{year}-'

        result = db.session.execute(
            db.select(func.max(WelfarePayment.payment_voucher_number)).where(
                WelfarePayment.payment_voucher_number.like(f'{prefix}%')
            )
        ).scalar()

        if result:
            last_num = int(result.split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1

        voucher_number = f'{prefix}{new_num:04d}'

        # Save withdrawal document
        from werkzeug.utils import secure_filename
        import os

        withdrawal_filename = secure_filename(withdrawal_file.filename)
        withdrawal_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        withdrawal_unique_filename = f"{voucher_number}_withdrawal_{withdrawal_timestamp}_{withdrawal_filename}"

        withdrawal_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'welfare_withdrawals')
        os.makedirs(withdrawal_folder, exist_ok=True)

        withdrawal_file_path = os.path.join(withdrawal_folder, withdrawal_unique_filename)
        withdrawal_file.save(withdrawal_file_path)

        # Save beneficiary receipt
        receipt_filename = secure_filename(receipt_file.filename)
        receipt_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        receipt_unique_filename = f"{voucher_number}_receipt_{receipt_timestamp}_{receipt_filename}"

        receipts_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'welfare_receipts')
        os.makedirs(receipts_folder, exist_ok=True)

        receipt_file_path = os.path.join(receipts_folder, receipt_unique_filename)
        receipt_file.save(receipt_file_path)

        # Create payment record
        payment = WelfarePayment(
            welfare_request_id=welfare_request.id,
            payment_voucher_number=voucher_number,
            amount_paid=amount_paid,
            payment_date=payment_date,
            payment_method='Cash Withdrawal from Bank Account',
            withdrawal_reference=request.form.get('withdrawal_reference'),
            withdrawal_document_path=f"welfare_withdrawals/{withdrawal_unique_filename}",
            transaction_reference=request.form.get('transaction_reference'),
            beneficiary_name=request.form.get('beneficiary_name'),
            beneficiary_phone=request.form.get('beneficiary_phone'),
            beneficiary_receipt_path=f"welfare_receipts/{receipt_unique_filename}",
            paid_by_treasurer=current_user.id,
            confirmed_by_secretary=current_user.id,  # Simplified - in production would be different users
            notes=request.form.get('notes')
        )

        db.session.add(payment)
        welfare_request.status = 'Paid'
        welfare_request.payment_voucher_number = voucher_number

        db.session.commit()

        flash(f'Payment recorded successfully! Voucher: {voucher_number}', 'success')
        return redirect(url_for('welfare.view_request', id=id))

    return render_template('welfare/pay.html', welfare_request=welfare_request)
