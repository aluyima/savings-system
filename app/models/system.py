"""
System Settings Model
Configurable system parameters and constants
"""
from app import db
from datetime import datetime


class SystemSetting(db.Model):
    """
    System Settings table
    Stores configurable system parameters
    """
    __tablename__ = 'system_settings'

    id = db.Column(db.Integer, primary_key=True)
    setting_key = db.Column(db.String(100), unique=True, nullable=False, index=True)
    setting_value = db.Column(db.Text, nullable=False)
    setting_type = db.Column(db.String(20), nullable=False)  # String, Integer, Decimal, Boolean, JSON
    category = db.Column(db.String(50))  # Financial, System, Notification, Security
    description = db.Column(db.Text)
    is_editable = db.Column(db.Boolean, default=True)
    updated_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    updater = db.relationship('User', foreign_keys=[updated_by])

    def __repr__(self):
        return f'<SystemSetting {self.setting_key}>'

    def get_value(self):
        """Get typed value based on setting_type"""
        if self.setting_type == 'Integer':
            return int(self.setting_value)
        elif self.setting_type == 'Decimal':
            from decimal import Decimal
            return Decimal(self.setting_value)
        elif self.setting_type == 'Boolean':
            return self.setting_value.lower() in ('true', '1', 'yes')
        elif self.setting_type == 'JSON':
            import json
            return json.loads(self.setting_value)
        else:
            return self.setting_value

    def set_value(self, value, user_id):
        """Set value with type conversion"""
        import json

        if not self.is_editable:
            raise ValueError(f'Setting {self.setting_key} is not editable')

        if self.setting_type == 'Integer':
            self.setting_value = str(int(value))
        elif self.setting_type == 'Decimal':
            from decimal import Decimal
            self.setting_value = str(Decimal(value))
        elif self.setting_type == 'Boolean':
            self.setting_value = str(bool(value))
        elif self.setting_type == 'JSON':
            self.setting_value = json.dumps(value)
        else:
            self.setting_value = str(value)

        self.updated_by = user_id
        self.updated_at = datetime.utcnow()
        db.session.commit()

    @staticmethod
    def get_setting(key, default=None):
        """Get setting value by key"""
        setting = SystemSetting.query.filter_by(setting_key=key).first()
        if setting:
            return setting.get_value()
        return default

    @staticmethod
    def update_setting(key, value, user_id):
        """Update setting value by key"""
        setting = SystemSetting.query.filter_by(setting_key=key).first()
        if not setting:
            raise ValueError(f'Setting {key} not found')

        setting.set_value(value, user_id)
        return setting

    @staticmethod
    def initialize_defaults():
        """
        Initialize default system settings
        Called during database initialization
        """
        default_settings = [
            # Financial Settings
            {
                'setting_key': 'MEMBERSHIP_FEE',
                'setting_value': '20000',
                'setting_type': 'Integer',
                'category': 'Financial',
                'description': 'One-time membership registration fee (UGX)',
                'is_editable': True
            },
            {
                'setting_key': 'MONTHLY_CONTRIBUTION',
                'setting_value': '100000',
                'setting_type': 'Integer',
                'category': 'Financial',
                'description': 'Standard monthly contribution amount (UGX)',
                'is_editable': True
            },
            {
                'setting_key': 'BEREAVEMENT_AMOUNT',
                'setting_value': '500000',
                'setting_type': 'Integer',
                'category': 'Financial',
                'description': 'Standard bereavement support amount (UGX)',
                'is_editable': True
            },
            {
                'setting_key': 'LOAN_INTEREST_RATE',
                'setting_value': '5.00',
                'setting_type': 'Decimal',
                'category': 'Financial',
                'description': 'Monthly loan interest rate (percentage)',
                'is_editable': True
            },
            {
                'setting_key': 'MAX_LOAN_PERIOD',
                'setting_value': '2',
                'setting_type': 'Integer',
                'category': 'Financial',
                'description': 'Maximum loan repayment period (months)',
                'is_editable': True
            },
            {
                'setting_key': 'LOAN_DEFAULT_DAYS',
                'setting_value': '30',
                'setting_type': 'Integer',
                'category': 'Financial',
                'description': 'Days after due date before loan is marked as defaulted',
                'is_editable': True
            },

            # Membership Settings
            {
                'setting_key': 'QUALIFICATION_PERIOD',
                'setting_value': '5',
                'setting_type': 'Integer',
                'category': 'Membership',
                'description': 'Consecutive months required to qualify for benefits',
                'is_editable': True
            },
            {
                'setting_key': 'QUORUM_REQUIREMENT',
                'setting_value': '5',
                'setting_type': 'Integer',
                'category': 'Membership',
                'description': 'Minimum members required for valid meeting quorum',
                'is_editable': True
            },

            # System Settings
            {
                'setting_key': 'SYSTEM_NAME',
                'setting_value': 'Old Timers Savings Group',
                'setting_type': 'String',
                'category': 'System',
                'description': 'System display name',
                'is_editable': True
            },
            {
                'setting_key': 'SYSTEM_TIMEZONE',
                'setting_value': 'Africa/Kampala',
                'setting_type': 'String',
                'category': 'System',
                'description': 'System timezone',
                'is_editable': True
            },
            {
                'setting_key': 'CURRENCY_CODE',
                'setting_value': 'UGX',
                'setting_type': 'String',
                'category': 'System',
                'description': 'Currency code',
                'is_editable': False
            },
            {
                'setting_key': 'SESSION_TIMEOUT',
                'setting_value': '30',
                'setting_type': 'Integer',
                'category': 'Security',
                'description': 'Session timeout in minutes',
                'is_editable': True
            },
            {
                'setting_key': 'MAX_LOGIN_ATTEMPTS',
                'setting_value': '5',
                'setting_type': 'Integer',
                'category': 'Security',
                'description': 'Maximum failed login attempts before account lock',
                'is_editable': True
            },
            {
                'setting_key': 'ACCOUNT_LOCK_DURATION',
                'setting_value': '30',
                'setting_type': 'Integer',
                'category': 'Security',
                'description': 'Account lock duration in minutes',
                'is_editable': True
            },
        ]

        for setting_data in default_settings:
            existing = SystemSetting.query.filter_by(setting_key=setting_data['setting_key']).first()
            if not existing:
                setting = SystemSetting(**setting_data)
                db.session.add(setting)

        db.session.commit()
