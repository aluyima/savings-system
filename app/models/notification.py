"""
Notification Model
Manages in-app notifications for users
"""
from app import db
from datetime import datetime


class Notification(db.Model):
    """
    Notification table
    Stores in-app notifications for users
    """
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    notification_type = db.Column(db.String(50), nullable=False)  # Info, Warning, Success, Danger
    category = db.Column(db.String(50))  # Meeting, Contribution, Welfare, Loan, System
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    link_url = db.Column(db.String(255))  # Optional link to related entity
    is_read = db.Column(db.Boolean, default=False, index=True)
    read_at = db.Column(db.DateTime)
    priority = db.Column(db.String(20), default='Normal')  # Low, Normal, High, Urgent
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    user = db.relationship('User', backref='notifications')

    def __repr__(self):
        return f'<Notification {self.title} - {self.user_id}>'

    def mark_as_read(self):
        """Mark notification as read"""
        self.is_read = True
        self.read_at = datetime.utcnow()
        db.session.commit()

    @staticmethod
    def create_notification(user_id, title, message, notification_type='Info',
                           category=None, link_url=None, priority='Normal'):
        """
        Helper method to create notifications

        Args:
            user_id: ID of user to notify
            title: Notification title
            message: Notification message
            notification_type: Type (Info, Warning, Success, Danger)
            category: Category (Meeting, Contribution, etc.)
            link_url: Optional URL to related entity
            priority: Priority level (Low, Normal, High, Urgent)
        """
        notification = Notification(
            user_id=user_id,
            notification_type=notification_type,
            category=category,
            title=title,
            message=message,
            link_url=link_url,
            priority=priority
        )

        db.session.add(notification)
        db.session.commit()

        return notification

    @staticmethod
    def create_bulk_notification(user_ids, title, message, notification_type='Info',
                                 category=None, link_url=None, priority='Normal'):
        """
        Create notifications for multiple users

        Args:
            user_ids: List of user IDs to notify
            title: Notification title
            message: Notification message
            notification_type: Type (Info, Warning, Success, Danger)
            category: Category (Meeting, Contribution, etc.)
            link_url: Optional URL to related entity
            priority: Priority level (Low, Normal, High, Urgent)
        """
        notifications = []
        for user_id in user_ids:
            notification = Notification(
                user_id=user_id,
                notification_type=notification_type,
                category=category,
                title=title,
                message=message,
                link_url=link_url,
                priority=priority
            )
            notifications.append(notification)

        db.session.add_all(notifications)
        db.session.commit()

        return notifications

    @staticmethod
    def get_unread_count(user_id):
        """Get count of unread notifications for a user"""
        return Notification.query.filter_by(user_id=user_id, is_read=False).count()
