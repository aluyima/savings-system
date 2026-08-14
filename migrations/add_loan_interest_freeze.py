"""
Database Migration: Add interest-freeze fields to the Loans Table

Adds columns that let a SuperAdmin freeze interest accrual on a running loan.
When a loan is frozen, the daily overdue auto-extension job skips it, so no
further monthly interest is added and its due date stops advancing.

Columns added:
    interest_frozen         BOOLEAN  (default 0)
    interest_frozen_date    DATETIME
    interest_frozen_by      INTEGER  (FK users.id)
    interest_frozen_reason  TEXT

Usage:
    python migrations/add_loan_interest_freeze.py --auto   # Run without confirmation
    python migrations/add_loan_interest_freeze.py          # Interactive mode

Safe to run multiple times (idempotent - skips columns that already exist).
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from sqlalchemy import text

# column name -> SQLite column definition
NEW_COLUMNS = [
    ('interest_frozen', 'BOOLEAN DEFAULT 0'),
    ('interest_frozen_date', 'DATETIME'),
    ('interest_frozen_by', 'INTEGER'),
    ('interest_frozen_reason', 'TEXT'),
]


def migrate(auto_confirm=False):
    """Add interest-freeze columns to the loans table"""
    app = create_app()

    with app.app_context():
        print("=" * 60)
        print("LOAN INTEREST FREEZE MIGRATION")
        print("=" * 60)
        print("\nThis migration will add the following columns to 'loans':")
        for name, coltype in NEW_COLUMNS:
            print(f"  - {name} ({coltype})")
        print("\nThis is SAFE to run multiple times (idempotent)")
        print("=" * 60)

        if not auto_confirm:
            response = input("\nProceed with migration? (yes/no): ").strip().lower()
            if response != 'yes':
                print("Migration cancelled.")
                return
        else:
            print("\nRunning in auto-confirm mode...")

        try:
            result = db.session.execute(text("PRAGMA table_info(loans)"))
            existing = {row[1] for row in result.fetchall()}

            added = 0
            for name, coltype in NEW_COLUMNS:
                if name in existing:
                    print(f"✓ Column '{name}' already exists. Skipping.")
                    continue
                print(f"→ Adding '{name}'...")
                db.session.execute(text(f"ALTER TABLE loans ADD COLUMN {name} {coltype}"))
                added += 1

            db.session.commit()

            print("\n" + "=" * 60)
            print(f"MIGRATION COMPLETED SUCCESSFULLY! ({added} column(s) added)")
            print("=" * 60)

        except Exception as e:
            db.session.rollback()
            print(f"\n✗ Error during migration: {str(e)}")
            print("Migration failed. Database rolled back.")
            raise


if __name__ == '__main__':
    auto_confirm = '--auto' in sys.argv or '-y' in sys.argv
    migrate(auto_confirm=auto_confirm)
