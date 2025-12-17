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
