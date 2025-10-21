import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

import requests
from dotenv import load_dotenv

# Ensure SMTP/API credentials come from .env when running locally.
load_dotenv()
logger = logging.getLogger(__name__)

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
EMAIL_PROVIDER = os.getenv("EMAIL_PROVIDER", "smtp").lower()
DEFAULT_RECIPIENT = os.getenv("EMAIL_TO")  # optional override


def _send_via_smtp(
    sender: str,
    recipient: str,
    subject: str,
    full_html: str,
    plain_text: str,
) -> None:
    user = os.getenv("SMTP_USER")
    password = os.getenv("SMTP_PASS")

    if not all([user, password]):
        logger.error("Missing SMTP_USER / SMTP_PASS; aborting SMTP send")
        raise RuntimeError("SMTP_USER / SMTP_PASS are required for SMTP provider.")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = recipient

    msg.attach(MIMEText(plain_text, "plain", "utf-8"))
    msg.attach(MIMEText(full_html, "html", "utf-8"))

    logger.debug(
        "Connecting to SMTP server %s:%s as %s", SMTP_HOST, SMTP_PORT, user
    )
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as server:
        server.starttls()
        server.login(user, password)
        logger.info("Sending email '%s' to %s via SMTP", subject, recipient)
        server.sendmail(sender, [recipient], msg.as_string())


def _send_via_sendgrid(
    sender: str,
    recipient: str,
    subject: str,
    full_html: str,
    plain_text: str,
) -> None:
    api_key = os.getenv("SENDGRID_API_KEY")
    if not api_key:
        logger.error("Missing SENDGRID_API_KEY; aborting SendGrid send")
        raise RuntimeError("SENDGRID_API_KEY is required for SendGrid provider.")

    payload = {
        "personalizations": [{"to": [{"email": recipient}]}],
        "from": {"email": sender},
        "subject": subject,
        "content": [
            {"type": "text/plain", "value": plain_text},
            {"type": "text/html", "value": full_html},
        ],
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    logger.info("Sending email '%s' to %s via SendGrid", subject, recipient)
    response = requests.post(
        "https://api.sendgrid.com/v3/mail/send",
        headers=headers,
        json=payload,
        timeout=30,
    )
    if response.status_code >= 400:
        logger.error(
            "SendGrid returned %s: %s", response.status_code, response.text
        )
        raise RuntimeError(
            f"SendGrid error {response.status_code}: {response.text}"
        )


def send_email(
    subject: str,
    html_body: str,
    text_body: Optional[str] = None,
    recipient: Optional[str] = None,
):
    sender = os.getenv("EMAIL_FROM")
    if not sender:
        logger.error("EMAIL_FROM missing; aborting email send")
        raise RuntimeError("EMAIL_FROM is required.")

    recipient = recipient or DEFAULT_RECIPIENT or sender
    plain_text = (text_body or "").strip()
    full_html = (
        '<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"></head>'
        f"<body>{html_body}</body></html>"
    )

    logger.debug(
        "Dispatching email via provider '%s' to %s", EMAIL_PROVIDER, recipient
    )

    if EMAIL_PROVIDER == "sendgrid":
        _send_via_sendgrid(sender, recipient, subject, full_html, plain_text)
    elif EMAIL_PROVIDER == "smtp":
        _send_via_smtp(sender, recipient, subject, full_html, plain_text)
    else:
        logger.error("Unsupported email provider '%s'", EMAIL_PROVIDER)
        raise RuntimeError(
            f"Unsupported EMAIL_PROVIDER '{EMAIL_PROVIDER}'. "
            "Valid options: 'smtp', 'sendgrid'."
        )
