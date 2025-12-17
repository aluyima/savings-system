"""
Contribution and Receipt Models
Tracks member contributions and generates receipts
"""
from app import db
from datetime import datetime
from sqlalchemy import event, UniqueConstraint


class Contribution(db.Model):
    """
    Contribution table
    Tracks all member contributions (multiple contributions per month allowed)
    """
    __tablename__ = 'contributions'

    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('members.id'), nullable=False)
    amount = db.Column(db.Numeric(15, 2), nullable=False)
    payment_date = db.Column(db.Date, nullable=False)
    contribution_month = db.Column(db.String(7), nullable=False)  # YYYY-MM
    payment_method = db.Column(db.String(20), nullable=False)  # Cash, MobileMoney, BankTransfer
    transaction_reference = db.Column(db.String(50))
    notes = db.Column(db.Text)
    proof_of_payment_path = db.Column(db.String(255))
    receipt_number = db.Column(db.String(20), unique=True)
    recorded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    recorder = db.relationship('User', foreign_keys=[recorded_by])
    receipt = db.relationship('Receipt', backref='contribution', uselist=False)

    def __repr__(self):
        return f'<Contribution {self.member.member_number} - {self.contribution_month}>'


class Receipt(db.Model):
    """
    Receipt table
    Stores generated receipt information
    """
    __tablename__ = 'receipts'

    id = db.Column(db.Integer, primary_key=True)
    receipt_number = db.Column(db.String(20), unique=True, nullable=False)
    contribution_id = db.Column(db.Integer, db.ForeignKey('contributions.id'))
    receipt_type = db.Column(db.String(20), nullable=False)  # Contribution, MembershipFee, LoanRepayment
    member_id = db.Column(db.Integer, db.ForeignKey('members.id'), nullable=False)
    amount = db.Column(db.Numeric(15, 2), nullable=False)
    payment_date = db.Column(db.Date, nullable=False)
    payment_method = db.Column(db.String(20), nullable=False)
    transaction_reference = db.Column(db.String(50))
    description = db.Column(db.Text)
    pdf_path = db.Column(db.String(255))
    generated_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    member = db.relationship('Member')
    generator = db.relationship('User', foreign_keys=[generated_by])

    def __repr__(self):
        return f'<Receipt {self.receipt_number}>'


# Event listener to auto-generate receipt number for contributions
@event.listens_for(Contribution, 'before_insert')
def generate_receipt_number(mapper, connection, target):
    """Auto-generate receipt number if not provided"""
    if not target.receipt_number:
        from datetime import date
        today = date.today()
        year = today.year
        month = today.month

        # Format: OT-YYYY-MM-NNNN
        prefix = f'OT-{year}-{month:02d}-'

        # Get the highest receipt number for this month
        result = connection.execute(
            db.select(db.func.max(Contribution.receipt_number)).where(
                Contribution.receipt_number.like(f'{prefix}%')
            )
        ).scalar()

        if result:
            last_num = int(result.split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1

        target.receipt_number = f'{prefix}{new_num:04d}'
