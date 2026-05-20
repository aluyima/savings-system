# Old Timers Savings Group - Digital Records Management System

A comprehensive Flask-based web application for managing the Old Timers Savings Group's operations, including member management, contributions tracking, welfare support, loan management, and meeting documentation.

## Features Implemented (Phase 1 - Foundation)

### Core Functionality
- **User Authentication & Authorization**
  - Secure login with password hashing (SHA256)
  - Role-based access control (SuperAdmin, Executive, Auditor, Member)
  - Account lockout after failed login attempts
  - Mandatory password change on first login
  - Session management with 30-minute timeout

- **Database Models**
  - Users and Members
  - Contributions and Receipts (auto-generated receipt numbers)
  - Welfare Requests and Payments
  - Loans and Repayments
  - Meetings, Attendance, Minutes, and Action Items
  - Audit Logs (comprehensive system activity tracking)
  - Notifications (in-app notification system)
  - System Settings (configurable parameters)

- **Dashboard Views**
  - Executive Dashboard (for SuperAdmin and Executive members)
  - Member Dashboard (personalized member view)
  - Auditor Dashboard (read-only financial oversight)

- **Utility Functions**
  - Currency formatting (UGX)
  - Date/time formatting (Africa/Kampala timezone)
  - Phone number validation and formatting
  - Status badge helpers
  - Receipt HTML generation

## Technology Stack

- **Backend**: Flask 3.0.0
- **Database**: SQLite 3 (SQLAlchemy ORM)
- **Authentication**: Flask-Login 0.6.3
- **Frontend**: Bootstrap 5.3 (CDN), Bootstrap Icons
- **PDF Generation**: ReportLab 4.0.7
- **Forms**: Flask-WTF 1.2.1
- **Phone Validation**: phonenumbers 8.13.26
- **Timezone**: pytz 2023.3.post1

## Project Structure

```
savings-system/
├── app/
│   ├── __init__.py              # Application factory
│   ├── models/                  # Database models
│   │   ├── __init__.py
│   │   ├── user.py             # User authentication
│   │   ├── member.py           # Member and NextOfKin
│   │   ├── contribution.py     # Contributions and Receipts
│   │   ├── welfare.py          # Welfare requests and payments
│   │   ├── loan.py             # Loans and repayments
│   │   ├── meeting.py          # Meetings and minutes
│   │   ├── audit.py            # Audit logs
│   │   ├── notification.py     # Notifications
│   │   └── system.py           # System settings
│   ├── routes/                  # Route blueprints
│   │   ├── __init__.py
│   │   ├── auth.py             # Authentication routes
│   │   └── main.py             # Dashboard routes
│   ├── templates/               # Jinja2 templates
│   │   ├── base.html           # Base layout
│   │   ├── auth/               # Authentication templates
│   │   ├── dashboard/          # Dashboard templates
│   │   └── notifications/      # Notification templates
│   ├── static/                  # Static files
│   │   ├── css/
│   │   ├── js/
│   │   ├── img/
│   │   └── uploads/
│   └── utils/                   # Utility functions
│       ├── __init__.py
│       ├── helpers.py          # Helper functions
│       └── decorators.py       # Custom decorators
├── instance/
│   └── oldtimerssavings.db     # SQLite database
├── requirements.txt             # Python dependencies
├── run.py                       # Application entry point
├── .env.example                 # Environment variables template
└── README.md                    # This file
```

## Setup Instructions

### 1. Prerequisites
- Python 3.8 or higher
- Virtual environment (venv)

### 2. Installation

```bash
# Clone or navigate to the project directory
cd savings-system

# Create and activate virtual environment (if not already created)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

```bash
# Copy environment variables template
cp .env.example .env

# Edit .env and set your configurations
# IMPORTANT: Change SECRET_KEY in production!
nano .env
```

### 4. Initialize Database

```bash
# Initialize database tables
flask init_db

# Create the first Super Admin user
flask create_admin
```

The `create_admin` command will prompt you for:
- Full name
- Phone number (will be used as username)
- Email address
- Password

### 5. Run the Application

```bash
# Development mode
flask run

# Or using the run.py file
python run.py
```

The application will be available at: `http://127.0.0.1:5000`

## User Roles and Permissions

### SuperAdmin
- Full system access
- User management
- System settings configuration
- All Executive permissions

### Executive (Chairman, Secretary, Treasurer)
- Member management
- Contribution recording
- Welfare request approval
- Loan management
- Meeting scheduling
- Report generation
- Next of kin access

### Auditor
- Read-only access to all records
- Financial reports
- Audit trail viewing
- No modification permissions

### Member
- View own contribution history
- Submit welfare requests
- Apply for loans
- View meeting schedules
- Update own profile

## Key System Rules (from Specification)

### Membership
- Membership fee: UGX 20,000 (one-time)
- Monthly contribution: UGX 100,000
- Qualification period: 5 consecutive months
- Suspension: After 3 missed contributions
- Expulsion: After 6 consecutive missed contributions
- Refund on expulsion: 80% of total contributed

### Loans
- Interest rate: 5% per month
- Maximum period: 2 months
- Security: Collateral OR 2 guarantors
- Approval: All 3 Executive members must approve

### Welfare
- Bereavement support: UGX 500,000 (standard)
- Approval workflow: Secretary reviews → Chairman approves
- Payment authorization: Treasurer + Secretary (dual control)

### Meetings
- Quorum requirement: Minimum 5 members
- Types: Regular, Emergency, Annual General Meeting
- Minutes must be approved by Chairperson before publication

## Flask CLI Commands

```bash
# Initialize database
flask init_db

# Create super admin user
flask create_admin

# Access Python shell with app context
flask shell

# Run development server
flask run
```

## Security Features

- Password hashing with Werkzeug (SHA256)
- Session security with httpOnly cookies
- Account lockout after 5 failed login attempts (30-minute lock)
- Mandatory password change on first login
- Comprehensive audit logging (all actions tracked with IP address)
- Role-based access control with decorators
- CSRF protection with Flask-WTF

## Next Development Phases

### Phase 2 - Member Management (Weeks 3-4)
- Member registration and profile management
- Next of kin management
- Member status tracking
- Suspension/expulsion workflow

### Phase 3 - Contributions (Weeks 5-6)
- Contribution recording
- Receipt generation (PDF)
- Payment tracking
- Contribution reports

### Phase 4 - Welfare (Weeks 7-8)
- Welfare request submission
- Approval workflow
- Payment processing
- Document management

### Phase 5 - Loans (Weeks 9-10)
- Loan application
- Approval workflow (3-member approval)
- Disbursement tracking
- Repayment management
- Default tracking

### Phase 6 - Meetings (Week 11)
- Meeting scheduling
- Attendance tracking
- Minutes management
- Action item tracking

### Phase 7 - Reports (Week 12)
- Financial reports
- Member reports
- Contribution statements
- Audit reports

### Phase 8 - Testing & Deployment (Week 13)
- Comprehensive testing
- PythonAnywhere deployment
- User training materials

## Support and Maintenance

For issues or questions, please refer to the System Specification document or contact the development team.

## License

Copyright © 2024 Old Timers Savings Group. All rights reserved.
