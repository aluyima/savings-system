"""
Flask CLI Commands
Custom management commands for the application
"""
import click
from flask import current_app
from app import db
from app.utils.loan_reminders import check_and_send_due_date_reminders, get_overdue_loans, get_upcoming_due_loans
from datetime import date


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
