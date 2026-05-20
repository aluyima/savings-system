#!/bin/bash
#
# Loan Due Date Reminder Script
# Run this script daily via cron to send loan payment reminders
#
# Cron example (run daily at 8:00 AM):
# 0 8 * * * /home/alex/savings-system/send_loan_reminders.sh >> /home/alex/savings-system/logs/loan_reminders.log 2>&1
#

# Change to the project directory
cd /home/alex/savings-system

# Activate virtual environment
source venv/bin/activate

# Run the Flask command
flask send-loan-reminders

# Exit
exit 0
