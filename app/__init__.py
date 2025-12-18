"""
Old Timers Savings Group - Digital Records Management System
Flask Application Factory
"""
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from dotenv import load_dotenv
import os
import pytz

# Load environment variables
load_dotenv()

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()


def create_app(config_name='development'):
    """Application factory pattern"""
    app = Flask(__name__)

    # Configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

    # Database configuration with absolute path support
    database_url = os.getenv('DATABASE_URL', 'sqlite:///oldtimerssavings.db')
    # If using SQLite and path is relative, convert to absolute path
    if database_url.startswith('sqlite:///') and not database_url.startswith('sqlite:////'):
        # Extract the relative path after sqlite:///
        db_path = database_url.replace('sqlite:///', '', 1)
        # If it's not already an absolute path, make it relative to the app's root directory
        if not os.path.isabs(db_path):
            base_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
            db_path = os.path.join(base_dir, db_path)
            # Ensure the directory exists
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            database_url = f'sqlite:///{db_path}'

    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_CONTENT_LENGTH', 10 * 1024 * 1024))  # 10 MB
    app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', 'app/static/uploads')
    app.config['TIMEZONE'] = pytz.timezone(os.getenv('TIMEZONE', 'Africa/Kampala'))

    # Session configuration
    # SESSION_COOKIE_SECURE should be True only when using HTTPS
    # For local development (HTTP), it should be False
    session_secure = os.getenv('SESSION_COOKIE_SECURE', 'False') == 'True'
    app.config['SESSION_COOKIE_SECURE'] = session_secure
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = os.getenv('SESSION_COOKIE_SAMESITE', 'Lax')
    app.config['PERMANENT_SESSION_LIFETIME'] = int(os.getenv('PERMANENT_SESSION_LIFETIME', 1800))

    # Session cookie name (helps avoid conflicts)
    app.config['SESSION_COOKIE_NAME'] = 'oldtimers_session'

    # Pagination
    app.config['ITEMS_PER_PAGE'] = int(os.getenv('ITEMS_PER_PAGE', 50))

    # System defaults (from specification)
    app.config['MEMBERSHIP_FEE'] = int(os.getenv('MEMBERSHIP_FEE', 20000))
    app.config['MONTHLY_CONTRIBUTION'] = int(os.getenv('MONTHLY_CONTRIBUTION', 100000))
    app.config['BEREAVEMENT_AMOUNT'] = int(os.getenv('BEREAVEMENT_AMOUNT', 500000))
    app.config['LOAN_INTEREST_RATE'] = float(os.getenv('LOAN_INTEREST_RATE', 5.00))
    app.config['LOAN_MAX_PERIOD'] = int(os.getenv('LOAN_MAX_PERIOD', 2))
    app.config['QUORUM_REQUIREMENT'] = int(os.getenv('QUORUM_REQUIREMENT', 5))
    app.config['SUSPENSION_THRESHOLD'] = int(os.getenv('SUSPENSION_THRESHOLD', 3))
    app.config['EXPULSION_THRESHOLD'] = int(os.getenv('EXPULSION_THRESHOLD', 6))
    app.config['QUALIFICATION_PERIOD'] = int(os.getenv('QUALIFICATION_PERIOD', 5))
    app.config['EXPELLED_REFUND_PERCENTAGE'] = int(os.getenv('EXPELLED_REFUND_PERCENTAGE', 80))

    # Email/Notification configuration
    app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True') == 'True'
    app.config['MAIL_USE_SSL'] = os.getenv('MAIL_USE_SSL', 'False') == 'True'
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER', 'Old Timers Savings Club <noreply@oldtimerssavings.org>')
    app.config['BASE_URL'] = os.getenv('BASE_URL', 'http://localhost:5000')

    # SMS Configuration (optional)
    app.config['SMS_ENABLED'] = os.getenv('SMS_ENABLED', 'False') == 'True'
    app.config['SMS_API_URL'] = os.getenv('SMS_API_URL')
    app.config['SMS_API_KEY'] = os.getenv('SMS_API_KEY')
    app.config['SMS_SENDER_ID'] = os.getenv('SMS_SENDER_ID', 'OTSC')

    # WhatsApp Configuration (optional)
    app.config['WHATSAPP_ENABLED'] = os.getenv('WHATSAPP_ENABLED', 'False') == 'True'
    app.config['WHATSAPP_API_URL'] = os.getenv('WHATSAPP_API_URL')
    app.config['WHATSAPP_API_TOKEN'] = os.getenv('WHATSAPP_API_TOKEN')
    app.config['WHATSAPP_PHONE_ID'] = os.getenv('WHATSAPP_PHONE_ID')

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    mail.init_app(app)

    # Register blueprints
    with app.app_context():
        from app.routes import auth, main
        from app.routes.members import members
        from app.routes.contributions import contributions
        from app.routes.membership_fees import membership_fees
        from app.routes.loans import loans
        from app.routes.welfare import welfare
        from app.routes.meetings import meetings
        from app.routes.reports import reports
        from app.routes.users import users
        from app.routes.expenses import expenses

        app.register_blueprint(auth)
        app.register_blueprint(main)
        app.register_blueprint(members)
        app.register_blueprint(contributions)
        app.register_blueprint(membership_fees)
        app.register_blueprint(loans)
        app.register_blueprint(welfare)
        app.register_blueprint(meetings)
        app.register_blueprint(reports)
        app.register_blueprint(users)
        app.register_blueprint(expenses)

        # Create database tables
        db.create_all()

    # Context processors and template filters
    @app.context_processor
    def utility_processor():
        """Make utility functions available in templates"""
        from app.utils.helpers import (
            format_currency, format_date, format_datetime, format_phone,
            truncate_string, get_status_badge_class
        )
        from app.models.notification import Notification

        # Get unread notifications count for navbar
        unread_count = 0
        if hasattr(app, 'extensions') and 'login_manager' in app.extensions:
            from flask_login import current_user
            if current_user.is_authenticated:
                unread_count = Notification.get_unread_count(current_user.id)

        return {
            'format_currency': format_currency,
            'format_date': format_date,
            'format_datetime': format_datetime,
            'format_phone': format_phone,
            'truncate_string': truncate_string,
            'get_status_badge_class': get_status_badge_class,
            'unread_notifications': unread_count,
            'app_name': os.getenv('APP_NAME', 'Old Timers Savings Group')
        }

    # Template filters
    @app.template_filter('format_currency')
    def format_currency_filter(amount):
        from app.utils.helpers import format_currency
        return format_currency(amount)

    @app.template_filter('format_date')
    def format_date_filter(date_value):
        from app.utils.helpers import format_date
        return format_date(date_value)

    @app.template_filter('format_datetime')
    def format_datetime_filter(datetime_value):
        from app.utils.helpers import format_datetime
        return format_datetime(datetime_value)

    @app.template_filter('truncate_string')
    def truncate_string_filter(text, max_length=50):
        from app.utils.helpers import truncate_string
        return truncate_string(text, max_length)

    @app.template_filter('get_status_badge_class')
    def get_status_badge_class_filter(status):
        from app.utils.helpers import get_status_badge_class
        return get_status_badge_class(status)

    # Register CLI commands
    from app.commands import register_commands
    register_commands(app)

    return app
