# CLAUDE.md

Guidance for working in this repository. This file tracks the architectural and
technical decisions behind the **Old Timers Savings Group – Digital Records
Management System**, a Flask web app for managing a savings group's members,
contributions, loans, welfare, meetings, and financial reporting.

## Running the app

```bash
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # then edit secrets
flask --app run init-db       # create tables + seed SystemSetting defaults
flask --app run create-superadmin   # interactive admin creation
flask run                     # dev server at http://localhost:5000
# or: python run.py           # debug=True
```

Currency is UGX throughout. Default timezone is `Africa/Kampala`.

## Architecture

Flask **application-factory** pattern. `create_app(config_name)` in
[app/__init__.py](app/__init__.py) builds the app, reads all config from
environment variables (via `python-dotenv`), initializes extensions, and
registers blueprints inside an app context.

- **Entry point**: [run.py](run.py) calls `create_app(os.getenv('FLASK_ENV', 'development'))`.
- **Extensions** (module-level singletons in `app/__init__.py`, `init_app`-ed in the factory):
  `db` (Flask-SQLAlchemy), `login_manager` (Flask-Login), `mail` (Flask-Mail).
- **ORM**: SQLAlchemy. DB is **SQLite** by default (`instance/oldtimerssavings.db`);
  relative SQLite URLs are rewritten to absolute paths in the factory. Postgres
  is intended for production via `DATABASE_URL`.
- **Schema creation**: `db.create_all()` runs on every startup. There is **no
  Alembic/Flask-Migrate**; schema changes are applied with hand-written scripts
  (see Migrations below).
- **Templating**: server-rendered Jinja2 + Bootstrap 5. Shared helpers
  (`format_currency`, `format_date`, etc.) and unread-notification count are
  injected via a context processor and registered as template filters in the
  factory.

### Layout

```
app/
├── __init__.py     # application factory, config, extension + blueprint wiring
├── commands.py     # Flask CLI commands (registered via register_commands)
├── models/         # one module per domain entity; aggregated in models/__init__.py
├── routes/         # one Blueprint per domain area (auth, members, contributions,
│                   #   membership_fees, loans, welfare, meetings, reports, users,
│                   #   expenses, main)
├── templates/      # Jinja2, one subfolder per area; base.html is the shell
├── static/         # css, js, img, uploads
└── utils/          # helpers.py, decorators.py, notifications.py, loan_reminders.py
                    #   (loan_reminders also holds apply_overdue_extensions)
migrations/         # standalone one-off python migration scripts (NOT Flask-Migrate)
docs/               # extensive feature/setup/bugfix documentation
instance/           # SQLite database lives here
```

## Domain model

Models live in [app/models/](app/models/) and are re-exported from
[app/models/__init__.py](app/models/__init__.py). Key entities:

- **User** ↔ **Member** is 1:1. `User` handles auth only; `Member` holds the
  person/financial record. `User.username` is the member's phone number.
- **Member / NextOfKin**, **Contribution / Receipt**, **Loan / LoanRepayment**,
  **WelfareRequest / WelfarePayment**, **Meeting / Attendance / Minutes /
  ActionItem**, **Expense**, **Notification**, **AuditLog**, **SystemSetting**.
- Money columns use `Numeric(15, 2)`. Convert to `float` only for arithmetic.

### Roles & access control

Four roles on `User.role`: **SuperAdmin**, **Executive**, **Auditor**, **Member**.
Enforced with decorators in [app/utils/decorators.py](app/utils/decorators.py):
`super_admin_required`, `executive_required`, `auditor_required` (hierarchical —
auditor view also allows executive/superadmin), `role_required(*roles)`,
`member_or_self_required`, plus `active_account_required`,
`password_change_required`, `check_account_lock`, and `audit_log(action, entity)`.

Security decisions: passwords hashed with Werkzeug; Flask-Login sessions with a
custom cookie name (`oldtimers_session`), `HttpOnly`, `SameSite=Lax`, and
`SECURE` toggled by env (off for local HTTP); CSRF via Flask-WTF; account
lockout after failed logins; forced password change on first login
(`must_change_password`).

## Configuration & business rules

All tunables come from environment variables with defaults in the factory, and
are **also** seeded into the `SystemSetting` table by `init-db`
(`SystemSetting.initialize_defaults`). `SystemSetting` is the runtime, admin-
editable source of truth (typed get/set, audited via `updated_by`); env vars are
the bootstrap defaults.

Current business rules (see also memory `project_loan_rules.md`):

- **Loan interest: 10% per month** (`.env.example` `LOAN_INTEREST_RATE=10.00`,
  changed 2026-05-20). Simple interest: `total = principal × (1 + rate/100 × months)`
  via `Loan.calculate_total_payable()`. NOTE: some hardcoded fallback defaults in
  code/README still say 5% — treat `.env`/`SystemSetting` as authoritative.
- Loan eligibility: member must have ≥ 3 consecutive monthly contributions
  (`LOAN_MIN_CONTRIBUTIONS`); concurrent loans are allowed. Max repayment period:
  2 months.
- **Guarantor qualification: 3 consecutive months** (`QUALIFICATION_PERIOD`, reduced
  from 5 on 2026-07-14). Drives `Member.qualified_for_benefits`, which gates who can
  appear in / act as a guarantor. Nothing else uses it (welfare does not).
- **"Consecutive" means an unbroken run of months.** `Member.consecutive_months()`
  counts distinct `Contribution.contribution_month` (`YYYY-MM`) values backwards from
  the latest month, stopping at the first gap — so Jan/May/Oct is a streak of 1, not 3.
  (Before 2026-07-14 this field was just a `count()` of contribution rows, so gaps were
  ignored and members qualified who shouldn't have.) Multiple contributions in the same
  month count once. After changing this logic or `QUALIFICATION_PERIOD`, run
  `flask --app run recalculate-member-stats` (dry run) then `--apply`.
- **UI must not hardcode business rules.** Loan templates read `config.LOAN_INTEREST_RATE`,
  `config.LOAN_MIN_CONTRIBUTIONS`, `config.LOAN_MAX_PERIOD` and `config.QUALIFICATION_PERIOD`
  via Jinja's `config` object. Do not reintroduce literals — the UI previously told members
  "5% per month" while the system charged 10%.
- **Early payoff (shorten):** an executive/admin can shorten an active loan's
  repayment period via `POST /loans/<id>/shorten`; interest is recomputed for the
  shorter period (`Loan.recompute_payable()`). e.g. a 2-month loan repaid within a
  month can be reset to 1 month of interest. Manual action by design.
- **Overdue auto-extension (no cap):** a loan more than `LOAN_EXTENSION_GRACE_DAYS`
  (default 10) past due is automatically extended by one month, adding one month's
  interest on the principal and pushing the due date out a month
  (`Loan.extend_one_month()`). Repeats every month until repaid — there is no cap
  and this rule does **not** mark loans Defaulted. Applied by
  `apply_overdue_extensions()` via the `extend-overdue-loans` CLI command, which is
  meant to run **daily** (cron / PythonAnywhere scheduled task). Extensions are
  recorded in `Loan.recovery_notes` and notified in-app to borrower + executives;
  they are not audit-logged (no acting user in the job).
- Loan approval is two-stage: **guarantors** (both must approve) or collateral,
  then **executives**, then disbursement. `Loan.status` is a string state machine
  (`Pending Guarantor Approval → Pending Executive Approval → Approved →
  Disbursed → Active → Completed`, with `Returned to Applicant`, `Rejected`,
  `Defaulted` branches).
- **Loan application fee:** a fee members deposit in the bank, entered manually by
  an executive/admin via `POST /loans/<id>/application-fee` (route
  `record_application_fee`). Amount is typed per loan (no standard amount), stored
  on the `Loan` (`application_fee_*` columns). It is **separate from the repayment**
  — not added to `total_payable`/interest — and does **not** gate approval or
  disbursement; it can be recorded/updated at any time. Schema added via
  `migrations/add_loan_application_fee.py`.
- Other defaults: membership fee 20,000; monthly contribution 100,000;
  bereavement 500,000; quorum 5; qualification period 5 months; loan default
  after 30 days overdue.

When changing a business rule, update **all** of: `.env.example`, the factory
default, the `SystemSetting` seed, and any stale hardcoded literals.

## Loan administration (admin acting on behalf of members)

Many members are not IT-savvy, so loan operations were stalling when a member had
to act for themselves. The **SuperAdmin** can therefore drive the whole loan
lifecycle on a member's behalf. Rules (all in [app/routes/loans.py](app/routes/loans.py)):

- **Apply on behalf:** executives/SuperAdmin file a loan under the member selected
  on the form; everyone else is forced to their own member. (The original code
  always used the logged-in user's member and silently ignored the dropdown —
  don't reintroduce that.)
- **Guarantor approve/decline on behalf:** a SuperAdmin submits `guarantor_position`
  (`1`/`2`) to act for that guarantor; `_resolve_guarantor_slot()` resolves the slot,
  otherwise it's derived from the logged-in member. The **qualification rule is
  enforced against the represented guarantor**, not the admin, and the audit log
  records "on behalf of \<name\>".
- **Edit/resubmit and cancel** a *Returned to Applicant* loan: allowed for the
  applicant **or** a SuperAdmin.
- **Delete an application** (`POST /loans/<id>/delete`, SuperAdmin only): gated by
  `Loan.can_be_deleted()` — permitted only **before executive approval**, and never
  once the loan is disbursed or (for guarantor-backed loans) already guaranteed by
  both guarantors. Collateral loans are deletable up until executive approval.
- **The administrator is not a group member and cannot borrow.** A loan may not be
  filed for a member whose linked user is a `SuperAdmin` (server guard in `apply`),
  and admin accounts are excluded from the borrower dropdown.

## Deployment (production: PythonAnywhere)

- Virtualenv `~/.virtualenvs/savings-env`; app in `~/savings-system`; reload via the
  **Web tab → Reload** after pulling.
- The live SQLite DB (`instance/`), `.env` and `app/static/uploads/` are **gitignored
  and must never be tracked** — a previously tracked DB caused merge conflicts that
  wedged the server. Always back up `instance/oldtimerssavings.db` before deploying.
- Deploy is a plain `git pull --ff-only origin main`. Run `git config core.fileMode false`
  on the server — executable-bit flapping on `.env.example` repeatedly blocked pulls.
  Never edit `.env.example` on the server; real config belongs in `.env`.
- If a release adds columns, run its `migrations/*.py` script after pulling (see Migrations).
- Rules that depend on a scheduler (`extend-overdue-loans`, `send-loan-reminders`) only
  fire if a **daily scheduled task** is configured — as of 2026-06 none was set up, so
  overdue auto-extension will not happen on its own until one is added.

## CLI commands

Defined in [run.py](run.py) and [app/commands.py](app/commands.py), run as
`flask --app run <cmd>`:

- `init-db` — create tables and seed system settings.
- `create-admin` / `create-superadmin` — create the SuperAdmin (+ its Member).
- `send-loan-reminders` — notify on loans due tomorrow (designed for cron; see
  [send_loan_reminders.sh](send_loan_reminders.sh) and `docs/LOAN_REMINDER_SETUP.md`).
- `check-overdue-loans`, `check-upcoming-loans --days N` — reporting.
- `recalculate-member-stats [--apply]` — recompute every member's consecutive-months
  streak and qualification. Dry run by default; reports who gains/loses qualification.
- `extend-overdue-loans` — auto-extend loans overdue beyond the grace period
  (designed for a daily cron; see Loan business rules above).
- `clear-database [--keep-admin]` — wipe data respecting FK order; keeps SuperAdmin.

## Notifications

In-app `Notification` records plus optional outbound channels, all env-gated:
Email (Flask-Mail / SMTP, default Gmail), SMS (`SMS_ENABLED`), WhatsApp
(`WHATSAPP_ENABLED`). Loan reminder logic is in
[app/utils/loan_reminders.py](app/utils/loan_reminders.py). See
`docs/NOTIFICATION_CONFIGURATION.md`.

## Migrations

No migration framework. To change schema:
1. Write a standalone script in [migrations/](migrations/) (see existing examples
   like `add_loan_due_date.py`, `update_loan_interest_rates.py`) or a `.sql` file
   in the repo root, and run it against the SQLite DB.
2. Add the corresponding column to the model so `db.create_all()` stays in sync
   for fresh installs.

Migration scripts write timestamped `.log` files into `migrations/`.

## Conventions

- One blueprint and one template subfolder per domain area; mirror existing
  naming when adding features.
- Keep authorization on routes via the decorators above — don't hand-roll role
  checks.
- Use `SystemSetting.get_setting(key, default)` for configurable values rather
  than re-reading env at request time.
- Match the existing docstring style (module + class/function docstrings) and the
  emoji/`=`-banner style used in CLI output.

### Gotchas

- `Decimal('abc')` raises `decimal.InvalidOperation`, **not** `ValueError`. Several
  older routes only catch `(ValueError, TypeError)` around `Decimal(...)` and will
  500 on non-numeric form input. Catch `InvalidOperation` too.
- `AuditLog.user_id` is `nullable=False`, so **background jobs cannot write audit
  logs** (there is no acting user). Automated changes are recorded on the entity
  itself (e.g. `Loan.recovery_notes`) plus `Notification` records instead.
- Templates guard on money fields inconsistently: `loans/view.html` does
  `{% if loan.balance > 0 %}` and divides by `loan.total_payable`, which only holds
  because those are populated at approval. Loans in Active/Disbursed/Completed always
  have them; don't render that block for other statuses.
- `Member.user` (backref from `User.member`) exists for every user, so
  `hasattr(current_user, 'member')` is always true — it cannot be used to tell an
  admin apart from a member.
