#!/usr/bin/env python3
"""
Database Migration Script: Fix Contribution Month
==================================================

Purpose: Correct wrongly entered contributions for month 2025-12 to 2025-09

Changes:
- Updates contribution_month from '2025-12' to '2025-09' for affected records

Author: Migration Script
Date: 2025-12-18
"""

import sys
import os

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models.contribution import Contribution
from sqlalchemy import text

def show_affected_records():
    """Display records that will be affected by this migration"""
    print("\n" + "="*80)
    print("RECORDS TO BE UPDATED")
    print("="*80)

    contributions = Contribution.query.filter_by(contribution_month='2025-12').all()

    if not contributions:
        print("\n⚠ No contributions found for month '2025-12'")
        return False

    print(f"\nFound {len(contributions)} contribution(s) for month '2025-12':\n")
    print(f"{'ID':<6} {'Member ID':<12} {'Amount':<15} {'Month':<12} {'Payment Date':<15}")
    print("-" * 80)

    for contrib in contributions:
        print(f"{contrib.id:<6} {contrib.member_id:<12} {contrib.amount:<15.2f} {contrib.contribution_month:<12} {contrib.payment_date}")

    print("\nThese records will be updated to contribution_month = '2025-09'")
    return True

def migrate(auto_confirm=False):
    """
    Main migration function

    Args:
        auto_confirm (bool): If True, skip confirmation prompt
    """
    print("\n" + "="*80)
    print("CONTRIBUTION MONTH CORRECTION MIGRATION")
    print("="*80)
    print("\nThis script will update contribution_month from '2025-12' to '2025-09'")
    print("for contributions that were wrongly entered.")

    # Show affected records
    has_records = show_affected_records()

    if not has_records:
        print("\n✓ No migration needed. Exiting.")
        return

    # Confirm before proceeding
    if not auto_confirm:
        print("\n" + "="*80)
        response = input("\nDo you want to proceed with this migration? (yes/no): ").strip().lower()
        if response not in ['yes', 'y']:
            print("\n✗ Migration cancelled by user.")
            return
    else:
        print("\n→ Auto-confirm mode: Proceeding with migration...")

    try:
        # Update the contribution month
        result = db.session.execute(
            text("UPDATE contributions SET contribution_month = '2025-09' WHERE contribution_month = '2025-12'")
        )

        # Commit the transaction
        db.session.commit()

        updated_count = result.rowcount

        print("\n" + "="*80)
        print("MIGRATION COMPLETED SUCCESSFULLY")
        print("="*80)
        print(f"\n✓ Updated {updated_count} contribution record(s)")
        print("✓ Contribution month changed from '2025-12' to '2025-09'")

        # Verify the changes
        print("\n" + "="*80)
        print("VERIFICATION - Updated Records")
        print("="*80)

        updated_contributions = Contribution.query.filter_by(contribution_month='2025-09').all()

        if updated_contributions:
            print(f"\nNow showing {len(updated_contributions)} contribution(s) for month '2025-09':\n")
            print(f"{'ID':<6} {'Member ID':<12} {'Amount':<15} {'Month':<12} {'Payment Date':<15}")
            print("-" * 80)

            for contrib in updated_contributions:
                print(f"{contrib.id:<6} {contrib.member_id:<12} {contrib.amount:<15.2f} {contrib.contribution_month:<12} {contrib.payment_date}")

        # Check if any records remain for 2025-12
        remaining = Contribution.query.filter_by(contribution_month='2025-12').count()

        if remaining == 0:
            print(f"\n✓ No contributions remaining for month '2025-12'")
        else:
            print(f"\n⚠ Warning: {remaining} contribution(s) still remain for month '2025-12'")

    except Exception as e:
        db.session.rollback()
        print("\n" + "="*80)
        print("MIGRATION FAILED")
        print("="*80)
        print(f"\n✗ Error during migration: {str(e)}")
        print("✗ Database rolled back. No changes were made.")
        raise

def rollback_migration():
    """Rollback function to revert changes if needed"""
    print("\n" + "="*80)
    print("ROLLBACK MIGRATION")
    print("="*80)
    print("\nThis will change contribution_month from '2025-09' back to '2025-12'")

    # Show records that would be affected
    contributions = Contribution.query.filter_by(contribution_month='2025-09').all()

    if not contributions:
        print("\n⚠ No contributions found for month '2025-09' to rollback")
        return

    print(f"\nFound {len(contributions)} contribution(s) for month '2025-09'")

    response = input("\nAre you sure you want to rollback? (yes/no): ").strip().lower()
    if response not in ['yes', 'y']:
        print("\n✗ Rollback cancelled.")
        return

    try:
        # Note: This rollback assumes ALL 2025-09 records should go back to 2025-12
        # In production, you might want to be more selective
        result = db.session.execute(
            text("UPDATE contributions SET contribution_month = '2025-12' WHERE contribution_month = '2025-09'")
        )

        db.session.commit()

        print(f"\n✓ Rolled back {result.rowcount} contribution record(s)")
        print("✓ Contribution month changed from '2025-09' back to '2025-12'")

    except Exception as e:
        db.session.rollback()
        print(f"\n✗ Error during rollback: {str(e)}")
        print("✗ Database rolled back.")
        raise

if __name__ == '__main__':
    # Create Flask app context
    app = create_app()

    with app.app_context():
        # Check for command line arguments
        auto_confirm = '--auto' in sys.argv or '-y' in sys.argv
        rollback = '--rollback' in sys.argv

        if rollback:
            rollback_migration()
        else:
            migrate(auto_confirm=auto_confirm)

        print("\n" + "="*80)
        print("Script completed.")
        print("="*80 + "\n")
