"""
Loan Due Date Reminder System
Sends notifications to executives and borrowers one day before loan due date
"""
from datetime import date, timedelta
from app import db
from app.models.loan import Loan
from app.models.user import User
from app.models.member import Member
from app.utils.notifications import NotificationService
from flask import current_app


def check_and_send_due_date_reminders():
    """
    Check for loans due tomorrow and send reminders
    Should be run daily (via cron job or task scheduler)

    Returns:
        dict: Summary of notifications sent
    """
    tomorrow = date.today() + timedelta(days=1)

    # Find all active loans due tomorrow
    loans_due_tomorrow = Loan.query.filter(
        Loan.status.in_(['Active', 'Disbursed']),
        Loan.due_date == tomorrow,
        Loan.balance > 0
    ).all()

    if not loans_due_tomorrow:
        return {
            'success': True,
            'loans_checked': 0,
            'notifications_sent': 0,
            'message': 'No loans due tomorrow'
        }

    notifications_sent = 0
    errors = []

    for loan in loans_due_tomorrow:
        try:
            # Send notification to borrower
            borrower_sent = send_borrower_reminder(loan)
            if borrower_sent:
                notifications_sent += 1

            # Send notification to executives
            exec_sent = send_executive_reminder(loan)
            notifications_sent += exec_sent

        except Exception as e:
            errors.append(f"Loan {loan.loan_number}: {str(e)}")

    return {
        'success': len(errors) == 0,
        'loans_checked': len(loans_due_tomorrow),
        'notifications_sent': notifications_sent,
        'errors': errors if errors else None
    }


def send_borrower_reminder(loan):
    """
    Send due date reminder to the borrower

    Args:
        loan: Loan object

    Returns:
        bool: True if sent successfully
    """
    member = loan.member

    if not member:
        return False

    # Email subject and body
    subject = f"Loan Payment Reminder - {loan.loan_number}"

    body = f"""Dear {member.full_name},

This is a friendly reminder that your loan payment is due tomorrow.

Loan Details:
- Loan Number: {loan.loan_number}
- Amount Borrowed: UGX {loan.amount_approved:,.0f}
- Total Payable: UGX {loan.total_payable:,.0f}
- Amount Paid: UGX {loan.total_paid:,.0f}
- Balance Remaining: UGX {loan.balance:,.0f}
- Due Date: {loan.due_date.strftime('%d/%m/%Y')}

Please ensure you make your payment by the due date to avoid late payment penalties.

If you have any questions or need to discuss payment arrangements, please contact the executive committee.

Thank you for your cooperation.

Best regards,
Old Timers Savings Club Kiteezi
"""

    # Send email
    email_sent = False
    if member.email:
        try:
            NotificationService.send_email(
                recipient_email=member.email,
                subject=subject,
                body=body
            )
            email_sent = True
        except Exception as e:
            print(f"Error sending email to {member.email}: {str(e)}")

    # Send SMS
    sms_sent = False
    if member.phone_primary and current_app.config.get('SMS_ENABLED'):
        sms_message = f"OTSC Reminder: Your loan {loan.loan_number} payment of UGX {loan.balance:,.0f} is due tomorrow ({loan.due_date.strftime('%d/%m/%Y')}). Please make your payment to avoid penalties."
        try:
            NotificationService.send_sms(
                phone_number=member.phone_primary,
                message=sms_message
            )
            sms_sent = True
        except Exception as e:
            print(f"Error sending SMS to {member.phone_primary}: {str(e)}")

    # Send WhatsApp
    whatsapp_sent = False
    if member.phone_primary and current_app.config.get('WHATSAPP_ENABLED'):
        whatsapp_message = f"""*Loan Payment Reminder*

Dear {member.full_name},

Your loan payment is due tomorrow:

*Loan Number:* {loan.loan_number}
*Balance:* UGX {loan.balance:,.0f}
*Due Date:* {loan.due_date.strftime('%d/%m/%Y')}

Please make your payment to avoid late fees.

_Old Timers Savings Club Kiteezi_"""
        try:
            NotificationService.send_whatsapp(
                phone_number=member.phone_primary,
                message=whatsapp_message
            )
            whatsapp_sent = True
        except Exception as e:
            print(f"Error sending WhatsApp to {member.phone_primary}: {str(e)}")

    return email_sent or sms_sent or whatsapp_sent


def send_executive_reminder(loan):
    """
    Send due date reminder to all executive members

    Args:
        loan: Loan object

    Returns:
        int: Number of executives notified
    """
    # Get all executive users
    executives = User.query.filter(
        User.role.in_(['Executive', 'SuperAdmin'])
    ).all()

    if not executives:
        return 0

    member = loan.member

    # Email subject and body
    subject = f"Loan Due Tomorrow - {loan.loan_number}"

    body = f"""Dear Executive Committee Member,

This is a reminder that the following loan is due for payment tomorrow:

Borrower: {member.full_name} ({member.member_number})
Loan Number: {loan.loan_number}
Amount Borrowed: UGX {loan.amount_approved:,.0f}
Total Payable: UGX {loan.total_payable:,.0f}
Amount Paid: UGX {loan.total_paid:,.0f}
Balance Remaining: UGX {loan.balance:,.0f}
Due Date: {loan.due_date.strftime('%d/%m/%Y')}

The borrower has been notified. Please follow up as necessary.

You can view the loan details here:
{current_app.config.get('BASE_URL')}/loans/{loan.id}

Best regards,
Old Timers Savings Club Kiteezi System
"""

    notifications_sent = 0

    for executive in executives:
        # Send email to executive
        if executive.email:
            try:
                NotificationService.send_email(
                    recipient_email=executive.email,
                    subject=subject,
                    body=body
                )
                notifications_sent += 1
            except Exception as e:
                print(f"Error sending email to executive {executive.email}: {str(e)}")

        # Send SMS to executive if they have a linked member profile
        if hasattr(executive, 'member') and executive.member and executive.member.phone_primary:
            if current_app.config.get('SMS_ENABLED'):
                sms_message = f"OTSC Alert: Loan {loan.loan_number} for {member.full_name} is due tomorrow. Balance: UGX {loan.balance:,.0f}. Follow up required."
                try:
                    NotificationService.send_sms(
                        phone_number=executive.member.phone_primary,
                        message=sms_message
                    )
                    notifications_sent += 1
                except Exception as e:
                    print(f"Error sending SMS to executive: {str(e)}")

    return notifications_sent


def get_overdue_loans():
    """
    Get all loans that are overdue (past due date with outstanding balance)

    Returns:
        list: List of overdue Loan objects
    """
    today = date.today()

    overdue_loans = Loan.query.filter(
        Loan.status.in_(['Active', 'Disbursed']),
        Loan.due_date < today,
        Loan.balance > 0
    ).order_by(Loan.due_date).all()

    return overdue_loans


def apply_overdue_extensions(grace_days=None):
    """Automatically extend loans that are more than `grace_days` past their due date.

    For each unpaid loan whose due date has been passed by more than the grace
    period, the repayment period is extended by one month (adding one month's
    interest on the principal) and the due date is pushed out a month. The
    extension repeats until the loan's due date is back within the grace window,
    so a single run also catches up loans that have been overdue for several
    months. Designed to be run once per day.

    Returns:
        dict: Summary of extensions applied
    """
    from app.models.system import SystemSetting

    if grace_days is None:
        grace_days = SystemSetting.get_setting(
            'LOAN_EXTENSION_GRACE_DAYS',
            current_app.config.get('LOAN_EXTENSION_GRACE_DAYS', 10)
        )
    grace_days = int(grace_days)
    today = date.today()

    overdue_loans = Loan.query.filter(
        Loan.status.in_(['Active', 'Disbursed']),
        Loan.balance > 0,
        Loan.due_date.isnot(None),
        Loan.due_date < today,
        # Frozen loans no longer accrue interest; skip them entirely.
        # isnot(True) also keeps legacy rows where the flag is NULL.
        Loan.interest_frozen.isnot(True)
    ).all()

    extended = []
    for loan in overdue_loans:
        months_added = 0
        interest_added = 0.0
        # Apply as many monthly extensions as needed to bring the due date back
        # within the grace window.
        while loan.due_date and (today - loan.due_date).days > grace_days and float(loan.balance or 0) > 0:
            interest_added += loan.extend_one_month()
            months_added += 1

        if months_added:
            note = (f"[{today.strftime('%d/%m/%Y')}] Auto-extended {months_added} month(s) for being "
                    f"more than {grace_days} days overdue; added interest UGX {interest_added:,.0f}; "
                    f"new due date {loan.due_date.strftime('%d/%m/%Y')}.")
            loan.recovery_notes = (loan.recovery_notes + "\n" + note) if loan.recovery_notes else note
            extended.append((loan, months_added, interest_added))

    if extended:
        db.session.commit()
        for loan, months_added, interest_added in extended:
            try:
                _notify_extension(loan, months_added, interest_added)
            except Exception as e:
                print(f"Extension notice failed for {loan.loan_number}: {str(e)}")

    return {
        'success': True,
        'loans_checked': len(overdue_loans),
        'loans_extended': len(extended),
        'details': [(loan.loan_number, m, i) for loan, m, i in extended]
    }


def _notify_extension(loan, months_added, interest_added):
    """Notify the borrower and executives that a loan was auto-extended."""
    from app.models.notification import Notification

    title = f"Loan {loan.loan_number} extended ({months_added} month(s))"
    message = (f"Because it was overdue, loan {loan.loan_number} has been automatically extended by "
               f"{months_added} month(s). Additional interest of UGX {interest_added:,.0f} has been "
               f"applied. New balance: UGX {float(loan.balance or 0):,.0f}, due {loan.due_date.strftime('%d/%m/%Y')}.")
    link = f"/loans/{loan.id}"

    # In-app notification to the borrower (if they have a user account)
    if loan.member and getattr(loan.member, 'user', None):
        Notification.create_notification(
            user_id=loan.member.user.id, title=title, message=message,
            notification_type='Warning', category='Loan', link_url=link, priority='High'
        )

    # In-app notification to executives / admins
    exec_user_ids = [u.id for u in User.query.filter(User.role.in_(['Executive', 'SuperAdmin'])).all()]
    if exec_user_ids:
        Notification.create_bulk_notification(
            user_ids=exec_user_ids, title=title, message=message,
            notification_type='Warning', category='Loan', link_url=link, priority='High'
        )


def get_upcoming_due_loans(days=7):
    """
    Get loans due within the next specified number of days

    Args:
        days (int): Number of days to look ahead (default: 7)

    Returns:
        list: List of Loan objects
    """
    today = date.today()
    future_date = today + timedelta(days=days)

    upcoming_loans = Loan.query.filter(
        Loan.status.in_(['Active', 'Disbursed']),
        Loan.due_date >= today,
        Loan.due_date <= future_date,
        Loan.balance > 0
    ).order_by(Loan.due_date).all()

    return upcoming_loans
