"""
Old Timers Savings Group - Digital Records Management System
Application Entry Point
"""
from app import create_app, db
import os
import click

app = create_app(os.getenv('FLASK_ENV', 'development'))


@app.shell_context_processor
def make_shell_context():
    """Make database and models available in flask shell"""
    from app.models import User, Member
    return {
        'db': db,
        'User': User,
        'Member': Member
    }


@app.cli.command('init-db')
def init_db_command():
    """Initialize the database tables"""
    with app.app_context():
        db.create_all()

        # Initialize default system settings
        from app.models.system import SystemSetting
        SystemSetting.initialize_defaults()

        click.echo('✓ Database initialized successfully!')
        click.echo('✓ System settings initialized')


@app.cli.command('create-admin')
def create_admin_command():
    """Create super admin user (interactive)"""
    from werkzeug.security import generate_password_hash
    from app.models.member import Member
    from app.models.user import User
    from datetime import date

    with app.app_context():
        # Check if admin already exists
        admin_user = User.query.filter_by(role='SuperAdmin').first()
        if admin_user:
            click.echo('⚠️  Super Admin already exists!')
            click.echo(f'Username: {admin_user.username}')
            return

        click.echo('\n' + '='*50)
        click.echo('Creating Super Admin Account')
        click.echo('='*50)

        # Get admin details
        full_name = click.prompt('Full Name', default='System Administrator')
        phone = click.prompt('Phone Number (e.g., 0700000000)', default='0700000000')
        email = click.prompt('Email Address (optional)', default='', show_default=False)

        # Validate password
        while True:
            password = click.prompt('Initial Password (min 8 characters)', hide_input=True)
            if len(password) >= 8:
                password_confirm = click.prompt('Confirm Password', hide_input=True)
                if password == password_confirm:
                    break
                else:
                    click.echo('❌ Passwords do not match. Try again.')
            else:
                click.echo('❌ Password must be at least 8 characters.')

        # Create admin member first
        admin_member = Member(
            member_number='OT-001',
            full_name=full_name,
            phone_primary=phone,
            email=email if email else None,
            date_joined=date.today(),
            status='Active',
            membership_fee_paid=True,
            total_contributed=0.00,
            created_by=1  # Self-created
        )
        db.session.add(admin_member)
        db.session.flush()  # Get the member ID

        # Create admin user
        admin_user = User(
            member_id=admin_member.id,
            username=phone,
            role='SuperAdmin',
            is_active=True,
            must_change_password=True
        )
        admin_user.set_password(password)

        db.session.add(admin_user)
        db.session.commit()

        click.echo('\n' + '='*50)
        click.echo('✓ Super Admin created successfully!')
        click.echo('='*50)
        click.echo(f'Username: {phone}')
        click.echo(f'Member Number: OT-001')
        click.echo('\n⚠️  You will be required to change your password on first login.')
        click.echo('\nTo start the application, run: flask run')
        click.echo('Then visit: http://127.0.0.1:5000')
        click.echo('='*50 + '\n')


if __name__ == '__main__':
    app.run(debug=True)
