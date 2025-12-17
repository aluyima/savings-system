"""
Loan and Loan Repayment Models
Handles loan applications, approvals, and repayments
"""
from app import db
from datetime import datetime


class Loan(db.Model):
    """
    Loan table
    Tracks loan applications and approvals
    """
    __tablename__ = 'loans'

    id = db.Column(db.Integer, primary_key=True)
    loan_number = db.Column(db.String(20), unique=True, nullable=False)  # LN-YYYY-NNN
    member_id = db.Column(db.Integer, db.ForeignKey('members.id'), nullable=False)
    amount_requested = db.Column(db.Numeric(15, 2), nullable=False)
    amount_approved = db.Column(db.Numeric(15, 2))
    purpose = db.Column(db.Text, nullable=False)
    repayment_period_months = db.Column(db.Integer, nullable=False)  # Max 2
    interest_rate = db.Column(db.Numeric(5, 2), nullable=False)  # 5.00%

    # Security
    security_type = db.Column(db.String(20), nullable=False)  # Collateral, Guarantors
    collateral_description = db.Column(db.Text)
    collateral_value = db.Column(db.Numeric(15, 2))
    collateral_documents_path = db.Column(db.String(255))
    guarantor1_id = db.Column(db.Integer, db.ForeignKey('members.id'))
    guarantor2_id = db.Column(db.Integer, db.ForeignKey('members.id'))
    guarantor1_approved = db.Column(db.Boolean)
    guarantor2_approved = db.Column(db.Boolean)
    guarantor1_approval_date = db.Column(db.DateTime)
    guarantor2_approval_date = db.Column(db.DateTime)
    guarantor1_rejection_reason = db.Column(db.Text)
    guarantor2_rejection_reason = db.Column(db.Text)

    # Executive approval (all 3 must approve)
    executive_approved = db.Column(db.Boolean, default=False)
    approved_by_chairman = db.Column(db.Integer, db.ForeignKey('users.id'))
    approved_by_secretary = db.Column(db.Integer, db.ForeignKey('users.id'))
    approved_by_treasurer = db.Column(db.Integer, db.ForeignKey('users.id'))
    approval_date = db.Column(db.Date)
    approval_notes = db.Column(db.Text)

    # Disbursement
    disbursed = db.Column(db.Boolean, default=False)
    disbursement_date = db.Column(db.Date)
    due_date = db.Column(db.Date)  # Calculated as disbursement_date + repayment_period_months
    disbursement_method = db.Column(db.String(50))
    disbursement_reference = db.Column(db.String(50))
    disbursement_document_path = db.Column(db.String(255))  # Path to withdrawal slip/receipt

    # Repayment tracking
    total_payable = db.Column(db.Numeric(15, 2))  # Principal + Interest
    total_paid = db.Column(db.Numeric(15, 2), default=0.00)
    balance = db.Column(db.Numeric(15, 2))
    status = db.Column(db.String(30), default='Pending Guarantor Approval')  # Pending Guarantor Approval, Returned to Applicant, Pending Executive Approval, Approved, Rejected, Disbursed, Active, Completed, Defaulted
    default_date = db.Column(db.Date)
    recovery_notes = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    guarantor1 = db.relationship('Member', foreign_keys=[guarantor1_id], overlaps="loans_guaranteed1")
    guarantor2 = db.relationship('Member', foreign_keys=[guarantor2_id], overlaps="loans_guaranteed2")
    chairman = db.relationship('User', foreign_keys=[approved_by_chairman])
    secretary = db.relationship('User', foreign_keys=[approved_by_secretary])
    treasurer = db.relationship('User', foreign_keys=[approved_by_treasurer])
    repayments = db.relationship('LoanRepayment', backref='loan', lazy='dynamic')

    def __repr__(self):
        return f'<Loan {self.loan_number}>'

    def calculate_total_payable(self):
        """Calculate total amount payable (principal + interest)

        Interest is calculated monthly at the specified rate.
        Formula: Total Interest = Principal × (Rate/100) × Months
        Example: UGX 300,000 at 5% monthly for 2 months = 300,000 + (300,000 × 0.05 × 2) = UGX 330,000
        """
        if self.amount_approved and self.interest_rate:
            principal = float(self.amount_approved)
            rate = float(self.interest_rate) / 100  # Convert percentage to decimal
            months = self.repayment_period_months
            # Calculate interest per month for total repayment period
            total_interest = principal * rate * months
            self.total_payable = principal + total_interest
            self.balance = self.total_payable
            return self.total_payable
        return 0

    def both_guarantors_approved(self):
        """Check if both guarantors have approved the loan"""
        if self.security_type != 'Guarantors':
            return True  # Not applicable for collateral loans
        return self.guarantor1_approved == True and self.guarantor2_approved == True

    def any_guarantor_rejected(self):
        """Check if any guarantor has rejected the loan"""
        if self.security_type != 'Guarantors':
            return False  # Not applicable for collateral loans
        return self.guarantor1_approved == False or self.guarantor2_approved == False

    def pending_guarantor_approval(self):
        """Check if loan is waiting for guarantor approval"""
        if self.security_type != 'Guarantors':
            return False  # Not applicable for collateral loans
        return (self.guarantor1_approved is None or self.guarantor2_approved is None) and not self.any_guarantor_rejected()


class LoanRepayment(db.Model):
    """
    Loan Repayment table
    Tracks individual loan repayments
    """
    __tablename__ = 'loan_repayments'

    id = db.Column(db.Integer, primary_key=True)
    loan_id = db.Column(db.Integer, db.ForeignKey('loans.id'), nullable=False)
    payment_date = db.Column(db.Date, nullable=False)
    amount_paid = db.Column(db.Numeric(15, 2), nullable=False)
    principal_portion = db.Column(db.Numeric(15, 2), nullable=False)
    interest_portion = db.Column(db.Numeric(15, 2), nullable=False)
    payment_method = db.Column(db.String(20), nullable=False)
    transaction_reference = db.Column(db.String(50))
    receipt_number = db.Column(db.String(20))
    recorded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    recorder = db.relationship('User', foreign_keys=[recorded_by])

    def __repr__(self):
        return f'<LoanRepayment {self.loan.loan_number} - {self.amount_paid}>'
