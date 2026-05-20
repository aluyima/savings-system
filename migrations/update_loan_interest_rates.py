#!/usr/bin/env python3
"""
Database Migration Script: Update Loan Interest Rates
======================================================

Purpose: Update interest rates for existing loans and recalculate total payable amounts

This migration will:
1. Update interest_rate for active/pending loans
2. Recalculate total_payable for affected loans
3. Create a backup log of changes
4. Skip loans that are already completed or defaulted

Usage:
    python migrations/update_loan_interest_rates.py 3.50              # Update to 3.50%
    python migrations/update_loan_interest_rates.py 3.50 --auto       # Auto-confirm
    python migrations/update_loan_interest_rates.py 3.50 -y           # Auto-confirm (short form)
    python migrations/update_loan_interest_rates.py --help            # Show help

Loan statuses that will be updated:
- Pending Guarantor Approval
- Returned to Applicant
- Pending Executive Approval
- Approved
- Disbursed
- Active

Loan statuses that will NOT be updated (already finalized):
- Completed
- Defaulted
- Rejected

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
from app.models.loan import Loan
from sqlalchemy import text


def show_help():
    """Display help information"""
    print(__doc__)
    sys.exit(0)


def validate_rate(rate_str):
    """Validate and convert interest rate"""
    try:
        rate = float(rate_str)
        if rate < 0 or rate > 100:
            print(f"\n✗ Error: Interest rate must be between 0 and 100. Got: {rate}")
            sys.exit(1)
        return Decimal(str(rate))
    except ValueError:
        print(f"\n✗ Error: Invalid interest rate '{rate_str}'. Must be a number.")
        sys.exit(1)


def show_affected_records(new_rate):
    """Display records that will be affected by this migration"""
    print("\n" + "="*80)
    print("LOANS TO BE UPDATED")
    print("="*80)

    # Statuses that should be updated (not finalized)
    updatable_statuses = [
        'Pending Guarantor Approval',
        'Returned to Applicant',
        'Pending Executive Approval',
        'Approved',
        'Disbursed',
        'Active'
    ]

    loans = Loan.query.filter(
        Loan.status.in_(updatable_statuses)
    ).order_by(Loan.loan_number).all()

    if not loans:
        print(f"\n⚠ No loans found with updatable statuses")
        return loans, 0

    print(f"\nFound {len(loans)} loan(s) to update:\n")
    print(f"{'Loan #':<15} {'Member':<10} {'Principal':<15} {'Current Rate':<14} {'New Rate':<12} {'Status':<25}")
    print("-" * 80)

    current_rate_sum = Decimal('0')
    new_rate_sum = Decimal('0')

    for loan in loans:
        # Only show loans where rate is different
        if loan.interest_rate != new_rate:
            member = f"ID:{loan.member_id}"
            current_rate = float(loan.interest_rate) if loan.interest_rate else 0
            new_rate_f = float(new_rate)
            principal = loan.amount_approved or loan.amount_requested
            
            print(f"{loan.loan_number:<15} {member:<10} {principal:<15.2f} {current_rate:<14.2f}% {new_rate_f:<12.2f}% {loan.status:<25}")
            current_rate_sum += loan.interest_rate or Decimal('0')
            new_rate_sum += new_rate

    print("\n" + "="*80)
    print("SUMMARY OF CHANGES")
    print("="*80)
    
    loans_to_update = [l for l in loans if l.interest_rate != new_rate]
    print(f"\nTotal loans to update: {len(loans_to_update)}")
    print(f"Current average rate: {float(current_rate_sum / len(loans_to_update)) if loans_to_update else 0:.2f}%")
    print(f"New average rate: {float(new_rate_sum / len(loans_to_update)) if loans_to_update else 0:.2f}%")
    
    return loans, len(loans_to_update)


def create_backup_log(loans_updated, new_rate):
    """Create a backup log of all changes"""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_filename = f"loan_interest_rate_update_{timestamp}.log"
    log_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'migrations',
        log_filename
    )

    with open(log_path, 'w') as f:
        f.write("LOAN INTEREST RATE UPDATE LOG\n")
        f.write("=" * 80 + "\n")
        f.write(f"Date: {datetime.now().isoformat()}\n")
        f.write(f"New Interest Rate: {new_rate}%\n")
        f.write("=" * 80 + "\n\n")

        for loan in loans_updated:
            f.write(f"Loan Number: {loan.loan_number}\n")
            f.write(f"  Member ID: {loan.member_id}\n")
            f.write(f"  Previous Rate: {loan.interest_rate}%\n")
            f.write(f"  New Rate: {new_rate}%\n")
            f.write(f"  Amount Approved: {loan.amount_approved}\n")
            f.write(f"  Repayment Period: {loan.repayment_period_months} months\n")
            f.write(f"  Status: {loan.status}\n")
            f.write(f"  Previous Total Payable: {loan.total_payable}\n")
            f.write(f"  New Total Payable: {loan.total_payable}\n")  # Will be recalculated
            f.write("\n")

    return log_path


def migrate(auto_confirm=False, new_rate=None):
    """
    Main migration function

    Args:
        auto_confirm (bool): If True, skip confirmation prompt
        new_rate (Decimal): New interest rate to apply
    """
    print("\n" + "="*80)
    print("LOAN INTEREST RATE UPDATE MIGRATION")
    print("="*80)

    if new_rate is None:
        print("\n✗ Error: Interest rate not provided")
        print("\nUsage: python migrations/update_loan_interest_rates.py <new_rate> [--auto]")
        print("Example: python migrations/update_loan_interest_rates.py 3.50")
        sys.exit(1)

    print(f"\nThis script will update all active loans to {float(new_rate):.2f}% interest rate")
    print("and recalculate their total payable amounts.")

    app = create_app()

    with app.app_context():
        # Show affected records
        loans, count = show_affected_records(new_rate)

        if count == 0:
            print("\n✓ No loans need updating. Exiting.")
            return

        # Confirm before proceeding
        if not auto_confirm:
            print("\n" + "="*80)
            response = input(f"\nProceed with updating {count} loan(s)? (yes/no): ").strip().lower()
            if response not in ['yes', 'y']:
                print("\n✗ Migration cancelled by user.")
                return
        else:
            print("\n→ Auto-confirm mode: Proceeding with migration...")

        try:
            print("\n→ Updating interest rates and recalculating totals...")

            # Get loans to update
            updatable_statuses = [
                'Pending Guarantor Approval',
                'Returned to Applicant',
                'Pending Executive Approval',
                'Approved',
                'Disbursed',
                'Active'
            ]

            loans_to_update = Loan.query.filter(
                Loan.status.in_(updatable_statuses)
            ).all()

            updated_count = 0
            for loan in loans_to_update:
                if loan.interest_rate != new_rate:
                    old_rate = loan.interest_rate
                    loan.interest_rate = new_rate
                    
                    # Recalculate total payable
                    if loan.amount_approved:
                        loan.calculate_total_payable()
                    
                    updated_count += 1
                    print(f"  ✓ {loan.loan_number}: {old_rate}% → {new_rate}% (Total Payable: {loan.total_payable})")

            if updated_count > 0:
                print(f"\n→ Committing {updated_count} updates to database...")
                db.session.commit()

                # Create backup log
                log_path = create_backup_log(
                    [l for l in loans_to_update if l.interest_rate == new_rate],
                    new_rate
                )
                print(f"✓ Backup log created: {log_path}")

                print("\n" + "="*80)
                print("MIGRATION COMPLETED SUCCESSFULLY!")
                print("="*80)
                print(f"\nUpdated: {updated_count} loan(s)")
                print(f"Interest rate: {float(new_rate):.2f}%")
                print(f"Log file: {log_path}")
                print("\nNext steps:")
                print("1. Review the updated loans in the system")
                print("2. Verify calculations in loan statements")
                print("3. If deploying to PythonAnywhere:")
                print("   - Update .env with new LOAN_INTEREST_RATE")
                print("   - Reload the web app")
            else:
                print("\n✓ No loans needed updating")

        except Exception as e:
            db.session.rollback()
            print(f"\n✗ Error during migration: {str(e)}")
            print("Migration failed. Database rolled back.")
            import traceback
            traceback.print_exc()
            raise


if __name__ == '__main__':
    # Parse command line arguments
    if '--help' in sys.argv or '-h' in sys.argv:
        show_help()

    auto_confirm = '--auto' in sys.argv or '-y' in sys.argv

    # Extract interest rate from arguments
    new_rate = None
    for arg in sys.argv[1:]:
        if arg not in ['--auto', '-y', '--help', '-h']:
            new_rate = validate_rate(arg)
            break

    migrate(auto_confirm=auto_confirm, new_rate=new_rate)
