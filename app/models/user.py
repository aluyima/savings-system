"""
User Model
Handles authentication and authorization
"""
from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime


class User(UserMixin, db.Model):
    """
    User table for authentication
    Each user is linked to a member
    """
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('members.id'), unique=True, nullable=False)
    username = db.Column(db.String(20), unique=True, nullable=False)  # Phone number
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # SuperAdmin, Executive, Auditor, Member
    is_active = db.Column(db.Boolean, default=True)
    must_change_password = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.DateTime)
    failed_login_attempts = db.Column(db.Integer, default=0)
    account_locked_until = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    member = db.relationship('Member', backref=db.backref('user', uselist=False))

    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verify password"""
        return check_password_hash(self.password_hash, password)

    def is_super_admin(self):
        """Check if user is Super Admin"""
        return self.role == 'SuperAdmin'

    def is_executive(self):
        """Check if user is Executive member"""
        return self.role == 'Executive'

    def is_auditor(self):
        """Check if user is Auditor"""
        return self.role == 'Auditor'

    def can_record_contributions(self):
        """Check if user can record contributions (Treasurer/Secretary)"""
        return self.role in ['SuperAdmin', 'Executive']

    def can_approve_welfare(self):
        """Check if user can approve welfare requests (Chairman)"""
        return self.role in ['SuperAdmin', 'Executive']

    def can_view_all_members(self):
        """Check if user can view all member records"""
        return self.role in ['SuperAdmin', 'Executive', 'Auditor']

    def can_manage_next_of_kin(self):
        """Check if user can manage next of kin"""
        return self.role in ['SuperAdmin', 'Executive']

    def is_auditor(self):
        """Check if user is an Auditor"""
        return self.role == 'Auditor'

    def __repr__(self):
        return f'<User {self.username} ({self.role})>'


@login_manager.user_loader
def load_user(user_id):
    """Load user by ID for Flask-Login"""
    return User.query.get(int(user_id))
