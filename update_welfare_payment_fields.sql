-- Update welfare_payments table to support bank withdrawal and beneficiary receipt uploads
-- Add withdrawal_reference, withdrawal_document_path, and beneficiary_receipt_path fields
-- Update payment_method column size and rename beneficiary_acknowledgment_path

BEGIN TRANSACTION;

-- Add new columns
ALTER TABLE welfare_payments ADD COLUMN withdrawal_reference VARCHAR(50);
ALTER TABLE welfare_payments ADD COLUMN withdrawal_document_path VARCHAR(255);
ALTER TABLE welfare_payments ADD COLUMN beneficiary_receipt_path VARCHAR(255);

-- Note: SQLite doesn't support ALTER COLUMN to rename or change type
-- If beneficiary_acknowledgment_path exists and needs to be renamed,
-- we would need to recreate the table. For now, we'll keep both columns.

COMMIT;
