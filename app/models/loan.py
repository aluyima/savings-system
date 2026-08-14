"""
Loan and Loan Repayment Models
Handles loan applications, approvals, and repayments
"""
from app import db
from datetime import datetime, date


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

    # Loan application fee (paid into the bank, recorded manually by an executive).
    # Separate from the loan repayment - not included in total_payable.
    application_fee_amount = db.Column(db.Numeric(15, 2))
    application_fee_paid = db.Column(db.Boolean, default=False)
    application_fee_date = db.Column(db.Date)
    application_fee_reference = db.Column(db.String(50))  # Bank deposit reference
    application_fee_recorded_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    application_fee_notes = db.Column(db.Text)

    # Interest freeze (SuperAdmin only). When frozen, the daily overdue
    # auto-extension job skips this loan, so no further monthly interest is added
    # and the due date stops advancing. Everything else (overdue display,
    # reminders, repayments) is unaffected.
    interest_frozen = db.Column(db.Boolean, default=False)
    interest_frozen_date = db.Column(db.DateTime)
    interest_frozen_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    interest_frozen_reason = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    guarantor1 = db.relationship('Member', foreign_keys=[guarantor1_id], overlaps="loans_guaranteed1")
    guarantor2 = db.relationship('Member', foreign_keys=[guarantor2_id], overlaps="loans_guaranteed2")
    chairman = db.relationship('User', foreign_keys=[approved_by_chairman])
    secretary = db.relationship('User', foreign_keys=[approved_by_secretary])
    treasurer = db.relationship('User', foreign_keys=[approved_by_treasurer])
    application_fee_recorder = db.relationship('User', foreign_keys=[application_fee_recorded_by])
    interest_frozen_by_user = db.relationship('User', foreign_keys=[interest_frozen_by])
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

    def can_be_deleted(self):
        """Whether this application may be deleted by an administrator.

        Deletion is only permitted before the executive approves the loan, and a
        loan that has been disbursed can never be deleted. In addition, a
        guarantor-backed loan cannot be deleted once both guarantors have approved
        (it has been guaranteed). Collateral-backed loans may be deleted any time
        before executive approval.
        """
        # Once approved by the executive or disbursed, the loan is part of the record
        if self.executive_approved or self.disbursed:
            return False
        if self.status in ['Approved', 'Disbursed', 'Active', 'Completed', 'Defaulted']:
            return False
        # Guarantor-backed loans cannot be deleted once they have been guaranteed
        if self.security_type == 'Guarantors' and self.both_guarantors_approved():
            return False
        return True

    def recompute_payable(self):
        """Recalculate total payable, balance, due date and status from the current
        principal, interest rate and repayment period, accounting for payments made.

        Used when an executive adjusts (e.g. shortens) the repayment period so that
        a borrower who repays early is only charged interest for the shorter period.
        """
        if self.amount_approved is None or self.interest_rate is None:
            return
        principal = float(self.amount_approved)
        rate = float(self.interest_rate) / 100  # monthly rate as a decimal
        self.total_payable = principal + (principal * rate * self.repayment_period_months)
        paid = float(self.total_paid or 0)
        self.balance = float(self.total_payable) - paid
        # Keep due date in step with the (new) period for disbursed loans
        if self.disbursement_date:
            from dateutil.relativedelta import relativedelta
            self.due_date = self.disbursement_date + relativedelta(months=self.repayment_period_months)
        # An early payoff may already cover the reduced balance
        if self.status in ['Active', 'Disbursed'] and self.balance <= 0:
            self.status = 'Completed'

    def recompute_from_repayments(self):
        """Recalculate total_paid, balance and status from the repayment rows that
        currently exist, rather than by adjusting the running totals.

        Used when a repayment is reversed (deleted) by an administrator, so the
        denormalized tracking fields can never drift away from the LoanRepayment
        records that back them. Recomputing from source also self-corrects a total
        that had already drifted.

        Caller must flush a pending delete before calling this, so the removed row
        is excluded from the sum. Returns the new balance (None if the loan has no
        total_payable yet, i.e. it was never approved).
        """
        paid = sum(float(r.amount_paid or 0) for r in self.repayments)
        self.total_paid = paid

        if self.total_payable is None:
            return None

        self.balance = float(self.total_payable) - paid
        # Reversing a payment can re-open a loan that the payment had closed.
        # 'Defaulted' is a separate business decision and is deliberately left alone.
        if self.status == 'Completed' and self.balance > 0:
            self.status = 'Active'
        return self.balance

    def extend_one_month(self):
        """Extend the repayment period by one month, adding one month's interest on
        the principal and pushing the due date out a month.

        Used by the automatic overdue-extension job. Returns the interest added.
        """
        from dateutil.relativedelta import relativedelta
        principal = float(self.amount_approved or 0)
        rate = float(self.interest_rate or 0) / 100
        added_interest = principal * rate
        self.repayment_period_months = (self.repayment_period_months or 0) + 1
        self.total_payable = float(self.total_payable or 0) + added_interest
        self.balance = float(self.balance or 0) + added_interest
        if self.due_date:
            self.due_date = self.due_date + relativedelta(months=1)
        return added_interest

    def months_since_disbursement(self):
        """Whole calendar months the loan has been running since disbursement.

        Returns 0 if the loan has not been disbursed.
        """
        if not self.disbursement_date:
            return 0
        from dateutil.relativedelta import relativedelta
        today = date.today()
        if today <= self.disbursement_date:
            return 0
        return relativedelta(today, self.disbursement_date).months + \
            12 * relativedelta(today, self.disbursement_date).years

    def can_freeze_interest(self):
        """Whether an administrator may freeze interest accrual on this loan.

        Permitted only for a live loan that is still accruing (Active/Disbursed
        with a balance), is not already frozen, and has been running for at least
        one month since disbursement - the freeze is meant for loans that have
        already had time to run, not brand-new disbursements.
        """
        if self.interest_frozen:
            return False
        if self.status not in ['Active', 'Disbursed']:
            return False
        if float(self.balance or 0) <= 0:
            return False
        return self.months_since_disbursement() >= 1


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
