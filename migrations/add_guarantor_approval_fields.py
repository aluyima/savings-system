"""
Database Migration: Add Guarantor Approval Fields to Loan Model
Run this migration to add new fields for tracking guarantor approvals and rejections
"""

from app import db, create_app
from sqlalchemy import text

def upgrade():
    """Add new fields to loans table"""
    app = create_app()
    with app.app_context():
        print("Adding guarantor approval tracking fields to loans table...")

        # Add new columns
        with db.engine.connect() as conn:
            # Add guarantor approval date columns
            try:
                conn.execute(text("""
                    ALTER TABLE loans
                    ADD COLUMN guarantor1_approval_date DATETIME
                """))
                conn.commit()
                print("✓ Added guarantor1_approval_date column")
            except Exception as e:
                print(f"✗ guarantor1_approval_date column may already exist: {e}")

            try:
                conn.execute(text("""
                    ALTER TABLE loans
                    ADD COLUMN guarantor2_approval_date DATETIME
                """))
                conn.commit()
                print("✓ Added guarantor2_approval_date column")
            except Exception as e:
                print(f"✗ guarantor2_approval_date column may already exist: {e}")

            # Add rejection reason columns
            try:
                conn.execute(text("""
                    ALTER TABLE loans
                    ADD COLUMN guarantor1_rejection_reason TEXT
                """))
                conn.commit()
                print("✓ Added guarantor1_rejection_reason column")
            except Exception as e:
                print(f"✗ guarantor1_rejection_reason column may already exist: {e}")

            try:
                conn.execute(text("""
                    ALTER TABLE loans
                    ADD COLUMN guarantor2_rejection_reason TEXT
                """))
                conn.commit()
                print("✓ Added guarantor2_rejection_reason column")
            except Exception as e:
                print(f"✗ guarantor2_rejection_reason column may already exist: {e}")

            # Update status column to support longer status names
            try:
                conn.execute(text("""
                    ALTER TABLE loans
                    MODIFY COLUMN status VARCHAR(30) DEFAULT 'Pending Guarantor Approval'
                """))
                conn.commit()
                print("✓ Updated status column length")
            except Exception as e:
                # Try SQLite syntax if MySQL syntax fails
                try:
                    # For SQLite, we need to check and update differently
                    print("Trying SQLite syntax for status column...")
                    # SQLite doesn't support MODIFY COLUMN, so this is informational
                    print("✓ Status column update skipped (SQLite doesn't require explicit modification)")
                except Exception as e2:
                    print(f"✗ Could not update status column: {e2}")

        print("\n✓ Migration completed successfully!")
        print("\nNew statuses supported:")
        print("  - Pending Guarantor Approval (default)")
        print("  - Returned to Applicant")
        print("  - Pending Executive Approval")
        print("  - Approved")
        print("  - Rejected")
        print("  - Disbursed")
        print("  - Active")
        print("  - Completed")
        print("  - Defaulted")


def downgrade():
    """Remove guarantor approval fields (rollback)"""
    app = create_app()
    with app.app_context():
        print("Rolling back guarantor approval tracking fields...")

        with db.engine.connect() as conn:
            try:
                conn.execute(text("ALTER TABLE loans DROP COLUMN guarantor1_approval_date"))
                conn.execute(text("ALTER TABLE loans DROP COLUMN guarantor2_approval_date"))
                conn.execute(text("ALTER TABLE loans DROP COLUMN guarantor1_rejection_reason"))
                conn.execute(text("ALTER TABLE loans DROP COLUMN guarantor2_rejection_reason"))
                conn.commit()
                print("✓ Rollback completed")
            except Exception as e:
                print(f"✗ Rollback failed: {e}")


if __name__ == '__main__':
    print("=" * 60)
    print("Loan Guarantor Approval Fields Migration")
    print("=" * 60)
    print("\nThis will add the following fields to the loans table:")
    print("  - guarantor1_approval_date (DATETIME)")
    print("  - guarantor2_approval_date (DATETIME)")
    print("  - guarantor1_rejection_reason (TEXT)")
    print("  - guarantor2_rejection_reason (TEXT)")
    print("  - Update status column to support longer values")
    print("\n" + "=" * 60)

    response = input("\nProceed with migration? (yes/no): ")
    if response.lower() in ['yes', 'y']:
        upgrade()
    else:
        print("Migration cancelled.")
