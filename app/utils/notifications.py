"""
Notification System
Supports Email, SMS, and WhatsApp notifications
"""
from flask import current_app, render_template_string
from flask_mail import Message
from app import mail, db
import requests
from datetime import datetime


class NotificationService:
    """Unified notification service for Email, SMS, and WhatsApp"""

    @staticmethod
    def send_guarantor_request_notification(loan, guarantor, guarantor_number):
        """
        Send notification to guarantor when they are selected for a loan

        Args:
            loan: Loan object
            guarantor: Member object (guarantor)
            guarantor_number: 1 or 2 (which guarantor)
        """
        member = loan.member

        # Prepare notification content
        subject = f"Loan Guarantor Request - {loan.loan_number}"
        message = f"""
Dear {guarantor.full_name},

You have been selected as Guarantor #{guarantor_number} for a loan application.

Loan Details:
- Loan Number: {loan.loan_number}
- Applicant: {member.full_name} ({member.member_number})
- Amount Requested: UGX {loan.amount_requested:,.2f}
- Purpose: {loan.purpose}
- Repayment Period: {loan.repayment_period_months} months

Please log in to the system to review and approve or decline this guarantor request.

Login URL: {current_app.config.get('BASE_URL', 'http://localhost:5000')}/auth/login

Thank you,
Old Timers Savings Club Kiteezi
        """.strip()

        # Send via enabled channels
        results = {
            'email': False,
            'sms': False,
            'whatsapp': False
        }

        # 1. Email (Primary - Always attempt)
        if guarantor.email:
            results['email'] = NotificationService._send_email(
                recipient=guarantor.email,
                subject=subject,
                body=message
            )

        # 2. SMS (Optional - if enabled and phone available)
        if current_app.config.get('SMS_ENABLED', False) and guarantor.phone_primary:
            sms_message = f"Loan Guarantor Request: You've been selected as guarantor for {member.full_name}'s loan ({loan.loan_number}). Amount: UGX {loan.amount_requested:,.0f}. Please log in to approve/decline."
            results['sms'] = NotificationService._send_sms(
                phone=guarantor.phone_primary,
                message=sms_message
            )

        # 3. WhatsApp (Optional - if enabled and phone available)
        if current_app.config.get('WHATSAPP_ENABLED', False) and guarantor.phone_primary:
            results['whatsapp'] = NotificationService._send_whatsapp(
                phone=guarantor.phone_primary,
                message=message,
                template_name='guarantor_request'
            )

        return results

    @staticmethod
    def send_guarantor_approval_notification(loan):
        """Notify applicant when both guarantors have approved"""
        member = loan.member

        subject = f"Loan Guarantors Approved - {loan.loan_number}"
        message = f"""
Dear {member.full_name},

Good news! Both guarantors have approved your loan application.

Loan Details:
- Loan Number: {loan.loan_number}
- Amount Requested: UGX {loan.amount_requested:,.2f}
- Status: Pending Executive Approval

Your loan is now pending approval from the Executive Committee.

Login URL: {current_app.config.get('BASE_URL', 'http://localhost:5000')}/auth/login

Thank you,
Old Timers Savings Club Kiteezi
        """.strip()

        results = {'email': False, 'sms': False, 'whatsapp': False}

        if member.email:
            results['email'] = NotificationService._send_email(
                recipient=member.email,
                subject=subject,
                body=message
            )

        if current_app.config.get('SMS_ENABLED', False) and member.phone_primary:
            sms_message = f"Great news! Both guarantors approved your loan {loan.loan_number}. Now pending executive approval."
            results['sms'] = NotificationService._send_sms(member.phone_primary, sms_message)

        if current_app.config.get('WHATSAPP_ENABLED', False) and member.phone_primary:
            results['whatsapp'] = NotificationService._send_whatsapp(member.phone_primary, message, 'loan_update')

        return results

    @staticmethod
    def send_guarantor_rejection_notification(loan, rejecting_guarantor_name, reason):
        """Notify applicant when a guarantor rejects their loan"""
        member = loan.member

        subject = f"Loan Application Returned - {loan.loan_number}"
        message = f"""
Dear {member.full_name},

Your loan application has been returned to you for revision.

Loan Details:
- Loan Number: {loan.loan_number}
- Amount Requested: UGX {loan.amount_requested:,.2f}
- Status: Returned to Applicant

Reason: {rejecting_guarantor_name} has declined to guarantee this loan.
{f'Comments: {reason}' if reason else ''}

You can:
1. Select a new guarantor to replace the one who declined
2. Change your security type to Collateral

Please log in to revise your application.

Login URL: {current_app.config.get('BASE_URL', 'http://localhost:5000')}/auth/login

Thank you,
Old Timers Savings Club Kiteezi
        """.strip()

        results = {'email': False, 'sms': False, 'whatsapp': False}

        if member.email:
            results['email'] = NotificationService._send_email(
                recipient=member.email,
                subject=subject,
                body=message
            )

        if current_app.config.get('SMS_ENABLED', False) and member.phone_primary:
            sms_message = f"Your loan application {loan.loan_number} has been returned. A guarantor declined. Please log in to revise."
            results['sms'] = NotificationService._send_sms(member.phone_primary, sms_message)

        if current_app.config.get('WHATSAPP_ENABLED', False) and member.phone_primary:
            results['whatsapp'] = NotificationService._send_whatsapp(member.phone_primary, message, 'loan_returned')

        return results

    @staticmethod
    def _send_email(recipient, subject, body):
        """Send email notification"""
        try:
            msg = Message(
                subject=subject,
                recipients=[recipient],
                body=body,
                sender=current_app.config.get('MAIL_DEFAULT_SENDER', 'noreply@oldtimerssavings.org')
            )
            mail.send(msg)
            current_app.logger.info(f"Email sent to {recipient}: {subject}")
            return True
        except Exception as e:
            current_app.logger.error(f"Failed to send email to {recipient}: {str(e)}")
            return False

    @staticmethod
    def _send_sms(phone, message):
        """Send SMS notification via configured SMS gateway"""
        try:
            sms_api_url = current_app.config.get('SMS_API_URL')
            sms_api_key = current_app.config.get('SMS_API_KEY')
            sms_sender_id = current_app.config.get('SMS_SENDER_ID', 'OTSC')

            if not sms_api_url or not sms_api_key:
                current_app.logger.warning("SMS API not configured")
                return False

            # Format phone number (ensure it starts with country code)
            if phone.startswith('0'):
                phone = '256' + phone[1:]  # Uganda country code
            elif not phone.startswith('+') and not phone.startswith('256'):
                phone = '256' + phone

            # Example API call - adjust based on your SMS provider
            response = requests.post(
                sms_api_url,
                json={
                    'to': phone,
                    'message': message,
                    'sender_id': sms_sender_id,
                    'api_key': sms_api_key
                },
                timeout=10
            )

            if response.status_code == 200:
                current_app.logger.info(f"SMS sent to {phone}")
                return True
            else:
                current_app.logger.error(f"SMS failed: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            current_app.logger.error(f"Failed to send SMS to {phone}: {str(e)}")
            return False

    @staticmethod
    def _send_whatsapp(phone, message, template_name=None):
        """Send WhatsApp notification via WhatsApp Business API"""
        try:
            whatsapp_api_url = current_app.config.get('WHATSAPP_API_URL')
            whatsapp_token = current_app.config.get('WHATSAPP_API_TOKEN')
            whatsapp_phone_id = current_app.config.get('WHATSAPP_PHONE_ID')

            if not whatsapp_api_url or not whatsapp_token:
                current_app.logger.warning("WhatsApp API not configured")
                return False

            # Format phone number
            if phone.startswith('0'):
                phone = '256' + phone[1:]
            elif not phone.startswith('256'):
                phone = '256' + phone

            headers = {
                'Authorization': f'Bearer {whatsapp_token}',
                'Content-Type': 'application/json'
            }

            # WhatsApp Business API message format
            payload = {
                'messaging_product': 'whatsapp',
                'to': phone,
                'type': 'text',
                'text': {
                    'body': message
                }
            }

            response = requests.post(
                f"{whatsapp_api_url}/{whatsapp_phone_id}/messages",
                headers=headers,
                json=payload,
                timeout=10
            )

            if response.status_code in [200, 201]:
                current_app.logger.info(f"WhatsApp sent to {phone}")
                return True
            else:
                current_app.logger.error(f"WhatsApp failed: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            current_app.logger.error(f"Failed to send WhatsApp to {phone}: {str(e)}")
            return False


# Notification Log Model (optional - for tracking notifications)
class NotificationLog(db.Model):
    """Track all notifications sent"""
    __tablename__ = 'notification_logs'

    id = db.Column(db.Integer, primary_key=True)
    notification_type = db.Column(db.String(50), nullable=False)  # guarantor_request, guarantor_approved, etc.
    channel = db.Column(db.String(20), nullable=False)  # email, sms, whatsapp
    recipient_id = db.Column(db.Integer, db.ForeignKey('members.id'), nullable=False)
    recipient_contact = db.Column(db.String(100))  # email or phone
    subject = db.Column(db.String(200))
    message = db.Column(db.Text)
    status = db.Column(db.String(20))  # sent, failed
    related_loan_id = db.Column(db.Integer, db.ForeignKey('loans.id'))
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    error_message = db.Column(db.Text)

    def __repr__(self):
        return f'<NotificationLog {self.notification_type} - {self.channel} - {self.status}>'
