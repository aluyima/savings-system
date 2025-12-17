"""
Welfare Request and Payment Models
Handles bereavement, medical support, and celebrations
"""
from app import db
from datetime import datetime


class WelfareRequest(db.Model):
    """
    Welfare Request table
    Members submit requests for bereavement, medical, or celebration support
    """
    __tablename__ = 'welfare_requests'

    id = db.Column(db.Integer, primary_key=True)
    request_number = db.Column(db.String(20), unique=True, nullable=False)  # WR-YYYY-NNN
    member_id = db.Column(db.Integer, db.ForeignKey('members.id'), nullable=False)
    request_type = db.Column(db.String(20), nullable=False)  # Bereavement, Medical, Celebration
    affected_person = db.Column(db.String(100))
    relationship = db.Column(db.String(50))  # Spouse, Child, Parent
    incident_date = db.Column(db.Date, nullable=False)
    description = db.Column(db.Text, nullable=False)
    amount_requested = db.Column(db.Numeric(15, 2))
    documents_path = db.Column(db.String(255))

    # Status and workflow
    status = db.Column(db.String(20), default='Submitted')  # Submitted, UnderReview, Approved, Rejected, Paid
    submitted_date = db.Column(db.DateTime, default=datetime.utcnow)

    # Secretary review
    reviewed_by_secretary = db.Column(db.Integer, db.ForeignKey('users.id'))
    secretary_review_date = db.Column(db.DateTime)
    secretary_notes = db.Column(db.Text)

    # Chairman approval
    approved_by_chairman = db.Column(db.Integer, db.ForeignKey('users.id'))
    chairman_approval_date = db.Column(db.DateTime)
    chairman_notes = db.Column(db.Text)
    amount_approved = db.Column(db.Numeric(15, 2))
    rejection_reason = db.Column(db.Text)
    payment_voucher_number = db.Column(db.String(20))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    secretary = db.relationship('User', foreign_keys=[reviewed_by_secretary])
    chairman = db.relationship('User', foreign_keys=[approved_by_chairman])
    payment = db.relationship('WelfarePayment', backref='welfare_request', uselist=False)

    def __repr__(self):
        return f'<WelfareRequest {self.request_number} - {self.request_type}>'


class WelfarePayment(db.Model):
    """
    Welfare Payment table
    Tracks actual payments for approved welfare requests
    """
    __tablename__ = 'welfare_payments'

    id = db.Column(db.Integer, primary_key=True)
    welfare_request_id = db.Column(db.Integer, db.ForeignKey('welfare_requests.id'), nullable=False)
    payment_voucher_number = db.Column(db.String(20), unique=True, nullable=False)
    amount_paid = db.Column(db.Numeric(15, 2), nullable=False)
    payment_date = db.Column(db.Date, nullable=False)
    payment_method = db.Column(db.String(50), nullable=False)
    withdrawal_reference = db.Column(db.String(50))  # Bank withdrawal reference
    withdrawal_document_path = db.Column(db.String(255))  # Bank withdrawal slip
    transaction_reference = db.Column(db.String(50))
    beneficiary_name = db.Column(db.String(100), nullable=False)
    beneficiary_phone = db.Column(db.String(20))
    beneficiary_receipt_path = db.Column(db.String(255))  # Beneficiary proof of receipt

    # Dual authorization (Treasurer + Secretary)
    paid_by_treasurer = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    confirmed_by_secretary = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    treasurer = db.relationship('User', foreign_keys=[paid_by_treasurer])
    secretary = db.relationship('User', foreign_keys=[confirmed_by_secretary])

    def __repr__(self):
        return f'<WelfarePayment {self.payment_voucher_number}>'
