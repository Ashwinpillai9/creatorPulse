import os
from dotenv import load_dotenv
import smtplib
from email.mime.text import MIMEText

# Ensure SMTP credentials come from .env when running locally.
load_dotenv()

def send_email(subject: str, body_markdown: str):
    sender = os.getenv("EMAIL_FROM")
    user = os.getenv("SMTP_USER")
    password = os.getenv("SMTP_PASS")

    if not all([sender, user, password]):
        raise RuntimeError("EMAIL_FROM / SMTP_USER / SMTP_PASS are required.")

    msg = MIMEText(body_markdown, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = sender

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(user, password)
        server.sendmail(sender, [sender], msg.as_string())
