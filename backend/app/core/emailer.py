import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from dotenv import load_dotenv

# Ensure SMTP credentials come from .env when running locally.
load_dotenv()
logger = logging.getLogger(__name__)


def send_email(subject: str, html_body: str, text_body: Optional[str] = None):
    sender = os.getenv("EMAIL_FROM")
    user = os.getenv("SMTP_USER")
    password = os.getenv("SMTP_PASS")

    if not all([sender, user, password]):
        logger.error("Missing SMTP configuration; aborting email send")
        raise RuntimeError("EMAIL_FROM / SMTP_USER / SMTP_PASS are required.")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = sender

    plain_part = MIMEText((text_body or "").strip(), "plain", "utf-8")
    full_html = (
        "<!DOCTYPE html><html lang=\"en\"><head><meta charset=\"UTF-8\"></head>"
        f"<body>{html_body}</body></html>"
    )
    html_part = MIMEText(full_html, "html", "utf-8")

    msg.attach(plain_part)
    msg.attach(html_part)

    logger.debug("Connecting to SMTP server as %s", user)
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(user, password)
        logger.info("Sending email '%s' to %s", subject, sender)
        server.sendmail(sender, [sender], msg.as_string())
