"""
Expenses Routes
Handles operational expenses (stationery, airtime, transport, etc.)
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, abort
from flask_login import login_required, current_user
from app import db
from app.models.expense import Expense
from app.models.audit import AuditLog
from app.utils.decorators import executive_required
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import func, extract
from werkzeug.utils import secure_filename
import os

expenses = Blueprint('expenses', __name__, url_prefix='/expenses')


@expenses.route('/')
@login_required
def list_expenses():
    """List all operational expenses - Auditors have read-only access"""
    if not (current_user.is_executive() or current_user.is_super_admin() or current_user.is_auditor()):
        abort(403)
    category_filter = request.args.get('category', '')
    month_filter = request.args.get('month', type=int)
    year_filter = request.args.get('year', type=int, default=date.today().year)

    query = Expense.query

    if category_filter:
        query = query.filter(Expense.expense_category == category_filter)

    if month_filter:
        query = query.filter(
            extract('year', Expense.expense_date) == year_filter,
            extract('month', Expense.expense_date) == month_filter
        )
    else:
        query = query.filter(extract('year', Expense.expense_date) == year_filter)

    expenses_list = query.order_by(Expense.expense_date.desc()).all()

    # Calculate statistics
    total_expenses = sum(e.amount for e in expenses_list)

    # Group by category
    category_totals = db.session.query(
        Expense.expense_category,
        func.sum(Expense.amount)
    ).filter(
        extract('year', Expense.expense_date) == year_filter
    ).group_by(Expense.expense_category).all()

    return render_template('expenses/list.html',
                         expenses=expenses_list,
                         category_filter=category_filter,
                         month_filter=month_filter,
                         year_filter=year_filter,
                         total_expenses=total_expenses,
                         category_totals=category_totals)


@expenses.route('/record', methods=['GET', 'POST'])
@login_required
@executive_required
def record_expense():
    """Record a new operational expense"""
    if request.method == 'POST':
        expense_category = request.form.get('expense_category')
        description = request.form.get('description')
        payee = request.form.get('payee')
        payment_method = request.form.get('payment_method')
        reference_number = request.form.get('reference_number')
        notes = request.form.get('notes')

        # Validate required fields
        if not all([expense_category, description, payee]):
            flash('Category, description, and payee are required!', 'danger')
            return redirect(url_for('expenses.record_expense'))

        try:
            amount = Decimal(request.form.get('amount'))
            if amount <= 0:
                flash('Amount must be greater than zero!', 'danger')
                return redirect(url_for('expenses.record_expense'))
        except (ValueError, TypeError):
            flash('Invalid amount!', 'danger')
            return redirect(url_for('expenses.record_expense'))

        try:
            expense_date = datetime.strptime(request.form.get('expense_date'), '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid expense date!', 'danger')
            return redirect(url_for('expenses.record_expense'))

        # Handle receipt upload
        receipt_path = None
        if 'receipt_document' in request.files:
            file = request.files['receipt_document']
            if file and file.filename:
                # Validate file type
                allowed_extensions = {'pdf', 'jpg', 'jpeg', 'png'}
                if '.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in allowed_extensions:
                    filename = secure_filename(file.filename)
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    unique_filename = f"receipt_{timestamp}_{filename}"

                    receipts_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'receipts')
                    os.makedirs(receipts_folder, exist_ok=True)

                    file_path = os.path.join(receipts_folder, unique_filename)
                    file.save(file_path)
                    receipt_path = f"receipts/{unique_filename}"

        # Create expense
        expense = Expense(
            expense_number=Expense.generate_expense_number(),
            expense_category=expense_category,
            description=description,
            amount=amount,
            expense_date=expense_date,
            payment_method=payment_method,
            reference_number=reference_number,
            payee=payee,
            recorded_by=current_user.id,
            approved_by=current_user.id,  # Auto-approved for executives
            receipt_document_path=receipt_path,
            notes=notes
        )

        db.session.add(expense)
        db.session.commit()

        # Log action
        AuditLog.log_action(
            user_id=current_user.id,
            action_type='ExpenseRecorded',
            entity_type='Expense',
            entity_id=expense.id,
            description=f'Recorded expense: {expense.expense_number} - {expense.expense_category} - {amount}',
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string
        )

        flash(f'Expense recorded successfully! Expense Number: {expense.expense_number}', 'success')
        return redirect(url_for('expenses.view_expense', id=expense.id))

    # GET request - show form
    from datetime import date
    categories = ['Stationery', 'Airtime', 'Transport', 'Meetings', 'Bank Charges', 'Office Supplies', 'Other']
    today = date.today().strftime('%Y-%m-%d')
    return render_template('expenses/record.html', categories=categories, today=today)


@expenses.route('/<int:id>')
@login_required
def view_expense(id):
    """View expense details - Auditors have read-only access"""
    if not (current_user.is_executive() or current_user.is_super_admin() or current_user.is_auditor()):
        abort(403)
    expense = Expense.query.get_or_404(id)
    return render_template('expenses/view.html', expense=expense)


@expenses.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@executive_required
def edit_expense(id):
    """Edit an expense"""
    expense = Expense.query.get_or_404(id)

    if request.method == 'POST':
        expense.expense_category = request.form.get('expense_category')
        expense.description = request.form.get('description')
        expense.payee = request.form.get('payee')
        expense.payment_method = request.form.get('payment_method')
        expense.reference_number = request.form.get('reference_number')
        expense.notes = request.form.get('notes')

        try:
            expense.amount = Decimal(request.form.get('amount'))
            if expense.amount <= 0:
                flash('Amount must be greater than zero!', 'danger')
                return redirect(url_for('expenses.edit_expense', id=id))
        except (ValueError, TypeError):
            flash('Invalid amount!', 'danger')
            return redirect(url_for('expenses.edit_expense', id=id))

        try:
            expense.expense_date = datetime.strptime(request.form.get('expense_date'), '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid expense date!', 'danger')
            return redirect(url_for('expenses.edit_expense', id=id))

        db.session.commit()

        # Log action
        AuditLog.log_action(
            user_id=current_user.id,
            action_type='ExpenseUpdated',
            entity_type='Expense',
            entity_id=expense.id,
            description=f'Updated expense: {expense.expense_number}',
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string
        )

        flash('Expense updated successfully!', 'success')
        return redirect(url_for('expenses.view_expense', id=id))

    # GET request
    categories = ['Stationery', 'Airtime', 'Transport', 'Meetings', 'Bank Charges', 'Office Supplies', 'Other']
    return render_template('expenses/edit.html', expense=expense, categories=categories)


@expenses.route('/<int:id>/delete', methods=['POST'])
@login_required
@executive_required
def delete_expense(id):
    """Delete an expense (soft delete by marking as void)"""
    expense = Expense.query.get_or_404(id)

    # Instead of deleting, we could add a status field, but for now we'll allow deletion
    # Store info for logging
    expense_number = expense.expense_number
    category = expense.expense_category

    db.session.delete(expense)
    db.session.commit()

    # Log action
    AuditLog.log_action(
        user_id=current_user.id,
        action_type='ExpenseDeleted',
        entity_type='Expense',
        entity_id=id,
        description=f'Deleted expense: {expense_number} - {category}',
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string
    )

    flash('Expense deleted successfully!', 'success')
    return redirect(url_for('expenses.list_expenses'))
