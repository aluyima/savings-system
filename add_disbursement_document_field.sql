-- Add disbursement_document_path field to loans table
-- This stores the path to the bank withdrawal slip/receipt

ALTER TABLE loans ADD COLUMN disbursement_document_path VARCHAR(255);
