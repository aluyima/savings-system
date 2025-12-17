"""
Authentication Routes
Handles login, logout, and password management
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user, login_required
from app import db
from app.models.user import User
from app.models.audit import AuditLog
from datetime import datetime, timedelta

auth = Blueprint('auth', __name__)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember', False)

        user = User.query.filter_by(username=username).first()

        # Check if account is locked
        if user and user.account_locked_until:
            if datetime.utcnow() < user.account_locked_until:
                remaining = (user.account_locked_until - datetime.utcnow()).seconds // 60
                flash(f'Account is locked due to multiple failed login attempts. Try again in {remaining} minutes.', 'danger')
                return redirect(url_for('auth.login'))
            else:
                # Unlock account
                user.account_locked_until = None
                user.failed_login_attempts = 0
                db.session.commit()

        # Verify credentials
        if user and user.check_password(password):
            if not user.is_active:
                flash('Your account has been deactivated. Please contact the administrator.', 'danger')
                return redirect(url_for('auth.login'))

            # Successful login
            login_user(user, remember=remember)
            user.last_login = datetime.utcnow()
            user.failed_login_attempts = 0
            db.session.commit()

            # Log successful login
            AuditLog.log_action(
                user_id=user.id,
                action_type='Login',
                description='User logged in successfully',
                ip_address=request.remote_addr,
                user_agent=request.user_agent.string
            )

            # Redirect to next page or dashboard
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('main.dashboard'))
        else:
            # Failed login
            if user:
                user.failed_login_attempts += 1

                # Lock account after max attempts
                from flask import current_app
                max_attempts = current_app.config.get('MAX_LOGIN_ATTEMPTS', 5)
                lock_duration = current_app.config.get('ACCOUNT_LOCK_DURATION', 30)

                if user.failed_login_attempts >= max_attempts:
                    user.account_locked_until = datetime.utcnow() + timedelta(minutes=lock_duration)
                    flash(f'Account locked due to {max_attempts} failed login attempts. Try again in {lock_duration} minutes.', 'danger')
                else:
                    remaining = max_attempts - user.failed_login_attempts
                    flash(f'Invalid username or password. {remaining} attempts remaining.', 'danger')

                db.session.commit()

                # Log failed login attempt
                AuditLog.log_action(
                    user_id=user.id,
                    action_type='LoginFailed',
                    description='Failed login attempt',
                    ip_address=request.remote_addr,
                    user_agent=request.user_agent.string
                )
            else:
                flash('Invalid username or password.', 'danger')

            return redirect(url_for('auth.login'))

    return render_template('auth/login.html')


@auth.route('/logout')
@login_required
def logout():
    """User logout"""
    # Log logout
    AuditLog.log_action(
        user_id=current_user.id,
        action_type='Logout',
        description='User logged out',
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string
    )

    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.login'))


@auth.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Change user password"""
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        # Validate current password
        if not current_user.check_password(current_password):
            flash('Current password is incorrect.', 'danger')
            return redirect(url_for('auth.change_password'))

        # Validate new password
        if len(new_password) < 8:
            flash('New password must be at least 8 characters long.', 'danger')
            return redirect(url_for('auth.change_password'))

        if new_password != confirm_password:
            flash('New passwords do not match.', 'danger')
            return redirect(url_for('auth.change_password'))

        # Update password
        current_user.set_password(new_password)
        current_user.must_change_password = False
        db.session.commit()

        # Log password change
        AuditLog.log_action(
            user_id=current_user.id,
            action_type='PasswordChange',
            description='User changed password',
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string
        )

        flash('Password changed successfully.', 'success')
        return redirect(url_for('main.dashboard'))

    return render_template('auth/change_password.html')


@auth.route('/request-password-reset', methods=['GET', 'POST'])
def request_password_reset():
    """Request password reset (placeholder for future implementation)"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')

        user = User.query.filter_by(username=username).first()
        if user:
            # TODO: Implement password reset token generation and email/SMS
            # For now, user must contact admin
            flash('Password reset requested. Please contact the administrator for assistance.', 'info')
        else:
            # Don't reveal if user exists
            flash('If a user with that username exists, password reset instructions will be sent.', 'info')

        return redirect(url_for('auth.login'))

    return render_template('auth/request_password_reset.html')
