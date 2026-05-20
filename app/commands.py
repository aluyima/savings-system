"""
Flask CLI Commands
Custom management commands for the application
"""
import click
from flask import current_app
from app import db
from app.utils.loan_reminders import check_and_send_due_date_reminders, get_overdue_loans, get_upcoming_due_loans
from datetime import date
import getpass


def register_commands(app):
    """Register CLI commands with the Flask app"""

    @app.cli.command('send-loan-reminders')
    def send_loan_reminders_command():
        """Send loan due date reminders for loans due tomorrow"""
        click.echo('=' * 60)
        click.echo('Loan Due Date Reminder System')
        click.echo('=' * 60)
        click.echo(f'Date: {date.today().strftime("%d/%m/%Y")}')
        click.echo('')

        with app.app_context():
            click.echo('Checking for loans due tomorrow...')
            result = check_and_send_due_date_reminders()

            click.echo('')
            click.echo(f"Loans checked: {result['loans_checked']}")
            click.echo(f"Notifications sent: {result['notifications_sent']}")

            if result.get('errors'):
                click.echo('')
                click.echo('Errors encountered:')
                for error in result['errors']:
                    click.echo(f'  - {error}', err=True)

            if result['success']:
                click.echo('')
                click.secho('✓ Reminders sent successfully!', fg='green')
            else:
                click.echo('')
                click.secho('✗ Some errors occurred', fg='red')

        click.echo('=' * 60)

    @app.cli.command('check-overdue-loans')
    def check_overdue_loans_command():
        """Check for overdue loans"""
        click.echo('=' * 60)
        click.echo('Overdue Loans Report')
        click.echo('=' * 60)
        click.echo(f'Date: {date.today().strftime("%d/%m/%Y")}')
        click.echo('')

        with app.app_context():
            overdue_loans = get_overdue_loans()

            if not overdue_loans:
                click.secho('No overdue loans found.', fg='green')
            else:
                click.secho(f'Found {len(overdue_loans)} overdue loan(s):', fg='yellow')
                click.echo('')

                for loan in overdue_loans:
                    days_overdue = (date.today() - loan.due_date).days
                    click.echo(f'  Loan: {loan.loan_number}')
                    click.echo(f'  Borrower: {loan.member.full_name} ({loan.member.member_number})')
                    click.echo(f'  Due Date: {loan.due_date.strftime("%d/%m/%Y")}')
                    click.echo(f'  Days Overdue: {days_overdue}')
                    click.echo(f'  Balance: UGX {loan.balance:,.0f}')
                    click.echo('')

        click.echo('=' * 60)

    @app.cli.command('check-upcoming-loans')
    @click.option('--days', default=7, help='Number of days to look ahead')
    def check_upcoming_loans_command(days):
        """Check for loans due in the next N days"""
        click.echo('=' * 60)
        click.echo(f'Loans Due in Next {days} Days')
        click.echo('=' * 60)
        click.echo(f'Date: {date.today().strftime("%d/%m/%Y")}')
        click.echo('')

        with app.app_context():
            upcoming_loans = get_upcoming_due_loans(days=days)

            if not upcoming_loans:
                click.echo(f'No loans due in the next {days} days.')
            else:
                click.echo(f'Found {len(upcoming_loans)} loan(s) due:')
                click.echo('')

                for loan in upcoming_loans:
                    days_until_due = (loan.due_date - date.today()).days
                    click.echo(f'  Loan: {loan.loan_number}')
                    click.echo(f'  Borrower: {loan.member.full_name} ({loan.member.member_number})')
                    click.echo(f'  Due Date: {loan.due_date.strftime("%d/%m/%Y")} ({days_until_due} days)')
                    click.echo(f'  Balance: UGX {loan.balance:,.0f}')
                    click.echo('')

        click.echo('=' * 60)

    @app.cli.command('create-superadmin')
    @click.option('--username', prompt='Username', help='Admin username')
    @click.option('--phone', prompt='Phone number', help='Admin phone number')
    @click.option('--email', prompt='Email', default='admin@oldtimerssavings.org', help='Admin email')
    @click.option('--name', prompt='Full name', default='System Administrator', help='Admin full name')
    def create_superadmin_command(username, phone, email, name):
        """Create a super admin user"""
        click.echo('=' * 60)
        click.echo('Create Super Admin User')
        click.echo('=' * 60)
        click.echo('')

        with app.app_context():
            from app.models.user import User
            from app.models.member import Member

            # Check if user already exists
            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                click.secho(f'Error: User with username "{username}" already exists!', fg='red')
                return

            # Check if phone is already used
            existing_member = Member.query.filter_by(phone_primary=phone).first()
            if existing_member:
                click.secho(f'Error: A member with phone number "{phone}" already exists!', fg='red')
                return

            # Get password (with confirmation)
            password = click.prompt('Password', hide_input=True, confirmation_prompt=True)

            if len(password) < 8:
                click.secho('Error: Password must be at least 8 characters long!', fg='red')
                return

            try:
                # Create member first
                admin_member = Member(
                    full_name=name,
                    phone_primary=phone,
                    email=email,
                    date_joined=date.today(),
                    status='Active',
                    membership_fee_paid=True
                )

                db.session.add(admin_member)
                db.session.flush()  # Get the member ID

                # Create user linked to member
                admin_user = User(
                    member_id=admin_member.id,
                    username=username,
                    role='SuperAdmin',
                    must_change_password=False  # Don't force password change for manually created admin
                )
                admin_user.set_password(password)

                db.session.add(admin_user)
                db.session.commit()

                click.echo('')
                click.secho('✓ Super admin created successfully!', fg='green')
                click.echo('')
                click.echo(f'  Username: {admin_user.username}')
                click.echo(f'  Member: {admin_member.full_name} ({admin_member.member_number})')
                click.echo(f'  Phone: {admin_member.phone_primary}')
                click.echo(f'  Email: {admin_member.email}')
                click.echo(f'  Role: {admin_user.role}')
                click.echo('')
                click.secho('You can now log in with these credentials.', fg='green')

            except Exception as e:
                db.session.rollback()
                click.echo('')
                click.secho(f'✗ Error creating super admin: {str(e)}', fg='red')

        click.echo('=' * 60)

    @app.cli.command('clear-database')
    @click.option('--keep-admin', is_flag=True, default=True, help='Keep the super admin account (default: True)')
    @click.confirmation_option(prompt='Are you sure you want to delete all data? This cannot be undone!')
    def clear_database_command(keep_admin):
        """Clear all database data except super admin account"""
        click.echo('=' * 60)
        click.echo('Clear Database Data')
        click.echo('=' * 60)
        click.echo('')

        with app.app_context():
            from app.models.user import User
            from app.models.member import Member, NextOfKin
            from app.models.contribution import Contribution, Receipt
            from app.models.loan import Loan, LoanRepayment
            from app.models.welfare import WelfareRequest, WelfarePayment
            from app.models.meeting import Meeting, Attendance, Minutes, ActionItem
            from app.models.expense import Expense
            from app.models.notification import Notification
            from app.models.audit import AuditLog
            from app.models.system import SystemSetting

            try:
                # Get super admin before deletion
                super_admin_user = None
                super_admin_member_id = None

                if keep_admin:
                    super_admin_user = User.query.filter_by(role='SuperAdmin').first()
                    if super_admin_user:
                        super_admin_member_id = super_admin_user.member_id
                        click.echo(f'Keeping super admin: {super_admin_user.username}')
                    else:
                        click.secho('Warning: No super admin found!', fg='yellow')

                click.echo('')
                click.echo('Deleting data...')

                # Delete in order to respect foreign key constraints
                deleted_counts = {}

                # 1. Delete audit logs
                count = AuditLog.query.delete()
                deleted_counts['Audit Logs'] = count
                click.echo(f'  - Deleted {count} audit logs')

                # 2. Delete notifications
                count = Notification.query.delete()
                deleted_counts['Notifications'] = count
                click.echo(f'  - Deleted {count} notifications')

                # 3. Delete action items
                count = ActionItem.query.delete()
                deleted_counts['Action Items'] = count
                click.echo(f'  - Deleted {count} action items')

                # 4. Delete meeting minutes
                count = Minutes.query.delete()
                deleted_counts['Minutes'] = count
                click.echo(f'  - Deleted {count} meeting minutes')

                # 5. Delete meeting attendance
                count = Attendance.query.delete()
                deleted_counts['Meeting Attendance'] = count
                click.echo(f'  - Deleted {count} meeting attendance records')

                # 6. Delete meetings
                count = Meeting.query.delete()
                deleted_counts['Meetings'] = count
                click.echo(f'  - Deleted {count} meetings')

                # 7. Delete expenses
                count = Expense.query.delete()
                deleted_counts['Expenses'] = count
                click.echo(f'  - Deleted {count} expenses')

                # 8. Delete loan repayments
                count = LoanRepayment.query.delete()
                deleted_counts['Loan Repayments'] = count
                click.echo(f'  - Deleted {count} loan repayments')

                # 9. Delete loans
                count = Loan.query.delete()
                deleted_counts['Loans'] = count
                click.echo(f'  - Deleted {count} loans')

                # 10. Delete welfare payments
                count = WelfarePayment.query.delete()
                deleted_counts['Welfare Payments'] = count
                click.echo(f'  - Deleted {count} welfare payments')

                # 11. Delete welfare requests
                count = WelfareRequest.query.delete()
                deleted_counts['Welfare Requests'] = count
                click.echo(f'  - Deleted {count} welfare requests')

                # 12. Delete receipts
                count = Receipt.query.delete()
                deleted_counts['Receipts'] = count
                click.echo(f'  - Deleted {count} receipts')

                # 13. Delete contributions
                count = Contribution.query.delete()
                deleted_counts['Contributions'] = count
                click.echo(f'  - Deleted {count} contributions')

                # 14. Delete users (except super admin)
                if keep_admin and super_admin_user:
                    count = User.query.filter(User.id != super_admin_user.id).delete()
                else:
                    count = User.query.delete()
                deleted_counts['Users'] = count
                click.echo(f'  - Deleted {count} users')

                # 15. Delete members (except super admin's member)
                if keep_admin and super_admin_member_id:
                    # First, delete next of kin for non-admin members
                    count = NextOfKin.query.filter(NextOfKin.member_id != super_admin_member_id).delete()
                    deleted_counts['Next of Kin'] = count
                    click.echo(f'  - Deleted {count} next of kin records')

                    # Then delete members except admin
                    count = Member.query.filter(Member.id != super_admin_member_id).delete()

                    # Reset the admin member's data
                    admin_member = Member.query.get(super_admin_member_id)
                    if admin_member:
                        admin_member.total_contributed = 0.00
                        admin_member.consecutive_months_paid = 0
                        admin_member.last_contribution_date = None
                        admin_member.qualified_for_benefits = False
                        admin_member.membership_fee_paid = True  # Keep membership fee as paid
                        click.echo(f'  - Reset admin member stats: {admin_member.full_name}')
                else:
                    count_kin = NextOfKin.query.delete()
                    deleted_counts['Next of Kin'] = count_kin
                    click.echo(f'  - Deleted {count_kin} next of kin records')

                    count = Member.query.delete()

                deleted_counts['Members'] = count
                click.echo(f'  - Deleted {count} members')

                # Commit all deletions
                db.session.commit()

                click.echo('')
                click.secho('✓ Database cleared successfully!', fg='green')
                click.echo('')
                click.echo('Summary:')
                for entity, count in deleted_counts.items():
                    click.echo(f'  {entity}: {count}')

                if keep_admin and super_admin_user:
                    click.echo('')
                    click.secho(f'Super admin account preserved: {super_admin_user.username}', fg='green')

            except Exception as e:
                db.session.rollback()
                click.echo('')
                click.secho(f'✗ Error clearing database: {str(e)}', fg='red')
                import traceback
                click.echo(traceback.format_exc())

        click.echo('=' * 60)
