"""
Utility Helper Functions
Common formatting and utility functions used throughout the application
"""
from datetime import datetime
import pytz
import phonenumbers
from flask import current_app


def format_currency(amount):
    """
    Format amount as UGX currency

    Args:
        amount: Numeric amount to format

    Returns:
        Formatted string like "UGX 100,000"
    """
    if amount is None:
        return "UGX 0"

    try:
        amount = float(amount)
        return f"UGX {amount:,.0f}"
    except (ValueError, TypeError):
        return "UGX 0"


def format_date(date_value, format_string='%d/%m/%Y'):
    """
    Format date value

    Args:
        date_value: Date or datetime object
        format_string: strftime format string

    Returns:
        Formatted date string
    """
    if date_value is None:
        return ""

    if isinstance(date_value, str):
        try:
            date_value = datetime.strptime(date_value, '%Y-%m-%d')
        except ValueError:
            return date_value

    try:
        return date_value.strftime(format_string)
    except AttributeError:
        return str(date_value)


def format_datetime(datetime_value, format_string='%d/%m/%Y %H:%M'):
    """
    Format datetime value

    Args:
        datetime_value: Datetime object
        format_string: strftime format string

    Returns:
        Formatted datetime string
    """
    if datetime_value is None:
        return ""

    try:
        return datetime_value.strftime(format_string)
    except AttributeError:
        return str(datetime_value)


def format_phone(phone_number, country_code='UG'):
    """
    Format phone number to international format

    Args:
        phone_number: Phone number string
        country_code: Country code (default: UG for Uganda)

    Returns:
        Formatted phone number
    """
    if not phone_number:
        return ""

    try:
        parsed = phonenumbers.parse(phone_number, country_code)
        return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
    except phonenumbers.phonenumberutil.NumberParseException:
        return phone_number


def parse_phone(phone_number, country_code='UG'):
    """
    Parse and validate phone number

    Args:
        phone_number: Phone number string
        country_code: Country code (default: UG for Uganda)

    Returns:
        Tuple (is_valid, formatted_number, error_message)
    """
    if not phone_number:
        return False, None, "Phone number is required"

    try:
        parsed = phonenumbers.parse(phone_number, country_code)
        if phonenumbers.is_valid_number(parsed):
            formatted = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
            return True, formatted, None
        else:
            return False, None, "Invalid phone number"
    except phonenumbers.phonenumberutil.NumberParseException as e:
        return False, None, str(e)


def get_current_time():
    """
    Get current time in system timezone

    Returns:
        Timezone-aware datetime object
    """
    timezone = current_app.config.get('TIMEZONE', 'Africa/Kampala')
    tz = pytz.timezone(timezone)
    return datetime.now(tz)


def get_financial_year():
    """
    Get current financial year (July to June)

    Returns:
        String like "2023/2024"
    """
    now = get_current_time()
    if now.month >= 7:
        return f"{now.year}/{now.year + 1}"
    else:
        return f"{now.year - 1}/{now.year}"


def get_contribution_month(date_value=None):
    """
    Get contribution month in YYYY-MM format

    Args:
        date_value: Date object (default: current date)

    Returns:
        String like "2024-01"
    """
    if date_value is None:
        date_value = get_current_time()

    return date_value.strftime('%Y-%m')


def calculate_age(date_of_birth):
    """
    Calculate age from date of birth

    Args:
        date_of_birth: Date object

    Returns:
        Age in years
    """
    if date_of_birth is None:
        return None

    today = get_current_time().date()
    age = today.year - date_of_birth.year

    # Adjust if birthday hasn't occurred this year
    if today.month < date_of_birth.month or (today.month == date_of_birth.month and today.day < date_of_birth.day):
        age -= 1

    return age


def generate_receipt_html(receipt_data):
    """
    Generate HTML for receipt

    Args:
        receipt_data: Dictionary with receipt information

    Returns:
        HTML string
    """
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Receipt - {receipt_data['receipt_number']}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .header {{ text-align: center; margin-bottom: 30px; }}
            .header h1 {{ margin: 0; color: #333; }}
            .header p {{ margin: 5px 0; color: #666; }}
            .receipt-info {{ margin-bottom: 20px; }}
            .receipt-info table {{ width: 100%; }}
            .receipt-info td {{ padding: 5px; }}
            .amount-box {{ background: #f5f5f5; padding: 15px; text-align: center; margin: 20px 0; border: 2px solid #333; }}
            .amount-box .amount {{ font-size: 24px; font-weight: bold; color: #2c3e50; }}
            .footer {{ margin-top: 40px; text-align: center; font-size: 12px; color: #666; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>OLD TIMERS SAVINGS GROUP</h1>
            <p>Official Receipt</p>
        </div>

        <div class="receipt-info">
            <table>
                <tr>
                    <td><strong>Receipt No:</strong></td>
                    <td>{receipt_data['receipt_number']}</td>
                    <td><strong>Date:</strong></td>
                    <td>{format_date(receipt_data['payment_date'])}</td>
                </tr>
                <tr>
                    <td><strong>Member:</strong></td>
                    <td colspan="3">{receipt_data['member_name']} ({receipt_data['member_number']})</td>
                </tr>
                <tr>
                    <td><strong>Payment Method:</strong></td>
                    <td>{receipt_data['payment_method']}</td>
                    <td><strong>Type:</strong></td>
                    <td>{receipt_data['receipt_type']}</td>
                </tr>
            </table>
        </div>

        <div class="amount-box">
            <p style="margin: 0;">Amount Paid</p>
            <p class="amount">{format_currency(receipt_data['amount'])}</p>
        </div>

        <p><strong>Description:</strong> {receipt_data.get('description', 'N/A')}</p>

        <div class="footer">
            <p>This is a computer-generated receipt and is valid without signature.</p>
            <p>Generated on {format_datetime(datetime.now())}</p>
        </div>
    </body>
    </html>
    """
    return html


def truncate_string(text, max_length=50):
    """
    Truncate string to max length with ellipsis

    Args:
        text: String to truncate
        max_length: Maximum length

    Returns:
        Truncated string
    """
    if not text:
        return ""

    if len(text) <= max_length:
        return text

    return text[:max_length - 3] + "..."


def get_status_badge_class(status):
    """
    Get Bootstrap badge class for status

    Args:
        status: Status string

    Returns:
        Bootstrap badge class
    """
    status_map = {
        # Member statuses
        'Active': 'success',
        'Inactive': 'secondary',
        'Suspended': 'warning',
        'Expelled': 'danger',
        'Deceased': 'dark',

        # Loan statuses
        'Pending': 'warning',
        'Approved': 'success',
        'Rejected': 'danger',
        'Disbursed': 'primary',
        'Repaying': 'info',
        'Completed': 'success',
        'Defaulted': 'danger',

        # Welfare statuses
        'Submitted': 'info',
        'UnderReview': 'warning',
        'Paid': 'success',

        # Meeting statuses
        'Scheduled': 'info',
        'Cancelled': 'danger',

        # Attendance
        'Present': 'success',
        'Absent': 'danger',
        'Excused': 'warning',

        # Generic
        'InProgress': 'primary',
    }

    return f"badge bg-{status_map.get(status, 'secondary')}"
