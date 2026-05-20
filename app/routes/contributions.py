"""
Contributions Management Routes
Handles member contributions, receipts, and batch processing
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file, abort
from flask_login import login_required, current_user
from app import db
from app.models.member import Member
from app.models.contribution import Contribution, Receipt
from app.utils.decorators import executive_required
from datetime import datetime, date
from sqlalchemy import extract, func
from decimal import Decimal
import io
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors

contributions = Blueprint('contributions', __name__, url_prefix='/contributions')


@contributions.route('/')
@login_required
def list_contributions():
    # Auditors can view but not modify
    if not (current_user.is_executive() or current_user.is_super_admin() or current_user.is_auditor()):
        abort(403)
    """List all contributions with filtering"""
    page = request.args.get('page', 1, type=int)
    month = request.args.get('month', '')
    member_number = request.args.get('member_number', '')
    payment_method = request.args.get('payment_method', '')

    query = Contribution.query

    # Apply filters
    if month:
        query = query.filter(Contribution.contribution_month == month)

    if member_number:
        member = Member.query.filter_by(member_number=member_number).first()
        if member:
            query = query.filter(Contribution.member_id == member.id)

    if payment_method:
        query = query.filter(Contribution.payment_method == payment_method)

    # Order by payment date descending
    query = query.order_by(Contribution.payment_date.desc())

    # Paginate
    contributions_paginated = query.paginate(page=page, per_page=20, error_out=False)

    # Get summary statistics for current filters
    total_amount = db.session.query(func.sum(Contribution.amount)).filter(
        *[filter for filter in [
            Contribution.contribution_month == month if month else None,
            Contribution.member_id == member.id if member_number and member else None,
            Contribution.payment_method == payment_method if payment_method else None
        ] if filter is not None]
    ).scalar() or 0

    total_contributions = query.count()

    return render_template('contributions/list.html',
                         contributions=contributions_paginated,
                         total_amount=total_amount,
                         total_contributions=total_contributions,
                         month=month,
                         member_number=member_number,
                         payment_method=payment_method)


@contributions.route('/add', methods=['GET', 'POST'])
@login_required
@executive_required
def add_contribution():
    """Add a new contribution"""
    if request.method == 'POST':
        member_id = request.form.get('member_id')

        if not member_id:
            flash('Please select a member!', 'danger')
            return redirect(url_for('contributions.add_contribution'))

        member = Member.query.get(member_id)

        if not member:
            flash('Member not found!', 'danger')
            return redirect(url_for('contributions.add_contribution'))

        if member.status != 'Active':
            flash(f'Cannot record contribution for {member.status} member!', 'warning')
            return redirect(url_for('contributions.add_contribution'))

        # Parse payment date
        payment_date = None
        if request.form.get('payment_date'):
            try:
                payment_date = datetime.strptime(request.form.get('payment_date'), '%Y-%m-%d').date()
            except ValueError:
                flash('Invalid payment date format!', 'danger')
                return redirect(url_for('contributions.add_contribution'))

        if not payment_date:
            payment_date = date.today()

        # Parse contribution month
        contribution_month = request.form.get('contribution_month')
        if not contribution_month:
            # Default to current month
            contribution_month = date.today().strftime('%Y-%m')

        # Parse amount
        try:
            amount = Decimal(request.form.get('amount', '0'))
            if amount <= 0:
                flash('Amount must be greater than zero!', 'danger')
                return redirect(url_for('contributions.add_contribution'))
        except (ValueError, TypeError):
            flash('Invalid amount!', 'danger')
            return redirect(url_for('contributions.add_contribution'))

        # Validate transaction reference (required for bank deposits)
        transaction_reference = request.form.get('transaction_reference', '').strip()
        if not transaction_reference:
            flash('Transaction reference is required for all bank deposits!', 'danger')
            return redirect(url_for('contributions.add_contribution'))

        # Create contribution
        contribution = Contribution(
            member_id=member.id,
            amount=amount,
            payment_date=payment_date,
            contribution_month=contribution_month,
            payment_method=request.form.get('payment_method'),
            transaction_reference=transaction_reference,
            notes=request.form.get('notes') or None,
            recorded_by=current_user.id
        )

        db.session.add(contribution)
        db.session.commit()

        # Update member contribution stats
        member.update_contribution_stats()
        db.session.commit()

        flash(f'Contribution recorded successfully! Receipt: {contribution.receipt_number}', 'success')
        return redirect(url_for('contributions.view_contribution', id=contribution.id))

    # GET request - show form
    # Get current month as default
    current_month = date.today().strftime('%Y-%m')

    # Get all active members for dropdown
    members = Member.query.filter_by(status='Active').order_by(Member.member_number).all()

    return render_template('contributions/add.html', current_month=current_month, members=members)


@contributions.route('/<int:id>')
@login_required
def view_contribution(id):
    """View contribution details - Auditors have read-only access"""
    if not (current_user.is_executive() or current_user.is_super_admin() or current_user.is_auditor()):
        abort(403)
    contribution = Contribution.query.get_or_404(id)
    return render_template('contributions/view.html', contribution=contribution)


@contributions.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@executive_required
def edit_contribution(id):
    """Edit contribution details"""
    contribution = Contribution.query.get_or_404(id)

    if request.method == 'POST':
        # Parse payment date
        payment_date = None
        if request.form.get('payment_date'):
            try:
                payment_date = datetime.strptime(request.form.get('payment_date'), '%Y-%m-%d').date()
            except ValueError:
                flash('Invalid payment date format!', 'danger')
                return redirect(url_for('contributions.edit_contribution', id=id))

        if not payment_date:
            flash('Payment date is required!', 'danger')
            return redirect(url_for('contributions.edit_contribution', id=id))

        # Parse amount
        try:
            amount = Decimal(request.form.get('amount', '0'))
            if amount <= 0:
                flash('Amount must be greater than zero!', 'danger')
                return redirect(url_for('contributions.edit_contribution', id=id))
        except (ValueError, TypeError):
            flash('Invalid amount!', 'danger')
            return redirect(url_for('contributions.edit_contribution', id=id))

        # Validate transaction reference (required for bank deposits)
        transaction_reference = request.form.get('transaction_reference', '').strip()
        if not transaction_reference:
            flash('Transaction reference is required for all bank deposits!', 'danger')
            return redirect(url_for('contributions.edit_contribution', id=id))

        # Update contribution
        contribution.amount = amount
        contribution.payment_date = payment_date
        contribution.payment_method = request.form.get('payment_method')
        contribution.transaction_reference = transaction_reference
        contribution.notes = request.form.get('notes') or None

        db.session.commit()

        # Update member contribution stats
        contribution.member.update_contribution_stats()
        db.session.commit()

        flash('Contribution updated successfully!', 'success')
        return redirect(url_for('contributions.view_contribution', id=id))

    return render_template('contributions/edit.html', contribution=contribution)


@contributions.route('/<int:id>/delete', methods=['POST'])
@login_required
@executive_required
def delete_contribution(id):
    """Delete a contribution"""
    contribution = Contribution.query.get_or_404(id)
    member = contribution.member  # Store reference before deletion

    # Delete associated receipt if exists
    if contribution.receipt:
        db.session.delete(contribution.receipt)

    db.session.delete(contribution)
    db.session.commit()

    # Update member contribution stats
    member.update_contribution_stats()
    db.session.commit()

    flash('Contribution deleted successfully!', 'success')
    return redirect(url_for('contributions.list_contributions'))


@contributions.route('/batch', methods=['GET', 'POST'])
@login_required
@executive_required
def batch_contributions():
    """Process batch contributions for a month"""
    if request.method == 'POST':
        contribution_month = request.form.get('contribution_month')

        if not contribution_month:
            flash('Contribution month is required!', 'danger')
            return redirect(url_for('contributions.batch_contributions'))

        # Validate month format
        try:
            datetime.strptime(contribution_month, '%Y-%m')
        except ValueError:
            flash('Invalid contribution month format!', 'danger')
            return redirect(url_for('contributions.batch_contributions'))

        # Get all member contributions for this batch
        member_ids = request.form.getlist('member_ids[]')
        amounts = request.form.getlist('amounts[]')
        payment_dates = request.form.getlist('payment_dates[]')
        payment_methods = request.form.getlist('payment_methods[]')
        transaction_references = request.form.getlist('transaction_references[]')

        if not member_ids:
            flash('No members selected!', 'warning')
            return redirect(url_for('contributions.batch_contributions'))

        success_count = 0
        error_count = 0
        errors = []
        updated_members = set()  # Track members that need stats update

        for i, member_id in enumerate(member_ids):
            member = Member.query.get(member_id)
            if not member:
                continue

            # Check for existing contribution
            existing = Contribution.query.filter_by(
                member_id=member.id,
                contribution_month=contribution_month
            ).first()

            if existing:
                errors.append(f'{member.member_number}: Already has contribution for {contribution_month}')
                error_count += 1
                continue

            # Parse amount
            try:
                amount = Decimal(amounts[i])
                if amount <= 0:
                    errors.append(f'{member.member_number}: Invalid amount')
                    error_count += 1
                    continue
            except (ValueError, TypeError, IndexError):
                errors.append(f'{member.member_number}: Invalid amount')
                error_count += 1
                continue

            # Parse payment date
            try:
                payment_date = datetime.strptime(payment_dates[i], '%Y-%m-%d').date()
            except (ValueError, IndexError):
                payment_date = date.today()

            # Get transaction reference
            transaction_reference = transaction_references[i] if i < len(transaction_references) else None
            if transaction_reference:
                transaction_reference = transaction_reference.strip() or None

            # Create contribution
            contribution = Contribution(
                member_id=member.id,
                amount=amount,
                payment_date=payment_date,
                contribution_month=contribution_month,
                payment_method=payment_methods[i] if i < len(payment_methods) else 'Cash',
                transaction_reference=transaction_reference,
                recorded_by=current_user.id
            )

            db.session.add(contribution)
            updated_members.add(member)  # Track member for stats update
            success_count += 1

        db.session.commit()

        # Update contribution stats for all affected members
        for member in updated_members:
            member.update_contribution_stats()
        db.session.commit()

        flash(f'Batch processing complete! Success: {success_count}, Errors: {error_count}', 'success')
        if errors:
            for error in errors:
                flash(error, 'warning')

        return redirect(url_for('contributions.list_contributions', month=contribution_month))

    # GET request - show batch form
    # Get all active members
    members = Member.query.filter_by(status='Active').order_by(Member.member_number).all()
    current_month = date.today().strftime('%Y-%m')

    return render_template('contributions/batch.html', members=members, current_month=current_month)


@contributions.route('/<int:id>/receipt')
@login_required
@executive_required
def generate_receipt(id):
    """Generate PDF receipt for a contribution"""
    contribution = Contribution.query.get_or_404(id)

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
    elements.append(Paragraph(f"<b>CONTRIBUTION RECEIPT</b>", heading_style))
    elements.append(Paragraph(f"Receipt No: {contribution.receipt_number}", normal_style))
    elements.append(Spacer(1, 0.2*inch))

    # Receipt details
    receipt_data = [
        ['Date:', contribution.payment_date.strftime('%d/%m/%Y')],
        ['Member Number:', contribution.member.member_number],
        ['Member Name:', contribution.member.full_name],
        ['Contribution Month:', datetime.strptime(contribution.contribution_month, '%Y-%m').strftime('%B %Y')],
        ['Amount Paid:', f'UGX {contribution.amount:,.2f}'],
        ['Payment Method:', contribution.payment_method],
        ['Transaction Ref:', contribution.transaction_reference or 'N/A'],
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
    elements.append(Paragraph("Thank you for your contribution!", normal_style))
    elements.append(Spacer(1, 0.3*inch))
    elements.append(Paragraph(f"Recorded by: {contribution.recorder.member.full_name}", normal_style))
    elements.append(Paragraph(f"Date Generated: {datetime.now().strftime('%d/%m/%Y %H:%M')}", normal_style))

    # Build PDF
    doc.build(elements)

    # Return PDF
    buffer.seek(0)
    return send_file(buffer,
                     mimetype='application/pdf',
                     as_attachment=True,
                     download_name=f'receipt_{contribution.receipt_number}.pdf')


@contributions.route('/summary')
@login_required
@executive_required
def contributions_summary():
    """View contributions summary and statistics"""
    # Get current year
    current_year = date.today().year
    year = request.args.get('year', current_year, type=int)

    # Monthly summary for the year
    monthly_data = db.session.query(
        Contribution.contribution_month,
        func.count(Contribution.id).label('count'),
        func.sum(Contribution.amount).label('total')
    ).filter(
        extract('year', func.cast(Contribution.contribution_month + '-01', db.Date)) == year
    ).group_by(
        Contribution.contribution_month
    ).order_by(
        Contribution.contribution_month
    ).all()

    # Top contributors for the year
    top_contributors = db.session.query(
        Member,
        func.count(Contribution.id).label('contribution_count'),
        func.sum(Contribution.amount).label('total_amount')
    ).join(
        Contribution, Member.id == Contribution.member_id
    ).filter(
        extract('year', func.cast(Contribution.contribution_month + '-01', db.Date)) == year
    ).group_by(
        Member.id
    ).order_by(
        func.sum(Contribution.amount).desc()
    ).limit(10).all()

    # Payment method breakdown
    payment_methods = db.session.query(
        Contribution.payment_method,
        func.count(Contribution.id).label('count'),
        func.sum(Contribution.amount).label('total')
    ).filter(
        extract('year', func.cast(Contribution.contribution_month + '-01', db.Date)) == year
    ).group_by(
        Contribution.payment_method
    ).all()

    # Total statistics
    total_year = db.session.query(
        func.count(Contribution.id),
        func.sum(Contribution.amount)
    ).filter(
        extract('year', func.cast(Contribution.contribution_month + '-01', db.Date)) == year
    ).first()

    return render_template('contributions/summary.html',
                         monthly_data=monthly_data,
                         top_contributors=top_contributors,
                         payment_methods=payment_methods,
                         total_count=total_year[0] or 0,
                         total_amount=total_year[1] or 0,
                         year=year)


@contributions.route('/member/<int:member_id>')
@login_required
def member_contributions(member_id):
    """View all contributions for a specific member"""
    member = Member.query.get_or_404(member_id)

    # Check permission - executives can view all, members can only view their own
    if not current_user.is_executive() and not current_user.is_super_admin():
        if not current_user.member or current_user.member.id != member_id:
            flash('You do not have permission to view this page.', 'danger')
            return redirect(url_for('main.dashboard'))

    page = request.args.get('page', 1, type=int)

    contributions_paginated = Contribution.query.filter_by(
        member_id=member_id
    ).order_by(
        Contribution.contribution_month.desc()
    ).paginate(page=page, per_page=12, error_out=False)

    # Summary statistics
    total_contributions = Contribution.query.filter_by(member_id=member_id).count()
    total_amount = db.session.query(func.sum(Contribution.amount)).filter_by(
        member_id=member_id
    ).scalar() or 0

    return render_template('contributions/member_contributions.html',
                         member=member,
                         contributions=contributions_paginated,
                         total_contributions=total_contributions,
                         total_amount=total_amount)
