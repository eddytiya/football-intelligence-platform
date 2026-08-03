import logging
import smtplib
from email.message import EmailMessage

from app.core.config import settings

logger = logging.getLogger(__name__)


def send_email(to: str, subject: str, body: str) -> bool:
    """
    Send a plain-text email through the configured SMTP provider.

    Safe to call unconditionally: when email delivery isn't configured yet
    (the default), this logs and returns without attempting a connection.
    """

    if not settings.NOTIFICATIONS_EMAIL_ENABLED or not settings.SMTP_HOST:
        logger.debug("Email delivery skipped (not configured): %s", subject)
        return False

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = settings.SMTP_FROM_EMAIL or settings.SMTP_USERNAME
    message["To"] = to
    message.set_content(body)

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
            server.starttls()
            if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.send_message(message)
        return True
    except Exception:
        logger.exception("Failed to send email: %s", subject)
        return False
