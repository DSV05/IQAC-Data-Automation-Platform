"""
Email Utility
=============
Sends transactional emails (password reset, notifications, etc).

Design:
- If SMTP_HOST/USER/PASSWORD are not configured in .env, emails are NOT sent
  over the network -- instead the full email (including the reset link) is
  written to the backend logs so local/dev environments work without a real
  mail server. This is why "no email arrived" in dev: the platform was never
  actually calling a send step at all (see auth.py forgot-password endpoint,
  which previously just had `pass  # TODO Module 11: send email`).
- If SMTP is configured, a real email is sent via smtplib over TLS.
- This function is synchronous by design so it can be scheduled as a
  FastAPI BackgroundTask (Starlette runs sync background tasks in a
  threadpool, so it never blocks the event loop).
"""
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


def send_email(to_email: str, subject: str, html_body: str, text_body: str | None = None) -> None:
    """Send an email, or log it if SMTP is not configured."""
    if not settings.smtp_configured:
        logger.warning(
            "smtp_not_configured_email_logged_only",
            to=to_email,
            subject=subject,
            body=text_body or html_body,
        )
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{settings.EMAILS_FROM_NAME} <{settings.EMAILS_FROM}>"
    msg["To"] = to_email

    if text_body:
        msg.attach(MIMEText(text_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
            if settings.SMTP_USE_TLS:
                server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.EMAILS_FROM, [to_email], msg.as_string())
        logger.info("email_sent", to=to_email, subject=subject)
    except Exception as exc:  # noqa: BLE001 -- never let email failure break the request
        logger.error("email_send_failed", to=to_email, subject=subject, error=str(exc))


def send_password_reset_email(to_email: str, reset_token: str, user_name: str = "") -> None:
    reset_link = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"
    greeting = f"Hi {user_name}," if user_name else "Hi,"

    text_body = (
        f"{greeting}\n\n"
        "We received a request to reset the password for your IQAC Data "
        "Automation Platform account.\n\n"
        f"Reset your password here (valid for 2 hours):\n{reset_link}\n\n"
        "If you did not request this, you can safely ignore this email.\n\n"
        "-- Ganpat University IQAC Platform"
    )

    html_body = f"""
    <div style="font-family: Arial, sans-serif; max-width: 480px; margin: 0 auto;">
      <h2 style="color:#003087;">Reset your password</h2>
      <p>{greeting}</p>
      <p>We received a request to reset the password for your
      <strong>IQAC Data Automation Platform</strong> account.</p>
      <p style="margin: 24px 0;">
        <a href="{reset_link}"
           style="background:#003087;color:#fff;padding:12px 24px;
                  border-radius:6px;text-decoration:none;font-weight:bold;">
          Reset Password
        </a>
      </p>
      <p style="color:#666;font-size:13px;">This link expires in 2 hours.
      If you did not request this, you can safely ignore this email.</p>
      <hr style="border:none;border-top:1px solid #eee;margin:24px 0;">
      <p style="color:#999;font-size:12px;">Ganpat University &mdash; IQAC Platform</p>
    </div>
    """

    send_email(to_email, "Reset your IQAC Platform password", html_body, text_body)
