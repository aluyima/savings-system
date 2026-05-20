# Notification System Configuration

## Overview
The system supports three notification channels: Email, SMS, and WhatsApp. Configure the channels you want to use.

## Configuration Settings

Add these settings to your `config.py` or environment variables:

### 1. Email Configuration (Primary - Always Enabled)

```python
# Email Settings (Flask-Mail)
MAIL_SERVER = 'smtp.gmail.com'  # or your email server
MAIL_PORT = 587
MAIL_USE_TLS = True
MAIL_USERNAME = 'your-email@gmail.com'
MAIL_PASSWORD = 'your-app-password'  # Use app-specific password for Gmail
MAIL_DEFAULT_SENDER = 'Old Timers Savings Club <noreply@oldtimerssavings.org>'

# Base URL for login links in emails
BASE_URL = 'https://yourdomain.com'  # or http://localhost:5000 for development
```

### 2. SMS Configuration (Optional)

```python
# SMS Settings
SMS_ENABLED = True  # Set to False to disable SMS
SMS_API_URL = 'https://your-sms-provider.com/api/send'
SMS_API_KEY = 'your-api-key'
SMS_SENDER_ID = 'OTSC'  # Your registered sender ID (max 11 chars)
```

**Recommended SMS Providers for Uganda:**
- **Africa's Talking** (https://africastalking.com)
  - Affordable rates (~UGX 35 per SMS)
  - Good delivery rates in Uganda
  - Easy API integration

- **Twilio** (https://twilio.com)
  - Global coverage
  - Slightly more expensive
  - Excellent documentation

**Example: Africa's Talking Configuration**
```python
SMS_ENABLED = True
SMS_API_URL = 'https://api.africastalking.com/version1/messaging'
SMS_API_KEY = 'your_africas_talking_api_key'
SMS_SENDER_ID = 'OTSC'  # Register this with Africa's Talking
```

### 3. WhatsApp Configuration (Optional)

```python
# WhatsApp Business API Settings
WHATSAPP_ENABLED = True  # Set to False to disable WhatsApp
WHATSAPP_API_URL = 'https://graph.facebook.com/v18.0'
WHATSAPP_API_TOKEN = 'your-whatsapp-business-token'
WHATSAPP_PHONE_ID = 'your-phone-number-id'
```

**WhatsApp Business API Setup:**

WhatsApp Business API is more complex to set up but has advantages:
- Free for first 1,000 conversations per month
- Higher engagement rates than SMS
- Rich media support

**Steps to Set Up:**
1. Create a Meta Business Account (https://business.facebook.com)
2. Set up WhatsApp Business Platform
3. Get your Phone Number ID and Access Token
4. Verify your phone number
5. Create message templates (if using templates)

**Alternative: WhatsApp Cloud API via Third-Party**
Easier options through providers like:
- **Twilio** (WhatsApp-enabled numbers)
- **360Dialog** (WhatsApp Business Solution Provider)
- **MessageBird**

## Complete Configuration Example

```python
# config.py

class Config:
    # ... existing config ...

    # Email (Primary)
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = 'Old Timers Savings Club <noreply@oldtimerssavings.org>'
    BASE_URL = os.environ.get('BASE_URL', 'http://localhost:5000')

    # SMS (Optional)
    SMS_ENABLED = os.environ.get('SMS_ENABLED', 'False') == 'True'
    SMS_API_URL = os.environ.get('SMS_API_URL')
    SMS_API_KEY = os.environ.get('SMS_API_KEY')
    SMS_SENDER_ID = os.environ.get('SMS_SENDER_ID', 'OTSC')

    # WhatsApp (Optional)
    WHATSAPP_ENABLED = os.environ.get('WHATSAPP_ENABLED', 'False') == 'True'
    WHATSAPP_API_URL = os.environ.get('WHATSAPP_API_URL')
    WHATSAPP_API_TOKEN = os.environ.get('WHATSAPP_API_TOKEN')
    WHATSAPP_PHONE_ID = os.environ.get('WHATSAPP_PHONE_ID')
```

## Environment Variables (.env)

```bash
# Email Configuration
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
BASE_URL=https://yourdomain.com

# SMS Configuration (Optional)
SMS_ENABLED=True
SMS_API_URL=https://api.africastalking.com/version1/messaging
SMS_API_KEY=your_api_key_here
SMS_SENDER_ID=OTSC

# WhatsApp Configuration (Optional)
WHATSAPP_ENABLED=False
WHATSAPP_API_URL=https://graph.facebook.com/v18.0
WHATSAPP_API_TOKEN=your_token_here
WHATSAPP_PHONE_ID=your_phone_id_here
```

## Testing Notifications

To test the notification system:

```python
# In Flask shell
flask shell

>>> from app.utils.notifications import NotificationService
>>> from app.models.member import Member
>>> from app.models.loan import Loan
>>>
>>> # Get a test loan and guarantor
>>> loan = Loan.query.first()
>>> guarantor = Member.query.first()
>>>
>>> # Test notification
>>> result = NotificationService.send_guarantor_request_notification(loan, guarantor, 1)
>>> print(result)
>>> # {'email': True, 'sms': False, 'whatsapp': False}
```

## Cost Estimates (Uganda)

### Email
- **Cost**: Free (using Gmail, SendGrid free tier, etc.)
- **Limit**: Gmail ~500/day, SendGrid ~100/day free

### SMS
- **Africa's Talking**: ~UGX 35 per SMS
- **Twilio**: ~UGX 100 per SMS
- **Monthly estimate** (100 notifications): UGX 3,500 - 10,000

### WhatsApp
- **Meta**: First 1,000 conversations/month free, then ~UGX 150 per conversation
- **Third-party providers**: Variable pricing
- **Monthly estimate** (100 notifications): Free (within free tier)

## Recommended Setup

### Minimum (Free):
- ✅ **Email only**: Use Gmail SMTP (free)
- Guarantors receive email notifications
- No additional costs

### Basic (Low Cost):
- ✅ **Email**: Gmail SMTP (free)
- ✅ **SMS**: Africa's Talking (~UGX 5,000/month for 150 SMS)
- Better reach, especially for members without regular email access

### Advanced (Best Experience):
- ✅ **Email**: Professional SMTP (SendGrid/Mailgun)
- ✅ **SMS**: Africa's Talking
- ✅ **WhatsApp**: Meta WhatsApp Business API
- Maximum reach and engagement

## Implementation Priority

1. **Phase 1** (Now): Email notifications only
2. **Phase 2** (Later): Add SMS via Africa's Talking
3. **Phase 3** (Future): Add WhatsApp Business API

Start with email and add other channels as needed based on member engagement and budget.
