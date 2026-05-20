"""
User Management Routes
Handles user account management, roles, and permissions
SuperAdmin only
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from app import db
from app.models.user import User
from app.models.member import Member
from app.models.audit import AuditLog
from app.utils.decorators import super_admin_required
from datetime import datetime

users = Blueprint('users', __name__, url_prefix='/users')


@users.route('/')
@login_required
@super_admin_required
def list_users():
    """List all user accounts"""
    # Get filters
    role_filter = request.args.get('role', '')
    status_filter = request.args.get('status', '')

    query = User.query

    if role_filter:
        query = query.filter(User.role == role_filter)

    if status_filter == 'active':
        query = query.filter(User.is_active == True)
    elif status_filter == 'inactive':
        query = query.filter(User.is_active == False)

    users_list = query.order_by(User.created_at.desc()).all()

    # Get statistics
    total_users = User.query.count()
    active_users = User.query.filter_by(is_active=True).count()
    super_admins = User.query.filter_by(role='SuperAdmin').count()
    executives = User.query.filter_by(role='Executive').count()

    return render_template('users/list.html',
                         users=users_list,
                         role_filter=role_filter,
                         status_filter=status_filter,
                         total_users=total_users,
                         active_users=active_users,
                         super_admins=super_admins,
                         executives=executives)


@users.route('/create', methods=['GET', 'POST'])
@login_required
@super_admin_required
def create_user():
    """Create a new user account"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        role = request.form.get('role')
        member_id = request.form.get('member_id')

        # Validation
        if not all([username, password, role]):
            flash('Username, password, and role are required!', 'danger')
            return redirect(url_for('users.create_user'))

        if len(password) < 8:
            flash('Password must be at least 8 characters long!', 'danger')
            return redirect(url_for('users.create_user'))

        if password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return redirect(url_for('users.create_user'))

        # Check if username already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists!', 'danger')
            return redirect(url_for('users.create_user'))

        # Validate member_id if provided
        if member_id:
            member = Member.query.get(int(member_id))
            if not member:
                flash('Invalid member selected!', 'danger')
                return redirect(url_for('users.create_user'))

            # Check if member already has a user account
            if User.query.filter_by(member_id=member.id).first():
                flash('This member already has a user account!', 'danger')
                return redirect(url_for('users.create_user'))

        # Create user
        user = User(
            username=username,
            role=role,
            member_id=int(member_id) if member_id else None,
            is_active=True,
            must_change_password=True  # Force password change on first login
        )
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        # Log action
        AuditLog.log_action(
            user_id=current_user.id,
            action_type='UserCreated',
            description=f'Created user account: {username} (Role: {role})',
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string
        )

        flash(f'User account created successfully! Username: {username}', 'success')
        return redirect(url_for('users.view_user', id=user.id))

    # GET request - show form
    members = Member.query.filter_by(status='Active').order_by(Member.member_number).all()

    # Filter out members who already have user accounts
    available_members = []
    for member in members:
        if not User.query.filter_by(member_id=member.id).first():
            available_members.append(member)

    return render_template('users/create.html', members=available_members)


@users.route('/<int:id>')
@login_required
@super_admin_required
def view_user(id):
    """View user details"""
    user = User.query.get_or_404(id)

    # Get recent activity from audit logs
    recent_activity = AuditLog.query.filter_by(user_id=id).order_by(
        AuditLog.timestamp.desc()
    ).limit(20).all()

    return render_template('users/view.html',
                         user=user,
                         recent_activity=recent_activity)


@users.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@super_admin_required
def edit_user(id):
    """Edit user account"""
    user = User.query.get_or_404(id)

    if request.method == 'POST':
        new_role = request.form.get('role')
        member_id = request.form.get('member_id')

        # Update role
        if new_role != user.role:
            old_role = user.role
            user.role = new_role

            # Log role change
            AuditLog.log_action(
                user_id=current_user.id,
                action_type='UserRoleChanged',
                description=f'Changed user {user.username} role from {old_role} to {new_role}',
                ip_address=request.remote_addr,
                user_agent=request.user_agent.string
            )

        # Update member association
        if member_id:
            new_member = Member.query.get(int(member_id))
            if new_member:
                # Check if new member already has a different user account
                existing_user = User.query.filter_by(member_id=new_member.id).first()
                if existing_user and existing_user.id != user.id:
                    flash('Selected member already has a user account!', 'danger')
                    return redirect(url_for('users.edit_user', id=id))

                user.member_id = new_member.id

        db.session.commit()

        flash('User account updated successfully!', 'success')
        return redirect(url_for('users.view_user', id=id))

    # GET request
    members = Member.query.filter_by(status='Active').order_by(Member.member_number).all()

    # Filter out members who already have user accounts (except this user's member)
    available_members = []
    for member in members:
        existing_user = User.query.filter_by(member_id=member.id).first()
        if not existing_user or existing_user.id == user.id:
            available_members.append(member)

    return render_template('users/edit.html',
                         user=user,
                         members=available_members)


@users.route('/<int:id>/reset-password', methods=['POST'])
@login_required
@super_admin_required
def reset_password(id):
    """Reset user password (admin function)"""
    user = User.query.get_or_404(id)

    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')

    if not new_password or len(new_password) < 8:
        flash('Password must be at least 8 characters long!', 'danger')
        return redirect(url_for('users.view_user', id=id))

    if new_password != confirm_password:
        flash('Passwords do not match!', 'danger')
        return redirect(url_for('users.view_user', id=id))

    # Reset password
    user.set_password(new_password)
    user.must_change_password = True  # Force password change on next login
    user.account_locked_until = None  # Unlock account if locked
    user.failed_login_attempts = 0

    db.session.commit()

    # Log action
    AuditLog.log_action(
        user_id=current_user.id,
        action_type='PasswordReset',
        description=f'Reset password for user: {user.username}',
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string
    )

    flash(f'Password reset successfully for {user.username}. User must change password on next login.', 'success')
    return redirect(url_for('users.view_user', id=id))


@users.route('/<int:id>/toggle-status', methods=['POST'])
@login_required
@super_admin_required
def toggle_status(id):
    """Activate or deactivate user account"""
    user = User.query.get_or_404(id)

    # Prevent deactivating yourself
    if user.id == current_user.id:
        flash('You cannot deactivate your own account!', 'danger')
        return redirect(url_for('users.view_user', id=id))

    # Prevent deactivating the last SuperAdmin
    if user.role == 'SuperAdmin' and user.is_active:
        active_super_admins = User.query.filter_by(role='SuperAdmin', is_active=True).count()
        if active_super_admins <= 1:
            flash('Cannot deactivate the last active SuperAdmin account!', 'danger')
            return redirect(url_for('users.view_user', id=id))

    # Toggle status
    user.is_active = not user.is_active
    db.session.commit()

    # Log action
    action = 'activated' if user.is_active else 'deactivated'
    AuditLog.log_action(
        user_id=current_user.id,
        action_type='UserStatusChanged',
        description=f'User {user.username} {action}',
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string
    )

    flash(f'User account {action} successfully!', 'success')
    return redirect(url_for('users.view_user', id=id))


@users.route('/<int:id>/unlock', methods=['POST'])
@login_required
@super_admin_required
def unlock_account(id):
    """Unlock a locked user account"""
    user = User.query.get_or_404(id)

    user.account_locked_until = None
    user.failed_login_attempts = 0
    db.session.commit()

    # Log action
    AuditLog.log_action(
        user_id=current_user.id,
        action_type='AccountUnlocked',
        description=f'Unlocked user account: {user.username}',
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string
    )

    flash(f'User account {user.username} unlocked successfully!', 'success')
    return redirect(url_for('users.view_user', id=id))
