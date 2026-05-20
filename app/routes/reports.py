"""
Reports Routes
Handles financial reports, member statements, and analytics
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, abort
from flask_login import login_required, current_user
from app import db
from app.models.member import Member
from app.models.contribution import Contribution, Receipt
from app.models.loan import Loan, LoanRepayment
from app.models.welfare import WelfareRequest, WelfarePayment
from app.models.meeting import Meeting, Attendance
from app.models.expense import Expense
from app.utils.decorators import executive_required
from datetime import datetime, date
from sqlalchemy import func, extract, and_, or_
from decimal import Decimal

reports = Blueprint('reports', __name__, url_prefix='/reports')


@reports.route('/')
@login_required
def reports_index():
    """Reports dashboard - accessible to all authenticated users"""
    return render_template('reports/index.html')


@reports.route('/financial-summary')
@login_required
def financial_summary():
    """Financial summary report - accessible to Executives and Members"""
    # Get date filters
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')

    # Default to current year if no dates provided
    if not start_date_str:
        start_date = date(date.today().year, 1, 1)
    else:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()

    if not end_date_str:
        end_date = date.today()
    else:
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

    # Membership Fees (from Receipt table with type 'MembershipFee')
    membership_fees_total = db.session.query(func.sum(Receipt.amount)).filter(
        and_(
            Receipt.payment_date >= start_date,
            Receipt.payment_date <= end_date,
            Receipt.receipt_type == 'MembershipFee'
        )
    ).scalar() or 0

    # Contributions
    contributions_total = db.session.query(func.sum(Contribution.amount)).filter(
        and_(
            Contribution.payment_date >= start_date,
            Contribution.payment_date <= end_date
        )
    ).scalar() or 0

    # Loan Repayments
    loan_repayments_total = db.session.query(func.sum(LoanRepayment.amount_paid)).filter(
        and_(
            LoanRepayment.payment_date >= start_date,
            LoanRepayment.payment_date <= end_date
        )
    ).scalar() or 0

    # Total Income
    total_income = membership_fees_total + contributions_total + loan_repayments_total

    # Loan Disbursements
    loans_disbursed = db.session.query(func.sum(Loan.amount_approved)).filter(
        and_(
            Loan.disbursement_date >= start_date,
            Loan.disbursement_date <= end_date,
            Loan.disbursed == True
        )
    ).scalar() or 0

    # Welfare Payments
    welfare_payments = db.session.query(func.sum(WelfarePayment.amount_paid)).filter(
        and_(
            WelfarePayment.payment_date >= start_date,
            WelfarePayment.payment_date <= end_date
        )
    ).scalar() or 0

    # Operational Expenses
    operational_expenses = db.session.query(func.sum(Expense.amount)).filter(
        and_(
            Expense.expense_date >= start_date,
            Expense.expense_date <= end_date
        )
    ).scalar() or 0

    # Total Expenses
    total_expenses = loans_disbursed + welfare_payments + operational_expenses

    # Net Position
    net_position = total_income - total_expenses

    # Active Loans
    active_loans_count = Loan.query.filter_by(status='Active').count()
    active_loans_balance = db.session.query(func.sum(Loan.balance)).filter(
        Loan.status == 'Active'
    ).scalar() or 0

    # Pending Welfare Requests
    pending_welfare_count = WelfareRequest.query.filter_by(status='Pending').count()
    pending_welfare_amount = db.session.query(func.sum(WelfareRequest.amount_approved)).filter(
        and_(
            WelfareRequest.status == 'Approved',
            WelfareRequest.id.notin_(
                db.session.query(WelfarePayment.welfare_request_id)
            )
        )
    ).scalar() or 0

    return render_template('reports/financial_summary.html',
                         start_date=start_date,
                         end_date=end_date,
                         membership_fees_total=membership_fees_total,
                         contributions_total=contributions_total,
                         loan_repayments_total=loan_repayments_total,
                         total_income=total_income,
                         loans_disbursed=loans_disbursed,
                         welfare_payments=welfare_payments,
                         operational_expenses=operational_expenses,
                         total_expenses=total_expenses,
                         net_position=net_position,
                         active_loans_count=active_loans_count,
                         active_loans_balance=active_loans_balance,
                         pending_welfare_count=pending_welfare_count,
                         pending_welfare_amount=pending_welfare_amount)


@reports.route('/member-statement/<int:member_id>')
@login_required
def member_statement(member_id):
    """Individual member statement"""
    member = Member.query.get_or_404(member_id)

    # Check permission - executives can view all, members only their own
    if not (current_user.is_executive() or current_user.is_super_admin()):
        if not hasattr(current_user, 'member') or current_user.member.id != member_id:
            flash('You do not have permission to view this statement!', 'danger')
            return redirect(url_for('main.dashboard'))

    # Get date filters
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')

    if not start_date_str:
        start_date = date(date.today().year, 1, 1)
    else:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()

    if not end_date_str:
        end_date = date.today()
    else:
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

    # Membership Fee (from Receipt table)
    membership_fee = Receipt.query.filter_by(
        member_id=member_id,
        receipt_type='MembershipFee'
    ).first()

    # Contributions
    contributions = Contribution.query.filter(
        and_(
            Contribution.member_id == member_id,
            Contribution.payment_date >= start_date,
            Contribution.payment_date <= end_date
        )
    ).order_by(Contribution.payment_date.desc()).all()

    contributions_total = sum(c.amount for c in contributions)

    # Loans
    loans = Loan.query.filter_by(member_id=member_id).all()
    loans_total_borrowed = sum(l.amount_approved for l in loans if l.amount_approved)
    loans_total_repaid = sum(l.total_paid for l in loans)
    loans_balance = sum(l.balance for l in loans if l.status == 'Active')

    # Welfare
    welfare_requests = WelfareRequest.query.filter_by(member_id=member_id).all()
    welfare_total = sum(w.amount_approved or 0 for w in welfare_requests if w.status == 'Approved')

    return render_template('reports/member_statement.html',
                         member=member,
                         start_date=start_date,
                         end_date=end_date,
                         membership_fee=membership_fee,
                         contributions=contributions,
                         contributions_total=contributions_total,
                         loans=loans,
                         loans_total_borrowed=loans_total_borrowed,
                         loans_total_repaid=loans_total_repaid,
                         loans_balance=loans_balance,
                         welfare_requests=welfare_requests,
                         welfare_total=welfare_total)


@reports.route('/contributions')
@login_required
def contributions_report():
    """Contributions report - Auditors have read-only access"""
    if not (current_user.is_executive() or current_user.is_super_admin() or current_user.is_auditor()):
        abort(403)
    # Get filters
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)

    if not year:
        year = date.today().year

    # Build query - contribution_month is VARCHAR in format 'YYYY-MM'
    query = Contribution.query

    if month:
        # Format: '2025-01', '2025-02', etc.
        target_month = f"{year}-{month:02d}"
        query = query.filter(Contribution.contribution_month == target_month)
    else:
        # Filter by year prefix: '2025-%'
        query = query.filter(Contribution.contribution_month.like(f"{year}-%"))

    contributions = query.order_by(Contribution.payment_date.desc()).all()

    # Summary statistics
    total_expected = len(Member.query.filter_by(status='Active').all()) * current_app.config['MONTHLY_CONTRIBUTION']
    if month:
        total_expected = total_expected  # For selected month
    else:
        total_expected = total_expected * 12  # For entire year

    total_received = sum(c.amount for c in contributions)
    total_outstanding = total_expected - total_received
    collection_rate = (total_received / total_expected * 100) if total_expected > 0 else 0

    # Group by member
    member_contributions = {}
    for contrib in contributions:
        if contrib.member_id not in member_contributions:
            member_contributions[contrib.member_id] = {
                'member': contrib.member,
                'contributions': [],
                'total': 0
            }
        member_contributions[contrib.member_id]['contributions'].append(contrib)
        member_contributions[contrib.member_id]['total'] += contrib.amount

    return render_template('reports/contributions.html',
                         year=year,
                         month=month,
                         contributions=contributions,
                         member_contributions=member_contributions,
                         total_expected=total_expected,
                         total_received=total_received,
                         total_outstanding=total_outstanding,
                         collection_rate=collection_rate)


@reports.route('/loans')
@login_required
def loans_report():
    """Loans report - Auditors have read-only access"""
    if not (current_user.is_executive() or current_user.is_super_admin() or current_user.is_auditor()):
        abort(403)
    status_filter = request.args.get('status', '')

    query = Loan.query

    if status_filter:
        query = query.filter(Loan.status == status_filter)

    loans = query.order_by(Loan.created_at.desc()).all()

    # Summary statistics
    total_disbursed = sum(l.amount_approved for l in loans if l.disbursed and l.amount_approved)
    total_repaid = sum(l.total_paid for l in loans)
    total_outstanding = sum(l.balance for l in loans if l.status == 'Active')
    total_interest_earned = sum(l.total_paid - (l.amount_approved or 0) for l in loans if l.total_paid > (l.amount_approved or 0))

    active_loans = [l for l in loans if l.status == 'Active']
    defaulted_loans = [l for l in loans if l.status == 'Defaulted']

    return render_template('reports/loans.html',
                         loans=loans,
                         status_filter=status_filter,
                         total_disbursed=total_disbursed,
                         total_repaid=total_repaid,
                         total_outstanding=total_outstanding,
                         total_interest_earned=total_interest_earned,
                         active_loans_count=len(active_loans),
                         defaulted_loans_count=len(defaulted_loans))


@reports.route('/welfare')
@login_required
def welfare_report():
    """Welfare report - Auditors have read-only access"""
    if not (current_user.is_executive() or current_user.is_super_admin() or current_user.is_auditor()):
        abort(403)
    year = request.args.get('year', type=int)

    if not year:
        year = date.today().year

    # Get welfare requests for the year
    requests = WelfareRequest.query.filter(
        extract('year', WelfareRequest.created_at) == year
    ).order_by(WelfareRequest.created_at.desc()).all()

    # Summary statistics
    total_requests = len(requests)
    approved_requests = [r for r in requests if r.status == 'Approved']
    pending_requests = [r for r in requests if r.status == 'Pending']
    rejected_requests = [r for r in requests if r.status == 'Rejected']

    total_approved_amount = sum(r.amount_approved or 0 for r in approved_requests)

    # Get payments
    payments = WelfarePayment.query.filter(
        extract('year', WelfarePayment.payment_date) == year
    ).all()
    total_paid = sum(p.amount_paid for p in payments)

    return render_template('reports/welfare.html',
                         year=year,
                         requests=requests,
                         total_requests=total_requests,
                         approved_count=len(approved_requests),
                         pending_count=len(pending_requests),
                         rejected_count=len(rejected_requests),
                         total_approved_amount=total_approved_amount,
                         total_paid=total_paid)


@reports.route('/meetings')
@login_required
def meetings_report():
    """Meetings report - accessible to Executives and Members"""
    year = request.args.get('year', type=int)

    if not year:
        year = date.today().year

    meetings = Meeting.query.filter(
        extract('year', Meeting.meeting_date) == year
    ).order_by(Meeting.meeting_date.desc()).all()

    # Summary statistics
    total_meetings = len(meetings)
    completed_meetings = [m for m in meetings if m.status == 'Completed']
    scheduled_meetings = [m for m in meetings if m.status == 'Scheduled']
    cancelled_meetings = [m for m in meetings if m.status == 'Cancelled']

    meetings_with_quorum = [m for m in meetings if m.quorum_met == True]
    meetings_without_quorum = [m for m in meetings if m.quorum_met == False]

    # Calculate average attendance
    total_attendance = sum(m.total_attendance or 0 for m in meetings if m.total_attendance)
    avg_attendance = total_attendance / len(meetings) if meetings else 0

    return render_template('reports/meetings.html',
                         year=year,
                         meetings=meetings,
                         total_meetings=total_meetings,
                         completed_count=len(completed_meetings),
                         scheduled_count=len(scheduled_meetings),
                         cancelled_count=len(cancelled_meetings),
                         quorum_met_count=len(meetings_with_quorum),
                         quorum_not_met_count=len(meetings_without_quorum),
                         avg_attendance=avg_attendance)
