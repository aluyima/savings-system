#!/usr/bin/env python3
"""
Database Migration Script: Delete Specific Member Contributions
================================================================

Purpose: Safely delete specific contributions for a member from the live environment

This script will:
1. Find the member by member number (e.g., OT-004)
2. Find contributions matching the specified payment dates
3. Show detailed information about what will be deleted
4. Create a backup log of deleted records
5. Delete the contributions and their associated receipts
6. Update member's total_contributed amount

Usage:
    python migrations/delete_member_contributions.py OT-004 "2026-03-09" "2026-04-03"
    python migrations/delete_member_contributions.py OT-004 "2026-03-09" "2026-04-03" --auto
    python migrations/delete_member_contributions.py --help

Date Format: YYYY-MM-DD

Author: Migration Script
Date: 2026-05-05
"""

import sys
import os
from datetime import datetime
from decimal import Decimal

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models.member import Member
from app.models.contribution import Contribution, Receipt
from sqlalchemy import text


def show_help():
    """Display help information"""
    print(__doc__)
    sys.exit(0)


def parse_date(date_str):
    """Parse and validate date string"""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        print(f"\n✗ Error: Invalid date format '{date_str}'")
        print("Please use format: YYYY-MM-DD (e.g., 2026-03-09)")
        sys.exit(1)


def show_member_contributions(member_number, payment_dates):
    """Show all contributions for this member and highlight the ones to be deleted"""
    app = create_app()

    with app.app_context():
        # Find member
        member = Member.query.filter_by(member_number=member_number).first()
        if not member:
            print(f"\n✗ Error: Member '{member_number}' not found in system")
            sys.exit(1)

        print("\n" + "="*90)
        print("MEMBER INFORMATION")
        print("="*90)
        print(f"Member Number: {member.member_number}")
        print(f"Name: {member.full_name}")
        print(f"Status: {member.status}")
        print(f"Total Contributed (Current): UGX {member.total_contributed:,.2f}")
        print(f"Phone: {member.phone_primary}")

        # Get all contributions for this member
        all_contributions = Contribution.query.filter_by(
            member_id=member.id
        ).order_by(Contribution.payment_date.desc()).all()

        if not all_contributions:
            print(f"\n✗ No contributions found for {member.member_number}")
            return member, []

        # Find contributions matching the payment dates
        contributions_to_delete = []
        for contrib in all_contributions:
            if contrib.payment_date in payment_dates:
                contributions_to_delete.append(contrib)

        if not contributions_to_delete:
            print(f"\n✗ No contributions found for the specified dates")
            print(f"\nAvailable contributions for {member.member_number}:")
            print(f"\n{'Receipt #':<15} {'Payment Date':<15} {'Contribution Month':<18} {'Amount':<15}")
            print("-" * 90)
            for contrib in all_contributions[:20]:  # Show last 20
                print(f"{contrib.receipt_number:<15} {contrib.payment_date} {contrib.contribution_month:<18} UGX {contrib.amount:>13,.2f}")
            return member, []

        print(f"\n" + "="*90)
        print("CONTRIBUTIONS TO BE DELETED")
        print("="*90)
        print(f"\nFound {len(contributions_to_delete)} contribution(s) to delete:\n")

        total_amount_to_delete = Decimal('0')
        print(f"{'Receipt #':<15} {'Payment Date':<15} {'Contribution Month':<18} {'Amount':<15}")
        print("-" * 90)

        for contrib in contributions_to_delete:
            print(f"{contrib.receipt_number:<15} {contrib.payment_date} {contrib.contribution_month:<18} UGX {contrib.amount:>13,.2f}")
            total_amount_to_delete += contrib.amount

        print("\n" + "="*90)
        print("SUMMARY")
        print("="*90)
        print(f"\nTotal contributions to delete: {len(contributions_to_delete)}")
        print(f"Total amount to be removed: UGX {total_amount_to_delete:,.2f}")
        print(f"New total_contributed after deletion: UGX {member.total_contributed - total_amount_to_delete:,.2f}")

        return member, contributions_to_delete


def create_backup_log(member, contributions_deleted):
    """Create a backup log of deleted contributions"""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_filename = f"delete_contributions_{member.member_number}_{timestamp}.log"
    log_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'migrations',
        log_filename
    )

    total_amount = Decimal('0')
    with open(log_path, 'w') as f:
        f.write("DELETED CONTRIBUTIONS LOG\n")
        f.write("=" * 80 + "\n")
        f.write(f"Date: {datetime.now().isoformat()}\n")
        f.write(f"Member: {member.member_number} - {member.full_name}\n")
        f.write(f"Total Contributions Deleted: {len(contributions_deleted)}\n")
        f.write("=" * 80 + "\n\n")

        for contrib in contributions_deleted:
            f.write(f"Receipt Number: {contrib.receipt_number}\n")
            f.write(f"  Payment Date: {contrib.payment_date}\n")
            f.write(f"  Contribution Month: {contrib.contribution_month}\n")
            f.write(f"  Amount: UGX {contrib.amount:,.2f}\n")
            f.write(f"  Payment Method: {contrib.payment_method}\n")
            f.write(f"  Transaction Reference: {contrib.transaction_reference}\n")
            f.write(f"  Notes: {contrib.notes}\n")
            f.write(f"  Recorded By: User ID {contrib.recorded_by}\n")
            f.write(f"  Created At: {contrib.created_at}\n\n")
            total_amount += contrib.amount

        f.write("=" * 80 + "\n")
        f.write(f"Total Amount Deleted: UGX {total_amount:,.2f}\n")

    return log_path


def migrate(auto_confirm=False, member_number=None, payment_dates=None):
    """
    Main migration function

    Args:
        auto_confirm (bool): If True, skip confirmation prompt
        member_number (str): Member number (e.g., OT-004)
        payment_dates (list): List of payment dates to delete
    """
    print("\n" + "="*90)
    print("DELETE MEMBER CONTRIBUTIONS")
    print("="*90)

    if not member_number or not payment_dates:
        print("\n✗ Error: Member number and payment dates are required")
        print("\nUsage: python migrations/delete_member_contributions.py OT-004 \"2026-03-09\" \"2026-04-03\"")
        sys.exit(1)

    # Parse dates
    parsed_dates = []
    for date_str in payment_dates:
        parsed_dates.append(parse_date(date_str))

    # Show what will be deleted
    member, contributions_to_delete = show_member_contributions(member_number, parsed_dates)

    if not contributions_to_delete:
        print("\n✗ No contributions matched. Exiting.")
        return

    # Confirm before proceeding
    if not auto_confirm:
        print("\n" + "="*90)
        response = input(f"\nProceed with DELETING {len(contributions_to_delete)} contribution(s)? (yes/no): ").strip().lower()
        if response not in ['yes', 'y']:
            print("\n✗ Deletion cancelled by user.")
            return
    else:
        print("\n→ Auto-confirm mode: Proceeding with deletion...")

    app = create_app()

    with app.app_context():
        try:
            print("\n→ Deleting contributions...")

            # Re-fetch member and contributions within the app context to avoid detached session errors
            member = Member.query.filter_by(member_number=member_number).first()
            if not member:
                print(f"\n✗ Error: Member '{member_number}' not found")
                return

            # Re-fetch contributions to delete by matching payment dates
            contributions_to_delete_fresh = Contribution.query.filter(
                Contribution.member_id == member.id,
                Contribution.payment_date.in_(payment_dates)
            ).all()

            if not contributions_to_delete_fresh:
                print(f"\n✗ No contributions found to delete")
                return

            total_amount_deleted = Decimal('0')

            # Delete contributions and update member
            for contrib in contributions_to_delete_fresh:
                # Delete associated receipt if it exists
                receipt = Receipt.query.filter_by(contribution_id=contrib.id).first()
                if receipt:
                    print(f"  ✓ Deleting receipt: {receipt.receipt_number}")
                    db.session.delete(receipt)

                print(f"  ✓ Deleting contribution: {contrib.receipt_number} (UGX {contrib.amount:,.2f})")
                total_amount_deleted += contrib.amount
                db.session.delete(contrib)

            # Update member's total_contributed
            member.total_contributed -= total_amount_deleted

            print(f"\n→ Updating member total_contributed...")
            print(f"  Previous: UGX {member.total_contributed + total_amount_deleted:,.2f}")
            print(f"  New: UGX {member.total_contributed:,.2f}")
            print(f"  Amount removed: UGX {total_amount_deleted:,.2f}")

            print(f"\n→ Committing changes to database...")
            db.session.commit()

            # Create backup log
            log_path = create_backup_log(member, contributions_to_delete_fresh)
            print(f"✓ Backup log created: {log_path}")

            print("\n" + "="*90)
            print("DELETION COMPLETED SUCCESSFULLY!")
            print("="*90)
            print(f"\nDeleted: {len(contributions_to_delete_fresh)} contribution(s)")
            print(f"Total amount removed: UGX {total_amount_deleted:,.2f}")
            print(f"Member '{member.member_number}' total_contributed updated")
            print(f"Log file: {log_path}")

        except Exception as e:
            db.session.rollback()
            print(f"\n✗ Error during deletion: {str(e)}")
            print("Deletion failed. Database rolled back.")
            import traceback
            traceback.print_exc()
            raise


if __name__ == '__main__':
    # Parse command line arguments
    if '--help' in sys.argv or '-h' in sys.argv:
        show_help()

    auto_confirm = '--auto' in sys.argv or '-y' in sys.argv

    # Extract arguments
    args = [arg for arg in sys.argv[1:] if arg not in ['--auto', '-y', '--help', '-h']]

    if len(args) < 2:
        print("Usage: python migrations/delete_member_contributions.py OT-004 \"2026-03-09\" \"2026-04-03\"")
        print("Use --help for more information")
        sys.exit(1)

    member_number = args[0]
    payment_dates = args[1:]

    migrate(auto_confirm=auto_confirm, member_number=member_number, payment_dates=payment_dates)
