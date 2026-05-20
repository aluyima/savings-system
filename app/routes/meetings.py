"""
Meetings Routes
Handles meeting scheduling, attendance, minutes, and action items
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from app import db
from app.models.meeting import Meeting, Attendance, Minutes, ActionItem
from app.models.member import Member
from app.utils.decorators import executive_required
from datetime import datetime, date, time
from sqlalchemy import func, extract

meetings = Blueprint('meetings', __name__, url_prefix='/meetings')


@meetings.route('/')
@login_required
def list_meetings():
    """List all meetings"""
    status_filter = request.args.get('status', '')
    type_filter = request.args.get('type', '')

    query = Meeting.query

    if status_filter:
        query = query.filter(Meeting.status == status_filter)

    if type_filter:
        query = query.filter(Meeting.meeting_type == type_filter)

    meetings_list = query.order_by(Meeting.meeting_date.desc()).all()

    # Get statistics
    total_meetings = Meeting.query.count()
    upcoming_meetings = Meeting.query.filter(
        Meeting.meeting_date >= date.today(),
        Meeting.status == 'Scheduled'
    ).count()

    return render_template('meetings/list.html',
                         meetings=meetings_list,
                         status_filter=status_filter,
                         type_filter=type_filter,
                         total_meetings=total_meetings,
                         upcoming_meetings=upcoming_meetings)


@meetings.route('/schedule', methods=['GET', 'POST'])
@login_required
@executive_required
def schedule_meeting():
    """Schedule a new meeting"""
    if request.method == 'POST':
        try:
            meeting_date = datetime.strptime(request.form.get('meeting_date'), '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid meeting date!', 'danger')
            return redirect(url_for('meetings.schedule_meeting'))

        try:
            meeting_time = datetime.strptime(request.form.get('meeting_time'), '%H:%M').time()
        except ValueError:
            flash('Invalid meeting time!', 'danger')
            return redirect(url_for('meetings.schedule_meeting'))

        meeting = Meeting(
            meeting_type=request.form.get('meeting_type'),
            meeting_date=meeting_date,
            meeting_time=meeting_time,
            venue=request.form.get('venue'),
            agenda=request.form.get('agenda'),
            called_by=current_user.id,
            status='Scheduled'
        )

        db.session.add(meeting)
        db.session.commit()

        flash('Meeting scheduled successfully!', 'success')
        return redirect(url_for('meetings.view_meeting', id=meeting.id))

    return render_template('meetings/schedule.html')


@meetings.route('/<int:id>')
@login_required
def view_meeting(id):
    """View meeting details"""
    meeting = Meeting.query.get_or_404(id)

    # Get attendance records
    attendance_records = Attendance.query.filter_by(meeting_id=id).all()

    # Get action items
    action_items = ActionItem.query.filter_by(meeting_id=id).all()

    return render_template('meetings/view.html',
                         meeting=meeting,
                         attendance_records=attendance_records,
                         action_items=action_items)


@meetings.route('/<int:id>/attendance', methods=['GET', 'POST'])
@login_required
@executive_required
def record_attendance(id):
    """Record attendance for a meeting"""
    meeting = Meeting.query.get_or_404(id)

    if meeting.status == 'Cancelled':
        flash('Cannot record attendance for cancelled meeting!', 'warning')
        return redirect(url_for('meetings.view_meeting', id=id))

    if request.method == 'POST':
        # Process attendance
        member_ids = request.form.getlist('member_ids[]')
        statuses = request.form.getlist('statuses[]')
        arrival_times = request.form.getlist('arrival_times[]')

        for i, member_id in enumerate(member_ids):
            if not member_id:
                continue

            status = statuses[i] if i < len(statuses) else 'Absent'
            arrival_time_str = arrival_times[i] if i < len(arrival_times) else None

            # Parse arrival time
            arrival_time = None
            if arrival_time_str and status == 'Present':
                try:
                    arrival_time = datetime.strptime(arrival_time_str, '%H:%M').time()
                except ValueError:
                    pass

            # Check if attendance already exists
            existing = Attendance.query.filter_by(
                meeting_id=meeting.id,
                member_id=int(member_id)
            ).first()

            if existing:
                existing.status = status
                existing.arrival_time = arrival_time
            else:
                attendance = Attendance(
                    meeting_id=meeting.id,
                    member_id=int(member_id),
                    status=status,
                    arrival_time=arrival_time,
                    recorded_by=current_user.id
                )
                db.session.add(attendance)

        # Check quorum
        meeting.check_quorum()
        db.session.commit()

        flash('Attendance recorded successfully!', 'success')
        return redirect(url_for('meetings.view_meeting', id=id))

    # GET request - show attendance form
    members = Member.query.filter_by(status='Active').order_by(Member.member_number).all()

    # Get existing attendance
    existing_attendance = {}
    for att in Attendance.query.filter_by(meeting_id=id).all():
        existing_attendance[att.member_id] = att

    return render_template('meetings/attendance.html',
                         meeting=meeting,
                         members=members,
                         existing_attendance=existing_attendance)


@meetings.route('/<int:id>/minutes', methods=['GET', 'POST'])
@login_required
@executive_required
def manage_minutes(id):
    """Add or update meeting minutes"""
    meeting = Meeting.query.get_or_404(id)

    if request.method == 'POST':
        # Handle PDF document upload
        if 'minutes_document' not in request.files:
            flash('Minutes document is required!', 'danger')
            return redirect(url_for('meetings.manage_minutes', id=id))

        file = request.files['minutes_document']
        if file.filename == '':
            flash('No file selected!', 'danger')
            return redirect(url_for('meetings.manage_minutes', id=id))

        # Validate file type
        if not file.filename.lower().endswith('.pdf'):
            flash('Only PDF files are allowed for meeting minutes!', 'danger')
            return redirect(url_for('meetings.manage_minutes', id=id))

        # Save the file
        from werkzeug.utils import secure_filename
        import os

        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        meeting_date_str = meeting.meeting_date.strftime('%Y%m%d')
        unique_filename = f"minutes_{meeting_date_str}_{timestamp}_{filename}"

        minutes_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'minutes')
        os.makedirs(minutes_folder, exist_ok=True)

        file_path = os.path.join(minutes_folder, unique_filename)
        file.save(file_path)

        resolutions_summary = request.form.get('resolutions_summary')

        existing_minutes = Minutes.query.filter_by(meeting_id=id).first()

        if existing_minutes:
            existing_minutes.minutes_document_path = f"minutes/{unique_filename}"
            existing_minutes.resolutions_summary = resolutions_summary
            existing_minutes.updated_at = datetime.utcnow()
        else:
            minutes = Minutes(
                meeting_id=id,
                minutes_document_path=f"minutes/{unique_filename}",
                resolutions_summary=resolutions_summary,
                created_by=current_user.id
            )
            db.session.add(minutes)

        meeting.status = 'Completed'
        db.session.commit()

        flash('Minutes uploaded successfully!', 'success')
        return redirect(url_for('meetings.view_meeting', id=id))

    minutes = Minutes.query.filter_by(meeting_id=id).first()
    return render_template('meetings/minutes.html', meeting=meeting, minutes=minutes)


@meetings.route('/<int:id>/action-item', methods=['POST'])
@login_required
@executive_required
def add_action_item(id):
    """Add action item from meeting"""
    meeting = Meeting.query.get_or_404(id)

    try:
        deadline = datetime.strptime(request.form.get('deadline'), '%Y-%m-%d').date()
    except ValueError:
        flash('Invalid deadline date!', 'danger')
        return redirect(url_for('meetings.view_meeting', id=id))

    action_item = ActionItem(
        meeting_id=id,
        description=request.form.get('description'),
        assigned_to=int(request.form.get('assigned_to')),
        deadline=deadline,
        status='Pending'
    )

    db.session.add(action_item)
    db.session.commit()

    flash('Action item added successfully!', 'success')
    return redirect(url_for('meetings.view_meeting', id=id))


@meetings.route('/action-items')
@login_required
def list_action_items():
    """List all action items"""
    status_filter = request.args.get('status', '')

    query = ActionItem.query

    if status_filter:
        query = query.filter(ActionItem.status == status_filter)

    # Sort by deadline
    action_items = query.order_by(ActionItem.deadline.asc()).all()

    return render_template('meetings/action_items.html',
                         action_items=action_items,
                         status_filter=status_filter,
                         today=date.today())


@meetings.route('/action-item/<int:id>/update', methods=['POST'])
@login_required
def update_action_item(id):
    """Update action item status"""
    action_item = ActionItem.query.get_or_404(id)

    # Check permission
    if not (current_user.is_executive() or current_user.is_super_admin()):
        if not hasattr(current_user, 'member') or action_item.assigned_to != current_user.member.id:
            flash('You do not have permission to update this action item!', 'danger')
            return redirect(url_for('meetings.list_action_items'))

    new_status = request.form.get('status')
    action_item.status = new_status

    if new_status == 'Completed':
        action_item.completion_date = date.today()
        action_item.completion_notes = request.form.get('completion_notes')

    db.session.commit()

    flash('Action item updated successfully!', 'success')
    return redirect(request.referrer or url_for('meetings.list_action_items'))


@meetings.route('/<int:id>/cancel', methods=['POST'])
@login_required
@executive_required
def cancel_meeting(id):
    """Cancel a scheduled meeting"""
    meeting = Meeting.query.get_or_404(id)

    if meeting.status != 'Scheduled':
        flash('Only scheduled meetings can be cancelled!', 'warning')
        return redirect(url_for('meetings.view_meeting', id=id))

    meeting.status = 'Cancelled'
    db.session.commit()

    flash('Meeting cancelled successfully.', 'info')
    return redirect(url_for('meetings.view_meeting', id=id))
