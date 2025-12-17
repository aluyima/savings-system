"""
Operational Expense Model
Handles operational expenses like stationery, airtime, transport, etc.
"""
from app import db
from datetime import datetime


class Expense(db.Model):
    """
    Expense table
    Tracks operational expenses
    """
    __tablename__ = 'expenses'

    id = db.Column(db.Integer, primary_key=True)
    expense_number = db.Column(db.String(20), unique=True, nullable=False, index=True)
    expense_category = db.Column(db.String(50), nullable=False)  # Stationery, Airtime, Transport, Meetings, Other
    description = db.Column(db.Text, nullable=False)
    amount = db.Column(db.Numeric(15, 2), nullable=False)
    expense_date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    payment_method = db.Column(db.String(50))  # Cash, Mobile Money, Bank Transfer
    reference_number = db.Column(db.String(100))  # Receipt/transaction reference
    payee = db.Column(db.String(200))  # Person/organization paid
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    recorded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    receipt_document_path = db.Column(db.String(255))  # Path to uploaded receipt
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    approver = db.relationship('User', foreign_keys=[approved_by], backref='expenses_approved')
    recorder = db.relationship('User', foreign_keys=[recorded_by], backref='expenses_recorded')

    def __repr__(self):
        return f'<Expense {self.expense_number} - {self.expense_category}>'

    @staticmethod
    def generate_expense_number():
        """Generate unique expense number"""
        from datetime import date
        today = date.today()
        prefix = f"EXP{today.strftime('%Y%m')}"

        # Get the last expense number for this month
        last_expense = Expense.query.filter(
            Expense.expense_number.like(f"{prefix}%")
        ).order_by(Expense.expense_number.desc()).first()

        if last_expense:
            # Extract the sequence number and increment
            last_seq = int(last_expense.expense_number[-4:])
            new_seq = last_seq + 1
        else:
            new_seq = 1

        return f"{prefix}{new_seq:04d}"
