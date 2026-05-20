-- Update disbursement_method column size from VARCHAR(20) to VARCHAR(50)
-- SQLite doesn't support ALTER COLUMN, so we need to recreate the table

BEGIN TRANSACTION;

-- Create temporary table with new schema
CREATE TABLE loans_new (
	id INTEGER NOT NULL,
	loan_number VARCHAR(20) NOT NULL,
	member_id INTEGER NOT NULL,
	amount_requested NUMERIC(15, 2) NOT NULL,
	amount_approved NUMERIC(15, 2),
	purpose TEXT NOT NULL,
	repayment_period_months INTEGER NOT NULL,
	interest_rate NUMERIC(5, 2) NOT NULL,
	security_type VARCHAR(20) NOT NULL,
	collateral_description TEXT,
	collateral_value NUMERIC(15, 2),
	collateral_documents_path VARCHAR(255),
	guarantor1_id INTEGER,
	guarantor2_id INTEGER,
	guarantor1_approved BOOLEAN,
	guarantor2_approved BOOLEAN,
	executive_approved BOOLEAN,
	approved_by_chairman INTEGER,
	approved_by_secretary INTEGER,
	approved_by_treasurer INTEGER,
	approval_date DATE,
	approval_notes TEXT,
	disbursed BOOLEAN,
	disbursement_date DATE,
	disbursement_method VARCHAR(50),
	disbursement_reference VARCHAR(50),
	disbursement_document_path VARCHAR(255),
	total_payable NUMERIC(15, 2),
	total_paid NUMERIC(15, 2),
	balance NUMERIC(15, 2),
	status VARCHAR(20),
	default_date DATE,
	recovery_notes TEXT,
	created_at DATETIME,
	updated_at DATETIME,
	PRIMARY KEY (id),
	UNIQUE (loan_number),
	FOREIGN KEY(member_id) REFERENCES members (id),
	FOREIGN KEY(guarantor1_id) REFERENCES members (id),
	FOREIGN KEY(guarantor2_id) REFERENCES members (id),
	FOREIGN KEY(approved_by_chairman) REFERENCES users (id),
	FOREIGN KEY(approved_by_secretary) REFERENCES users (id),
	FOREIGN KEY(approved_by_treasurer) REFERENCES users (id)
);

-- Copy data from old table to new table
INSERT INTO loans_new SELECT
	id, loan_number, member_id, amount_requested, amount_approved, purpose,
	repayment_period_months, interest_rate, security_type, collateral_description,
	collateral_value, collateral_documents_path, guarantor1_id, guarantor2_id,
	guarantor1_approved, guarantor2_approved, executive_approved, approved_by_chairman,
	approved_by_secretary, approved_by_treasurer, approval_date, approval_notes,
	disbursed, disbursement_date, disbursement_method, disbursement_reference,
	disbursement_document_path, total_payable, total_paid, balance, status,
	default_date, recovery_notes, created_at, updated_at
FROM loans;

-- Drop old table
DROP TABLE loans;

-- Rename new table to loans
ALTER TABLE loans_new RENAME TO loans;

COMMIT;
