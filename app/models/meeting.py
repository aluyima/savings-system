"""
Meeting, Attendance, Minutes, and ActionItem Models
Handles meeting management and documentation
"""
from app import db
from datetime import datetime


class Meeting(db.Model):
    """
    Meeting table
    Tracks scheduled and completed meetings
    """
    __tablename__ = 'meetings'

    id = db.Column(db.Integer, primary_key=True)
    meeting_type = db.Column(db.String(20), nullable=False)  # Regular, Emergency, AnnualGeneral
    meeting_date = db.Column(db.Date, nullable=False)
    meeting_time = db.Column(db.Time, nullable=False)
    venue = db.Column(db.String(255), nullable=False)
    agenda = db.Column(db.Text, nullable=False)
    called_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    quorum_met = db.Column(db.Boolean)
    total_attendance = db.Column(db.Integer)
    status = db.Column(db.String(20), default='Scheduled')  # Scheduled, Completed, Cancelled
    notification_sent = db.Column(db.Boolean, default=False)
    notification_sent_date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    caller = db.relationship('User', foreign_keys=[called_by])
    attendance_records = db.relationship('Attendance', backref='meeting', lazy='dynamic', cascade='all, delete-orphan')
    minutes = db.relationship('Minutes', backref='meeting', uselist=False)
    action_items = db.relationship('ActionItem', backref='meeting', lazy='dynamic')

    def __repr__(self):
        return f'<Meeting {self.meeting_date} - {self.meeting_type}>'

    def check_quorum(self):
        """Check if quorum is met (5 members per specification)"""
        from flask import current_app
        quorum_requirement = current_app.config.get('QUORUM_REQUIREMENT', 5)
        present_count = Attendance.query.filter_by(meeting_id=self.id, status='Present').count()
        self.total_attendance = present_count
        self.quorum_met = present_count >= quorum_requirement
        return self.quorum_met


class Attendance(db.Model):
    """
    Attendance table
    Records member attendance at meetings
    """
    __tablename__ = 'attendance'
    __table_args__ = (
        db.UniqueConstraint('meeting_id', 'member_id', name='uq_meeting_member'),
    )

    id = db.Column(db.Integer, primary_key=True)
    meeting_id = db.Column(db.Integer, db.ForeignKey('meetings.id'), nullable=False)
    member_id = db.Column(db.Integer, db.ForeignKey('members.id'), nullable=False)
    status = db.Column(db.String(20), nullable=False)  # Present, Absent, Excused
    arrival_time = db.Column(db.Time)
    departure_time = db.Column(db.Time)
    notes = db.Column(db.Text)
    recorded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    member = db.relationship('Member')
    recorder = db.relationship('User', foreign_keys=[recorded_by])

    def __repr__(self):
        return f'<Attendance {self.meeting.meeting_date} - {self.member.full_name}>'


class Minutes(db.Model):
    """
    Minutes table
    Stores meeting minutes
    """
    __tablename__ = 'minutes'

    id = db.Column(db.Integer, primary_key=True)
    meeting_id = db.Column(db.Integer, db.ForeignKey('meetings.id'), unique=True, nullable=False)
    minutes_document_path = db.Column(db.String(255))
    minutes_html = db.Column(db.Text)
    resolutions_summary = db.Column(db.Text)
    chairperson_approved = db.Column(db.Boolean, default=False)
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    approved_date = db.Column(db.DateTime)
    published = db.Column(db.Boolean, default=False)
    published_date = db.Column(db.DateTime)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    approver = db.relationship('User', foreign_keys=[approved_by])
    creator = db.relationship('User', foreign_keys=[created_by])

    def __repr__(self):
        return f'<Minutes {self.meeting.meeting_date}>'


class ActionItem(db.Model):
    """
    Action Item table
    Tracks action items from meetings
    """
    __tablename__ = 'action_items'

    id = db.Column(db.Integer, primary_key=True)
    meeting_id = db.Column(db.Integer, db.ForeignKey('meetings.id'), nullable=False)
    description = db.Column(db.Text, nullable=False)
    assigned_to = db.Column(db.Integer, db.ForeignKey('members.id'), nullable=False)
    deadline = db.Column(db.Date)
    status = db.Column(db.String(20), default='Pending')  # Pending, InProgress, Completed, Cancelled
    completion_date = db.Column(db.Date)
    completion_notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    assignee = db.relationship('Member', foreign_keys=[assigned_to])

    def __repr__(self):
        return f'<ActionItem {self.description[:30]}...>'
