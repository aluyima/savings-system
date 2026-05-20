"""
Custom Decorators
Permission and access control decorators
"""
from functools import wraps
from flask import abort, flash, redirect, url_for
from flask_login import current_user


def login_required_with_message(f):
    """
    Custom login required decorator with flash message

    Usage:
        @login_required_with_message
        def protected_view():
            pass
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


def super_admin_required(f):
    """
    Require Super Admin role

    Usage:
        @super_admin_required
        def admin_only_view():
            pass
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))

        if not current_user.is_super_admin():
            flash('You do not have permission to access this page.', 'danger')
            abort(403)

        return f(*args, **kwargs)
    return decorated_function


def executive_required(f):
    """
    Require Executive or Super Admin role

    Usage:
        @executive_required
        def executive_view():
            pass
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))

        if not (current_user.is_executive() or current_user.is_super_admin()):
            flash('You do not have permission to access this page.', 'danger')
            abort(403)

        return f(*args, **kwargs)
    return decorated_function


def auditor_required(f):
    """
    Require Auditor, Executive, or Super Admin role

    Usage:
        @auditor_required
        def auditor_view():
            pass
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))

        if not (current_user.is_auditor() or current_user.is_executive() or current_user.is_super_admin()):
            flash('You do not have permission to access this page.', 'danger')
            abort(403)

        return f(*args, **kwargs)
    return decorated_function


def role_required(*roles):
    """
    Require specific role(s)

    Usage:
        @role_required('SuperAdmin', 'Executive')
        def multi_role_view():
            pass
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Please log in to access this page.', 'warning')
                return redirect(url_for('auth.login'))

            if current_user.role not in roles:
                flash('You do not have permission to access this page.', 'danger')
                abort(403)

            return f(*args, **kwargs)
        return decorated_function
    return decorator


def active_account_required(f):
    """
    Require active user account

    Usage:
        @active_account_required
        def active_user_view():
            pass
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))

        if not current_user.is_active:
            flash('Your account has been deactivated. Please contact the administrator.', 'danger')
            return redirect(url_for('auth.logout'))

        return f(*args, **kwargs)
    return decorated_function


def check_account_lock(f):
    """
    Check if account is locked due to failed login attempts

    Usage:
        @check_account_lock
        def login_view():
            pass
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_authenticated and current_user.account_locked_until:
            from datetime import datetime
            if datetime.utcnow() < current_user.account_locked_until:
                flash('Your account is temporarily locked due to multiple failed login attempts. Please try again later.', 'danger')
                return redirect(url_for('auth.logout'))

        return f(*args, **kwargs)
    return decorated_function


def password_change_required(f):
    """
    Redirect to password change if must_change_password is True

    Usage:
        @password_change_required
        def protected_view():
            pass
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))

        # Allow access to password change and logout
        from flask import request
        if request.endpoint not in ['auth.change_password', 'auth.logout']:
            if current_user.must_change_password:
                flash('You must change your password before continuing.', 'warning')
                return redirect(url_for('auth.change_password'))

        return f(*args, **kwargs)
    return decorated_function


def member_or_self_required(f):
    """
    Allow access if user is viewing their own data or is Executive/SuperAdmin/Auditor

    Usage:
        @member_or_self_required
        def view_member(member_id):
            pass
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))

        member_id = kwargs.get('member_id') or kwargs.get('id')

        # Allow if viewing own data or is Executive/SuperAdmin/Auditor
        if not (current_user.member_id == member_id or
                current_user.is_executive() or
                current_user.is_super_admin() or
                current_user.is_auditor()):
            flash('You do not have permission to access this page.', 'danger')
            abort(403)

        return f(*args, **kwargs)
    return decorated_function


def audit_log(action_type, entity_type=None):
    """
    Decorator to automatically log actions to audit trail

    Usage:
        @audit_log('Create', 'Member')
        def create_member():
            pass
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            from flask import request
            from app.models.audit import AuditLog

            # Execute the function
            result = f(*args, **kwargs)

            # Log the action if user is authenticated
            if current_user.is_authenticated:
                description = f"{action_type}"
                if entity_type:
                    description += f" {entity_type}"

                entity_id = kwargs.get('id') or kwargs.get('member_id') or kwargs.get('loan_id')

                AuditLog.log_action(
                    user_id=current_user.id,
                    action_type=action_type,
                    description=description,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    ip_address=request.remote_addr,
                    user_agent=request.user_agent.string
                )

            return result
        return decorated_function
    return decorator
