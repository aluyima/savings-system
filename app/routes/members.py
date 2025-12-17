"""
Member Management Routes
Handles member CRUD operations and next of kin management
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app import db
from app.models.member import Member, NextOfKin
from app.models.user import User
from app.utils.decorators import executive_required, member_or_self_required
from app.utils.helpers import parse_phone, get_current_time
from datetime import date

members = Blueprint('members', __name__, url_prefix='/members')


@members.route('/')
@login_required
def list_members():
    """List all members - Auditors have read-only access"""
    # Check permissions
    if not (current_user.is_executive() or current_user.is_super_admin() or current_user.is_auditor()):
        abort(403)
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', 'all')
    search = request.args.get('search', '')

    query = Member.query

    # Apply filters
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)

    if search:
        query = query.filter(
            db.or_(
                Member.full_name.ilike(f'%{search}%'),
                Member.member_number.ilike(f'%{search}%'),
                Member.phone_primary.ilike(f'%{search}%')
            )
        )

    # Paginate
    per_page = 20
    members_page = query.order_by(Member.member_number).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return render_template('members/list.html',
                         members=members_page,
                         status_filter=status_filter,
                         search=search)


@members.route('/<int:id>')
@login_required
@member_or_self_required
def view_member(id):
    """View member details"""
    member = Member.query.get_or_404(id)

    # Get member's user account if exists
    user_account = User.query.filter_by(member_id=id).first()

    # Get next of kin
    next_of_kin = NextOfKin.query.filter_by(member_id=id).all()

    # Get contribution summary
    from app.models.contribution import Contribution
    contributions = Contribution.query.filter_by(member_id=id).order_by(
        Contribution.payment_date.desc()
    ).limit(10).all()

    # Get active loans
    from app.models.loan import Loan
    active_loans = Loan.query.filter(
        Loan.member_id == id,
        Loan.status.in_(['Disbursed', 'Repaying'])
    ).all()

    return render_template('members/view.html',
                         member=member,
                         user_account=user_account,
                         next_of_kin=next_of_kin,
                         contributions=contributions,
                         active_loans=active_loans)


@members.route('/add', methods=['GET', 'POST'])
@login_required
@executive_required
def add_member():
    """Add new member"""
    if request.method == 'POST':
        # Validate phone number
        phone = request.form.get('phone_primary')
        is_valid, formatted_phone, error = parse_phone(phone)
        if not is_valid:
            flash(f'Invalid phone number: {error}', 'danger')
            return redirect(url_for('members.add_member'))

        # Check if phone already exists
        existing = Member.query.filter_by(phone_primary=formatted_phone).first()
        if existing:
            flash('A member with this phone number already exists.', 'danger')
            return redirect(url_for('members.add_member'))

        # Parse dates
        from datetime import datetime
        date_of_birth = None
        if request.form.get('date_of_birth'):
            try:
                date_of_birth = datetime.strptime(request.form.get('date_of_birth'), '%Y-%m-%d').date()
            except ValueError:
                pass

        date_joined_value = date.today()
        if request.form.get('date_joined'):
            try:
                date_joined_value = datetime.strptime(request.form.get('date_joined'), '%Y-%m-%d').date()
            except ValueError:
                pass

        # Create member
        member = Member(
            full_name=request.form.get('full_name'),
            national_id=request.form.get('national_id') or None,
            date_of_birth=date_of_birth,
            gender=request.form.get('gender'),
            phone_primary=formatted_phone,
            phone_secondary=request.form.get('phone_secondary') or None,
            email=request.form.get('email') or None,
            physical_address=request.form.get('physical_address') or None,
            occupation=request.form.get('occupation') or None,
            date_joined=date_joined_value,
            status='Active',
            created_by=current_user.id
        )

        db.session.add(member)
        db.session.commit()

        # Log the action
        from app.models.audit import AuditLog
        AuditLog.log_action(
            user_id=current_user.id,
            action_type='Create',
            description=f'Created new member: {member.full_name} ({member.member_number})',
            entity_type='Member',
            entity_id=member.id,
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string
        )

        flash(f'Member {member.full_name} added successfully! Member Number: {member.member_number}', 'success')
        return redirect(url_for('members.view_member', id=member.id))

    return render_template('members/add.html')


@members.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@executive_required
def edit_member(id):
    """Edit member details"""
    member = Member.query.get_or_404(id)

    if request.method == 'POST':
        # Store old values for audit
        old_values = {
            'full_name': member.full_name,
            'phone_primary': member.phone_primary,
            'email': member.email
        }

        # Validate phone number if changed
        phone = request.form.get('phone_primary')
        if phone != member.phone_primary:
            is_valid, formatted_phone, error = parse_phone(phone)
            if not is_valid:
                flash(f'Invalid phone number: {error}', 'danger')
                return redirect(url_for('members.edit_member', id=id))

            # Check if phone already exists
            existing = Member.query.filter(
                Member.phone_primary == formatted_phone,
                Member.id != id
            ).first()
            if existing:
                flash('A member with this phone number already exists.', 'danger')
                return redirect(url_for('members.edit_member', id=id))

            member.phone_primary = formatted_phone

        # Parse date of birth
        from datetime import datetime
        date_of_birth = None
        if request.form.get('date_of_birth'):
            try:
                date_of_birth = datetime.strptime(request.form.get('date_of_birth'), '%Y-%m-%d').date()
            except ValueError:
                pass

        # Update member details
        member.full_name = request.form.get('full_name')
        member.national_id = request.form.get('national_id') or None
        member.date_of_birth = date_of_birth
        member.gender = request.form.get('gender')
        member.phone_secondary = request.form.get('phone_secondary') or None
        member.email = request.form.get('email') or None
        member.physical_address = request.form.get('physical_address') or None
        member.occupation = request.form.get('occupation') or None

        db.session.commit()

        # Log the action
        from app.models.audit import AuditLog
        new_values = {
            'full_name': member.full_name,
            'phone_primary': member.phone_primary,
            'email': member.email
        }
        AuditLog.log_action(
            user_id=current_user.id,
            action_type='Update',
            description=f'Updated member: {member.full_name} ({member.member_number})',
            entity_type='Member',
            entity_id=member.id,
            old_values=old_values,
            new_values=new_values,
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string
        )

        flash(f'Member {member.full_name} updated successfully!', 'success')
        return redirect(url_for('members.view_member', id=id))

    return render_template('members/edit.html', member=member)


@members.route('/<int:id>/add-next-of-kin', methods=['GET', 'POST'])
@login_required
@executive_required
def add_next_of_kin(id):
    """Add next of kin for member"""
    member = Member.query.get_or_404(id)

    if request.method == 'POST':
        # Validate phone number
        phone = request.form.get('phone')
        is_valid, formatted_phone, error = parse_phone(phone)
        if not is_valid:
            flash(f'Invalid phone number: {error}', 'danger')
            return redirect(url_for('members.add_next_of_kin', id=id))

        # Create next of kin
        nok = NextOfKin(
            member_id=id,
            kin_type='Primary' if request.form.get('is_primary') == 'on' else 'Alternative',
            full_name=request.form.get('full_name'),
            relationship=request.form.get('relationship'),
            phone_primary=formatted_phone,
            email=request.form.get('email') or None,
            physical_address=request.form.get('physical_address') or None
        )

        # If setting as primary, unset other primary NOKs
        if nok.kin_type == 'Primary':
            NextOfKin.query.filter_by(member_id=id, kin_type='Primary').update({'kin_type': 'Alternative'})

        db.session.add(nok)
        db.session.commit()

        flash(f'Next of kin {nok.full_name} added successfully!', 'success')
        return redirect(url_for('members.view_member', id=id))

    return render_template('members/add_next_of_kin.html', member=member)


@members.route('/<int:member_id>/next-of-kin/<int:nok_id>/delete', methods=['POST'])
@login_required
@executive_required
def delete_next_of_kin(member_id, nok_id):
    """Delete next of kin"""
    nok = NextOfKin.query.get_or_404(nok_id)

    if nok.member_id != member_id:
        abort(404)

    name = nok.full_name
    db.session.delete(nok)
    db.session.commit()

    flash(f'Next of kin {name} removed successfully!', 'success')
    return redirect(url_for('members.view_member', id=member_id))


@members.route('/<int:id>/suspend', methods=['POST'])
@login_required
@executive_required
def suspend_member(id):
    """Suspend member"""
    member = Member.query.get_or_404(id)

    if member.status == 'Suspended':
        flash('Member is already suspended.', 'warning')
        return redirect(url_for('members.view_member', id=id))

    member.status = 'Suspended'
    member.suspension_date = date.today()
    db.session.commit()

    # Log the action
    from app.models.audit import AuditLog
    AuditLog.log_action(
        user_id=current_user.id,
        action_type='Suspend',
        description=f'Suspended member: {member.full_name} ({member.member_number})',
        entity_type='Member',
        entity_id=member.id,
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string
    )

    flash(f'Member {member.full_name} has been suspended.', 'success')
    return redirect(url_for('members.view_member', id=id))


@members.route('/<int:id>/reactivate', methods=['POST'])
@login_required
@executive_required
def reactivate_member(id):
    """Reactivate suspended member"""
    member = Member.query.get_or_404(id)

    if member.status != 'Suspended':
        flash('Only suspended members can be reactivated.', 'warning')
        return redirect(url_for('members.view_member', id=id))

    member.status = 'Active'
    member.suspension_date = None
    db.session.commit()

    # Log the action
    from app.models.audit import AuditLog
    AuditLog.log_action(
        user_id=current_user.id,
        action_type='Reactivate',
        description=f'Reactivated member: {member.full_name} ({member.member_number})',
        entity_type='Member',
        entity_id=member.id,
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string
    )

    flash(f'Member {member.full_name} has been reactivated.', 'success')
    return redirect(url_for('members.view_member', id=id))
