# Old Timers Savings Group - Digital Records Management System

A comprehensive web-based system for managing savings group operations including member management, contributions, loans, welfare, and financial reporting.

---

## 📚 Documentation

All documentation has been organized in the [`docs/`](docs/) directory.

### Quick Start

**[→ View Complete Documentation Index](docs/INDEX.md)**

### Essential Documents

1. **[Quick Start Guide](docs/QUICKSTART.md)** - Get started with the system
2. **[Loan Reminders Setup](docs/README_LOAN_REMINDERS.md)** - Configure automated payment reminders
3. **[Guarantor Workflow](docs/QUICK_START_GUARANTOR_WORKFLOW.md)** - Loan approval process
4. **[Notification Setup](docs/NOTIFICATION_CONFIGURATION.md)** - Email/SMS/WhatsApp configuration

---

## 🚀 Quick Installation

### 1. Clone and Setup

```bash
cd /home/alex/savings-system
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Environment

Create `.env` file:
```bash
cp .env.example .env
# Edit .env with your settings
```

### 3. Initialize Database

```bash
flask shell
>>> from app import db
>>> db.create_all()
>>> exit()
```

### 4. Run Application

```bash
flask run
```

Visit: http://localhost:5000

---

## 📖 Key Features

### Member Management
- Member registration and profiles
- Membership fee tracking
- Qualification status monitoring
- Member statements

### Financial Management
- Monthly contributions
- Loan processing with guarantor approval
- Welfare payments (bereavement support)
- Operational expense tracking
- Comprehensive financial reports

### Loan System
- ✅ Guarantor-based or collateral-based loans
- ✅ Two-step approval (guarantors → executives)
- ✅ Automatic due date calculation
- ✅ Automated payment reminders (Email/SMS/WhatsApp)
- ✅ Interest calculation (5% monthly)
- ✅ Repayment tracking

### Notifications
- Email notifications
- SMS alerts (optional)
- WhatsApp messages (optional)
- Automated loan payment reminders

### Reporting
- Financial summary
- Member statements
- Meeting attendance
- Audit logs

---

## 🔐 User Roles

- **Super Admin** - Full system access
- **Executive** - Manage operations, approve loans
- **Auditor** - Read-only access to financial records
- **Member** - View own records, apply for loans

---

## 📊 System Requirements

- Python 3.8+
- SQLite 3+ (or PostgreSQL for production)
- Modern web browser
- Email account (for notifications)

---

## 📁 Project Structure

```
savings-system/
├── app/
│   ├── models/         # Database models
│   ├── routes/         # Application routes
│   ├── templates/      # HTML templates
│   ├── static/         # CSS, JS, images
│   └── utils/          # Helper functions
├── docs/               # Documentation (20+ files)
├── migrations/         # Database migrations
├── venv/              # Virtual environment
├── requirements.txt   # Python dependencies
└── run.py            # Application entry point
```

---

## 🔧 Configuration

See [docs/NOTIFICATION_CONFIGURATION.md](docs/NOTIFICATION_CONFIGURATION.md) for:
- Email setup (Gmail, SMTP)
- SMS configuration (Africa's Talking)
- WhatsApp setup (Business API)

---

## 📅 Recent Updates (December 17, 2025)

- ✅ Loan due date tracking with automated reminders
- ✅ Guarantor qualification requirements (5+ consecutive months)
- ✅ Improved guarantor access control
- ✅ Operational expenses in financial summary
- ✅ Multiple bug fixes and improvements

See: [docs/SESSION_SUMMARY_2025-12-17.md](docs/SESSION_SUMMARY_2025-12-17.md)

---

## 📞 Support & Documentation

### Getting Help

1. **Setup Issues** → [docs/QUICKSTART.md](docs/QUICKSTART.md)
2. **Loan Reminders** → [docs/LOAN_REMINDER_SETUP.md](docs/LOAN_REMINDER_SETUP.md)
3. **Bug Reports** → [docs/BUGFIXES_2025-12-17.md](docs/BUGFIXES_2025-12-17.md)
4. **Complete Index** → [docs/INDEX.md](docs/INDEX.md)

### Documentation Index

All 20+ documentation files are organized by topic:
- Setup & Installation
- Loan Management
- Financial Management
- User Management
- Notifications
- Bug Fixes & Improvements

**[→ Browse Complete Documentation Index](docs/INDEX.md)**

---

## 🛡️ Security

- Password hashing with Werkzeug
- Session management with Flask-Login
- Role-based access control
- SQL injection prevention (SQLAlchemy ORM)
- CSRF protection (Flask-WTF)

---

## 📄 License

Copyright © 2025 Old Timers Savings Group Kiteezi

---

## 🙏 Credits

Built with:
- Flask 3.0
- SQLAlchemy
- Bootstrap 5
- Python 3.12

---

**Status**: ✅ Production Ready

**Last Updated**: December 17, 2025

**Version**: 1.0.0

For detailed documentation, see the [`docs/`](docs/) directory.
# savings-system
