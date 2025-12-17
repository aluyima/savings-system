"""
Member and NextOfKin Models
Core membership management
"""
from app import db
from datetime import datetime
from sqlalchemy import event


class Member(db.Model):
    """
    Member table - core entity
    Stores all member information
    """
    __tablename__ = 'members'

    id = db.Column(db.Integer, primary_key=True)
    member_number = db.Column(db.String(10), unique=True, nullable=False)  # OT-001
    full_name = db.Column(db.String(100), nullable=False)
    national_id = db.Column(db.String(20), unique=True)
    date_of_birth = db.Column(db.Date)
    gender = db.Column(db.String(10))  # Male, Female
    phone_primary = db.Column(db.String(20), nullable=False)
    phone_secondary = db.Column(db.String(20))
    email = db.Column(db.String(100))
    physical_address = db.Column(db.Text)
    occupation = db.Column(db.String(100))

    # Membership information
    date_joined = db.Column(db.Date, nullable=False)
    membership_fee_paid = db.Column(db.Boolean, default=False)
    membership_fee_date = db.Column(db.Date)
    membership_fee_receipt = db.Column(db.String(20))
    status = db.Column(db.String(20), default='Active')  # Active, Inactive, Suspended, Expelled, Deceased
    total_contributed = db.Column(db.Numeric(15, 2), default=0.00)
    consecutive_months_paid = db.Column(db.Integer, default=0)
    last_contribution_date = db.Column(db.Date)
    qualified_for_benefits = db.Column(db.Boolean, default=False)

    # Status tracking
    suspension_date = db.Column(db.Date)
    expulsion_date = db.Column(db.Date)
    expulsion_reason = db.Column(db.Text)
    refund_amount = db.Column(db.Numeric(15, 2))
    refund_paid = db.Column(db.Boolean, default=False)

    # System fields
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer)

    # Relationships
    next_of_kin = db.relationship('NextOfKin', backref='member', lazy='dynamic', cascade='all, delete-orphan')
    contributions = db.relationship('Contribution', backref='member', lazy='dynamic')
    welfare_requests = db.relationship('WelfareRequest', backref='member', lazy='dynamic')
    loans = db.relationship('Loan', backref='member', lazy='dynamic', foreign_keys='Loan.member_id')
    loans_guaranteed1 = db.relationship('Loan', foreign_keys='Loan.guarantor1_id', lazy='dynamic')
    loans_guaranteed2 = db.relationship('Loan', foreign_keys='Loan.guarantor2_id', lazy='dynamic')

    def __repr__(self):
        return f'<Member {self.member_number} - {self.full_name}>'

    def update_contribution_stats(self):
        """Update total contributed and consecutive months"""
        from app.models.contribution import Contribution
        from sqlalchemy import func

        # Calculate total contributed
        total = db.session.query(func.sum(Contribution.amount)).filter_by(member_id=self.id).scalar()
        self.total_contributed = total or 0.00

        # Update last contribution date
        last_contribution = Contribution.query.filter_by(member_id=self.id).order_by(Contribution.payment_date.desc()).first()
        if last_contribution:
            self.last_contribution_date = last_contribution.payment_date

        # Calculate consecutive months (simplified - full logic would check month gaps)
        contribution_count = Contribution.query.filter_by(member_id=self.id).count()
        self.consecutive_months_paid = contribution_count

        # Update qualification status (5 consecutive months per specification)
        from flask import current_app
        qualification_period = current_app.config.get('QUALIFICATION_PERIOD', 5)
        self.qualified_for_benefits = self.consecutive_months_paid >= qualification_period

    def is_active(self):
        """Check if member is active"""
        return self.status == 'Active'

    def is_qualified(self):
        """Check if member qualifies for benefits"""
        return self.qualified_for_benefits and self.status == 'Active'


class NextOfKin(db.Model):
    """
    Next of Kin information
    Only accessible to Executive members
    """
    __tablename__ = 'next_of_kin'

    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('members.id'), nullable=False)
    kin_type = db.Column(db.String(20), nullable=False)  # Primary, Alternative
    full_name = db.Column(db.String(100), nullable=False)
    relationship = db.Column(db.String(50), nullable=False)
    national_id = db.Column(db.String(20))
    date_of_birth = db.Column(db.Date)
    phone_primary = db.Column(db.String(20), nullable=False)
    phone_secondary = db.Column(db.String(20))
    email = db.Column(db.String(100))
    physical_address = db.Column(db.Text)
    distribution_percentage = db.Column(db.Integer, default=100)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<NextOfKin {self.full_name} ({self.kin_type})>'


# Event listener to auto-generate member number
@event.listens_for(Member, 'before_insert')
def generate_member_number(mapper, connection, target):
    """Auto-generate member number if not provided"""
    if not target.member_number:
        # Get the highest member number
        result = connection.execute(
            db.select(db.func.max(Member.member_number))
        ).scalar()

        if result:
            # Extract number and increment
            last_num = int(result.split('-')[1])
            new_num = last_num + 1
        else:
            new_num = 1

        target.member_number = f'OT-{new_num:03d}'
