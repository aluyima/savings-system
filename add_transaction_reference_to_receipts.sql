-- Migration: Add transaction_reference field to receipts table
-- Run this SQL command in your SQLite database:
-- sqlite3 instance/oldtimerssavings.db < add_transaction_reference_to_receipts.sql

ALTER TABLE receipts ADD COLUMN transaction_reference VARCHAR(50);

-- Optional: Update existing receipts to have transaction reference from contributions
UPDATE receipts
SET transaction_reference = (
    SELECT c.transaction_reference
    FROM contributions c
    WHERE c.id = receipts.contribution_id
)
WHERE receipts.contribution_id IS NOT NULL;
