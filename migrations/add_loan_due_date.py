"""
Database Migration: Add due_date to Loans Table
Adds due_date field to track loan repayment deadline

Usage:
    python migrations/add_loan_due_date.py --auto    # Run without confirmation
    python migrations/add_loan_due_date.py           # Interactive mode
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from sqlalchemy import text

def migrate(auto_confirm=False):
    """Add due_date column to loans table"""
    app = create_app()

    with app.app_context():
        print("=" * 60)
        print("LOAN DUE DATE MIGRATION")
        print("=" * 60)
        print("\nThis migration will:")
        print("1. Add 'due_date' column to loans table")
        print("2. Calculate due dates for existing disbursed loans")
        print("\nThis is SAFE to run multiple times (idempotent)")
        print("=" * 60)

        if not auto_confirm:
            response = input("\nProceed with migration? (yes/no): ").strip().lower()
            if response != 'yes':
                print("Migration cancelled.")
                return
        else:
            print("\nRunning in auto-confirm mode...")
            print("Proceeding with migration...")

        try:
            # Check if column already exists
            result = db.session.execute(text("PRAGMA table_info(loans)"))
            columns = [row[1] for row in result.fetchall()]

            if 'due_date' in columns:
                print("\n✓ Column 'due_date' already exists. Skipping column creation.")
            else:
                print("\n→ Adding 'due_date' column to loans table...")
                db.session.execute(text(
                    "ALTER TABLE loans ADD COLUMN due_date DATE"
                ))
                db.session.commit()
                print("✓ Column 'due_date' added successfully!")

            # Update due dates for existing disbursed loans
            print("\n→ Calculating due dates for existing disbursed loans...")

            from app.models.loan import Loan
            from datetime import timedelta
            from dateutil.relativedelta import relativedelta

            disbursed_loans = Loan.query.filter(
                Loan.disbursed == True,
                Loan.disbursement_date.isnot(None)
            ).all()

            updated_count = 0
            for loan in disbursed_loans:
                if loan.due_date is None and loan.disbursement_date:
                    # Calculate due date: disbursement_date + repayment_period_months
                    loan.due_date = loan.disbursement_date + relativedelta(months=loan.repayment_period_months)
                    updated_count += 1

            if updated_count > 0:
                db.session.commit()
                print(f"✓ Updated due dates for {updated_count} existing loan(s)")
            else:
                print("✓ No existing loans needed due date updates")

            print("\n" + "=" * 60)
            print("MIGRATION COMPLETED SUCCESSFULLY!")
            print("=" * 60)
            print("\nNext steps:")
            print("1. Review loan due dates in the system")
            print("2. Set up the daily notification task scheduler")
            print("3. Test notification sending")

        except Exception as e:
            db.session.rollback()
            print(f"\n✗ Error during migration: {str(e)}")
            print("Migration failed. Database rolled back.")
            raise

if __name__ == '__main__':
    # Check for --auto flag
    auto_confirm = '--auto' in sys.argv or '-y' in sys.argv
    migrate(auto_confirm=auto_confirm)
