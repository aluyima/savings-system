"""
Membership Fees Management Routes
Handles one-time membership fee payments of UGX 20,000
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, abort
from flask_login import login_required, current_user
from app import db
from app.models.member import Member
from app.models.contribution import Receipt
from app.utils.decorators import executive_required
from datetime import datetime, date
from decimal import Decimal

membership_fees = Blueprint('membership_fees', __name__, url_prefix='/membership-fees')


@membership_fees.route('/')
@login_required
def list_members():
    """List all members with their membership fee status - Auditors have read-only access"""
    if not (current_user.is_executive() or current_user.is_super_admin() or current_user.is_auditor()):
        abort(403)
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', '')
    search = request.args.get('search', '')

    query = Member.query

    # Apply status filter
    if status_filter == 'paid':
        query = query.filter(Member.membership_fee_paid == True)
    elif status_filter == 'unpaid':
        query = query.filter(Member.membership_fee_paid == False)

    # Apply search filter
    if search:
        query = query.filter(
            db.or_(
                Member.full_name.ilike(f'%{search}%'),
                Member.member_number.ilike(f'%{search}%')
            )
        )

    # Order by member number
    query = query.order_by(Member.member_number)

    # Paginate
    members_paginated = query.paginate(page=page, per_page=20, error_out=False)

    # Get statistics
    total_members = Member.query.count()
    paid_count = Member.query.filter_by(membership_fee_paid=True).count()
    unpaid_count = Member.query.filter_by(membership_fee_paid=False).count()
    total_collected = db.session.query(db.func.sum(Receipt.amount)).filter(
        Receipt.receipt_type == 'MembershipFee'
    ).scalar() or 0

    return render_template('membership_fees/list.html',
                         members=members_paginated,
                         total_members=total_members,
                         paid_count=paid_count,
                         unpaid_count=unpaid_count,
                         total_collected=total_collected,
                         status_filter=status_filter,
                         search=search,
                         membership_fee=current_app.config['MEMBERSHIP_FEE'])


@membership_fees.route('/record/<int:member_id>', methods=['GET', 'POST'])
@login_required
@executive_required
def record_payment(member_id):
    """Record membership fee payment for a member"""
    member = Member.query.get_or_404(member_id)

    if request.method == 'POST':
        # Check if already paid (with valid receipt)
        if member.membership_fee_paid and member.membership_fee_receipt:
            flash('Membership fee has already been paid for this member!', 'warning')
            return redirect(url_for('membership_fees.list_members'))

        # Parse payment date
        payment_date = None
        if request.form.get('payment_date'):
            try:
                payment_date = datetime.strptime(request.form.get('payment_date'), '%Y-%m-%d').date()
            except ValueError:
                flash('Invalid payment date format!', 'danger')
                return redirect(url_for('membership_fees.record_payment', member_id=member_id))

        if not payment_date:
            payment_date = date.today()

        # Validate transaction reference
        transaction_reference = request.form.get('transaction_reference', '').strip()
        if not transaction_reference:
            flash('Transaction reference is required!', 'danger')
            return redirect(url_for('membership_fees.record_payment', member_id=member_id))

        # Get membership fee amount
        membership_fee = current_app.config['MEMBERSHIP_FEE']

        # Generate receipt number
        today = date.today()
        year = today.year
        month = today.month
        prefix = f'MF-{year}-{month:02d}-'

        # Get the highest receipt number for this month
        result = db.session.execute(
            db.select(db.func.max(Receipt.receipt_number)).where(
                Receipt.receipt_number.like(f'{prefix}%')
            )
        ).scalar()

        if result:
            last_num = int(result.split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1

        receipt_number = f'{prefix}{new_num:04d}'

        # Create receipt
        receipt = Receipt(
            receipt_number=receipt_number,
            receipt_type='MembershipFee',
            member_id=member.id,
            amount=membership_fee,
            payment_date=payment_date,
            payment_method=request.form.get('payment_method'),
            transaction_reference=request.form.get('transaction_reference'),
            description=f'Membership Fee for {member.full_name} ({member.member_number})',
            generated_by=current_user.id
        )

        # Update member record
        member.membership_fee_paid = True
        member.membership_fee_date = payment_date
        member.membership_fee_receipt = receipt_number

        db.session.add(receipt)
        db.session.commit()

        flash(f'Membership fee recorded successfully! Receipt: {receipt_number}', 'success')
        return redirect(url_for('membership_fees.view_receipt', receipt_number=receipt_number))

    # GET request - show form
    return render_template('membership_fees/record.html',
                         member=member,
                         membership_fee=current_app.config['MEMBERSHIP_FEE'])


@membership_fees.route('/edit/<string:receipt_number>', methods=['GET', 'POST'])
@login_required
@executive_required
def edit_payment(receipt_number):
    """Edit membership fee payment"""
    receipt = Receipt.query.filter_by(receipt_number=receipt_number).first_or_404()

    if receipt.receipt_type != 'MembershipFee':
        flash('This is not a membership fee receipt!', 'danger')
        return redirect(url_for('membership_fees.list_members'))

    member = receipt.member

    if request.method == 'POST':
        try:
            # Update receipt details
            payment_date_str = request.form.get('payment_date')
            payment_date = datetime.strptime(payment_date_str, '%Y-%m-%d').date()

            receipt.payment_date = payment_date
            receipt.payment_method = request.form.get('payment_method')

            # Update member record
            member.membership_fee_date = payment_date

            db.session.commit()

            flash('Membership fee payment updated successfully!', 'success')
            return redirect(url_for('membership_fees.view_receipt', receipt_number=receipt_number))

        except Exception as e:
            db.session.rollback()
            flash(f'Error updating payment: {str(e)}', 'danger')
            return redirect(url_for('membership_fees.edit_payment', receipt_number=receipt_number))

    # GET request - show form
    return render_template('membership_fees/edit.html',
                         receipt=receipt,
                         member=member,
                         membership_fee=current_app.config['MEMBERSHIP_FEE'])


@membership_fees.route('/receipt/<string:receipt_number>')
@login_required
def view_receipt(receipt_number):
    """View membership fee receipt - Auditors have read-only access"""
    if not (current_user.is_executive() or current_user.is_super_admin() or current_user.is_auditor()):
        abort(403)
    receipt = Receipt.query.filter_by(receipt_number=receipt_number).first_or_404()

    if receipt.receipt_type != 'MembershipFee':
        flash('This is not a membership fee receipt!', 'danger')
        return redirect(url_for('membership_fees.list_members'))

    return render_template('membership_fees/receipt.html', receipt=receipt)


@membership_fees.route('/receipt/<string:receipt_number>/download')
@login_required
@executive_required
def download_receipt(receipt_number):
    """Generate and download PDF receipt"""
    from flask import send_file
    import io
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import inch
    from reportlab.pdfgen import canvas
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib import colors

    receipt = Receipt.query.filter_by(receipt_number=receipt_number).first_or_404()

    if receipt.receipt_type != 'MembershipFee':
        flash('This is not a membership fee receipt!', 'danger')
        return redirect(url_for('membership_fees.list_members'))

    # Create PDF in memory
    buffer = io.BytesIO()

    # Create PDF document
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []

    # Styles
    styles = getSampleStyleSheet()
    title_style = styles['Title']
    heading_style = styles['Heading2']
    normal_style = styles['Normal']

    # Header
    elements.append(Paragraph("Old Timers Savings Club Kiteezi", title_style))
    elements.append(Paragraph("P.O. Box 501056 Wandegeya, Kampala, Uganda", normal_style))
    elements.append(Paragraph("Tel: +256771804646/+256772302775", normal_style))
    elements.append(Spacer(1, 0.3*inch))

    # Receipt title
    elements.append(Paragraph(f"<b>MEMBERSHIP FEE RECEIPT</b>", heading_style))
    elements.append(Paragraph(f"Receipt No: {receipt.receipt_number}", normal_style))
    elements.append(Spacer(1, 0.2*inch))

    # Receipt details
    receipt_data = [
        ['Date:', receipt.payment_date.strftime('%d/%m/%Y')],
        ['Member Number:', receipt.member.member_number],
        ['Member Name:', receipt.member.full_name],
        ['Description:', 'One-time Membership Fee'],
        ['Amount Paid:', f'UGX {receipt.amount:,.2f}'],
        ['Payment Method:', receipt.payment_method],
        ['Transaction Ref:', receipt.transaction_reference or 'N/A'],
    ]

    receipt_table = Table(receipt_data, colWidths=[2*inch, 4*inch])
    receipt_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
    ]))

    elements.append(receipt_table)
    elements.append(Spacer(1, 0.5*inch))

    # Footer
    elements.append(Paragraph("Thank you for becoming a member of Old Timers Savings Club Kiteezi!", normal_style))
    elements.append(Spacer(1, 0.3*inch))
    elements.append(Paragraph(f"Recorded by: {receipt.generator.member.full_name}", normal_style))
    elements.append(Paragraph(f"Date Generated: {datetime.now().strftime('%d/%m/%Y %H:%M')}", normal_style))

    # Build PDF
    doc.build(elements)

    # Return PDF
    buffer.seek(0)
    return send_file(buffer,
                     mimetype='application/pdf',
                     as_attachment=True,
                     download_name=f'membership_fee_receipt_{receipt.receipt_number}.pdf')


@membership_fees.route('/unpaid')
@login_required
@executive_required
def unpaid_members():
    """List members who haven't paid membership fee"""
    page = request.args.get('page', 1, type=int)

    members_paginated = Member.query.filter_by(
        membership_fee_paid=False
    ).order_by(
        Member.member_number
    ).paginate(page=page, per_page=20, error_out=False)

    return render_template('membership_fees/unpaid.html',
                         members=members_paginated,
                         membership_fee=current_app.config['MEMBERSHIP_FEE'])
