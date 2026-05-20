"""
Main Routes
Dashboard and home page routes
"""
from flask import Blueprint, render_template, redirect, url_for, request, abort
from flask_login import login_required, current_user
from app import db
from app.models.member import Member
from app.models.contribution import Contribution
from app.models.loan import Loan
from app.models.welfare import WelfareRequest
from app.models.meeting import Meeting
from app.models.notification import Notification
from app.utils.decorators import password_change_required
from sqlalchemy import func, extract
from datetime import datetime, date

main = Blueprint('main', __name__)


@main.route('/')
def index():
    """Landing page - redirect to login or dashboard"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('auth.login'))


@main.route('/dashboard')
@login_required
@password_change_required
def dashboard():
    """Main dashboard - different views based on user role"""
    if current_user.is_super_admin() or current_user.is_executive():
        return executive_dashboard()
    elif current_user.is_auditor():
        return auditor_dashboard()
    else:
        return member_dashboard()


def executive_dashboard():
    """Dashboard for Executive and Super Admin users"""
    # Summary statistics
    total_members = Member.query.filter_by(status='Active').count()
    active_members = Member.query.filter(
        Member.status == 'Active',
        Member.qualified_for_benefits == True
    ).count()

    # Current month contributions
    current_month = date.today().strftime('%Y-%m')
    month_contributions = Contribution.query.filter_by(contribution_month=current_month).count()

    # Total contributed this month
    from sqlalchemy import func
    month_total = db.session.query(func.sum(Contribution.amount)).filter_by(
        contribution_month=current_month
    ).scalar() or 0

    # Pending welfare requests
    pending_welfare = WelfareRequest.query.filter_by(status='Submitted').count()

    # Pending loan applications
    pending_loans = Loan.query.filter_by(status='Pending').count()

    # Active loans
    active_loans = Loan.query.filter(Loan.status.in_(['Disbursed', 'Repaying'])).count()

    # Upcoming meetings
    upcoming_meetings = Meeting.query.filter(
        Meeting.meeting_date >= date.today(),
        Meeting.status == 'Scheduled'
    ).order_by(Meeting.meeting_date).limit(3).all()

    # Recent contributions
    recent_contributions = Contribution.query.order_by(
        Contribution.created_at.desc()
    ).limit(5).all()

    # Unread notifications
    unread_notifications = Notification.get_unread_count(current_user.id)

    return render_template('dashboard/executive.html',
                         total_members=total_members,
                         active_members=active_members,
                         month_contributions=month_contributions,
                         month_total=month_total,
                         pending_welfare=pending_welfare,
                         pending_loans=pending_loans,
                         active_loans=active_loans,
                         upcoming_meetings=upcoming_meetings,
                         recent_contributions=recent_contributions,
                         unread_notifications=unread_notifications)


def auditor_dashboard():
    """Dashboard for Auditor users"""
    # Summary statistics (read-only view)
    total_members = Member.query.count()
    active_members = Member.query.filter_by(status='Active').count()

    # Financial summary
    from sqlalchemy import func, extract
    current_year = date.today().year

    # Total contributions this year
    year_contributions = db.session.query(func.sum(Contribution.amount)).filter(
        extract('year', Contribution.payment_date) == current_year
    ).scalar() or 0

    # Total welfare paid this year
    from app.models.welfare import WelfarePayment
    year_welfare = db.session.query(func.sum(WelfarePayment.amount_paid)).filter(
        extract('year', WelfarePayment.payment_date) == current_year
    ).scalar() or 0

    # Total loans disbursed this year
    year_loans = db.session.query(func.sum(Loan.amount_approved)).filter(
        extract('year', Loan.disbursement_date) == current_year,
        Loan.disbursed == True
    ).scalar() or 0

    # Recent audit logs
    from app.models.audit import AuditLog
    recent_logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(10).all()

    return render_template('dashboard/auditor.html',
                         total_members=total_members,
                         active_members=active_members,
                         year_contributions=year_contributions,
                         year_welfare=year_welfare,
                         year_loans=year_loans,
                         recent_logs=recent_logs)


def member_dashboard():
    """Dashboard for regular Member users"""
    member = current_user.member

    # Member's contribution summary
    total_contributed = member.total_contributed
    consecutive_months = member.consecutive_months_paid
    qualified = member.qualified_for_benefits

    # Current month status
    current_month = date.today().strftime('%Y-%m')
    month_contribution = Contribution.query.filter_by(
        member_id=member.id,
        contribution_month=current_month
    ).first()

    # Recent contributions
    recent_contributions = Contribution.query.filter_by(
        member_id=member.id
    ).order_by(Contribution.payment_date.desc()).limit(5).all()

    # All loans (including pending for tracking)
    active_loans = Loan.query.filter(
        Loan.member_id == member.id,
        Loan.status.in_(['Pending Guarantor Approval', 'Returned to Applicant', 'Pending Executive Approval', 'Approved', 'Active', 'Disbursed'])
    ).order_by(Loan.created_at.desc()).all()

    # Loans where member is a guarantor and approval is pending
    guarantor_requests = Loan.query.filter(
        db.or_(
            db.and_(Loan.guarantor1_id == member.id, Loan.guarantor1_approved == None),
            db.and_(Loan.guarantor2_id == member.id, Loan.guarantor2_approved == None)
        ),
        Loan.status.in_(['Pending Guarantor Approval', 'Returned to Applicant'])
    ).order_by(Loan.created_at.desc()).all()

    # All welfare requests (including pending for tracking)
    welfare_requests = WelfareRequest.query.filter_by(
        member_id=member.id
    ).order_by(WelfareRequest.submitted_date.desc()).limit(5).all()

    # Upcoming meetings
    upcoming_meetings = Meeting.query.filter(
        Meeting.meeting_date >= date.today(),
        Meeting.status == 'Scheduled'
    ).order_by(Meeting.meeting_date).limit(2).all()

    # Unread notifications
    unread_notifications = Notification.get_unread_count(current_user.id)

    return render_template('dashboard/member.html',
                         member=member,
                         total_contributed=total_contributed,
                         consecutive_months=consecutive_months,
                         qualified=qualified,
                         month_contribution=month_contribution,
                         current_month=current_month,
                         recent_contributions=recent_contributions,
                         active_loans=active_loans,
                         guarantor_requests=guarantor_requests,
                         welfare_requests=welfare_requests,
                         upcoming_meetings=upcoming_meetings,
                         unread_notifications=unread_notifications)


@main.route('/notifications')
@login_required
@password_change_required
def notifications():
    """View all notifications"""
    page = request.args.get('page', 1, type=int)
    per_page = 20

    notifications = Notification.query.filter_by(
        user_id=current_user.id
    ).order_by(Notification.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return render_template('notifications/list.html', notifications=notifications)


@main.route('/notifications/<int:id>/read', methods=['POST'])
@login_required
def mark_notification_read(id):
    """Mark notification as read"""
    notification = Notification.query.get_or_404(id)

    # Ensure user owns this notification
    if notification.user_id != current_user.id:
        abort(403)

    notification.mark_as_read()
    flash('Notification marked as read.', 'success')

    return redirect(url_for('main.notifications'))
