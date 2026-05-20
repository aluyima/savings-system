"""
Audit Log Model
Comprehensive audit trail for all system actions
"""
from app import db
from datetime import datetime


class AuditLog(db.Model):
    """
    Audit Log table
    Tracks all significant actions in the system
    """
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action_type = db.Column(db.String(50), nullable=False)  # Login, Logout, Create, Update, Delete, Approve, etc.
    entity_type = db.Column(db.String(50))  # Member, Contribution, Loan, WelfareRequest, etc.
    entity_id = db.Column(db.Integer)
    description = db.Column(db.Text, nullable=False)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(255))
    old_values = db.Column(db.Text)  # JSON string of old values
    new_values = db.Column(db.Text)  # JSON string of new values
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    user = db.relationship('User', backref='audit_logs')

    def __repr__(self):
        return f'<AuditLog {self.action_type} - {self.entity_type}>'

    @staticmethod
    def log_action(user_id, action_type, description, entity_type=None, entity_id=None,
                   old_values=None, new_values=None, ip_address=None, user_agent=None):
        """
        Helper method to create audit log entries

        Args:
            user_id: ID of user performing action
            action_type: Type of action (Login, Create, Update, etc.)
            description: Human-readable description
            entity_type: Type of entity affected (optional)
            entity_id: ID of entity affected (optional)
            old_values: JSON string of old values (optional)
            new_values: JSON string of new values (optional)
            ip_address: User's IP address (optional)
            user_agent: User's browser/client info (optional)
        """
        import json

        log = AuditLog(
            user_id=user_id,
            action_type=action_type,
            entity_type=entity_type,
            entity_id=entity_id,
            description=description,
            ip_address=ip_address,
            user_agent=user_agent,
            old_values=json.dumps(old_values) if old_values else None,
            new_values=json.dumps(new_values) if new_values else None
        )

        db.session.add(log)
        db.session.commit()

        return log
